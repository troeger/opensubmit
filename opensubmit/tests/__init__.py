from django.test.runner import DiscoverRunner as DjangoRunner
import os

class DiscoverRunner(DjangoRunner):
    def __init__(self, **kwargs):
    	# This seems to be the only way to convince LiveServerTestCase of another port
        os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS']='localhost:8000'
        super(DiscoverRunner, self).__init__(kwargs)
