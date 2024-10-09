from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FeedBackAgentViewSet

router = DefaultRouter()
router.register(r'feedback', FeedBackAgentViewSet)  # Register the viewset with the router

urlpatterns = [
    path('', include(router.urls)),  # Include the router's URLs
]
