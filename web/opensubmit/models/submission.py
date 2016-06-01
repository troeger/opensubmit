from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail, EmailMessage
from django.utils import timezone
from django.core.urlresolvers import reverse

from datetime import datetime
import tempfile, zipfile, tarfile
from django.utils.encoding import smart_text

from .submissionfile import upload_path, SubmissionFile
from .submissiontestresult import SubmissionTestResult

from django.conf import settings

import logging
logger = logging.getLogger('OpenSubmit')

class ValidSubmissionsManager(models.Manager):
    '''
        A model manager used by the Submission model. It returns a sorted list
        of submissions that are not withdrawn.
    '''

    def get_queryset(self):
        submissions = Submission.objects.exclude(
                state__in=[Submission.WITHDRAWN, Submission.RECEIVED]).order_by('pk')
        return submissions

class PendingStudentTestsManager(models.Manager):
    '''
        A model manager used by the Submission model. It returns a sorted list
        of executor work to be done that relates to compilation and
        validation test jobs for students.
        The basic approach is that compilation should happen before validation in FIFO order,
        under the assumption is that the time effort is increasing.
    '''

    def get_queryset(self):
        jobs = Submission.objects.filter(
            state__in=[ Submission.TEST_COMPILE_PENDING,
                        Submission.TEST_VALIDITY_PENDING]
            ).order_by('state').order_by('-modified')
        return jobs

class PendingFullTestsManager(models.Manager):
    '''
        A model manager used by the Submission model. It returns a sorted list
        of full test executor work to be done.
        The basic approach is that non-graded job validation wins over closed job
        re-evaluation triggered by the teachers,
        under the assumption is that the time effort is increasing.
    '''

    def get_queryset(self):
        jobs = Submission.objects.filter(
            state__in=[ Submission.TEST_FULL_PENDING,
                        Submission.CLOSED_TEST_FULL_PENDING]
            ).order_by('-state').order_by('-modified')
        return jobs

class PendingTestsManager(models.Manager):
    '''
        A combination of both, with focus on getting the full tests later than the validity tests.
    '''
    def get_queryset(self):
        jobs = Submission.objects.filter(
            state__in=[ Submission.TEST_FULL_PENDING,           # PF
                        Submission.CLOSED_TEST_FULL_PENDING,    # CT
                        Submission.TEST_COMPILE_PENDING,        # PC
                        Submission.TEST_VALIDITY_PENDING ]      # PV
            ).order_by('-state').order_by('-modified')
        return jobs


