# Administration script functionality on the production system
# We cover some custom actions and a small subset of django-admin here

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "opensubmit.settings")

import sys, shutil
from ConfigParser import RawConfigParser
from pkg_resources import Requirement, resource_filename

#TODO: DRY is missing here, the same paths are stored in settings.py
CONFIG_PATH = '/etc/opensubmit'
WEB_CONFIG_FILE = CONFIG_PATH+'/settings.ini'
WEB_TEMPLATE = "opensubmit/settings.ini.template"                   # relative to package path
EXECUTOR_CONFIG_FILE = CONFIG_PATH+'/executor.ini'
EXECUTOR_TEMPLATE = "opensubmit/executor/executor.cfg.template"     # relative to package path

def django_admin(command):
    '''
        Run something like it would be done through Django's manage.py.
    '''
    from django.core.management import execute_from_command_line
    execute_from_command_line([sys.argv[0], command])

def check_web_config():
    '''
        Everything related to configuration file checks.
    '''
    print "Checking configuration of the OpenSubmit web application..."
    config = RawConfigParser()
    try:
        config.readfp(open(WEB_CONFIG_FILE)) 
        print "Config file found at "+WEB_CONFIG_FILE
        return True
    except IOError:
        print "ERROR: Seems like the config file %s does not exist."%WEB_CONFIG_FILE
        print "       I am creating a new one, don't forget to edit it !"
        os.makedirs(CONFIG_PATH)
        orig = resource_filename(Requirement.parse("OpenSubmit"),WEB_TEMPLATE)
        shutil.copy(orig,WEB_CONFIG_FILE)
        return False    # Manual editing is needed before further proceeding with the fresh file

def check_web_db():
    '''
        Everything related to database checks and updates.
    '''
    print "Testing for neccessary database migrations..."
    django_admin("migrate")             # apply schema migrations
    django_admin("fixperms")            # Fix django backend user permissions, if needed

def check_executor_config():
    '''
        Everything related to the executor configuration file.
    '''
    print "Checking configuration of the OpenSubmit executor..."
    config = RawConfigParser()
    try:
        config.readfp(open(EXECUTOR_CONFIG_FILE)) 
        print "Config file found at "+EXECUTOR_CONFIG_FILE
        return True
    except IOError:
        print "ERROR: Seems like the config file %s does not exist."%EXECUTOR_CONFIG_FILE
        print "       I am creating a new one, don't forget to edit it !"
        try:
            os.makedirs(CONFIG_PATH)
        except:
            pass    # if directory already exists
        orig = resource_filename(Requirement.parse("OpenSubmit"),EXECUTOR_TEMPLATE)
        shutil.copy(orig,EXECUTOR_CONFIG_FILE)
        return False    # Manual editing is needed before further proceeding with the fresh file

def console_script():
    '''
        The main entry point for the production administration script 'opensubmit', installed by setuptools.
    '''
    if len(sys.argv) == 1:
        print "opensubmit [check_web|check_executor|executor|help]"
        exit(0)

    if "help" in sys.argv:
        print "check_web:      Check config files and database for correct installation of the OpenSubmit web server."
        print "check_executor: Check config files and registration of a OpenSubmit test machine."
        print "executor:       Fetch and run code to be tested from the OpenSubmit web server. Suitable for crontab."
        print "help:           Print this help"
        exit(0)

    if "check_web" in sys.argv:
        if not check_web_config():
            return          # Let them first fix the config file before trying a DB access
        check_web_db()
        exit(0)

    if "check_executor" in sys.argv:
        if not check_executor_config():
            return
        print "Registering OpenSubmit executor..."
        from opensubmit.executor import send_config
        send_config(EXECUTOR_CONFIG_FILE)
        exit(0)

    if "executor" in sys.argv:
        from opensubmit.executor import run
        run(EXECUTOR_CONFIG_FILE)

