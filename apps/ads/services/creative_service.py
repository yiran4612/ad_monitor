# Layer: service
import uuid

from django.db import transaction
from django.db.models import QuerySet

from apps.ads.exceptions import CampaignNotFound, CreativeNotFound
from apps.ads.models import Campaign, Creative
from apps.ads.tasks import process_creative_task


class CreativeService:
    @staticmethod
    def _to_campaign_id(campaign_id) -> uuid.UUID:
        """字符串/UUID 统一转 UUID，非法值视为活动不存在。"""
        try:
            return uuid.UUID(str(campaign_id))
        except (ValueError, AttributeError, TypeError) as e:
            raise CampaignNotFound(campaign_id) from e

    @staticmethod
    def _to_creative_id(creative_id) -> uuid.UUID:
        """字符串/UUID 统一转 UUID，非法值视为素材不存在。"""
        try:
            return uuid.UUID(str(creative_id))
        except (ValueError, AttributeError, TypeError) as e:
            raise CreativeNotFound(creative_id) from e

    @staticmethod
    @transaction.atomic
    def create_creative(data: dict) -> Creative:
        payload = dict(data)
        campaign_id = payload.pop("campaign")
        campaign_uuid = CreativeService._to_campaign_id(campaign_id)
        try:
            Campaign.objects.get(id=campaign_uuid, is_deleted=False)
        except Campaign.DoesNotExist as e:
            raise CampaignNotFound(campaign_uuid) from e
        creative = Creative.objects.create(campaign_id=campaign_uuid, **payload)
        # SDK 隔离：异步后处理走 Celery 任务（视频探时长 / 素材校验），不阻塞写入
        process_creative_task.delay(str(creative.id))
        return creative

    @staticmethod
    def list_creatives_by_campaign(campaign_id) -> QuerySet:
        campaign_uuid = CreativeService._to_campaign_id(campaign_id)
        if not Campaign.objects.filter(id=campaign_uuid, is_deleted=False).exists():
            raise CampaignNotFound(campaign_uuid)
        return Creative.objects.filter(campaign_id=campaign_uuid, is_deleted=False)

    # ── P2：素材查询（content/query 与 adElementList 共用）──

    @staticmethod
    def get_creative(creative_id) -> Creative:
        """按 ID 取未删除素材，不存在（含非法 UUID）抛 CreativeNotFound。"""
        creative_uuid = CreativeService._to_creative_id(creative_id)
        try:
            return Creative.objects.get(id=creative_uuid, is_deleted=False)
        except Creative.DoesNotExist as e:
            raise CreativeNotFound(creative_uuid) from e

    @staticmethod
    def query_creatives(
        campaign_id=None,
        status=None,
        material_type=None,
        page: int = 1,
        page_size: int = 10,
    ) -> dict:
        """多条件分页查询素材，返回 ``{count, results}``（P2 规格）。

        ``campaign_id`` 合法性在 Service 层校验（非法 UUID 抛 CampaignNotFound，
        由 View 转 1001 参数错误）。
        """
        queryset = Creative.objects.filter(is_deleted=False).select_related("campaign")

        if campaign_id:
            campaign_uuid = CreativeService._to_campaign_id(campaign_id)
            if not Campaign.objects.filter(id=campaign_uuid, is_deleted=False).exists():
                raise CampaignNotFound(campaign_uuid)
            queryset = queryset.filter(campaign_id=campaign_uuid)
        if status:
            queryset = queryset.filter(status=status)
        if material_type:
            queryset = queryset.filter(material_type=material_type)

        total = queryset.count()
        offset = (page - 1) * page_size
        creatives = queryset[offset : offset + page_size]
        return {"count": total, "results": [CreativeService.to_payload(c) for c in creatives]}

    @staticmethod
    def to_payload(creative: Creative) -> dict:
        """单条素材的对外结构：规格字段 + 前端 ADPutManage 页面别名字段。"""
        base = {
            # 规格字段
            "id": str(creative.id),
            "name": creative.name,
            "url": creative.file_url,
            "material_type": creative.material_type,
            "status": creative.status,
            "campaign_id": str(creative.campaign_id),
            "created_at": creative.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            # 前端别名字段（ADPutManage/index.vue 直接消费）
            "element_id": str(creative.id),
            "epgName": creative.name,
            "contentType": 0 if creative.material_type == Creative.MaterialType.IMAGE else 1,
            "dulation": creative.duration or 0,
            "definition": "",
            "hotImgUrl": creative.file_url,
            "vedioUrl": creative.file_url if creative.material_type == Creative.MaterialType.VIDEO else "",
            "createTime": creative.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        return base
