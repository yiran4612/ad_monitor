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
    """登录参数。

    前端（Vue3）登录表单字段名为 ``account``，为兼容 Swagger / 后端调用方，
    同时接受 ``username`` 与旧的 ``mobile``，三者任选其一。
    校验通过后统一归一化为 ``account``。
    """

    account = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")
    username = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")
    mobile = serializers.CharField(max_length=11, required=False, allow_blank=True, default="")
    password = serializers.CharField(max_length=128, write_only=True)

    def validate(self, attrs):
        account = attrs.get("account") or attrs.get("username") or attrs.get("mobile")
        if not account:
            raise serializers.ValidationError("账号不能为空")
        attrs["account"] = account
        return attrs


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
