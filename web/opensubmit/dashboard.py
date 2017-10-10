from django.utils.translation import ugettext_lazy as _
from grappelli.dashboard import modules, Dashboard
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from opensubmit import settings
from opensubmit.models import Submission, TestMachine

import settings

class TeacherDashboard(Dashboard):

    class Media:
        css = {'all': ('css/teacher.css',)}

    def init_with_context(self, context):
        general=[]
        if context.request.user.has_perm('opensubmit.change_course'):
            general.append(['Show all courses', reverse('teacher:opensubmit_course_changelist'), False])
        if context.request.user.has_perm('opensubmit.change_submissionfile'):
            general.append(['Show all submission files',reverse('teacher:opensubmit_submissionfile_changelist'), False])
        if context.request.user.has_perm('opensubmit.change_gradingscheme'):
            general.append(['Show all grading schemes ',reverse('teacher:opensubmit_gradingscheme_changelist'), False])
        if context.request.user.has_perm('opensubmit.add_course'):
            general.append(['Create new course',reverse('teacher:opensubmit_course_add'), False])
        if context.request.user.has_perm('opensubmit.add_gradingscheme'):
            general.append(['Create new grading scheme',reverse('teacher:opensubmit_gradingscheme_add'), False])
        if len(general)>0:
            self.children.append(modules.Group(
                title="System",
                column=1,
                children=[
                    modules.LinkList(title="Actions",children=(general)),
                    modules.DashboardModule(title="Info",pre_content=
                        '<table style="border:0">'+
                        '<tr><td>OpenSubmit release</td><td><a href="https://github.com/troeger/opensubmit/releases/tag/{0}">{0}</a></td></tr>'.format(settings.VERSION) +
                        '<tr><td>Administrator</td><td><a href="mailto:%s">%s</a></td></tr>' % (settings.ADMINS[0][1], settings.ADMINS[0][0]) +
                        '<tr><td>Registered users</td><td>%u</td></tr>' % (User.objects.count()) +
                        '<tr><td>Submitted solutions</td><td>%u</td></tr>' % (Submission.objects.count()) +
                        '<tr><td>Test machines</td><td>%u</td></tr>' % (TestMachine.objects.count()) +
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
            links.append(['Show submissions',course.grading_url(), False])
            ass_url="%s?course__id__exact=%u"%(
                                reverse('teacher:opensubmit_assignment_changelist'),
                                course.pk
                            )
            if context.request.user.has_perm('opensubmit.change_assignment'):
                links.append(['Show assignments',ass_url, False])
            links.append(['Show grading table',reverse('gradingtable', args=[course.pk]), False])
            if context.request.user.has_perm('opensubmit.add_assignment'):
                links.append(['Create new assignment','opensubmit/assignment/add/', False])
            links.append(['Create eMail for students',reverse('mail2all', args=[course.pk]), False])
            if context.request.user.has_perm('opensubmit.change_course'):
                links.append(['Edit course details',reverse('teacher:opensubmit_course_change', args=[course.pk]), False])
            links.append(['Download course archive',reverse('coursearchive', args=[course.pk]), False])

            # Add course group box to dashboard
            self.children.append(modules.Group(
                title=u"Course '{0}'".format(course.title),
                column=column,
                children=[
                    modules.LinkList(title="Actions",children=(links)),
                    modules.DashboardModule(title="Info",pre_content=
                        '<table>'+
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


class AdminDashboard(Dashboard):

    class Media:
        css = {'all': ('css/admin.css',)}

    def init_with_context(self, context):
        # Put database models in  column
        self.children.append(modules.ModelList(
            title='Security Management',
            column=2,
        ))




