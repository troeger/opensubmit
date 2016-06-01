from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.urlresolvers import reverse

from .submission import Submission
from .submissiontestresult import SubmissionTestResult

class Assignment(models.Model):
    '''
        An assignment for which students can submit their solution.
    '''

    title = models.CharField(max_length=200)
    course = models.ForeignKey('Course', related_name='assignments')
    download = models.URLField(max_length=200, verbose_name="Link for assignment description")
    created = models.DateTimeField(auto_now_add=True, editable=False)
    gradingScheme = models.ForeignKey('GradingScheme', related_name="assignments", verbose_name="grading scheme")
    publish_at = models.DateTimeField(default=timezone.now)
    soft_deadline = models.DateTimeField(blank=True, null=True, help_text="Deadline shown to students. After this point in time, submissions are still possible. Leave empty for only using a hard deadline.")
    hard_deadline = models.DateTimeField(help_text="Deadline after which submissions are no longer possible.")
    has_attachment = models.BooleanField(default=False, verbose_name="Student file upload ?", help_text="Activate this if the students must upload a (document / ZIP /TGZ) file as solution. Otherwise, they can only fill the notes field.")
    attachment_test_timeout = models.IntegerField(default=30, verbose_name="Timout for tests", help_text="Timeout (in seconds) after which the compilation / validation test / full test is cancelled. The submission is marked as invalid in this case. Intended for student code with deadlocks.")
    attachment_test_compile = models.BooleanField(default=False, verbose_name="Compile test ?", help_text="If activated, the student upload is uncompressed and 'make' is executed on one of the test machines.")
    attachment_test_validity = models.FileField(upload_to="testscripts", blank=True, null=True, verbose_name='Validation script', help_text="If given, the student upload is uncompressed, compiled and the script is executed for it on a test machine. Student submissions are marked as valid if this script was successful.")
    validity_script_download = models.BooleanField(default=False, verbose_name='Download of validation script ?', help_text='If activated, the students can download the validation script for offline analysis.')
    attachment_test_full = models.FileField(upload_to="testscripts", blank=True, null=True, verbose_name='Full test script', help_text='Same as the validation script, but executed AFTER the hard deadline to determine final grading criterias for the submission. Results are not shown to students.')
    test_machines = models.ManyToManyField('TestMachine', blank=True, related_name="assignments", help_text="The test machines that will take care of submissions for this assignment.")

    class Meta:
        app_label = 'opensubmit'

    def directory_name(self):
        ''' The assignment name in a format that is suitable for a directory name.  '''
        return self.title.replace(" ", "_").replace("\\", "_").replace(",","").lower()

    def gradable_submissions(self):
        qs = self.valid_submissions()
        qs = qs.filter(state__in=[Submission.GRADING_IN_PROGRESS, Submission.SUBMITTED_TESTED, Submission.TEST_FULL_FAILED, Submission.SUBMITTED])
        return qs

    def grading_unfinished_submissions(self):
        qs = self.valid_submissions()
        qs = qs.filter(state__in=[Submission.GRADING_IN_PROGRESS])
        return qs

    def graded_submissions(self):
        qs = self.valid_submissions().filter(state__in=[Submission.GRADED])
        return qs

    def grading_url(self):
        '''
            Determines the teacher backend link to the filtered list of gradable submissions for this assignment.
        '''
        grading_url="%s?coursefilter=%u&assignmentfilter=%u&statefilter=tobegraded"%(
                            reverse('teacher:opensubmit_submission_changelist'),
                            self.course.pk, self.pk
                        )
        return grading_url

    def authors(self):
        qs = self.valid_submissions().values_list('authors',flat=True).distinct()
        return qs

    def valid_submissions(self):
        qs = self.submissions.exclude(state=Submission.WITHDRAWN)
        return qs

    def uploads(self):
        '''
            Return a queryset for all non-replaced file uploads for  this assignment.
        '''
        from .submissionfile import SubmissionFile
        return SubmissionFile.valid_ones.filter(submissions__assignment=self)

    def uploads_by_md5(self):
        '''
           Return uploads, but ordered by MD5 sum. Crucial for duplicate view regroup to work properly.
        '''
        return self.uploads().order_by('md5')

    def has_perf_results(self):
        '''
            Figure out if any submission for this assignment has performance data being available.
        '''
        num_results = SubmissionTestResult.objects.filter(perf_data__isnull=False).filter(submission_file__submissions__assignment=self).count()
        return num_results != 0

    def validity_test_url(self):
        '''
            Return absolute download URL for validity test script.
            Using reverse() seems to be broken with FORCE_SCRIPT in use, so we use direct URL formulation.
        '''
        if self.pk and self.has_validity_test():
            return settings.MAIN_URL + "/download/%u/validity_testscript/secret=%s" % (self.pk, settings.JOB_EXECUTOR_SECRET)
        else:
            return None

    def full_test_url(self):
        '''
            Return absolute download URL for full test script.
            Using reverse() seems to be broken with FORCE_SCRIPT in use, so we use direct URL formulation.
        '''
        if self.pk and self.has_full_test():
            return settings.MAIN_URL + "/download/%u/full_testscript/secret=%s" % (self.pk, settings.JOB_EXECUTOR_SECRET)
        else:
            return None

    def has_validity_test(self):
        return str(self.attachment_test_validity).strip() != ""

    def has_full_test(self):
        return str(self.attachment_test_full).strip() != ""

    def attachment_is_tested(self):
        return self.attachment_test_compile is True or self.has_validity_test() or self.has_full_test()

    def __unicode__(self):
        return unicode(self.title)

    def can_create_submission(self, user=None):
        '''
            Central access control for submitting things related to assignments.
        '''

        if user:
            # Super users, course owners and tutors should be able to test their validations
            # before the submission is officially possible.
            # They should also be able to submit after the deadline.
            if user.is_superuser or user is self.course.owner or self.course.tutors.filter(pk=user.pk).exists():
                return True
            if self.course not in user.profile.user_courses():
                # The user is not enrolled in this assignment's course.
                return False

            if user.authored.filter(assignment=self).exclude(state=Submission.WITHDRAWN).count() > 0:
                # User already has a valid submission for this assignment.
                return False

        if self.hard_deadline < timezone.now():
            # Hard deadline has been reached.
            return False

        if self.publish_at > timezone.now():
            # The assignment has not yet been published.
            return False

        return True

    def authors_valid(self, authors=()):
        for author in authors:
            if not self.can_create_submission(author):
                return False

        return True
