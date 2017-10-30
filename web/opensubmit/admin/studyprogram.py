from django.contrib.admin import ModelAdmin

def number_of_students(studyprogram):
    ''' The list of grading schemes using this grading.'''
    return str(studyprogram.students.all().count())

class StudyProgramAdmin(ModelAdmin):
    list_display = ['__str__', number_of_students]

    class Media:
        css = {'all': ('css/teacher.css',)}
