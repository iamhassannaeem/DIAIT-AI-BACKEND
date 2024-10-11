from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("user/", include("authentication.urls")),
    path('ai_call_agent/', include('ai_call_agent.urls')),
    path('twilio/', include('ai_call_agent.Twiilio_authen.urls')),
    path('Agent/', include('ai_call_agent.agent_creat.urls')),
    path('Feedback_Agent/', include('ai_call_agent.Feedback.urls')),
    path('Library/', include('ai_call_agent.Library.urls')),

]
