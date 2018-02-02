# Submission admin interface

from django.contrib.admin import SimpleListFilter, ModelAdmin
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from django.http import HttpResponse
from django.utils.html import format_html
from opensubmit.models import Assignment, Submission, Grading
from django.utils import timesince

import io
import zipfile


def grading_file(submission):
    ''' Determines if the submission has a grading file,
        leads to nice little icon in the submission overview.
    '''
    if submission.grading_file.name:
        return True
    else:
        return False


grading_file.boolean = True            # show nice little icon


def test_results(submission):
    return "Foo"


class SubmissionStateFilter(SimpleListFilter):

    ''' This custom filter allows to filter the submissions according to their state.
        Additionally, only submissions the user is tutor for are shown.
    '''
    title = _('Submission Status')
    parameter_name = 'statefilter'

    def lookups(self, request, model_admin):
        return (
            ('notwithdrawn', _('All, except withdrawn')),
            ('valid', _('Tested')),
            ('tobegraded', _('Grading needed')),
            ('gradingunfinished', _('Grading not finished')),
            ('graded', _('Grading finished')),
            ('closed', _('Closed, student notified')),
        )

    def queryset(self, request, qs):
        qs = qs.filter(assignment__course__in=list(
            request.user.profile.tutor_courses()))
        if self.value() == 'notwithdrawn':
            return Submission.qs_notwithdrawn(qs)
        elif self.value() == 'valid':
            return Submission.qs_valid(qs)
        elif self.value() == 'tobegraded':
            return Submission.qs_tobegraded(qs)
        elif self.value() == 'gradingunfinished':
            return qs.filter(state__in=[Submission.GRADING_IN_PROGRESS])
        elif self.value() == 'graded':
            return qs.filter(state__in=[Submission.GRADED])
        elif self.value() == 'closed':
            return Submission.qs_notified(qs)
        else:
            return qs


class SubmissionAssignmentFilter(SimpleListFilter):

    ''' This custom filter allows to filter the submissions according to their
        assignment. Only submissions from courses were the user is tutor are
        considered.
    '''
    title = _('Assignment')
    parameter_name = 'assignmentfilter'

    def lookups(self, request, model_admin):
        tutor_assignments = Assignment.objects.filter(course__in=list(
            request.user.profile.tutor_courses())).order_by('title')
        return ((ass.pk, ass.title) for ass in tutor_assignments)

    def queryset(self, request, qs):
        if self.value():
            return qs.filter(assignment__exact=self.value())
        else:
            return qs.filter(assignment__course__in=list(request.user.profile.tutor_courses()))


class SubmissionCourseFilter(SimpleListFilter):

    ''' This custom filter allows to filter the submissions according to
        the course they belong to. Additionally, only submission that the
        user is a tutor for are returned in any of the filter settings.
    '''
    title = _('Course')
    parameter_name = 'coursefilter'

    def lookups(self, request, model_admin):
        return ((c.pk, c.title) for c in list(request.user.profile.tutor_courses()))

    def queryset(self, request, qs):
        if self.value():
            return qs.filter(assignment__course__exact=self.value())
        else:
            return qs.filter(assignment__course__in=list(request.user.profile.tutor_courses()))


