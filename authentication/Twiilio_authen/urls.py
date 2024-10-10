# authentication/Twiilio_authen/urls.py

from django.urls import path
from .view import verify_twilio,list_twilio_numbers

urlpatterns = [
    path('verify_number/', verify_twilio, name='verify_twilio'),
    path('list_twilio_numbers/<int:user_id>/', list_twilio_numbers, name='list_twilio_numbers'),
]
