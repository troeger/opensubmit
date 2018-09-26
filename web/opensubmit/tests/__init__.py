import os
import logging

from django.test.runner import DiscoverRunner

# Unicode crap, to be added to all test suite string input
# Ensures proper handling of unicode content everywhere, as reaction to #154
uccrap = str('öäüßé')

# Root directory of the test data, for finding the test files
rootdir = os.path.dirname(__file__) + os.sep

# Override for log output during test run
log_level = logging.ERROR
