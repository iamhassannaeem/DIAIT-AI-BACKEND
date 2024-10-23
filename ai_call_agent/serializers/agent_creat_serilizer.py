from rest_framework import serializers
from ai_call_agent.models import FeedbackAgent, SalesAgent, File, AgentFileMapping, FeedbackQuestion
from ai_call_agent.models import AIModel, AITec, AIAudio, TwilioNumbers

class Twilio_agentNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TwilioNumbers
        fields = ['phone_number']

class File_agentSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['file_name']

class AIModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIModel
        fields = ['id', 'ai_model_provider']

class AIAudioSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIAudio
        fields = ['id', 'ai_audio_provider']

class AITecSerializer(serializers.ModelSerializer):
    class Meta:
        model = AITec
        fields = ['id', 'ai_tec_provider']

class FeedbackQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackQuestion
        fields = ['order', 'question_text']

class AgentFileMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentFileMapping
        fields = ['file']

class FeedbackAgentDetailsSerializer(serializers.ModelSerializer):
    feed_questions = FeedbackQuestionSerializer(many=True, required=False)

    class Meta:
        model = FeedbackAgent
        fields = '__all__'
        extra_kwargs = {'user': {'read_only': True}}

    def create(self, validated_data):
        feed_questions_data = validated_data.pop('feed_questions', [])
        user = self.context['request'].user
        feedback_agent = FeedbackAgent.objects.create(user=user, **validated_data)
        for question_data in feed_questions_data:
            FeedbackQuestion.objects.create(feedback_agent=feedback_agent, **question_data)
        return feedback_agent

    def update(self, instance, validated_data):
        feed_questions_data = validated_data.pop('feed_questions', [])
        user = self.context['request'].user
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.user = user
        instance.save()
        if feed_questions_data:
            instance.feed_questions.all().delete()
            for question_data in feed_questions_data:
                FeedbackQuestion.objects.create(feedback_agent=instance, **question_data)
        return instance

class SalesAgentDetailsSerializer(serializers.ModelSerializer):
    prompt_files = serializers.ListField(write_only=True, required=False)

    class Meta:
        model = SalesAgent
        fields = '__all__'
        extra_kwargs = {'user': {'read_only': True}}

    def create(self, validated_data):
        prompt_files_data = validated_data.pop('prompt_files', [])
        user = self.context['request'].user
        sales_agent = SalesAgent.objects.create(user=user, **validated_data)
        if not prompt_files_data:
            sales_agent.prompt_files = None
            sales_agent.save()
        for file_id in prompt_files_data:
            try:
                file_instance = File.objects.get(id=file_id)
                AgentFileMapping.objects.create(agent_details=sales_agent, file=file_instance)
            except File.DoesNotExist:
                raise serializers.ValidationError(f"File with id {file_id} does not exist.")
        return sales_agent

    def update(self, instance, validated_data):
        prompt_files_data = validated_data.pop('prompt_files', [])
        user = self.context['request'].user
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.user = user
        instance.save()
        if prompt_files_data:
            AgentFileMapping.objects.filter(agent_details=instance).delete()
            for file_id in prompt_files_data:
                try:
                    file_instance = File.objects.get(id=file_id)
                    AgentFileMapping.objects.create(agent_details=instance, file=file_instance)
                except File.DoesNotExist:
                    raise serializers.ValidationError(f"File with id {file_id} does not exist.")
        return instance
