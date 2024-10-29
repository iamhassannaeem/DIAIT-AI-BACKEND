from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("user/", include("authentication.urls")),
    path("agent/", include("ai_call_agent.urls")),
]
