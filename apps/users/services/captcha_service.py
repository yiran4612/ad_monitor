# Layer: Service
"""短信验证码服务（P1 为 mock 实现，不接真实短信网关）。

真实短信 SDK 接入时只需替换 ``send`` 的内部实现，
View 层禁止直接调用缓存或第三方 SDK。
"""

import logging
import secrets

from django.core.cache import cache

logger = logging.getLogger(__name__)


class CaptchaService:
    """短信验证码：下发（mock）+ 校验。"""

    CACHE_KEY_PREFIX = "users:captcha:"
    TTL = 5 * 60  # 验证码有效期（秒）

    @staticmethod
    def _cache_key(phone: str) -> str:
        return f"{CaptchaService.CACHE_KEY_PREFIX}{phone}"

    @staticmethod
    def send(phone: str) -> str:
        """生成并缓存验证码，返回明文码（仅用于日志 / DEBUG 回显）。"""
        code = f"{secrets.randbelow(1_000_000):06d}"
        cache.set(CaptchaService._cache_key(phone), code, CaptchaService.TTL)
        # 未接短信网关：验证码只落到日志，联调时从日志里取
        logger.info("[mock 短信] 手机号 %s 的验证码为 %s（%s 秒后失效）", phone, code, CaptchaService.TTL)
        return code

    @staticmethod
    def verify(phone: str, code: str) -> bool:
        """校验验证码；通过返回 True（校验成功后立即失效）。"""
        cached = cache.get(CaptchaService._cache_key(phone))
        if cached is None or cached != code:
            return False
        cache.delete(CaptchaService._cache_key(phone))
        return True
