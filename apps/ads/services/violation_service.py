# Layer: service
from django.db import transaction
from django.db.models import QuerySet

from apps.ads.exceptions import (
    CampaignNotFound,
    ViolationAlreadyResolved,
    ViolationNotFound,
)
from apps.ads.models import Campaign, ViolationRecord


class ViolationService:
    @staticmethod
    @transaction.atomic
    def create_violation(data: dict) -> ViolationRecord:
        payload = dict(data)
        campaign_id = payload.pop("campaign")
        rule_id = payload.pop("rule")
        try:
            Campaign.objects.get(id=campaign_id, is_deleted=False)
        except Campaign.DoesNotExist as e:
            raise CampaignNotFound(campaign_id) from e
        return ViolationRecord.objects.create(campaign_id=campaign_id, rule_id=rule_id, **payload)

    @staticmethod
    @transaction.atomic
    def resolve_violation(violation_id) -> ViolationRecord:
        try:
            violation = ViolationRecord.objects.get(id=violation_id)
        except ViolationRecord.DoesNotExist as e:
            raise ViolationNotFound(violation_id) from e
        if violation.resolved:
            raise ViolationAlreadyResolved(violation_id)
        violation.resolved = True
        violation.save(update_fields=["resolved", "updated_at"])
        return violation

    @staticmethod
    def list_violations_by_campaign(campaign_id) -> QuerySet:
        return ViolationRecord.objects.filter(campaign_id=campaign_id)
