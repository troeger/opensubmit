from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from .assignment import Assignment
from .submission import Submission

class Course(models.Model):
    title = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    owner = models.ForeignKey(User, related_name='courses', help_text="Only this user can change the course details and create new assignments.")
    tutors = models.ManyToManyField(User, blank=True, related_name='courses_tutoring', help_text="These users can edit / grade submissions for the course.")
    homepage = models.URLField(max_length=200, verbose_name="Course description link")
    active = models.BooleanField(default=True, help_text="Only assignments and submissions of active courses are shown to students and tutors. Use this flag for archiving past courses.")
    max_authors = models.PositiveSmallIntegerField(default=1, help_text="Maximum number of authors (= group size) for assignments in this course.")

    class Meta:
        app_label = 'opensubmit'

    def __unicode__(self):
        return unicode(self.title)

    def open_assignments(self):
        qs = Assignment.objects.filter(hard_deadline__gt=timezone.now())
        qs = qs.filter(publish_at__lt=timezone.now())
        qs = qs.filter(course=self)
        qs = qs.order_by('soft_deadline').order_by('hard_deadline').order_by('title')
        return qs

    def gradable_submissions(self):
        qs = self.valid_submissions()
        qs = qs.filter(state__in=[Submission.GRADING_IN_PROGRESS, Submission.SUBMITTED_TESTED, Submission.TEST_FULL_FAILED, Submission.SUBMITTED])
        return qs

    def graded_submissions(self):
        qs = self.valid_submissions().filter(state__in=[Submission.GRADED])
        return qs

    def authors(self):
        qs = self.valid_submissions().values_list('authors',flat=True).distinct()
        return qs

    def valid_submissions(self):
        qs = Submission.objects.filter(assignment__course=self).exclude(state=Submission.WITHDRAWN)
        return qs
