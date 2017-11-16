from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

from opensubmit.security import make_tutor

class Command(BaseCommand):
    help = 'Makes the given user a course tutor.'

    def add_arguments(self, parser):
        parser.add_argument('email', nargs=1, type=str)

    def handle(self, *args, **options):
        try:
            u=User.objects.get(email=options['email'][0])
            print("Found %s %s (%s), activating course tutor rights."%(u.first_name, u.last_name, u.email))
            make_tutor(u)            
        except User.DoesNotExist:
            print("This user does not exist.")
