from django.urls import path,include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from authentication.Twiilio_authen.view import verify_twilio
from .views import (
    register_view,
    LoginView,
    logout_view,
    reset_password_view_old,
    activate_view,
    Forgot_pwd_request_view,
    reset_password_view,
    get_all_users_view

)

router = DefaultRouter()

urlpatterns = [
    path("register/", register_view, name="register"),
    path('activate/<uidb64>/<token>/', activate_view, name='activate'),
    path('login/', LoginView.as_view(), name='login'),
    path('password_reset_request/',Forgot_pwd_request_view, name='password_reset_request'),
    path('reset_password/<uidb64>/<token>/', reset_password_view, name='reset_password'),

    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),

    path("logout/", logout_view, name="logout"),
    path('users/', get_all_users_view, name='users'),
    path("reset-password_old/", reset_password_view_old, name="reset-password_old"),



]

urlpatterns += router.urls
