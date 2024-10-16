
from rest_framework import serializers
from ai_call_agent.models import FeedBackAgent

class FeedBackAgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedBackAgent
        fields = ['feedback_id', 'user', 'questions']
