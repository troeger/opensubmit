from django.test.runner import DiscoverRunner as DjangoRunner
from django.conf import settings
import os
import unittest
from django.test.utils import setup_test_environment


class DiscoverRunner(DjangoRunner):
    '''
        A custom overloaded test runner seems to be the only reasonable way
        to get DEBUG=True and a different port number into LiveServerTestCase.
    '''
    def setup_test_environment(self, **kwargs):
        os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS']='localhost:8000'
        setup_test_environment()
        settings.DEBUG = True
        unittest.installHandler()
