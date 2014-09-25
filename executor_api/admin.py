from django.contrib import admin

from executor_api.models import *

# Register your models here.
class TestMachineAdmin(admin.ModelAdmin):
    model = TestMachine
    list_display = ['machine_user', 'name', ]

admin.site.register(TestMachine, TestMachineAdmin)

# default admins
admin.site.register(AssignmentTest, admin.ModelAdmin)
admin.site.register(TestJob, admin.ModelAdmin)
admin.site.register(TestResult, admin.ModelAdmin)