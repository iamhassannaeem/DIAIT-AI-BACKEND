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
            "call_duaration",
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
            "campaign_local_datetime",
        ]

    def get_agent_name(self, obj):

        if obj.feedback_agent:
            return obj.feedback_agent.name
        elif obj.sales_agent:
            return obj.sales_agent.name
        return None

    def create(self, validated_data):
        call_details_data = validated_data.pop("call_details", [])
        validated_data["user"] = self.context.get("request").user

        campaign = Campaign.objects.create(**validated_data)

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

        if call_details_data:
            CallDetails.objects.filter(campaign=instance).delete()
            for call_detail in call_details_data:
                call_detail["campaign"] = instance
                CallDetails.objects.create(**call_detail)

        return instance

    # def update(self, instance, validated_data):
    #     print("dfvdmfhd")
    #     call_details_data = validated_data.pop("call_details", [])
    #     campaign_type = validated_data.get("type", instance.type)
    #     agent_id = self.context.get("request").data.get("agent")
    #
    #     if campaign_type == 1:
    #         if agent_id:
    #             instance.feedback_agent = FeedbackAgent.objects.get(id=agent_id)
    #             instance.sales_agent = None
    #     elif campaign_type == 2:
    #         if agent_id:
    #             instance.sales_agent = SalesAgent.objects.get(id=agent_id)
    #             instance.feedback_agent = None
    #     else:
    #         raise serializers.ValidationError("Invalid campaign type.")
    #
    #     instance = super().update(instance, validated_data)
    #
    #     CallDetails.objects.filter(campaign=instance, status__isnull=True).delete()
    #     for call_detail in call_details_data:
    #         call_detail["campaign"] = instance
    #         CallDetails.objects.create(**call_detail)
    #
    #     return instance


class FeedbackReportSerializer(serializers.ModelSerializer):
    feedback_question = FeedbackQuestionSerializer(read_only=True)

    class Meta:
        model = FeedbackReport
        fields = [
            "id",
            "answer",
            "call_sentiments",
            "call_detail",
            "feedback_question",
        ]
