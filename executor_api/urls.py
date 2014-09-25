from django.conf.urls import patterns, include, url

from executor_api import views #Job, Jobs, JobAssigner


urlpatterns = patterns('',
    url(r'^$', views.IndexView.as_view(), name='index'),

    url(r'^job/assign/', views.JobAssignmentView.as_view(), name='job_assign'),
    url(r'^job/(?P<job_id>[0-9]+)/result/', views.JobResultView.as_view(), name='job_result'),
    url(r'^job/(?P<job_id>[0-9]+)/submission/download/', views.JobSubmissionDownloadView.as_view(), name='job_submission_download'),
    url(r'^job/(?P<job_id>[0-9]+)/', views.JobView.as_view(), name='job'),
    url(r'^jobs/', views.JobsView.as_view(), name='jobs'),

    url(r'^assignment/(?P<ass_id>[0-9]+)/test/download', views.AssignmentTestDownloadView.as_view(), name='assignment_test_download'),
    url(r'^assignment/(?P<ass_id>[0-9]+)/', views.AssignmentTestView.as_view(), name='assignment_test'),
    url(r'^assignments/', views.AssignmentTestsView.as_view(), name='assignment_tests'),

    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),
)
