# Layer: service
class AdvertiserNotFound(Exception):
    """广告主不存在。"""

    def __init__(self, advertiser_id=None):
        self.advertiser_id = advertiser_id
        detail = "广告主不存在" if advertiser_id is None else f"广告主不存在: {advertiser_id}"
        super().__init__(detail)


class CampaignNotFound(Exception):
    """广告活动不存在。"""

    def __init__(self, campaign_id=None):
        self.campaign_id = campaign_id
        detail = "广告活动不存在" if campaign_id is None else f"广告活动不存在: {campaign_id}"
        super().__init__(detail)


class CreativeNotFound(Exception):
    """广告素材不存在。"""

    def __init__(self, creative_id=None):
        self.creative_id = creative_id
        detail = "素材不存在" if creative_id is None else f"素材不存在: {creative_id}"
        super().__init__(detail)


class AdvPlatformNotFound(Exception):
    """广告平台位不存在。"""

    def __init__(self, element_id=None):
        self.element_id = element_id
        detail = "广告平台位不存在" if element_id is None else f"广告平台位不存在: {element_id}"
        super().__init__(detail)


class ViolationNotFound(Exception):
    """违规记录不存在。"""

    def __init__(self, violation_id=None):
        self.violation_id = violation_id
        detail = "违规记录不存在" if violation_id is None else f"违规记录不存在: {violation_id}"
        super().__init__(detail)


class ViolationAlreadyResolved(Exception):
    """违规记录已处理，不能重复处理。"""

    def __init__(self, violation_id=None):
        self.violation_id = violation_id
        detail = "违规记录已处理" if violation_id is None else f"违规记录已处理: {violation_id}"
        super().__init__(detail)
