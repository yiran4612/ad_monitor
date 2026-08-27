# Layer: api
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.ads.exceptions import AdvertiserNotFound
from apps.ads.models import MonitorRule
from apps.ads.serializers import MonitorRuleSerializer
from apps.ads.services.monitor_rule_service import MonitorRuleService


@extend_schema(tags=["监控规则"])
class MonitorRuleViewSet(viewsets.GenericViewSet):
    """监控规则 ViewSet：仅 list / create，手动方法，不使用 DRF 写钩子。"""

    serializer_class = MonitorRuleSerializer

    @extend_schema(
        summary="监控规则列表",
        description="支持可选参数 ?advertiser_id=<uuid>；带参时仅返回该广告主启用中的规则，不带参时返回全部规则。",
        responses={200: MonitorRuleSerializer(many=True)},
    )
    def list(self, request):
        advertiser_id = request.query_params.get("advertiser_id")
        if advertiser_id:
            try:
                queryset = MonitorRuleService.list_active_rules_by_advertiser(
                    advertiser_id
                )
            except AdvertiserNotFound:
                return Response(
                    {"code": 400, "msg": "广告主不存在"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            queryset = MonitorRule.objects.all()

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

    @extend_schema(
        summary="创建监控规则",
        request=MonitorRuleSerializer,
        responses={201: MonitorRuleSerializer},
    )
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            rule = MonitorRuleService.create_rule(serializer.validated_data)
        except AdvertiserNotFound:
            return Response(
                {"code": 400, "msg": "广告主不存在"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"code": 200, "msg": "创建成功", "data": self.get_serializer(rule).data},
            status=status.HTTP_201_CREATED,
        )
