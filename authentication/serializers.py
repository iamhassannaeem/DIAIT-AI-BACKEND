from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


class RegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)
    name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ["email", "password", "name"]

    def create(self, validated_data):

        user = User(
            email=validated_data["email"],
            name=validated_data["name"],
            is_active=False,
            is_email_verified=False,
        )
        user.set_password(validated_data["password"])
        user.save()

        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)
    is_trusted = serializers.BooleanField(required=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        is_trusted = attrs.get("is_trusted")

        user = User.objects.filter(email=email).first()
        if user is None or not user.check_password(password):
            raise serializers.ValidationError("Invalid email or password.")

        attrs["user"] = user
        return attrs


class UserDetailSerializer(serializers.ModelSerializer):
    token = serializers.SerializerMethodField()

    def get_token(self, obj):
        refresh = RefreshToken.for_user(obj)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "name",
            "token",
            "is_email_verified",
            "is_active",
        ]


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["name"]


class UpdateTrustedStatusSerializer(serializers.ModelSerializer):
    is_trusted = serializers.BooleanField(required=True)

    class Meta:
        model = User
        fields = ["is_trusted"]

    def update(self, instance, validated_data):
        instance.is_trusted = validated_data.get("is_trusted", instance.is_trusted)
        instance.save()
        return instance
