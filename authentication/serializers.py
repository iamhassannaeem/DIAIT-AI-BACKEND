from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data.update({
            "email": self.user.email,
            "name": self.user.name,
        })
        return data


from rest_framework import serializers
from .models import User
class RegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    name = serializers.CharField()
    is_organization_owner = serializers.BooleanField(required=False, default=False)  # Add this line

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            name=validated_data["name"],
            password=validated_data["password"],
            is_organization_owner=validated_data.get("is_organization_owner", False),  # Update this line
        )
        return user


# class RegistrationSerializer(serializers.Serializer):
#     email = serializers.EmailField()
#     password = serializers.CharField(write_only=True)
#     name = serializers.CharField()
#
#     def create(self, validated_data):
#         user = User.objects.create_user(
#             email=validated_data["email"],
#             name=validated_data["name"],
#             password=validated_data["password"],
#         )
#         return user


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
        fields = ["id", "email", "name", "token"]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["name"]


class RegisteredUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name']




class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data.update(
            {
                "email": self.user.email,
                "name": self.user.name,
            }
        )
        return data
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data.update({
            "email": self.user.email,
            "name": self.user.name,
        })
        return data



