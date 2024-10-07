from rest_framework import serializers
from .models import User, PermissionGroup
from rest_framework_simplejwt.tokens import RefreshToken


class RegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    name = serializers.CharField()
    # org = serializers.CharField()
    # sub_type = serializers.CharField()
    # package = serializers.IntegerField()
    permission_group_id = serializers.IntegerField(required=False)

    def create(self, validated_data):

        user = User.objects.create_user(
            email=validated_data["email"],
            name=validated_data["name"],
            password=validated_data["password"],
        )
        return user


class RegisteredUserSerializer(serializers.ModelSerializer):
    token = serializers.SerializerMethodField()

    def get_token(self, obj):
        refresh = RefreshToken.for_user(obj)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

    class Meta:
        model = User
        fields = ["id", "email", "name", "token", "is_organization_owner"]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["name"]


###############################

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        # Add custom user data to the response (e.g., email, name)
        data.update(
            {
                "email": self.user.email,
                "name": self.user.name,
            }
        )

        return data
