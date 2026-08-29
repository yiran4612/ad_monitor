# Layer: API
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
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


# ──────────────────────────────────────────────
# P1 用户相关接口序列化器
# ──────────────────────────────────────────────


class PhoneCaptchaSerializer(serializers.Serializer):
    """getPhoneCaptcha 入参。"""

    phone = serializers.CharField(max_length=11, min_length=11)

    def validate_phone(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("手机号必须为纯数字")
        return value


class CustomerProfileUpdateSerializer(serializers.Serializer):
    """editCustomerInfos 入参。

    字段名对齐前端提交体（camelCase），同时接受 snake_case 别名，
    便于 Swagger 与后端调用方使用。全部字段可选，只更新传入的部分。
    """

    customerName = serializers.CharField(max_length=128, required=False, allow_blank=True)
    company_name = serializers.CharField(max_length=128, required=False, allow_blank=True)
    contactName = serializers.CharField(max_length=64, required=False, allow_blank=True)
    contact_name = serializers.CharField(max_length=64, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=11, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    address = serializers.CharField(max_length=255, required=False, allow_blank=True)
    licenseUrl = serializers.URLField(max_length=512, required=False, allow_blank=True)
    license_url = serializers.URLField(max_length=512, required=False, allow_blank=True)
    # area 是「浙江省/杭州市/西湖区」展示文本；areaId 是地区树节点 id
    area = serializers.CharField(max_length=255, required=False, allow_blank=True)
    areaId = serializers.IntegerField(required=False, min_value=0)
    area_id = serializers.IntegerField(required=False, min_value=0)
    captcha = serializers.CharField(max_length=6, required=False, allow_blank=True)

    def validate_phone(self, value):
        if value and not value.isdigit():
            raise serializers.ValidationError("手机号必须为纯数字")
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """changePsw 入参：原密码 + 新密码（同时接受 camelCase 别名）。"""

    old_password = serializers.CharField(max_length=128, required=False, allow_blank=True)
    new_password = serializers.CharField(max_length=128, required=False, allow_blank=True)
    oldPassword = serializers.CharField(max_length=128, required=False, allow_blank=True)
    newPassword = serializers.CharField(max_length=128, required=False, allow_blank=True)

    def validate(self, attrs):
        old_password = attrs.get("old_password") or attrs.get("oldPassword")
        new_password = attrs.get("new_password") or attrs.get("newPassword")
        if not old_password:
            raise serializers.ValidationError("原密码不能为空")
        if not new_password:
            raise serializers.ValidationError("新密码不能为空")

        try:
            validate_password(new_password, self.context.get("user"))
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

        attrs["old_password"] = old_password
        attrs["new_password"] = new_password
        return attrs
