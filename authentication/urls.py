from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .views import (
    register_view,
    login_view,
    logout_view,
    reset_password_view_old,
    activate_view,
    Forgot_pwd_request_view,
    reset_password_view,
    get_all_users_view,
    resend_activation_email_view,
    verify_code_view

)

router = DefaultRouter()

urlpatterns = [
    path("register/", register_view, name="register"),
    path('activate/<str:token>/<str:uidb64>/', activate_view, name='activate'),
    path('request_new_activation/', resend_activation_email_view, name='request_new_activation'),
    path('login/',login_view, name='login'),
    path('verify-code/',verify_code_view, name='verify_code'),
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
