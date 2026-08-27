# Layer: API
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.users.exceptions import InvalidCredentials, UserAlreadyExists
from apps.users.serializers import LoginSerializer, RegisterSerializer
from apps.users.services.user_service import UserService


@api_view(["POST"])
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
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        result = UserService.login_user(**serializer.validated_data)
    except InvalidCredentials as e:
        return Response({"code": 401, "msg": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

    return Response({"code": 200, "msg": "登录成功", "data": result})
