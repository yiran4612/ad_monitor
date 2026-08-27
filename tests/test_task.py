import pytest
from unittest.mock import MagicMock, patch


pytestmark = pytest.mark.django_db


class TestTask:

    @patch("apps.ads.views.task_view.detect_video_task")
    @patch("apps.ads.views.task_view.AsyncResult")
    def test_trigger_detect_task(
        self, mock_async_result, mock_detect_video_task, auth_client, test_campaign
    ):
        fake_result = MagicMock()
        fake_result.id = "fake-task-id"
        mock_detect_video_task.delay.return_value = fake_result

        # 让 retrieve 查询时也返回 pending，虽然这个测试不直接查，但防止后续扩展
        mock_async_result_instance = MagicMock()
        mock_async_result_instance.state = "PENDING"
        mock_async_result.return_value = mock_async_result_instance

        resp = auth_client.post(
            "/api/tasks/",
            {
                "campaign_id": str(test_campaign.id),
                "video_url": "https://example.com/test.mp4",
            },
            format="json",
        )
        print("TRIGGER STATUS:", resp.status_code)
        print("TRIGGER BODY:", resp.json())

        assert resp.status_code == 201
        assert resp.json()["code"] == 200
        assert resp.json()["data"]["task_id"] == "fake-task-id"
        assert resp.json()["data"]["status"] == "pending"

        mock_detect_video_task.delay.assert_called_once_with(
            str(test_campaign.id), "https://example.com/test.mp4"
        )

    @patch("apps.ads.views.task_view.detect_video_task")
    @patch("apps.ads.views.task_view.AsyncResult")
    def test_get_task_status(
        self, mock_async_result, mock_detect_video_task, auth_client, test_campaign
    ):
        fake_result = MagicMock()
        fake_result.id = "fake-task-id"
        mock_detect_video_task.delay.return_value = fake_result

        ar = MagicMock()
        ar.state = "PROGRESS"
        ar.info = {"progress": 50, "step": "detecting"}
        mock_async_result.return_value = ar

        resp = auth_client.post(
            "/api/tasks/",
            {
                "campaign_id": str(test_campaign.id),
                "video_url": "https://example.com/test.mp4",
            },
            format="json",
        )
        assert resp.status_code == 201
        task_id = resp.json()["data"]["task_id"]

        resp2 = auth_client.get(f"/api/tasks/{task_id}/")
        print("STATUS BODY:", resp2.status_code, resp2.json())

        assert resp2.status_code == 200
        data = resp2.json()["data"]
        assert data["task_id"] == task_id
        assert data["status"] == "running"
        assert data["progress"] == 50