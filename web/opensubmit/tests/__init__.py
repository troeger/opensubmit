import os
import unittest
import logging

from django.test.runner import DiscoverRunner as DjangoRunner
from django.conf import settings
from django.test.utils import setup_test_environment

# Unicode crap, to be added to all test suite string input
# Ensures proper handling of unicode content everywhere, as reaction to #154
uccrap = str('öäüßé')

# Root directory of the test data, for finding the test files
rootdir = os.path.dirname(__file__) + os.sep


# Override for log output during test run
log_level = logging.DEBUG


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

        logger = logging.getLogger('OpenSubmit')
        logger.setLevel(log_level)
        logger = logging.getLogger('opensubmitexec')
        logger.setLevel(log_level)

