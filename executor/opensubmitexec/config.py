'''
    Common functions dealing with the library configuration.
'''

import platform
import os
import uuid
from configparser import ConfigParser, RawConfigParser

from urllib.request import urlopen

from . import CONFIG_FILE_DEFAULT

import logging
logger = logging.getLogger('opensubmitexec')


DEFAULT_SETTINGS = {
    'Execution': {
        'cleanup': 'True',                       # Override for disabling file cleanup
        'message_size': '10000',                 # Override for result text limit
        'timeout': '3600',                       # Override for execution timeout
        # Command to compile something on this machine
        'compile_cmd': 'make',
        'directory': '/tmp/',                    # Base directory for temporary directories
        'pidfile': '/tmp/executor.lock',         # Lock file for script lock
        # Execution environment for validation scripts
        'script_runner': '/usr/bin/env python3'
    },
    'Server': {
        'url': 'http://localhost:8000',          # OpenSubmit web server
        # Shared secret with OpenSubmit web server
        'secret': '49846zut93purfh977TTTiuhgalkjfnk89',
        'uuid': uuid.getnode()
    },
    'Logging': {
        'format': '%%(asctime)-15s (%%(process)d): %%(message)s',
        'file': '/tmp/executor.log',
        'to_file': 'False',
        'level': 'DEBUG'
    }
}

DEFAULT_SETTINGS_FLAT = {}
for outer_key, inner_dict in DEFAULT_SETTINGS.items():
    for key, value in inner_dict.items():
        DEFAULT_SETTINGS_FLAT[key] = value

DEFAULT_FILE_CONTENT = '''
[Server]

# The OpenSubmit server
url={url}

# Shared secret, must match to /etc/opensubmit/settings.ini on the web server
secret={secret}

# UUID of this executor
uuid={uuid}

[Execution]

# Place where downloaded archives are extracted, compiled and validated
# The executor will create sub-directories per fetched job
directory={directory}

# Delete all student files after the executor did its work.
# Disable this to debug problems that are only reproducible by running the
# downloaded student code manually.
# Disabling this will obviousely fill your hard disk very quickly.
cleanup={cleanup}

# Script interpreter to be used for the validation scripts
script_runner={script_runner}

# Validators can decide to run alone on the machine.
# In this case, the following lock file is used.
pidfile={pidfile}

# Whatver runs under this account is not allowed to run longer than this time
# This is the ultimate safeguard for deadlocks and submission processes going mad
# This also means that you should not use this account for interactive work
timeout={timeout}

# Limit the size of result message to a number of bytes, because of database entry
# size. <=0 means no limit, any positive value limits the message size
message_size={message_size}

# Customize the compilation command to be executed
compile_cmd={compile_cmd}

[Logging]

# Logging format, as described in the Python logging module documentation
format={format}

# Target file for logging information
# only needed if to_file=True
file={file}

# If false, logging goes to console
to_file={to_file}

# Log level, as described in the Python logging module documentation
level={level}
'''


def read_config(config_file=CONFIG_FILE_DEFAULT, override_url=None):
    ''' Read configuration file, perform sanity check and return configuration
        dictionary used by other functions.'''
    config = ConfigParser()
    config.read_dict(DEFAULT_SETTINGS)

    try:
        config.readfp(open(config_file))
        logger.debug("Using config file at " + config_file)
    except:
        logger.error(
            "Could not find {0}, running with defaults.".format(config_file))

    if not logger.handlers:
        # Before doing anything else, configure logging
        # Handlers might be already registered in repeated test suite runs
        # In production, this should never happen
        if config.getboolean("Logging", "to_file"):
            handler = logging.FileHandler(config.get("Logging", "file"))
        else:
            handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            config.get("Logging", "format")))
        logger.addHandler(handler)
    logger.setLevel(config.get("Logging", "level"))

    if override_url:
        config['Server']['url'] = override_url

    return config


def check_config(config):
    '''
        Check the executor config file for consistency.
    '''
    # Check server URL
    url = config.get("Server", "url")
    try:
        urlopen(url)
    except Exception as e:
        logger.error(
            "The configured OpenSubmit server URL ({0}) seems to be invalid: {1}".format(url, e))
        return False
    # Check directory specification
    targetdir = config.get("Execution", "directory")
    if platform.system() is not "Windows" and not targetdir.startswith("/"):
        logger.error(
            "Please use absolute paths, starting with a /, in your Execution-directory setting.")
        return False
    if not targetdir.endswith(os.sep):
        logger.error(
            "Your Execution-directory setting must end with a " + os.sep)
        return False
    return True


def has_config(config_fname):
    '''
    Determine if the given config file exists.
    '''
    config = RawConfigParser()
    try:
        config.readfp(open(config_fname))
        return True
    except IOError:
        return False


def create_config(config_fname, override_url=None):
    '''
    Create the config file from the defaults under the given name.
    '''
    config_path = os.path.dirname(config_fname)
    os.makedirs(config_path, exist_ok=True)

    # Consider override URL. Only used by test suite runs
    settings = DEFAULT_SETTINGS_FLAT
    if override_url:
        settings['url'] = override_url

    # Create fresh config file, including new UUID
    with open(config_fname, 'wt') as config:
        config.write(DEFAULT_FILE_CONTENT.format(**settings))
    return True
