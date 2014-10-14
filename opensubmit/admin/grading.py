from django.contrib.admin import ModelAdmin

def grading_schemes(grading):
    ''' The list of grading schemes using this grading.'''
    return ",\n".join([str(scheme) for scheme in grading.schemes.all()])


def means_passed(grading):
    return grading.means_passed
means_passed.boolean = True

class GradingAdmin(ModelAdmin):
    list_display = ['__unicode__', grading_schemes, means_passed]
