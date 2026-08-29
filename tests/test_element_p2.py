"""P2：素材查询（content/query、adElementList）+ 广告平台/楼宇 Mock 接口。

Mock 种子数据来自 migration 0003：3 条 AdvPlatform、5 条 Building（2 条已选）。
"""

import pytest

from apps.ads.models import AdvPlatform, Creative

pytestmark = pytest.mark.django_db

CONTENT_QUERY_URL = "/api/element/content/query"
AD_ELEMENT_LIST_URL = "/api/user/adElementList"
ADV_PLATFORM_LIST_URL = "/api/element/advPlatform/list"
GET_ALL_LY_URL = "/api/user/getAllLy"
GET_SELECTED_LY_URL = "/api/user/getSelectedLy"


@pytest.fixture
def creatives(db, test_campaign):
    """4 条素材：2 video / 1 image / 1 text，状态各不相同。"""
    return [
        Creative.objects.create(
            campaign=test_campaign,
            name="夏日促销视频A",
            material_type=Creative.MaterialType.VIDEO,
            status=Creative.Status.APPROVED,
            file_url="https://cdn.example.com/a.mp4",
            duration=15,
        ),
        Creative.objects.create(
            campaign=test_campaign,
            name="夏日促销视频B",
            material_type=Creative.MaterialType.VIDEO,
            status=Creative.Status.PENDING,
            file_url="https://cdn.example.com/b.mp4",
            duration=30,
        ),
        Creative.objects.create(
            campaign=test_campaign,
            name="品牌海报",
            material_type=Creative.MaterialType.IMAGE,
            status=Creative.Status.APPROVED,
            file_url="https://cdn.example.com/c.jpg",
        ),
        Creative.objects.create(
            campaign=test_campaign,
            name="图文素材",
            material_type=Creative.MaterialType.TEXT,
            status=Creative.Status.REJECTED,
            file_url="",
        ),
    ]


