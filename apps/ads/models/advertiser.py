# Layer: model
import uuid

from django.db import models


class Advertiser(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "正常"
        INACTIVE = "inactive", "停用"
        PAUSED = "paused", "暂停"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, verbose_name="广告主名称")
    contact_mobile = models.CharField(max_length=20, verbose_name="联系电话")
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="状态",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    is_deleted = models.BooleanField(default=False, verbose_name="软删除")

    class Meta:
        db_table = "ads_advertiser"
        verbose_name = "广告主"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
