from rest_framework import viewsets
from .serializers import AssignmentSerializer

from opensubmit.models import Assignment


class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
