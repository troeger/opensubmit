'''
    This module contains administrative functionality
    that is available as command-line tool "opensubmit-web".

    All functions that demand a working Django ORM are implemented
    as Django management command and just called from here.

    Everything else is implemented here, so this file works without
    any of the install dependencies.
'''

import os
import pwd
import grp
import urllib.request
import urllib.parse
import urllib.error
import sys
import argparse
from base64 import b64encode
from configparser import RawConfigParser

DEFAULT_CONFIG = '''
# This is the configuration file for the OpenSubmit tool.
# https://github.com/troeger/opensubmit
#
# It is expected to be located at:
# /etc/opensubmit/settings.ini (on production system), or
# <project_root>/web/opensubmit/settings_dev.ini (on developer systems)
#
# For further information, check the output of 'opensubmit-web configcreate -h'.
#

[general]
DEBUG: {debug}
DEMO: {login_demo}

[server]
HOST: {server_host}
HOST_DIR: {server_hostdir}
HOST_ALIASES: {server_hostaliases}
MEDIA_ROOT: {server_mediaroot}
LOG_FILE: {server_logfile}
TIME_ZONE: {server_timezone}
SECRET_KEY: {server_secretkey}

[database]
DATABASE_ENGINE: {database_engine}
DATABASE_NAME: {database_name}
DATABASE_USER: {database_user}
DATABASE_PASSWORD: {database_password}
DATABASE_HOST: {database_host}
DATABASE_PORT: {database_port}

[executor]
# The shared secret with the job executor. This ensures that only authorized
# machines can fetch submitted solution attachments for validation, and not
# every student ...
# Change it, the value does not matter.
SHARED_SECRET: 49846zut93purfh977TTTiuhgalkjfnk89

[admin]
ADMIN_NAME: {admin_name}
ADMIN_EMAIL: {admin_email}
ADMIN_ADDRESS: {admin_address}

[login]
LOGIN_DESCRIPTION: {login_openid_title}
OPENID_PROVIDER: {login_openid_provider}
LOGIN_TWITTER_OAUTH_KEY: {login_twitter_oauth_key}
LOGIN_TWITTER_OAUTH_SECRET: {login_twitter_oauth_secret}
LOGIN_GOOGLE_OAUTH_KEY: {login_google_oauth_key}
LOGIN_GOOGLE_OAUTH_SECRET: {login_google_oauth_secret}
LOGIN_GITHUB_OAUTH_KEY: {login_github_oauth_key}
LOGIN_GITHUB_OAUTH_SECRET: {login_github_oauth_secret}
LOGIN_SHIB_DESCRIPTION: {login_shib_title}
LOGIN_DEMO: {login_demo}
'''


def django_admin(args):
    '''
        Run something like it would be done through Django's manage.py.
    '''
    from django.core.management import execute_from_command_line
    from django.core.exceptions import ImproperlyConfigured
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "opensubmit.settings")
    try:
        execute_from_command_line([sys.argv[0]] + args)
    except ImproperlyConfigured as e:
        print(str(e))
        exit(-1)


def apache_config(config, outputfile):
    '''
        Generate a valid Apache configuration file, based on the given settings.
    '''
    if os.path.exists(outputfile):
        os.rename(outputfile, outputfile + ".old")
        print("Renamed existing Apache config file to " + outputfile + ".old")

    from opensubmit import settings
    f = open(outputfile, 'w')
    print("Generating Apache configuration in " + outputfile)
    subdir = (len(settings.HOST_DIR) > 0)
    text = """
    # OpenSubmit Configuration for Apache 2.4
    # These directives are expected to live in some <VirtualHost> block
    """
    if subdir:
        text += "Alias /%s/static/ %s\n" % (settings.HOST_DIR,
                                            settings.STATIC_ROOT)
        text += "    WSGIScriptAlias /%s %s/wsgi.py\n" % (
            settings.HOST_DIR, settings.SCRIPT_ROOT)
    else:
        text += "Alias /static/ %s\n" % (settings.STATIC_ROOT)
        text += "    WSGIScriptAlias / %s/wsgi.py" % (settings.SCRIPT_ROOT)
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


def check_path(file_path):
    '''
        Checks if the directories for this path exist, and creates them in case.
    '''
    directory = os.path.dirname(file_path)
    if directory != '':
        if not os.path.exists(directory):
            os.makedirs(directory, 0o775)   # rwxrwxr-x


