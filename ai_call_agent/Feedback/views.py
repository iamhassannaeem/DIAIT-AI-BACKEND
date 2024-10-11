
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from ..models import FeedBackAgent
from .serializers import FeedBackAgentSerializer
from django.shortcuts import get_object_or_404


DUMMY_USER_ID = 22

class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = FeedBackAgent.objects.all()
    serializer_class = FeedBackAgentSerializer

    def get_queryset(self):

        return FeedBackAgent.objects.filter(user_id=DUMMY_USER_ID)

    def create(self, request, *args, **kwargs):

        request.data['user'] = DUMMY_USER_ID
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):

        instance = get_object_or_404(FeedBackAgent, feedback_id=kwargs['pk'], user_id=DUMMY_USER_ID)
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):

        instance = get_object_or_404(FeedBackAgent, feedback_id=kwargs['pk'], user_id=DUMMY_USER_ID)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
