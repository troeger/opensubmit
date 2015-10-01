# User admin interface
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.admin import StackedInline
from opensubmit.models import UserProfile

class UserProfileInline(StackedInline):
    model = UserProfile
    classes = ('grp-collapse grp-open',)
    inline_classes = ('grp-collapse grp-open',)

class UserAdmin(DjangoUserAdmin):
    inlines = (UserProfileInline, )

