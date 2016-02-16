from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group
from opensubmit.signalhandlers import check_permission_system

class Command(BaseCommand):
    help = 'Makes sure that the OpenSubmit permission system is up and valid'
    def handle(self, *args, **options):
        print("Scanning existing users ...")
        check_permission_system()
