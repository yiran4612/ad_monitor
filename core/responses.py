# Layer: infrastructure
"""统一响应信封：``{code, msg, data}``。

约定（与前端 axios 拦截器一致，前端以 ``res.data.code === 200`` 判定成功）：

===========  ============================================================
code         含义
===========  ============================================================
200          成功
1001         参数错误（序列化器校验失败）
401          未登录 / token 无效（由 DRF 权限层直接返回，见 exception_handler）
1002         权限不足或业务规则不允许
===========  ============================================================

注意：1001 / 1002 默认以 HTTP 200 返回。前端 axios 响应拦截器会把非 2xx
判为网络异常并丢弃 ``msg``，只有 HTTP 200 + 非 200 的 code 才能让前端
弹出生效的服务端提示。
"""

from rest_framework.response import Response

SUCCESS = 200
PARAM_ERROR = 1001
UNAUTHORIZED = 401
BIZ_ERROR = 1002


def api_response(code: int, msg: str, data=None, status: int = 200) -> Response:
    """响应信封的唯一出口。"""
    return Response({"code": code, "msg": msg, "data": data}, status=status)


def success(data=None, msg: str = "success") -> Response:
    return api_response(SUCCESS, msg, data)


def param_error(msg: str = "请求参数错误", data=None) -> Response:
    return api_response(PARAM_ERROR, msg, data)


def biz_error(msg: str, data=None) -> Response:
    return api_response(BIZ_ERROR, msg, data)


def unauthorized(msg: str = "未登录", data=None) -> Response:
    return api_response(UNAUTHORIZED, msg, data, status=UNAUTHORIZED)


def first_error(errors) -> str:
    """从 DRF 的 ``serializer.errors`` 中提取第一条可读消息。

    errors 形态可能为：
    ``{"field": ["msg1", ...]}`` / ``{"non_field_errors": ["msg"]}`` / ``["msg"]``
    """
    if isinstance(errors, dict):
        for value in errors.values():
            message = first_error(value)
            if message:
                return message
        return "请求参数错误"
    if isinstance(errors, list):
        return str(errors[0]) if errors else "请求参数错误"
    return str(errors)
