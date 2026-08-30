# Layer: model
import uuid

from django.db import models


class Creative(models.Model):
    class MaterialType(models.TextChoices):
        VIDEO = "video", "视频"
        IMAGE = "image", "图片"
        TEXT = "text", "图文"

    class Status(models.TextChoices):
        PENDING = "pending", "审核中"
        APPROVED = "approved", "已通过"
        REJECTED = "rejected", "已驳回"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(
        "Campaign",
        on_delete=models.CASCADE,
        related_name="creatives",
        null=True,
        blank=True,
        verbose_name="广告活动",
    )
    name = models.CharField(max_length=200, verbose_name="素材名称")
    material_type = models.CharField(
        max_length=16,
        choices=MaterialType.choices,
        verbose_name="素材类型",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="审核状态",
    )
    file_url = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="素材地址",
        help_text="本地相对路径 /media/... 或完整 URL",
    )
    cover_url = models.CharField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="封面地址",
        help_text="视频封面图（本地相对路径，无则为空）",
    )
    duration = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="视频时长",
        help_text="视频时长秒",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    is_deleted = models.BooleanField(default=False, verbose_name="软删除")

    class Meta:
        db_table = "ads_creative"
        verbose_name = "广告素材"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
