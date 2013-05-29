import submit
from submit import settings

def footer(request):
    return {'submit_version': submit.__version__, 'submit_admin': settings.ADMINS[0][1]}
