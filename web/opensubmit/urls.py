from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth.decorators import login_required

from opensubmit.admin import teacher_backend, admin_backend

from settings import MEDIA_ROOT, MEDIA_URL_RELATIVE

urlpatterns = patterns('',
    url(r'^$', 'opensubmit.views.index', name='index'),
    url(r'^logout/$', 'opensubmit.views.logout', name='logout'),
    url(r'^dashboard/$', 'opensubmit.views.dashboard', name='dashboard'),
    url(r'^details/(?P<subm_id>\d+)/$', 'opensubmit.views.details', name='details'),
    url(r'^assignments/(?P<ass_id>\d+)/new/$', 'opensubmit.views.new', name='new'),
    url(r'^withdraw/(?P<subm_id>\d+)/$', 'opensubmit.views.withdraw', name='withdraw'),
    url(r'^preview/(?P<subm_id>\d+)/$', 'opensubmit.views.preview', name='preview'),
    url(r'^update/(?P<subm_id>\d+)/$', 'opensubmit.views.update', name='update'),
    url(r'^course/(?P<course_id>\d+)/gradingtable/$', 'opensubmit.views.gradingtable', name='gradingtable'),
    url(r'^course/(?P<course_id>\d+)/archive/$', 'opensubmit.views.coursearchive', name='coursearchive'),
    url(r'^course/(?P<course_id>\d+)/mail2all/$', 'opensubmit.views.mail2all', name='mail2all'),
    url(r'^jobs/$', 'opensubmit.api.jobs', name='jobs'),
    url(r'^download/(?P<obj_id>\d+)/(?P<filetype>\w+)/secret=(?P<secret>\w+)$', 'opensubmit.api.download', name='download_secret'),
    url(r'^download/(?P<obj_id>\d+)/(?P<filetype>\w+)/$', 'opensubmit.api.download', name='download'),
    url(r'^machine/(?P<machine_id>\d+)/$', 'opensubmit.views.machine', name='machine'),
    url(r'^machines/$', 'opensubmit.api.machines', name='machines'),
    url(r'^settings/$', 'opensubmit.views.settings', name='settings'),
    url(r'^courses/$', 'opensubmit.views.courses', name='courses'),
    url(r'^mergeusers/$', 'opensubmit.views.mergeusers', name='mergeusers'),

    url(r'^grappelli/', include('grappelli.urls')), # grappelli URLS
    url('', include('social.apps.django_app.urls', namespace='social')),
    url(r'^teacher/', include(teacher_backend.urls)),
    url(r'^admin/', include(admin_backend.urls))
)

# only working when DEBUG==FALSE
# on production systems, both static and media files must be served directly by Apache
urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(MEDIA_URL_RELATIVE, document_root=MEDIA_ROOT)

# import urls
# def show_urls(urllist, depth=0):
#     for entry in urllist:
#         print "  " * depth, entry.regex.pattern
#         if hasattr(entry, 'url_patterns'):
#             show_urls(entry.url_patterns, depth + 1)
# show_urls(urls.urlpatterns)