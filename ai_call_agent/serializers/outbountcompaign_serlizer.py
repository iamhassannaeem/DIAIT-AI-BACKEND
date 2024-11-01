from rest_framework import serializers

from ai_call_agent.models import (
    OutboundCampaign,
    FeedbackAgent,
    CampaignNumberList,
    FeedbackQuestion,
    CallDetails,
)
from .agent import AIModelSerializer, AITecSerializer, AIAudioSerializer
from .twillio_auth_serilizer import TwilioNumbersSerializer


class FeedbackQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackQuestion
        fields = ["id", "order", "question_text"]


class FeedbackAgentSerializer(serializers.ModelSerializer):
    feed_questions = FeedbackQuestionSerializer(many=True, read_only=True)
    ai_model_details = AIModelSerializer(source="ai_model", read_only=True)
    ai_tec_details = AITecSerializer(source="ai_tec", read_only=True)
    voice_name_details = AIAudioSerializer(source="voice_name", read_only=True)

    tts_technology_provider_details = AITecSerializer(
        source="tts_technology_provider", read_only=True
    )
    stt_technology_provider_details = AITecSerializer(
        source="stt_technology_provider", read_only=True
    )

    class Meta:
        model = FeedbackAgent
        fields = [
            "id",
            "first_message",
            "name",
            "active",
            "gender",
            "created_date",
            "user",
            "tts_technology_provider_details",
            "stt_technology_provider_details",
            "feed_questions",
            "ai_model_details",
            "ai_tec_details",
            "voice_name_details",
        ]


class CampaignNumberListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignNumberList
        fields = ["id", "phone_number", "created_at"]


class OutboundCampaignSerializer(serializers.ModelSerializer):
    feedback_agent = serializers.PrimaryKeyRelatedField(
        queryset=FeedbackAgent.objects.all()
    )
    feedback_agent_details = FeedbackAgentSerializer(
        source="feedback_agent", read_only=True
    )
    phone_numbers = serializers.ListField(
        child=serializers.CharField(max_length=15), write_only=True
    )
    campaign_numbers = serializers.SerializerMethodField()
    twilio_number_details = serializers.SerializerMethodField()

    class Meta:
        model = OutboundCampaign
        fields = [
            "id",
            "name",
            "feedback_agent",
            "feedback_agent_details",
            "start_time",
            "end_time",
            "time_zone",
            "status",
            "phone_numbers",
            "campaign_numbers",
            "twilio_number_details",  #
        ]

    def get_campaign_numbers(self, obj):
        return CampaignNumberListSerializer(obj.campaign_numbers.all(), many=True).data

    def get_twilio_number_details(self, obj):

        if obj.feedback_agent and obj.feedback_agent.twillio_number:
            try:

                twilio_number = obj.feedback_agent.twillio_number
                return TwilioNumbersSerializer(twilio_number).data
            except Exception as e:
                return {"error": str(e)}
        return None

    def create(self, validated_data):
        phone_numbers = validated_data.pop("phone_numbers")
        campaign = OutboundCampaign.objects.create(**validated_data)

        for phone in phone_numbers:
            CampaignNumberList.objects.create(
                phone_number=phone, outbound_campaign=campaign
            )

        return campaign

    def update(self, instance, validated_data):
        phone_numbers = validated_data.pop("phone_numbers", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if phone_numbers is not None:

            instance.campaign_numbers.all().delete()
            for phone in phone_numbers:
                CampaignNumberList.objects.create(
                    phone_number=phone, outbound_campaign=instance
                )

        instance.save()
        return instance


class CallDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallDetails
        fields = [
            "id",
            "campaign_number",
            "call_duration",
            "conversation",
            "ended_reason",
            "status",
            "type",
            "call_id",
            "call_cost",
            "assistant",
            "customer",
        ]
