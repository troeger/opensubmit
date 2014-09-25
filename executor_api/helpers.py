from pprint import pprint
from functools import wraps

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.utils.decorators import available_attrs

from rest_framework.exceptions import ParseError
from rest_framework.permissions import BasePermission
from rest_framework.views import APIView

from executor_api.models import TestMachine


SAFE_SCHEMES = [
    "https",
]


def require_ssl(view):
    @wraps(view, assigned=available_attrs(view))
    def require_ssl_view_wrapper(request, *args, **kwargs):
        if not settings.DEBUG:
            scheme = request.META['wsgi.url_scheme'].lower().strip()
            if scheme not in SAFE_SCHEMES:
                return HttpResponseForbidden()
        return view(request, *args, **kwargs)
    return require_ssl_view_wrapper


class HasAPIPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('executor_api.api_usage')


class ExecutorAPIView(APIView):
    permission_classes = (HasAPIPermission, )
    
    def discover_machine(self, request, require=True):
        try:
            machine = TestMachine.objects.get(machine_user=request.user)
        except TestMachine.DoesNotExist:
            machine = None

            if require:
                raise PermissionDenied("Only test machines are allowed to access this view.")
        machine.last_contact = timezone.now()
        machine.save()
        return machine

    def check_requirements(self, requirements, data):
        data = dict(data)

        for requirement in requirements:
            field, validity = requirement[:2]
            if not field in data:
                raise ParseError("Field '{}' must be set.".format(field))

            value = data[field]
            if len(requirement) == 3:
                mapping = requirement[2]
                try:
                    value = mapping(value)
                except Exception:
                    raise ParseError("The value given for the field '{}' is invalid.".format(field))
                data[field] = value
            if hasattr(validity, '__call__'):
                validity_check = validity

                is_valid = validity_check(value)
                if not is_valid:
                    raise ParseError("The value given for the field '{}' is invalid.".format(field))
            else:
                valid_values = validity

                if not value in valid_values:
                    message_fmt = "'{}' is not a valid value for '{}'. Valid values are '{}'."
                    message = message_fmt.format(
                        value,
                        field,
                        "', '".join(valid_values)
                    )
                    raise ParseError(message)

        return data

class ExecutorAssignmentAPIView(ExecutorAPIView):
    def ensure_assignment_test_access(self, machine, assignment_test):
        perm_err = PermissionDenied("You are not allowed to access this AssignmentTest object.")
        if not assignment_test.machines.filter(pk__exact=machine.pk).exists():
            raise perm_err


class ExecutorJobAPIView(ExecutorAPIView):
    def ensure_job_access(self, machine, job):
        perm_err = PermissionDenied("You are not allowed to access this Job object.")
        if job.machine != machine:
            raise perm_err

        if job.result is not None:
            raise perm_err
