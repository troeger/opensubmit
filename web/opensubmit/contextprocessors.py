from opensubmit import settings


def footer(request):
    return {
        'main_url': settings.MAIN_URL,
        'opensubmit_version': settings.VERSION,
        'opensubmit_admin_name': settings.ADMIN_NAME,
        'opensubmit_admin_mail': settings.ADMIN_EMAIL,
        'opensubmit_admin_address': settings.ADMIN_ADDRESS,
    }
