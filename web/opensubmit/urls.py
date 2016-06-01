from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect

from opensubmit import views, admin, api

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^dashboard/$', views.dashboard, name='dashboard'),
    url(r'^details/(?P<subm_id>\d+)/$', views.details, name='details'),
    url(r'^assignments/(?P<ass_id>\d+)/new/$', views.new, name='new'),
    url(r'^assignments/(?P<ass_id>\d+)/perftable/$', views.perftable, name='perftable'),
    url(r'^assignments/(?P<ass_id>\d+)/duplicates/$', views.duplicates, name='duplicates'),
    url(r'^assignments/(?P<ass_id>\d+)/archive/$', views.assarchive, name='assarchive'),
    url(r'^withdraw/(?P<subm_id>\d+)/$', views.withdraw, name='withdraw'),
    url(r'^preview/(?P<subm_id>\d+)/$', views.preview, name='preview'),
    url(r'^update/(?P<subm_id>\d+)/$', views.update, name='update'),
    url(r'^course/(?P<course_id>\d+)/gradingtable/$', views.gradingtable, name='gradingtable'),
    url(r'^course/(?P<course_id>\d+)/archive/$', views.coursearchive, name='coursearchive'),
    url(r'^course/(?P<course_id>\d+)/mail2all/$', views.mail2all, name='mail2all'),
    url(r'^jobs/$', api.jobs, name='jobs'),
    url(r'^download/(?P<obj_id>\d+)/(?P<filetype>\w+)/secret=(?P<secret>\w+)$', api.download, name='download_secret'),
    url(r'^download/(?P<obj_id>\d+)/(?P<filetype>\w+)/$', api.download, name='download'),
    url(r'^machine/(?P<machine_id>\d+)/$', views.machine, name='machine'),
    url(r'^machines/$', api.machines, name='machines'),
    url(r'^settings/$', views.settings, name='settings'),
    url(r'^courses/$', views.courses, name='courses'),
    url(r'^mergeusers/$', views.mergeusers, name='mergeusers'),

    url('', include('social.apps.django_app.urls', namespace='social')),
    url(r'^lti/$', views.lti, name='lti'),
    url(r'^teacher/', include(admin.teacher_backend.urls)),
    url(r'^admin/', include(admin.admin_backend.urls)),
    url(r'^grappelli/', include('grappelli.urls')), # grappelli URLS
]

# only working when DEBUG==FALSE
# on production systems, static files are served directly by Apache
urlpatterns += staticfiles_urlpatterns()

import urls
def show_urls(urllist, depth=0):
    for entry in urllist:
        print "  " * depth, entry.regex.pattern
        if hasattr(entry, 'url_patterns'):
            show_urls(entry.url_patterns, depth + 1)
#show_urls(urls.urlpatterns)