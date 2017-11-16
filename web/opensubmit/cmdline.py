'''
    This module contains administrative functionality that is available as command-line tool "opensubmit-web".
'''

import os, pwd, grp, urllib.request, urllib.parse, urllib.error, sys, shutil
from configparser import RawConfigParser
from pkg_resources import Requirement, resource_filename

DEFAULT_CONFIG='''
# This is the configuration file for the OpenSubmit tool.
# https://github.com/troeger/opensubmit
#
# It is expected to be located at:
# /etc/opensubmit/settings.ini (on production system), or
# ./settings_dev.ini (on developer systems)

[general]
# Enabling this will lead to detailed developer error information as result page
# whenever something goes wrong on server side.
# In production systems, you never want that to be enabled, for obvious security reasons.
DEBUG: False

[server]
# This is the root host url were the OpenSubmit tool is offered by your web server.
# If you serve the content from a subdirectory, please specify it too, without leading or trailing slashes,
# otherwise leave it empty.
HOST: ***not configured***
HOST_DIR: submit

# This is the local directory were the uploaded assignment attachments are stored.
# Your probably need a lot of space here.
# Make sure that the path starts and ends with a slash.
MEDIA_ROOT: ***not configured***

# This is the logging file. The web server must be allowed to write into it.
LOG_FILE: /var/log/opensubmit.log

# This is the timezone all dates and deadlines are specified in.
# This setting overrides your web server default for the time zone.
# The list of available zones is here:
# http://en.wikipedia.org/wiki/List_of_tz_database_time_zones
TIME_ZONE: Europe/Berlin

# This is a unique string needed for some of the security features.
# Change it, the value does not matter.
SECRET_KEY: uzfp=4gv1u((#hb*#o3*4^v#u#g9k8-)us2nw^)@rz0-$2-23)

[database]
# The database you are using. Possible choices are
# - postgresql_psycopg2
# - mysql
# - sqlite3
# - oracle
DATABASE_ENGINE: sqlite3

# The name of the database. It must be already available for being used.
# In SQLite, this is the path to the database file.
DATABASE_NAME: database.sqlite

# The user name for accessing the database. Not needed for SQLite.
DATABASE_USER:

# The user password for accessing the database. Not needed for SQLite.
DATABASE_PASSWORD:

# The host name for accessing the database. Not needed for SQLite.
# An empty settings means that the database is on the same host as the web server.
DATABASE_HOST:

# The port number for accessing the database. Not needed for SQLite.
# An empty settings means that the database default use used.
DATABASE_PORT:

[executor]
# The shared secret with the job executor. This ensures that only authorized
# machines can fetch submitted solution attachments for validation, and not
# every student ...
# Change it, the value does not matter.
SHARED_SECRET: 49846zut93purfh977TTTiuhgalkjfnk89

[admin]
# The administrator for this installation. Course administrators
# are stored in the database, so this is only the technical contact for problems
# with the tool itself. Exceptions that happen due to bugs or other issues
# are sent to this address.
ADMIN_NAME: Super Admin
ADMIN_EMAIL: root@localhost

[login]
# Enables or disables login with OpenID
LOGIN_OPENID: True

# Text shown beside the OpenID login icon.
LOGIN_DESCRIPTION: StackExchange

# OpenID provider URL to be used for login.
OPENID_PROVIDER: https://openid.stackexchange.com

# Enables or disables login with Twitter
LOGIN_TWITTER: False

# OAuth application credentials for Twitter
LOGIN_TWITTER_OAUTH_KEY:
LOGIN_TWITTER_OAUTH_SECRET:

# Enables or disables login with Google
LOGIN_GOOGLE: False

# OAuth application credentials for Google
LOGIN_GOOGLE_OAUTH_KEY:
LOGIN_GOOGLE_OAUTH_SECRET:

# Enables or disables login with GitHub
LOGIN_GITHUB: False

# OAuth application credentials for GitHub
LOGIN_GITHUB_OAUTH_KEY:
LOGIN_GITHUB_OAUTH_SECRET:

# Enables or diables login through Apache 2.4 mod_shib authentication
LOGIN_SHIB: False
LOGIN_SHIB_DESCRIPTION: Shibboleth
'''

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
        print("Renamed existing Apache config file to "+outputfile+".old")

    from opensubmit import settings
    f = open(outputfile,'w')
    print("Generating Apache configuration in "+outputfile)
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
    try:
        if directory != '':
            if not os.path.exists(directory):
                os.makedirs(directory, 0o775)   # rwxrwxr-x
    except:
        print("ERROR: Could not create {0}. Please use sudo or become root.".format(directory))

def check_file(filepath):
    '''
        - Checks if the parent directories for this path exist.
        - Checks that the file exists.
        - Donates the file to the web server user.

        TODO: This is Debian / Ubuntu specific.
    '''
    check_path(os.path.dirname(filepath))
    if not os.path.exists(filepath):
        print("WARNING: File does not exist. Creating it: %s"%filepath)
        open(filepath, 'a').close()
    try:
        print("Setting access rights for %s for www-data user"%(filepath))
        uid = pwd.getpwnam("www-data").pw_uid
        gid = grp.getgrnam("www-data").gr_gid
        os.chown(filepath, uid, gid)
        os.chmod(filepath, 0o660) # rw-rw---
    except:
        print("WARNING: Could not adjust file system permissions for %s. Make sure your web server can write into it."%filepath)

