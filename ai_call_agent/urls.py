from django.urls import path, include
from rest_framework import routers

# from .views import (
#     CampaignViewSet,
#     CallDetailsViewSet,
#     FeedbackReportViewSet,
# )
from .views import (
    TwilioNumbersViewSet,
    FileViewSet,
    InputDataView,
    AgentViewSet,
    QuestionViewSet,
    CampaignViewSet,
    CallLogViewSet,
    StopCampaignTaskViewSet,
    CallLogContentView,
    ContactViewSet,
)

router = routers.DefaultRouter()

router.register(r"campaigns", CampaignViewSet, basename="outbound-campaigns")
router.register(r"call/logs", CallLogViewSet, basename="call-dtaeils")
router.register(r"stopcampaigns", StopCampaignTaskViewSet, basename="campaigns")
router.register(r"contacts", ContactViewSet)

router.register("agent", AgentViewSet, basename="agent")
router.register("agents/InputData", InputDataView, basename="InputData")


router.register("twillio_auth", TwilioNumbersViewSet, basename="twillio_auth")

router.register("library", FileViewSet, basename="library")

router.register(r"questions", QuestionViewSet)

# router.register(r"payments", UserPaymentViewSet, basename="user-payment")

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
    path(
        "library/replace/<int:pk>/",
        FileViewSet.as_view({"put": "replace_file"}),
        name="file-replace",
    ),
    path("", include(router.urls)),
    path(
        "call/contentlogs/",
        CallLogContentView.as_view(),
        name="calllog_combined_list",
    ),
    path(
        "call/contentlogs/<int:pk>/",
        CallLogContentView.as_view(),
        name="calllog_combined_detail",
    ),
]
