# Layer: Model
# from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    """使用 mobile 作为唯一标识的管理器。"""

    def create_user(self, mobile, password=None, **extra_fields):
        if not mobile:
            raise ValueError("mobile 为必填字段")
        extra_fields.setdefault("is_active", True)
        user = self.model(mobile=mobile, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, mobile, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.ADMIN)
        extra_fields.setdefault("is_active", True)
        return self.create_user(mobile, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        ADMIN = "admin", "管理员"
        ADVERTISER = "advertiser", "广告主"
        MONITOR = "monitor", "监察员"

    mobile = models.CharField(max_length=11, unique=True, verbose_name="手机号")
    nickname = models.CharField(max_length=64, blank=True, default="", verbose_name="昵称")
    role = models.CharField(
        max_length=16,
        choices=Role.choices,
        default=Role.ADVERTISER,
        verbose_name="角色",
    )
    is_staff = models.BooleanField(default=False, verbose_name="可访问后台")
    is_superuser = models.BooleanField(default=False, verbose_name="超级管理员")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    # is_active = models.BooleanField(default=True, verbose_name="激活状态")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    objects = UserManager()

    USERNAME_FIELD = "mobile"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        db_table = "users"
        verbose_name = "用户"
        verbose_name_plural = verbose_name

    def __str__(self):
        # return f"{self.mobile} ({self.get_role_display()})"
        return f"{self.mobile}({self.nickname})"
