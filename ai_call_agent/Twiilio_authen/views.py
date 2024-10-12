
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from twilio.rest import Client
from authentication.models import TwilioNumbers
from .serializers import TwilioNumbersSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class TwilioNumbersViewSet(viewsets.ModelViewSet):
    serializer_class = TwilioNumbersSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return TwilioNumbers.objects.filter(user=user)

    def create(self, request, *args, **kwargs):
        account_sid = request.data.get('account_sid')
        auth_token = request.data.get('auth_token')
        phone_number = request.data.get('phone_number')

        if not account_sid or not auth_token or not phone_number:
            return Response({'error': 'All fields (account_sid, auth_token, phone_number) are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            client = Client(account_sid, auth_token)


            incoming_numbers = client.incoming_phone_numbers.list()
            number_exists = any(in_number.phone_number == phone_number for in_number in incoming_numbers)

            if not number_exists:
                return Response({'error': 'The phone number is not associated with this account.'}, status=status.HTTP_400_BAD_REQUEST)


            client.lookups.v1.phone_numbers(phone_number).fetch()

            if TwilioNumbers.objects.filter(user=request.user, phone_number=phone_number).exists():
                return Response({'error': 'Phone number already exists.'}, status=status.HTTP_400_BAD_REQUEST)

            twilio_number = TwilioNumbers(
                user=request.user,
                phone_number=phone_number,
                account_sid=account_sid,
                account_auth_token=auth_token,
                auth_token_label=request.user.name
            )
            twilio_number.save()

            return Response(TwilioNumbersSerializer(twilio_number).data, status=status.HTTP_201_CREATED)

        except Exception as e:
            if 'Authentication' in str(e):
                return Response({'error': 'Invalid Account SID or Auth Token.'}, status=status.HTTP_401_UNAUTHORIZED)
            elif 'Phone number' in str(e):
                return Response({'error': 'Invalid phone number.'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
