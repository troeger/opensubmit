'''
    The model storing the configured access data for LTI consumers.
'''

from django.db import models
import logging
logger = logging.getLogger('OpenSubmit')

class LtiConsumer(models.Model):
    title = models.CharField(max_length=200, help_text="Descriptive text for the LTI consumer.")
    key = models.CharField(max_length=20, help_text="The key to be used by the LTI consumer.")
    secret = models.CharField(max_length=20, help_text="The secret to be used by the LTI consumer.")

    class Meta:
        app_label = 'opensubmit'

    def __unicode__(self):
        return unicode(self.title)

def consumer_lookup(key):
    '''
        Consumer function as expected by blti package.
    '''
    try:
        return LtiConsumer.objects.get(key=key).secret
    except:
        return None