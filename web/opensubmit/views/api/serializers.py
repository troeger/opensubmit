from rest_framework import serializers

from opensubmit.models import Assignment


class AssignmentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Assignment
        fields = ('pk', 'attachment_test_validity', 'attachment_test_full')
