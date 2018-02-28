from jet.dashboard import modules
from jet.dashboard.dashboard import Dashboard

from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from opensubmit import settings
from opensubmit.models import Submission, TestMachine


class TableDashboardModule(modules.DashboardModule):
    template = 'teacher_dash_table.html'

    def init_with_context(self, context):
        super().init_with_context(context)

class TeacherDashboard(Dashboard):

    class Media:
        css = {'all': ('css/teacher.css',)}

    def init_with_context(self, context):
        general = []
        if context.request.user.has_perm('opensubmit.change_course'):
            general.append(
                {'title': 'Manage courses',
                 'url': reverse('teacher:opensubmit_course_changelist'),
                 'external': False}
            )
        if context.request.user.has_perm('opensubmit.change_gradingscheme'):
            general.append(
                {'title': 'Manage grading schemes',
                 'url': reverse('teacher:opensubmit_gradingscheme_changelist'),
                 'external': False}
            )
        if context.request.user.has_perm('opensubmit.change_studyprogram'):
            general.append(
                {'title': 'Manage study programs',
                 'url': reverse('teacher:opensubmit_studyprogram_changelist'),
                 'external': False}
            )
        if context.request.user.has_perm('opensubmit.change_user'):
            general.append(
                {'title': 'Manage users',
                 'url': reverse('admin:auth_user_changelist'),
                 'external': False}
            )
        if context.request.user.has_perm('opensubmit.change_user'):
            general.append(
                {'title': 'Manage user groups',
                 'url': reverse('admin:auth_group_changelist'),
                 'external': False}
            )
        if context.request.user.has_perm('opensubmit.change_permission'):
            general.append(
                {'title': 'Manage permissions',
                 'url': reverse('admin:auth_permission_changelist'),
                 'external': False}
            )
        if context.request.user.has_perm('opensubmit.change_testmachine'):
            general.append(
                {'title': 'Manage test machines',
                 'url': reverse('teacher:opensubmit_testmachine_changelist'),
                 'external': False}
            )
        self.available_children = None
        self.children.append(modules.LinkList(
            title="Actions",
            column=0,
            children=general
        ))

        self.children.append(TableDashboardModule(
            title="Info",
            column=0,
            children=[['OpenSubmit release', settings.VERSION],
                      ['Administrator', '<a href="mailto:{0}">{1}</a>'.format(settings.ADMINS[0][1], settings.ADMINS[0][0])],
                      ['Registered users', str(User.objects.count())],
                      ['Submitted solutions', str(Submission.objects.count())],
                      ['Test machines', '{0} enabled, {1} disabled'.format(TestMachine.objects.filter(enabled=True).count(), TestMachine.objects.filter(enabled=False).count())]
                      ]
        ))

        # Put course action boxes in column
        try:
            courses = context.request.user.profile.tutor_courses().all()
        except Exception:
            courses = []

        column = 2
        for course in courses:
            # Prepare course-related links
            links = []
            links.append(['Manage submissions', course.grading_url(), False])
            ass_url = "%s?course__id__exact=%u" % (
                reverse('teacher:opensubmit_assignment_changelist'),
                course.pk
            )
            if context.request.user.has_perm('opensubmit.change_assignment'):
                links.append(['Manage assignments', ass_url, False])
            links.append(['Show grading table', reverse(
                'gradingtable', args=[course.pk]), False])
            links.append(['Create eMail for students', reverse(
                'mailcourse', args=[course.pk]), False])
            if context.request.user.has_perm('opensubmit.change_course'):
                links.append(['Edit course details', reverse(
                    'teacher:opensubmit_course_change', args=[course.pk]), False])
            links.append(['Download course archive', reverse(
                'coursearchive', args=[course.pk]), False])

            # Add course group box to dashboard
            self.children.append(modules.Group(
                title="Course '{0}'".format(course.title),
                column=column,
                children=[
                    modules.LinkList(title="Actions", children=(links)),
                    modules.DashboardModule(title="Info", pre_content='<table class="teacher_dashboard_info">' +
                                            '<tr><td>Course URL for students</td><td>%s/?course=%u</td></tr>' % (settings.MAIN_URL, course.pk) +
                                            '<tr><td>Course owner</td><td><a href="mailto:%s">%s</a></td></tr>' % (course.owner.email, course.owner.get_full_name()) +
                                            "<tr><td>Open assignments</td><td>%u</td></tr>" % course.open_assignments().count() +
                                            "<tr><td>Submissions to be graded</td><td>%u</td></tr>" % course.gradable_submissions().count() +
                                            "<tr><td>Grading finished, not notified</td><td>%u</td></tr>" % course.graded_submissions().count() +
                                            "<tr><td>Registered students</td><td>%u</td></tr>" % course.participants.count() +
                                            "<tr><td>Authoring students</td><td>%u</td></tr>" % course.authors().count() +
                                            "</table>"
                                            )
                ]
            ))
            column += 1
