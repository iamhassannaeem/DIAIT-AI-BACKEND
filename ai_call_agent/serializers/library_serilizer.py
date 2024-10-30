from rest_framework import serializers
from ai_call_agent.models import File, FeedbackAgent, AgentFileMapping, SalesAgent


class AgentDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesAgent
        fields = ["name", "active"]


class AgentFileMappingSerializer(serializers.ModelSerializer):
    agent_details = AgentDetailsSerializer()

    class Meta:
        model = AgentFileMapping
        fields = ["file", "agent_details"]


class FileSerializer(serializers.ModelSerializer):
    agent_details = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = [
            "id",
            "file_name",
            "file_type",
            "request_id",
            "file_size",
            "content_type",
            "last_modified",
            "created_date",
            "agent_details",
        ]

    def get_agent_details(self, obj):
        agent_mappings = obj.agentfilemapping_set.all()

        unique_mappings = {}
        for mapping in agent_mappings:
            key = (mapping.file_id, mapping.agent_details.id)
            if key not in unique_mappings:
                unique_mappings[key] = mapping

        return AgentFileMappingSerializer(unique_mappings.values(), many=True).data
