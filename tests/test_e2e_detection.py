"""E2E 检测链路测试：scan_campaigns_task → detect_video_task → ViolationRecord。

约定：
- scan 测试在导入处 patch detect_video_task，只验证触发行为，不实际执行检测；
- "真实链路"测试直接调用任务函数体（不下载任何外部资源：
  DetectionService.fetch_video_text 默认返回 URL 本身），并 mock
  update_state 以避免触碰 Redis result backend。
"""
import uuid

import pytest
from unittest.mock import patch

from apps.ads.models import Campaign, Creative, ViolationRecord
from apps.ads.tasks import detect_video_task, scan_campaigns_task

pytestmark = pytest.mark.django_db

VIDEO_URL = "https://example.com/videos/竞品A_promo.mp4"


@pytest.fixture
def test_running_campaign(test_advertiser):
    """投放中（RUNNING）活动——定时扫描的目标状态。

    注：Campaign.Status 无 "active"，投放中对应 RUNNING。
    """
    return Campaign.objects.create(
        advertiser=test_advertiser,
        title="投放中的活动",
        platform="douyin",
        budget=5000.00,
        start_date="2026-08-01",
        end_date="2026-08-31",
        status=Campaign.Status.RUNNING,
    )


@pytest.fixture
def test_video_creative(test_running_campaign):
    """待检视频素材：URL 中包含规则关键词（占位取文本实现直接匹配 URL）。"""
    return Creative.objects.create(
        campaign=test_running_campaign,
        name="竞品A宣传视频",
        material_type=Creative.MaterialType.VIDEO,
        file_url=VIDEO_URL,
    )


class TestScanCampaigns:
    """scan_campaigns_task：扫描 active(RUNNING) Campaign + 视频 Creative → 触发检测。"""

    @patch("apps.ads.tasks.detect_video_task")
    def test_scan_triggers_detect_exactly_once(
        self, mock_detect, test_running_campaign, test_video_creative
    ):
        result = scan_campaigns_task()

        mock_detect.delay.assert_called_once_with(
            str(test_running_campaign.id), VIDEO_URL
        )
        assert result == {"scanned_campaigns": 1, "triggered_tasks": 1}

    @patch("apps.ads.tasks.detect_video_task")
    def test_scan_skips_non_running_campaign(self, mock_detect, test_advertiser):
        Campaign.objects.create(
            advertiser=test_advertiser,
            title="草稿活动",
            platform="douyin",
            budget=100.00,
            start_date="2026-08-01",
            end_date="2026-08-31",
            status=Campaign.Status.DRAFT,
        )

        result = scan_campaigns_task()

        mock_detect.delay.assert_not_called()
        assert result == {"scanned_campaigns": 0, "triggered_tasks": 0}

    @patch("apps.ads.tasks.detect_video_task")
    def test_scan_skips_image_soft_deleted_and_empty_url_creatives(
        self, mock_detect, test_running_campaign
    ):
        # 图片素材：不检测
        Creative.objects.create(
            campaign=test_running_campaign,
            name="海报",
            material_type=Creative.MaterialType.IMAGE,
            file_url="https://example.com/poster.png",
        )
        # 软删除的视频：不检测
        Creative.objects.create(
            campaign=test_running_campaign,
            name="已删除视频",
            material_type=Creative.MaterialType.VIDEO,
            file_url="https://example.com/deleted.mp4",
            is_deleted=True,
        )
        # 无地址的视频：不检测
        Creative.objects.create(
            campaign=test_running_campaign,
            name="无地址视频",
            material_type=Creative.MaterialType.VIDEO,
            file_url="",
        )

        result = scan_campaigns_task()

        mock_detect.delay.assert_not_called()
        assert result == {"scanned_campaigns": 1, "triggered_tasks": 0}


class TestDetectVideoTask:
    """detect_video_task：规则匹配 → 命中写 ViolationRecord（真实链路，无外部下载）。"""

    def test_writes_violation_on_keyword_hit(
        self, test_running_campaign, test_rule
    ):
        # update_state 会写 result backend（Redis），测试中打桩隔离
        with patch.object(detect_video_task, "update_state"):
            result = detect_video_task(
                campaign_id=str(test_running_campaign.id),
                video_url=VIDEO_URL,
            )

        assert result["status"] == "violation_found"
        assert result["matched_rules"] == ["竞品A"]
        assert len(result["violation_ids"]) == 1

        assert ViolationRecord.objects.count() == 1
        violation = ViolationRecord.objects.first()
        assert str(violation.campaign_id) == str(test_running_campaign.id)
        assert str(violation.rule_id) == str(test_rule.id)
        assert violation.resolved is False
        assert "竞品A" in violation.description

    def test_clean_when_no_keyword_match(
        self, test_running_campaign, test_advertiser, test_video_creative
    ):
        from apps.ads.models import MonitorRule

        MonitorRule.objects.create(
            advertiser=test_advertiser,
            rule_type=MonitorRule.RuleType.KEYWORD,
            keyword="绝不命中的关键词",
            is_active=True,
        )

        with patch.object(detect_video_task, "update_state"):
            result = detect_video_task(
                campaign_id=str(test_running_campaign.id),
                video_url=VIDEO_URL,
            )

        assert result["status"] == "clean"
        assert result["violation_ids"] == []
        assert ViolationRecord.objects.count() == 0

    def test_no_rules_returns_no_rules(self, test_running_campaign):
        with patch.object(detect_video_task, "update_state"):
            result = detect_video_task(
                campaign_id=str(test_running_campaign.id),
                video_url=VIDEO_URL,
            )

        assert result["status"] == "no_rules"
        assert ViolationRecord.objects.count() == 0

    def test_campaign_not_found_returns_error(self, test_running_campaign):
        with patch.object(detect_video_task, "update_state"):
            result = detect_video_task(
                campaign_id=str(uuid.uuid4()),
                video_url=VIDEO_URL,
            )

        assert result["status"] == "error"
        assert "活动不存在" in result["detail"]
