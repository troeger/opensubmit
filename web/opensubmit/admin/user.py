# User admin interface
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.admin import StackedInline
from opensubmit.models import UserProfile, tutor_courses
from django.shortcuts import render
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.core.urlresolvers import reverse



class UserProfileInline(StackedInline):
    model = UserProfile
    classes = ('grp-collapse grp-open',)
    inline_classes = ('grp-collapse grp-open',)

def social(user):
    '''
        Returns the social ID of this user.
    '''
    try:
        return str(user.social_auth.get().uid)
    except:
        return None

class UserAdmin(DjangoUserAdmin):
    actions = ['mergeusers',]

    inlines = (UserProfileInline, )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff',  social)

    def mergeusers(modeladmin, request, queryset):
        if len(queryset) != 2:
            modeladmin.message_user(request, "Please choose exactly two users to merge.", level=messages.WARNING)
            return reverse('admin:index')
        # In most cases, we want to keep the user logged in recently, so we query accordingly
        primary, secondary = queryset.order_by('-date_joined')
        if len(tutor_courses(primary)) > 0 or len(tutor_courses(secondary)) > 0:
            # Since the user is deleted, this is more complicated (course ownership, gradings given etc.)
            modeladmin.message_user(request, "Merging course owners or tutors is not support at the moment.", level=messages.WARNING)
            return reverse('admin:index')
        return HttpResponseRedirect('%s?primary_id=%u&secondary_id=%s'%(reverse('mergeusers'), primary.pk, secondary.pk))
    mergeusers.short_description = "Merge selected users"
