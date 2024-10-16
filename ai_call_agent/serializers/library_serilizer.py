
from rest_framework import serializers
from ai_call_agent.models import File

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['id', 'file_name', 'user']
        read_only_fields = ['user']
