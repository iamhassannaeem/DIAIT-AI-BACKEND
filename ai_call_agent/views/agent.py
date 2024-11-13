from django.db.models import Max
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework import viewsets
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ai_call_agent.models import (
    FeedbackAgent,
    SalesAgent,
    AIAudio,
    AIModel,
    AITec,
    TwilioNumbers,
    File,
    Question,
    Campaign,
)
from ai_call_agent.serializers import (
    FeedbackAgentDetailsSerializer,
    SalesAgentDetailsSerializer,
    AIModelSerializer,
    AITecSerializer,
    AIAudioSerializer,
    Twilio_agentNumberSerializer,
    File_agentSerializer,
    QuestionSerializer,
)


class AgentViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request):
        agent_type = request.data.get("agent_type")

        if agent_type == "feedback":
            serializer = FeedbackAgentDetailsSerializer(
                data=request.data, context={"request": request}
            )
        elif agent_type == "sales":
            serializer = SalesAgentDetailsSerializer(
                data=request.data, context={"request": request}
            )
        else:
            return Response(
                {"error": "Invalid agent type specified."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if serializer.is_valid():
            agent = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None, agent_type=None):
        if agent_type == "feedback":
            agent = get_object_or_404(FeedbackAgent, pk=pk, user=request.user)
            serializer = FeedbackAgentDetailsSerializer(agent)
        elif agent_type == "sales":
            agent = get_object_or_404(SalesAgent, pk=pk, user=request.user)
            serializer = SalesAgentDetailsSerializer(agent)
        else:
            return Response(
                {"error": "Invalid agent type specified."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(serializer.data, status=status.HTTP_200_OK)

    def list(self, request):
        feedback_agents = FeedbackAgent.objects.filter(user=request.user).order_by(
            "created_date"
        )
        sales_agents = SalesAgent.objects.filter(user=request.user).order_by(
            "created_date"
        )

        feedback_data = FeedbackAgentDetailsSerializer(feedback_agents, many=True).data
        sales_data = SalesAgentDetailsSerializer(sales_agents, many=True).data

        for item in feedback_data:
            item["type"] = "feedback"

        for item in sales_data:
            item["type"] = "sales"

        return Response(
            {
                "feedback_agents": feedback_data,
                "sales_agents": sales_data,
            }
        )

    def update(self, request, pk=None):
        agent_type = request.data.get("agent_type")

        if agent_type == "feedback":
            agent = get_object_or_404(FeedbackAgent, pk=pk, user=request.user)
            if Campaign.objects.filter(feedback_agent=agent).exists():
                return Response(
                    {
                        "error": "This agent is affiliated with an active campaign. Status cannot be changed."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = FeedbackAgentDetailsSerializer(
                agent, data=request.data, context={"request": request}
            )

        elif agent_type == "sales":
            agent = get_object_or_404(SalesAgent, pk=pk, user=request.user)
            if Campaign.objects.filter(sales_agent=agent).exists():
                return Response(
                    {
                        "error": "This agent is affiliated with an active campaign. Status cannot be changed."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = SalesAgentDetailsSerializer(
                agent, data=request.data, context={"request": request}
            )
        else:
            return Response(
                {"error": "Invalid agent type specified."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        agent_type = request.data.get("agent_type")

        if agent_type == "feedback":
            agent = get_object_or_404(FeedbackAgent, pk=pk, user=request.user)
        elif agent_type == "sales":
            agent = get_object_or_404(SalesAgent, pk=pk, user=request.user)
        else:
            return Response(
                {"error": "Invalid agent type specified."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        agent.delete()
        return Response(
            {"message": "Agent deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )


class InputDataView(viewsets.ViewSet):
    def list(self, request):
        user = request.user

        ai_models = AIModel.objects.all()
        ai_tecs = AITec.objects.all()
        ai_audio = AIAudio.objects.all()
        twilio_numbers = TwilioNumbers.objects.filter(user=user, status="active")
        user_files = File.objects.filter(user=user)

        ai_model_data = AIModelSerializer(ai_models, many=True).data
        ai_tec_data = AITecSerializer(ai_tecs, many=True).data
        ai_audio_data = AIAudioSerializer(ai_audio, many=True).data
        twilio_numbers_data = Twilio_agentNumberSerializer(
            twilio_numbers, many=True
        ).data
        user_files_data = File_agentSerializer(user_files, many=True).data

        response_data = {
            "ai_models": ai_model_data,
            "ai_tecs": ai_tec_data,
            "voices": ai_audio_data,
            "twilio_numbers": twilio_numbers_data,
            "files": user_files_data,
        }

        return Response(response_data)


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

    def create(self, request, *args, **kwargs):
        feedback_agent_id = request.data.get("feedback_agent")
        sales_agent_id = request.data.get("sales_agent")

        if feedback_agent_id:
            try:
                feedback_agent = FeedbackAgent.objects.get(id=feedback_agent_id)
            except FeedbackAgent.DoesNotExist:
                raise NotFound(detail="FeedbackAgent not found.")

            max_order = Question.objects.filter(
                feedback_agent=feedback_agent
            ).aggregate(Max("order"))["order__max"]
            new_order = (max_order or 0) + 1

            request.data["feedback_agent"] = feedback_agent.id
            request.data["sales_agent"] = None
            request.data["order"] = new_order

        elif sales_agent_id:
            try:
                sales_agent = SalesAgent.objects.get(id=sales_agent_id)
            except SalesAgent.DoesNotExist:
                raise NotFound(detail="SalesAgent not found.")

            max_order = Question.objects.filter(sales_agent=sales_agent).aggregate(
                Max("order")
            )["order__max"]
            new_order = (max_order or 0) + 1

            request.data["sales_agent"] = sales_agent.id
            request.data["feedback_agent"] = None
            request.data["order"] = new_order

        else:
            raise ValidationError(
                detail="Either feedback_agent or sales_agent must be provided."
            )

        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        feedback_agent_id = request.data.get("feedback_agent")
        sales_agent_id = request.data.get("sales_agent")

        if feedback_agent_id:
            try:
                feedback_agent = FeedbackAgent.objects.get(id=feedback_agent_id)
            except FeedbackAgent.DoesNotExist:
                raise NotFound(detail="FeedbackAgent not found.")

            request.data["feedback_agent"] = feedback_agent.id
            request.data["sales_agent"] = None

        elif sales_agent_id:
            try:
                sales_agent = SalesAgent.objects.get(id=sales_agent_id)
            except SalesAgent.DoesNotExist:
                raise NotFound(detail="SalesAgent not found.")

            request.data["sales_agent"] = sales_agent.id
            request.data["feedback_agent"] = None

        else:
            raise ValidationError(
                detail="Either feedback_agent or sales_agent must be provided."
            )

        return super().update(request, *args, **kwargs)
