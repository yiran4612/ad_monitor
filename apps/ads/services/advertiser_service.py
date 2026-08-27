# Layer: service
from django.db import transaction
from django.db.models import Q, QuerySet

from apps.ads.exceptions import AdvertiserNotFound
from apps.ads.models import Advertiser


class AdvertiserService:

    @staticmethod
    def _get_active(advertiser_id) -> Advertiser:
        try:
            return Advertiser.objects.get(id=advertiser_id, is_deleted=False)
        except Advertiser.DoesNotExist:
            raise AdvertiserNotFound(advertiser_id)

    @staticmethod
    @transaction.atomic
    def create_advertiser(data: dict) -> Advertiser:
        return Advertiser.objects.create(**data)

    @staticmethod
    @transaction.atomic
    def update_advertiser(advertiser_id, data: dict) -> Advertiser:
        advertiser = AdvertiserService._get_active(advertiser_id)
        for field, value in data.items():
            setattr(advertiser, field, value)
        advertiser.save()
        return advertiser

    @staticmethod
    @transaction.atomic
    def delete_advertiser(advertiser_id) -> None:
        advertiser = AdvertiserService._get_active(advertiser_id)
        advertiser.is_deleted = True
        advertiser.save(update_fields=["is_deleted", "updated_at"])

    @staticmethod
    def get_advertiser(advertiser_id) -> Advertiser:
        return AdvertiserService._get_active(advertiser_id)

    @staticmethod
    def list_advertisers(filters: dict | None = None) -> QuerySet:
        qs = Advertiser.objects.filter(is_deleted=False)
        if not filters:
            return qs
        keyword = filters.get("keyword")
        status = filters.get("status")
        if keyword:
            qs = qs.filter(
                Q(name__icontains=keyword) | Q(contact_mobile__icontains=keyword)
            )
        if status:
            qs = qs.filter(status=status)
        return qs
