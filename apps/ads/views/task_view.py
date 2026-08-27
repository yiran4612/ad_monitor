# Layer: api
from rest_framework import viewsets, status
from rest_framework.response import Response
from celery.result import AsyncResult
from apps.ads.tasks import detect_video_task

class TaskViewSet(viewsets.ViewSet):

    def create(self, request):
        campaign_id = request.data.get("campaign_id")
        video_url = request.data.get("video_url")
        if not campaign_id or not video_url:
            return Response(
                {"code": 400, "msg": "campaign_id 和 video_url 必填"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        result = detect_video_task.delay(campaign_id, video_url)
        return Response({
            "code": 200, "msg": "任务已提交",
            "data": {"task_id": result.id, "status": "pending"}
        }, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        result = AsyncResult(pk)
        if result.state == "PENDING":
            data = {"task_id": pk, "status": "pending", "progress": 0}
        elif result.state == "PROGRESS":
            meta = result.info or {}
            data = {"task_id": pk, "status": "running", "progress": meta.get("progress", 0), "step": meta.get("step", "")}
        elif result.state == "SUCCESS":
            data = {"task_id": pk, "status": "success", "result": result.result}
        elif result.state == "FAILURE":
            data = {"task_id": pk, "status": "failed", "error": str(result.info)}
        else:
            data = {"task_id": pk, "status": result.state.lower()}
        return Response({"code": 200, "msg": "查询成功", "data": data})