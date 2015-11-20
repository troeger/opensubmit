from django.db import models

class GradingScheme(models.Model):
    title = models.CharField(max_length=200, help_text="Choose a directly understandable name, such as 'ECTS' or 'Pass / Fail'.")
    gradings = models.ManyToManyField('Grading', related_name='schemes', help_text="The list of gradings that form this grading scheme.")

    class Meta:
        app_label = 'opensubmit'

    def __unicode__(self):
        return unicode(self.title)
