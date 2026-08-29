# Layer: api
"""P2 路由：素材查询 + 广告平台/楼宇 Mock 接口。

- ``element_urlpatterns``：挂 ``/api/element/`` 与 ``/element/``（双前缀）
- ``user_urlpatterns``：挂 ``/api/user/`` 与 ``/user/``（双前缀）

全部路径不带尾斜杠（``APPEND_SLASH = False``）。
"""

from django.urls import path

from apps.ads.views import element_views

element_urlpatterns = [
    # 素材内容
    path("content/query", element_views.content_query, name="element-content-query"),
    # 广告平台位（Mock）
    path("advPlatform/list", element_views.adv_platform_list, name="adv-platform-list"),
    path("advPlatform/add", element_views.adv_platform_add, name="adv-platform-add"),
    path("advPlatform/edit", element_views.adv_platform_edit, name="adv-platform-edit"),
    path("advPlatform/del", element_views.adv_platform_del, name="adv-platform-del"),
    path("advPlatform/updateLock", element_views.adv_platform_update_lock, name="adv-platform-lock"),
]

user_urlpatterns = [
    path("adElementList", element_views.ad_element_list, name="user-ad-element-list"),
    path("getAllLy", element_views.get_all_ly, name="user-get-all-ly"),
    path("getSelectedLy", element_views.get_selected_ly, name="user-get-selected-ly"),
]

urlpatterns = element_urlpatterns
