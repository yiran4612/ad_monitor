# Layer: API
"""P2：素材查询真实实现 + 广告平台/楼宇 Mock 接口。

路由约定：
- element 前缀组挂 ``/api/element/`` 与 ``/element/``（双前缀，兼容前端两种路径）
- user 前缀组挂 ``/api/user/`` 与 ``/user/``
- 全部不带尾斜杠（``APPEND_SLASH = False``）
- 全部需登录（``IsAuthenticated``），未登录由 DRF 权限层返回 401

响应约定：
- 列表分页同时返回规格字段（``count``/``results``）与前端消费字段（``total``/``list``），
  前端 ``data?.list || data`` 与规格消费方均可直接使用。
"""

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from apps.ads.element_serializers import (
    AdvPlatformDeleteSerializer,
    AdvPlatformLockSerializer,
    AdvPlatformSaveSerializer,
    BuildingQuerySerializer,
    CreativeQuerySerializer,
    CreativeUploadSerializer,
    PaginationSerializer,
)
from apps.ads.exceptions import (
    AdvPlatformNotFound,
    CampaignNotFound,
    CreativeNotFound,
    UploadParamError,
    UploadTypeMismatch,
)
from apps.ads.models import Creative
from apps.ads.services.adv_platform_service import AdvPlatformService
from apps.ads.services.building_service import BuildingService
from apps.ads.services.creative_service import CreativeService
from core.responses import biz_error, first_error, param_error, success


def _paged(data: dict) -> dict:
    """列表返回体：规格 {count, results} + 前端 {total, list} 并存。"""
    items = data["results"] if "results" in data else data["list"]
    return {
        "count": data.get("count", data.get("total", len(items))),
        "total": data.get("total", data.get("count", len(items))),
        "results": items,
        "list": items,
    }


@extend_schema(tags=["素材-P2"], summary="素材内容查询（详情/列表）")
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def content_query(request):
    """``GET /element/content/query``。

    - 带 ``id``：返回单条素材详情
    - 不带 ``id``：按 ``campaign_id/status/material_type/page/page_size``（兼容
      ``pageNum/pageSize``）分页查询
    """
    serializer = CreativeQuerySerializer(data=request.query_params)
    if not serializer.is_valid():
        return param_error(first_error(serializer.errors))
    params = serializer.validated_data

    if params.get("id"):
        try:
            creative = CreativeService.get_creative(params["id"])
        except CreativeNotFound as e:
            return biz_error(str(e))
        return success(CreativeService.to_payload(creative, request=request))

    try:
        result = CreativeService.query_creatives(
            campaign_id=params.get("campaign_id"),
            status=params.get("status"),
            material_type=params.get("material_type"),
            page=serializer.effective_page,
            page_size=serializer.effective_page_size,
            request=request,
        )
    except CampaignNotFound as e:
        return param_error(str(e))
    return success(_paged(result))


@extend_schema(tags=["素材-P2"], summary="广告素材列表（投放配置用）")
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ad_element_list(request):
    """``GET /user/adElementList``：映射 Creative，返回前端消费的 {list, total}。"""
    serializer = CreativeQuerySerializer(data=request.query_params)
    if not serializer.is_valid():
        return param_error(first_error(serializer.errors))
    params = serializer.validated_data

    try:
        result = CreativeService.query_creatives(
            campaign_id=params.get("campaign_id"),
            status=params.get("status"),
            material_type=params.get("material_type"),
            page=serializer.effective_page,
            page_size=serializer.effective_page_size,
            request=request,
        )
    except CampaignNotFound as e:
        return param_error(str(e))
    return success(_paged(result))


# ── P2.5：素材上传（本地 media 存储，OSS 替代方案）──

