from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ai_call_agent.models import Campaign, CallDetails, FeedbackAgent, SalesAgent
from ai_call_agent.serializers import CampaignSerializer, CallDetailsSerializer

User = get_user_model()


class CampaignViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CampaignSerializer

    def get_queryset(self):
        feedback_agent_ids = FeedbackAgent.objects.filter(
            user=self.request.user
        ).values("id")
        sales_agent_ids = SalesAgent.objects.filter(user=self.request.user).values("id")

        return Campaign.objects.filter(
            Q(feedback_agent__in=feedback_agent_ids)
            | Q(sales_agent__in=sales_agent_ids)
        )

    def perform_create(self, serializer):
        feedback_agents = FeedbackAgent.objects.filter(user=self.request.user)
        sales_agents = SalesAgent.objects.filter(user=self.request.user)

        if not feedback_agents.exists() and not sales_agents.exists():
            raise PermissionDenied(
                "No feedback or sales agent associated with your account."
            )

        campaign_type = serializer.validated_data.get("type")
        if campaign_type == 1:
            feedback_agent = feedback_agents.first()
            campaign = serializer.save(feedback_agent=feedback_agent)
        elif campaign_type == 2:
            sales_agent = sales_agents.first()
            campaign = serializer.save(sales_agent=sales_agent)

        call_details_data = self.request.data.get("call_details", [])
        for call_data in call_details_data:
            call_data["campaign"] = campaign.id
            call_detail_serializer = CallDetailsSerializer(data=call_data)
            call_detail_serializer.is_valid(raise_exception=True)
            call_detail_serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class CallDetailsViewSet(viewsets.ModelViewSet):
    queryset = CallDetails.objects.all()
    serializer_class = CallDetailsSerializer
    permission_classes = [IsAuthenticated]
