'''
    Test cases for the command line tools.
'''

from django.test import TestCase
from opensubmit import cmdline, settings
import sys, tempfile, os.path, ConfigParser, shutil

class CmdLineConfigureTestCase(TestCase):
    '''
        Test cases for the "configure" functionality of the command-line script.
    '''
    def setUp(self):
        sys.argv=['opensubmit-web','configure'] # simulate command-line argument
        self.tmpdir=tempfile.mkdtemp()+os.sep   # prepare target directory for install tests

    def tearDown(self):
        print("Removing temporary installation directory")
        shutil.rmtree(self.tmpdir)

    def testConfigureCall(self):
        '''
            Simulate real command-line calls of the 'configure' functionality.

            This needs some explanation:
            - The 'configure' functionality does not care about Django settings, so we use
              the 'fsroot' parameter to force them into the temporary directory.
            - This should lead to the creation of a fresh settings file, which then must be
              adjusted by the user. We mock that accordingly.
            - The second run of 'configure' now finds the adjusted settings file. It parses
              the content and performs some validation and generation steps.
            - The last step of 'configure' is to call some Django manage.py functionality for
              the collection of static files. Since Django settings are already loaded by the test suite,
              the modified INI file is not respected here. For this reason, we need the settings decorator
              override.
        '''
        cmdline.console_script(fsroot=self.tmpdir)
        conf_name = self.tmpdir+'etc/opensubmit/settings.ini'
        self.assertEquals(True, os.path.isfile(conf_name))
        # Got a working settings file from the template, now configure it
        cfg=ConfigParser.ConfigParser()
        with open(conf_name) as cfg_file:
            cfg.readfp(cfg_file)
        cfg.set('server',  'HOST','http://www.troeger.eu')
        cfg.set('server',  'MEDIA_ROOT',self.tmpdir+settings.MEDIA_ROOT)
        cfg.set('server',  'LOG_FILE',self.tmpdir+settings.LOG_FILE)
        cfg.set('database','DATABASE_NAME',self.tmpdir+'database.sqlite')
        with open(conf_name,'w') as cfg_file:
            cfg.write(cfg_file)
        # We got an adjusted INI file, which is not-reconsidered by the indirectly triggered Django code,
        # but only by the 'configure' code itself.
        with self.settings(STATIC_ROOT=self.tmpdir+'static'):
            cmdline.console_script(fsroot=self.tmpdir)
            self.assertEquals(True, os.path.isfile(self.tmpdir+'etc/opensubmit/apache24.conf'))
            self.assertEquals(True, os.path.isdir(self.tmpdir+'static/css'))

