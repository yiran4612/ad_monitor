# Layer: model
import uuid

from django.db import models


class Creative(models.Model):
    class MaterialType(models.TextChoices):
        VIDEO = "video", "视频"
        IMAGE = "image", "图片"
        TEXT = "text", "图文"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(
        "Campaign",
        on_delete=models.CASCADE,
        related_name="creatives",
        verbose_name="广告活动",
    )
    name = models.CharField(max_length=200, verbose_name="素材名称")
    material_type = models.CharField(
        max_length=16,
        choices=MaterialType.choices,
        verbose_name="素材类型",
    )
    file_url = models.URLField(blank=True, verbose_name="素材地址")
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
