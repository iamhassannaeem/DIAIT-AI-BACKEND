from rest_framework import serializers

from ai_call_agent.models import (
    Campaign,
    Agent,
    CallLog,
    Contact,
)


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ["id", "phone_number", "email", "address"]


class CallLogSerializer(serializers.ModelSerializer):
    campaign = serializers.PrimaryKeyRelatedField(queryset=Campaign.objects.all())
    contact = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.all(), required=False
    )
    class Meta:
        model = CallLog
        fields = [
            "id",
            "phone_number",
            "tag",
            "call_start_time",
            "call_end_time",
            "call_duration",
            "conversation",
            "status",
            "call_cost",
            "campaign",
            "content",
            "sentiments",
            "contact",
        ]


class CallLogContentSerializer(serializers.ModelSerializer):
    combined_answers = serializers.SerializerMethodField()
    class Meta:
        model = CallLog
        fields = [
            "id",
            "phone_number",
            "combined_answers",
        ]

    def get_combined_answers(self, instance):
        content = instance.content or {}
        combined_answers = []
        for i in range(1, (len(content) // 2) + 1):
            combined_answers.append(
                {
                    "question_text": content.get(f"Q{i}", "No Question"),
                    "answer": content.get(f"A{i}", "No Answer"),
                    "sentiment": self.get_sentiment(instance, i),
                }
            )

        return combined_answers

    def get_sentiment(self, instance, index):
        sentiments = instance.sentiments or {}
        if index == 1:
            return "positive" if sentiments.get("positive", 0) > 0.5 else "neutral"
        elif index == 2:
            return "neutral" if sentiments.get("neutral", 0) > 0.5 else "unknown"
        return "unknown"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["call_detail_id"] = data.pop("id")
        return data


class CampaignSerializer(serializers.ModelSerializer):
    agent = serializers.PrimaryKeyRelatedField(
        queryset=Agent.objects.all(), required=False
    )
    call_details = CallLogSerializer(many=True, required=False)
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
            "agent",
            "agent_name",
            "call_details",
            "task_id",
            "campaign_local_datetime",
        ]

    def get_agent_name(self, obj):
        return obj.agent.name if obj.agent else None

    def create(self, validated_data):
        call_details_data = validated_data.pop("call_details", [])
        validated_data["user"] = self.context.get("request").user

        campaign = Campaign.objects.create(**validated_data)

        for call_detail in call_details_data:
            call_detail["campaign"] = campaign
            CallLog.objects.create(**call_detail)

        return campaign

    def update(self, instance, validated_data):
        call_details_data = validated_data.pop("call_details", [])
        campaign_type = validated_data.get("type", instance.type)
        agent_id = self.context.get("request").data.get("agent")
        instance.agent = Agent.objects.get(id=agent_id)

        instance = super().update(instance, validated_data)

        if call_details_data:
            CallLog.objects.filter(campaign=instance).delete()
            for call_detail in call_details_data:
                call_detail["campaign"] = instance
                CallLog.objects.create(**call_detail)

        return instance


