# Layer: service
import uuid

from django.db import transaction
from django.db.models import QuerySet

from apps.ads.exceptions import CampaignNotFound
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
