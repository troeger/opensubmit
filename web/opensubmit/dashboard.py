from grappelli.dashboard import modules, Dashboard
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from opensubmit import settings
from opensubmit.models import Submission, TestMachine


class TeacherDashboard(Dashboard):

    class Media:
        css = {'all': ('css/teacher.css',)}

    def init_with_context(self, context):
        general = []
        if context.request.user.has_perm('opensubmit.change_course'):
            general.append(['Manage courses', reverse('teacher:opensubmit_course_changelist'), False])
        if context.request.user.has_perm('opensubmit.change_gradingscheme'):
            general.append(['Manage grading schemes', reverse('teacher:opensubmit_gradingscheme_changelist'), False])
        if context.request.user.has_perm('opensubmit.change_studyprogram'):
            general.append(['Manage study programs', reverse('teacher:opensubmit_studyprogram_changelist'), False])
        if context.request.user.has_perm('opensubmit.change_user'):
            general.append(['Manage users', reverse('admin:auth_user_changelist'), False])
        if context.request.user.has_perm('opensubmit.change_user'):
            general.append(['Manage user groups', reverse('admin:auth_group_changelist'), False])
        if context.request.user.has_perm('opensubmit.change_permission'):
            general.append(['Manage permissions', reverse('admin:auth_permission_changelist'), False])
        if context.request.user.has_perm('opensubmit.change_testmachine'):
            general.append(['Manage test machines', reverse('teacher:opensubmit_testmachine_changelist'), False])
        self.children.append(modules.Group(
            title="System",
            column=1,
            children=[
                modules.LinkList(title="Actions",children=(general)),
                modules.DashboardModule(title="Info",pre_content=
                    '<table class="teacher_dashboard_info">'+
                    '<tr><td>OpenSubmit release</td><td><a href="https://github.com/troeger/opensubmit/releases/tag/v{0}">v{0}</a></td></tr>'.format(settings.VERSION) +
                    '<tr><td>Administrator</td><td><a href="mailto:%s">%s</a></td></tr>' % (settings.ADMINS[0][1], settings.ADMINS[0][0]) +
                    '<tr><td>Registered users</td><td>%u</td></tr>' % (User.objects.count()) +
                    '<tr><td>Submitted solutions</td><td>%u</td></tr>' % (Submission.objects.count()) +
                    '<tr><td>Test machines</td><td>%u enabled, %u disabled</td></tr>' % (TestMachine.objects.filter(enabled=True).count(), TestMachine.objects.filter(enabled=False).count()) +
                    "</table>"
                )
            ]
        ))


        # Put course action boxes in column
        try:
            courses = context.request.user.profile.tutor_courses().all()
        except:
            courses = []

        column=2
        for course in courses:
            # Prepare course-related links
            links=[]
            links.append(['Manage submissions',course.grading_url(), False])
            ass_url="%s?course__id__exact=%u"%(
                                reverse('teacher:opensubmit_assignment_changelist'),
                                course.pk
                            )
            if context.request.user.has_perm('opensubmit.change_assignment'):
                links.append(['Manage assignments',ass_url, False])
            links.append(['Show grading table',reverse('gradingtable', args=[course.pk]), False])
            links.append(['Create eMail for students',reverse('mailcourse', args=[course.pk]), False])
            if context.request.user.has_perm('opensubmit.change_course'):
                links.append(['Edit course details',reverse('teacher:opensubmit_course_change', args=[course.pk]), False])
            links.append(['Download course archive',reverse('coursearchive', args=[course.pk]), False])

            # Add course group box to dashboard
            self.children.append(modules.Group(
                title="Course '{0}'".format(course.title),
                column=column,
                children=[
                    modules.LinkList(title="Actions",children=(links)),
                    modules.DashboardModule(title="Info",pre_content=
                        '<table class="teacher_dashboard_info">'+
                        '<tr><td>Course URL for students</td><td>%s/?course=%u</td></tr>' % (settings.MAIN_URL, course.pk) +
                        '<tr><td>Course owner</td><td><a href="mailto:%s">%s</a></td></tr>' % (course.owner.email,course.owner.get_full_name()) +
                        "<tr><td>Open assignments</td><td>%u</td></tr>" % course.open_assignments().count() +
                        "<tr><td>Submissions to be graded</td><td>%u</td></tr>" % course.gradable_submissions().count() +
                        "<tr><td>Grading finished, not notified</td><td>%u</td></tr>" % course.graded_submissions().count() +
                        "<tr><td>Registered students</td><td>%u</td></tr>" % course.participants.count() +
                        "<tr><td>Authoring students</td><td>%u</td></tr>" % course.authors().count() +
                        "</table>"
                    )
                ]
            ))
            column+=1

