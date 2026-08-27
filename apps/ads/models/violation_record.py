# Layer: model
import uuid

from django.db import models


class ViolationRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(
        "Campaign",
        on_delete=models.CASCADE,
        related_name="violation_records",
        verbose_name="广告活动",
    )
    rule = models.ForeignKey(
        "MonitorRule",
        on_delete=models.CASCADE,
        related_name="violation_records",
        verbose_name="监控规则",
    )
    description = models.TextField(verbose_name="违规描述")
    screenshot_url = models.URLField(blank=True, verbose_name="截图地址")
    detected_at = models.DateTimeField(verbose_name="检测时间")
    resolved = models.BooleanField(default=False, verbose_name="是否已处理")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "ads_violation_record"
        verbose_name = "违规记录"
        verbose_name_plural = verbose_name
        ordering = ["-detected_at"]

    def __str__(self):
        return f"{self.campaign} - {self.detected_at}"
