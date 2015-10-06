from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from grappelli.dashboard import modules, Dashboard
from grappelli.dashboard.utils import get_admin_site_name

from opensubmit.models import tutor_courses, TestMachine, Submission

class Statistics(modules.DashboardModule):
    title = _('Statistics')
    template = 'grappelli/dashboard/module.html'

    def __init__(self,  title='', **kwargs):
        super(Statistics, self).__init__(title, **kwargs)

    def init_with_context(self, context):
        if self._initialized:
            return
        from django.db.models import Q

        request = context['request']

        self.children = "tbd"
        self._initialized = True

class TeacherDashboard(Dashboard):
    def init_with_context(self, context):
        site_name = get_admin_site_name(context)

        # append an app list module for "Applications"
        self.children.append(modules.AppList(
            _(''),
            collapsible=False,
            column=1,
            css_classes=('collapse closed',),
            exclude=('django.contrib.*',),
        ))

        courses = tutor_courses(context.request.user)

        from opensubmit.admin.submission import SubmissionCourseFilter, SubmissionStateFilter
        tobegraded = SubmissionStateFilter.qs_tobegraded(Submission.objects.all()).count()

        rendered_list = [{'title': c.title,
                          'url': '/teacher/opensubmit/submission/?statefilter=tobegraded&coursefilter='+str(c.pk),
                          'external': False} for c in courses]

        self.children.append(modules.LinkList(
            _('Submissions to be graded (%u)'%tobegraded),
            column=1,
            collapsible=False,
            children=rendered_list
        ))
        # append a recent actions module
        self.children.append(modules.RecentActions(
            _('Recent Actions'),
            limit=5,
            collapsible=False,
            column=3,
        ))

        #self.children.append(Statistics(column=2, title='Statistics'))

class AdminDashboard(Dashboard):
    def init_with_context(self, context):
        site_name = get_admin_site_name(context)

        self.children.append(modules.AppList(
                    _(''),
                    column=1,
                    collapsible=False,
                    models=('django.contrib.*',)
        ))

        self.children.append(modules.AppList(
                    _(''),
                    column=1,
                    css_classes=('collapse closed',),
                    exclude=('django.contrib.*',)
        ))


        # append a recent actions module
        self.children.append(modules.RecentActions(
            _('Recent Actions'),
            limit=5,
            collapsible=False,
            column=3,
        ))

