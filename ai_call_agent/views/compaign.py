from celery.result import AsyncResult
from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_call_agent.tasks import *
from ai_call_agent.views.utils import stop_campaign_task

User = get_user_model()
from datetime import datetime
import pytz
from ai_call_agent.models import (
    Agent,
    CallLog,
    Contact,
)
from ai_call_agent.serializers import (
    CampaignSerializer,
    CallLogSerializer,
    ContactSerializer,
    CallLogContentSerializer,
)


class CampaignViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CampaignSerializer

    def get_queryset(self):
        agent_ids = Agent.objects.filter(user=self.request.user).values_list(
            "id", flat=True
        )
        return Campaign.objects.filter(agent_id__in=agent_ids)

    def perform_create(self, serializer):
        agents = Agent.objects.filter(user=self.request.user)
        if not agents.exists():
            raise PermissionDenied("No  agent associated with your account.")

        campaign_type = serializer.validated_data.get("type")

    def create(self, request, *args, **kwargs):
        return self._process_campaign(request)

    def update(self, request, *args, **kwargs):
        return self._process_campaign(request, update_instance=True)

    def _process_campaign(self, request, update_instance=False):

        campaign_data = {
            "name": request.data.get("name"),
            "datetime": request.data.get("datetime"),
            "timezone": request.data.get("timezone"),
            "type": request.data.get("type"),
            "agent": request.data.get("agent"),
        }

        agent_id = campaign_data["agent"]
        agent = Agent.objects.filter(id=agent_id).first()
        if not agent:
            raise ValidationError("Invalid agent provided.")
        campaign_data["feedback_agent"] = agent_id

        given_datetime_str = request.data.get("datetime")
        timezone_str = request.data.get("timezone")
        try:
            given_datetime = datetime.strptime(given_datetime_str, "%Y-%m-%d %H:%M:%S")
            timezone = pytz.timezone(timezone_str)
            given_datetime = timezone.localize(given_datetime)
        except pytz.UnknownTimeZoneError:
            raise ValidationError("Invalid timezone provided.")

        current_time_in_timezone = datetime.now(timezone)
        if given_datetime <= current_time_in_timezone:
            raise ValidationError("The provided datetime cannot be in the past.")

        local_time = datetime.now().astimezone()
        time_difference = given_datetime - current_time_in_timezone
        adjusted_local_time = local_time + time_difference

        if update_instance:
            instance = self.get_object()
            old_task_id = instance.task_id
            if old_task_id:
                try:
                    task = AsyncResult(old_task_id)
                    task.revoke(terminate=True)
                except Exception as e:
                    print(f"Failed to revoke task {old_task_id}: {str(e)}")

            campaign_serializer = CampaignSerializer(
                instance, data=campaign_data, context={"request": request}, partial=True
            )
        else:
            campaign_serializer = CampaignSerializer(
                data=campaign_data, context={"request": request}
            )

        campaign_serializer.is_valid(raise_exception=True)
        campaign = campaign_serializer.save()

        task = Ai_task.apply_async((campaign.id,), eta=adjusted_local_time)
        campaign.campaign_local_datetime = adjusted_local_time
        campaign.task_id = task.id
        campaign.status = 2
        campaign.save()

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
            call_detail_serializer = CallLogSerializer(data=call_data)
            call_detail_serializer.is_valid(raise_exception=True)
            call_detail_serializer.save()

        return Response(
            {"campaign_id": campaign.id},
            status=status.HTTP_200_OK if update_instance else status.HTTP_201_CREATED,
        )


class StopCampaignTaskViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["post"])
    def stop(self, request, pk=None):
        campaign_id = pk
        stop_campaign_task(campaign_id)
        return Response(
            {"message": "Campaign task stopped successfully."},
            status=status.HTTP_200_OK,
        )


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]


class CallLogViewSet(viewsets.ModelViewSet):
    queryset = CallLog.objects.all()
    serializer_class = CallLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        campaigns = Campaign.objects.filter(user=user)
        return CallLog.objects.filter(campaign__in=campaigns)


class CallLogContentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        user = request.user
        campaigns = Campaign.objects.filter(user=user)
        call_logs = CallLog.objects.filter(campaign__in=campaigns)
        serialized_data = CallLogContentSerializer(call_logs, many=True).data
        filtered_data = [item for item in serialized_data if item["combined_answers"]]
        return Response(filtered_data)
