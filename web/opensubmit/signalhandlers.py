from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db import transaction

from .security import check_permission_system
from .models import Submission, Course, SubmissionFile

from opensubmit.models import UserProfile

import logging
logger = logging.getLogger('OpenSubmit')


@receiver(user_logged_in)
def post_user_login(sender, request, user, **kwargs):
    """
        Create a profile for the user, when missing.
        Make sure that all neccessary user groups exist and have the right permissions.
        We need that automatism for people not calling the configure tool,
        admin rights for admins after the first login, and similar cases.
    """
    logger.debug("Running post-processing for user login.")
    # Users created by social login or admins have no profile.
    # We fix that during their first login.
    try:
        with transaction.atomic():
            profile, created = UserProfile.objects.get_or_create(user=user)
            if created:
                logger.info("Created missing profile for user " + str(user.pk))
    except Exception as e:
        logger.error("Error while creating user profile: " + str(e))
    check_permission_system()


@receiver(post_save, sender=SubmissionFile)
def submissionfile_post_save(sender, instance, signal, created, **kwargs):
    '''
        Update MD5 field for newly uploaded files.
    '''
    if created:
        logger.debug("Running post-processing for new submission file.")
        instance.md5 = instance.attachment_md5()
        instance.save()


@receiver(post_save, sender=Submission)
def submission_post_save(sender, instance, **kwargs):
    ''' Several sanity checks after we got a valid submission object.'''
    logger.debug("Running post-processing for submission")
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
            same_author_subm = User.objects.get(pk=author.pk).authored.all().exclude(
                pk=instance.pk).filter(assignment=instance.assignment)
            for subm in same_author_subm:
                subm.state = Submission.WITHDRAWN
                subm.save()


@receiver(post_save, sender=Course)
def course_post_save(sender, instance, **kwargs):
    '''
        After creating / modifying a course, make sure that only tutors and course owners have backend access rights.
        We do that here since tutor addition and removal ends up in a course modification signal.
    '''
    logger.debug("Running post-processing for course change.")
    check_permission_system()
