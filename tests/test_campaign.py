import pytest

from apps.ads.models import Campaign

pytestmark = pytest.mark.django_db


class TestCampaignStatus:
    """活动状态流转边界（Creative 无 approve/reject，改测实际存在的
    PATCH /api/ads/campaigns/{id}/status/ action）。
    """

    # ===== 合法状态变更 -> 200，状态写库 =====
    def test_update_campaign_status_success(self, auth_client, test_campaign):
        resp = auth_client.patch(
            f"/api/ads/campaigns/{test_campaign.id}/status/",
            {"status": "paused"},
            format="json",
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert body["msg"] == "状态更新成功"
        assert body["data"]["status"] == "paused"
        test_campaign.refresh_from_db()
        assert test_campaign.status == "paused"

    # ===== 非法状态值 -> 400（ChoiceField 校验拦截）=====
    def test_update_campaign_status_invalid_value(self, auth_client, test_campaign):
        resp = auth_client.patch(
            f"/api/ads/campaigns/{test_campaign.id}/status/",
            {"status": "active"},
            format="json",
        )
        assert resp.status_code == 400

    # ===== 活动不存在 -> 404 =====
    def test_update_campaign_status_not_found(self, auth_client):
        resp = auth_client.patch(
            "/api/ads/campaigns/00000000-0000-0000-0000-000000000000/status/",
            {"status": "paused"},
            format="json",
        )
        assert resp.status_code == 404
        assert "活动不存在" in resp.json()["msg"]

    # ===== 软删除活动 -> 404（Service 层过滤 is_deleted）=====
    def test_update_campaign_status_soft_deleted(self, auth_client, test_advertiser):
        deleted = Campaign.objects.create(
            advertiser=test_advertiser,
            title="已删活动",
            platform="douyin",
            budget=1,
            start_date="2025-06-01",
            end_date="2025-06-30",
            status="running",
            is_deleted=True,
        )
        resp = auth_client.patch(
            f"/api/ads/campaigns/{deleted.id}/status/",
            {"status": "paused"},
            format="json",
        )
        assert resp.status_code == 404
        deleted.refresh_from_db()
        assert deleted.status == "running"
