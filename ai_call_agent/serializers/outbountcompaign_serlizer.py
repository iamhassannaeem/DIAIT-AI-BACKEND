from rest_framework import serializers

from ai_call_agent.models import (
    Campaign,
    FeedbackAgent,
    FeedbackQuestion,
    CallDetails,
    TimeZone,
    SalesAgent,
)


class FeedbackQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackQuestion
        fields = ["id", "order", "question_text"]


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
    timezone = serializers.PrimaryKeyRelatedField(queryset=TimeZone.objects.all())
    feedback_agent = serializers.PrimaryKeyRelatedField(
        queryset=FeedbackAgent.objects.all(), required=False
    )
    sales_agent = serializers.PrimaryKeyRelatedField(
        queryset=SalesAgent.objects.all(), required=False
    )
    call_details = CallDetailsSerializer(many=True)

    class Meta:
        model = Campaign
        fields = [
            "id",
            "agent_name",
            "datetime",
            "timezone",
            "status",
            "type",
            "feedback_agent",
            "sales_agent",
            "call_details",
        ]

    def create(self, validated_data):
        call_details_data = validated_data.pop("call_details")
        campaign = Campaign.objects.create(**validated_data)

        # Set the campaign for each call detail and save
        for call_detail in call_details_data:
            call_detail["campaign"] = campaign  # Set the campaign field
            CallDetails.objects.create(**call_detail)

        return campaign
