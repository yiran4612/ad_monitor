# Layer: infrastructure
"""自定义认证：兼容前端 axios 的 token 请求头。

前端（Vue3 + axios）在请求拦截器中写入：

    config.headers['token'] = localStorage.getItem('token')

而 SimpleJWT 默认只认 ``Authorization: Bearer <jwt>``，两者协议不一致。
本模块复用 SimpleJWT 的校验逻辑读取 ``token`` 头，实现零前端改动的适配。
"""

import logging

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

logger = logging.getLogger(__name__)

# localStorage 为空时 axios 可能把字面量写进请求头，视为未携带 token
_EMPTY_TOKENS = {"", "null", "undefined", "none"}


class TokenHeaderAuthentication(BaseAuthentication):
    """从请求头 ``token`` 字段读取 JWT 并完成认证。

    - 无 token 头（或为空/占位值）→ 返回 None，交给后续认证类（Bearer）处理
    - token 无效 / 过期 / 用户不存在 → AuthenticationFailed（401）
    """

    keyword = "token"

    def authenticate(self, request):
        token = request.headers.get(self.keyword)
        if not token or str(token).strip().lower() in _EMPTY_TOKENS:
            return None

        jwt_auth = JWTAuthentication()
        try:
            validated_token = jwt_auth.get_validated_token(token)
            user = jwt_auth.get_user(validated_token)
        except Exception as exc:
            # 不向调用方透传具体原因（避免 token 结构/用户枚举信息泄露），细节记日志
            logger.warning("token 头认证失败: %s", exc)
            raise AuthenticationFailed("未授权") from exc

        return (user, validated_token)

    def authenticate_header(self, request):
        return self.keyword
