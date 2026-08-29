import pytest

from apps.users.models import CustomerProfile

pytestmark = pytest.mark.django_db

AREA_URL = "/api/users/getAreaInfo"
PROFILE_URL = "/api/users/getCustomerInfos"


class TestCheckLogin:
    """check-login：需登录，返回 is_login + 用户信息。"""

    def test_check_login_success(self, auth_client, test_user):
        user, _token = test_user
        resp = auth_client.get("/api/users/check-login")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["is_login"] is True
        assert body["data"]["user"]["id"] == user.id
        assert body["data"]["user"]["phone"] == user.mobile

    def test_check_login_unauthenticated(self, api_client):
        resp = api_client.get("/api/users/check-login")
        assert resp.status_code == 401
        assert resp.json()["code"] == 401


class TestAreaInfo:
    """getAreaInfo：id=0 返回全量树，其他返回子节点。"""

    def test_get_area_info_root(self, auth_client):
        resp = auth_client.get(f"{AREA_URL}?id=0")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list) and len(data) > 0
        province = data[0]
        assert set(province) == {"id", "name", "children"}
        # 省 -> 市 -> 区 三级齐全，前端 cascader 才能一次选到底
        assert province["children"][0]["children"]

    def test_get_area_info_children(self, auth_client):
        resp = auth_client.get(f"{AREA_URL}?id=330000")  # 浙江省
        assert resp.status_code == 200
        names = [item["name"] for item in resp.json()["data"]]
        assert names == ["杭州市", "宁波市"]

    def test_get_area_info_leaf(self, auth_client):
        resp = auth_client.get(f"{AREA_URL}?id=330106")  # 西湖区（叶子）
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_get_area_info_invalid_id(self, auth_client):
        resp = auth_client.get(f"{AREA_URL}?id=abc")
        assert resp.status_code == 200
        assert resp.json()["code"] == 1001

    def test_get_area_info_requires_auth(self, api_client):
        assert api_client.get(f"{AREA_URL}?id=0").status_code == 401


class TestCustomerInfos:
    """getCustomerInfos / editCustomerInfos。"""

    def test_get_customer_infos_default(self, auth_client, test_user):
        user, _token = test_user
        resp = auth_client.get(PROFILE_URL)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["customer_audit_status"] == CustomerProfile.AuditStatus.PENDING
        assert data["login_phone"] == user.mobile
        assert data["customerName"] == ""

    def test_edit_customer_infos_success(self, auth_client, test_user):
        user, _token = test_user
        resp = auth_client.post(
            "/api/users/editCustomerInfos",
            {
                "customerName": "杭州某某传媒有限公司",
                "contactName": "张三",
                "phone": "13900139111",
                "email": "zhangsan@example.com",
                "address": "文一西路 100 号",
                "licenseUrl": "https://example.com/license.png",
                "area": "浙江省/杭州市/西湖区",
            },
            format="json",
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["customerName"] == "杭州某某传媒有限公司"

        profile = CustomerProfile.objects.get(user=user)
        assert profile.contact_name == "张三"
        assert profile.contact_phone == "13900139111"
        assert profile.area_path == "浙江省/杭州市/西湖区"
        # 未显式传 areaId：由名称路径反查到最深层节点
        assert profile.area_id == 330106

    def test_edit_customer_infos_with_area_id(self, auth_client, test_user):
        user, _token = test_user
        resp = auth_client.post(
            "/api/users/editCustomerInfos",
            {"customerName": "宁波分公司", "areaId": 330203},
            format="json",
        )
        assert resp.json()["code"] == 200
        assert CustomerProfile.objects.get(user=user).area_id == 330203

    def test_edit_customer_infos_invalid_email(self, auth_client):
        resp = auth_client.post(
            "/api/users/editCustomerInfos",
            {"customerName": "X", "email": "not-an-email"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == 1001

    def test_edit_customer_infos_requires_auth(self, api_client):
        resp = api_client.post("/api/users/editCustomerInfos", {"customerName": "X"}, format="json")
        assert resp.status_code == 401
        assert resp.json()["code"] == 401

    def test_edit_customer_infos_only_touches_current_user(self, auth_client, test_user, django_user_model):
        """写操作只作用于 request.user，不会改到别人的资料。"""
        user, _token = test_user
        other = django_user_model.objects.create_user(mobile="13900139999", password="Test123456")
        CustomerProfile.objects.create(user=other, company_name="别人的公司")

        auth_client.post("/api/users/editCustomerInfos", {"customerName": "我的公司"}, format="json")

        assert CustomerProfile.objects.get(user=user).company_name == "我的公司"
        assert CustomerProfile.objects.get(user=other).company_name == "别人的公司"


class TestChangePsw:
    """changePsw：验旧密码 + 改密码。"""

    def test_change_psw_success(self, auth_client, test_user, api_client):
        user, _token = test_user
        resp = auth_client.post(
            "/api/users/changePsw",
            {"old_password": "Test123456", "new_password": "NewPass123456"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == 200
        user.refresh_from_db()
        assert user.check_password("NewPass123456")

        # 新密码可直接登录
        login = api_client.post(
            "/api/users/login/",
            {"account": user.mobile, "password": "NewPass123456"},
            format="json",
        )
        assert login.json()["code"] == 200

    def test_change_psw_wrong_old_password(self, auth_client):
        resp = auth_client.post(
            "/api/users/changePsw",
            {"old_password": "WrongOld123", "new_password": "NewPass123456"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == 1002

    def test_change_psw_weak_new_password(self, auth_client):
        resp = auth_client.post(
            "/api/users/changePsw",
            {"oldPassword": "Test123456", "newPassword": "123"},
            format="json",
        )
        assert resp.json()["code"] == 1001

    def test_change_psw_requires_auth(self, api_client):
        resp = api_client.post(
            "/api/users/changePsw",
            {"old_password": "Test123456", "new_password": "NewPass123456"},
            format="json",
        )
        assert resp.status_code == 401


class TestMiscP1:
    """getLoginTipInfo / getPhoneCaptcha。"""

    def test_get_login_tip_info(self, auth_client):
        resp = auth_client.get("/api/users/getLoginTipInfo")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["tip_url"] == []

    def test_get_phone_captcha_no_auth(self, api_client, settings):
        settings.DEBUG = True  # DEBUG 下回显验证码，便于联调
        resp = api_client.get("/api/users/getPhoneCaptcha?phone=13900139000")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert len(body["data"]["captcha"]) == 6
        assert body["data"]["expires_in"] == 300

    def test_get_phone_captcha_invalid_phone(self, api_client):
        resp = api_client.get("/api/users/getPhoneCaptcha?phone=139")
        assert resp.status_code == 200
        assert resp.json()["code"] == 1001

    def test_captcha_roundtrip(self, api_client, auth_client, test_user, settings):
        """下发验证码 -> 用验证码提交资料：正确放行、错误返回 1002。"""
        user, _token = test_user
        settings.DEBUG = True
        phone = user.mobile
        captcha = api_client.get(f"/api/users/getPhoneCaptcha?phone={phone}").json()["data"]["captcha"]

        bad = auth_client.post(
            "/api/users/editCustomerInfos",
            {"customerName": "验证码错误", "phone": phone, "captcha": "000000"},
            format="json",
        )
        assert bad.json()["code"] == 1002

        ok = auth_client.post(
            "/api/users/editCustomerInfos",
            {"customerName": "验证码正确", "phone": phone, "captcha": captcha},
            format="json",
        )
        assert ok.json()["code"] == 200
        assert CustomerProfile.objects.get(user=user).company_name == "验证码正确"
