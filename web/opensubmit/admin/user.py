# User admin interface
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.shortcuts import render
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.core.urlresolvers import reverse

from opensubmit.models import UserProfile
from opensubmit.security import make_student, make_tutor, make_owner, make_admin, STUDENT_TUTORS_GROUP_NAME, COURSE_OWNERS_GROUP_NAME


class UserProfileInline(admin.TabularInline):
    model = UserProfile
    verbose_name_plural="Student Details"
    can_delete = False
#    classes = ('grp-collapse grp-open',)
    inline_classes = ('grp-collapse grp-open',)

def study_program(user):
    return user.profile.study_program

def is_student(user):
    return user.is_staff
is_student.short_description = "Backend?"
is_student.boolean = True

def is_tutor(user):
    return user.groups.filter(name=STUDENT_TUTORS_GROUP_NAME).exists()
is_tutor.short_description = "Tutor?"
is_tutor.boolean = True

def is_owner(user):
    return user.groups.filter(name=COURSE_OWNERS_GROUP_NAME).exists()
is_owner.short_description = "Owner?"
is_owner.boolean = True

def is_admin(user):
    return user.is_superuser
is_admin.short_description = "Admin?"
is_admin.boolean = True

def groups(user):
    return ",".join(str(group) for group in user.groups.all())

def student_id(user):
    return user.profile.student_id
student_id.short_description = "Student ID"

def social_login_id(user):
    try:
        return str(user.social_auth.get().uid)
    except:
        return None
social_login_id.short_description = "Social Login ID"

class UserAdmin(DjangoUserAdmin):
    actions = ['mergeusers','make_student','make_tutor','make_owner','make_admin']
    fieldsets = (
        ("User Data", {
            "classes": ("grp-collapse grp-open",),
            "fields": ("username","password","first_name","last_name", "email")
        }),
        ("Details", {
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

    class Media:
        css = {'all': ('css/teacher.css',)}

    inlines = (UserProfileInline, )
    list_display = ('username', 'email', 'first_name', 'last_name', student_id, study_program, is_student, is_tutor, is_owner, is_admin, social_login_id)

    def make_student(self, request, queryset):
        for user in queryset:
            make_student(user)
    make_student.short_description = "Configure selected users as student"

    def make_tutor(self, request, queryset):
        for user in queryset:
            make_tutor(user)
    make_tutor.short_description = "Configure selected users as tutor"

    def make_owner(self, request, queryset):
        for user in queryset:
            make_owner(user)
    make_owner.short_description = "Configure selected users as course owner"

    def make_admin(self, request, queryset):
        for user in queryset:
            make_admin(user)
    make_admin.short_description = "Configure selected users as admin"

    def mergeusers(modeladmin, request, queryset):
        if len(queryset) != 2:
            modeladmin.message_user(request, "Please choose exactly two users to merge.", level=messages.WARNING)
            return reverse('admin:index')
        # In most cases, we want to keep the user logged in recently, so we query accordingly
        primary, secondary = queryset.order_by('-date_joined')
        # Since the user is deleted, merging staff users is more complicated
        # (course ownership, gradings given etc.)
        # We therefore only support the merging of real students
        if primary.profile.tutor_courses().count() > 0:
            modeladmin.message_user(request, "{0} is a course owner or tutor, which cannot be merged.".format(primary), level=messages.WARNING)
            return reverse('admin:index')
        if secondary.profile.tutor_courses().count() > 0:
            modeladmin.message_user(request, "{0} is a course owner or tutor, which cannot be merged.".format(secondary), level=messages.WARNING)
            return reverse('admin:index')
        return HttpResponseRedirect(reverse('mergeusers', kwargs={'primary_pk': primary.pk, 'secondary_pk': secondary.pk}))
    mergeusers.short_description = "Merge selected users"
