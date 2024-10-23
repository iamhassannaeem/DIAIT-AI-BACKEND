from rest_framework import routers
from .views import TwilioNumbersViewSet,FileViewSet,InputDataView,AgentViewSet

from django.urls import path, include

router = routers.DefaultRouter()

router.register("agent",AgentViewSet, basename="agent")
router.register("agents/InputData", InputDataView, basename="InputData")




router.register("twillio_auth", TwilioNumbersViewSet, basename="twillio_auth")

router.register("library",FileViewSet, basename="library")

urlpatterns = [
    path('library/download/<str:file_name>/', FileViewSet.as_view({'get': 'download'}), name='file-download'),
    path('library/<int:pk>/', FileViewSet.as_view({'delete': 'destroy'}), name='file-delete'),
    path('', include(router.urls)),
]

