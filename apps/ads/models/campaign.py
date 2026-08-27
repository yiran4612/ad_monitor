# Layer: model
import uuid

from django.db import models


class Campaign(models.Model):
    class Platform(models.TextChoices):
        DOUYIN = "douyin", "抖音"
        KUAISHOU = "kuaishou", "快手"
        TOUTIAO = "toutiao", "头条"
        WECHAT = "wechat", "微信"
        BILIBILI = "bilibili", "B站"
        OTHER = "other", "其他"

    class Status(models.TextChoices):
        DRAFT = "draft", "草稿"
        RUNNING = "running", "投放中"
        PAUSED = "paused", "已暂停"
        ENDED = "ended", "已结束"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    advertiser = models.ForeignKey(
        "Advertiser",
        on_delete=models.CASCADE,
        related_name="campaigns",
        verbose_name="广告主",
    )
    title = models.CharField(max_length=200, verbose_name="活动标题")
    platform = models.CharField(
        max_length=16,
        choices=Platform.choices,
        default=Platform.OTHER,
        verbose_name="投放平台",
    )
    budget = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="预算")
    start_date = models.DateField(verbose_name="开始日期")
    end_date = models.DateField(verbose_name="结束日期")
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="状态",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    is_deleted = models.BooleanField(default=False, verbose_name="软删除")

    class Meta:
        db_table = "ads_campaign"
        verbose_name = "广告活动"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
