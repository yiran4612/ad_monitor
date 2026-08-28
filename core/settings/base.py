# Layer: infrastructure
"""
Django 4.2 base settings for ad_monitor project.

此文件包含所有环境共享的基础配置。
环境差异配置由 dev.py / prod.py 覆盖。

JWT 工具统一使用 core.auth.jwt.JWTService，禁止在 View / Service 中
直接调用 SimpleJWT 的 serializer。
"""

from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# ──────────────────────────────────────────────
# 1. 基础路径 & 环境变量
# 找到 .env 文件并加载
# ──────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 加载 .env（BASE_DIR/.env），环境变量优先于文件
load_dotenv(BASE_DIR / ".env")

import os

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-CHANGE-ME-IN-PRODUCTION")

# JWT 签名密钥：优先读环境变量 JWT_SIGNING_KEY（>= 32 字节，容器/生产必填），
# 未设置时回退到 SECRET_KEY（本地开发）。SimpleJWT 会自动使用该值签发/校验 Token。
JWT_SIGNING_KEY = os.environ.get("JWT_SIGNING_KEY") or SECRET_KEY

DEBUG = True

ALLOWED_HOSTS: list[str] = []


# ──────────────────────────────────────────────
# 2. 自定义用户模型
# ──────────────────────────────────────────────
# apps/users/apps.py 中 name='apps.users'，Django 默认 label='users'
AUTH_USER_MODEL = "users.User"


# ──────────────────────────────────────────────
# 3. INSTALLED_APPS
# ──────────────────────────────────────────────

INSTALLED_APPS = [
    # --- Django 内置 ---
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # --- 第三方 ---
    "rest_framework",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "import_export",
    "django_extensions",
    "django_cleanup.apps.CleanupConfig",
    # --- 业务 App ---
    # "apps.users",
    "apps.users.apps.UsersConfig",
    "apps.ads.apps.AdsConfig",
]


# ──────────────────────────────────────────────
# 4. 中间件
# ──────────────────────────────────────────────

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # CORS 必须在最前
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ──────────────────────────────────────────────
# 5. URL 路由
# ──────────────────────────────────────────────

ROOT_URLCONF = "ad_monitor.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "ad_monitor.wsgi.application"
ASGI_APPLICATION = "ad_monitor.asgi.application"


# ──────────────────────────────────────────────
# 6. 数据库（dev.py / prod.py 覆盖）
# ──────────────────────────────────────────────

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ──────────────────────────────────────────────
# 7. 国际化
# ──────────────────────────────────────────────

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True


# ──────────────────────────────────────────────
# 8. 静态文件 & 媒体文件
# ──────────────────────────────────────────────

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ──────────────────────────────────────────────
# 9. DRF 配置
# ──────────────────────────────────────────────

REST_FRAMEWORK = {
    # 认证：SimpleJWT
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework_simplejwt.authentication.JWTAuthentication",),
    # 权限：默认需要登录（注册/登录视图在 apps/users/views.py 显式 AllowAny）
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    # 分页
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    # 过滤
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    # Schema
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}


# ──────────────────────────────────────────────
# 10. SimpleJWT 配置
# ──────────────────────────────────────────────
# JWTService（core/auth/jwt.py）封装了 SimpleJWT 的
# RefreshToken / AccessToken，自动读取以下配置。
# 禁止在 View / Service 中直接使用 SimpleJWT serializer。
# ──────────────────────────────────────────────

SIMPLE_JWT = {
    # 签名密钥：独立于 Django SECRET_KEY，来源环境变量 JWT_SIGNING_KEY
    "SIGNING_KEY": JWT_SIGNING_KEY,
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "TOKEN_BLACKLIST_ENABLED": True,
    "UPDATE_LAST_LOGIN": True,
    "TOKEN_TYPE_CLAIM": "token_type",
    "JTI_CLAIM": "jti",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "SERIALIZER_CLAIMS": "apps.users.serializers.CustomTokenObtainPairSerializer",
}


# ──────────────────────────────────────────────
# 11. CORS 配置（dev.py 覆盖具体白名单）
# ──────────────────────────────────────────────

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True


# ──────────────────────────────────────────────
# 12. drf-spectacular
# ──────────────────────────────────────────────

SPECTACULAR_SETTINGS = {
    "TITLE": "ad_monitor API",
    "DESCRIPTION": "亿叮咚·客户广告投放监察平台后端 API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}


# ──────────────────────────────────────────────
# 13. 密码校验器
# ──────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ──────────────────────────────────────────────
# 14. 登录 / 登出 URL（Django Admin 用）
# ──────────────────────────────────────────────

LOGIN_URL = "admin:login"
LOGOUT_URL = "admin:logout"
LOGIN_REDIRECT_URL = "/admin/"
