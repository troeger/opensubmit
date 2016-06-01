from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .assignment import Assignment
from .course import Course
from .submission import Submission

class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name='profile')
    student_id = models.CharField(max_length=30, blank=True, null=True)
    courses = models.ManyToManyField(Course, blank=True, related_name='participants', limit_choices_to={'active__exact': True})

    class Meta:
        app_label = 'opensubmit'

    def add_course_safe(self, id):
        '''
            Adds a course for the user after conducting a set of sanity checks.
            Return the title of the course or an exception.
        '''
        course = get_object_or_404(Course, pk=int(id), active=True)
        if course not in self.courses.all():
            self.courses.add(course)
        return course.title

    def tutor_courses(self):
        '''
            Returns the list of courses this user is tutor or owner for.
        '''
        tutoring = self.user.courses_tutoring.all().filter(active__exact=True)
        owning = self.user.courses.all().filter(active__exact=True)
        result = (tutoring | owning).distinct()
        return result

    def user_courses(self):
        '''
            Returns the list of courses this user is subscribed for, or owning, or tutoring.
            This leads to the fact that tutors and owners don't need course membership.
        '''
        registered=self.courses.filter(active__exact=True).distinct()
        return (self.tutor_courses() | registered).distinct()

    def open_assignments(self):
        '''
            Returns the list of open assignments from the viewpoint of this user.
        '''
        qs = Assignment.objects.filter(hard_deadline__gt=timezone.now())
        qs = qs.filter(publish_at__lt=timezone.now())
        qs = qs.filter(course__in=self.user_courses())
        qs = qs.order_by('soft_deadline').order_by('hard_deadline').order_by('title')
        waiting_for_action = [subm.assignment for subm in self.user.authored.all().exclude(state=Submission.WITHDRAWN)]
        return [ass for ass in qs if ass not in waiting_for_action]

def db_fixes(user):
    '''
        Fix users that already exist and never got a user profile attached.
        This may be user accounts that were created by the Django Social or manually by the admin.

        TODO: This belongs into a User post_save handler.
    '''
    profile, created = UserProfile.objects.get_or_create(user=user)

def user_unicode(self):
    '''
        Monkey patch for getting better user name stringification,
        user proxies did not make the job.
        Django's custom user model feature would have needed to be introduced
        before the first syncdb, which does not work for existing installations.
'''
    if self.email:
        shortened = self.email.split('@')[0]
        return u'%s %s (%s@...)' % (self.first_name, self.last_name, shortened)
    elif self.first_name or self.last_name:
        return u'%s %s' % (self.first_name, self.last_name)
    elif self.username:
        return u'%s' % (self.username)
    else:
        return u'User %u' % (self.pk)
User.__unicode__ = user_unicode

@transaction.atomic
def move_user_data(primary, secondary):
    '''
        Moves all submissions and other data linked to the secondary user into the primary user.
        Nothing is deleted here, we just modify foreign user keys.
    '''
    # Update all submission authorships of the secondary to the primary
    submissions = Submission.objects.filter(authors__id=secondary.pk)
    for subm in submissions:
        if subm.submitter == secondary:
            subm.submitter = primary;
        subm.authors.remove(secondary)
        subm.authors.add(primary)
        subm.save()
    # Transfer course registrations
    try:
        for course in secondary.profile.courses.all():
            primary.profile.courses.add(course)
            primary.profile.save()
    except UserProfile.DoesNotExist:
        # That's a database consistency problem, but he will go away anyway
        pass
