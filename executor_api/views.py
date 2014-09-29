import mimetypes

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db import transaction, IntegrityError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from rest_framework.exceptions import ParseError
from rest_framework.response import Response

from executor_api.helpers import require_ssl
from executor_api.helpers import ExecutorAPIView, ExecutorJobAPIView, ExecutorAssignmentAPIView
from executor_api.models import *


API_VERSION = 1
API_VERSION_COMPATIBLE = [API_VERSION, ]


# Create your views here.
@require_ssl
def index(request):
    return HttpResponse("Hello!")


class IndexView(ExecutorAPIView):
    def get(self, request):
        machine = self.discover_machine(request, require=False)

        response_obj = {
            'machine': machine.pk if machine else None,
            'message': "Hello!",
            'version': API_VERSION,
            'compatible': API_VERSION_COMPATIBLE,
        }
        return Response(response_obj)


class JobsView(ExecutorAPIView):
    def get(self, request):
        machine = self.discover_machine(request)
        jobs_not_completed = machine.jobs_not_completed()
        jobs_not_completed_obj = [job.pk for job in jobs_not_completed]
        response_obj = {
            'num_jobs_available': machine.jobs_available().count(),
            'jobs_not_completed': jobs_not_completed_obj,
        }
        return Response(response_obj)


class JobView(ExecutorJobAPIView):
    def get(self, request, job_id):
        job = get_object_or_404(TestJob, pk=job_id)
        machine = self.discover_machine(request)
        self.ensure_job_access(machine, job)

        submission_download = None
        if job.submission.file_upload:
            submission_download = reverse('api:job_submission_download', kwargs={'job_id': job.pk})

        assignment_download = reverse('api:assignment_test', kwargs={'ass_id': job.assignment_test.pk})

        response_obj = {
            'id': job.pk,
            'assignment': job.assignment_test.pk,
            'assignment_download': assignment_download,
            'test': job.test.pk,
            'notes': job.submission.notes,
            'submission_download': submission_download,
        }
        return Response(response_obj)


class JobSubmissionDownloadView(ExecutorJobAPIView):
    def get(self, request, job_id):
        job = get_object_or_404(TestJob, pk=job_id)
        machine = self.discover_machine(request)
        self.ensure_job_access(machine, job)

        submission = job.submission
        file = submission.file_upload
        file_obj = file.attachment
        file_name = file.basename()
        mimetype, charset = mimetypes.guess_type(file_name, strict=False)
        if mimetype is None:
            mimetype = 'application/octet-stream'

        r = HttpResponse(file_obj, content_type=mimetype)
        r['Content-Disposition'] = 'attachment; filename="{}"'.format(file_name)
        r['Content-Length'] = str(file_obj.size)
        return r


class JobResultView(ExecutorJobAPIView):
    def error(self, request, data, machine, job):
        requirements = [
            ('detail', lambda s: isinstance(s, (str, unicode, )) and len(s) > 0),
        ]
        data = self.check_requirements(requirements, data)
        error = TestJobError(
            machine=machine,
            job=job,
            message=data['detail'],
        )
        error.save()
        job.machine = None
        job.save()
        return Response()

    def completed(self, request, data, machine, job):
        requirements = [
            ('result', [True, False, ], lambda v: bool(v), ),
        ]
        data = self.check_requirements(requirements, data)
        result = TestResult(
            job=job,
            success=data['result'],
        )
        result.save()
        return Response()

    def post(self, request, job_id):
        job = get_object_or_404(TestJob, pk=job_id)
        machine = self.discover_machine(request)
        self.ensure_job_access(machine, job)

        valid_states = (
            'error',
            'completed',
        )
        states_mapping = lambda s: str(s).lower().strip()

        requirements = [
            ('state', valid_states, states_mapping, ),
        ]

        data = self.check_requirements(requirements, request.DATA)
        state = data['state']

        if state == 'error':
            return self.error(request, data, machine, job)
        elif state == 'completed':
            return self.completed(request, data, machine, job)


class JobAssignmentView(ExecutorAPIView):
    def get(self, request):
        machine = self.discover_machine(request)

        job = None
        try_again = 15 # 15 seconds. Should be moved into settings sometimes.
        try:
            with transaction.atomic():
                jobs = machine.jobs_available()
                job = jobs.order_by('submission__modified', 'submission__created').first()
                if job is not None:
                    job.machine = machine
                    job.save()
        except IntegrityError:
            try_again = 0 # try again immediately.
        
        if job is None:
            return Response({
                'state': 'not_assigned',
                'try_again': try_again,
            })
        else:
            return Response({
                'state': 'assigned',
                'job': job.pk,
                'job_download': reverse('api:job', kwargs={'job_id': job.pk}),
            })


class AssignmentTestsView(ExecutorAPIView):
    def get(self, request):
        machine = self.discover_machine(request)
        magic_no = 12345678987654321
        url_scheme = reverse('api:assignment_test', kwargs={'ass_id': magic_no, }).replace(str(magic_no), '{}')

        return Response({
            'url_scheme': url_scheme,
            'assignments': [ass.pk for ass in machine.assignments.all()],
        })


class AssignmentTestView(ExecutorAssignmentAPIView):
    def get(self, request, ass_id):
        ass_test = get_object_or_404(AssignmentTest, pk=ass_id)
        machine = self.discover_machine(request)
        self.ensure_assignment_test_access(machine, ass_test)

        test_script_download = None
        if ass_test.test_script:
            test_script_download = reverse('api:assignment_test_download', kwargs={'ass_id': ass_test.pk})

        return Response({
            'id': ass_test.pk,
            'title': ass_test.assignment.title,
            'puppet_config': ass_test.puppet_config,
            'test_script_download': test_script_download,
            'last_modified': ass_test.last_modified,
        })


class AssignmentTestDownloadView(ExecutorAssignmentAPIView):
    def get(self, request, ass_id):
        ass_test = get_object_or_404(AssignmentTest, pk=ass_id)
        machine = self.discover_machine(request)
        self.ensure_assignment_test_access(machine, ass_test)

        file_obj = ass_test.test_script
        file_name = file_obj.name[file_obj.name.rfind('/')+1:]
        mimetype, charset = mimetypes.guess_type(file_name, strict=False)
        if mimetype is None:
            mimetype = 'application/octet-stream'

        r = HttpResponse(file_obj, content_type=mimetype)
        r['Content-Disposition'] = 'attachment; filename="{}"'.format(file_name)
        r['Content-Length'] = str(file_obj.size)
        return r
