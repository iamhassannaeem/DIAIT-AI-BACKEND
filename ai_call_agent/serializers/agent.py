from rest_framework import serializers, status
from rest_framework.response import Response

from ai_call_agent.models import AITec, AIAudio, AIModel, Campaign, Industries
from ai_call_agent.models import Agent, File, Question, AgentFileMapping


class File_agentSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ["id", "file_name", "file_type"]

    def get_file_type(self, obj):
        agent_file_mapping = AgentFileMapping.objects.filter(file=obj).first()
        return (
            agent_file_mapping.get_file_type_display() if agent_file_mapping else None
        )


class AIModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIModel
        fields = ["id", "ai_model_provider"]


class AIAudioSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIAudio
        fields = ["id", "ai_audio_provider"]


class AITecSerializer(serializers.ModelSerializer):
    class Meta:
        model = AITec
        fields = ["id", "ai_tec_provider"]


class AIIndustrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Industries
        fields = ["id", "interest"]


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "order", "question_text", "status", "agent"]


class AgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = "__all__"
        extra_kwargs = {"user": {"read_only": True}}

    def _create_mappings(self, agent, file_data):
        for file_entry in file_data:
            file_type = file_entry.get("file_type")
            file_id = file_entry.get("file")
            if file_type and file_id:
                file_instance = File.objects.get(id=file_id)
                AgentFileMapping.objects.create(
                    agent_details=agent, file=file_instance, file_type=file_type
                )

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["user"] = request.user

        questions_data = validated_data.pop("questions", [])
        files_data = validated_data.pop("files", [])
        agent = Agent.objects.create(**validated_data)

        self._create_mappings(agent, files_data)

        for question_data in questions_data:
            Question.objects.create(agent=agent, **question_data)

        return agent

    def update(self, instance, validated_data):
        if Campaign.objects.filter(agent_id=instance.id).exists():
            return Response(
                {
                    "error": "This agent is affiliated with an active campaign. Status cannot be changed."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        questions_data = validated_data.pop("questions", [])
        files_data = validated_data.pop("files", [])
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["user"] = request.user
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if questions_data:
            instance.questions.all().delete()
            for question_data in questions_data:
                Question.objects.create(agent=instance, **question_data)
        if files_data:
            AgentFileMapping.objects.filter(agent_details=instance).delete()
            self._create_mappings(instance, files_data)

        return instance
