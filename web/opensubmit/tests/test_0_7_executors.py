'''
Tests for executors after version 0.7.0, which support a completely new
format for validation.
'''

import sys, os

from django.test import TestCase

sys.path.insert(0, os.path.dirname(__file__)+'/../../../executor/')
print(sys.path)
from opensubmitexec import cmdline, config

class ExecutorTestingMode(TestCase):
    '''
    These test cases simulate the usage of opensubmit-exec test <dir_name>.
    '''
    def setUp(self):
        super(ExecutorTestingMode, self).setUp()
        self.config = config.read_config(os.path.dirname(__file__)+"/executor.cfg")

    def test_all(self):
        '''
        Go through all test scenarios and run them through the local-only test mode
        of the eexecutor.
        Mainly intended for catching weird exceptions.
        Result testing is not possible here, since no reporting to the server takes
        place. You just have the executor log output.
        '''
        base_dir = os.path.dirname(__file__)+'/0_7_executors/'

        for root, dirs, files in os.walk(base_dir):
            for directory in dirs:
                cmdline.copy_and_run(self.config, root+directory)
