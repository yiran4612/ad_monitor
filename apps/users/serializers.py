# Layer: API
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.users.models import User


class RegisterSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11, min_length=11)
    password = serializers.CharField(max_length=128, write_only=True)
    nickname = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")
    role = serializers.ChoiceField(choices=User.Role.choices, default=User.Role.ADVERTISER)

    def validate_mobile(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("手机号必须为纯数字")
        return value


class LoginSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11, min_length=11)
    password = serializers.CharField(max_length=128, write_only=True)

    def validate_mobile(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("手机号必须为纯数字")
        return value


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """自定义 JWT Token 序列化器 — 仅做数据组装，无业务逻辑。

    - token payload 增加 mobile / role
    - 响应返回 access / refresh / mobile / nickname / role
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # 自定义 claims：mobile / role
        token["mobile"] = user.mobile
        token["role"] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # 响应中附加用户信息
        data["mobile"] = self.user.mobile
        data["nickname"] = self.user.nickname
        data["role"] = self.user.role
        return data
