from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.urlresolvers import reverse

from datetime import datetime
import tempfile
import zipfile
import tarfile

from opensubmit import mails

from .submissionfile import upload_path, SubmissionFile
from .submissiontestresult import SubmissionTestResult

import logging
import shutil
import os
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
            state=Submission.TEST_VALIDITY_PENDING).order_by('-modified')
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
            state__in=[Submission.TEST_FULL_PENDING,
                       Submission.CLOSED_TEST_FULL_PENDING]
        ).order_by('-state').order_by('-modified')
        return jobs


class PendingTestsManager(models.Manager):
    '''
        A combination of both, with focus on getting the full tests later than the validity tests.
    '''

    def get_queryset(self):
        jobs = Submission.objects.filter(
            state__in=[Submission.TEST_FULL_PENDING,           # PF
                       Submission.CLOSED_TEST_FULL_PENDING,    # CT
                       Submission.TEST_VALIDITY_PENDING]      # PV
        ).order_by('-state').order_by('-modified')
        return jobs


class Submission(models.Model):
    '''
        A student submission for an assignment.
    '''

    RECEIVED = 'R'                   # Only for initialization, this should never persist
    WITHDRAWN = 'W'                  # Withdrawn by the student
    SUBMITTED = 'S'                  # Submitted, no tests so far
    TEST_VALIDITY_PENDING = 'PV'     # Submitted, validity test planned
    TEST_VALIDITY_FAILED = 'FV'      # Submitted, validity test failed
    TEST_FULL_PENDING = 'PF'         # Submitted, full test planned
    TEST_FULL_FAILED = 'FF'          # Submitted, full test failed
    SUBMITTED_TESTED = 'ST'          # Submitted, all tests performed, grading planned
    GRADING_IN_PROGRESS = 'GP'       # Grading in progress, but not finished
    GRADED = 'G'                     # Graded, student notification not done
    CLOSED = 'C'                     # Graded, student notification done
    CLOSED_TEST_FULL_PENDING = 'CT'  # Keep grading status, full test planned

    # Docs start: States
    # State description in teacher backend
    STATES = (

        # The submission is currently uploaded,
        # some internal processing still takes place.
        (RECEIVED, 'Received'),

        # The submission was withdrawn by the student
        # before the deadline. No further automated action
        # will take place with this submission.
        (WITHDRAWN, 'Withdrawn'),

        # The submission is completely uploaded.
        # If code validation is configured, the state will
        # directly change to TEST_VALIDITY_PENDING.
        (SUBMITTED, 'Submitted'),

        # The submission is waiting to be validated with the
        # validation script on one of the test machines.
        # The submission remains in this state until some
        # validation result was sent from the test machines.
        (TEST_VALIDITY_PENDING, 'Validity test pending'),

        # The validation of the student sources on the
        # test machine failed. No further automated action will
        # take place with this submission.
        # The students get informed by email.
        (TEST_VALIDITY_FAILED, 'Validity test failed'),

        # The submission is waiting to be checked with the
        # full test script on one of the test machines.
        # The submission remains in this state until
        # some result was sent from the test machines.
        (TEST_FULL_PENDING, 'Full test pending'),

        # The (compilation and) validation of the student
        # sources on the test machine worked, only the full test
        # failed. No further automated action will take place with
        # this submission.
        (TEST_FULL_FAILED, 'All but full test passed, grading pending'),

        # The compilation (if configured) and the validation and
        #  the full test (if configured) of the submission were
        # successful. No further automated action will take
        # place with this submission.
        (SUBMITTED_TESTED, 'All tests passed, grading pending'),

        # Some grading took place in the teacher backend,
        # and the submission was explicitly marked with
        # 'grading not finished'. This allows correctors to have
        # multiple runs over the submissions and see which
        # of the submissions were already investigated.
        (GRADING_IN_PROGRESS, 'Grading not finished'),

        # Some grading took place in the teacher backend,
        # and the submission was explicitly marked with
        # 'grading not finished'. This allows correctors
        # to have multiple runs over the submissions and
        #  see which of the submissions were already investigated.
        (GRADED, 'Grading finished'),

        # The submission is closed, meaning that in the
        # teacher backend, the submission was marked
        # as closed to trigger the student notification
        # for their final assignment grades.
        # Students are notified by email.
        (CLOSED, 'Closed, student notified'),

        # The submission is closed, but marked for
        # another full test run.
        # This is typically used to have some post-assignment
        # analysis of student submissions
        # by the help of full test scripts.
        # Students never get any notification about this state.
        (CLOSED_TEST_FULL_PENDING, 'Closed, full test pending')
    )

    # State description in student dashboard
    STUDENT_STATES = (
        (RECEIVED, 'Received'),
        (WITHDRAWN, 'Withdrawn'),
        (SUBMITTED, 'Waiting for grading'),
        (TEST_VALIDITY_PENDING, 'Waiting for validation test'),
        (TEST_VALIDITY_FAILED, 'Validation failed'),
        (TEST_FULL_PENDING, 'Waiting for grading'),
        (TEST_FULL_FAILED, 'Waiting for grading'),
        (SUBMITTED_TESTED, 'Waiting for grading'),
        (GRADING_IN_PROGRESS, 'Waiting for grading'),
        (GRADED, 'Waiting for grading'),
        (CLOSED, 'Done'),
        (CLOSED_TEST_FULL_PENDING, 'Done')
    )
    # Docs end: States    

    assignment = models.ForeignKey('Assignment', related_name='submissions')
    submitter = models.ForeignKey(User, related_name='submitted')
    # includes also submitter, see submission_post_save() handler
    authors = models.ManyToManyField(User, related_name='authored')
    notes = models.TextField(max_length=200, blank=True)
    file_upload = models.ForeignKey(
        'SubmissionFile', related_name='submissions', blank=True, null=True, verbose_name='New upload')
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(
        auto_now=True, editable=False, blank=True, null=True)
    grading = models.ForeignKey('Grading', blank=True, null=True)
    grading_notes = models.TextField(max_length=10000, blank=True, null=True,
                                     help_text="Specific notes about the grading for this submission.")
    grading_file = models.FileField(upload_to=upload_path, blank=True, null=True,
                                    help_text="Additional information about the grading as file.")
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

    def __str__(self):
        if self.pk:
            return str(self.pk)
        else:
            return "New Submission instance"

    def author_list(self):
        ''' The list of authors als text, for admin submission list overview.'''
        author_list = [self.submitter] + \
            [author for author in self.authors.all().exclude(pk=self.submitter.pk)]
        return ",\n".join([author.get_full_name() for author in author_list])
    author_list.admin_order_field = 'submitter'

    def course(self):
        ''' The course of this submission as text, for admin submission list overview.'''
        return self.assignment.course
    course.admin_order_field = 'assignment__course'

    def grading_status_text(self):
        '''
        A rendering of the grading that is an answer on the question
        "Is grading finished?".
        Used in duplicate view and submission list on the teacher backend.
        '''
        if self.assignment.is_graded():
            if self.is_grading_finished():
                return str('Yes ({0})'.format(self.grading))
            else:
                return str('No')
        else:
            return str('Not graded')
    grading_status_text.admin_order_field = 'grading__title'
    grading_status_text.short_description = "Grading finished?"

    def has_grading_notes(self):
        ''' Determines if the submission has grading notes.
            Used for submission list overview in teacher backend.
        '''
        if self.grading_notes is not None and len(self.grading_notes) > 0:
            return True
        else:
            return False
    has_grading_notes.short_description = "Grading notes?"
    has_grading_notes.admin_order_field = 'grading_notes'
    has_grading_notes.boolean = True            # show nice little icon

    def grading_value_text(self):
        '''
        A rendering of the grading that is an answer to the question
        "What is the grade?".
        '''
        if self.assignment.is_graded():
            if self.is_grading_finished():
                return str(self.grading)
            else:
                return str('pending')
        else:
            if self.is_grading_finished():
                return str('done')
            else:
                return str('not done')

    def grading_means_passed(self):
        '''
        Information if the given grading means passed.
        Non-graded assignments are always passed.
        '''
        if self.assignment.is_graded():
            if self.grading and self.grading.means_passed:
                return True
            else:
                return False
        else:
            return True

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
            #self.log('DEBUG', "Submission cannot be modified, user is not an authorized user ({!r} not in {!r})", user, self.authorized_users)
            return False

        # Modification of submissions, that are withdrawn, graded or currently being graded, is prohibited.
        if self.state in [self.WITHDRAWN, self.GRADED, self.GRADING_IN_PROGRESS, ]:
            #self.log('DEBUG', "Submission cannot be modified, is in state '{}'", self.state)
            return False

        # Modification of closed submissions is prohibited.
        if self.is_closed():
            if self.assignment.is_graded():
                # There is a grading procedure, so taking it back would invalidate the tutors work
                #self.log('DEBUG', "Submission cannot be modified, it is closed and graded")
                return False
            else:
                #self.log('DEBUG', "Closed submission can be modified, since it has no grading scheme.")
                return True

        # Submissions, that are executed right now, cannot be modified
        if self.state in [self.TEST_VALIDITY_PENDING, self.TEST_FULL_PENDING]:
            if not self.file_upload:
                self.log(
                    'CRITICAL', "Submission is in invalid state! State is '{}', but there is no file uploaded!", self.state)
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
        if self.assignment.hard_deadline and timezone.now() > self.assignment.hard_deadline:
            #self.log('DEBUG', "Submission cannot be modified - assignment's hard deadline has passed (hard deadline is: {})", self.assignment.hard_deadline)
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
        if self.state not in (self.TEST_VALIDITY_FAILED, self.TEST_FULL_FAILED):
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
        return self.assignment.gradingScheme != None and self.is_closed()

    def get_initial_state(self):
        '''
            Return first state for this submission after upload,
            which depends on the kind of assignment.
        '''
        if not self.assignment.attachment_is_tested():
            return Submission.SUBMITTED
        else:
            if self.assignment.attachment_test_validity:
                return Submission.TEST_VALIDITY_PENDING
            elif self.assignment.attachment_test_full:
                return Submission.TEST_FULL_PENDING

    def state_for_students(self):
        '''
            Return human-readable description of current state for students.
        '''
        try:
            return dict(self.STUDENT_STATES)[self.state]
        except:
            # deal with old databases that have pre 0.7 states, such as "FC"
            return "Unknown"

    def state_for_tutors(self):
        '''
            Return human-readable description of current state for tutors.
        '''
        return dict(self.STATES)[self.state]

    def grading_file_url(self):
        # to implement access protection, we implement our own download
        # this implies that the Apache media serving is disabled
        return reverse('submission_grading_file', args=(self.pk,))

    def _save_test_result(self, machine, text_student, text_tutor, kind, perf_data):
        result = SubmissionTestResult(
            result=text_student,
            result_tutor=text_tutor,
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
        SubmissionFile.objects.filter(
            pk=self.file_upload.pk).update(fetched=datetime.now())

    def get_fetch_date(self):
        return self.file_upload.fetched

    def clean_fetch_date(self):
        SubmissionFile.objects.filter(
            pk=self.file_upload.pk).update(fetched=None)

    def save_validation_result(self, machine, text_student, text_tutor, perf_data=None):
        self._save_test_result(
            machine, text_student, text_tutor, SubmissionTestResult.VALIDITY_TEST, perf_data)

    def save_fulltest_result(self, machine, text_tutor, perf_data=None):
        self._save_test_result(
            machine, None, text_tutor, SubmissionTestResult.FULL_TEST, perf_data)

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
            We hand-in explicitely about which new state we want to inform,
            since this may not be reflected in the model at the moment.
        '''
        mails.inform_student(self, state)

    def info_file(self, delete=True):
        '''
            Prepares an open temporary file with information about the submission.
            Closing it will delete it, which must be considered by the caller.
            This file is not readable, since the tempfile library wants either readable or writable files.
        '''
        info = tempfile.NamedTemporaryFile(
            mode='wt', encoding='utf-8', delete=delete)
        info.write("Submission ID:\t%u\n" % self.pk)
        info.write("Submitter:\t%s (%u)\n" %
                   (self.submitter.get_full_name(), self.submitter.pk))
        info.write("Authors:\n")
        for auth in self.authors.all():
            info.write("\t%s (%u)\n" % (auth.get_full_name(), auth.pk))
        info.write("\n")
        info.write("Creation:\t%s\n" % str(self.created))
        info.write("Last modification:\t%s\n" % str(self.modified))
        info.write("Status:\t%s\n" % self.state_for_students())
        if self.grading:
            info.write("Grading:\t%s\n" % str(self.grading))
        if self.notes:
            notes = self.notes
            info.write("Author notes:\n-------------\n%s\n\n" % notes)
        if self.grading_notes:
            notes = self.grading_notes
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
                shutil.copyfile(self.file_upload.absolute_path(),
                                targetdir + "/" + self.file_upload.basename())
        except IOError:
            logger.error("I/O exception while accessing %s." %
                         (self.file_upload.absolute_path()))
            pass

    def add_to_zipfile(self, z):
        submitter = "user" + str(self.submitter.pk)
        assdir = self.assignment.directory_name_with_course()
        if self.modified:
            modified = self.modified.strftime("%Y_%m_%d_%H_%M_%S")
        else:
            modified = self.created.strftime("%Y_%m_%d_%H_%M_%S")
        state = self.state_for_students().replace(" ", "_").lower()
        submdir = "%s/%u_%s/" % (assdir, self.pk, state)
        if self.file_upload:
            # Copy student upload
            tempdir = tempfile.mkdtemp()
            self.copy_file_upload(tempdir)
            # Add content to final ZIP file
            allfiles = [(subdir, files)
                        for (subdir, dirs, files) in os.walk(tempdir)]
            for subdir, files in allfiles:
                for f in files:
                    zip_relative_dir = subdir.replace(tempdir, "")
                    zip_relative_file = '%s/%s' % (zip_relative_dir, f)
                    z.write(subdir + "/" + f, submdir + 'student_files/%s' %
                            zip_relative_file, zipfile.ZIP_DEFLATED)
        # add text file with additional information
        info = self.info_file()
        z.write(info.name, submdir + "info.txt")
