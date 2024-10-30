import json

from django.utils import timezone
import jwt
from django.conf import settings
from django.contrib.auth import authenticate, update_session_auth_hash
from django.contrib.auth.hashers import make_password

from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken, UntypedToken

from  .models import User
from .serializers import RegistrationSerializer
from .utils import send_email
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site

User = get_user_model()

@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)


    if User.objects.filter(email=serializer.validated_data["email"]).exists():
        return Response(
            {"message": "Email already exists. Please use a different email."},
            status=status.HTTP_400_BAD_REQUEST
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


    send_verification_email(request, user,access_token)

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

    send_email(
        subject=mail_subject,
        message=message,
        recipient_list=[user.email]
    )



@api_view(["GET"])
@permission_classes([AllowAny])
def activate_view(request, token):
    try:
        payload = UntypedToken(token)
        user_id = payload.get("user_id")

        if not user_id:
            return Response({"error": "Invalid token payload."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.get(id=user_id)

        if user.is_active:
            return Response({"message": "Your account is already activated."}, status=status.HTTP_200_OK)

        user.is_active = True
        user.save()

        return Response({"message": "Your account has been activated."}, status=status.HTTP_200_OK)

    except TokenError:
        return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
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



        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        send_verification_email(request, user,access_token)

        # uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        return Response(
            {
                "message": "Verification email has been resent. Check your inbox.",
                "access_token": access_token,
                # "uid": uidb64,
            },
            status=status.HTTP_200_OK,
        )

    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)



def send_password_reset_email(user, request):
    token = RefreshToken.for_user(user).access_token
    current_site = get_current_site(request)
    reset_url = f"http://{current_site.domain}/user/reset_password/{token}/"  # Use formatted string
    mail_subject = "Reset your password."
    message = f"Hi {user.name},\n\nClick the link below to reset your password:\n{reset_url}"
    send_email(mail_subject, message, [user.email])

@api_view(["POST"])
@permission_classes([AllowAny])
def forgot_pwd_request_view(request):
    email = request.data.get("email")

    try:
        user = User.objects.get(email=email)
        print(user)
        send_password_reset_email(user,request)
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
def reset_password_view(request,token):
    # token = request.data.get("token")
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
        user.set_verification_code()
        send_mail(
            "Your Verification Code",
            f"Your verification code is {user.verification_code}.",
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
            data = request.data
            verification_code = data.get("verification_code")
            user_email = data.get("user_email")

            user = User.objects.get(email=user_email)


            if (
                user.verification_code == verification_code and
                user.verification_code_expires_at > timezone.now()
            ):

                user.verification_code = None
                user.verification_code_expires_at = None
                user.save()

                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)

                return Response(
                    {
                        "message": "User Verified.",
                        "access_token": access_token,
                        "refresh_token": refresh_token
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return JsonResponse({"error": "Invalid or expired verification code."}, status=400)

        except User.DoesNotExist:
            return JsonResponse({"error": "User not found."}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    refresh_token = request.data.get("refresh")
    if refresh_token:
        try:
            token = RefreshToken(refresh_token)

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
