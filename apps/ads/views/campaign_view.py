# Layer: api
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.ads.exceptions import AdvertiserNotFound, CampaignNotFound
from apps.ads.filters import CampaignFilter
from apps.ads.models import Campaign
from apps.ads.serializers import (
    CampaignListSerializer,
    CampaignSerializer,
    CampaignStatusUpdateSerializer,
)
from apps.ads.services.campaign_service import CampaignService


@extend_schema(tags=["广告活动"])
class CampaignViewSet(viewsets.GenericViewSet):
    filterset_class = CampaignFilter

    def get_queryset(self):
        return Campaign.objects.filter(is_deleted=False)

    def get_serializer_class(self):
        if self.action == "list":
            return CampaignListSerializer
        if self.action == "update_status":
            return CampaignStatusUpdateSerializer
        return CampaignSerializer

    @extend_schema(summary="广告活动列表", description="支持 ?advertiser_id=<uuid> 过滤", responses={200: CampaignListSerializer(many=True)})
    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return Response(
                {
                    "code": 200,
                    "msg": "查询成功",
                    "data": {
                        "count": self.paginator.page.paginator.count,
                        "next": self.paginator.get_next_link(),
                        "previous": self.paginator.get_previous_link(),
                        "results": serializer.data,
                    },
                }
            )
        serializer = self.get_serializer(queryset, many=True)
        return Response({"code": 200, "msg": "查询成功", "data": serializer.data})

    @extend_schema(summary="创建广告活动", request=CampaignSerializer, responses={201: CampaignListSerializer})
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            campaign = CampaignService.create_campaign(serializer.validated_data)
        except AdvertiserNotFound as e:
            return Response({"code": 400, "msg": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {"code": 200, "msg": "创建成功", "data": CampaignListSerializer(campaign).data},
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(summary="变更活动状态", request=CampaignStatusUpdateSerializer, responses={200: CampaignListSerializer})
    @action(detail=True, methods=["patch"], url_path="status")
    def update_status(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            campaign = CampaignService.update_campaign_status(pk, serializer.validated_data["status"])
        except CampaignNotFound as e:
            return Response({"code": 404, "msg": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {"code": 200, "msg": "状态更新成功", "data": CampaignListSerializer(campaign).data}
        )
