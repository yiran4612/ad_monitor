# Layer: service
"""
视频违规检测业务逻辑（由 Celery 任务 apps.ads.tasks.detect_video_task 调用）。

链路：Campaign → 取广告主启用中的 keyword 规则 → 取待检文本 → 逐条匹配 →
命中则经 ViolationService 写入 ViolationRecord。

说明：
- fetch_video_text 为可替换的取文本缝（seam）：当前返回 URL 本身作占位，
  生产环境应替换为 下载视频 + ASR/OCR 管道（封装在本 Service 内，禁止外部依赖
  直接渗入 Task/View 层）；
- 规则匹配为纯函数式 keyword in text，无外部 AI 依赖。
"""

from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from apps.ads.models import Campaign, Creative, MonitorRule
from apps.ads.services.violation_service import ViolationService


class DetectionService:
    # ──────────────────────────────────────────────
    # 查询：定时扫描的数据来源（只读）
    # ──────────────────────────────────────────────

    @staticmethod
    def list_active_campaigns() -> QuerySet:
        """投放中（RUNNING）且未软删除的活动。"""
        return Campaign.objects.filter(status=Campaign.Status.RUNNING, is_deleted=False)

    @staticmethod
    def list_video_creatives(campaign: Campaign) -> QuerySet:
        """活动下待检的视频素材：video 类型、未软删、地址非空。

        注：Creative 模型无 status 字段（approved/pending 不存在），
        故以 is_deleted + file_url 非空作为可检过滤条件。
        """
        return Creative.objects.filter(
            campaign=campaign,
            material_type=Creative.MaterialType.VIDEO,
            is_deleted=False,
        ).exclude(file_url="")

    @staticmethod
    def list_keyword_rules(campaign: Campaign) -> QuerySet:
        """该活动广告主启用中的关键词规则。"""
        return MonitorRule.objects.filter(
            advertiser=campaign.advertiser,
            is_active=True,
            rule_type=MonitorRule.RuleType.KEYWORD,
        )

    # ──────────────────────────────────────────────
    # 检测：取文本 + 规则匹配 + 写违规
    # ──────────────────────────────────────────────

    @staticmethod
    def fetch_video_text(video_url: str) -> str:
        """获取视频待检文本（占位实现，不发生任何网络下载）。

        生产替换点：下载视频 → ASR 转写 / OCR 关键帧，仍须封装在 Service 内。
        """
        return video_url or ""

    @staticmethod
    def match_keyword_rules(rules, text: str) -> list:
        """返回 keyword 命中 text 的规则列表。"""
        if not text:
            return []
        return [r for r in rules if r.keyword and r.keyword in text]

    @staticmethod
    @transaction.atomic
    def run_video_detection(campaign: Campaign, video_url: str) -> dict:
        """对单个视频执行规则检测，命中则写 ViolationRecord（经 ViolationService）。"""
        rules = list(DetectionService.list_keyword_rules(campaign))
        if not rules:
            return {"status": "no_rules", "matched_rules": [], "violation_ids": []}

        text = DetectionService.fetch_video_text(video_url)
        matched = DetectionService.match_keyword_rules(rules, text)
        if not matched:
            return {"status": "clean", "matched_rules": [], "violation_ids": []}

        violation_ids = []
        for rule in matched:
            violation = ViolationService.create_violation(
                {
                    "campaign": str(campaign.id),
                    "rule": str(rule.id),
                    "description": f"[自动检测] 视频 {video_url} 命中关键词「{rule.keyword}」",
                    "screenshot_url": "",
                    "detected_at": timezone.now(),
                    "resolved": False,
                }
            )
            violation_ids.append(str(violation.id))

        return {
            "status": "violation_found",
            "matched_rules": [r.keyword for r in matched],
            "violation_ids": violation_ids,
        }
