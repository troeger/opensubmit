from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password


class Command(BaseCommand):
    ''' Make sure that superuser exists. '''

    def handle(self, *args, **option):
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username='root', is_superuser=True, is_staff=True)
        if created:
            pw = User.objects.make_random_password()
            user.password = make_password(pw)
            user.save()
            print("Superuser created, password is '{0}'.".format(pw))
        else:
            print("Superuser exists, nothing changed.")
