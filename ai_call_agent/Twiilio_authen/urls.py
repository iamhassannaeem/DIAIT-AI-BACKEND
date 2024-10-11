
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TwilioNumbersViewSet

router = DefaultRouter()
router.register(r'twilio_numbers', TwilioNumbersViewSet, basename='twilio_numbers')

urlpatterns = [
    path('', include(router.urls)),
]
