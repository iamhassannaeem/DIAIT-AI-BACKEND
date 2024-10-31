import random
from datetime import timedelta

import jwt
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import make_password
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.tokens import UntypedToken

from .models import User
from .serializers import LoginSerializer
from .serializers import (
    RegistrationSerializer,
    UpdateTrustedStatusSerializer,
)
from .utils import send_email

User = get_user_model()


@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    if User.objects.filter(email=serializer.validated_data["email"]).exists():
        return Response(
            {"message": "Email already exists. Please use a different email."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = User.objects.create_user(
        email=serializer.validated_data["email"],
        name=serializer.validated_data["name"],
        password=serializer.validated_data["password"],
    )
    user.is_active = False
    user.save()

    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    send_verification_email(request, user, access_token)

    response_data = {
        "message": "Registration successful. Check your email to activate your account.",
        "access_token": access_token,
        "refresh_token": str(refresh),
    }
    return Response(response_data, status=status.HTTP_201_CREATED)


def send_verification_email(request, user, access_token):
    current_site = get_current_site(request)
    mail_subject = "Activate your account."
    activation_url = f"http://{current_site.domain}/user/activate/{access_token}/"

    message = (
        f"Hi {user.name},\n\n"
        f"Please activate your account by clicking the link below:\n"
        f"{activation_url}\n\n"
        "Thank you!"
    )

    send_email(subject=mail_subject, message=message, recipient_list=[user.email])


@api_view(["POST"])
@permission_classes([AllowAny])
def activate_view(request, token):
    try:
        payload = UntypedToken(token)
        user_id = payload.get("user_id")

        if not user_id:
            return Response(
                {"error": "Invalid token payload."}, status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.get(id=user_id)

        if user.is_email_verified:
            return Response(
                {"message": "Your account is already activated."},
                status=status.HTTP_200_OK,
            )

        user.is_email_verified = True
        user.is_active = True
        user.save()

        return Response(
            {"message": "Your account has been activated."}, status=status.HTTP_200_OK
        )

    except TokenError:
        return Response(
            {"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST
        )
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
@permission_classes([AllowAny])
def resend_activation_email_view(request):
    email = request.data.get("email")

    if not email:
        return Response(
            {"error": "Email not provided."}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email=email)

        if user.is_active:
            return Response(
                {"message": "Your account is already activated."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        send_verification_email(request, user, access_token)

        return Response(
            {
                "message": "Verification email has been resent. Check your inbox.",
                "access_token": access_token,
            },
            status=status.HTTP_200_OK,
        )

    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)


def send_password_reset_email(user, request):
    token = RefreshToken.for_user(user).access_token
    current_site = get_current_site(request)
    reset_url = f"http://{current_site.domain}/user/forgot/password/{token}/"
    mail_subject = "Reset your password."
    message = (
        f"Hi {user.name},\n\nClick the link below to reset your password:\n{reset_url}"
    )
    send_email(mail_subject, message, [user.email])


@api_view(["POST"])
@permission_classes([AllowAny])
def forgot_pwd_request_view(request):
    email = request.data.get("email")

    try:
        user = User.objects.get(email=email)

        send_password_reset_email(user, request)
        return Response(
            {"message": "Password reset link has been sent to your email."},
            status=status.HTTP_200_OK,
        )
    except User.DoesNotExist:
        return Response(
            {"error": "User with this email does not exist."},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password_view(request, token):
    new_password = request.data.get("new_password")
    if not token or not new_password:
        return Response(
            {"error": "Token and new password must be provided."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        payload = UntypedToken(token)
        user_id = payload.get("user_id")
        user = User.objects.get(id=user_id)

        if user:
            user.set_password(new_password)
            user.save()
            return Response(
                {"message": "Your password has been reset successfully."},
                status=status.HTTP_200_OK,
            )
    except jwt.ExpiredSignatureError:
        return Response(
            {"error": "This reset link has expired."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except (jwt.DecodeError, User.DoesNotExist):
        return Response(
            {"error": "Invalid token."},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reset_password_view_old(request):
    old_password = request.data.get("old_password")
    new_password = request.data.get("new_password")

    if not old_password or not new_password:
        return Response(
            {"error": "Both old and new passwords are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = request.user

    if not user.check_password(old_password):
        return Response(
            {"error": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST
        )

    user.password = make_password(new_password)
    user.save()
    update_session_auth_hash(request, user)

    return Response(
        {"message": "Password has been reset successfully."}, status=status.HTTP_200_OK
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data["email"]
    password = serializer.validated_data["password"]
    is_trusted = serializer.validated_data.get("is_trusted", False)

    user = authenticate(request, email=email, password=password)

    if user is not None:
        if not user.is_email_verified:
            return Response(
                {"error": "Your email is not verified. Please verify your email."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if user.is_trusted:

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            update_serializer = UpdateTrustedStatusSerializer(
                user, data={"is_trusted": is_trusted}, partial=True
            )
            update_serializer.is_valid(raise_exception=True)
            update_serializer.save()

            return Response(
                {
                    "message": "Login successful.",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                },
                status=status.HTTP_200_OK,
            )

        verification_code = str(random.randint(100000, 999999)).zfill(6)
        payload = {
            "email": user.email,
            "verification_code": verification_code,
            "exp": timezone.now() + timedelta(minutes=5),
        }

        jwt_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        send_mail(
            "Your Verification Code",
            f"Your verification code is {verification_code}.",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

        return Response(
            {
                "message": "Login successful. Check your email for the verification code.",
                "jwt_token": jwt_token,
                "is_trusted": is_trusted,
            },
            status=status.HTTP_200_OK,
        )

    return Response(
        {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_code_view(request):
    data = request.data
    jwt_token = data.get("jwt_token")
    verification_code = data.get("verification_code")
    is_trusted = data.get("is_trusted")

    try:

        payload = jwt.decode(jwt_token, settings.SECRET_KEY, algorithms=["HS256"])
        user_email = payload["email"]
        original_code = payload["verification_code"]

        if verification_code != original_code:
            return Response(
                {"error": "Invalid verification code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.get(email=user_email)
        update_serializer = UpdateTrustedStatusSerializer(
            user, data={"is_trusted": is_trusted}, partial=True
        )
        update_serializer.is_valid(raise_exception=True)
        update_serializer.save()
        user.is_active = True
        user.first_login_time = (
            timezone.now() if not user.first_login_time else user.first_login_time
        )
        user.save()

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        return Response(
            {
                "message": "User Verified.",
                "access_token": access_token,
                "refresh_token": refresh_token,
            },
            status=status.HTTP_200_OK,
        )

    except jwt.ExpiredSignatureError:
        return Response(
            {"error": "Verification token has expired."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except jwt.DecodeError:
        return Response({"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