class SubmissionAdmin(ModelAdmin):

    ''' This is our version of the admin view for a single submission.
    '''
    list_display = ['__str__', 'created', 'modified', 'author_list', 'course',
                    'assignment', 'state', 'grading_status_text', 'has_grading_notes']
    list_filter = (SubmissionStateFilter, SubmissionCourseFilter,
                   SubmissionAssignmentFilter)
    filter_horizontal = ('authors',)
    actions = ['downloadArchiveAction', 'setInitialStateAction', 'setFullPendingStateAction', 'setGradingNotFinishedStateAction',
               'setGradingFinishedStateAction', 'closeAndNotifyAction', 'sendMailAction', 'notifyAction', 'getPerformanceResultsAction']
    search_fields = ['=id', '=authors__email', '=authors__first_name',
                     '=authors__last_name', '=authors__username', '=notes']
    change_list_template = "admin/change_list_filter_sidebar.html"

    class Media:
        css = {'all': ('css/teacher.css',)}

    fieldsets = (
        ('General',
         {'fields': ('assignment', 'assignment_info', ('submitter', 'modified')), }),
        ('Authors',
         {'fields': ('authors',),
          'classes': ('grp-collapse grp-closed',)
          }),
        ('Student submission', {'fields': (('file_link', 'file_upload'), 'notes')}),
        ('Test results',
         {'fields': (('validationtest_result_student', 'validationtest_result_tutor'), 'fulltest_result'),
          }),
        ('Grading',
         {'fields': (('grading', 'grading_status'), 'grading_notes', 'grading_file',), }),
    )

    def assignment_info(self, instance):
        message = 'Course: %s<br/>' % instance.assignment.course
        message += 'Deadline: %s (%s ago)' % (instance.assignment.hard_deadline,
                                              timesince.timesince(instance.assignment.hard_deadline))
        if instance.can_modify(instance.submitter):
            message += '''<p style="color: red">Warning: Assignment is still open. Saving grading information will disable withdrawal and re-upload for the authors.</p>'''
        return mark_safe(message)
    assignment_info.short_description = "Details"

    def file_link(self, instance):
        '''
            Renders the link to the student upload file.
        '''
        sfile = instance.file_upload
        if not sfile:
            return mark_safe('No file submitted by student.')
        else:
            return mark_safe('<a href="%s">%s</a><br/>(<a href="%s" target="_new">Preview</a>)' % (sfile.get_absolute_url(), sfile.basename(), sfile.get_preview_url()))
    file_link.short_description = "Stored upload"

    def _render_test_result(self, result_obj, enabled, show_student_data):
        if not result_obj:
            if enabled:
                return mark_safe('Enabled, no results.')
            else:
                return mark_safe('Not enabled, no results.')
        else:
            if show_student_data:
                text = result_obj.result
            else:
                text = result_obj.result_tutor
            return format_html("{1}<div style='font-size:80%'><br/>(Generated by {0})</div>", result_obj.machine, text)

    def validationtest_result_student(self, instance):
        result_obj = instance.get_validation_result()
        return self._render_test_result(result_obj, instance.assignment.attachment_test_validity, True)
    validationtest_result_student.short_description = "Validation test"
    validationtest_result_student.allow_tags = True

    def validationtest_result_tutor(self, instance):
        result_obj = instance.get_validation_result()
        return self._render_test_result(result_obj, instance.assignment.attachment_test_validity, False)
    validationtest_result_tutor.short_description = "Validation test (tutor only)"
    validationtest_result_tutor.allow_tags = True

    def fulltest_result(self, instance):
        result_obj = instance.get_fulltest_result()
        return self._render_test_result(result_obj, instance.assignment.attachment_test_full, False)
    fulltest_result.short_description = "Full test (tutor only)"
    fulltest_result.allow_tags = True

    def grading_status(self, instance):
        message = '''<input type="radio" name="newstate" value="unfinished">&nbsp;Grading not finished</input>
            <input type="radio" name="newstate" value="finished">&nbsp;Grading finished</input>
        '''
        return mark_safe(message)
    grading_status.short_description = "Status"

    def get_queryset(self, request):
        ''' Restrict the listed submission for the current user.'''
        qs = super(SubmissionAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        else:
            return qs.filter(Q(assignment__course__tutors__pk=request.user.pk) | Q(assignment__course__owner=request.user)).distinct()

    def get_readonly_fields(self, request, obj=None):
        ''' Make some of the form fields read-only, but only if the view used to
            modify an existing submission. Overriding the ModelAdmin getter
            is the documented way to do that.
        '''
        # Pseudo-fields generated by functions always must show up in the readonly list
        pseudo_fields = ('file_link', 'validationtest_result_student', 'validationtest_result_tutor', 'fulltest_result',
                         'grading_status', 'assignment_info', 'modified')
        if obj:
            return ('assignment', 'submitter', 'notes') + pseudo_fields
        else:
            # New manual submission
            return pseudo_fields

    def formfield_for_dbfield(self, db_field, **kwargs):
        ''' Offer grading choices from the assignment definition as potential form
            field values for 'grading'.
            When no object is given in the form, the this is a new manual submission
        '''
        if db_field.name == "grading":
            submurl = kwargs['request'].path
            try:
                # Does not work on new submission action by admin or with a change of URLs. The former is expectable.
                submid = [int(s) for s in submurl.split('/') if s.isdigit()][0]
                kwargs["queryset"] = Submission.objects.get(
                    pk=submid).assignment.gradingScheme.gradings
            except:
                kwargs["queryset"] = Grading.objects.none()
        return super(SubmissionAdmin, self).formfield_for_dbfield(db_field, **kwargs)

    def save_model(self, request, obj, form, change):
        ''' Our custom addition to the view
            adds an easy radio button choice for the new state. This is meant to be for tutors.
            We need to peel this choice from the form data and set the state accordingly.
            The radio buttons have no default, so that we can keep the existing state
            if the user makes no explicit choice.
            Everything else can be managed as prepared by the framework.
        '''
        if 'newstate' in request.POST:
            if request.POST['newstate'] == 'finished':
                obj.state = Submission.GRADED
            elif request.POST['newstate'] == 'unfinished':
                obj.state = Submission.GRADING_IN_PROGRESS
        obj.save()

    def setInitialStateAction(self, request, queryset):
        for subm in queryset:
            subm.state = subm.get_initial_state()
            subm.save()
    setInitialStateAction.short_description = "Re-run validation test for selection submissions (student visible)"

    def setGradingNotFinishedStateAction(self, request, queryset):
        '''
            Set all marked submissions to "grading not finished".
            This is intended to support grading corrections on a larger scale.
        '''
        for subm in queryset:
            subm.state = Submission.GRADING_IN_PROGRESS
            subm.save()
    setGradingNotFinishedStateAction.short_description = "Mark selected submissions as 'Grading not finished'"

    def setGradingFinishedStateAction(self, request, queryset):
        '''
            Set all marked submissions to "grading finished".
            This is intended to support grading corrections on a larger scale.
        '''
        for subm in queryset:
            subm.state = Submission.GRADED
            subm.save()
    setGradingFinishedStateAction.short_description = "Mark selected submissions as 'Grading finished'"

    def setFullPendingStateAction(self, request, queryset):
        # do not restart tests for withdrawn solutions
        queryset = queryset.exclude(state=Submission.WITHDRAWN)
        # do not restart tests for queued things
        queryset = queryset.exclude(state=Submission.TEST_VALIDITY_PENDING)
        queryset = queryset.exclude(state=Submission.TEST_FULL_PENDING)
        numchanged = 0
        for subm in queryset:
            if subm.assignment.has_full_test():
                if subm.state == Submission.CLOSED:
                    subm.state = Submission.CLOSED_TEST_FULL_PENDING
                else:
                    subm.state = Submission.TEST_FULL_PENDING
                subm.save()
                numchanged += 1
        if numchanged == 0:
            self.message_user(
                request, "Nothing changed, no testable submission found.")
        else:
            self.message_user(
                request, "Changed status of %u submissions." % numchanged)
    setFullPendingStateAction.short_description = "Re-run full test for selected submissions (student invisible)"

    def closeAndNotifyAction(self, request, queryset):
        ''' Close all submissions were the tutor sayed that the grading is finished,
            and inform the student. CLosing only graded submissions is a safeguard,
            since backend users tend to checkbox-mark all submissions without thinking.
        '''
        mails = []
        qs = queryset.filter(Q(state=Submission.GRADED))
        for subm in qs:
            subm.inform_student(Submission.CLOSED)
            mails.append(str(subm.pk))
        # works in bulk because inform_student never fails
        qs.update(state=Submission.CLOSED)
        if len(mails) == 0:
            self.message_user(request, "Nothing closed, no mails sent.")
        else:
            self.message_user(
                request, "Mail sent for submissions: " + ",".join(mails))
    closeAndNotifyAction.short_description = "Close + send student notification for selected submissions"

    def sendMailAction(self, request, queryset):
        receiver_list = []
        for submission in queryset:
            for author in submission.authors.all():
                if author.pk not in receiver_list:
                    receiver_list.append(author.pk)
        return redirect('mailstudents', user_list=','.join([str(pk) for pk in receiver_list]))
    sendMailAction.short_description = "Send eMail to authors of selected submissions"

    def downloadArchiveAction(self, request, queryset):
        '''
        Download selected submissions as archive, for targeted correction.
        '''
        output = io.BytesIO()
        z = zipfile.ZipFile(output, 'w')

        for sub in queryset:
            sub.add_to_zipfile(z)

        z.close()
        # go back to start in ZIP file so that Django can deliver it
        output.seek(0)
        response = HttpResponse(
            output, content_type="application/x-zip-compressed")
        response['Content-Disposition'] = 'attachment; filename=submissions.zip'
        return response
    downloadArchiveAction.short_description = "Download selected submissions as ZIP archive"

    # ToDo: Must be refactored to consider new performance data storage model
    # def getPerformanceResultsAction(self, request, queryset):
    #     qs = queryset.exclude(state=Submission.WITHDRAWN)  # avoid accidental addition of withdrawn solutions
    #     response = HttpResponse(content_type="text/csv")
    #     response.write("Submission ID;Course;Assignment;Authors;Performance Data\n")
    #     for subm in qs:
    #         if subm.file_upload and subm.file_upload.perf_data is not None:
    #             auth = ", ".join([author.get_full_name() for author in subm.authors.all()])
    #             response.write("%u;%s;%s;%s;" % (subm.pk, course(subm), subm.assignment, auth))
    #             response.write(subm.file_upload.perf_data)
    #             response.write("\n")
    #     return response
    # getPerformanceResultsAction.short_description = "Download performance data as CSV"
