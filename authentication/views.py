import json
import random

from django.conf import settings
from django.contrib.auth import authenticate, update_session_auth_hash
from django.contrib.auth.hashers import make_password
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import RegistrationSerializer
from .utils import send_email


@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = User.objects.create_user(
        email=serializer.validated_data["email"],
        name=serializer.validated_data["name"],
        password=serializer.validated_data["password"],
    )
    user.is_active = False
    user.save()

    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    send_verification_email(request, user)
    response_data = {
        "message": "Registration successful. Check your email to activate your account.",
        "access_token": access_token,
        "refresh_token": str(refresh),
        "uid": uidb64,
    }
    return Response(response_data, status=status.HTTP_201_CREATED)


def send_verification_email(request, user):
    current_site = get_current_site(request)
    mail_subject = "Activate your account."

    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

    activation_url = (
        f"http://{current_site.domain}/user/activate/{access_token}/{uidb64}/"
    )

    message = render_to_string(
        "activation_form.html",
        {
            "user": user,
            "activation_url": activation_url,
        },
    )

    send_email(mail_subject, message, [user.email])


@api_view(["GET"])
@permission_classes([AllowAny])
def activate_view(request, token, uidb64):
    uid = force_str(urlsafe_base64_decode(uidb64))

    try:
        user = User.objects.get(pk=uid)
        UntypedToken(token)
        if user.is_active:
            return Response(
                {"message": "Your account is already activated."},
                status=status.HTTP_200_OK,
            )
        user.is_active = True
        user.save()

        return Response(
            {"message": "Your account has been activated."}, status=status.HTTP_200_OK
        )
    except TokenError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


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

        send_verification_email(request, user)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        return Response(
            {
                "message": "Verification email has been resent. Check your inbox.",
                "access_token": access_token,
                "uid": uidb64,
            },
            status=status.HTTP_200_OK,
        )

    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)


def send_password_reset_email(request, user):
    current_site = get_current_site(request)
    mail_subject = "Reset your password."
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    reset_link = reverse("reset_password", kwargs={"uidb64": uid, "token": token})
    reset_url = f"http://{current_site.domain}{reset_link}"

    message = render_to_string(
        "password_reset_email.html",
        {
            "user": user,
            "reset_url": reset_url,
        },
    )

    send_email(mail_subject, message, [user.email])


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    refresh_token = request.data.get("refresh")
    if refresh_token:
        try:
            token = RefreshToken(refresh_token)
            # Blacklist the token
            token.blacklist()

            return Response(
                {"message": "Successfully logged out."},
                status=status.HTTP_205_RESET_CONTENT,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(
            {"error": "Refresh token not provided."}, status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def Forgot_pwd_request_view(request):
    email = request.data.get("email")

    user = User.objects.get(email=email)
    send_password_reset_email(request, user)
    return Response(
        {"message": "Password reset link has been sent to your email."},
        status=status.HTTP_200_OK,
    )


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def reset_password_view(request, uidb64, token):
    uid = force_str(urlsafe_base64_decode(uidb64))
    user = User.objects.get(pk=uid)

    if request.method == "GET":
        if default_token_generator.check_token(user, token):
            return render(
                request, "password_reset_form.html", {"uidb64": uidb64, "token": token}
            )
        else:
            return Response(
                {"error": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    elif request.method == "POST":
        if default_token_generator.check_token(user, token):
            new_password = request.data.get("new_password")
            user.set_password(new_password)
            user.save()
            return Response(
                {"message": "Your password has been reset successfully."},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST
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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_users_view(request):
    users = User.objects.all()
    user_data = RegisteredUserSerializer(users, many=True).data
    return Response(user_data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get("email")
    password = request.data.get("password")

    user = authenticate(request, email=email, password=password)

    if user is not None:

        verification_code = str(random.randint(100000, 999999))

        request.session["verification_code"] = verification_code

        send_mail(
            "Your Verification Code",
            f"Your verification code is {verification_code}.",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

        return Response(
            {
                "message": "Login successful. Check your email for the verification code."
            },
            status=status.HTTP_200_OK,
        )

    return Response(
        {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_code_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            verification_code = data.get("verification_code")
            user_email = data.get("user_email")

            user = User.objects.get(email=user_email)

            session_verification_code = request.session.get("verification_code")

            if session_verification_code == verification_code:

                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)

                return Response(
                    {
                        "message": "Verify",
                        "access_token": access_token,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return JsonResponse({"error": "Invalid verification code."}, status=400)

        except User.DoesNotExist:
            return JsonResponse({"error": "User not found."}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)
