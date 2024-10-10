from django.urls import path
from .views import add_agent_details, success_view,select_phone_number

urlpatterns = [
    path('add_agent_details/<int:user_id>/', add_agent_details, name='add_agent_details'),
    path('success/', success_view, name='success'),
    path('select_phone_number/<int:agent_id>/', select_phone_number, name='select_phone_number'),

]
