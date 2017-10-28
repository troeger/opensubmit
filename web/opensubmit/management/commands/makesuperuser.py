from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Makes the given user a superuser, adds him to all courses as tutor.'

    def add_arguments(self, parser):
        parser.add_argument('email', nargs=1, type=str)

    def handle(self, *args, **options):
        try:
            u=User.objects.get(email=options['email'][0])
            print("Found %s %s (%s), setting superuser status."%(u.first_name, u.last_name, u.email))
            u.is_superuser=True
            u.is_staff=True
            u.save()
        except:
            print("Invalid user email address.")
