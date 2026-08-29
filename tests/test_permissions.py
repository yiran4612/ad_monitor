import pytest

pytestmark = pytest.mark.django_db


class TestPermissions:
    """认证边界：未认证 / 无效 JWT 访问受保护接口。

    全局权限为 IsAuthenticated（core/settings/base.py），
    注册/登录视图在 apps/users/views.py 显式 AllowAny。
    """

    # ===== 未认证访问受保护接口 -> 401 =====
    def test_unauthenticated_access_advertisers_returns_401(self, api_client):
        resp = api_client.get("/api/ads/advertisers/")
        assert resp.status_code == 401

    # ===== 无效 JWT -> 401（认证阶段即拒绝，与权限无关）=====
    def test_invalid_jwt_token_returns_401(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid.token.here")
        resp = api_client.get("/api/ads/advertisers/")
        assert resp.status_code == 401
        body = resp.json()
        # 统一响应信封：{code, msg, data}
        assert body["code"] == 401
        assert "msg" in body
        assert body["data"] is None

    # ===== 前端协议：token 请求头 -> 与 Bearer 等价 =====
    def test_token_header_authenticates(self, api_client, test_user):
        _user, token = test_user
        api_client.credentials(HTTP_TOKEN=token)
        resp = api_client.get("/api/ads/advertisers/")
        assert resp.status_code == 200
        assert resp.json()["code"] == 200
