import pytest

@pytest.mark.django_db
class TestAuth:
    def test_register(self, api_client):
        resp = api_client.post("/api/users/register/", {
            "mobile": "13900139001",
            "password": "Test123456",
        }, format="json")
        assert resp.status_code in (200, 201)
        assert resp.json()["code"] == 200

    def test_login(self, api_client):
        # 先注册
        api_client.post("/api/users/register/", {
            "mobile": "13900139002",
            "password": "Test123456",
        }, format="json")
        # 再登录
        resp = api_client.post("/api/users/login/", {
            "mobile": "13900139002",
            "password": "Test123456",
        }, format="json")
        assert resp.status_code == 200
        assert "access" in resp.json()["data"] 

    def test_login_wrong_password(self, api_client):
        api_client.post("/api/users/register/", {
            "mobile": "13900139003",
            "password": "Test123456",
        }, format="json")
        resp = api_client.post("/api/users/login/", {
            "mobile": "13900139003",
            "password": "WrongPass123",
        }, format="json")
        assert resp.status_code in (400, 401)