# Layer: api
from rest_framework import serializers

from apps.ads.models import Advertiser, Campaign, Creative, MonitorRule, ViolationRecord


# ──────────────────────────────────────────────
# 广告主
# ──────────────────────────────────────────────

class AdvertiserSerializer(serializers.ModelSerializer):
    """广告主：列表 / 详情 / 创建 / 更新 共用。"""

    class Meta:
        model = Advertiser
        fields = ["id", "name", "contact_mobile", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class AdvertiserBriefSerializer(serializers.ModelSerializer):
    """广告主基本信息（嵌套展示用）。"""

    class Meta:
        model = Advertiser
        fields = ["id", "name", "contact_mobile", "status"]


# ──────────────────────────────────────────────
# 广告活动
# ──────────────────────────────────────────────

class CampaignListSerializer(serializers.ModelSerializer):
    """广告活动列表：嵌套广告主基本信息。"""

    advertiser = AdvertiserBriefSerializer(read_only=True)

    class Meta:
        model = Campaign
        fields = [
            "id", "advertiser", "title", "platform", "budget",
            "start_date", "end_date", "status", "created_at", "updated_at",
        ]


class CampaignSerializer(serializers.ModelSerializer):
    """广告活动创建：advertiser 只接受 UUID 字符串，不嵌套写入。"""

    advertiser = serializers.UUIDField(write_only=True)

    class Meta:
        model = Campaign
        fields = [
            "id", "advertiser", "title", "platform", "budget",
            "start_date", "end_date", "status", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]


class CampaignStatusUpdateSerializer(serializers.Serializer):
    """广告活动状态变更。"""

    status = serializers.ChoiceField(choices=Campaign.Status.choices)


class CampaignBriefSerializer(serializers.ModelSerializer):
    """广告活动基本信息（违规记录嵌套展示用）。"""

    class Meta:
        model = Campaign
        fields = ["id", "title", "platform", "status"]


# ──────────────────────────────────────────────
# 违规记录
# ──────────────────────────────────────────────

class ViolationListSerializer(serializers.ModelSerializer):
    """违规记录列表 / 详情：嵌套广告活动基本信息。"""

    campaign = CampaignBriefSerializer(read_only=True)

    class Meta:
        model = ViolationRecord
        fields = [
            "id", "campaign", "rule", "description", "screenshot_url",
            "detected_at", "resolved", "created_at", "updated_at",
        ]
        read_only_fields = ["resolved", "created_at", "updated_at"]


class ViolationCreateSerializer(serializers.ModelSerializer):
    """违规记录创建：campaign / rule 只接受 UUID 字符串，不嵌套写入。"""

    campaign = serializers.UUIDField(write_only=True)
    rule = serializers.UUIDField(write_only=True)

    class Meta:
        model = ViolationRecord
        fields = [
            "id", "campaign", "rule", "description", "screenshot_url",
            "detected_at", "resolved", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "resolved", "created_at", "updated_at"]


# ──────────────────────────────────────────────
# 监控规则
# ──────────────────────────────────────────────

class MonitorRuleSerializer(serializers.ModelSerializer):
    """监控规则：列表 / 创建共用。

    advertiser：
    - 写入（创建）：只接受 UUID 字符串，不嵌套写入；
    - 展示（读取）：嵌套返回 {id, name}，不泄露其余字段。
    """

    advertiser = serializers.UUIDField(write_only=True)
    rule_type = serializers.ChoiceField(choices=MonitorRule.RuleType.choices)

    class Meta:
        model = MonitorRule
        fields = [
            "id", "advertiser", "rule_type", "keyword", "threshold",
            "is_active", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        adv = instance.advertiser
        ret["advertiser"] = {"id": str(adv.id), "name": adv.name} if adv else None
        return ret


# ──────────────────────────────────────────────
# 广告素材
# ──────────────────────────────────────────────

class CreativeListSerializer(serializers.ModelSerializer):
    """广告素材列表 / 详情：嵌套广告活动基本信息。"""

    campaign = CampaignBriefSerializer(read_only=True)

    class Meta:
        model = Creative
        fields = [
            "id", "campaign", "name", "material_type", "file_url",
            "duration", "created_at", "updated_at",
        ]


class CreativeSerializer(serializers.ModelSerializer):
    """广告素材创建：campaign 只接受 UUID 字符串，不嵌套写入。"""

    campaign = serializers.UUIDField(write_only=True)
    material_type = serializers.ChoiceField(choices=Creative.MaterialType.choices)

    class Meta:
        model = Creative
        fields = [
            "id", "campaign", "name", "material_type", "file_url",
            "duration", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
