import logging
logger = logging.getLogger('OpenSubmit')

class CourseRegister():
	'''
		Allows to enable a course for an user based on a GET parameter with the course ID.
		Sanity checks are done in the model method for adding it, which may throw a 404 exception.
	'''
	def process_request(self, request):
	    if 'course' in request.GET and request.user and request.user.is_authenticated():
        	course_id=request.GET['course']

        	request.user.profile.add_course_safe(course_id)
        	logger.debug("Adding user %u to course %s"%(request.user.pk, course_id))
		return None
