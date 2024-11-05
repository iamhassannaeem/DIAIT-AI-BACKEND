from rest_framework import serializers

from ai_call_agent.models import (
    Campaign,
    FeedbackAgent,
    FeedbackQuestion,
    CallDetails,
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

        instance.name = validated_data.get("name", instance.name)
        instance.datetime = validated_data.get("datetime", instance.datetime)
        instance.timezone = validated_data.get("timezone", instance.timezone)
        instance.status = validated_data.get("status", instance.status)
        instance.type = validated_data.get("type", instance.type)
        instance.feedback_agent = validated_data.get(
            "feedback_agent", instance.feedback_agent
        )
        instance.sales_agent = validated_data.get("sales_agent", instance.sales_agent)
        instance.save()

        call_details_data = validated_data.pop("call_details", None)
        if call_details_data is not None:
            instance.call_details.all().delete()

            for call_detail in call_details_data:
                call_detail["campaign"] = instance
                CallDetails.objects.create(**call_detail)

        return instance