def check_file(filepath):
    '''
        - Checks if the parent directories for this path exist.
        - Checks that the file exists.
        - Donates the file to the web server user.

        TODO: This is Debian / Ubuntu specific.
    '''
    check_path(filepath)
    if not os.path.exists(filepath):
        print("WARNING: File does not exist. Creating it: %s" % filepath)
        open(filepath, 'a').close()
    try:
        print("Setting access rights for %s for www-data user" % (filepath))
        uid = pwd.getpwnam("www-data").pw_uid
        gid = grp.getgrnam("www-data").gr_gid
        os.chown(filepath, uid, gid)
        os.chmod(filepath, 0o660)  # rw-rw---
    except:
        print("WARNING: Could not adjust file system permissions for %s. Make sure your web server can write into it." % filepath)


def check_web_config_consistency(config):
    '''
        Check the web application config file for consistency.
    '''
    login_conf_deps = {
        'LOGIN_TWITTER_OAUTH_KEY': ['LOGIN_TWITTER_OAUTH_SECRET'],
        'LOGIN_GOOGLE_OAUTH_KEY': ['LOGIN_GOOGLE_OAUTH_SECRET'],
        'LOGIN_GITHUB_OAUTH_KEY': ['LOGIN_GITHUB_OAUTH_SECRET'],
        'LOGIN_TWITTER_OAUTH_SECRET': ['LOGIN_TWITTER_OAUTH_KEY'],
        'LOGIN_GOOGLE_OAUTH_SECRET': ['LOGIN_GOOGLE_OAUTH_KEY'],
        'LOGIN_GITHUB_OAUTH_SECRET': ['LOGIN_GITHUB_OAUTH_KEY'],
    }

    print("Checking configuration of the OpenSubmit web application...")
    # Let Django's manage.py load the settings file, to see if this works in general
    django_admin(["check"])
    # Check configured host
    try:
        urllib.request.urlopen(config.get("server", "HOST"))
    except Exception as e:
        # This may be ok, when the admin is still setting up to server
        print("The configured HOST seems to be invalid at the moment: " + str(e))
    # Check configuration dependencies
    for k, v in list(login_conf_deps.items()):
        if config.get('login', k):
            for needed in v:
                if len(config.get('login', needed)) < 1:
                    print(
                        "ERROR: You have enabled %s in settings.ini, but %s is not set." % (k, needed))
                    return False
    # Check media path
    check_path(config.get('server', 'MEDIA_ROOT'))
    # Prepare empty log file, in case the web server has no creation rights
    log_file = config.get('server', 'LOG_FILE')
    print("Preparing log file at " + log_file)
    check_file(log_file)
    # If SQLite database, adjust file system permissions for the web server
    if config.get('database', 'DATABASE_ENGINE') == 'sqlite3':
        name = config.get('database', 'DATABASE_NAME')
        if not os.path.isabs(name):
            print("ERROR: Your SQLite database name must be an absolute path. The web server must have directory access permissions for this path.")
            return False
        check_file(config.get('database', 'DATABASE_NAME'))
    # everything ok
    return True


def check_web_config(config_fname):
    '''
        Try to load the Django settings.
        If this does not work, than settings file does not exist.

        Returns:
            Loaded configuration, or None.
    '''
    print("Looking for config file at {0} ...".format(config_fname))
    config = RawConfigParser()
    try:
        config.readfp(open(config_fname))
        return config
    except IOError:
        print("ERROR: Seems like the config file does not exist. Please call 'opensubmit-web configcreate' first, or specify a location with the '-c' option.")
        return None


def check_web_db():
    '''
        Everything related to database checks and updates.
    '''
    print("Testing for neccessary database migrations...")
    django_admin(["migrate"])             # apply schema migrations
    print("Checking the OpenSubmit permission system...")
    # configure permission system, of needed
    django_admin(["fixperms"])
    return True


def configcreate(config_fname, settings):
    settings['server_secretkey'] = b64encode(os.urandom(64)).decode('utf-8')
    url_parts = settings['server_url'].split('/', 3)
    settings['server_host'] = url_parts[0] + '//' + url_parts[2]
    if len(url_parts) > 3:
        settings['server_hostdir'] = url_parts[3]
    else:
        settings['server_hostdir'] = ''
    content = DEFAULT_CONFIG.format(**settings)

    try:
        check_path(config_fname)
        f = open(config_fname, 'wt')
        f.write(content)
        f.close()
        print("Config file %s generated" % (config_fname))
    except Exception as e:
        print("ERROR: Could not create config file at {0}: {1}".format(config_fname, str(e)))


