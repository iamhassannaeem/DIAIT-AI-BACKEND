from django.contrib.auth import get_user_model
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from twilio.base.exceptions import TwilioException
from twilio.rest import Client

from ai_call_agent.models import TwilioNumbers
from ai_call_agent.serializers import TwilioNumbersSerializer

User = get_user_model()


class TwilioNumbersViewSet(viewsets.ModelViewSet):
    serializer_class = TwilioNumbersSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return TwilioNumbers.objects.filter(user=user)

    def create(self, request, *args, **kwargs):
        account_sid = request.data.get("account_sid")
        auth_token = request.data.get("auth_token")
        phone_number = request.data.get("phone_number")
        user_iden_name = request.data.get("name")

        if not account_sid or not auth_token or not phone_number:
            missing_fields = []
            if not account_sid:
                missing_fields.append("Account SID")
            if not auth_token:
                missing_fields.append("Authentication Token")
            if not phone_number:
                missing_fields.append("Phone Number")

            error_message = f"The following fields are required: {', '.join(missing_fields)}. Please provide the missing information."
            return Response(
                {"error": error_message}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            client = Client(account_sid, auth_token)
            client.api.accounts(account_sid).fetch()
        except TwilioException as e:
            error_message = str(e)
            formatted_message = "Invalid credentials. Please check your account SID and authentication token."
            if "Authentication Error" in error_message:
                formatted_message = "Credentials are not valid. Please check your account SID and auth token."
            return Response(
                {"error": formatted_message}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            incoming_numbers = client.incoming_phone_numbers.list()
            number_exists = any(
                in_number.phone_number == phone_number for in_number in incoming_numbers
            )

            if not number_exists:
                return Response(
                    {"error": "The phone number is not associated with this account."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            client.lookups.v1.phone_numbers(phone_number).fetch()

        except TwilioException as e:
            return Response(
                {"error": "Unable to fetch phone number details: " + str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if TwilioNumbers.objects.filter(
            user=request.user, phone_number=phone_number
        ).exists():
            return Response(
                {"error": "Phone number already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        twilio_number = TwilioNumbers(
            user=request.user,
            phone_number=phone_number,
            account_sid=account_sid,
            account_auth_token=auth_token,
            auth_token_label=user_iden_name,
            status="active",
        )
        twilio_number.save()

        return Response(
            TwilioNumbersSerializer(twilio_number).data, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["patch"])
    def update_status(self, request, pk=None):
        try:
            twilio_number = self.get_object()
            new_status = request.data.get("status")

            if new_status not in ["active", "inactive"]:
                return Response(
                    {"error": 'Invalid status value. Must be "active" or "inactive".'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            twilio_number.status = new_status
            twilio_number.save()
            return Response(
                {"status": f"Status updated to {new_status}"}, status=status.HTTP_200_OK
            )
        except TwilioNumbers.DoesNotExist:
            return Response(
                {"error": "Twilio number not found"}, status=status.HTTP_404_NOT_FOUND
            )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        response_data = []

        for twilio_number in queryset:
            response_data.append(
                {
                    "id": twilio_number.id,
                    "user": twilio_number.user.id,
                    "phone_number": twilio_number.phone_number,
                    "auth_token_label": twilio_number.auth_token_label,
                    "status": twilio_number.status,
                     "created_date": twilio_number.created_date.isoformat() + "Z" if twilio_number.created_date else None,
                    "usage_count": twilio_number.usage_count,
                }
            )

        return Response(response_data, status=status.HTTP_200_OK)
