'''
    Test cases for the command line tools.
'''

import sys
import tempfile
import os.path
import configparser
import shutil

from django.test import TestCase
from opensubmit import cmdline
from django.conf import settings
from opensubmit.models import Course
from .helpers import user


class CmdLine(TestCase):
    '''
    Test cases for the "configure" functionality of the command-line script.
    '''

    def setUp(self):
        # prepare temporary target directory for tests
        self.tmpdir = tempfile.mkdtemp() + os.sep
        '''
        Create config file.
        This needs some explanation:
        - The 'configure' functionality does not care about Django settings,
          so we use the 'fsroot' parameter to force them into the
          temporary directory.
        - This should lead to the creation of a fresh settings file,
          which then must be adjusted by the user. We mock that accordingly.
        '''
        sys.argv = ['opensubmit-web', 'configcreate']
        cmdline.console_script(fsroot=self.tmpdir)
        self.conf_name = self.tmpdir + 'etc/opensubmit/settings.ini'
        self.assertEqual(True, os.path.isfile(self.conf_name))
        # Got a working settings file from the template, now configure it
        self.cfg = configparser.ConfigParser()
        with open(self.conf_name) as cfg_file:
            self.cfg.readfp(cfg_file)
        self.cfg.set('server', 'HOST', 'http://www.troeger.eu')
        self.cfg.set('server', 'MEDIA_ROOT', self.tmpdir + settings.MEDIA_ROOT)
        self.cfg.set('server', 'LOG_FILE', self.tmpdir + settings.LOG_FILE)
        self.cfg.set('database', 'DATABASE_NAME', self.tmpdir + 'database.sqlite')
        self.cfg.set('login', 'LOGIN_GOOGLE_OAUTH_KEY', 'foo')
        self.cfg.set('login', 'LOGIN_GOOGLE_OAUTH_SECRET', 'bar')
        with open(self.conf_name, 'w') as cfg_file:
            self.cfg.write(cfg_file)
        # We got an adjusted INI file, which is not-reconsidered by the
        # indirectly triggered Django code, but by the cmdline functionalities.

    def tearDown(self):
        print("Removing temporary installation directory")
        shutil.rmtree(self.tmpdir)

    def test_democreate_call(self):
        sys.argv = ['opensubmit-web', 'democreate']
        cmdline.console_script(fsroot=self.tmpdir)
        self.assertNotEqual(0, Course.objects.all().count())

    def test_fixperms_call(self):
        sys.argv = ['opensubmit-web', 'fixperms']
        cmdline.console_script(fsroot=self.tmpdir)

    def test_fixchecksums_call(self):
        sys.argv = ['opensubmit-web', 'fixchecksums']
        cmdline.console_script(fsroot=self.tmpdir)

    def test_makeadmin_call(self):
        u = user.create_user(user.get_student_dict(0))
        sys.argv = ['opensubmit-web', 'makeadmin', u.email]
        cmdline.console_script(fsroot=self.tmpdir)
        u.refresh_from_db()
        self.assertEqual(True, u.is_superuser)
        self.assertEqual(True, u.is_staff)

    def test_makeowner_call(self):
        u = user.create_user(user.get_student_dict(0))
        sys.argv = ['opensubmit-web', 'makeowner', u.email]
        cmdline.console_script(fsroot=self.tmpdir)
        u.refresh_from_db()
        self.assertEqual(False, u.is_superuser)
        self.assertEqual(True, u.is_staff)

    def test_maketutor_call(self):
        u = user.create_user(user.get_student_dict(0))
        sys.argv = ['opensubmit-web', 'maketutor', u.email]
        cmdline.console_script(fsroot=self.tmpdir)
        u.refresh_from_db()
        self.assertEqual(False, u.is_superuser)
        self.assertEqual(True, u.is_staff)

    def test_makestudent_call(self):
        u = user.create_user(user.admin_dict)
        sys.argv = ['opensubmit-web', 'makestudent', u.email]
        cmdline.console_script(fsroot=self.tmpdir)
        u.refresh_from_db()
        self.assertEqual(False, u.is_superuser)
        self.assertEqual(False, u.is_staff)

    def test_bool_configcreate_env(self):
        '''
        Test if boolean values from environment variables are
        correctly interpreted in the config file generation.
        '''
        sys.argv = ['opensubmit-web', 'configcreate']
        os.environ['OPENSUBMIT_DEBUG'] = 'True'
        cmdline.console_script(fsroot=self.tmpdir)
        data = open(self.conf_name, 'rt').readlines()
        self.assertTrue("DEBUG: True\n" in data)
        self.assertTrue("DEMO: False\n" in data)
        os.environ['OPENSUBMIT_LOGIN_DEMO'] = 'True'
        cmdline.console_script(fsroot=self.tmpdir)
        data = open(self.conf_name, 'rt').readlines()
        self.assertTrue("DEMO: True\n" in data)

    def test_configtest_call(self):
        '''
        Simulate real command-line calls of the 'configure' functionality.

        Since the config file ist valid,  some Django manage.py
        functionality for the collection of static files is triggered here.
        Since Django settings are already loaded by the test suite,
        the modified INI file is not respected here.
        For this reason, we need the settings decorator override.
        '''
        # simulate command-line argument
        with self.settings(STATIC_ROOT=self.tmpdir + 'static'):
            sys.argv = ['opensubmit-web', 'configtest']
            cmdline.console_script(fsroot=self.tmpdir)
            self.assertEqual(True, os.path.isdir(self.tmpdir + 'static/grappelli'))
