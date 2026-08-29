"""
URL configuration for ad_monitor project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.ads.element_urls import user_urlpatterns

urlpatterns = [
    # Django 管理后台
    path("admin/", admin.site.urls),
    # API 文档（Swagger UI）
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # path("api/", include("apps.ads.urls", namespace="ads")),
    # 广告监察平台 API
    path("api/ads/", include("apps.ads.urls", namespace="ads")),
    # 用户模块 API（后面接登录注册用）
    path("api/users/", include("apps.users.urls", namespace="users")),
    # 任务模块 API
    path("api/tasks/", include("apps.ads.task_urls", namespace="tasks")),
    # P2：素材查询 + 广告平台/楼宇 Mock（双前缀，兼容前端带/不带 /api 两种路径）
    path("api/element/", include("apps.ads.element_urls")),
    path("element/", include("apps.ads.element_urls")),
    path("api/user/", include(user_urlpatterns)),
    path("user/", include(user_urlpatterns)),
]