def check_web_config_consistency(config):
    '''
        Check the web application config file for consistency.
    '''
    login_conf_deps = {
        'LOGIN_TWITTER': ['LOGIN_TWITTER_OAUTH_KEY','LOGIN_TWITTER_OAUTH_SECRET'],
        'LOGIN_GOOGLE':  ['LOGIN_GOOGLE_OAUTH_KEY', 'LOGIN_GOOGLE_OAUTH_SECRET'],
        'LOGIN_GITHUB':  ['LOGIN_GITHUB_OAUTH_KEY', 'LOGIN_GITHUB_OAUTH_SECRET']
    }

    print("Checking configuration of the OpenSubmit web application...")
    # Let Django's manage.py load the settings file, to see if this works in general
    django_admin(["check"])
    # Check configured host
    try:
        urllib.request.urlopen(config.get("server", "HOST"))
    except Exception as e:
        # This may be ok, when the admin is still setting up to server
        print("The configured HOST seems to be invalid at the moment: "+str(e))
    # Check configuration dependencies
    for k, v in list(login_conf_deps.items()):
        if config.getboolean('login', k):
            for needed in v:
                if len(config.get('login', needed)) < 1:
                    print("ERROR: You have enabled %s in settings.ini, but %s is not set."%(k, needed))
                    return False
    # Check media path
    check_path(config.get('server', 'MEDIA_ROOT'))
    # Prepare empty log file, in case the web server has no creation rights
    log_file = config.get('server', 'LOG_FILE')
    print("Preparing log file at "+log_file)
    check_file(log_file)
    # If SQLite database, adjust file system permissions for the web server
    if config.get('database','DATABASE_ENGINE') == 'sqlite3':
        name = config.get('database','DATABASE_NAME')
        if not os.path.isabs(name):
            print("ERROR: Your SQLite database name must be an absolute path. The web server must have directory access permissions for this path.")
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
    print("Looking for config file at {0} ...".format(WEB_CONFIG_FILE))
    config = RawConfigParser()
    try:
        config.readfp(open(WEB_CONFIG_FILE))
        return config
    except IOError:
        print("ERROR: Seems like the config file does not exist.")
        print("       I am creating a new one. Please edit it and re-run this command.")
    # Create fresh config file
    try:
        check_path(config_path)
        f=open(WEB_CONFIG_FILE,'wt')
        f.write(DEFAULT_CONFIG)
        f.close()
        check_file(WEB_CONFIG_FILE)
        return None    # Manual editing is needed before further proceeding with the fresh file
    except FileNotFoundError:
        print("ERROR: Could not create config file at {0}. Please use sudo or become root.".format(WEB_CONFIG_FILE))
        return None

def check_web_db():
    '''
        Everything related to database checks and updates.
    '''
    print("Testing for neccessary database migrations...")
    django_admin(["migrate"])             # apply schema migrations
    print("Checking the OpenSubmit permission system...")
    django_admin(["fixperms"])            # configure permission system, of needed
    return True

def configure(fsroot='/'):
    print("Inspecting OpenSubmit configuration ...")
    config = check_web_config(fsroot+'etc/opensubmit')
    if not config:
        return          # Let them first fix the config file before trying a DB access
    if not check_web_config_consistency(config):
        return
    if not check_web_db():
        return
    print("Preparing static files for web server...")
    django_admin(["collectstatic","--noinput","--clear","-v 0"])
    apache_config(config, fsroot+'etc/opensubmit/apache24.conf')


def print_help():
    print("configure:           Check config files and database for correct installation of the OpenSubmit web server.")
    print("fixperms:            Check and fix student and tutor permissions")
    print("fixchecksums:        Re-create all student file checksums (for duplicate detection)")
    print("makeadmin   <email>: Make this user an admin with backend rights.")
    print("makeowner   <email>: Make this user a course owner with backend rights.")
    print("maketutor   <email>: Make this user a course tutor with backend rights.")
    print("makestudent <email>: Make this user a student without backend rights.")

def console_script(fsroot='/'):
    '''
        The main entry point for the production administration script 'opensubmit-web', installed by setuptools.
        The argument allows the test suite to override the root of all paths used in here.
    '''

    if len(sys.argv) == 2 and "configure" in sys.argv[1]:
        configure(fsroot)

    elif len(sys.argv) == 2 and sys.argv[1] in ['fixperms', 'fixchecksums']:
        django_admin([sys.argv[1]])

    elif len(sys.argv) == 3 and  sys.argv[1] in ['makeadmin', 'makeowner', 'maketutor', 'makestudent']:
        django_admin([sys.argv[1], sys.argv[2]])

    else:
        print_help()

if __name__ == "__main__":
    console_script()