class Submission(models.Model):
    '''
        A student submission for an assignment.
    '''

    RECEIVED = 'R'                   # Only for initialization, this should never persist
    WITHDRAWN = 'W'                  # Withdrawn by the student
    SUBMITTED = 'S'                  # Submitted, no tests so far
    TEST_COMPILE_PENDING = 'PC'      # Submitted, compile test planned
    TEST_COMPILE_FAILED = 'FC'       # Submitted, compile test failed
    TEST_VALIDITY_PENDING = 'PV'     # Submitted, validity test planned
    TEST_VALIDITY_FAILED = 'FV'      # Submitted, validity test failed
    TEST_FULL_PENDING = 'PF'         # Submitted, full test planned
    TEST_FULL_FAILED = 'FF'          # Submitted, full test failed
    SUBMITTED_TESTED = 'ST'          # Submitted, all tests performed, grading planned
    GRADING_IN_PROGRESS = 'GP'       # Grading in progress, but not finished
    GRADED = 'G'                     # Graded, student notification not done
    CLOSED = 'C'                     # Graded, student notification done
    CLOSED_TEST_FULL_PENDING = 'CT'  # Keep grading status, full test planned
    STATES = (                       # States from the backend point of view
        (RECEIVED, 'Received'),
        (WITHDRAWN, 'Withdrawn'),
        (SUBMITTED, 'Submitted'),
        (TEST_COMPILE_PENDING, 'Compilation test pending'),
        (TEST_COMPILE_FAILED, 'Compilation test failed'),
        (TEST_VALIDITY_PENDING, 'Validity test pending'),
        (TEST_VALIDITY_FAILED, 'Validity test failed'),
        (TEST_FULL_PENDING, 'Full test pending'),
        (TEST_FULL_FAILED, 'All but full test passed, grading pending'),
        (SUBMITTED_TESTED, 'All tests passed, grading pending'),
        (GRADING_IN_PROGRESS, 'Grading not finished'),
        (GRADED, 'Grading finished'),
        (CLOSED, 'Closed, student notified'),
        (CLOSED_TEST_FULL_PENDING, 'Closed, full test pending')
    )
    STUDENT_STATES = (              # States from the student point of view
        (RECEIVED, 'Received'),
        (WITHDRAWN, 'Withdrawn'),
        (SUBMITTED, 'Waiting for grading'),
        (TEST_COMPILE_PENDING, 'Waiting for compilation test'),
        (TEST_COMPILE_FAILED, 'Compilation failed'),
        (TEST_VALIDITY_PENDING, 'Waiting for validation test'),
        (TEST_VALIDITY_FAILED, 'Validation failed'),
        (TEST_FULL_PENDING, 'Waiting for grading'),
        (TEST_FULL_FAILED, 'Waiting for grading'),
        (SUBMITTED_TESTED, 'Waiting for grading'),
        (GRADING_IN_PROGRESS, 'Waiting for grading'),
        (GRADED, 'Waiting for grading'),
        (CLOSED, 'Graded'),
        (CLOSED_TEST_FULL_PENDING, 'Graded')
    )

    assignment = models.ForeignKey('Assignment', related_name='submissions')
    submitter = models.ForeignKey(User, related_name='submitted')
    authors = models.ManyToManyField(User, related_name='authored') # includes also submitter, see submission_post_save() handler
    notes = models.TextField(max_length=200, blank=True)
    file_upload = models.ForeignKey('SubmissionFile', related_name='submissions', blank=True, null=True, verbose_name='New upload')
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False, blank=True, null=True)
    grading = models.ForeignKey('Grading', blank=True, null=True)
    grading_notes = models.TextField(max_length=10000, blank=True, null=True, help_text="Specific notes about the grading for this submission.")
    grading_file = models.FileField(upload_to=upload_path, blank=True, null=True, help_text="Additional information about the grading as file.")
    state = models.CharField(max_length=2, choices=STATES, default=RECEIVED)

    objects = models.Manager()
    pending_student_tests = PendingStudentTestsManager()
    pending_full_tests = PendingFullTestsManager()
    pending_tests = PendingTestsManager()
    valid_ones = ValidSubmissionsManager()

    class Meta:
        app_label = 'opensubmit'

    @staticmethod
    def qs_valid(qs):
        '''
            A filtering of the given Submission queryset for all submissions that were successfully validated. This includes the following cases:

            - The submission was submitted and there are no tests.
            - The submission was successfully validity-tested, regardless of the full test status (not existent / failed / success).
            - The submission was graded or the grading was already started.
            - The submission was closed.

            The idea is to get all submissions that were a valid solution, regardless of the point in time where you check the list.
        '''
        return qs.filter(state__in=[Submission.SUBMITTED, Submission.SUBMITTED_TESTED, Submission.TEST_FULL_FAILED, Submission.GRADING_IN_PROGRESS, Submission.GRADED, Submission.CLOSED, Submission.CLOSED_TEST_FULL_PENDING])

    @staticmethod
    def qs_tobegraded(qs):
        '''
            A filtering of the given Submission queryset for all submissions that are gradeable. This includes the following cases:

            - The submission was submitted and there are no tests.
            - The submission was successfully validity-tested, regardless of the full test status (not existent / failed / success).
            - The grading was already started, but not finished.

            The idea is to get a list of work to be done for the correctors.
        '''
        return qs.filter(state__in=[Submission.SUBMITTED, Submission.SUBMITTED_TESTED, Submission.TEST_FULL_FAILED, Submission.GRADING_IN_PROGRESS])

    @staticmethod
    def qs_notified(qs):
        '''
            A filtering of the given Submission queryset for all submissions were students already got notification about their grade. This includes the following cases:

            - The submission was closed.
            - The submission was closed and full tests were re-started.

            The idea is to get indirectly a list of emails that went out.
        '''
        return qs.filter(state__in=[Submission.CLOSED, Submission.CLOSED_TEST_FULL_PENDING])

    @staticmethod
    def qs_notwithdrawn(qs):
        '''
            A filtering of the given Submission queryset for all submissions that were not withdrawn. This excludes the following cases:

            - The submission was withdrawn.
            - The submission was received and never left that status due to an error.

            The idea is a list of all submissions, but without the garbage.
        '''
        return qs.exclude(state__in=[Submission.WITHDRAWN, Submission.RECEIVED])

    def __unicode__(self):
        if self.pk:
            return unicode("%u" % (self.pk))
        else:
            return unicode("New Submission instance")

    def log(self, level, format_string, *args, **kwargs):
        level_mapping = {
            'CRITICAL': logging.CRITICAL,
            'ERROR': logging.ERROR,
            'WARNING': logging.WARNING,
            'INFO': logging.INFO,
            'DEBUG': logging.DEBUG,
            'NOTSET': logging.NOTSET,
        }
        level_numeric = level_mapping[level] if level in level_mapping else level_mapping['NOTSET']
        if self.pk:
            log_prefix = "<{} pk={}>".format(self.__class__.__name__, self.pk)
        else:
            log_prefix = "<{} new>".format(self.__class__.__name__)
        return logger.log(level_numeric, "{} {}".format(log_prefix, format_string.format(*args, **kwargs)))

    def can_modify(self, user=None):
        """Determines whether the submission can be modified.
        Returns a boolean value.
        The 'user' parameter is optional and additionally checks whether
        the given user is authorized to perform these actions.

        This function checks the submission states and assignment deadlines."""

        # The user must be authorized to commit these actions.
        if user and not self.user_can_modify(user):
            self.log('DEBUG', "Submission cannot be modified, user is not an authorized user ({!r} not in {!r})", user, self.authorized_users)
            return False

        # Modification of submissions, that are withdrawn, graded or currently being graded, is prohibited.
        if self.state in [self.WITHDRAWN, self.GRADED, self.GRADING_IN_PROGRESS, ]:
            self.log('DEBUG', "Submission cannot be modified, is in state '{}'", self.state)
            return False

        # Modification of closed submissions is prohibited.
        if self.is_closed():
            self.log('DEBUG', "Submission cannot be modified, is closed")
            return False

        # Submissions, that are executed right now, cannot be modified
        if self.state in [self.TEST_COMPILE_PENDING, self.TEST_VALIDITY_PENDING, self.TEST_FULL_PENDING, ]:
            if not self.file_upload:
                self.log('CRITICAL', "Submission is in invalid state! State is '{}', but there is no file uploaded!", self.state)
                raise AssertionError()
                return False
            if self.file_upload.is_executed():
                # The above call informs that the uploaded file is being executed, or execution has been completed.
                # Since the current state is 'PENDING', the execution cannot yet be completed.
                # Thus, the submitted file is being executed right now.
                return False

        # Submissions must belong to an assignment.
        if not self.assignment:
            self.log('CRITICAL', "Submission does not belong to an assignment!")
            raise AssertionError()

        # Submissions, that belong to an assignment where the hard deadline has passed,
        # cannot be modified.
        if timezone.now() > self.assignment.hard_deadline:
            self.log('DEBUG', "Submission cannot be modified - assignment's hard deadline has passed (hard deadline is: {})", self.assignment.hard_deadline)
            return False

        # The soft deadline has no effect (yet).
        if self.assignment.soft_deadline:
            if timezone.now() > self.assignment.soft_deadline:
                # The soft deadline has passed
                pass  # do nothing.

        #self.log('DEBUG', "Submission can be modified.")
        return True

    def can_withdraw(self, user=None):
        """Determines whether a submisison can be withdrawn.
        Returns a boolean value.

        Requires: can_modify.

        Currently, the conditions for modifications and withdrawal are the same."""
        return self.can_modify(user=user)

    def can_reupload(self, user=None):
        """Determines whether a submission can be re-uploaded.
        Returns a boolean value.

        Requires: can_modify.

        Re-uploads are allowed only when test executions have failed."""

        # Re-uploads are allowed only when test executions have failed.
        if self.state not in (self.TEST_COMPILE_FAILED, self.TEST_VALIDITY_FAILED, self.TEST_FULL_FAILED, ):
            return False

        # It must be allowed to modify the submission.
        if not self.can_modify(user=user):
            return False

        return True

    def user_can_modify(self, user):
        """Determines whether a user is allowed to modify a specific submission in general.
        Returns a boolean value.

        A user is authorized when he is part of the authorized users (submitter and authors)."""
        return user in self.authorized_users

    @property
    def authorized_users(self):
        """Returns a list of all authorized users (submitter and additional authors)."""
        return [self.submitter, ] + list(self.authors.all())

    def is_withdrawn(self):
        return self.state == self.WITHDRAWN

    def is_closed(self):
        return self.state in [self.CLOSED, self.CLOSED_TEST_FULL_PENDING]

    def is_grading_finished(self):
        return self.state in [self.GRADED, self.CLOSED, self.CLOSED_TEST_FULL_PENDING]

    def show_grading(self):
        return self.is_closed()

    def get_initial_state(self):
        '''
            Return first state for this submission after upload,
            which depends on the kind of assignment.
        '''
        if not self.assignment.attachment_is_tested():
            return Submission.SUBMITTED
        else:
            if self.assignment.attachment_test_compile:
                return Submission.TEST_COMPILE_PENDING
            elif self.assignment.attachment_test_validity:
                return Submission.TEST_VALIDITY_PENDING
            elif self.assignment.attachment_test_full:
                return Submission.TEST_FULL_PENDING

    def state_for_students(self):
        '''
            Return human-readable description of current state for students.
        '''
        return dict(self.STUDENT_STATES)[self.state]

    def state_for_tutors(self):
        '''
            Return human-readable description of current state for tutors.
        '''
        return dict(self.STATES)[self.state]

    def grading_file_url(self):
        # to implement access protection, we implement our own download
        # this implies that the Apache media serving is disabled
        return reverse('download', args=(self.pk, 'grading_file', ))

    def _save_test_result(self, machine, text, kind, perf_data):
        result = SubmissionTestResult(
            result=text,
            machine=machine,
            kind=kind,
            perf_data=perf_data,
            submission_file=self.file_upload)
        result.save()

    def _get_test_result(self, kind):
        try:
            return self.file_upload.test_results.filter(kind=kind).order_by('-created')[0]
        except:
            return None

    def save_fetch_date(self):
        SubmissionFile.objects.filter(pk=self.file_upload.pk).update(fetched=datetime.now())

    def get_fetch_date(self):
        return self.file_upload.fetched

    def clean_fetch_date(self):
        SubmissionFile.objects.filter(pk=self.file_upload.pk).update(fetched=None)

    def save_compile_result(self, machine, text):
        self._save_test_result(machine, text, SubmissionTestResult.COMPILE_TEST, None)

    def save_validation_result(self, machine, text, perf_data):
        self._save_test_result(machine, text, SubmissionTestResult.VALIDITY_TEST, perf_data)

    def save_fulltest_result(self, machine, text, perf_data):
        self._save_test_result(machine, text, SubmissionTestResult.FULL_TEST, perf_data)

    def get_compile_result(self):
        '''
            Return the most recent compile result object for this submission.
        '''
        return self._get_test_result(SubmissionTestResult.COMPILE_TEST)

    def get_validation_result(self):
        '''
            Return the most recent validity test result object for this submission.
        '''
        return self._get_test_result(SubmissionTestResult.VALIDITY_TEST)

    def get_fulltest_result(self):
        '''
            Return the most recent full test result object for this submission.
        '''
        return self._get_test_result(SubmissionTestResult.FULL_TEST)

    def inform_student(self, state):
        '''
            Create a mail message for the student, based on the given submission state.
            We hand-in explicitely about which new state we want to inform, since this may not be reflected
            in the model at the moment.
        '''
        # we cannot send eMail on SUBMITTED_TESTED, since this may have been triggered by test repitition in the backend
        if state == Submission.TEST_COMPILE_FAILED:
            subject = 'Warning: Your submission did not pass the compilation test'
            message = u'Hi,\n\nthis is a short automated notice that your submission for "%s" in "%s" did not pass the automated compilation test. You need to update the uploaded files for a valid submission.\n\n Further information can be found at %s.\n\n'
            message = message % (self.assignment, self.assignment.course, settings.MAIN_URL)

        elif state == Submission.TEST_VALIDITY_FAILED:
            subject = 'Warning: Your submission did not pass the validation test'
            message = u'Hi,\n\nthis is a short automated notice that your submission for "%s" in "%s" did not pass the automated validation test. You need to update the uploaded files for a valid submission.\n\n Further information can be found at %s.\n\n'
            message = message % (self.assignment, self.assignment.course, settings.MAIN_URL)

        elif state == Submission.CLOSED:
            subject = 'Grading completed'
            message = u'Hi,\n\nthis is a short automated notice that your submission for "%s" in "%s" was graded.\n\n Further information can be found at %s.\n\n'
            message = message % (self.assignment, self.assignment.course, settings.MAIN_URL)
        else:
            return

        subject = "[%s] %s" % (self.assignment.course, subject)
        from_email = self.assignment.course.owner.email
        recipients = self.authors.values_list('email', flat=True).distinct().order_by('email')
        # send student email with BCC to course owner.
        # TODO: This might be configurable later
        # email = EmailMessage(subject, message, from_email, recipients, [self.assignment.course.owner.email])
        email = EmailMessage(subject, message, from_email, recipients)
        email.send(fail_silently=True)

    def inform_course_owner(self, request):
        if self.state == Submission.WITHDRAWN:
            subject = "Submission withdrawn"
            message = "Withdrawn solution %u for '%s'" % (self.pk, self.assignment)

        elif self.state == Submission.SUBMITTED:
            subject = "Submission ready for grading"
            message = "Solution for '%s' that is ready for grading." % (self.assignment)

        elif self.state == Submission.SUBMITTED_TESTED:
            subject = "Submission tested and ready for grading"
            message = "Solution for '%s' that was tested and is ready for grading." % (self.assignment)

        else:
            subject = "Submission changed state"
            message = "Submission has now the state '%s'." % (self.STATES[self.state])

        from_email = self.assignment.course.owner.email
        recipients = [self.assignment.course.owner.email]
        # TODO: Make this configurable, some course owners got annoyed by this
        # send_mail(subject, message, from_email, recipients, fail_silently=True)

    def info_file(self):
        '''
            Prepares a temporary file with information about the submission.
            Closing it will delete it, which must be considered by the caller.
        '''
        info = tempfile.NamedTemporaryFile()
        info.write("Submission ID:\t%u\n" % self.pk)
        info.write("Submitter:\t%s (%u)\n" % (self.submitter.get_full_name().encode('utf-8'), self.submitter.pk))
        info.write("Authors:\n")
        for auth in self.authors.all():
            info.write("\t%s (%u)\n" % (auth.get_full_name().encode('utf-8'), auth.pk))
        info.write("\n")
        info.write("Creation:\t%s\n" % str(self.created))
        info.write("Last modification:\t%s\n" % str(self.modified))
        info.write("Status:\t%s\n" % self.state_for_students())
        if self.grading:
            info.write("Grading:\t%s\n" % str(self.grading))
        if self.notes:
            notes = smart_text(self.notes).encode('utf8')
            info.write("Author notes:\n-------------\n%s\n\n" % notes)
        if self.grading_notes:
            notes = smart_text(self.grading_notes).encode('utf8')
            info.write("Grading notes:\n--------------\n%s\n\n" % notes)
        info.flush()    # no closing here, because it disappears then
        return info

    def copy_file_upload(self, targetdir):
        '''
            Copies the currently valid file upload into the given directory.
            If possible, the content is un-archived in the target directory.
        '''
        assert(self.file_upload)
        # unpack student data to temporary directory
        # os.chroot is not working with tarfile support
        tempdir = tempfile.mkdtemp()
        try:
            if zipfile.is_zipfile(self.file_upload.absolute_path()):
                f = zipfile.ZipFile(self.file_upload.absolute_path(), 'r')
                f.extractall(targetdir)
            elif tarfile.is_tarfile(self.file_upload.absolute_path()):
                tar = tarfile.open(self.file_upload.absolute_path())
                tar.extractall(targetdir)
                tar.close()
            else:
                # unpacking not possible, just copy it
                shutil.copyfile(self.file_upload.absolute_path(), targetdir + "/" + self.file_upload.basename())
        except IOError:
            logger.error("I/O exception while accessing %s."%(self.file_upload.absolute_path()))
            pass

