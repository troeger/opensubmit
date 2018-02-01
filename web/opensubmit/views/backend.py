'''
OpenSubmit backend views that are not realized with Django admin.
'''

from django.views.generic import TemplateView, DetailView
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import redirect

from opensubmit.models import Submission, Assignment, Course
from opensubmit.models.userprofile import move_user_data
from opensubmit.models.views.helpers import StaffRequiredMixin, ZipDownloadDetailView


class AssignmentArchiveView(StaffRequiredMixin, ZipDownloadDetailView):
    model = Assignment

    def fill_zip_file(self, z):
        assignment = self.object
        assignment.add_to_zipfile(z)
        subs = Submission.valid_ones.filter(assignment=assignment).order_by('submitter')
        for sub in subs:
            sub.add_to_zipfile(z)
        return assignment.directory_name()


class CourseArchiveView(StaffRequiredMixin, ZipDownloadDetailView):
    model = Course

    def fill_zip_file(self, z):
        course = self.object
        assignments = course.assignments.order_by('title')
        for ass in assignments:
            ass.add_to_zipfile(z)
            subs = ass.submissions.all().order_by('submitter')
            for sub in subs:
                sub.add_to_zipfile(z)
        return course.directory_name()


class PreviewView(StaffRequiredMixin, DetailView):
    template_name = 'file_preview.html'
    model = Submission


class DuplicatesView(StaffRequiredMixin, DetailView):
    template_name = 'duplicates.html'
    model = Assignment


class GradingTableView(StaffRequiredMixin, DetailView):
    template_name = 'gradingtable.html'
    model = Course

    def get_context_data(self, **kwargs):
        course = self.object
        assignments = course.assignments.all().order_by('title')

        # find all gradings per author and assignment
        author_submissions = {}
        for assignment in assignments:
            for submission in assignment.submissions.all().filter(state=Submission.CLOSED):
                for author in submission.authors.all():
                    # author_submissions is a dict mapping authors to another dict
                    # This second dict maps assignments to submissions (for this author)
                    # A tuple as dict key does not help here, since we want to iterate over the assignments later
                    if author not in list(author_submissions.keys()):
                        author_submissions[author] = {assignment.pk: submission}
                    else:
                        author_submissions[author][assignment.pk] = submission
        resulttable = []
        for author, ass2sub in list(author_submissions.items()):
            columns = []
            numpassed = 0
            numgraded = 0
            pointsum = 0
            columns.append(author.last_name if author.last_name else '')
            columns.append(author.first_name if author.first_name else '')
            columns.append(
                author.profile.student_id if author.profile.student_id else '')
            columns.append(
                author.profile.study_program if author.profile.study_program else '')
            # Process all assignments in the table order, once per author (loop above)
            for assignment in assignments:
                if assignment.pk in ass2sub:
                    # Ok, we have a submission for this author in this assignment
                    submission = ass2sub[assignment.pk]
                    if assignment.is_graded():
                        # is graded, make part of statistics
                        numgraded += 1
                        if submission.grading_means_passed():
                            numpassed += 1
                            try:
                                pointsum += int(str(submission.grading))
                            except Exception:
                                pass
                    # considers both graded and ungraded assignments
                    columns.append(submission.grading_value_text())
                else:
                    # No submission for this author in this assignment
                    # This may or may not be bad, so we keep it neutral here
                    columns.append('-')
            columns.append("%s / %s" % (numpassed, numgraded))
            columns.append("%u" % pointsum)
            resulttable.append(columns)

        context = super().get_context_data(**kwargs)
        context['assignments'] = assignments
        context['resulttable'] = sorted(resulttable)
        return context


class MergeUsersView(StaffRequiredMixin, TemplateView):
    template_name = 'mergeusers.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['primary'] = get_object_or_404(User, pk=kwargs['primary_pk'])
        context['secondary'] = get_object_or_404(User, pk=kwargs['secondary_pk'])
        return context

    def post(self, request, *args, **kwargs):
        primary = get_object_or_404(User, pk=kwargs['primary_pk'])
        secondary = get_object_or_404(User, pk=kwargs['secondary_pk'])
        try:
            move_user_data(primary, secondary)
            messages.info(request, 'Submissions moved to user %u.' %
                          (primary.pk))
        except Exception:
            messages.error(
                request, 'Error during data migration, nothing changed.')
            return redirect('admin:index')
        messages.info(request, 'User %u updated, user %u deleted.' % (primary.pk, secondary.pk))
        secondary.delete()
        return redirect('admin:index')
