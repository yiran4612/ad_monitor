# Layer: api
import django_filters

from apps.ads.models import Advertiser, Campaign, Creative, ViolationRecord


class AdvertiserFilter(django_filters.FilterSet):
    """广告主过滤：?status=active|inactive|paused"""

    class Meta:
        model = Advertiser
        fields = ["status"]


class CampaignFilter(django_filters.FilterSet):
    """广告活动过滤：?advertiser_id=<uuid>"""

    advertiser_id = django_filters.UUIDFilter(field_name="advertiser_id")

    class Meta:
        model = Campaign
        fields = ["advertiser_id"]


class ViolationFilter(django_filters.FilterSet):
    """违规记录过滤：?campaign_id=<uuid>"""

    campaign_id = django_filters.UUIDFilter(field_name="campaign_id")

    class Meta:
        model = ViolationRecord
        fields = ["campaign_id"]


class CreativeFilter(django_filters.FilterSet):
    """广告素材过滤：?campaign_id=<uuid>"""

    campaign_id = django_filters.UUIDFilter(field_name="campaign_id")

    class Meta:
        model = Creative
        fields = ["campaign_id"]
