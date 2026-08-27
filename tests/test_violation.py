import pytest
from apps.ads.models import ViolationRecord

pytestmark = pytest.mark.django_db


class TestViolation:

    # ========== 创建违规记录 ==========
    def test_create_violation(self, auth_client, test_campaign, test_rule):
        resp = auth_client.post("/api/ads/violations/", {
            "campaign": str(test_campaign.id),
            "rule": str(test_rule.id),
            "description": "检测到违规内容",
            "detected_at": "2025-06-15T14:30:00Z",
            "resolved": False,
        }, format="json")
        assert resp.status_code in (200, 201)

    # ========== 列出违规记录 ==========
    def test_list_violations(self, auth_client, test_campaign, test_rule):
        ViolationRecord.objects.create(
            campaign=test_campaign,
            rule=test_rule,                     # ← 必填，NOT NULL
            description="已有违规",
            detected_at="2025-06-15T14:30:00Z",
            resolved=False,
        )
        resp = auth_client.get("/api/ads/violations/")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1

    # ========== 处理违规 ==========
    def test_resolve_violation(self, auth_client, test_campaign, test_rule):
        v = ViolationRecord.objects.create(
            campaign=test_campaign,
            rule=test_rule,                     # ← 必填，NOT NULL
            description="待处理违规",
            detected_at="2025-06-15T14:30:00Z",
            resolved=False,
        )
        resp = auth_client.patch(f"/api/ads/violations/{v.id}/resolve/")
        assert resp.status_code == 200
        assert resp.json()["data"]["resolved"] is True

    # ========== 重复处理应返回 400 ==========
    def test_resolve_already_resolved(self, auth_client, test_campaign, test_rule):
        v = ViolationRecord.objects.create(
            campaign=test_campaign,
            rule=test_rule,                     # ← 必填，NOT NULL
            description="已处理违规",
            detected_at="2025-06-15T14:30:00Z",
            resolved=True,
        )
        resp = auth_client.patch(f"/api/ads/violations/{v.id}/resolve/")
        assert resp.status_code == 400
        assert "已处理" in resp.json()["msg"]