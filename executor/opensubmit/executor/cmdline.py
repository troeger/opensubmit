# Administration script functionality on the production system

import sys

from . import CONFIG_FILE_DEFAULT
from .server import fetch_job, send_hostinfo
from .execution import kill_longrunning, run
from .locking import ScriptLock, break_lock
from .result import FailResult
from .config import read_config, has_config, create_config, check_config

import logging
logger = logging.getLogger('opensubmit.executor')

def fetch_and_run(config):
    '''
    Main operation of the daemon mode. Also used by the test suite with its
    own configuration.

    Returns boolean failure indication about preparation step.
    '''
    sub = fetch_job(config) 
    if sub:
        prep_result=sub.prepare()
        if type(prep_result) is FailResult:
            sub.send_result(prep_result)
            return False
        else:
            validation_result=run(sub)
            sub.send_result(validation_result)
            return True

def console_script():
    '''
        The main entry point for the production administration script 'opensubmit-exec', installed by setuptools.
    '''
    if len(sys.argv) == 1:
        print("opensubmit-exec [configure|run|unlock|help] [-c config_file]")
        exit(0)

    if "help" in sys.argv[1]:
        print("configure:        Check config files and registration of a OpenSubmit test machine.")
        print("run:              Fetch and run code to be tested from the OpenSubmit web server. Suitable for crontab.")
        print("unlock:           Break the script lock, because of crashed script."    )
        print("help:             Print this help")
        print("-c config_file    Configuration file to be used (default: {0})".format(CONFIG_FILE_DEFAULT))
        exit(0)

    if len(sys.argv)>2 and sys.argv[2]=="-c":
        config_fname=sys.argv[3]
    else:
        config_fname=CONFIG_FILE_DEFAULT

    if "configure" in sys.argv[1]:
        print("Checking configuration of the OpenSubmit executor...")        
        if has_config(config_fname):
            print("Config file found at "+config_fname)
            config=read_config(config_fname)
            if not check_config(config):
                exit(1)
        else:
            print("ERROR: Seems like the config file %s does not exist."%config_fname)
            print("       I am creating a new one, don't forget to edit it !")
            print("       Re-run this script again afterwards.")
            if create_config(config_fname):
                print("File created.")
                exit(0)
            else:
                exit(1)

        send_hostinfo(config)
        exit(0)

    if "unlock" in sys.argv[1]:
        config=read_config(config_fname)
        break_lock(config)
        exit(0)

    if "run" in sys.argv[1]:
        config=read_config(config_fname)
        kill_longrunning(config)
        with ScriptLock(config):
            fetch_and_run(config)
        exit(0)

console_script()
