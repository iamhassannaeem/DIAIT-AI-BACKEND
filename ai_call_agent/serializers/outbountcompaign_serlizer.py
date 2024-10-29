from rest_framework import serializers
from ai_call_agent.models import (
    OutboundCampaign,
    CampaignNumberList,
    FeedbackAgent,
    FeedbackQuestion,
)
from ai_call_agent.serializers import TwilioNumbersSerializer
from .agent_creat_serilizer import AIModelSerializer, AITecSerializer, AIAudioSerializer


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
    number_list = CampaignNumberListSerializer(many=True, read_only=True)
    number_list_ids = serializers.PrimaryKeyRelatedField(
        queryset=CampaignNumberList.objects.all(),
        many=True,
        write_only=True,
        required=False,
    )
    feedback_agent = FeedbackAgentSerializer()

    twilio_number_details = serializers.SerializerMethodField()

    class Meta:
        model = OutboundCampaign
        fields = [
            "id",
            "name",
            "feedback_agent",
            "start_time",
            "end_time",
            "time_zone",
            "status",
            "number_list",
            "number_list_ids",
            "twilio_number_details",
        ]

    def get_twilio_number_details(self, obj):

        if obj.feedback_agent and obj.feedback_agent.twillio_number:
            try:
                twilio_number = TwilioNumbersSerializer(
                    obj.feedback_agent.twillio_number
                )
                return twilio_number.data
            except Exception as e:
                return {"error": str(e)}
        return None

    def create(self, validated_data):
        feedback_agent_data = validated_data.pop("feedback_agent", None)
        number_list_ids = validated_data.pop("number_list_ids", [])

        campaign = OutboundCampaign.objects.create(**validated_data)

        if feedback_agent_data:
            feedback_agent = FeedbackAgent.objects.create(**feedback_agent_data)
            campaign.feedback_agent = feedback_agent

        campaign.number_list.set(number_list_ids)
        return campaign

    def update(self, instance, validated_data):
        feedback_agent_data = validated_data.pop("feedback_agent", None)
        number_list_ids = validated_data.pop("number_list_ids", [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if feedback_agent_data:
            for attr, value in feedback_agent_data.items():
                setattr(instance.feedback_agent, attr, value)
            instance.feedback_agent.save()

        instance.number_list.set(number_list_ids)
        instance.save()
        return instance
