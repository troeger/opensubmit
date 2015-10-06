from django.contrib.auth.models import User
from opensubmit.models import Course, Grading, GradingScheme, Assignment, SubmissionFile, Submission, TestMachine
from django.contrib.admin.sites import AdminSite

from user import UserAdmin
from course import CourseAdmin
from grading import GradingAdmin
from gradingscheme import GradingSchemeAdmin
from assignment import AssignmentAdmin
from submissionfile import SubmissionFileAdmin
from submission import SubmissionAdmin

class AdminBackend(AdminSite):
    site_header = "OpenSubmit Admin Backend"
    site_title = "OpenSubmit Admin Backend"

admin_backend = AdminBackend(name="admin")
admin_backend.register(User, UserAdmin)
admin_backend.register(Course, CourseAdmin)

class TeacherBackend(AdminSite):
    site_header = "Teacher Backend"
    site_title = "OpenSubmit Teacher Backend"
    login_template = "teacher/login.html"

teacher_backend = TeacherBackend(name="teacher")
teacher_backend.register(Grading, GradingAdmin)
teacher_backend.register(GradingScheme, GradingSchemeAdmin)
teacher_backend.register(Assignment, AssignmentAdmin)
teacher_backend.register(SubmissionFile, SubmissionFileAdmin)
teacher_backend.register(Submission, SubmissionAdmin)
teacher_backend.register(Course, CourseAdmin)
teacher_backend.register(TestMachine)
