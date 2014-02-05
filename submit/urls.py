from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth.decorators import login_required
from django.contrib import admin
import settings
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'submit.views.index', name='index'),
    url(r'^login/$', 'submit.views.login', name='login'),
    url(r'^logout/$', 'submit.views.logout', name='logout'),
    url(r'^dashboard/$', 'submit.views.dashboard', name='dashboard'),
    url(r'^details/(?P<subm_id>\d+)/$', 'submit.views.details', name='details'),
    url(r'^assignments/(?P<ass_id>\d+)/new/$', 'submit.views.new', name='new'),
    url(r'^assignments/(?P<ass_id>\d+)/manual/$', 'submit.views.manual_submit', name='manual_submit'),
    url(r'^withdraw/(?P<subm_id>\d+)/$', 'submit.views.withdraw', name='withdraw'),
    url(r'^update/(?P<subm_id>\d+)/$', 'submit.views.update', name='update'),
    url(r'^course/(?P<course_id>\d+)/gradingtable$', 'submit.views.gradingtable', name='gradingtable'),
    url(r'^course/(?P<course_id>\d+)/archive$', 'submit.views.coursearchive', name='coursearchive'),
    url(r'^jobs/secret=(?P<secret>\w+)$', 'submit.api.jobs', name='jobs'),
    url(r'^download/(?P<obj_id>\d+)/(?P<filetype>\w+)/secret=(?P<secret>\w+)$', 'submit.api.download', name='download_secret'),
    url(r'^download/(?P<obj_id>\d+)/(?P<filetype>\w+)/$', 'submit.api.download', name='download'),
    url(r'^machine/(?P<machine_id>\d+)/$', 'submit.views.machine', name='machine'),
    url(r'^machines/secret=(?P<secret>\w+)$', 'submit.api.machines', name='machines'),
    url(r'^settings/$', 'submit.views.settings', name='settings'),
    url(r'^courses/$', 'submit.views.courses', name='courses'),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)

# disables itself when DEBUG==FALSE
urlpatterns += staticfiles_urlpatterns()
