from rest_framework import serializers

from ai_call_agent.models import (
    Campaign,
    FeedbackAgent,
    CallDetails,
    SalesAgent,
    FeedbackReport,
)
from ai_call_agent.serializers import FeedbackQuestionSerializer


class FeedbackAgentSerializer(serializers.ModelSerializer):
    feed_questions = FeedbackQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = FeedbackAgent
        fields = [
            "id",
            "name",
            "active",
            "gender",
            "created_date",
            "user",
            "feed_questions",
        ]


class CallDetailsSerializer(serializers.ModelSerializer):
    campaign = serializers.PrimaryKeyRelatedField(queryset=Campaign.objects.all())

    class Meta:
        model = CallDetails
        fields = [
            "id",
            "phone_number",
            "tag",
            "call_start_time",
            "call_end_time",
            "conversation",
            "status",
            "call_cost",
            "campaign",
        ]


class CampaignSerializer(serializers.ModelSerializer):
    feedback_agent = serializers.PrimaryKeyRelatedField(
        queryset=FeedbackAgent.objects.all(), required=False
    )
    sales_agent = serializers.PrimaryKeyRelatedField(
        queryset=SalesAgent.objects.all(), required=False
    )
    call_details = CallDetailsSerializer(many=True, required=False)
    agent_name = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = [
            "id",
            "name",
            "datetime",
            "timezone",
            "status",
            "type",
            "feedback_agent",
            "sales_agent",
            "agent_name",
            "call_details",
            "task_id",
        ]

    def get_agent_name(self, obj):

        if obj.feedback_agent:
            return obj.feedback_agent.name
        elif obj.sales_agent:
            return obj.sales_agent.name
        return None

    def create(self, validated_data):
        call_details_data = validated_data.pop("call_details", [])

        campaign = Campaign.objects.create(**validated_data)

        if call_details_data:
            for call_detail in call_details_data:
                call_detail["campaign"] = campaign
                CallDetails.objects.create(**call_detail)

        return campaign

    def update(self, instance, validated_data):
        call_details_data = validated_data.pop("call_details", [])

        campaign_type = validated_data.get("type", instance.type)
        agent_id = self.context.get("request").data.get("agent")

        if campaign_type == 1:
            if agent_id:
                instance.feedback_agent = FeedbackAgent.objects.get(id=agent_id)
                instance.sales_agent = None
        elif campaign_type == 2:
            if agent_id:
                instance.sales_agent = SalesAgent.objects.get(id=agent_id)
                instance.feedback_agent = None
        else:
            raise serializers.ValidationError("Invalid campaign type.")

        instance = super().update(instance, validated_data)

        instance.calls.all().delete()
        for call_detail in call_details_data:
            call_detail["campaign"] = instance
            CallDetails.objects.create(**call_detail)

        return instance


class FeedbackReportSerializer(serializers.ModelSerializer):
    feedback_question_text = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()

    class Meta:
        model = FeedbackReport
        fields = [
            "id",
            "feedback_question_text",
            "answer",
            "call_sentiments",
            "call_detail",
            "phone_number",
        ]

    def get_feedback_question_text(self, obj):
        return obj.feedback_question.question_text

    def get_phone_number(self, obj):
        return obj.call_detail.phone_number

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if "call_detail" not in self.context:
            self.context["call_detail"] = {}

        call_detail_id = instance.call_detail.id
        if call_detail_id not in self.context["call_detail"]:
            self.context["call_detail"][call_detail_id] = {
                "call_detail": call_detail_id,
                "phone_number": [],
                "feedback_questions": [],
                "answers": [],
                "call_sentiments": [],
            }

        phone_number = instance.call_detail.phone_number
        feedback_question_text = self.get_feedback_question_text(instance)
        answer = instance.answer
        call_sentiment = instance.get_call_sentiments_display()

        if (
            phone_number
            not in self.context["call_detail"][call_detail_id]["phone_number"]
        ):
            self.context["call_detail"][call_detail_id]["phone_number"].append(
                phone_number
            )
        if (
            feedback_question_text
            not in self.context["call_detail"][call_detail_id]["feedback_questions"]
        ):
            self.context["call_detail"][call_detail_id]["feedback_questions"].append(
                feedback_question_text
            )
        if answer not in self.context["call_detail"][call_detail_id]["answers"]:
            self.context["call_detail"][call_detail_id]["answers"].append(answer)
        if (
            call_sentiment
            not in self.context["call_detail"][call_detail_id]["call_sentiments"]
        ):
            self.context["call_detail"][call_detail_id]["call_sentiments"].append(
                call_sentiment
            )

        return self.context["call_detail"][call_detail_id]
