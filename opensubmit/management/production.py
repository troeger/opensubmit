# Administration script functionality on the production system
# We cover some custom actions and a small subset of django-admin here

import os, urllib
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
APACHE_CONFIG_FILE = CONFIG_PATH+'/apache24.conf'

def django_admin(args):
    '''
        Run something like it would be done through Django's manage.py.
    '''
    from django.core.management import execute_from_command_line
    execute_from_command_line([sys.argv[0]]+args)

def apache_config(config):
    ''' 
        Generate a valid Apache configuration file, based on the given settings.
    '''
    from opensubmit import settings
    f = open(APACHE_CONFIG_FILE,'w')
    print "Generating Apache configuration in "+APACHE_CONFIG_FILE
    if len(settings.FORCE_SCRIPT_NAME)>0:
        script_url_path = '/'+settings.FORCE_SCRIPT_NAME+'/'
    else:
        script_url_path = '/'
    text = """
    # OpenSubmit Configuration for Apache 2.4
    # These directives are expected to live in some <VirtualHost> block

    Alias {script}static/ {static_path}/
    <Directory {static_path}>
         Require all granted
    </Directory>
    WSGIScriptAlias {script} {install_path}/wsgi.py
    WSGIPassAuthorization On
    <Directory {install_path}>
         <Files wsgi.py>
              Require all granted
         </Files>
    </Directory>
    """.format( script=script_url_path, 
                static_path=settings.STATIC_ROOT,
                install_path=settings.SCRIPT_ROOT)
    f.write(text)
    f.close()

def check_web_config_consistency(config):
    '''
        Check the web application config file for consistency.
    '''
    login_conf_deps = {
        'LOGIN_TWITTER': ['LOGIN_TWITTER_OAUTH_KEY', 'LOGIN_TWITTER_OAUTH_SECRET'],
        'LOGIN_GOOGLE': ['LOGIN_GOOGLE_OAUTH_KEY', 'LOGIN_GOOGLE_OAUTH_SECRET'],
        'LOGIN_GITHUB': ['LOGIN_GITHUB_OAUTH_KEY', 'LOGIN_GITHUB_OAUTH_SECRET']
    }

    print "Checking configuration of the OpenSubmit web application..."
    # Check configured host
    try:
        urllib.urlopen(config.get("server", "HOST"))
    except Exception as e:
        # This may be ok, when the admin is still setting up to server
        print "WARNING: The configured HOST seems to be invalid: "+str(e)
    # Check configuration dependencies
    for k, v in login_conf_deps.iteritems():
        if config.getboolean('login', k):
            for needed in v:
                if len(config.get('login', needed)) < 1:
                    print "ERROR: You have enabled %s in settings.ini, but %s is not set."%(k, needed)
                    return False
    # Check media path
    if not os.path.exists(config.get('server', 'MEDIA_ROOT')):
        print "ERROR: The configured path for MEDIA_ROOT does not exist. (%s)"%config.get('server', 'MEDIA_ROOT')
        return False
    # Prepare empty log file, in case the web server has no creation rights
    log_file = config.get('server', 'LOG_FILE')
    print "Preparing log file at "+log_file
    with open(log_file, 'a'):
        os.utime(log_file, None)
    # everything ok
    return True


def check_web_config():
    '''
        Everything related to configuration file checks.
    '''
    print "Looking for config files ..."
    config = RawConfigParser()
    try:
        config.readfp(open(WEB_CONFIG_FILE)) 
        print "Config file found at "+WEB_CONFIG_FILE
        return config
    except IOError:
        print "ERROR: Seems like the config file %s does not exist."%WEB_CONFIG_FILE
        print "       I am creating a new one. Please edit it and re-run this command."
        if not os.path.exists(CONFIG_PATH):
            os.makedirs(CONFIG_PATH)
        orig = resource_filename(Requirement.parse("OpenSubmit"),WEB_TEMPLATE)
        shutil.copy(orig,WEB_CONFIG_FILE)
        return None    # Manual editing is needed before further proceeding with the fresh file

def check_web_db():
    '''
        Everything related to database checks and updates.
    '''
    print "Testing for neccessary database migrations..."
    django_admin(["migrate"])             # apply schema migrations
    django_admin(["fixperms"])            # Fix django backend user permissions, if needed
    return True

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

def check_warnings():
    if warning_counter > 0:
        print("There were warnings, please check the output above.")

def console_script():
    '''
        The main entry point for the production administration script 'opensubmit', installed by setuptools.
    '''
    if len(sys.argv) == 1:
        print "opensubmit [install_web|install_executor|executor|help]"
        exit(0)

    if "help" in sys.argv:
        print "install_web:      Check config files and database for correct installation of the OpenSubmit web server."
        print "install_executor: Check config files and registration of a OpenSubmit test machine."
        print "executor:         Fetch and run code to be tested from the OpenSubmit web server. Suitable for crontab."
        print "help:             Print this help"
        exit(0)

    if "install_web" in sys.argv:
        config = check_web_config()
        if not config:
            return          # Let them first fix the config file before trying a DB access
        if not check_web_config_consistency(config):
            return
        if not check_web_db():
            return
        print("Preparing static files for web server...")
        django_admin(["collectstatic","--noinput", "-v 0"])
        apache_config(config)
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


