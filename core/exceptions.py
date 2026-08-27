# Layer: infrastructure
class TokenExpired(Exception):
    """Access token 已过期。"""

    def __init__(self):
        super().__init__("Token 已过期")


class InvalidToken(Exception):
    """Token 非法或格式错误。"""

    def __init__(self, detail: str = "无效的 Token"):
        self.detail = detail
        super().__init__(detail)


class TokenBlacklisted(Exception):
    """Token 已被加入黑名单。"""

    def __init__(self):
        super().__init__("Token 已被拉黑")
