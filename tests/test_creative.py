from unittest.mock import patch

import pytest

from apps.ads.models import Campaign, Creative

pytestmark = pytest.mark.django_db


def _results(resp):
    """兼容分页(dict)/非分页(list) 两种响应结构。"""
    data = resp.json()["data"]
    return data["results"] if isinstance(data, dict) else data


class TestCreative:
    def _payload(self, campaign, **overrides):
        payload = {
            "campaign": str(campaign.id),
            "name": "测试素材",
            "material_type": "video",
            "file_url": "https://example.com/test.mp4",
            "duration": None,
        }
        payload.update(overrides)
        return payload

    # ===== 创建：201 + Celery 任务被触发 =====
    @patch("apps.ads.services.creative_service.process_creative_task")
    def test_create_creative(self, mock_task, auth_client, test_campaign):
        resp = auth_client.post("/api/ads/creatives/", self._payload(test_campaign), format="json")
        assert resp.status_code == 201
        body = resp.json()
        assert body["code"] == 200
        assert body["msg"] == "创建成功"
        data = body["data"]
        assert data["name"] == "测试素材"
        assert data["material_type"] == "video"
        assert data["campaign"]["id"] == str(test_campaign.id)
        # Celery 任务在 Service 层被触发一次，参数为新建素材 id
        mock_task.delay.assert_called_once_with(data["id"])

    # ===== 图片素材创建：任务仍被触发（无条件后处理）=====
    @patch("apps.ads.services.creative_service.process_creative_task")
    def test_create_image_creative(self, mock_task, auth_client, test_campaign):
        resp = auth_client.post(
            "/api/ads/creatives/",
            self._payload(
                test_campaign,
                material_type="image",
                file_url="https://example.com/a.png",
            ),
            format="json",
        )
        assert resp.status_code == 201
        mock_task.delay.assert_called_once()

    # ===== 列表 =====
    def test_list_creatives(self, auth_client, test_campaign):
        Creative.objects.create(
            campaign=test_campaign,
            name="已有素材",
            material_type="image",
            file_url="https://example.com/x.png",
        )
        resp = auth_client.get("/api/ads/creatives/")
        assert resp.status_code == 200
        assert len(_results(resp)) >= 1

    # ===== 按 campaign_id 过滤 =====
    def test_list_by_campaign_filter(self, auth_client, test_campaign, test_advertiser):
        other = Campaign.objects.create(
            advertiser=test_advertiser,
            title="他活动",
            platform="douyin",
            budget=1,
            start_date="2025-06-01",
            end_date="2025-06-30",
            status="active",
        )
        Creative.objects.create(campaign=test_campaign, name="归属A", material_type="image")
        Creative.objects.create(campaign=other, name="归属B", material_type="image")
        resp = auth_client.get(f"/api/ads/creatives/?campaign_id={test_campaign.id}")
        assert resp.status_code == 200
        names = [r["name"] for r in _results(resp)]
        assert "归属A" in names
        assert "归属B" not in names

    # ===== 缺失 campaign -> 404，任务不触发 =====
    @patch("apps.ads.services.creative_service.process_creative_task")
    def test_create_missing_campaign(self, mock_task, auth_client):
        payload = {
            "campaign": "00000000-0000-0000-0000-000000000000",
            "name": "孤儿素材",
            "material_type": "video",
            "file_url": "https://example.com/x.mp4",
            "duration": None,
        }
        resp = auth_client.post("/api/ads/creatives/", payload, format="json")
        assert resp.status_code == 404
        assert "活动不存在" in resp.json()["msg"]
        mock_task.delay.assert_not_called()

    # ===== 非法 material_type -> 400，任务不触发 =====
    @patch("apps.ads.services.creative_service.process_creative_task")
    def test_create_invalid_material_type(self, mock_task, auth_client, test_campaign):
        resp = auth_client.post(
            "/api/ads/creatives/",
            self._payload(test_campaign, material_type="invalid"),
            format="json",
        )
        assert resp.status_code == 400
        mock_task.delay.assert_not_called()

    # ===== 软删除素材不出现在列表 =====
    def test_list_excludes_soft_deleted(self, auth_client, test_campaign):
        Creative.objects.create(campaign=test_campaign, name="存活", material_type="image")
        Creative.objects.create(campaign=test_campaign, name="已删", material_type="image", is_deleted=True)
        resp = auth_client.get("/api/ads/creatives/")
        names = [r["name"] for r in _results(resp)]
        assert "存活" in names
        assert "已删" not in names
