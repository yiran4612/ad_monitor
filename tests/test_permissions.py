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
        assert body["code"] == "token_not_valid"
