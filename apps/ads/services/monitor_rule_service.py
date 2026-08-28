# Layer: service
import uuid

from django.db import transaction
from django.db.models import QuerySet

from apps.ads.exceptions import AdvertiserNotFound
from apps.ads.models import Advertiser, MonitorRule


class MonitorRuleService:
    @staticmethod
    def _to_advertiser_id(advertiser_id) -> uuid.UUID:
        """字符串/UUID 统一转 UUID，非法值视为广告主不存在。"""
        try:
            return uuid.UUID(str(advertiser_id))
        except (ValueError, AttributeError, TypeError) as e:
            raise AdvertiserNotFound(advertiser_id) from e

    @staticmethod
    @transaction.atomic
    def create_rule(data: dict) -> MonitorRule:
        payload = dict(data)
        advertiser_id = payload.pop("advertiser")
        advertiser_uuid = MonitorRuleService._to_advertiser_id(advertiser_id)
        try:
            Advertiser.objects.get(id=advertiser_uuid, is_deleted=False)
        except Advertiser.DoesNotExist as e:
            raise AdvertiserNotFound(advertiser_uuid) from e
        return MonitorRule.objects.create(advertiser_id=advertiser_uuid, **payload)

    @staticmethod
    def list_active_rules_by_advertiser(advertiser_id) -> QuerySet:
        advertiser_uuid = MonitorRuleService._to_advertiser_id(advertiser_id)
        if not Advertiser.objects.filter(id=advertiser_uuid, is_deleted=False).exists():
            raise AdvertiserNotFound(advertiser_uuid)
        return MonitorRule.objects.filter(advertiser_id=advertiser_uuid, is_active=True)
