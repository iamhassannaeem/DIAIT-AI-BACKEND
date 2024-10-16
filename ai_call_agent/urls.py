from rest_framework import routers
from .views import AgentDetailsViewSet,FeedbackViewSet,TwilioNumbersViewSet,FileViewSet


router = routers.DefaultRouter()

router.register("agent", AgentDetailsViewSet, basename="agent")
router.register("feedback", FeedbackViewSet, basename="feedback")
router.register("twillio_auth", TwilioNumbersViewSet, basename="twillio_auth")

router.register("library",FileViewSet, basename="library")


urlpatterns = router.urls
