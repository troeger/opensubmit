import opensubmit
from opensubmit import settings


def footer(request):
    return {
        'main_url': settings.MAIN_URL,
        'opensubmit_version': opensubmit.__version__,
        'opensubmit_admin': settings.ADMINS[0][1],
    }
