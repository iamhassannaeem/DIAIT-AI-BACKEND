
from rest_framework import serializers
from ..models import FeedBackAgent

class FeedBackAgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedBackAgent
        fields = ['feedback_id', 'user', 'questions']
