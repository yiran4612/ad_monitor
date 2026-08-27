# Layer: api
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.ads.exceptions import CampaignNotFound
from apps.ads.filters import CreativeFilter
from apps.ads.models import Creative
from apps.ads.serializers import CreativeListSerializer, CreativeSerializer
from apps.ads.services.creative_service import CreativeService


@extend_schema(tags=["广告素材"])
class CreativeViewSet(viewsets.GenericViewSet):
    filterset_class = CreativeFilter

    def get_queryset(self):
        return Creative.objects.filter(is_deleted=False)

    def get_serializer_class(self):
        return CreativeListSerializer if self.action == "list" else CreativeSerializer

    @extend_schema(
        summary="广告素材列表",
        description="支持 ?campaign_id=<uuid> 过滤；自动排除软删除素材",
        responses={200: CreativeListSerializer(many=True)},
    )
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

    @extend_schema(
        summary="创建广告素材",
        request=CreativeSerializer,
        responses={201: CreativeListSerializer},
    )
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            creative = CreativeService.create_creative(serializer.validated_data)
        except CampaignNotFound as e:
            return Response(
                {"code": 404, "msg": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {"code": 200, "msg": "创建成功", "data": CreativeListSerializer(creative).data},
            status=status.HTTP_201_CREATED,
        )
