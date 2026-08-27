from pathlib import Path
import os

from dotenv import load_dotenv

from .base import *  # noqa
# ===== JWT 有效期 =====
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(BASE_DIR / "db.sqlite3"),
    }
}

DEBUG = True

# 开发期放开 Host 校验，避免 DisallowedHost（生产由 prod.py 收紧）
ALLOWED_HOSTS = ["*"]

CORS_ALLOW_ALL_ORIGINS = True

INSTALLED_APPS = [
    # ===== Django 内置（必须保留）=====
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # ===== 第三方 =====
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "corsheaders",

    # ===== 项目应用 =====
    "apps.users",
    "apps.ads",
]

# ===== JWT 配置 =====
# 默认access token有效期为5分钟，refresh token有效期为1天，开发期可以调整为更长时间，方便测试   
SIMPLE_JWT = {
    # 签名密钥沿用 base 的环境变量 JWT_SIGNING_KEY（未设置时回退 SECRET_KEY）
    "SIGNING_KEY": JWT_SIGNING_KEY,
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=24),   # 改成 24 小时
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),    # 改成 7 天
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
}

# ===== Celery =====
from celery.schedules import crontab

# broker/backend 支持环境变量覆盖（容器/CI 注入），本地默认连开发机 Redis
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://192.168.175.3:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://192.168.175.3:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Shanghai"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = False

# ===== Celery Beat 定时调度 =====
# 每 10 分钟扫描一次投放中活动的视频素材（Beat 由 celery -A ad_monitor beat 启动）
CELERY_BEAT_SCHEDULE = {
    "scan-campaigns-every-10-min": {
        "task": "ads.scan_campaigns",
        "schedule": crontab(minute="*/10"),
    },
}

# ===== DRF Spectacular (API 文档) =====
SPECTACULAR_SETTINGS = {
    "TITLE": "Ad Monitor API",
    "DESCRIPTION": "广告合规监测平台接口文档",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": True,
    # JWT 认证：让文档页面支持填 Token
    "SECURITY_DEFINITIONS": {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    },
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    # 自动打 tag 分组
    "TAGS": [
        {"name": "auth", "description": "认证：注册 / 登录 / Token 刷新"},
        {"name": "advertisers", "description": "广告主管理"},
        {"name": "campaigns", "description": "广告活动管理"},
        {"name": "violations", "description": "违规记录 & 处置"},
        {"name": "monitor-rules", "description": "监测规则"},
        {"name": "tasks", "description": "异步任务提交与查询"},
    ],
}