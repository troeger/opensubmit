from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from .security import check_permission_system
from .models import Submission, Course, SubmissionFile
from .models.userprofile import db_fixes


@receiver(post_save, sender=User)
def post_user_save(sender,instance, signal, created, **kwargs):
    """
        Make sure that all neccessary user groups exist and have the right permissions,
        directly after the auth system was installed. We detect this by waiting for the admin
        account creation here, which smells hacky.
        We need that automatism for the test database creation, people not calling the configure tool and similar cases.

        Second task: Every user need a profile, which is not created by the social libraries.        
    """
    if instance.is_staff and created:
        check_permission_system()
    db_fixes(instance)

@receiver(post_save, sender=SubmissionFile)
def submissionfile_post_save(sender,instance, signal, created, **kwargs):
    '''
        Update MD5 field for newly uploaded files.
    '''
    if created:
        instance.md5 = instance.attachment_md5()
        instance.save()

@receiver(post_save, sender=Submission)
def submission_post_save(sender, instance, **kwargs):
    ''' Several sanity checks after we got a valid submission object.'''
    # Make the submitter an author
    if instance.submitter not in instance.authors.all():
        instance.authors.add(instance.submitter)
        instance.save()
    # Mark all existing submissions for this assignment by these authors as invalid.
    # This fixes a race condition with parallel new submissions in multiple browser windows by the same user.
    # Solving this as pre_save security exception does not work, since we have no instance with valid foreign keys to check there.
    # Considering that this runs also on tutor correction backend activities, it also serves as kind-of cleanup functionality
    # for multiplse submissions by the same students for the same assignment - however they got in here.
    if instance.state == instance.get_initial_state():
        for author in instance.authors.all():
            same_author_subm = User.objects.get(pk=author.pk).authored.all().exclude(pk=instance.pk).filter(assignment=instance.assignment)
            for subm in same_author_subm:
                subm.state = Submission.WITHDRAWN
                subm.save()

@receiver(post_save, sender=Course)
def course_post_save(sender, instance, **kwargs):
    '''
        After creating / modifying a course, make sure that only tutors and course owners have backend access rights.
        We do that here since tutor addition and removal ends up in a course modification signal.
    '''
    check_permission_system()