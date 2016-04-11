# User admin interface
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from opensubmit.models import UserProfile
from django.shortcuts import render
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.core.urlresolvers import reverse


def social(user):
    '''
        Returns the social ID of this user.
    '''
    try:
        return str(user.social_auth.get().uid)
    except:
        return None

class UserProfileInline(admin.TabularInline):
    model = UserProfile
    verbose_name_plural="Student Details"
    can_delete = False
#    classes = ('grp-collapse grp-open',)
    inline_classes = ('grp-collapse grp-open',)

class UserAdmin(DjangoUserAdmin):
    actions = ['mergeusers',]
    fieldsets = (
        ("User Data", {
            "classes": ("grp-collapse grp-open",),
            "fields": ("username","password","first_name","last_name", "email")
        }),
        ("Student Details", {
            "classes": ("placeholder profile-group",),
            "fields": ()
        }),
        ("Authorization", {
            "classes": ("grp-collapse grp-open",),
            "fields": ("is_active", "is_staff", "is_superuser", "groups")
        }),
        ("Info", {
            "classes": ("grp-collapse grp-open",),
            "fields": ("last_login","date_joined")
        }),
    )

    inlines = (UserProfileInline, )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff',  social)

    def mergeusers(modeladmin, request, queryset):
        if len(queryset) != 2:
            modeladmin.message_user(request, "Please choose exactly two users to merge.", level=messages.WARNING)
            return reverse('admin:index')
        # In most cases, we want to keep the user logged in recently, so we query accordingly
        primary, secondary = queryset.order_by('-date_joined')
        if primary.profile.tutor_courses().count() > 0 or secondary.profile.tutor_courses().count() > 0:
            # Since the user is deleted, this is more complicated (course ownership, gradings given etc.)
            modeladmin.message_user(request, "Merging course owners or tutors is not support at the moment.", level=messages.WARNING)
            return reverse('admin:index')
        return HttpResponseRedirect('%s?primary_id=%u&secondary_id=%s'%(reverse('mergeusers'), primary.pk, secondary.pk))
    mergeusers.short_description = "Merge selected users"
