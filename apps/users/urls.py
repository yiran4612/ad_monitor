# Layer: API
from django.urls import path

from apps.users.views import login_view, register_view

app_name = "users"

urlpatterns = [
    path("register/", register_view, name="user-register"),
    path("login/", login_view, name="user-login"),
]
