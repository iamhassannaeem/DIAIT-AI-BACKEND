from rest_framework import serializers
from ai_call_agent.models import (
    FeedbackAgent,
    SalesAgent,
    File,
    AgentFileMapping,
    FeedbackQuestion,
)
from ai_call_agent.models import AIModel, AITec, AIAudio, TwilioNumbers


class Twilio_agentNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TwilioNumbers
        fields = ["id", "phone_number"]


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


class FeedbackQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackQuestion
        fields = ["order", "question_text"]


class AgentFileMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentFileMapping
        fields = ["file"]


class FeedbackAgentDetailsSerializer(serializers.ModelSerializer):
    feed_questions = FeedbackQuestionSerializer(many=True, required=False)

    class Meta:
        model = FeedbackAgent
        fields = "__all__"
        extra_kwargs = {"user": {"read_only": True}}

    def create(self, validated_data):
        feed_questions_data = validated_data.pop("feed_questions", [])
        user = self.context["request"].user
        feedback_agent = FeedbackAgent.objects.create(user=user, **validated_data)
        for question_data in feed_questions_data:
            FeedbackQuestion.objects.create(
                feedback_agent=feedback_agent, **question_data
            )
        return feedback_agent

    def update(self, instance, validated_data):
        feed_questions_data = validated_data.pop("feed_questions", [])
        user = self.context["request"].user
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.user = user
        instance.save()
        if feed_questions_data:
            instance.feed_questions.all().delete()
            for question_data in feed_questions_data:
                FeedbackQuestion.objects.create(
                    feedback_agent=instance, **question_data
                )
        return instance


class SalesAgentDetailsSerializer(serializers.ModelSerializer):
    files = serializers.ListField(child=serializers.DictField(), required=False)
    associated_files = serializers.SerializerMethodField()

    class Meta:
        model = SalesAgent
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
        user = self.context["request"].user
        files_data = validated_data.pop("files", [])
        sales_agent = SalesAgent.objects.create(user=user, **validated_data)
        self._create_mappings(sales_agent, files_data)
        return sales_agent

    def update(self, instance, validated_data):
        user = self.context["request"].user
        files_data = validated_data.pop("files", [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if "user" in validated_data:
            instance.user = user

        instance.save()

        existing_mappings = list(
            AgentFileMapping.objects.filter(agent_details=instance)
        )

        #
        current_file_types = {
            mapping.file_type: mapping for mapping in existing_mappings
        }

        for file_entry in files_data:
            file_type = file_entry.get("file_type")
            file_id = file_entry.get("file")

            if file_type and file_id:

                file_instance = File.objects.get(id=file_id)

                if file_type in current_file_types:

                    current_file_types[file_type].file = file_instance
                    current_file_types[file_type].save()
                else:

                    AgentFileMapping.objects.create(
                        agent_details=instance, file_type=file_type, file=file_instance
                    )

        return instance

    def get_associated_files(self, obj):
        mappings = AgentFileMapping.objects.filter(agent_details=obj)
        return [
            {
                "file_name": mapping.file.file_name,
                "file_type": mapping.file_type,
            }
            for mapping in mappings
        ]


# class SalesAgentDetailsSerializer(serializers.ModelSerializer):
#     files = serializers.ListField(
#         child=serializers.DictField(),
#         required=False
#     )
#
#     class Meta:
#         model = SalesAgent
#         fields = '__all__'
#         extra_kwargs = {'user': {'read_only': True}}
#
#     def _create_mappings(self, agent, file_data):
#
#         for file_entry in file_data:
#             file_type = file_entry.get('file_type')
#             file_id = file_entry.get('file')
#             if file_type and file_id:
#                 file_instance = File.objects.get(id=file_id)
#                 AgentFileMapping.objects.create(
#                     agent_details=agent,
#                     file=file_instance,
#                     file_type=file_type
#                 )
#
#     def create(self, validated_data):
#         user = self.context['request'].user
#         files_data = validated_data.pop('files', [])
#
#
#         sales_agent = SalesAgent.objects.create(user=user, **validated_data)
#
#
#         self._create_mappings(sales_agent, files_data)
#
#         return sales_agent
#
#     def update(self, instance, validated_data):
#         user = self.context['request'].user
#         files_data = validated_data.pop('files', [])
#
#
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.user = user
#         instance.save()
#
#
#         AgentFileMapping.objects.filter(agent_details=instance).delete()
#
#
#         self._create_mappings(instance, files_data)
#
#         return instance
