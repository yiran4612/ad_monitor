# Layer: api
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.ads.views.advertiser_view import AdvertiserViewSet
from apps.ads.views.campaign_view import CampaignViewSet
from apps.ads.views.creative_view import CreativeViewSet
from apps.ads.views.monitor_rule_view import MonitorRuleViewSet
from apps.ads.views.violation_view import ViolationViewSet

app_name = "ads"

router = DefaultRouter()
router.register("advertisers", AdvertiserViewSet, basename="advertiser")
router.register("campaigns", CampaignViewSet, basename="campaign")
router.register("creatives", CreativeViewSet, basename="creative")
router.register("monitor-rules", MonitorRuleViewSet, basename="monitor-rule")
router.register("violations", ViolationViewSet, basename="violation")

urlpatterns = [
    path("", include(router.urls)),
]
