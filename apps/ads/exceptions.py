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
