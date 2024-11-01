from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)

from .views import (
    register_view,
    login_view,
    reset_password_view_old,
    activate_view,
    forgot_pwd_request_view,
    reset_password_view,
    resend_activation_email_view,
    verify_code_view,
)

router = DefaultRouter()

urlpatterns = [
    path("register/", register_view, name="register"),
    path("activate/<str:token>/", activate_view, name="activate"),
    path(
        "request_new_activation/",
        resend_activation_email_view,
        name="request_new_activation",
    ),
    path("login/", login_view, name="login"),
    path("verify/code/", verify_code_view, name="verify_code"),
    path(
        "password_reset_request/",
        forgot_pwd_request_view,
        name="password_reset_request",
    ),
    path("forgot/password/<str:token>/", reset_password_view, name="forgot/password/"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("reset/password/", reset_password_view_old, name="reset-password_old"),
    path("logout/", TokenBlacklistView.as_view(), name="token_blacklist"),
]

urlpatterns += router.urls
