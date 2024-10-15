
from rest_framework import serializers
from ai_call_agent.models import AgentDetails

class AgentDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentDetails
        fields = '__all__'
