from django.core.management.base import BaseCommand, CommandError 
from django.contrib.auth.models import User, Group
from opensubmit.signalhandlers import ensure_user_groups

class Command(BaseCommand):
    help = 'Makes sure that all internal permissions are set'
    def handle(self, *args, **options): 
        users = User.objects.all()
        for user in users:
            if ensure_user_groups(user, True):      # emulate user creation to actually make a change
                print("Resetting Django group permissions for %s"%str(user))
            else:
                print("Resetting Django group permissions for %s failed"%str(user))



