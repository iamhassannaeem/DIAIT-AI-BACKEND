from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_call_agent.models import (
    CallDetails,
    FeedbackAgent,
    SalesAgent,
    FeedbackReport,
)
from ai_call_agent.serializers import (
    CampaignSerializer,
    CallDetailsSerializer,
    FeedbackReportSerializer,
)
from ai_call_agent.tasks import *
from .utils import stop_campaign_task

User = get_user_model()
from datetime import datetime
import pytz


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
            serializer.save(feedback_agent=feedback_agent)
        elif campaign_type == 2:
            sales_agent = sales_agents.first()
            serializer.save(sales_agent=sales_agent)

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

        given_datetime_str = request.data.get("datetime")
        timezone_str = request.data.get("timezone")

        given_datetime = datetime.strptime(given_datetime_str, "%Y-%m-%d %H:%M:%S")
        timezone = pytz.timezone(timezone_str)
        given_datetime = timezone.localize(given_datetime)

        current_time_in_timezone = datetime.now(timezone)
        if given_datetime <= current_time_in_timezone:
            raise ValidationError("The provided datetime cannot be in the past.")

        local_time = datetime.now().astimezone()
        time_difference = given_datetime - current_time_in_timezone
        adjusted_local_time = local_time + time_difference

        task = Ai_task.apply_async((campaign.id,), eta=adjusted_local_time)

        campaign.task_id = task.id
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
            call_detail_serializer = CallDetailsSerializer(data=call_data)
            call_detail_serializer.is_valid(raise_exception=True)
            call_detail_serializer.save()

        return Response({"campaign_id": campaign.id}, status=status.HTTP_201_CREATED)


class StopCampaignTaskView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, campaign_id):
        stop_campaign_task(campaign_id)
        return Response(
            {"message": "Campaign task stopped successfully."},
            status=status.HTTP_200_OK,
        )


class CallDetailsViewSet(viewsets.ModelViewSet):
    queryset = CallDetails.objects.all()
    serializer_class = CallDetailsSerializer
    permission_classes = [IsAuthenticated]


class FeedbackReportViewSet(viewsets.ModelViewSet):
    queryset = FeedbackReport.objects.all().select_related(
        "call_detail", "feedback_question"
    )
    serializer_class = FeedbackReportSerializer

    def list(self, request, *args, **kwargs):

        feedback_reports = self.get_queryset()
        grouped_data = {}

        for report in feedback_reports:
            call_detail_id = report.call_detail.id
            if call_detail_id not in grouped_data:
                grouped_data[call_detail_id] = {
                    "call_detail": call_detail_id,
                    "phone_number": [],
                    "feedback_questions": [],
                    "answers": [],
                    "call_sentiments": [],
                }

            phone_number = report.call_detail.phone_number
            feedback_question_text = report.feedback_question.question_text
            answer = report.answer
            call_sentiment = report.get_call_sentiments_display()

            if phone_number not in grouped_data[call_detail_id]["phone_number"]:
                grouped_data[call_detail_id]["phone_number"].append(phone_number)
            if (
                feedback_question_text
                not in grouped_data[call_detail_id]["feedback_questions"]
            ):
                grouped_data[call_detail_id]["feedback_questions"].append(
                    feedback_question_text
                )
            if answer not in grouped_data[call_detail_id]["answers"]:
                grouped_data[call_detail_id]["answers"].append(answer)
            if call_sentiment not in grouped_data[call_detail_id]["call_sentiments"]:
                grouped_data[call_detail_id]["call_sentiments"].append(call_sentiment)

        # Convert grouped data to a list and return it
        return Response(list(grouped_data.values()))
