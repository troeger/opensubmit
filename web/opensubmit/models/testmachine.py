from django.db import models
from django.utils import timezone


class TestMachine(models.Model):
    name = models.CharField(null=True, blank=True, max_length=50, help_text="Human-readable name of this machine.")
    host = models.CharField(null=True, max_length=50, help_text="UUID of this machine.")
    last_contact = models.DateTimeField(editable=False, default=timezone.now)
    config = models.TextField(null=True, help_text="Host configuration in JSON format.")
    enabled = models.BooleanField(default=True, help_text="Test machines can be temporarily disabled for maintenance. All jobs are held back during that time.")

    class Meta:
        app_label = 'opensubmit'

    def __str__(self):
        if self.name:
            return self.name
        else:
            return "Test Machine {0}".format(self.pk)
