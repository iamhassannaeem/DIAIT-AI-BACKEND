from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from ai_call_agent.models import OutboundCampaign, CampaignNumberList, FeedbackAgent
from ai_call_agent.serializers import (
    OutboundCampaignSerializer,
    CampaignNumberListSerializer,
)
from django.contrib.auth import get_user_model

User = get_user_model()
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory


class CampaignNumberListViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CampaignNumberListSerializer

    def get_queryset(self):

        return CampaignNumberList.objects.filter(user=self.request.user)

    def perform_create(self, serializer):

        serializer.save(user=self.request.user)

    def perform_update(self, serializer):

        if self.request.user != serializer.instance.user:
            raise PermissionDenied("You cannot modify this campaign number list.")
        serializer.save()


class OutboundCampaignViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OutboundCampaignSerializer

    def get_queryset(self):

        return OutboundCampaign.objects.filter(feedback_agent__user=self.request.user)

    def perform_create(self, serializer):

        feedback_agents = FeedbackAgent.objects.filter(user=self.request.user)

        if not feedback_agents.exists():
            raise PermissionDenied(
                "You do not have a feedback agent associated with your account."
            )

        feedback_agent = feedback_agents.first()
        serializer.save(feedback_agent=feedback_agent)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )
