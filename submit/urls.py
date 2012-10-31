from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'submit.views.index', name='index'),
    url(r'^login/$', 'submit.views.login', name='login'),
    url(r'^dashboard/$', 'submit.views.dashboard', name='dashboard'),
    url(r'^new/$', 'submit.views.new', name='new'),
    url(r'^delete/(?P<subm_id>\d+)/$', 'submit.views.delete', name='delete'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
