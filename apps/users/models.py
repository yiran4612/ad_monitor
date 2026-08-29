# Layer: Model
# from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.conf import settings
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


class CustomerProfile(models.Model):
    """客户资料（实名认证信息）。

    与 User 一对一：登录手机号在 User.mobile，企业/联系人信息在本表。
    审核状态与前端约定：-1 驳回 / 0 审核中 / 1 审核通过。
    """

    class AuditStatus(models.IntegerChoices):
        REJECTED = -1, "驳回"
        PENDING = 0, "审核中"
        APPROVED = 1, "审核通过"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="用户",
    )
    company_name = models.CharField(max_length=128, blank=True, default="", verbose_name="公司名称")
    contact_name = models.CharField(max_length=64, blank=True, default="", verbose_name="联系人")
    contact_phone = models.CharField(max_length=11, blank=True, default="", verbose_name="联系电话")
    email = models.EmailField(max_length=128, blank=True, default="", verbose_name="邮箱")
    address = models.CharField(max_length=255, blank=True, default="", verbose_name="详细地址")
    license_url = models.URLField(max_length=512, blank=True, default="", verbose_name="营业执照")
    # 地区：area_id 指向 apps/users/areas.py 静态树的节点 id，area_path 是「省/市/区」展示文本
    area_id = models.IntegerField(default=0, verbose_name="地区ID")
    area_path = models.CharField(max_length=255, blank=True, default="", verbose_name="地区名称")
    audit_status = models.SmallIntegerField(
        choices=AuditStatus.choices,
        default=AuditStatus.PENDING,
        verbose_name="审核状态",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "customer_profile"
        verbose_name = "客户资料"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.company_name or '-'}({self.user_id})"
