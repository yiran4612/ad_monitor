# Layer: model
"""楼宇（Mock）。

对应前端 ``/user/getAllLy``（可选楼宇）与 ``/user/getSelectedLy``（已选楼宇）。
"""

from django.db import models


class Building(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="楼宇ID")
    name = models.CharField(max_length=200, verbose_name="楼宇名称")
    address = models.CharField(max_length=255, blank=True, verbose_name="地址")
    is_selected = models.BooleanField(default=False, verbose_name="是否已选投放")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    is_deleted = models.BooleanField(default=False, verbose_name="软删除")

    class Meta:
        db_table = "ads_building"
        verbose_name = "楼宇"
        verbose_name_plural = verbose_name
        ordering = ["id"]

    def __str__(self):
        return self.name
