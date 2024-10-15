from rest_framework import viewsets
from rest_framework.response import Response
from ai_call_agent.models import AgentDetails, TwilioNumbers
from ai_call_agent.serializers import AgentDetailsSerializer
from rest_framework.decorators import action
from rest_framework import status


class AgentDetailsViewSet(viewsets.ModelViewSet):
    queryset = AgentDetails.objects.all()
    serializer_class = AgentDetailsSerializer

    def create(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        return super().update(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def phone_numbers(self, request):
        user = request.user
        phone_numbers = TwilioNumbers.objects.filter(user=user)
        phone_numbers_list = [{"phone_number": number.phone_number, "account_sid": number.account_sid}
                              for number in phone_numbers]

        return Response(phone_numbers_list, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def select_phone_number(self, request, pk=None):
        agent_details = self.get_object()
        user = request.user
        phone_numbers = TwilioNumbers.objects.filter(user=user)

        if not phone_numbers.exists():
            return Response({'error': 'No phone numbers found for this user.'}, status=status.HTTP_404_NOT_FOUND)

        selected_phone_number = request.data.get('phone_number')
        if not phone_numbers.filter(phone_number=selected_phone_number).exists():
            return Response({'error': 'Phone number not found for the authenticated user.'},
                            status=status.HTTP_400_BAD_REQUEST)

        agent_details.phone_number = selected_phone_number
        agent_details.save()

        return Response({'status': 'Phone number selected successfully.'}, status=status.HTTP_200_OK)
