import pytest

@pytest.mark.django_db
class TestAdvertiser:
    def test_list_advertisers(self, auth_client):
        resp = auth_client.get("/api/ads/advertisers/")
        assert resp.status_code == 200
        assert resp.json()["code"] == 200

    def test_create_advertiser(self, auth_client):
        resp = auth_client.post("/api/ads/advertisers/", {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "测试广告主B",
            "status": "active",
            "contact_mobile": "13900139004",
            "created_at": "2025-06-15T14:30:00Z",
            "updated_at": "2025-06-15T14:30:00Z",
        }, format="json")
        assert resp.status_code in (200, 201)
        assert resp.json()["data"]["name"] == "测试广告主B"

    def test_get_advertiser(self, auth_client, test_advertiser):
        resp = auth_client.get(f"/api/ads/advertisers/{test_advertiser.id}/")
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "测试广告主"

    def test_update_advertiser(self, auth_client, test_advertiser):
        resp = auth_client.patch(
            f"/api/ads/advertisers/{test_advertiser.id}/",
            {"name": "已更新广告主", "contact_mobile": "13900139000",},
            format="json"
        )
        print("UPDATE STATUS:", resp.status_code)
        print("UPDATE BODY:", resp.json())
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "已更新广告主"

    def test_delete_advertiser(self, auth_client, test_advertiser):
        resp = auth_client.delete(f"/api/ads/advertisers/{test_advertiser.id}/")
        assert resp.status_code in (200, 204)