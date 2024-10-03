from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/',admin.site.urls),
    path('aut/',include('authentication.url')),  # Include authentication URLs
]
