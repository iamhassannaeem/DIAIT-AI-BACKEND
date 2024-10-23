# serializers.py
from rest_framework import serializers
from ai_call_agent.models import File, FeedbackAgent, AgentFileMapping,SalesAgent


class AgentDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesAgent
        fields = ['name', 'active']


class AgentFileMappingSerializer(serializers.ModelSerializer):
    agent_details = AgentDetailsSerializer()

    class Meta:
        model = AgentFileMapping
        fields = ['agent_details']


class FileSerializer(serializers.ModelSerializer):

    agent_details = AgentFileMappingSerializer(many=True, source='agentfilemapping_set',required=False)

    class Meta:
        model = File
        fields = ['id', 'file_name', 'file_type', 'request_id', 'file_size', 'content_type', 'last_modified', 'created_date', 'agent_details']
