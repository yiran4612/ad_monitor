# Layer: API
"""P1 用户相关接口。

路由统一挂在 ``/api/users/`` 下且**不带尾斜杠**（对齐前端 axios 实际请求路径，
本项目 ``APPEND_SLASH = False``，带斜杠注册前端会 404）。

认证约定：
- ``getPhoneCaptcha`` 免登录（下发验证码）
- 其余接口需登录（``IsAuthenticated``），未登录由 DRF 权限层返回 401
- 所有写操作只作用于 ``request.user``，不接受调用方传入的用户标识
"""

from django.conf import settings
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.users.areas import get_area_tree
from apps.users.exceptions import CaptchaInvalid, OldPasswordIncorrect
from apps.users.serializers import (
    ChangePasswordSerializer,
    CustomerProfileUpdateSerializer,
    PhoneCaptchaSerializer,
)
from apps.users.services.captcha_service import CaptchaService
from apps.users.services.customer_service import CustomerProfileService
from core.responses import biz_error, first_error, param_error, success


@extend_schema(tags=["用户-P1"], summary="检查登录态")
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def check_login(request):
    """校验 Authorization / token 头是否有效，返回当前登录用户。"""
    user = request.user
    return success(
        {
            "is_login": True,
            "user": {
                "id": user.id,
                "username": user.nickname or user.mobile,
                "phone": user.mobile,
            },
        }
    )


@extend_schema(
    tags=["用户-P1"],
    summary="地区级联数据",
    parameters=[
        OpenApiParameter(
            name="id",
            type=int,
            location=OpenApiParameter.QUERY,
            description="父级地区ID，0 返回全量省市区树",
            default=0,
        )
    ],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_area_info(request):
    """返回 a-cascader 直接消费的 ``[{id, name, children}]`` 结构。"""
    raw_id = request.query_params.get("id", "0")
    try:
        parent_id = int(raw_id)
    except (TypeError, ValueError):
        return param_error("id 必须为整数")
    if parent_id < 0:
        return param_error("id 不能为负数")
    return success(get_area_tree(parent_id))


@extend_schema(tags=["用户-P1"], summary="获取客户资料")
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_customer_infos(request):
    return success(CustomerProfileService.get_profile(request.user))


@extend_schema(tags=["用户-P1"], summary="提交/更新客户资料")
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def edit_customer_infos(request):
    serializer = CustomerProfileUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return param_error(first_error(serializer.errors))

    try:
        profile = CustomerProfileService.update_profile(request.user, serializer.validated_data)
    except CaptchaInvalid as e:
        return biz_error(str(e))

    return success(profile, msg="提交成功，请等待审核")


@extend_schema(tags=["用户-P1"], summary="修改密码")
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_psw(request):
    serializer = ChangePasswordSerializer(data=request.data, context={"user": request.user})
    if not serializer.is_valid():
        return param_error(first_error(serializer.errors))

    try:
        CustomerProfileService.change_password(
            request.user,
            serializer.validated_data["old_password"],
            serializer.validated_data["new_password"],
        )
    except OldPasswordIncorrect as e:
        return biz_error(str(e))

    return success(msg="密码修改成功")


@extend_schema(tags=["用户-P1"], summary="登录提示信息")
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_login_tip_info(request):
    """P1 返回静态空列表：前端判断 ``data.tip_url.length > 0`` 才弹窗。"""
    return success({"tip_url": []})


@extend_schema(
    tags=["用户-P1"],
    summary="获取短信验证码（mock）",
    parameters=[OpenApiParameter(name="phone", type=str, location=OpenApiParameter.QUERY, required=True)],
)
@api_view(["GET"])
@permission_classes([AllowAny])
def get_phone_captcha(request):
    """不接短信网关：验证码写入日志 + 缓存，DEBUG 模式下在响应里回显便于联调。"""
    serializer = PhoneCaptchaSerializer(data=request.query_params)
    if not serializer.is_valid():
        return param_error(first_error(serializer.errors))

    phone = serializer.validated_data["phone"]
    code = CaptchaService.send(phone)

    data = {"phone": phone, "expires_in": CaptchaService.TTL}
    if getattr(settings, "DEBUG", False):
        data["captcha"] = code
    return success(data, msg="验证码已发送")
