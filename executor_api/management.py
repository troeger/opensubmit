from django.db.models import signals
from django.contrib.auth.models import Group, Permission

import models
import executor_api.models


def create_groups(app, created_models, verbosity, **kwargs):
#    if verbosity > 0:
#        print "Creating default groups for executor_api app...",
    api_group, created = Group.objects.get_or_create(name="API Users (automatic group)")
    api_group.permissions.add(Permission.objects.get(codename='api_usage'))
    api_group.save()
#    if verbosity > 0:
#        print " done."
    

signals.post_syncdb.connect(
    create_groups, 
    sender=executor_api.models.TestMachine,
    dispatch_uid='executor_api.management.create_groups'
)