from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("mobile", "nickname", "role", "is_staff", "is_active", "created_at")
    list_filter = ("is_staff", "is_superuser", "role", "is_active")
    search_fields = ("mobile", "nickname")
    ordering = ("-created_at",)

    # 如果你用的是 AbstractBaseUser + PermissionsMixin，
    # 需要告诉 Django admin 用哪些字段做 add/edit 表单
    fieldsets = (
        (None, {"fields": ("mobile", "password")}),
        ("个人信息", {"fields": ("nickname", "role")}),
        ("权限", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("mobile", "nickname", "role", "password1", "password2"),
        }),
    )