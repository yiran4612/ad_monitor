import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.ads.models import Advertiser, Campaign

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def test_user(db):
    """创建测试用户并返回 (user, access_token)"""
    user = User.objects.create_user(
        mobile="13900139000",
        password="Test123456",
    )  # pyright: ignore[reportCallIssue]
    user.is_staff = True
    user.is_superuser = True
    user.save()

    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken()
    refresh["user_id"] = str(user.id)
    access_token = str(refresh.access_token)

    return user, access_token


@pytest.fixture
def auth_client(api_client, test_user):
    _user, token = test_user
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.fixture
def test_advertiser(db):
    return Advertiser.objects.create(
        name="测试广告主",
        # contact_email="test@example.com",
        contact_mobile="13900139000",
    )


@pytest.fixture
def test_campaign(db, test_advertiser):
    return Campaign.objects.create(
        advertiser=test_advertiser,
        title="测试活动",
        platform="douyin",
        budget=10000.00,
        start_date="2025-06-01",
        end_date="2025-06-30",
        status="running",
    )


@pytest.fixture
def test_rule(db, test_advertiser):
    from apps.ads.models import MonitorRule

    return MonitorRule.objects.create(
        advertiser=test_advertiser,
        rule_type="keyword",
        keyword="竞品A",
        is_active=True,
    )
