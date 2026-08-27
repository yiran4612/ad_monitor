# Layer: task
"""
Celery 异步任务：视频违规检测 + 定时扫描。

- detect_video_task：单个视频检测（规则匹配 → 写 ViolationRecord），业务逻辑
  委托 DetectionService，本层只做进度上报与异常转结果；
- scan_campaigns_task：定时扫描投放中活动的视频素材，逐个触发 detect_video_task；
- process_creative_task：素材异步后处理（CreativeService.create_creative 触发）。
"""
from celery import shared_task

from apps.ads.models import Campaign, Creative

# 注意：DetectionService 采用函数内延迟导入——creative_service 模块级导入了
# process_creative_task（既有测试在导入处 mock，不可改），tasks 模块级再导入
# services 包会形成循环导入（tasks → services/__init__ → creative_service → tasks）。


def _detection_service():
    from apps.ads.services.detection_service import DetectionService
    return DetectionService


@shared_task(bind=True, name="ads.detect_video")
def detect_video_task(self, campaign_id=None, video_url=None):
    """检测单个视频：Campaign 校验 → 规则匹配 → 命中写 ViolationRecord。"""
    self.update_state(state="PROGRESS", meta={"step": "loading", "progress": 10})
    try:
        campaign = Campaign.objects.get(id=campaign_id, is_deleted=False)
    except Campaign.DoesNotExist:
        return {"status": "error", "detail": f"活动不存在: {campaign_id}"}

    self.update_state(state="PROGRESS", meta={"step": "analyzing", "progress": 50})
    try:
        result = _detection_service().run_video_detection(campaign, video_url)
    except Exception as e:  # 任务层兜底：异常转结构化结果，不让 Worker 崩
        return {"status": "error", "detail": str(e)}

    self.update_state(state="PROGRESS", meta={"step": "done", "progress": 100})
    return result


@shared_task(name="ads.scan_campaigns")
def scan_campaigns_task():
    """定时扫描：投放中活动的视频素材 → 逐个触发 detect_video_task。

    返回 {scanned_campaigns, triggered_tasks}。
    """
    detection = _detection_service()
    scanned_campaigns = 0
    triggered_tasks = 0

    for campaign in detection.list_active_campaigns():
        scanned_campaigns += 1
        for creative in detection.list_video_creatives(campaign):
            detect_video_task.delay(str(campaign.id), creative.file_url)
            triggered_tasks += 1

    return {
        "scanned_campaigns": scanned_campaigns,
        "triggered_tasks": triggered_tasks,
    }


@shared_task(bind=True, name="ads.process_creative")
def process_creative_task(self, creative_id=None):
    """素材异步后处理：视频探测时长 / 图片校验 / 文本审核。

    由 CreativeService.create_creative 触发；测试中在导入处 mock，不实际执行。
    """
    self.update_state(state="PROGRESS", meta={"step": "probing", "progress": 30})
    try:
        creative = Creative.objects.get(id=creative_id, is_deleted=False)
    except Creative.DoesNotExist:
        return {"status": "error", "detail": f"素材不存在: {creative_id}"}

    # 视频素材且未设时长：模拟探测（实际应调 ffprobe 等外部能力）
    if creative.material_type == "video" and creative.duration is None:
        creative.duration = 30
        creative.save(update_fields=["duration", "updated_at"])

    self.update_state(state="PROGRESS", meta={"step": "done", "progress": 100})
    return {
        "creative_id": str(creative.id),
        "status": "processed",
        "material_type": creative.material_type,
    }
