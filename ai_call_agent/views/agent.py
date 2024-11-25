from django.db.models import Max
from rest_framework import status, viewsets
from rest_framework.exceptions import NotFound
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ai_call_agent.models import (
    Agent,
    AIAudio,
    TwilioNumbers,
    File,
    Question,
    AgentFileMapping,
    Campaign,
    Industries,
)
from ai_call_agent.serializers import TwilioNumbersSerializer
from ai_call_agent.serializers.agent import (
    AgentSerializer,
    # AIModelSerializer,
    # AITecSerializer,
    AIAudioSerializer,
    File_agentSerializer,
    QuestionSerializer,
    AIIndustrySerializer,
)
from ai_call_agent.serializers.library_serilizer import AgentFileMappingSerializer


class InputDataView(viewsets.ViewSet):
    def list(self, request):
        user = request.user

        # ai_models = AIModel.objects.all()
        # ai_tecs = AITec.objects.all()
        industry = Industries.objects.all()
        ai_audio = AIAudio.objects.all()
        twilio_numbers = TwilioNumbers.objects.filter(user=user, status="active")
        user_files = File.objects.filter(user=user)

        # ai_model_data = AIModelSerializer(ai_models, many=True).data
        industry_data = AIIndustrySerializer(industry, many=True).data
        # ai_tec_data = AITecSerializer(ai_tecs, many=True).data
        ai_audio_data = AIAudioSerializer(ai_audio, many=True).data
        twilio_numbers_data = TwilioNumbersSerializer(twilio_numbers, many=True).data
        user_files_data = File_agentSerializer(user_files, many=True).data

        response_data = {
            "voices": ai_audio_data,
            "twilio_numbers": twilio_numbers_data,
            "files": user_files_data,
            "industry_data": industry_data,
        }

        return Response(response_data)


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

    def create(self, request, *args, **kwargs):
        agent_id = request.data.get("agent")
        if agent_id:
            try:
                agent = Agent.objects.get(id=agent_id)
                print(agent)
            except Agent.DoesNotExist:
                raise NotFound(detail="Agent not found.")
            max_order = Question.objects.filter(agent=agent).aggregate(Max("order"))[
                "order__max"
            ]
            new_order = (max_order or 0) + 1
            request.data["agent"] = agent.id
            request.data["order"] = new_order

        else:
            raise ValidationError(detail="Agent must be provided.")

        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        agent_id = request.data.get("agent")
        if agent_id:
            try:
                agent = Agent.objects.get(id=agent_id)
            except Agent.DoesNotExist:
                raise NotFound(detail="Agent not found.")

            request.data["agent"] = agent.id
        else:
            raise ValidationError(detail="Agent must be provided.")
        return super().update(request, *args, **kwargs)


class AgentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Agent.objects.all()
    serializer_class = AgentSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def get_object(self):
        pk = self.kwargs.get("pk")
        try:
            return Agent.objects.get(pk=pk, user=self.request.user)
        except Agent.DoesNotExist:
            raise NotFound("Agent not found")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        agent = self.get_object()
        questions = Question.objects.filter(agent=agent)
        questions_serializer = QuestionSerializer(questions, many=True)
        file_mappings = AgentFileMapping.objects.filter(agent_details=agent)
        file_serializer = AgentFileMappingSerializer(file_mappings, many=True)
        files_data = file_serializer.data
        for file_data in files_data:
            file_data.pop("agent_details", None)

        agent_serializer = AgentSerializer(agent)
        merged_data = agent_serializer.data
        merged_data["questions"] = questions_serializer.data
        merged_data["files"] = files_data
        return Response(merged_data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        agent = self.get_object()
        if Campaign.objects.filter(agent_id=agent.id).exists():
            return Response(
                {
                    "error": "This agent is affiliated with an active campaign. Status cannot be changed."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        files_data = request.data.get("files", [])
        current_file_types = {}
        for file_entry in files_data:
            file_type = file_entry.get("file_type")
            file_id = file_entry.get("file")
            if file_type and file_id:
                try:
                    file_instance = File.objects.get(id=file_id)
                except File.DoesNotExist:
                    return Response(
                        {"detail": "File not found."}, status=status.HTTP_404_NOT_FOUND
                    )
                if file_instance.user != request.user:
                    return Response(
                        {"detail": "File not associated with the current user."},
                        status=status.HTTP_403_FORBIDDEN,
                    )
                existing_mapping = AgentFileMapping.objects.filter(
                    agent_details=agent, file_type=file_type
                ).first()
                if existing_mapping:
                    existing_mapping.file = file_instance
                    existing_mapping.save()
                else:
                    AgentFileMapping.objects.create(
                        agent_details=agent,
                        file_type=file_type,
                        file=file_instance,
                    )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        agent = self.get_object()
        agent.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
