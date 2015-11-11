'''
    Test cases for the command line tools.
'''

from django.test import TestCase
from opensubmit import cmdline
import sys, tempfile, os.path, ConfigParser, shutil


class CmdLineConfigureTestCase(TestCase):
    '''
        Test cases for the "configure" functionality of the command-line script.

        Test cases here rely on the 'fsroot' argument for the command-line script entry function.
        It allows to re-direct all file accesses of the module to another directory.
    '''
    def setUp(self):
        sys.argv=['opensubmit-web','configure'] # simulate command-line argument
        self.tmpdir=tempfile.mkdtemp()+os.sep   # prepare target directory

    def tearDown(self):
        print("Removing temporary installation directory")
        shutil.rmtree(self.tmpdir)

    def _createValidConfigFile(self):
        # prepare config file directory
        # prepare config file
        config = ConfigParser.RawConfigParser()
        config.add_section('general')
        config.set('general','SCRIPT_ROOT',self.tmpdir+'static/')
        config.add_section('server')
        config.set('server','HOST','http://example.com')
        config.set('server','MEDIA_ROOT',self.tmpdir+'mediadir/')
        config.set('server','LOG_FILE',self.tmpdir+'test.log')
        config.add_section('login')
        config.set('login','LOGIN_OPENID',False)
        config.set('login','LOGIN_TWITTER',False)
        config.set('login','LOGIN_GOOGLE',False)
        config.set('login','LOGIN_GITHUB',False)
        config.set('login','LOGIN_SHIB',False)
        config.add_section('database')
        config.set('database','DATABASE_ENGINE','sqlite3')
        config.set('database','DATABASE_NAME',self.tmpdir+'database.sqlite')
        fdir = self.tmpdir+'etc/opensubmit/'
        os.makedirs(fdir)
        with open(fdir+'settings.ini', 'wb') as configfile:
            config.write(configfile)
        return fdir

    def testFirstConfigureCall(self):
        '''
            Simulate a real first-time command-line call of the 'configure' functionality.
            This should create settings.ini.
        '''
        cmdline.console_script(fsroot=self.tmpdir)
        assert(os.path.isfile(self.tmpdir+'etc/opensubmit/settings.ini'))

    def testConfigureCallWithConfig(self):
        '''
            Simulate a real command-line call of the 'configure' functionality with a valid settings file
            in existence.
        '''
        self._createValidConfigFile()
        # run command-line tool functionality
        cmdline.console_script(fsroot=self.tmpdir)
