"""P2.5：素材上传（本地 media 存储，OSS 替代方案）。

路由：POST /api/element/content/upload（uploadImage / uploadVideo 为别名路由）。
MEDIA_ROOT 在测试中重定向到 tmp_path，不污染真实 media 目录。
"""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.ads.models import Creative
from apps.ads.services import storage_service

pytestmark = pytest.mark.django_db

UPLOAD_URL = "/api/element/content/upload"
UPLOAD_IMAGE_URL = "/api/element/content/uploadImage"
UPLOAD_VIDEO_URL = "/api/element/content/uploadVideo"
CONTENT_QUERY_URL = "/api/element/content/query"
AD_ELEMENT_LIST_URL = "/api/user/adElementList"

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"0" * 128
MP4_BYTES = b"\x00\x00\x00\x18ftypmp42" + b"0" * 512


@pytest.fixture
def media_root(settings, tmp_path):
    """MEDIA_ROOT 指向临时目录，测试落盘不污染真实 media/。"""
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


def _png(name="poster.png"):
    return SimpleUploadedFile(name, PNG_BYTES, content_type="image/png")


def _mp4(name="promo.mp4"):
    return SimpleUploadedFile(name, MP4_BYTES, content_type="video/mp4")


def _post(client, url=UPLOAD_URL, **fields):
    """multipart POST，Host 指到 localhost:8000（build_absolute_uri 拼完整地址）。"""
    return client.post(url, data=fields, format="multipart", HTTP_HOST="localhost:8000")


class TestContentUpload:
    def test_upload_image_success(self, auth_client, media_root):
        resp = _post(auth_client, file=_png(), material_type="image", name="品牌海报")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert body["msg"] == "上传成功"
        data = body["data"]
        assert data["url"].startswith("http://localhost:8000/media/creatives/images/")
        assert data["url"].endswith(".png")
        assert data["materialType"] == 0  # 0=图片（前端 contentType 枚举）
        assert data["coverUrl"] is None
        assert data["duration"] == 0.0
        assert data["filename"] == "poster.png"
        assert data["size"] == len(PNG_BYTES)
        assert data["campaignId"] is None
        # 文件真实落盘
        assert len(list(media_root.glob("creatives/images/*.png"))) == 1
        # name 生效；status=pending
        assert Creative.objects.filter(name="品牌海报", status=Creative.Status.PENDING).count() == 1

    def test_upload_video_success(self, auth_client, media_root):
        resp = _post(auth_client, url=UPLOAD_VIDEO_URL, file=_mp4())
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["materialType"] == 1  # 1=视频
        assert "/media/creatives/videos/" in data["url"]
        assert data["url"].endswith(".mp4")
        # 无 ffmpeg/moviepy 环境：封面为 null、时长 0.0，接口仍 200
        assert data["coverUrl"] is None
        assert data["duration"] == 0.0
        assert len(list(media_root.glob("creatives/videos/*.mp4"))) == 1

    def test_upload_image_route_forces_image(self, auth_client, media_root):
        """uploadImage 路由强制 image：mp4 后缀 → 1002 类型不一致。"""
        resp = _post(auth_client, url=UPLOAD_IMAGE_URL, file=_mp4())
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 1002
        assert body["msg"] == "文件类型与素材类型不一致"
        assert Creative.objects.count() == 0

    def test_upload_with_campaign(self, auth_client, media_root, test_campaign):
        resp = _post(
            auth_client,
            file=_png(),
            material_type="image",
            campaign_id=str(test_campaign.id),
        )
        assert resp.json()["code"] == 200
        assert resp.json()["data"]["campaignId"] == str(test_campaign.id)
        assert Creative.objects.get().campaign_id == test_campaign.id

    def test_no_token_401(self, api_client):
        resp = _post(api_client, file=_png())
        assert resp.status_code == 401

    def test_missing_file_1001(self, auth_client):
        resp = _post(auth_client, material_type="image")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 1001
        assert body["msg"] == "请选择文件"

    def test_oversize_1001(self, auth_client, monkeypatch):
        """模拟超大文件：monkeypatch 大小上限为 100 字节。"""
        monkeypatch.setattr(storage_service, "MAX_IMAGE_SIZE", 100)
        resp = _post(auth_client, file=_png(), material_type="image")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 1001
        assert body["msg"] == "文件过大（图片10M/视频200M）"

    def test_exe_type_mismatch_1002(self, auth_client):
        exe = SimpleUploadedFile("virus.exe", b"MZ" + b"0" * 64, content_type="application/x-msdownload")
        resp = _post(auth_client, file=exe, material_type="image")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 1002
        assert body["msg"] == "文件类型与素材类型不一致"

    def test_same_name_reupload_no_overwrite(self, auth_client, media_root):
        """同名文件二次上传：uuid 重命名，生成新文件，不覆盖旧文件。"""
        resp1 = _post(auth_client, file=_png(name="a.png"), material_type="image")
        resp2 = _post(auth_client, file=_png(name="a.png"), material_type="image")
        url1, url2 = resp1.json()["data"]["url"], resp2.json()["data"]["url"]
        assert url1 != url2
        assert len(list(media_root.glob("creatives/images/*.png"))) == 2
        assert Creative.objects.count() == 2
        # 两条记录 id 不同
        assert resp1.json()["data"]["id"] != resp2.json()["data"]["id"]

    def test_query_finds_uploaded(self, auth_client, media_root):
        resp = _post(auth_client, file=_mp4(), material_type="video")
        creative_id = resp.json()["data"]["id"]

        # 详情模式
        detail = auth_client.get(f"{CONTENT_QUERY_URL}?id={creative_id}").json()
        assert detail["code"] == 200
        assert detail["data"]["id"] == creative_id
        # 列表模式（新建时间倒序，第一条即刚上传的）
        listing = auth_client.get(f"{CONTENT_QUERY_URL}?material_type=video&page=1&page_size=10").json()
        assert listing["data"]["count"] >= 1
        assert listing["data"]["results"][0]["id"] == creative_id
        assert listing["data"]["results"][0]["url"].startswith("http://testserver/media/creatives/videos/")

    def test_ad_element_list_contains_uploaded(self, auth_client, media_root):
        resp = _post(auth_client, file=_mp4(name="投放视频.mp4"), material_type="video")
        data = resp.json()["data"]

        listing = auth_client.get(AD_ELEMENT_LIST_URL).json()
        items = [x for x in listing["data"]["list"] if x["element_id"] == data["id"]]
        assert len(items) == 1
        item = items[0]
        assert item["contentType"] == 1
        assert item["vedioUrl"].startswith("http://testserver/media/creatives/videos/")
        assert item["epgName"] == "投放视频"  # name 缺省用原文件名去扩展名
