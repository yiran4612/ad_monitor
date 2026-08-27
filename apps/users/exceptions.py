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
