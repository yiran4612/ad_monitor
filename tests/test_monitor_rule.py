import uuid

import pytest

from apps.ads.models import MonitorRule


@pytest.mark.django_db
class TestMonitorRule:
    def test_list_monitor_rules(self, auth_client):
        resp = auth_client.get("/api/ads/monitor-rules/")
        assert resp.status_code == 200
        assert resp.json()["code"] == 200
        assert "results" in resp.json()["data"]

    def test_create_monitor_rule(self, auth_client, test_advertiser):
        resp = auth_client.post(
            "/api/ads/monitor-rules/",
            {
                "advertiser": str(test_advertiser.id),
                "rule_type": "keyword",
                "keyword": "竞品B",
                "is_active": True,
            },
            format="json",
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["keyword"] == "竞品B"
        assert data["advertiser"]["id"] == str(test_advertiser.id)
        assert MonitorRule.objects.filter(pk=data["id"]).exists()

    def test_list_monitor_rules_by_advertiser(self, auth_client, test_advertiser, test_rule):
        # 同广告主的一条未启用规则，不应出现在过滤结果中
        MonitorRule.objects.create(
            advertiser=test_advertiser,
            rule_type="custom",
            keyword="未启用规则",
            is_active=False,
        )
        resp = auth_client.get(f"/api/ads/monitor-rules/?advertiser_id={test_advertiser.id}")
        assert resp.status_code == 200
        ids = [item["id"] for item in resp.json()["data"]["results"]]
        assert str(test_rule.id) in ids
        assert all(item["is_active"] for item in resp.json()["data"]["results"])

    def test_list_monitor_rules_advertiser_not_found(self, auth_client):
        resp = auth_client.get(f"/api/ads/monitor-rules/?advertiser_id={uuid.uuid4()}")
        assert resp.status_code == 400
        assert resp.json()["msg"] == "广告主不存在"

    def test_create_monitor_rule_advertiser_not_found(self, auth_client):
        resp = auth_client.post(
            "/api/ads/monitor-rules/",
            {
                "advertiser": str(uuid.uuid4()),
                "rule_type": "keyword",
                "keyword": "竞品C",
            },
            format="json",
        )
        assert resp.status_code == 400
        assert resp.json()["msg"] == "广告主不存在"

    def test_create_invalid_rule_type(self, auth_client, test_advertiser):
        resp = auth_client.post(
            "/api/ads/monitor-rules/",
            {
                "advertiser": str(test_advertiser.id),
                "rule_type": "bogus_type",
                "keyword": "竞品D",
            },
            format="json",
        )
        assert resp.status_code == 400
