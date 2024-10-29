from rest_framework import viewsets
from rest_framework import permissions
from .models import FeedBackAgent
from .serializers import FeedBackAgentSerializer


class FeedBackAgentViewSet(viewsets.ModelViewSet):
    queryset = FeedBackAgent.objects.all()
    serializer_class = FeedBackAgentSerializer
    permission_classes = [permissions.IsAuthenticated]
