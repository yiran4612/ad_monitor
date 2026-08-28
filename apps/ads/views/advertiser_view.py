# Layer: api
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.ads.exceptions import AdvertiserNotFound
from apps.ads.filters import AdvertiserFilter
from apps.ads.serializers import AdvertiserSerializer
from apps.ads.services.advertiser_service import AdvertiserService


@extend_schema(tags=["广告主"])
class AdvertiserViewSet(viewsets.ModelViewSet):
    serializer_class = AdvertiserSerializer
    filterset_class = AdvertiserFilter

    def get_queryset(self):
        return AdvertiserService.list_advertisers({})

    @extend_schema(
        summary="广告主列表",
        description="支持 ?status=active 过滤",
        responses={200: AdvertiserSerializer(many=True)},
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

    @extend_schema(summary="创建广告主", request=AdvertiserSerializer, responses={201: AdvertiserSerializer})
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        advertiser = AdvertiserService.create_advertiser(serializer.validated_data)
        return Response(
            {"code": 200, "msg": "创建成功", "data": self.get_serializer(advertiser).data},
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(summary="广告主详情", responses={200: AdvertiserSerializer})
    def retrieve(self, request, pk=None):
        try:
            advertiser = AdvertiserService.get_advertiser(pk)
        except AdvertiserNotFound as e:
            return Response({"code": 404, "msg": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response({"code": 200, "msg": "查询成功", "data": self.get_serializer(advertiser).data})

    @extend_schema(summary="更新广告主", request=AdvertiserSerializer, responses={200: AdvertiserSerializer})
    def update(self, request, pk=None, partial=False):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            advertiser = AdvertiserService.update_advertiser(pk, serializer.validated_data)
        except AdvertiserNotFound as e:
            return Response({"code": 404, "msg": str(e)}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(advertiser, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            advertiser = AdvertiserService.update_advertiser(pk, serializer.validated_data)
        except AdvertiserNotFound as e:
            return Response({"code": 404, "msg": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response({"code": 200, "msg": "更新成功", "data": self.get_serializer(advertiser).data})

    @extend_schema(summary="删除广告主（软删除）", responses={200: None})
    def destroy(self, request, pk=None):
        try:
            AdvertiserService.delete_advertiser(pk)
        except AdvertiserNotFound as e:
            return Response({"code": 404, "msg": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response({"code": 200, "msg": "删除成功"})
