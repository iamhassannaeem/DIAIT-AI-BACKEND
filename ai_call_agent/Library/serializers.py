
from rest_framework import serializers
from ..models import File

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['id', 'file_name', 'user']  # Include 'user' if you want to allow users to set it
        read_only_fields = ['user']  # Make user read-only, set automatically
