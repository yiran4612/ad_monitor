# Layer: Service
class UserAlreadyExists(Exception):
    """手机号已被注册。"""

    def __init__(self, mobile: str):
        self.mobile = mobile
        super().__init__(f"手机号 {mobile} 已被注册")


class InvalidCredentials(Exception):
    """手机号或密码错误。"""

    def __init__(self):
        super().__init__("手机号或密码错误")


class OldPasswordIncorrect(Exception):
    """修改密码时原密码校验失败。"""

    def __init__(self):
        super().__init__("原密码错误")


class CaptchaInvalid(Exception):
    """短信验证码错误或已过期。"""

    def __init__(self):
        super().__init__("验证码错误或已过期")
