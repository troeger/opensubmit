from django.test.runner import DiscoverRunner as DjangoRunner
from django.conf import settings
import os
import unittest
from django.test.utils import setup_test_environment

# Unicode crap, to be added to all test suite string input
# Ensures proper handling of unicode content everywhere, as reaction to #154
uccrap = str('öäüßé')

# Root directory of the test data, for finding the test files
rootdir = os.path.dirname(__file__) + os.sep


class DiscoverRunner(DjangoRunner):
    '''
        A custom overloaded test runner seems to be the only reasonable way
        to get DEBUG=True and a different port number into LiveServerTestCase.
    '''

    def setup_test_environment(self, **kwargs):
        os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = "localhost:8100-9999"
        setup_test_environment()
        settings.DEBUG = True
        unittest.installHandler()
