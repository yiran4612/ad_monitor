# Layer: API
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.users.exceptions import InvalidCredentials, UserAlreadyExists
from apps.users.serializers import LoginSerializer, RegisterSerializer
from apps.users.services.user_service import UserService


@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        user = UserService.register_user(**serializer.validated_data)
    except UserAlreadyExists as e:
        return Response({"code": 400, "msg": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {
            "code": 200,
            "msg": "注册成功",
            "data": {"mobile": user.mobile, "nickname": user.nickname, "role": user.role},
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    """用户登录。

    响应遵循前端协议：``{code, msg, data}``，其中 ``data.token`` 会被前端
    写入 localStorage，并在后续请求中作为 ``token`` 请求头回传
    （见 core.authentication.TokenHeaderAuthentication）。
    """
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        result = UserService.login_user(
            mobile=serializer.validated_data["account"],
            password=serializer.validated_data["password"],
        )
    except InvalidCredentials as e:
        return Response({"code": 401, "msg": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

    return Response(
        {
            "code": 200,
            "msg": "success",
            "data": {
                # ── 前端协议字段 ──
                "token": result["access"],
                "account": result["mobile"],
                "customerName": result["nickname"] or "",
                # ── 兼容字段（Swagger / 既有调用方）──
                "access": result["access"],
                "refresh": result["refresh"],
                "mobile": result["mobile"],
                "nickname": result["nickname"],
                "role": result["role"],
            },
        }
    )
