# Layer: model
import uuid

from django.db import models


class MonitorRule(models.Model):
    class RuleType(models.TextChoices):
        KEYWORD = "keyword", "关键词"
        BUDGET_OVERRUN = "budget_overrun", "预算超支"
        PLATFORM_VIOLATION = "platform_violation", "平台违规"
        CUSTOM = "custom", "自定义"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    advertiser = models.ForeignKey(
        "Advertiser",
        on_delete=models.CASCADE,
        related_name="monitor_rules",
        verbose_name="广告主",
    )
    rule_type = models.CharField(
        max_length=32,
        choices=RuleType.choices,
        verbose_name="规则类型",
    )
    keyword = models.CharField(max_length=200, blank=True, verbose_name="关键词")
    threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="阈值",
    )
    is_active = models.BooleanField(default=True, verbose_name="是否启用")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "ads_monitor_rule"
        verbose_name = "监控规则"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_rule_type_display()} - {self.keyword}"
