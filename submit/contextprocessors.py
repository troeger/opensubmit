import submit
from submit import settings

def footer(request):
    return {'main_url': settings.MAIN_URL, 'submit_version': submit.__version__, 'submit_admin': settings.ADMINS[0][1]}