def configtest(config_fname):
    print("Inspecting OpenSubmit configuration ...")
    config = check_web_config(config_fname)
    if not config:
        return          # Let them first fix the config file before trying a DB access
    if not check_web_config_consistency(config):
        return
    if not check_web_db():
        return
    print("Preparing static files for web server...")
    django_admin(["collectstatic", "--noinput", "--clear", "-v 0"])


def console_script(fsroot=''):
    '''
        The main entry point for the production administration script 'opensubmit-web'.
        The argument allows the test suite to override the root of all paths used in here.
    '''

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, description='Administration for the OpenSubmit web application.')
    parser.add_argument('-c', '--config', default='/etc/opensubmit/settings.ini', help='OpenSubmit configuration file.')
    subparsers = parser.add_subparsers(dest='command', help='Supported administrative actions.')
    parser_configcreate = subparsers.add_parser('configcreate', help='Create initial config files for the OpenSubmit web server.')
    parser_configcreate.add_argument('--debug', default=bool(os.environ.get('OPENSUBMIT_DEBUG', 'False')), action='store_true', help='Enable debug mode, not for production systems.')
    parser_configcreate.add_argument('--server_url', default=os.environ.get('OPENSUBMIT_SERVER_URL', 'http://localhost:8000'), help='The main URL of the OpenSubmit installation, including sub-directories.')
    parser_configcreate.add_argument('--server_mediaroot', default=os.environ.get('OPENSUBMIT_SERVER_MEDIAROOT', '/tmp/'), help='Storage path for uploadeded files.')
    parser_configcreate.add_argument('--server_hostaliases', default=os.environ.get('OPENSUBMIT_SERVER_HOSTALIASES', '127.0.0.1'), help='Comma-separated list of alternative host names for the web server.')
    parser_configcreate.add_argument('--server_logfile', default=os.environ.get('OPENSUBMIT_SERVER_LOGFILE', '/tmp/opensubmit.log'), help='Log file for the OpenSubmit application.')
    parser_configcreate.add_argument('--server_timezone', default=os.environ.get('OPENSUBMIT_SERVER_TIMEZONE', 'Europe/Berlin'), help='Time zone for all dates and deadlines.')
    parser_configcreate.add_argument('--database_name', default=os.environ.get('OPENSUBMIT_DATABASE_NAME', '/tmp/database.sqlite'), help='Name of the database (file).'),
    parser_configcreate.add_argument('--database_engine', default=os.environ.get('OPENSUBMIT_DATABASE_ENGINE', 'sqlite3'), choices=['postgresql', 'mysql', 'sqlite3', 'oracle'])
    parser_configcreate.add_argument('--database_user', default=os.environ.get('OPENSUBMIT_DATABASE_USER', ''), help='The user name for accessing the database. Not needed for SQLite.')
    parser_configcreate.add_argument('--database_password', default=os.environ.get('OPENSUBMIT_DATABASE_PASSWORD', ''), help='The user password for accessing the database. Not needed for SQLite.')
    parser_configcreate.add_argument('--database_host', default=os.environ.get('OPENSUBMIT_DATABASE_HOST', ''), help='The host name for accessing the database. Not needed for SQLite. Default is localhost.')
    parser_configcreate.add_argument('--database_port', default=os.environ.get('OPENSUBMIT_DATABASE_PORT', ''), help='The port number for accessing the database. Not needed for SQLite.')
    parser_configcreate.add_argument('--login_google_oauth_key', default=os.environ.get('OPENSUBMIT_LOGIN_GOOGLE_OAUTH_KEY', ''), help='Google OAuth client key.')
    parser_configcreate.add_argument('--login_google_oauth_secret', default=os.environ.get('OPENSUBMIT_LOGIN_GOOGLE_OAUTH_SECRET', ''), help='Google OAuth client secret.')
    parser_configcreate.add_argument('--login_twitter_oauth_key', default=os.environ.get('OPENSUBMIT_LOGIN_TWITTER_OAUTH_KEY', ''), help='Twitter OAuth client key.')
    parser_configcreate.add_argument('--login_twitter_oauth_secret', default=os.environ.get('OPENSUBMIT_LOGIN_TWITTER_OAUTH_SECRET', ''), help='Twitter OAuth client secret.')
    parser_configcreate.add_argument('--login_github_oauth_key', default=os.environ.get('OPENSUBMIT_LOGIN_GITHUB_OAUTH_KEY', ''), help='GitHub OAuth client key.')
    parser_configcreate.add_argument('--login_github_oauth_secret', default=os.environ.get('OPENSUBMIT_LOGIN_GITHUB_OAUTH_SECRET', ''), help='GitHUb OAuth client secret.')
    parser_configcreate.add_argument('--login_openid_title', default=os.environ.get('OPENSUBMIT_LOGIN_OPENID_TITLE', 'StackExchange'), help='Title of the OpenID login button.')
    parser_configcreate.add_argument('--login_openid_provider', default=os.environ.get('OPENSUBMIT_LOGIN_OPENID_PROVIDER', 'https://openid.stackexchange.com'), help='URL of the OpenID provider.')
    parser_configcreate.add_argument('--login_shib_title', default=os.environ.get('OPENSUBMIT_LOGIN_SHIB_TITLE', ''), help='Title of the Shibboleth login button.')
    parser_configcreate.add_argument('--login_demo', default=bool(os.environ.get('OPENSUBMIT_LOGIN_DEMO', 'False')), action='store_true', help='Title of the Shibboleth login button.')
    parser_configcreate.add_argument('--admin_name', default=os.environ.get('OPENSUBMIT_ADMIN_NAME', 'OpenSubmit Administrator'), help='Name of the administrator, shown in privacy policy, impress and backend.')
    parser_configcreate.add_argument('--admin_email', default=os.environ.get('OPENSUBMIT_ADMIN_EMAIL', 'root@localhost'), help='eMail of the administrator, shown in privacy policy, impress and backend.')
    parser_configcreate.add_argument('--admin_address', default=os.environ.get('OPENSUBMIT_ADMIN_ADDRESS', '(address available by eMail)'), help='Address of the administrator, shown in privacy policy and impress.')
    parser_configcreate.add_argument('--admin_impress_page', default=os.environ.get('OPENSUBMIT_IMPRESS_PAGE', ''), help='Link to alternative impress page.')
    parser_configcreate.add_argument('--admin_privacy_page', default=os.environ.get('OPENSUBMIT_PRIVACY_PAGE', ''), help='Link to alternative privacy policy page.')

    parser_configtest = subparsers.add_parser('configtest', aliases=['configure'], help='Check config files and database for correct installation of the OpenSubmit web server.')
    parser_democreate = subparsers.add_parser('democreate', aliases=['createdemo'], help='Install some test data (courses, assignments, users).')
    parser_apachecreate = subparsers.add_parser('apachecreate', help='Create config file snippet for Apache 2.4.')
    parser_fixperms = subparsers.add_parser('fixperms', help='Check and fix student and tutor permissions.')
    parser_fixchecksums = subparsers.add_parser('fixchecksums', help='Re-create all student file checksums (for duplicate detection).')

    parser_makeadmin = subparsers.add_parser('makeadmin', help='Make this user an admin with backend rights.')
    parser_makeadmin.add_argument('email')
    parser_makeowner = subparsers.add_parser('makeowner', help='Make this user a course owner with backend rights.')
    parser_makeowner.add_argument('email')
    parser_maketutor = subparsers.add_parser('maketutor', help='Make this user a course tutor with backend rights.')
    parser_maketutor.add_argument('email')
    parser_makestudent = subparsers.add_parser('makestudent', help='Make this user a student without backend rights.')
    parser_makestudent.add_argument('email')
    args = parser.parse_args()

    config_file = fsroot + args.config

    if args.command == 'apachecreate':
        config = check_web_config(config_file)
        if config:
            apache_config(config, os.path.dirname(config_file) + os.sep + 'apache24.conf')
        return

    if args.command == 'configcreate':
        configcreate(config_file, vars(args))
        return

    if args.command == 'configtest':
        configtest(config_file)
        return

    if args.command in ['fixperms', 'fixchecksums', 'democreate']:
        django_admin([args.command])
        return

    if args.command in ['makeadmin', 'makeowner', 'maketutor', 'makestudent']:
        django_admin([args.command, args.email])
        return


if __name__ == "__main__":
    console_script()
