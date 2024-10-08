from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .views import (
    register_view,
    LoginView,
    logout_view,
    reset_password_confirm_view,
    reset_password_view,
    reset_password_view_old,

    # login_view,
    # verify_code_view,
)

router = DefaultRouter()

urlpatterns = [
    path("register/", register_view, name="register"),
    path('login/', LoginView.as_view(), name='login'),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("logout/", logout_view, name="logout"),
    path(
        "reset-password-confirm/<uidb64>/<token>/",
        reset_password_confirm_view,
        name="reset_password_confirm",
    ),
    path("reset-password/", reset_password_view, name="reset_password"),
    path("reset-password_old/", reset_password_view_old, name="reset-password_old"),
    # path("login/", login_view, name="login"),
    # path("verify-code/", verify_code_view, name="verify_code"),
]

urlpatterns += router.urls
