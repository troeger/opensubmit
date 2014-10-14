# User admin interface
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.admin import StackedInline
from opensubmit.models import UserProfile

class UserProfileInline(StackedInline):
    model = UserProfile


class UserAdmin(DjangoUserAdmin):
    inlines = (UserProfileInline, )
