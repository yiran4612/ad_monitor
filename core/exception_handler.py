# Layer: infrastructure
"""统一异常响应格式：{code, msg, data}。

前端 axios 响应拦截器与业务代码均按 ``res.data.code`` / ``res.data.msg``
判断成败，因此所有 DRF 异常都要转成该信封格式（成功响应由各 View 自行组装）。
"""

from rest_framework.response import Response
from rest_framework.views import exception_handler


def _extract_message(body):
    """从 DRF 原始错误体中提取一句可直接展示给用户的 msg。"""
    if isinstance(body, dict):
        if "detail" in body:
            return body["detail"]
        if "non_field_errors" in body:
            errors = body["non_field_errors"]
            return errors[0] if isinstance(errors, list) and errors else str(errors)
        # serializer 字段级校验错误：msg 给通用提示（详见 data 字段说明）
        return "请求参数错误"
    if isinstance(body, list):
        return body[0] if body else "请求错误"
    return str(body)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        # DRF 未处理的异常（500 等）同样统一格式，避免前端拿到非 JSON 报错页
        return Response(
            {"code": 500, "msg": "服务器内部错误", "data": None},
            status=500,
        )

    return Response(
        {
            "code": response.status_code,
            "msg": _extract_message(response.data),
            "data": None,
        },
        status=response.status_code,
    )
