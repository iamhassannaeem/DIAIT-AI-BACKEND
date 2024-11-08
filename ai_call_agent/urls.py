from django.urls import path, include
from rest_framework import routers

from .views import (
    CampaignViewSet,
    CallDetailsViewSet,
    FeedbackReportViewSet,
    StopCampaignTaskView,
)
from .views import (
    TwilioNumbersViewSet,
    FileViewSet,
    InputDataView,
    AgentViewSet,
    FeedbackQuestionViewSet,
)

router = routers.DefaultRouter()

router.register(r"feedbackreport", FeedbackReportViewSet, basename="FeedbackReport")

router.register(r"campaigns", CampaignViewSet, basename="outbound-campaigns")
router.register(r"call/details", CallDetailsViewSet, basename="call-dtaeils")
path(
    "campaigns/stop/<int:campaign_id>/",
    StopCampaignTaskView.as_view(),
    name="stop-campaign-task",
),

router.register("agent", AgentViewSet, basename="agent")
router.register("agents/InputData", InputDataView, basename="InputData")


router.register("twillio_auth", TwilioNumbersViewSet, basename="twillio_auth")

router.register("library", FileViewSet, basename="library")

router.register(r"feedback-questions", FeedbackQuestionViewSet)

urlpatterns = [
    path(
        "library/download/<str:file_name>/",
        FileViewSet.as_view({"get": "download"}),
        name="file-download",
    ),
    path(
        "library/<int:pk>/",
        FileViewSet.as_view({"delete": "destroy"}),
        name="file-delete",
    ),
    path("", include(router.urls)),
    path(
        "agent/<str:agent_type>/<int:pk>/",
        AgentViewSet.as_view({"get": "retrieve"}),
        name="agent-retrieve",
    ),
]
