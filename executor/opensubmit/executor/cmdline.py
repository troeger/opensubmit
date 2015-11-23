# Administration script functionality on the production system

import os, urllib, sys, shutil, uuid
from ConfigParser import RawConfigParser
from pkg_resources import Requirement, resource_filename

#TODO: DRY is missing here, the same paths are stored in settings.py
CONFIG_PATH = '/etc/opensubmit'
EXECUTOR_CONFIG_FILE = CONFIG_PATH+'/executor.ini'
EXECUTOR_TEMPLATE = "opensubmit/executor.cfg.template"     # relative to package path

UUID_PLACEHOLDER = "<replaced by opensubmit-exec configure>"

def check_exec_config_consistency(config):
    '''
        Check the executor config file for consistency.
    '''
    print "Checking configuration of the OpenSubmit executor..."
    # Check configured host
    try:
        urllib.urlopen(config.get("Server", "url"))
    except Exception as e:
        print "ERROR: The configured OpenSubmit server URL seems to be invalid: "+str(e)
        return False
    # Check UUID to be set
    if config.get("Server", "uuid") == UUID_PLACEHOLDER:
        print "ERROR: The machine UUID is not set, please re-create the config file with opensubmit-exec."
        return False
    return True

def check_executor_config():
    '''
        Everything related to the executor configuration file.
    '''
    print "Looking for config files..."
    config = RawConfigParser()
    try:
        config.readfp(open(EXECUTOR_CONFIG_FILE))
        print "Config file found at "+EXECUTOR_CONFIG_FILE
        return config
    except IOError:
        print "ERROR: Seems like the config file %s does not exist."%EXECUTOR_CONFIG_FILE
        print "       I am creating a new one, don't forget to edit it !"
        print "       Re-run this script again afterwards."
        try:
            os.makedirs(CONFIG_PATH)
        except:
            pass    # if directory already exists
        orig = resource_filename(Requirement.parse("opensubmit-exec"),EXECUTOR_TEMPLATE)
        shutil.copy(orig,EXECUTOR_CONFIG_FILE)
        # Generate installation UID for this machine as identifier
        final_config = open(EXECUTOR_CONFIG_FILE, 'r')
        data = final_config.read().replace("uuid="+UUID_PLACEHOLDER, "uuid="+str(uuid.uuid1()))
        final_config = open(EXECUTOR_CONFIG_FILE, 'w')
        final_config.write(data)
        final_config.close()
        return None    # Manual editing is needed before further proceeding with the fresh file

def check_warnings():
    if warning_counter > 0:
        print("There were warnings, please check the output above.")

def console_script():
    '''
        The main entry point for the production administration script 'opensubmit-exec', installed by setuptools.
    '''
    if len(sys.argv) == 1:
        print "opensubmit-exec [configure|run|help]"
        exit(0)

    if "help" in sys.argv:
        print "configure: Check config files and registration of a OpenSubmit test machine."
        print "run:       Fetch and run code to be tested from the OpenSubmit web server. Suitable for crontab."
        print "unlock:    Break the script lock, because of crashed script."    
        print "help:      Print this help"
        exit(0)

    if "configure" in sys.argv:
        config = check_executor_config()
        if not config:
            return
        if not check_exec_config_consistency(config):
            return
        print "Registering OpenSubmit executor..."
        from . import send_config
        send_config(EXECUTOR_CONFIG_FILE)
        exit(0)
    if "unlock" in sys.argv:
        from . import read_config
        config=read_config(EXECUTOR_CONFIG_FILE)
        try:
            from lockfile import FileLock
            FileLock(config.get("Execution","pidfile")).break_lock()
            print "Lock removed."
        except Exception as e:
            print "ERROR breaking lock: " + str(e)
        
        
    if "run" in sys.argv:
        from . import run
        run(EXECUTOR_CONFIG_FILE)
