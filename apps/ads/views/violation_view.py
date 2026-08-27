# Layer: api
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.ads.exceptions import (
    CampaignNotFound,
    ViolationAlreadyResolved,
    ViolationNotFound,
)
from apps.ads.filters import ViolationFilter
from apps.ads.models import ViolationRecord
from apps.ads.serializers import ViolationCreateSerializer, ViolationListSerializer
from apps.ads.services.violation_service import ViolationService


@extend_schema(tags=["违规记录"])
class ViolationViewSet(viewsets.GenericViewSet):
    filterset_class = ViolationFilter

    def get_queryset(self):
        return ViolationRecord.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return ViolationCreateSerializer
        return ViolationListSerializer

    @extend_schema(summary="违规记录列表", description="支持 ?campaign_id=<uuid> 过滤", responses={200: ViolationListSerializer(many=True)})
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

    @extend_schema(summary="创建违规记录", request=ViolationCreateSerializer, responses={201: ViolationListSerializer})
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            violation = ViolationService.create_violation(serializer.validated_data)
        except CampaignNotFound as e:
            return Response({"code": 400, "msg": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {"code": 200, "msg": "创建成功", "data": ViolationListSerializer(violation).data},
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(summary="标记违规已处理", responses={200: ViolationListSerializer})
    @action(detail=True, methods=["patch"])
    def resolve(self, request, pk=None):
        try:
            violation = ViolationService.resolve_violation(pk)
        except ViolationNotFound as e:
            return Response({"code": 404, "msg": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ViolationAlreadyResolved as e:
            return Response({"code": 400, "msg": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {"code": 200, "msg": "处理成功", "data": ViolationListSerializer(violation).data}
        )
