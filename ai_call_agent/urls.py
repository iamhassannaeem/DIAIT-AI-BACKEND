from rest_framework import routers
from .views import TwilioNumbersViewSet,FileViewSet,InputDataView,AgentViewSet
from .views import CampaignNumberListViewSet, OutboundCampaignViewSet
from django.urls import path, include

router = routers.DefaultRouter()

router.register(r'campaign-numbers', CampaignNumberListViewSet, basename='campaign-numbers')
router.register(r'outbound-campaigns', OutboundCampaignViewSet, basename='outbound-campaigns')

router.register("agent",AgentViewSet, basename="agent")
router.register("agents/InputData", InputDataView, basename="InputData")




router.register("twillio_auth", TwilioNumbersViewSet, basename="twillio_auth")

router.register("library",FileViewSet, basename="library")

urlpatterns = [
    path('library/download/<str:file_name>/', FileViewSet.as_view({'get': 'download'}), name='file-download'),
    path('library/<int:pk>/', FileViewSet.as_view({'delete': 'destroy'}), name='file-delete'),
    path('', include(router.urls)),
    path('agent/<str:agent_type>/<int:pk>/', AgentViewSet.as_view({'get': 'retrieve'}), name='agent-retrieve')
]

