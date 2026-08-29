# Layer: API
from django.urls import path

from apps.users.views import login_view, p1_views, register_view

app_name = "users"

urlpatterns = [
    # ── P0：注册 / 登录（保留尾斜杠，前端与既有调用方均带斜杠）──
    path("register/", register_view, name="user-register"),
    path("login/", login_view, name="user-login"),
    # ── P1：用户相关接口 ──
    # 注意：全部不带尾斜杠。前端 axios 请求的是 /api/users/getAreaInfo?id=0，
    # 而项目 APPEND_SLASH=False，注册成 "getAreaInfo/" 会导致 404。
    path("check-login", p1_views.check_login, name="user-check-login"),
    path("getAreaInfo", p1_views.get_area_info, name="user-get-area-info"),
    path("getCustomerInfos", p1_views.get_customer_infos, name="user-get-customer-infos"),
    path("editCustomerInfos", p1_views.edit_customer_infos, name="user-edit-customer-infos"),
    path("changePsw", p1_views.change_psw, name="user-change-psw"),
    path("getLoginTipInfo", p1_views.get_login_tip_info, name="user-get-login-tip-info"),
    path("getPhoneCaptcha", p1_views.get_phone_captcha, name="user-get-phone-captcha"),
]
