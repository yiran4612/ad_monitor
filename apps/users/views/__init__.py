# Layer: API
"""users 视图包。

- ``auth_views``：注册 / 登录（P0 前端协议适配）
- ``p1_views``  ：P1 用户相关接口（check-login / 地区 / 客户资料 / 改密 / 验证码）

本文件重导出登录注册视图，保持 ``from apps.users.views import login_view`` 可用。
"""

from apps.users.views.auth_views import login_view, register_view

__all__ = ["login_view", "register_view"]
