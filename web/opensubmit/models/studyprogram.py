from django.db import models

class StudyProgram(models.Model):
    '''
        A study program a student belongs to.
    '''
    title = models.CharField(max_length=200)

    class Meta:
        app_label = 'opensubmit'

    def __unicode__(self):
        return unicode(self.title)

