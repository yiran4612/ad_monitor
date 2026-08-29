# Layer: service
"""广告平台位 Mock 服务（/element/advPlatform/*）。"""

from django.db import transaction

from apps.ads.exceptions import AdvPlatformNotFound
from apps.ads.models import AdvPlatform


class AdvPlatformService:
    @staticmethod
    def _get(element_id) -> AdvPlatform:
        try:
            return AdvPlatform.objects.get(id=element_id, is_deleted=False)
        except AdvPlatform.DoesNotExist as e:
            raise AdvPlatformNotFound(element_id) from e

    @staticmethod
    def list_platforms(page: int = 1, page_size: int = 10) -> dict:
        queryset = AdvPlatform.objects.filter(is_deleted=False)
        total = queryset.count()
        offset = (page - 1) * page_size
        platforms = queryset[offset : offset + page_size]
        return {"total": total, "list": [AdvPlatformService.to_payload(p) for p in platforms]}

    @staticmethod
    @transaction.atomic
    def add_platform(data: dict, cname: str = "") -> AdvPlatform:
        payload = dict(data)
        payload.setdefault("cname", cname)
        return AdvPlatform.objects.create(**payload)

    @staticmethod
    @transaction.atomic
    def update_platform(element_id, data: dict) -> AdvPlatform:
        platform = AdvPlatformService._get(element_id)
        for field in (
            "epg_name",
            "element_name",
            "element_type",
            "element_url",
            "hot_img_url",
            "dulation",
            "byte_rate",
            "frame_rate",
            "definition",
            "file_size",
            "ext",
            "md_5",
        ):
            if field in data:
                setattr(platform, field, data[field])
        platform.save(update_fields=[f for f in data if f != "element_id"] + ["updated_at"])
        return platform

    @staticmethod
    @transaction.atomic
    def delete_platform(element_id) -> None:
        platform = AdvPlatformService._get(element_id)
        platform.is_deleted = True
        platform.save(update_fields=["is_deleted", "updated_at"])

    @staticmethod
    @transaction.atomic
    def update_lock(element_id, is_locked: bool) -> AdvPlatform:
        platform = AdvPlatformService._get(element_id)
        platform.is_locked = is_locked
        platform.save(update_fields=["is_locked", "updated_at"])
        return platform

    @staticmethod
    def to_payload(platform: AdvPlatform) -> dict:
        return {
            "element_id": platform.id,
            "epgName": platform.epg_name,
            "element_name": platform.element_name,
            "contentType": platform.element_type,
            "elementUrl": platform.element_url,
            "hotImgUrl": platform.hot_img_url,
            "vedioUrl": platform.element_url if platform.element_type == AdvPlatform.ElementType.VIDEO else "",
            "dulation": platform.dulation,
            "byte_rate": platform.byte_rate,
            "frame_rate": platform.frame_rate,
            "definition": platform.definition,
            "file_size": platform.file_size,
            "ext": platform.ext,
            "md_5": platform.md_5,
            "is_locked": platform.is_locked,
            "cname": platform.cname,
            "createTime": platform.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
