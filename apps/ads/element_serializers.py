# Layer: api
"""P2 素材查询 / 广告平台 / 楼宇接口的入参序列化器。

分页参数同时兼容两套命名：
- 规格命名：``page`` / ``page_size``
- 前端实际传参：``pageNum`` / ``pageSize``
"""

from rest_framework import serializers

from apps.ads.models import AdvPlatform, Building, Creative


def _page_of(data: dict, *keys: str, default: int) -> int:
    """按优先级取第一个存在的分页参数。"""
    for key in keys:
        if data.get(key) is not None:
            return data[key]
    return default


class PaginationSerializer(serializers.Serializer):
    """分页参数基类：兼容 ``page/page_size`` 与 ``pageNum/pageSize`` 两套命名。"""

    page = serializers.IntegerField(required=False, min_value=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100)
    pageNum = serializers.IntegerField(required=False, min_value=1)
    pageSize = serializers.IntegerField(required=False, min_value=1, max_value=100)

    @property
    def effective_page(self) -> int:
        return _page_of(self.validated_data, "page", "pageNum", default=1)

    @property
    def effective_page_size(self) -> int:
        return _page_of(self.validated_data, "page_size", "pageSize", default=10)


class CreativeQuerySerializer(PaginationSerializer):
    """``GET /element/content/query`` 与 ``GET /user/adElementList`` 公共参数。"""

    id = serializers.UUIDField(required=False, help_text="素材ID（传入则走详情模式）")
    campaign_id = serializers.UUIDField(required=False, help_text="广告活动ID")
    status = serializers.ChoiceField(choices=Creative.Status.choices, required=False)
    material_type = serializers.ChoiceField(choices=Creative.MaterialType.choices, required=False)


class CreativeUploadSerializer(serializers.Serializer):
    """``POST /element/content/upload`` 表单参数（file 由 View 直接从 FILES 取）。"""

    material_type = serializers.ChoiceField(
        choices=[Creative.MaterialType.IMAGE, Creative.MaterialType.VIDEO],
        required=False,
        help_text="素材类型（image|video，默认 image；uploadImage/uploadVideo 路由会强制覆盖）",
    )
    campaign_id = serializers.UUIDField(required=False, help_text="广告活动ID（可选）")
    name = serializers.CharField(required=False, max_length=200, allow_blank=True, help_text="素材名")


class AdvPlatformSaveSerializer(serializers.Serializer):
    """``POST /element/advPlatform/add`` 与 ``/edit`` 公共参数（edit 需 element_id）。"""

    element_id = serializers.IntegerField(required=False, min_value=1)
    epg_name = serializers.CharField(required=False, max_length=200)
    element_name = serializers.CharField(required=False, max_length=255)
    element_type = serializers.ChoiceField(choices=AdvPlatform.ElementType.choices, required=False)
    element_url = serializers.URLField(required=False)
    hot_img_url = serializers.URLField(required=False)
    dulation = serializers.IntegerField(required=False, min_value=0)
    byte_rate = serializers.IntegerField(required=False, min_value=0)
    frame_rate = serializers.IntegerField(required=False, min_value=0)
    definition = serializers.CharField(required=False, max_length=32)
    file_size = serializers.IntegerField(required=False, min_value=0)
    ext = serializers.CharField(required=False, max_length=16)
    md_5 = serializers.CharField(required=False, max_length=64)


class AdvPlatformDeleteSerializer(serializers.Serializer):
    element_id = serializers.IntegerField(required=True, min_value=1)


class AdvPlatformLockSerializer(serializers.Serializer):
    element_id = serializers.IntegerField(required=True, min_value=1)
    is_locked = serializers.BooleanField(required=True)


class BuildingQuerySerializer(PaginationSerializer):
    """``GET /user/getAllLy`` 与 ``GET /user/getSelectedLy`` 公共参数。"""

    search = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)


class BuildingItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = ["id", "name", "address", "is_selected"]
