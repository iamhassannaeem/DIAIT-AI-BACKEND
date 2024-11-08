from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
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
    FeedbackQuestion,
)
from ai_call_agent.serializers import (
    FeedbackAgentDetailsSerializer,
    SalesAgentDetailsSerializer,
    AIModelSerializer,
    AITecSerializer,
    AIAudioSerializer,
    Twilio_agentNumberSerializer,
    File_agentSerializer,
    FeedbackQuestionSerializer,
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
            feed_questions_data = request.data.get("feed_questions", [])

            feed_question_ids = [
                question.get("id")
                for question in feed_questions_data
                if question.get("id")
            ]
            for feed_question_id in feed_question_ids:
                feed_question = get_object_or_404(FeedbackQuestion, pk=feed_question_id)
                for question_data in feed_questions_data:
                    if question_data.get("id") == feed_question_id:
                        feed_question.question_text = question_data.get(
                            "question_text", feed_question.question_text
                        )

                        feed_question.save()
            agent = get_object_or_404(FeedbackAgent, pk=pk, user=request.user)
            serializer = FeedbackAgentDetailsSerializer(
                agent, data=request.data, context={"request": request}
            )
        elif agent_type == "sales":
            agent = get_object_or_404(SalesAgent, pk=pk, user=request.user)
            serializer = SalesAgentDetailsSerializer(
                agent, data=request.data, context={"request": request}
            )
        else:
            return Response(
                {"error": "Invalid agent type specified."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if serializer.is_valid():
            agent = serializer.save()
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

        # Query data
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


class FeedbackQuestionViewSet(viewsets.ModelViewSet):
    queryset = FeedbackQuestion.objects.all()
    serializer_class = FeedbackQuestionSerializer
