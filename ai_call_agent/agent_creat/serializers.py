# serializers.py
from rest_framework import serializers
from ..models import AgentDetails

class AgentDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentDetails
        fields = '__all__'  # Or specify the fields you want to include
