from django.contrib.auth.models import User, Permission, Group
from opensubmit.models import Course, Grading, GradingScheme, Assignment, SubmissionFile, Submission, TestMachine
from opensubmit import settings
from django.contrib.admin.sites import AdminSite
from django.shortcuts import redirect

from user import UserAdmin
from course import CourseAdmin
from grading import GradingAdmin
from gradingscheme import GradingSchemeAdmin
from assignment import AssignmentAdmin
from submissionfile import SubmissionFileAdmin
from submission import SubmissionAdmin

class AdminBackend(AdminSite):
	site_header = "OpenSubmit"
	site_url = settings.MAIN_URL
	index_title = "Administrator Backend"

	def app_index(self, request, app_label, extra_context=None):
		return redirect('admin:index')


admin_backend = AdminBackend(name="admin")
admin_backend.register(User, UserAdmin)
admin_backend.register(Course, CourseAdmin)
admin_backend.register(TestMachine)
admin_backend.register(Permission)
admin_backend.register(Group)


class TeacherBackend(AdminSite):
	site_header = "OpenSubmit"
	site_url = settings.MAIN_URL
	index_title = "Teacher Backend"

	def app_index(self, request, app_label, extra_context=None):
		return redirect('teacher:index')

teacher_backend = TeacherBackend(name="teacher")
teacher_backend.register(Grading, GradingAdmin)
teacher_backend.register(GradingScheme, GradingSchemeAdmin)
teacher_backend.register(Assignment, AssignmentAdmin)
teacher_backend.register(SubmissionFile, SubmissionFileAdmin)
teacher_backend.register(Submission, SubmissionAdmin)
teacher_backend.register(Course, CourseAdmin)
teacher_backend.register(TestMachine)
