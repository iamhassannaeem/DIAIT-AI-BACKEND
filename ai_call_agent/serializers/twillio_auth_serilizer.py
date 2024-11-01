from rest_framework import serializers

from ai_call_agent.models import TwilioNumbers


class TwilioNumbersSerializer(serializers.ModelSerializer):
    class Meta:
        model = TwilioNumbers
        fields = [
            "id",
            "user",
            "phone_number",
            "account_sid",
            "account_auth_token",
            "auth_token_label",
            "status",
            "created_date",
            "usage_count",
            "account_api_secret",
            "account_api_sid",
        ]
