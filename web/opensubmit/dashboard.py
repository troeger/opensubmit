from django.utils.translation import ugettext_lazy as _
from grappelli.dashboard import modules, Dashboard
from django.core.urlresolvers import reverse

from opensubmit import settings
from opensubmit.models import TestMachine, Submission

class TeacherDashboard(Dashboard):

    class Media:
        css = {'all': ('css/admin.css',)}

    def init_with_context(self, context):
        # Put database models in  column
        self.children.append(modules.ModelList(
            title='Database Management',
            column=2,
            exclude=('django.contrib.*','opensubmit.models.grading.*'),
        ))

        # Put course action boxes in column
        try:
            courses = context.request.user.profile.tutor_courses().all()
        except:
            courses = []

        for course in courses:
            # Prepare course-related links
            links=[]
            links.append(['Check all submissions',course.grading_url(), False])
            ass_url="%s?course__id__exact=%u"%(
                                reverse('teacher:opensubmit_assignment_changelist'),
                                course.pk
                            )
            links.append(['Check assignments',ass_url, False])
            links.append(['Show current grading table',reverse('gradingtable', args=[course.pk]), False])
            links.append(['eMail to students',reverse('mail2all', args=[course.pk]), False])
            links.append(['Edit course',reverse('teacher:opensubmit_course_change', args=[course.pk]), False])
            links.append(['Download course archive',reverse('coursearchive', args=[course.pk]), False])

            # Add course group box to dashboard
            self.children.append(modules.Group(
                title=course.title,
                column=1,
                children=[
                    modules.LinkList(title="Actions",children=(links)),
                    modules.DashboardModule(title="Info",pre_content=
                        'Course URL for students: %s/?course=%u<br/>' % (settings.MAIN_URL, course.pk) +
                        "Open assignments: %u<br/>" % course.open_assignments().count() +
                        "Submissions to be graded: %u<br/>" % course.gradable_submissions().count() +
                        "Grading finished, not notified: %u<br/>" % course.graded_submissions().count() +
                        "Registered students: %u<br/>" % course.participants.count() +
                        "Authoring students: %u<br/>" % course.authors().count()
                    )
                ]
            ))

        # Put recent actions in third column
        self.children.append(modules.RecentActions(
            title='Recent teacher activities',
            column=3,
        ))


class AdminDashboard(Dashboard):

    class Media:
        css = {'all': ('css/admin.css',)}

    def init_with_context(self, context):
        # Put database models in  column
        self.children.append(modules.ModelList(
            title='Database Management',
            column=2,
        ))




