from rest_framework import serializers

from .models import LoginSession, User, phone_validator


class PhoneInput(serializers.Serializer):
    phone = serializers.CharField(max_length=16, validators=[phone_validator])


class PasswordInput(PhoneInput):
    password = serializers.CharField(max_length=128, trim_whitespace=False, write_only=True)


class CodeInput(PhoneInput):
    code = serializers.RegexField(r"^[0-9]{6}$")


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone", "role", "is_active", "is_deleted", "created_at"]
        read_only_fields = ["id", "created_at"]
        extra_kwargs = {"phone": {"validators": [phone_validator]}}


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginSession
        fields = ["id", "created_at", "expires_at", "revoked_at"]
        read_only_fields = fields
