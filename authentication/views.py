from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import make_password
from .serializers import CustomTokenObtainPairSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from .utils import send_email
from django.shortcuts import render

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken, OutstandingToken
from .models import User
from .serializers import RegistrationSerializer, RegisteredUserSerializer
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

User = get_user_model()


@api_view(['POST'])
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
    user_data = RegisteredUserSerializer(user).data
    send_verification_email(request, user)

    response_data = {
        "user": user_data,
        'message': 'Registration successful. Check your email to activate your account.'
    }
    return Response(response_data, status=status.HTTP_201_CREATED)


def send_verification_email(request, user):
    current_site = get_current_site(request)
    mail_subject = 'Activate your account.'
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    verification_link = reverse('activate', kwargs={'uidb64': uid, 'token': token})
    activation_url = f"http://{current_site.domain}{verification_link}"

    message = render_to_string('activation_form.html', {
        'user': user,
        'activation_url': activation_url,
    })

    send_email(mail_subject, message, [user.email])


@api_view(['GET'])
@permission_classes([AllowAny])
def activate_view(request, uidb64, token):
    uid = force_str(urlsafe_base64_decode(uidb64))
    user = User.objects.get(pk=uid)

    if default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return Response({'message': 'Your account has been activated.'}, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


def send_password_reset_email(request, user):
    current_site = get_current_site(request)
    mail_subject = 'Reset your password.'
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    reset_link = reverse('reset_password', kwargs={'uidb64': uid, 'token': token})
    reset_url = f"http://{current_site.domain}{reset_link}"

    message = render_to_string('password_reset_email.html', {
        'user': user,
        'reset_url': reset_url,
    })

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

            return Response({"message": "Successfully logged out."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({"error": "Refresh token not provided."}, status=status.HTTP_400_BAD_REQUEST)




@api_view(['POST'])
@permission_classes([AllowAny])
def Forgot_pwd_request_view(request):
    email = request.data.get('email')
    print(email)
    user = User.objects.get(email=email)
    send_password_reset_email(request, user)
    return Response({'message': 'Password reset link has been sent to your email.'}, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def reset_password_view(request, uidb64, token):
    uid = force_str(urlsafe_base64_decode(uidb64))
    user = User.objects.get(pk=uid)

    if request.method == 'GET':
        if default_token_generator.check_token(user, token):
            return render(request, 'password_reset_form.html', {'uidb64': uidb64, 'token': token})
        else:
            return Response({'error': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'POST':
        if default_token_generator.check_token(user, token):
            new_password = request.data.get('new_password')
            user.set_password(new_password)
            user.save()
            return Response({'message': 'Your password has been reset successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reset_password_view_old(request):
    old_password = request.data.get("old_password")
    new_password = request.data.get("new_password")

    if not old_password or not new_password:
        return Response({"error": "Both old and new passwords are required."}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user

    if not user.check_password(old_password):
        return Response({"error": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

    user.password = make_password(new_password)
    user.save()
    update_session_auth_hash(request, user)

    return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_users_view(request):
    users = User.objects.all()
    user_data = RegisteredUserSerializer(users, many=True).data
    return Response(user_data, status=status.HTTP_200_OK)
