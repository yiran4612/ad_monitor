# Layer: Service
from django.contrib.auth import authenticate
from django.db import transaction

from apps.users.exceptions import InvalidCredentials, UserAlreadyExists
from apps.users.models import User
from core.auth.jwt import JWTService


class UserService:
    @staticmethod
    @transaction.atomic
    def register_user(*, mobile: str, password: str, nickname: str, role: str) -> User:
        if User.objects.filter(mobile=mobile).exists():
            raise UserAlreadyExists(mobile)
        user = User.objects.create_user(
            mobile=mobile,
            password=password,
            nickname=nickname,
            role=role,
        )
        return user

    @staticmethod
    def login_user(*, mobile: str, password: str) -> dict:
        user = authenticate(mobile=mobile, password=password)
        if user is None:
            raise InvalidCredentials()
        tokens = JWTService.generate_tokens(user)
        return {
            "access": tokens["access"],
            "refresh": tokens["refresh"],
            "mobile": user.mobile,
            "nickname": user.nickname,
            "role": user.role,
        }
