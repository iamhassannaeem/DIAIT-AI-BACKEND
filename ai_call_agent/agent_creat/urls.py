# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AgentDetailsViewSet

router = DefaultRouter()
router.register(r'agent-details', AgentDetailsViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
