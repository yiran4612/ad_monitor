# Layer: infrastructure
"""
Docker 容器专用 settings（compose 中 DJANGO_SETTINGS_MODULE=core.settings.docker）。

数据库策略：
- DB_ENGINE=sqlite（默认）→ 落盘 /app/docker-data/db.sqlite3（compose named volume
  sqlite_data 挂载该目录持久化），无需额外 DB 服务
- DB_ENGINE=postgres      → 读 POSTGRES 系列环境变量，连接外部 DB（后续引入）

其他关键环境变量：
- JWT_SIGNING_KEY / SECRET_KEY：密钥（生产必填，>= 32 字节）
- CELERY_BROKER_URL / CELERY_RESULT_BACKEND：默认 redis://redis:6379/0（compose 注入）
- DEBUG / ALLOWED_HOSTS：生产默认关 DEBUG、Host 可配置
"""

import os
from pathlib import Path

from dotenv import load_dotenv

from .base import *

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 容器内由 compose env_file(.env) 注入环境变量（环境变量优先于文件），此处仅作直跑兜底
load_dotenv(BASE_DIR / ".env")

# ──────────────────────────────────────────────
# 1. 基础开关
# ──────────────────────────────────────────────

DEBUG = os.environ.get("DEBUG", "false").lower() in ("1", "true", "yes")

# 容器内默认放开（compose 网络内由上游 Nginx 收紧），可用 ALLOWED_HOSTS 覆盖
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "*").split(",") if h.strip()]

# ──────────────────────────────────────────────
# 2. 数据库策略：sqlite（默认）/ postgres
# ──────────────────────────────────────────────

# 当前固定 SQLite（named volume 持久化）；设置 DB_ENGINE=postgres 可切换（后续引入）
_DB_ENGINE = os.environ.get("DB_ENGINE", "sqlite").lower()

if _DB_ENGINE == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            # 默认落在 /app/docker-data/db.sqlite3（compose named volume 挂载目录）
            "NAME": BASE_DIR / os.environ.get("SQLITE_PATH", "docker-data/db.sqlite3"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME", "ad_monitor"),
            "USER": os.environ.get("DB_USER", "ad_monitor"),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "db"),
            "PORT": os.environ.get("DB_PORT", "5432"),
            "CONN_MAX_AGE": int(os.environ.get("DB_CONN_MAX_AGE", "60")),
        }
    }

# ──────────────────────────────────────────────
# 3. Celery：默认连接 compose 网络的 redis 服务，可用环境变量覆盖
# ──────────────────────────────────────────────

# 兼容旧 REDIS_URL 变量；均未设置时回退 redis://redis:6379/0（compose 中已注入）
_redis_url = os.environ.get("REDIS_URL")
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL") or _redis_url or "redis://redis:6379/0"
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND") or _redis_url or "redis://redis:6379/0"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_ACKS_LATE = True
# 容器内由独立 celery 服务执行任务，不走 eager 模式
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = False

# ──────────────────────────────────────────────
# 3.1 Celery Beat 定时调度
# ──────────────────────────────────────────────

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "scan-campaigns-every-10-min": {
        "task": "ads.scan_campaigns",
        "schedule": crontab(minute="*/10"),
    },
}

# ──────────────────────────────────────────────
# 4. CORS（由环境变量控制白名单，默认放开）
# ──────────────────────────────────────────────

CORS_ALLOW_ALL_ORIGINS = os.environ.get("CORS_ALLOW_ALL_ORIGINS", "true").lower() in (
    "1",
    "true",
    "yes",
)

# ──────────────────────────────────────────────
# 5. 静态文件：collectstatic 输出到 volume
# ──────────────────────────────────────────────

STATIC_ROOT = BASE_DIR / os.environ.get("STATIC_ROOT_DIR", "staticfiles")