class TestContentQuery:
    """素材内容查询：列表模式。"""

    def test_list_all(self, auth_client, creatives):
        resp = auth_client.get(CONTENT_QUERY_URL)
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["count"] == 4
        assert len(body["data"]["results"]) == 4
        item = body["data"]["results"][0]
        # 规格字段
        assert {"id", "name", "url", "material_type", "status", "campaign_id", "created_at"} <= set(item)

    def test_filters(self, auth_client, creatives, test_campaign):
        # material_type 过滤
        resp = auth_client.get(f"{CONTENT_QUERY_URL}?material_type=video")
        assert resp.json()["data"]["count"] == 2
        # status 过滤
        resp = auth_client.get(f"{CONTENT_QUERY_URL}?status=approved")
        assert resp.json()["data"]["count"] == 2
        # campaign_id 过滤
        resp = auth_client.get(f"{CONTENT_QUERY_URL}?campaign_id={test_campaign.id}")
        assert resp.json()["data"]["count"] == 4
        # 组合过滤
        resp = auth_client.get(f"{CONTENT_QUERY_URL}?material_type=video&status=pending")
        assert resp.json()["data"]["count"] == 1
        # 不存在的活动：1001
        resp = auth_client.get(f"{CONTENT_QUERY_URL}?campaign_id=00000000-0000-0000-0000-000000000000")
        assert resp.json()["code"] == 1001

    def test_pagination(self, auth_client, creatives):
        # 规格命名 page/page_size
        resp = auth_client.get(f"{CONTENT_QUERY_URL}?page=1&page_size=2")
        data = resp.json()["data"]
        assert data["count"] == 4 and len(data["results"]) == 2
        page1_names = {item["name"] for item in data["results"]}
        # 前端命名 pageNum/pageSize
        resp = auth_client.get(f"{CONTENT_QUERY_URL}?pageNum=2&pageSize=2")
        data = resp.json()["data"]
        assert data["count"] == 4 and len(data["results"]) == 2
        page2_names = {item["name"] for item in data["results"]}
        assert not (page1_names & page2_names)
        # 非法分页参数
        assert auth_client.get(f"{CONTENT_QUERY_URL}?page=0").json()["code"] == 1001

    def test_detail_mode(self, auth_client, creatives):
        target = creatives[0]
        resp = auth_client.get(f"{CONTENT_QUERY_URL}?id={target.id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == str(target.id)
        assert data["name"] == "夏日促销视频A"
        assert data["campaign_id"] == str(target.campaign_id)
        # 不存在 → 1002
        resp = auth_client.get(f"{CONTENT_QUERY_URL}?id=00000000-0000-0000-0000-000000000000")
        assert resp.json()["code"] == 1002
        # 非法 UUID → 1001
        resp = auth_client.get(f"{CONTENT_QUERY_URL}?id=not-a-uuid")
        assert resp.json()["code"] == 1001

    def test_requires_auth(self, api_client):
        assert api_client.get(CONTENT_QUERY_URL).status_code == 401


class TestAdElementList:
    """广告素材列表（投放配置用，前端消费 list/total）。"""

    def test_list_with_front_fields(self, auth_client, creatives):
        resp = auth_client.get(f"{AD_ELEMENT_LIST_URL}?pageNum=1&pageSize=2")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        data = body["data"]
        # 前端消费：data.list / data.total
        assert data["total"] == 4 and len(data["list"]) == 2
        item = data["list"][0]
        assert item["epgName"] == item["name"]
        assert item["element_id"] == item["id"]
        assert item["contentType"] in (0, 1)
        assert item["createTime"]

    def test_double_prefix(self, auth_client, creatives):
        """无 /api 前缀的路径同样可达。"""
        assert auth_client.get("/user/adElementList").json()["data"]["total"] == 4
        assert auth_client.get("/element/content/query").json()["data"]["count"] == 4


class TestAdvPlatform:
    """广告平台位 Mock 接口（种子数据：3 条）。"""

    def test_list_seeded(self, auth_client):
        resp = auth_client.get(ADV_PLATFORM_LIST_URL)
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["total"] == 3
        names = {item["epgName"] for item in body["data"]["list"]}
        assert "抖音信息流广告-夏日促销" in names
        item = body["data"]["list"][0]
        assert {"element_id", "epgName", "contentType", "dulation", "definition", "cname", "createTime"} <= set(item)

    def test_add_edit_del(self, auth_client):
        # add
        resp = auth_client.post(
            "/api/element/advPlatform/add",
            {
                "epg_name": "测试广告位",
                "element_name": "test.mp4",
                "element_type": 1,
                "element_url": "https://cdn.example.com/test.mp4",
                "hot_img_url": "https://cdn.example.com/test_cover.jpg",
                "dulation": 20,
                "definition": "1920x1080",
                "file_size": 5000000,
                "ext": "mp4",
                "md_5": "d41d8cd98f00b204e9800998ecf8427e",
            },
            format="json",
        )
        assert resp.json()["code"] == 200
        element_id = resp.json()["data"]["element_id"]
        assert AdvPlatform.objects.filter(id=element_id, is_deleted=False).exists()

        # edit
        resp = auth_client.post(
            "/api/element/advPlatform/edit",
            {"element_id": element_id, "epg_name": "改名后的广告位", "dulation": 25},
            format="json",
        )
        assert resp.json()["code"] == 200
        platform = AdvPlatform.objects.get(id=element_id)
        assert platform.epg_name == "改名后的广告位"
        assert platform.dulation == 25

        # del（软删除）
        resp = auth_client.post(
            "/api/element/advPlatform/del",
            {"element_id": element_id},
            format="json",
        )
        assert resp.json()["code"] == 200
        assert not AdvPlatform.objects.filter(id=element_id, is_deleted=False).exists()
        assert AdvPlatform.objects.filter(id=element_id, is_deleted=True).exists()

        # 删除后再编辑 → 1002
        resp = auth_client.post(
            "/api/element/advPlatform/edit",
            {"element_id": element_id, "epg_name": "再改"},
            format="json",
        )
        assert resp.json()["code"] == 1002

    def test_update_lock(self, auth_client):
        platform = AdvPlatform.objects.filter(is_deleted=False).first()
        assert platform.is_locked is False

        resp = auth_client.post(
            "/api/element/advPlatform/updateLock",
            {"element_id": platform.id, "is_locked": True},
            format="json",
        )
        assert resp.json()["code"] == 200
        assert AdvPlatform.objects.get(id=platform.id).is_locked is True

        # 不存在的平台位 → 1002；缺参 → 1001
        resp = auth_client.post(
            "/api/element/advPlatform/updateLock",
            {"element_id": 99999, "is_locked": True},
            format="json",
        )
        assert resp.json()["code"] == 1002
        resp = auth_client.post("/api/element/advPlatform/updateLock", {"element_id": 1}, format="json")
        assert resp.json()["code"] == 1001


class TestBuilding:
    """楼宇 Mock 接口（种子数据：5 条楼宇，2 条已选）。"""

    def test_get_all_ly(self, auth_client):
        resp = auth_client.get(f"{GET_ALL_LY_URL}?pageNum=1&pageSize=10")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["total"] == 5
        item = body["data"]["list"][0]
        assert {"id", "name", "address", "is_selected"} <= set(item)

    def test_get_all_ly_search(self, auth_client):
        resp = auth_client.get(f"{GET_ALL_LY_URL}?search=黄龙")
        data = resp.json()["data"]
        assert data["total"] == 1
        assert data["list"][0]["name"] == "黄龙世纪广场"
        # 搜索无结果
        assert auth_client.get(f"{GET_ALL_LY_URL}?search=不存在").json()["data"]["total"] == 0

    def test_get_selected_ly(self, auth_client):
        resp = auth_client.get(GET_SELECTED_LY_URL)
        data = resp.json()["data"]
        assert data["total"] == 2
        assert all(item["is_selected"] for item in data["list"])
        names = {item["name"] for item in data["list"]}
        assert names == {"西湖国贸中心", "黄龙世纪广场"}
        # search 同样生效（“黄龙”只命中黄龙世纪广场；注意“西湖”会同时命中
        # “西湖国贸中心”与地址含“西湖区”的黄龙世纪广场）
        assert auth_client.get(f"{GET_SELECTED_LY_URL}?search=黄龙").json()["data"]["total"] == 1
        assert auth_client.get(f"{GET_SELECTED_LY_URL}?search=西湖").json()["data"]["total"] == 2

    def test_requires_auth(self, api_client):
        assert api_client.get(GET_ALL_LY_URL).status_code == 401
        assert api_client.get(GET_SELECTED_LY_URL).status_code == 401
