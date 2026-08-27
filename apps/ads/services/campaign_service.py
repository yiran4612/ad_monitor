# Layer: service
from django.db import transaction
from django.db.models import QuerySet

from apps.ads.exceptions import AdvertiserNotFound, CampaignNotFound
from apps.ads.models import Advertiser, Campaign


class CampaignService:

    @staticmethod
    def _get_active(campaign_id) -> Campaign:
        try:
            return Campaign.objects.get(id=campaign_id, is_deleted=False)
        except Campaign.DoesNotExist:
            raise CampaignNotFound(campaign_id)

    @staticmethod
    @transaction.atomic
    def create_campaign(data: dict) -> Campaign:
        payload = dict(data)
        advertiser_id = payload.pop("advertiser")
        try:
            Advertiser.objects.get(id=advertiser_id, is_deleted=False)
        except Advertiser.DoesNotExist:
            raise AdvertiserNotFound(advertiser_id)
        return Campaign.objects.create(advertiser_id=advertiser_id, **payload)

    @staticmethod
    @transaction.atomic
    def update_campaign_status(campaign_id, status) -> Campaign:
        campaign = CampaignService._get_active(campaign_id)
        campaign.status = status
        campaign.save(update_fields=["status", "updated_at"])
        return campaign

    @staticmethod
    def list_campaigns_by_advertiser(advertiser_id) -> QuerySet:
        return Campaign.objects.filter(advertiser_id=advertiser_id, is_deleted=False)
