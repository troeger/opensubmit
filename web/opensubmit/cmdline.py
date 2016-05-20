'''
    This module contains administrative functionality that is available as command-line tool "opensubmit-web".
'''

import os, pwd, grp, urllib, sys, shutil
from ConfigParser import RawConfigParser
from pkg_resources import Requirement, resource_filename

def django_admin(args):
    '''
        Run something like it would be done through Django's manage.py.
    '''
    from django.core.management import execute_from_command_line
    from django.core.exceptions import ImproperlyConfigured
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "opensubmit.settings")
    try:
        execute_from_command_line([sys.argv[0]]+args)
    except ImproperlyConfigured as e:
        print(str(e))
        exit(-1)

def apache_config(config, outputfile):
    '''
        Generate a valid Apache configuration file, based on the given settings.
    '''
    if os.path.exists(outputfile):
        os.rename(outputfile, outputfile+".old")
        print "Renamed existing Apache config file to "+outputfile+".old"

    from opensubmit import settings
    f = open(outputfile,'w')
    print "Generating Apache configuration in "+outputfile
    subdir = (len(settings.HOST_DIR)>0)
    text = """
    # OpenSubmit Configuration for Apache 2.4
    # These directives are expected to live in some <VirtualHost> block
    """
    if subdir:
        text += "Alias /%s/static/ %s\n"%(settings.HOST_DIR, settings.STATIC_ROOT)
        text += "    WSGIScriptAlias /%s %s/wsgi.py\n"%(settings.HOST_DIR, settings.SCRIPT_ROOT)
    else:
        text += "Alias /static/ %s\n"%(settings.STATIC_ROOT)
        text += "    WSGIScriptAlias / %s/wsgi.py"%(settings.SCRIPT_ROOT)
    text += """
    WSGIPassAuthorization On
    <Directory {static_path}>
         Require all granted
    </Directory>
    <Directory {install_path}>
         <Files wsgi.py>
              Require all granted
         </Files>
    </Directory>
    """.format(static_path=settings.STATIC_ROOT, install_path=settings.SCRIPT_ROOT)

    f.write(text)
    f.close()

def check_path(directory):
    '''
        Checks if the directories for this path exist, and creates them in case.
    '''
    if directory != '':
        if not os.path.exists(directory):
            os.makedirs(directory, 0775)   # rwxrwxr-x

def check_file(filepath):
    '''
        - Checks if the parent directories for this path exist.
        - Checks that the file exists.
        - Donates the file to the web server user.

        TODO: This is Debian / Ubuntu specific.
    '''
    check_path(os.path.dirname(filepath))
    if not os.path.exists(filepath):
        print "WARNING: File does not exist. Creating it: %s"%filepath
        open(filepath, 'a').close()
    try:
        print "Setting access rights for %s for www-data user"%(filepath)
        uid = pwd.getpwnam("www-data").pw_uid
        gid = grp.getgrnam("www-data").gr_gid
        os.chown(filepath, uid, gid)
        os.chmod(filepath, 0660) # rw-rw---
    except:
        print "WARNING: Could not adjust file system permissions for %s. Make sure your web server can write into it."%filepath

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
    # Let Django's manage.py load the settings file, to see if this works in general
    django_admin(["check"])
    # Check configured host
    try:
        urllib.urlopen(config.get("server", "HOST"))
    except Exception as e:
        # This may be ok, when the admin is still setting up to server
        print "The configured HOST seems to be invalid at the moment: "+str(e)
    # Check configuration dependencies
    for k, v in login_conf_deps.iteritems():
        if config.getboolean('login', k):
            for needed in v:
                if len(config.get('login', needed)) < 1:
                    print "ERROR: You have enabled %s in settings.ini, but %s is not set."%(k, needed)
                    return False
    # Check media path
    check_path(config.get('server', 'MEDIA_ROOT'))
    # Prepare empty log file, in case the web server has no creation rights
    log_file = config.get('server', 'LOG_FILE')
    print "Preparing log file at "+log_file
    check_file(log_file)
    # If SQLite database, adjust file system permissions for the web server
    if config.get('database','DATABASE_ENGINE') == 'sqlite3':
        name = config.get('database','DATABASE_NAME')
        if not os.path.isabs(name):
            print "ERROR: Your SQLite database name must be an absolute path. The web server must have directory access permissions for this path."
            return False
        check_file(config.get('database','DATABASE_NAME'))
    # everything ok
    return True

def check_web_config(config_path):
    '''
        Try to load the Django settings.
        If this does not work, than settings file does not exist.
    '''
    WEB_CONFIG_FILE = config_path+'/settings.ini'
    WEB_TEMPLATE = "opensubmit/settings.ini.template"                   # relative to package path
    print "Looking for config files ..."
    config = RawConfigParser()
    try:
        config.readfp(open(WEB_CONFIG_FILE))
        print "Config file found at "+WEB_CONFIG_FILE
        return config
    except IOError:
        print "ERROR: Seems like the config file does not exist."
        print "       I am creating a new one. Please edit it and re-run this command."
        check_path(config_path)
        orig = resource_filename(Requirement.parse("opensubmit-web"),WEB_TEMPLATE)
        shutil.copy(orig, WEB_CONFIG_FILE)
        check_file(WEB_CONFIG_FILE)
        return None    # Manual editing is needed before further proceeding with the fresh file

def check_web_db():
    '''
        Everything related to database checks and updates.
    '''
    print "Testing for neccessary database migrations..."
    django_admin(["migrate"])             # apply schema migrations
    print "Checking the OpenSubmit permission system..."
    django_admin(["fixperms"])            # configure permission system, of needed
    return True

def console_script(fsroot='/'):
    '''
        The main entry point for the production administration script 'opensubmit-web', installed by setuptools.

        The argument allows the test suite to override the root of all paths used in here.
    '''

    if len(sys.argv) == 1:
        print "opensubmit-web [configure|createsuperuser|fixperms|fixchecksums|help]"
        exit(0)

    if "help" in sys.argv:
        print "configure:        Check config files and database for correct installation of the OpenSubmit web server."
        print "createsuperuser:  (Re-)Creates the superuser account for the OpenSubmit installation."
        print "fixperms:         Check and fix student and tutor permissions"
        print "fixchecksums:     Re-create all student file checksums (for duplicate detection)"
        print "help:             Print this help"
        return 0

    if "configure" in sys.argv:
        config = check_web_config(fsroot+'etc/opensubmit')
        if not config:
            return          # Let them first fix the config file before trying a DB access
        if not check_web_config_consistency(config):
            return
        if not check_web_db():
            return
        print("Preparing static files for web server...")
        django_admin(["collectstatic","--noinput","--clear"])
        apache_config(config, fsroot+'etc/opensubmit/apache24.conf')

    if "createsuperuser" in sys.argv:
        django_admin(["createsuperuser"])

    if "fixperms" in sys.argv:
        django_admin(["fixperms"])

    if "fixchecksums" in sys.argv:
        django_admin(["fixchecksums"])
