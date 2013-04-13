#!/usr/bin/python
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
import os, argparse, subprocess, sys
from datetime import date

git_rm_files = ["test_bimibase.py",
                "run_unittest.py",
                "make_release.py",
                "session.vim"]

version_subs_files = ["CHANGELOG",
                      "README"]

# Parse arguments
parser = argparse.ArgumentParser(add_help=True, description='Readies code base for realease')
parser.add_argument('version_number',
                    default=None,
                    help="Version number for substitution",
                    type=str)
options = parser.parse_args()

script_dir = os.path.realpath(os.path.dirname(sys.argv[0]))

# Substitute version tag with given string
for item in version_subs_files:
    item = os.path.join(script_dir, item)
    subprocess.call(["sed", "-i", "s:\$version\$:" + options.version_number + ":", item])
    subprocess.call(["sed", "-i", "s:\$date\$:" + str(date.today()) + ":", item])

# Remove files from git
for item in git_rm_files:
    process = subprocess.Popen(["git", "rm", item], stdout=subprocess.PIPE)
    sys.stdout.write(process.communicate()[0])

