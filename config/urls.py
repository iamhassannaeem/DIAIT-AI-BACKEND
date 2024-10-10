from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("user/", include("authentication.urls")),
    path('ai_call_agent/', include('ai_call_agent.urls')),
    path('twilio/', include('authentication.Twiilio_authen.urls')),
    path('Agent/', include('ai_call_agent.agent_creat.urls')),

]
