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
import os
import sys
import logging
from copy import copy, deepcopy

try:
    import yaml
except ImportError:
    print("----------------------------------------------------------------------")
    print "| Check your python yaml setup! (Debian/Ubuntu: install python-yaml) |"
    print("----------------------------------------------------------------------")
    sys.exit(1)


class BimiConfig:
    _logger = logging.getLogger('BimiConfig')
    _script_dir = os.path.realpath(os.path.dirname(sys.argv[0]))
    _config_file_path = os.path.join(_script_dir, 'bmt_config.yaml')

    # Initialize default configuration
    _default_config_dict = {'db_path': os.path.join(_script_dir,'bmt_db.sqlite'),
                            'gui_path': os.path.join(_script_dir,'bmt.glade'),
                            'mail_path': os.path.join(_script_dir,'mail.txt'),
                            'currency': '€'.decode('utf-8'),
                            'deposit': 0.0,
                            'num_comboboxes': 4,
                            'mail_text':\
"""Guten Tag werter Flur,
die aktuelle Abrechnung der Getränkeliste zeigt folgende Kontostände:

    $accInfos:$name $balance

des Weiteren präsentiere ich für jede Getränkeklasse die Königinnen und Könige:

    $kings:$drink-King ist $name mit $amount Flaschen

Auf ein munteres Weiterzechen!
Euer BiMi"""               }

    _config_dict = _default_config_dict
    _rm_opts = ['db_path', 'gui_path', 'mail_path'] ##< Options that will be removed before dumping the config


    ## Returns a copy of _config_dict.
    #
    #  \return \b Dictionary copy containing all config options
    #
    @staticmethod
    def config():
        return deepcopy(BimiConfig._config_dict)


    ## Loads config options from a file or sets the defaults
    #
    #  Raises exceptions if no file can be found at conf_file_path or if file
    #  is not a yaml file.
    #
    #  \param conf_file_path \b String (const) containing the path to the conf file
    #
    @staticmethod
    def load(conf_file_path=None):
        if conf_file_path is not None:
            BimiConfig._config_file_path = conf_file_path

        try:
            yaml_file = open(BimiConfig._config_file_path, 'r')
        except IOError as io:
            if conf_file_path is None:
                BimiConfig._logger.debug('No config file found. Writing one to %s', BimiConfig._config_file_path)
                BimiConfig.writeConfig()
            else:
                BimiConfig._logger.error('Reading file %s failed! Using default configuration. [io: %s]', BimiConfig._config_file_path, io)
            return

        try:
            BimiConfig._config_dict = yaml.safe_load(yaml_file)
        except yaml.YAMLError as yamlerr:
            yaml_file.close()
            BimiConfig._logger.error('%s is not a valid config file! Using default configuration. [yaml: %s]', BimiConfig._config_file_path, yamlerr)
            return
        yaml_file.close()

        if not BimiConfig._config_dict:
            BimiConfig._config_dict = BimiConfig._default_config_dict
            BimiConfig._logger.debug('No options specified in %s. Using default configuration.', BimiConfig._config_file_path)
            return
        elif type(BimiConfig._config_dict) is not dict:
            BimiConfig._config_dict = BimiConfig._default_config_dict
            BimiConfig._logger.error('%s is not a valid config file! Using default configuration. [yaml: No dictionary found!]', BimiConfig._config_file_path)
            return

        # Check for mandatory but missing options
        for k,v in BimiConfig._default_config_dict.items():
            if BimiConfig.option(k) is None:
                BimiConfig.setOption(k, v)


    ## Returns a copy of the specified option or None if option was not found
    #
    #  \param option \b String (const) key from dictionary _config_dict.
    #  \return \b Object associated to the option string or None if option wasn't found
    #
    @staticmethod
    def option(option):
        try:
            return deepcopy(BimiConfig._config_dict[str(option)])
        except KeyError:
            BimiConfig._logger.debug('Option %s not found!',option)
            return None


    ## Sets the _config_dict to a copy of the given dictionary
    #
    #  \param conf_dict \b Dictionary (const) which will be copied and used as new config
    #
    @staticmethod
    def setConfig(conf_dict):
        BimiConfig._config_dict = deepcopy(conf_dict)
        BimiConfig.writeConfig()


    ## Sets or adds a config option in _config_dict
    #
    #  \param option \b String (const) key from dictionary _config_dict
    #  \param value  \b Object (const) which will be assoziated with the key
    #
    @staticmethod
    def setOption(option, value):
        if option not in BimiConfig._config_dict:
            BimiConfig._logger.debug('Adding option %s to _config_dict.',option)
        BimiConfig._config_dict[option] = deepcopy(value)


    ## Writes _config_dict to a yaml file.
    #
    #  Options specified in _rm_opts are removed before writing.
    #  TODO: enhance this function.
    #
    @staticmethod
    def writeConfig():
        # Check if directories exist, if not create them
        if not os.path.isdir(os.path.dirname(BimiConfig._config_file_path)):
            try:
                os.makedirs(os.path.dirname(BimiConfig._config_file_path))
            except OSError as oe:
                BimiConfig._logger.error('Not possible to create directory %s! Config not safe O_O [os: %s]',\
                                         os.path.dirname(BimiConfig._config_file_path), oe)

        # Remove specified options before dumping
        dump_dict = deepcopy(BimiConfig._config_dict)
        for item in BimiConfig._rm_opts:
            try:
                del dump_dict[item]
            except KeyError:
                pass

        # Write dictionary to yaml file
        try:
            yaml_file = open(BimiConfig._config_file_path, 'w')
        except IOError as io:
            BimiConfig._logger.error("Oh noes, file %s not writeable! [io: %s]", BimiConfig._config_file_path, io)
        yaml.safe_dump(dump_dict, stream=yaml_file, default_flow_style=False, allow_unicode=True, encoding='utf-8')
        yaml_file.close()
