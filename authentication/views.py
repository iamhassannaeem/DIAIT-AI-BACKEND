from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import IntegrityError
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import (
    RefreshToken,
    OutstandingToken,
)

from .models import User
from .serializers import (
    RegistrationSerializer,
    RegisteredUserSerializer,
)


# from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegistrationSerializer(data=request.data)
    if serializer.is_valid():
        try:
            user = User.objects.create_user(
                email=serializer.validated_data["email"],
                name=serializer.validated_data["name"],
                password=serializer.validated_data["password"],
            )
            user.is_organization_owner = True
            user.save()

            # permission_group = PermissionGroup.objects.get(id=serializer.validated_data.get("permission_group_id"))
            # user.group = permission_group
            # user.save()

            # Use RegisteredUserSerializer to return user info and token
            registered_user_serializer = RegisteredUserSerializer(user)
            refresh = RefreshToken.for_user(user)
            data = {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
            return Response(data)

            return Response(
                registered_user_serializer.data, status=status.HTTP_201_CREATED
            )

        except PermissionGroup.DoesNotExist:
            return Response(
                {"error": "Permission group does not exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except IntegrityError:
            return Response(
                {"error": "Duplicate email."}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            if user.id is not None:
                user.delete()  # Rollback user creation on error
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class LoginView(TokenObtainPairView):
#     serializer_class = CustomTokenObtainPairSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:

        refresh_token = request.data.get("refresh")

        if refresh_token:

            OutstandingToken.objects.filter(token=refresh_token).update(
                blacklisted=True
            )
            return Response(
                {"message": "Successfully logged out."},
                status=status.HTTP_205_RESET_CONTENT,
            )
        else:
            return Response(
                {"error": "Refresh token not provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password_confirm_view(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)

        if default_token_generator.check_token(user, token):
            new_password = request.data.get("new_password")
            user.set_password(new_password)
            user.save()
            return Response(
                {"message": "Password has been reset."}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST
            )
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({"error": "Invalid user."}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password_view(request):
    email = request.data.get("email")
    try:
        user = User.objects.get(email=email)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f"http://yourfrontend/reset-password/{uid}/{token}/"

        message = render_to_string(
            "reset_password_email.html",
            {
                "user": user,
                "reset_link": reset_link,
            },
        )

        try:
            send_mail(
                "Password Reset",
                message,
                "shahzaib.adil@kics.edu.pk",  # Sender's email
                [email],  # Recipient list
                fail_silently=False,
            )
        except Exception as email_error:
            return Response(
                {"error": f"Failed to send email: {str(email_error)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"message": "Password reset link sent to email."}, status=status.HTTP_200_OK
        )
    except User.DoesNotExist:
        return Response(
            {"error": "User with this email does not exist."},
            status=status.HTTP_404_NOT_FOUND,
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


###### twilio#########

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
import random

from .utils import send_verification_code


verification_codes = {}


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get("email")
    password = request.data.get("password")
    phone_number = request.data.get("phone_number")

    user = authenticate(request, username=email, password=password)
    if user is not None:

        verification_code = random.randint(100000, 999999)
        verification_codes[phone_number] = verification_code

        send_verification_code(phone_number, verification_code)

        return Response(
            {"message": "Verification code sent."}, status=status.HTTP_200_OK
        )

    return Response(
        {"error": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_code_view(request):
    phone_number = request.data.get("phone_number")
    verification_code = request.data.get("verification_code")

    if verification_codes.get(phone_number) == int(verification_code):

        del verification_codes[phone_number]
        return Response(
            {"message": "Verification successful. You are logged in."},
            status=status.HTTP_200_OK,
        )

    return Response(
        {"error": "Invalid verification code."}, status=status.HTTP_400_BAD_REQUEST
    )
