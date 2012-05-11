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
    print "Please install python-yaml or check the environment variables!\n"
    sys.exit(1)


class BimiConfig:
    _logger = logging.getLogger('BimiConfig')
    _config_file_path = os.path.expanduser(os.path.join("~",".config","bimiTool","bmt_config.yaml"))

    # Initialize default configuration
    #_config_dict = {'db_path': os.path.join(os.path.dirname(_config_file_path),"bmt_db.sqlite"),\
    script_dir = os.path.realpath(os.path.dirname(sys.argv[0]))
    _config_dict = {'db_path': os.path.join(script_dir,'bmt_db.sqlite'),\
                    'gui_path' : os.path.join(script_dir,'bmt.glade'),\
                    'mail_path' : os.path.join(script_dir,'mail.txt'),\
                    'currency' : '€'.decode('utf-8'),
                    'log_level' : logging.INFO}


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
    #  is not a yaml file. Look out for IOError and YAMLError.
    #
    #  \param conf_file_path \b String (const) containing the path to the conf file
    #
    @staticmethod
    def load(conf_file_path=None):
        if conf_file_path is not None:
            conf_file_path = os.path.expanduser(str(conf_file_path))
            if os.path.exists(conf_file_path):
                BimiConfig._config_file_path = conf_file_path
            else:
                BimiConfig._logger.error('File %s not found! Using default configuration.', conf_file_path)
                raise IOError('File %s not found! Using default configuration.', conf_file_path)

        try:
            yaml_file = open(BimiConfig._config_file_path, 'r')
        except IOError as io:
            BimiConfig._logger.debug('Reading file %s failed! Using default configuration. [io: %s]', BimiConfig._config_file_path, io)
            return

        try:
            BimiConfig._config_dict = yaml.safe_load(yaml_file)
        except yaml.YAMLError as yamlerr:
            yaml_file.close()
            BimiConfig._logger.error('File %s is not a valid! [yaml: %s]', BimiConfig._config_file_path, yamlerr)
            raise yaml.YAMLError('%s',yamlerr)
        yaml_file.close()


    ## Returns a copy of the specified option or None if option was not found
    #
    #  \param option \b String (const) key from dictionary _config_dict.
    #  \return \b Object associated to the option string or None if option wasn't found
    #
    @staticmethod
    def option(option):
        try:
            return deepcopy(BimiConfig._config_dict[option])
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
            BimiConfig._logger.debug('Option %s not in _config_dict. Adding it.',option)
        BimiConfig._config_dict[option] = deepcopy(value)
        BimiConfig.writeConfig()

    ## Writes _config_dict to a yaml file
    #
    #  Raises exceptions if config can't be written. Look out
    #  for OSError and IOError.
    #
    @staticmethod
    def writeConfig():
        # Check if directories exist, if not create them
        if not os.path.isdir(os.path.dirname(BimiConfig._config_file_path)):
            try:
                os.makedirs(os.path.dirname(BimiConfig._config_file_path))
            except OSError as oe:
                BimiConfig._logger.error('Not possible to create directory %s! Config not safe :Q [os: %s]',\
                                         os.path.dirname(BimiConfig._config_file_path), oe)
                raise OSError('Not possible to create directory %s! Config not safe D: [os: %s]',\
                               os.path.dirname(BimiConfig._config_file_path), oe)

        # Write dictionary to yaml file
        try:
            yaml_file = open(BimiConfig._config_file_path, 'w')
        except IOError as io:
            BimiConfig._logger.error("Oh noes, file %s not writeable! [io: %s]", BimiConfig._config_file_path, io)
            raise IOError("Oh noes, file %s not writeable! [io: %s]", BimiConfig._config_file_path, io)

        yaml.safe_dump(BimiConfig._config_dict, stream=yaml_file, width=70, indent=4)
        yaml_file.close()
