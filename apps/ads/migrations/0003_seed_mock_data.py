# Layer: migration
"""P2 Mock 种子数据：3 条广告平台位 + 5 条楼宇（其中 2 条已选投放）。

幂等：按 epg_name / name get_or_create，重复执行不会产生脏数据。
"""

from django.db import migrations


def seed_mock_data(apps, schema_editor):
    AdvPlatform = apps.get_model("ads", "AdvPlatform")
    Building = apps.get_model("ads", "Building")

    platforms = [
        {
            "epg_name": "抖音信息流广告-夏日促销",
            "element_name": "douyin_summer.mp4",
            "element_type": 1,
            "element_url": "https://example-cdn.com/mock/douyin_summer.mp4",
            "hot_img_url": "https://example-cdn.com/mock/douyin_summer_cover.jpg",
            "dulation": 15,
            "byte_rate": 4000,
            "frame_rate": 25,
            "definition": "1920x1080",
            "file_size": 7500000,
            "ext": "mp4",
            "md_5": "a1b2c3d4e5f60718293a4b5c6d7e8f90",
            "cname": "admin",
        },
        {
            "epg_name": "微信朋友圈广告-品牌宣传",
            "element_name": "wechat_brand.mp4",
            "element_type": 1,
            "element_url": "https://example-cdn.com/mock/wechat_brand.mp4",
            "hot_img_url": "https://example-cdn.com/mock/wechat_brand_cover.jpg",
            "dulation": 30,
            "byte_rate": 5000,
            "frame_rate": 25,
            "definition": "1920x1080",
            "file_size": 18000000,
            "ext": "mp4",
            "md_5": "b2c3d4e5f60718293a4b5c6d7e8f9001",
            "cname": "admin",
        },
        {
            "epg_name": "电梯屏广告-新品上市",
            "element_name": "elevator_launch.jpg",
            "element_type": 0,
            "element_url": "https://example-cdn.com/mock/elevator_launch.jpg",
            "hot_img_url": "https://example-cdn.com/mock/elevator_launch.jpg",
            "dulation": 0,
            "byte_rate": 0,
            "frame_rate": 0,
            "definition": "1080x1920",
            "file_size": 900000,
            "ext": "jpg",
            "md_5": "c3d4e5f60718293a4b5c6d7e8f900102",
            "cname": "admin",
        },
    ]
    for item in platforms:
        AdvPlatform.objects.get_or_create(epg_name=item["epg_name"], defaults=item)

    buildings = [
        {"name": "西湖国贸中心", "address": "上城区延安路98号", "is_selected": True},
        {"name": "黄龙世纪广场", "address": "西湖区曙光路122号", "is_selected": True},
        {"name": "滨江星光国际大厦", "address": "滨江区江南大道228号", "is_selected": False},
        {"name": "钱江新城万象城", "address": "上城区富春路701号", "is_selected": False},
        {"name": "未来科技城海创园", "address": "余杭区文一西路998号", "is_selected": False},
    ]
    for item in buildings:
        Building.objects.get_or_create(name=item["name"], defaults=item)


def unseed_mock_data(apps, schema_editor):
    AdvPlatform = apps.get_model("ads", "AdvPlatform")
    Building = apps.get_model("ads", "Building")
    AdvPlatform.objects.filter(
        epg_name__in=["抖音信息流广告-夏日促销", "微信朋友圈广告-品牌宣传", "电梯屏广告-新品上市"]
    ).delete()
    Building.objects.filter(
        name__in=["西湖国贸中心", "黄龙世纪广场", "滨江星光国际大厦", "钱江新城万象城", "未来科技城海创园"]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("ads", "0002_advplatform_building_creative_status"),
    ]

    operations = [
        migrations.RunPython(seed_mock_data, unseed_mock_data),
    ]
