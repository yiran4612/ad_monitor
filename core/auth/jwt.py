# Layer: infrastructure
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken, TokenError

from core.exceptions import InvalidToken, TokenBlacklisted, TokenExpired


class JWTService:
    """SimpleJWT 封装层 — 生成 / 解析 token。"""

    @staticmethod
    def generate_tokens(user) -> dict:
        """为指定 user 生成 access + refresh token 对。"""
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

    @staticmethod
    def decode_access_token(token: str) -> dict:
        """
        解析 access token，成功返回 payload dict。
        失败按原因抛 TokenExpired / TokenBlacklisted / InvalidToken。
        """
        try:
            access_token = AccessToken(token)
        except TokenError as e:
            message = str(e).lower()
            if "expired" in message:
                raise TokenExpired()
            if "blacklist" in message:
                raise TokenBlacklisted()
            raise InvalidToken(str(e))
        return access_token.payload
