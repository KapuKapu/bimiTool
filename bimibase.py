# vim: set fileencoding=utf-8
# ----------------------------------------------------------------------------#
#    Copyright 2012 Julian Weitz                                              #
#                                                                             #
#    This program is free software: you can redistribute it and/or modify     #
#    it under the terms of the GNU General Public License as published by     #
#    the Free Software Foundation, either version 3 of the License, or        #
#    any later version.                                                       #
#                                                                             #
#    This program is distributed in the hope that it will be useful,          #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#    GNU General Public License for more details.                             #
#                                                                             #
#    You should have received a copy of the GNU General Public License        #
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.    #
# ----------------------------------------------------------------------------#
import os, sys, datetime, logging

try:
    from pysqlite2 import dbapi2 as sqlite3
except ImportError:
    print("------------------------------------------------------------------------------")
    print("| Check your python sqlite3 setup! (Debian/Ubuntu: install python-pysqlite2) |")
    print("------------------------------------------------------------------------------")
    sys.exit(1)


## sqlite3 data base interface
#
#  accounts            stores account ids and names
#    aid               unique account id
#    name              name of the user
#
#  drinks              stores information of drinks
#    did               unique drink id
#    name              name of the drink
#    sales_price       price at which the drink is sold
#    purchase_price    price at which the drink was purchased
#    deposit           value of an empty bottle
#    bottles_full      number of full bottles available
#    bottles_empty     number of empte bottles
#    deleted           true if drink was deleted but is used in table transacts
#    kings             true if drink should be returned by DataBase::kings()
#
#  kings               stores information about how many drinks a user has consumed
#    aid               from table accounts
#    did               from table drinks
#    quaffed           number of drinks consumed
#
#  transacts           stores all debit and credit informations. Primary key = tid+aid+did
#    tid               transaction id
#    aid               from table accounts
#    did               from table drinks (0 for plain credit/debit transactions)
#    count             value multiplyer i.e. number of drinks
#    value             value of one drink or credit/debit added
#    date              date and time of transaction
#
class BimiBase:
    def __init__(self, path):
        self._logger = logging.getLogger('BimiBase')

        # Check for database file and directory structure
        if not os.path.isdir(os.path.dirname(path)):
            try:
                os.makedirs(os.path.dirname(path))
            except OSError as oe:
                self._logger.error('Not possible to create directory %s! No database available! [os: %s]',\
                                         os.path.dirname(path), oe)
                raise OSError('Not possible to create directory %s! No database available! [os: %s]',\
                               os.path.dirname(path), oe)

        self.dbcon = sqlite3.connect(path,detect_types=sqlite3.PARSE_DECLTYPES)
        self.cur = self.dbcon.cursor()

        # check if DB already exists, if not create one
        try:
            self.cur.execute("CREATE TABLE accounts(aid INTEGER PRIMARY KEY,\
                                                    name TEXT)")

            self.cur.execute("CREATE TABLE drinks(did INTEGER PRIMARY KEY,\
                                                  name TEXT,\
                                                  sales_price INTEGER,\
                                                  purchase_price INTEGER,\
                                                  deposit INTEGER,\
                                                  bottles_full INTEGER,\
                                                  bottles_empty INTEGER,\
                                                  deleted BOOL,\
                                                  kings BOOL)")

            self.cur.execute("CREATE TABLE kings(aid INTEGER,\
                                                 did INTEGER,\
                                                 quaffed INTEGER)")

            self.cur.execute("CREATE TABLE transacts(tid INTEGER,\
                                                     aid INTEGER,\
                                                     did INTEGER,\
                                                     count INTEGER,\
                                                     value INTEGER,\
                                                     date TIMESTAMP)")
            self.dbcon.commit()
            self._logger.info('Created new data base @ ' + path)

        except sqlite3.OperationalError:
            self._logger.info('Found an existing data base @ ' + path)
            try:
                self.cur.execute("select aid,name from accounts")
                self.cur.execute("select tid,aid,did,count,value,date from transacts")
                self.cur.execute("select did,name,sales_price,purchase_price,deposit,bottles_full from drinks")
                self.cur.execute("select aid,did,quaffed from kings")
            except sqlite3.OperationalError as err:
                self._logger.critical('Oh noes, data base corrupt or created by an older version! [sqlite3: %s]', str(err))
                sys.exit(1)
            self._logger.info('Yay, database seems to be useable.')


    ## Returns a list containing account IDs and names odered ascending by names
    #
    #  \return \b List of tuples containing (aid,name) from table accounts
    #
    def accounts(self):
        self.cur.execute("SELECT * FROM accounts ORDER BY name ASC")
        return self.cur.fetchall()


    ## Adds a new account to accounts table.
    #
    #  \param account_name \b String containing the name of the user
    #  \param credit       \b Integer value of the credit to be added. Can be negative.
    #
    def addAccount(self, account_name, credit=None):
        self.cur.execute("INSERT INTO accounts VALUES(?,?)", [None, account_name.decode('utf-8')])
        self.dbcon.commit()
        if credit is not None:
            self.addCredit(self.cur.lastrowid, credit)


    ## Creates a transaction which adds credit to account_id.
    #
    #  Doesn't check if account_id exists!
    #
    #  \param account_id \b Integer that corresponds to an aid in table accounts
    #  \param credit     \b Integer value of the credit to be added. Can be negative.
    #
    def addCredit(self, account_id, credit):
        self.cur.execute("SELECT EXISTS(SELECT * FROM transacts)")
        if self.cur.fetchone()[0] != 0:
            self.cur.execute("INSERT INTO transacts VALUES((SELECT MAX(tid) FROM transacts)+1,?,?,?,?,?)",\
                             [int(account_id), 0, 1, int(credit), datetime.datetime.now()])
        else:
            self.cur.execute("INSERT INTO transacts VALUES(1,?,?,?,?,?)",\
                             [int(account_id), 0, 1, int(credit), datetime.datetime.now()])
        self.dbcon.commit()


    ## Adds a new drink to drinks table.
    #
    #  \param nspdfek \b List[7] containing: string  containing the name of the drink
    #                                        integer representing the price at which the beverage will be sold
    #                                        integer representing the price at which the beverage is purchased
    #                                        integer containing the value of an empty bottle
    #                                        integer number of full bottles available
    #                                        integer number of empty bottles
    #                                        bool    if drink should show up in kings() call
    #
    def addDrink(self, nspdfek=[]):
        nspdfek = [None] + nspdfek
        nspdfek.insert(7, False)
        nspdfek[1] = nspdfek[1].decode('utf-8')
        self.cur.execute("INSERT INTO drinks VALUES(?,?,?,?,?,?,?,?,?)", nspdfek)
        self.dbcon.commit()


    ## Creates one db-entry per drink in transacts with the same tid.
    #
    #  \param account_id        \b Integer that corresponds to an aid in table accounts
    #  \param drinkIDs_amounts  \b List that contains tuples (did, amount) to know the amount of drinks consumed
    #
    def consumeDrinks(self, account_id, drinkIDs_amounts):
        # Get drink informations from drinks table
        drink_infos = {}
        for item in drinkIDs_amounts:
            self.cur.execute("SELECT sales_price,bottles_full,bottles_empty FROM drinks WHERE did=?", [item[0]])
            data = self.cur.fetchone()
            if not data:
                self._logger.error("DrinkID %d in table drinks not found. Can't consume this drink :(", item[0])
                return
            # Check if drink ist listed multiple times
            if item[0] in drink_infos:
                buf = list(drink_infos[item[0]])
                buf[0] += item[1]
                drink_infos[item[0]] = tuple(buf)
            else:
                drink_infos[item[0]] = ((item[1]),) + data

        # get max(tid)
        new_tid = 0
        for item in self.cur.execute("SELECT MAX(tid) FROM transacts"):
            new_tid = item[0]+1;
        if new_tid == sys.maxint:
            self._logger.error("TID in table transacts reached maxINT! Can't commit any transactions X_X")
            return

        # update transacts and drinks tables
        for k,v in drink_infos.iteritems():
            self.cur.execute("INSERT INTO transacts VALUES(?,?,?,?,?,?)", [new_tid, account_id, k, v[0], -v[1], datetime.datetime.now()])
            self.cur.execute("UPDATE drinks SET bottles_full=?,bottles_empty=? WHERE did=?", [v[2]-v[0], v[3]+v[0], k])
        self.dbcon.commit()

        # update kings table
        self.updateKing(account_id, drinkIDs_amounts)


    ## Deletes all references to account_id in the database
    #
    #  \param account_id \b Integer that corresponds to an aid in table accounts
    #
    def delAccount(self, account_id):
        # delete account from account-table
        self.cur.execute("DELETE FROM accounts WHERE aid=?", [account_id])
        # delete all transactions related to the account
        self.cur.execute("DELETE FROM transacts WHERE aid=?", [account_id])
        #delete account from kings
        self.cur.execute("DELETE FROM kings WHERE aid=?", [account_id])
        self.dbcon.commit()


    ## Marks the drink as deleted in table drinks
    #
    #  \param drink_id \b Integer containing the did from table drinks
    #
    #TODO: delete drink if there are no transactions attached
    def delDrink(self, drink_id):
        self.cur.execute("UPDATE drinks SET deleted=1, kings=0 WHERE did=?", [drink_id])
        self.dbcon.commit()


    ## Returns a list of all available drinks
    #
    #  \return \b List of ntuples containing all columns form table drinks except deleted
    #
    def drinks(self):
        self.cur.execute("SELECT did, name, sales_price, purchase_price, deposit, bottles_full, bottles_empty, kings \
                            FROM drinks \
                           WHERE deleted=0 \
                        ORDER BY name ASC")
        return self.cur.fetchall()


    ## Returns those who have consumed the most for each drink
    #
    #  For every relevant drink name and username calculate the amount
    #  and keep only the user with MAX(quaffed)
    #
    #  \return \b List of ntuples (accounts.name, drinks.name, quaffed) for every
    #             drink with drinks.kings=True and quaffed = MAX(quaffed)ordered
    #             ascending by accounts.name
    #
    def kings(self):
        self.cur.execute("SELECT name, dname, MAX(total)\
                          FROM (SELECT k.aid, d.name AS dname, SUM(k.quaffed) AS total\
                                FROM kings AS k\
                                JOIN drinks AS d ON k.did=d.did\
                                WHERE d.name IN (SELECT DISTINCT name FROM drinks WHERE kings=1 AND deleted=0)\
                                GROUP BY k.aid, d.name) AS b\
                          JOIN accounts AS a ON b.aid=a.aid\
                          GROUP BY dname\
                          ORDER BY name ASC")
        return self.cur.fetchall()


    ## Sets the name from account_id to name
    def setAccountName(self, account_id, name):
        self.cur.execute("UPDATE accounts SET name=? WHERE aid=?", [name.decode('utf-8'), account_id])
        self.dbcon.commit()


    ## Sets columns of drinks table, depending on values in nspdfek
    def setDrink(self, drink_id, nspdfek=[]):
        nspdfek[0] = nspdfek[0].decode('utf-8')
        if len(nspdfek) == 7:
            nspdfek.append(drink_id)
            self.cur.execute("UPDATE drinks SET name=?,\
                                                sales_price=?,\
                                                purchase_price=?,\
                                                deposit=?,\
                                                bottles_full=?,\
                                                bottles_empty=?,\
                                                kings=? \
                                            WHERE did=?", nspdfek)
            self.dbcon.commit()
        else:
            self._logger.debug("Invalid parameter count (%i), nothing done!", len(nspdfek)-1)


    ## Returns a list including all transactions of an user
    #
    #  \param account_id \b Integer that corresponds to an aid in table accounts
    #  \return           \b List of ntuples (tid, drinks.name, count, value, date).
    #                       tid can occur multiple times and value is the cost of
    #                       one bottle, i.e. it is negative.
    #
    def transactions(self, account_id):
        self.cur.execute("SELECT tid, name, count, value, date FROM (SELECT * FROM transacts WHERE aid=?) AS t \
                 LEFT OUTER JOIN drinks \
                              ON drinks.did=t.did \
                        ORDER BY tid ASC", [account_id])
        balance_list = self.cur.fetchall()
        return balance_list


    ## Reverses a credit/debit transaction
    #
    #  The given transaction will be deleted from transacts and if
    #  drinks were consumed the drinks and kings tables will be
    #  updated to reflect the reversion.
    #
    #  \param transact_id \b Integer containing the tid to be deleted
    #                        from table transacts.
    def undoTransaction(self, transact_id):
        self.cur.execute("SELECT aid, did, count FROM transacts WHERE tid=?", [transact_id])
        aids_dids_counts = self.cur.fetchall()
        # Update drinks table
        for item in aids_dids_counts:
            if item[1] != 0:
                self.cur.execute("SELECT bottles_full, bottles_empty FROM drinks WHERE did=?",[item[1]])
                full_empty = self.cur.fetchone()
                self.cur.execute("UPDATE drinks SET bottles_full=?, bottles_empty=? WHERE did=?",
                                 [full_empty[0]+item[2], full_empty[1]-item[2], item[1]])
        # Update kings table
        for item in aids_dids_counts:
            if item[1] != 0:
                self.cur.execute("SELECT quaffed FROM kings WHERE aid=? AND did=?", [item[0], item[1]])
                actual_quaffed = self.cur.fetchone()
                if actual_quaffed:
                    self.cur.execute("UPDATE kings SET quaffed=? WHERE aid=? AND did=?", [actual_quaffed[0]-item[2], item[0], item[1]])
        # Update transacts table
        self.cur.execute("DELETE FROM transacts WHERE tid=?", [transact_id])
        self.dbcon.commit()


    ## Adds the consumed amount of drinks to the quaffed value in the table kings
    #
    #  \param account_id        \b Integer that corresponds to an aid in table accounts
    #  \param drinkIDs_amounts  \b List that contains tuples (did, amount) to know the amount of drinks consumed
    #
    def updateKing(self, account_id, drinkIDs_amounts):
        for item in drinkIDs_amounts:
            self.cur.execute("SELECT quaffed FROM kings WHERE aid=? AND did=?", [account_id, item[0]])

            # check if account,drink combination is already in database
            actual_quaffed = self.cur.fetchone()
            if actual_quaffed:
                # add number of quaffed drinks to existing number
                self.cur.execute("UPDATE kings SET quaffed=? WHERE aid=? AND did=?",\
                                  [actual_quaffed[0] + item[1], account_id, item[0]])
            else:
                self.cur.execute("INSERT INTO kings VALUES(?,?,?)", [account_id, item[0], item[1]])
        self.dbcon.commit()
