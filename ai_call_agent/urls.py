from django.urls import path, include
from rest_framework import routers

from .views import (
    CampaignViewSet,
    CallDetailsViewSet,
    FeedbackReportViewSet,
    UserPaymentViewSet,
)
from .views import (
    TwilioNumbersViewSet,
    FileViewSet,
    InputDataView,
    AgentViewSet,
    QuestionViewSet,
)
from .views.compaign import StopCampaignTaskViewSet

router = routers.DefaultRouter()

router.register(r"feedbackreport", FeedbackReportViewSet, basename="FeedbackReport")

router.register(r"campaigns", CampaignViewSet, basename="outbound-campaigns")


router.register(r"call/details", CallDetailsViewSet, basename="call-dtaeils")
router.register(r"stopcampaigns", StopCampaignTaskViewSet, basename="campaigns")

router.register("agent", AgentViewSet, basename="agent")
router.register("agents/InputData", InputDataView, basename="InputData")


router.register("twillio_auth", TwilioNumbersViewSet, basename="twillio_auth")

router.register("library", FileViewSet, basename="library")

router.register(r"feedback-questions", QuestionViewSet)

router.register(r"payments", UserPaymentViewSet, basename="user-payment")

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
    # path("payment/", ai_call_agent.views.payment, name="payment"),  # Payment form
    # path(
    #     "process_payment/", ai_call_agent.views.process_payment, name="process_payment"
    # ),
]
