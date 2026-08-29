# Layer: model
"""广告平台位（Mock）。

对应前端 ``/element/advPlatform/*`` 系列接口（广告上传/已有广告列表）。
字段命名对齐前端 ``ADManage`` 页面的 snake_case 提交参数：
``epg_name / element_type / dulation / definition / md_5 ...``。
"""

from django.db import models


class AdvPlatform(models.Model):
    class ElementType(models.IntegerChoices):
        IMAGE = 0, "图片"
        VIDEO = 1, "视频"

    id = models.AutoField(primary_key=True, verbose_name="平台位ID")
    epg_name = models.CharField(max_length=200, verbose_name="广告名称")
    element_name = models.CharField(max_length=255, blank=True, verbose_name="文件名")
    element_type = models.IntegerField(
        choices=ElementType.choices,
        default=ElementType.VIDEO,
        verbose_name="素材类型",
    )
    element_url = models.URLField(blank=True, verbose_name="素材地址")
    hot_img_url = models.URLField(blank=True, verbose_name="封面图地址")
    dulation = models.IntegerField(default=0, verbose_name="时长(秒)")
    byte_rate = models.IntegerField(default=0, verbose_name="码率")
    frame_rate = models.IntegerField(default=0, verbose_name="帧率")
    definition = models.CharField(max_length=32, blank=True, verbose_name="分辨率")
    file_size = models.BigIntegerField(default=0, verbose_name="文件大小(字节)")
    ext = models.CharField(max_length=16, blank=True, verbose_name="扩展名")
    md_5 = models.CharField(max_length=64, blank=True, verbose_name="文件MD5")
    is_locked = models.BooleanField(default=False, verbose_name="是否锁定")
    cname = models.CharField(max_length=64, blank=True, verbose_name="上传人")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    is_deleted = models.BooleanField(default=False, verbose_name="软删除")

    class Meta:
        db_table = "ads_adv_platform"
        verbose_name = "广告平台位"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]

    def __str__(self):
        return self.epg_name
