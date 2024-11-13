from celery.result import AsyncResult
from django.contrib.auth import get_user_model
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ai_call_agent.models import (
    CallDetails,
    FeedbackAgent,
    SalesAgent,
    Calllogs,
    Question,
)
from ai_call_agent.serializers import (
    CampaignSerializer,
    CallDetailsSerializer,
    QuestionSerializer,
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
        print("test")
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
        return self._process_campaign(request)

    def update(self, request, *args, **kwargs):
        return self._process_campaign(request, update_instance=True)

    def _process_campaign(self, request, update_instance=False):
        campaign_data = {
            "name": request.data.get("name"),
            "datetime": request.data.get("datetime"),
            "timezone": request.data.get("timezone"),
            "type": request.data.get("type"),
        }

        campaign_type = str(request.data.get("type"))
        agent_id = request.data.get("agent")

        if campaign_type == "1":
            agent = FeedbackAgent.objects.filter(id=agent_id).first()
            if not agent:
                raise ValidationError("Invalid feedback agent provided.")
            campaign_data["feedback_agent"] = agent_id
        elif campaign_type == "2":
            agent = SalesAgent.objects.filter(id=agent_id).first()
            if not agent:
                raise ValidationError("Invalid sales agent provided.")
            campaign_data["sales_agent"] = agent_id
        else:
            raise ValidationError("Invalid campaign type provided.")

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

        if update_instance:
            instance = self.get_object()
            old_task_id = instance.task_id

            print("old_task_id", old_task_id)
            campaign_id = instance.id
            print("campaign_id", campaign_id)

            if old_task_id:
                try:
                    task = AsyncResult(old_task_id)
                    task.revoke(terminate=True)
                    print(f"revideed{old_task_id}")

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
            call_detail_serializer = CallDetailsSerializer(data=call_data)
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


class CallDetailsViewSet(viewsets.ModelViewSet):
    queryset = CallDetails.objects.all()
    serializer_class = CallDetailsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        campaigns = Campaign.objects.filter(user=user)
        return CallDetails.objects.filter(campaign__in=campaigns)


class FeedbackReportViewSet(viewsets.ModelViewSet):
    serializer_class = FeedbackReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        feedback_agent_campaigns = Campaign.objects.filter(feedback_agent__user=user)
        sales_agent_campaigns = Campaign.objects.filter(sales_agent__user=user)

        campaigns = feedback_agent_campaigns | sales_agent_campaigns

        return Calllogs.objects.filter(call_detail__campaign__in=campaigns)

    def list(self, request):
        reports = (
            self.get_queryset()
            .values("call_detail_id")
            .annotate(
                answers=ArrayAgg("answer"),
                sentiments=ArrayAgg("call_sentiments"),
                feedback_ids=ArrayAgg("feedback_question_id"),
            )
        )

        response_data = []
        for report in reports:
            feedback_questions = Question.objects.filter(id__in=report["feedback_ids"])
            questions_data = QuestionSerializer(feedback_questions, many=True).data

            call_detail = CallDetails.objects.filter(
                id=report["call_detail_id"]
            ).first()
            phone_number = call_detail.phone_number if call_detail else "Unknown"

            question_map = {q["id"]: q for q in questions_data}

            combined_answers = []
            for idx, answer in enumerate(report["answers"]):
                feedback_id = (
                    report["feedback_ids"][idx]
                    if idx < len(report["feedback_ids"])
                    else None
                )
                question_text = question_map.get(feedback_id, {}).get(
                    "question_text", "Unknown Question"
                )

                sentiment_text = (
                    report["sentiments"][idx].strip().capitalize()
                    if idx < len(report["sentiments"]) and report["sentiments"][idx]
                    else "Unknown Sentiment"
                )

                valid_sentiments = dict(Calllogs.SENTIMENT_CHOICES).values()
                sentiment_display = (
                    sentiment_text
                    if sentiment_text in valid_sentiments
                    else "Unknown Sentiment"
                )

                combined_answers.append(
                    {
                        "answer": answer,
                        "feedback_question_id": feedback_id,
                        "question_text": question_text,
                        "sentiment": sentiment_display,
                    }
                )

            response_data.append(
                {
                    "call_detail_id": report["call_detail_id"],
                    "phone_number": phone_number,
                    "combined_answers": combined_answers,
                }
            )

        return Response(response_data)

    def retrieve(self, request, pk=None):
        try:
            feedback_report = self.get_queryset().get(id=pk)
            serializer = FeedbackReportSerializer(feedback_report)
            return Response(serializer.data)
        except Calllogs.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
