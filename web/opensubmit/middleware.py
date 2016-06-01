from django.contrib import messages

import logging
logger = logging.getLogger('OpenSubmit')

class CourseRegister():
    '''
        Allows to enable a course for an user based on a GET parameter with the course ID.
        Sanity checks are done in the model method for adding it, which may throw a 404 exception.
    '''
    def process_request(self, request):
        if 'course' in request.GET:
            if request.user and request.user.is_authenticated():
                # We got a user being logged in. Register him for the course.
                title = request.user.profile.add_course_safe(request.GET['course'])
                messages.add_message(request, messages.INFO, "You were added to the course '%s'."%title)
            else:
                # We got the wish for course registration, but the user is not logged in.
                # Remember this as part of the session, which survives the login, and do it later.
                request.session["course_registration_request"]=request.GET['course']
        else:
            if request.user and request.user.is_authenticated():
                # We got a user being logged in.
                # Check if we have an earlier request for course registration still pending, and do it.
                if "course_registration_request" in request.session:
                    # Remove session entry anyway, so that a failing registration request does not happen forever.
                    course_id = request.session['course_registration_request']
                    del request.session['course_registration_request']
                    title = request.user.profile.add_course_safe(course_id)
                    messages.add_message(request, messages.INFO, "You were added to the course '%s'."%title)
        return None