# 别名路由 → 强制素材类型（uploadImage / uploadVideo 与 upload 共用同一 view）
_UPLOAD_FORCED_TYPE = {
    "uploadimage": Creative.MaterialType.IMAGE,
    "uploadvideo": Creative.MaterialType.VIDEO,
}


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def content_upload(request):
    """``POST /element/content/upload``（uploadImage / uploadVideo 为别名路由）。

    - multipart/form-data，``file`` 必填
    - ``material_type`` 可选（image|video，默认 image），uploadImage/uploadVideo
      路由会根据路径强制覆盖
    - 校验与落盘在 Service 层（LocalStorageService），本函数只取参数
    """
    route_tail = request.path.rstrip("/").rsplit("/", 1)[-1].lower()
    forced_type = _UPLOAD_FORCED_TYPE.get(route_tail)

    serializer = CreativeUploadSerializer(data=request.data)
    if not serializer.is_valid():
        return param_error(first_error(serializer.errors))

    material_type = forced_type or serializer.validated_data.get("material_type") or Creative.MaterialType.IMAGE
    uploaded = request.FILES.get("file")
    if uploaded is None:
        return param_error("请选择文件")

    try:
        result = CreativeService.upload_creative(
            uploaded,
            material_type,
            name=serializer.validated_data.get("name"),
            campaign_id=serializer.validated_data.get("campaign_id"),
        )
    except UploadParamError as e:
        return param_error(str(e))
    except UploadTypeMismatch as e:
        return biz_error(str(e))
    except CampaignNotFound as e:
        return param_error(str(e))

    creative = result["creative"]
    payload = {
        "id": str(creative.id),
        "elementId": str(creative.id),
        "materialType": 0 if creative.material_type == Creative.MaterialType.IMAGE else 1,
        "url": request.build_absolute_uri(creative.file_url),
        "coverUrl": request.build_absolute_uri(creative.cover_url) if creative.cover_url else None,
        "duration": float(creative.duration or 0),
        "filename": result["filename"],
        "size": result["size"],
        "campaignId": str(creative.campaign_id) if creative.campaign_id else None,
    }
    return success(payload, msg="上传成功")


# ── 广告平台位（Mock）──


@extend_schema(tags=["广告平台-P2"], summary="广告平台位列表")
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def adv_platform_list(request):
    serializer = PaginationSerializer(data=request.query_params)
    if not serializer.is_valid():
        return param_error(first_error(serializer.errors))
    result = AdvPlatformService.list_platforms(
        page=serializer.effective_page,
        page_size=serializer.effective_page_size,
    )
    return success(_paged(result))


@extend_schema(tags=["广告平台-P2"], summary="新增广告平台位")
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def adv_platform_add(request):
    serializer = AdvPlatformSaveSerializer(data=request.data)
    if not serializer.is_valid():
        return param_error(first_error(serializer.errors))
    platform = AdvPlatformService.add_platform(
        serializer.validated_data,
        cname=request.user.nickname or request.user.mobile,
    )
    return success(AdvPlatformService.to_payload(platform), msg="添加成功")


@extend_schema(tags=["广告平台-P2"], summary="编辑广告平台位")
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def adv_platform_edit(request):
    serializer = AdvPlatformSaveSerializer(data=request.data)
    if not serializer.is_valid():
        return param_error(first_error(serializer.errors))
    element_id = serializer.validated_data.get("element_id")
    if element_id is None:
        return param_error("element_id 不能为空")

    try:
        platform = AdvPlatformService.update_platform(element_id, serializer.validated_data)
    except AdvPlatformNotFound as e:
        return biz_error(str(e))
    return success(AdvPlatformService.to_payload(platform), msg="修改成功")


@extend_schema(tags=["广告平台-P2"], summary="删除广告平台位")
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def adv_platform_del(request):
    serializer = AdvPlatformDeleteSerializer(data=request.data)
    if not serializer.is_valid():
        return param_error(first_error(serializer.errors))

    try:
        AdvPlatformService.delete_platform(serializer.validated_data["element_id"])
    except AdvPlatformNotFound as e:
        return biz_error(str(e))
    return success(msg="删除成功")


@extend_schema(tags=["广告平台-P2"], summary="更新广告平台锁定状态")
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def adv_platform_update_lock(request):
    serializer = AdvPlatformLockSerializer(data=request.data)
    if not serializer.is_valid():
        return param_error(first_error(serializer.errors))

    try:
        platform = AdvPlatformService.update_lock(
            serializer.validated_data["element_id"],
            serializer.validated_data["is_locked"],
        )
    except AdvPlatformNotFound as e:
        return biz_error(str(e))
    return success(AdvPlatformService.to_payload(platform), msg="状态更新成功")


# ── 楼宇（Mock）──


@extend_schema(tags=["楼宇-P2"], summary="获取所有楼宇列表")
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_ly(request):
    serializer = BuildingQuerySerializer(data=request.query_params)
    if not serializer.is_valid():
        return param_error(first_error(serializer.errors))
    result = BuildingService.list_buildings(
        selected_only=False,
        search=serializer.validated_data.get("search", ""),
        page=serializer.effective_page,
        page_size=serializer.effective_page_size,
    )
    return success(_paged(result))


@extend_schema(tags=["楼宇-P2"], summary="获取已选投放楼宇列表")
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_selected_ly(request):
    serializer = BuildingQuerySerializer(data=request.query_params)
    if not serializer.is_valid():
        return param_error(first_error(serializer.errors))
    result = BuildingService.list_buildings(
        selected_only=True,
        search=serializer.validated_data.get("search", ""),
        page=serializer.effective_page,
        page_size=serializer.effective_page_size,
    )
    return success(_paged(result))
