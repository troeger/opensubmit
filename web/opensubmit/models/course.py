from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.urlresolvers import reverse

from .assignment import Assignment
from .submission import Submission

class ValidCoursesManager(models.Manager):
    '''
        A model manager used by the Course model. It returns a sorted list
        of courses that are not inactive.
    '''

    def get_queryset(self):
        return Course.objects.exclude(active=False).order_by('title')

class Course(models.Model):
    title = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    owner = models.ForeignKey(User, related_name='courses', help_text="Only this user can change the course details and create new assignments.")
    tutors = models.ManyToManyField(User, blank=True, related_name='courses_tutoring', help_text="These users can edit / grade submissions for the course.")
    homepage = models.URLField(max_length=200, verbose_name="Course description link")
    active = models.BooleanField(default=True, help_text="Only assignments and submissions of active courses are shown to students and tutors. Use this flag for archiving past courses.")
    lti_key = models.CharField(max_length=100, null=True, blank=True, help_text="Key to be used by an LTI consumer when accessing this course.")
    lti_secret = models.CharField(max_length=100, null=True, blank=True, help_text="Secret to be used by an LTI consumer when accessing this course.")

    objects = models.Manager()
    valid_ones = ValidCoursesManager()

    class Meta:
        app_label = 'opensubmit'

    def __str__(self):
        if self.active:
            return self.title
        else:
            return self.title+' (inactive)'

    def directory_name(self):
        ''' The course name in a format that is suitable for a directory name.  '''
        return self.title.replace(" ", "_").replace("\\", "_").replace("/", "_").replace(",","").lower()

    def open_assignments(self):
        qs = Assignment.objects.filter(hard_deadline__gt=timezone.now()) | Assignment.objects.filter(hard_deadline__isnull=True)
        qs = qs.filter(publish_at__lt=timezone.now())
        qs = qs.filter(course=self)
        qs = qs.order_by('soft_deadline').order_by('hard_deadline').order_by('title')
        return qs

    def gradable_submissions(self):
        '''
            Queryset for the gradable submissions that are worth a look by tutors.
        '''
        qs = self._valid_submissions()
        qs = qs.filter(state__in=[Submission.GRADING_IN_PROGRESS, Submission.SUBMITTED_TESTED, Submission.TEST_FULL_FAILED, Submission.SUBMITTED])
        return qs

    def graded_submissions(self):
        '''
            Queryset for the graded submissions, which are worth closing.
        '''
        qs = self._valid_submissions().filter(state__in=[Submission.GRADED])
        return qs

    def grading_url(self):
        '''
            Determines the teacher backend link to the filtered list of gradable submissions for this course.
        '''
        grading_url="%s?coursefilter=%u&statefilter=tobegraded"%(
                            reverse('teacher:opensubmit_submission_changelist'),
                            self.pk
                        )
        return grading_url


    def authors(self):
        '''
            Queryset for all distinct authors this course had so far. Important for statistics.
            Note that this may be different from the list of people being registered for the course,
            f.e. when they submit something and the leave the course.
        '''
        qs = self._valid_submissions().values_list('authors',flat=True).distinct()
        return qs

    def _valid_submissions(self):
        qs = Submission.objects.filter(assignment__course=self).exclude(state=Submission.WITHDRAWN)
        return qs

