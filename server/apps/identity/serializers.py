from rest_framework import serializers

from .access import CAPABILITIES, effective_permissions
from .models import LoginSession, User, phone_validator


class PhoneInput(serializers.Serializer):
    phone = serializers.CharField(max_length=16, validators=[phone_validator])


class PasswordInput(PhoneInput):
    password = serializers.CharField(max_length=128, trim_whitespace=False, write_only=True)


class CodeInput(PhoneInput):
    code = serializers.RegexField(r"^[0-9]{6}$")


class UserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    password = serializers.CharField(
        required=False, write_only=True, trim_whitespace=False, max_length=128
    )
    permissions = serializers.SerializerMethodField()

    def to_internal_value(self, data):
        if set(data) - {
            "phone",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "is_deleted",
            "password",
        }:
            raise serializers.ValidationError({"non_field_errors": ["Unsupported account fields."]})
        return super().to_internal_value(data)

    def get_permissions(self, user):
        return sorted(effective_permissions(user))

    class Meta:
        model = User
        fields = [
            "id",
            "phone",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "is_deleted",
            "created_at",
            "password",
            "permissions",
        ]
        read_only_fields = ["id", "created_at"]
        extra_kwargs = {"phone": {"validators": [phone_validator]}}


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginSession
        fields = ["id", "created_at", "expires_at", "revoked_at"]
        read_only_fields = fields


class PermissionInput(serializers.Serializer):
    permissions = serializers.ListField(
        child=serializers.ChoiceField(choices=list(CAPABILITIES)), max_length=len(CAPABILITIES)
    )
    expected_permissions = serializers.ListField(
        child=serializers.ChoiceField(choices=list(CAPABILITIES)), max_length=len(CAPABILITIES)
    )

    def validate(self, data):
        for field in ("permissions", "expected_permissions"):
            if len(data[field]) != len(set(data[field])):
                raise serializers.ValidationError({field: "Select distinct permissions."})
        return data
