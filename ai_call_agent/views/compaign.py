from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
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
        ).values_list("id", flat=True)
        sales_agent_ids = SalesAgent.objects.filter(user=self.request.user).values_list(
            "id", flat=True
        )

        return Campaign.objects.filter(
            Q(feedback_agent_id__in=feedback_agent_ids)
            | Q(sales_agent_id__in=sales_agent_ids)
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

        return campaign

    def create(self, request, *args, **kwargs):

        campaign_data = {
            "name": request.data.get("name"),
            "datetime": request.data.get("datetime"),
            "timezone": request.data.get("timezone"),
            "type": request.data.get("type"),
        }

        campaign_type = str(request.data.get("type"))
        if campaign_type == "1":
            campaign_data["feedback_agent"] = request.data.get("agent")
        elif campaign_type == "2":
            campaign_data["sales_agent"] = request.data.get("agent")
        else:
            raise ValidationError("Invalid campaign type provided.")

        campaign_serializer = CampaignSerializer(data=campaign_data)
        campaign_serializer.is_valid(raise_exception=True)
        campaign = campaign_serializer.save()

        call_details = request.data.get("call_details", [])
        for call in call_details:
            call_data = {
                "campaign": campaign.id,
                "phone_number": call.get("phone_number"),
                "tag": call.get("tag"),
                "call_start_time": call.get("call_start_time"),
                "call_end_time": call.get("call_end_time"),
                "conversation": call.get("conversation"),
                "call_cost": call.get("call_cost"),
            }
            call_detail_serializer = CallDetailsSerializer(data=call_data)
            call_detail_serializer.is_valid(raise_exception=True)
            call_detail_serializer.save()

        return Response({"campaign_id": campaign.id}, status=status.HTTP_201_CREATED)


class CallDetailsViewSet(viewsets.ModelViewSet):
    queryset = CallDetails.objects.all()
    serializer_class = CallDetailsSerializer
    permission_classes = [IsAuthenticated]
