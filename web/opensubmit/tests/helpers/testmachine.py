import datetime
import json

from opensubmit.tests import uccrap
from opensubmit.models import TestMachine


def create_test_machine(test_host):
    '''
        Create test machine entry. The configuration information
        is expected to be some JSON dictionary, since this is
        normally directly rendered in the machine details view.
    '''
    machine = TestMachine(
        last_contact=datetime.datetime.now(),
        host=test_host,
        config=json.dumps([['Operating system', uccrap + 'Plan 9'], ]))
    machine.save()
    return machine
