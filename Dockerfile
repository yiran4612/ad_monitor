# Layer: infrastructure
# ad_monitor 镜像：web / celery-worker / celery-beat 共用
# 数据库策略：SQLite + named volume（/app/docker-data 挂载持久化），暂不引入 Postgres
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=core.settings.docker

WORKDIR /app

# 依赖全部为 wheel / 纯 Python 包（无 mysqlclient / psycopg2），
# slim 镜像无需编译链，直接安装
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 先拷依赖清单再拷代码，利用镜像层缓存
COPY . .

# 非 root 运行；预建 SQLite/静态/媒体目录并授权
# （/app/docker-data 由 compose named volume 挂载，volume 首次挂载会继承目录属主）
RUN useradd --create-home --shell /bin/sh appuser \
    && mkdir -p /app/staticfiles /app/media /app/docker-data \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# 启动：迁移 → 收集静态文件 → gunicorn（celery 服务在 compose 中覆盖 command）
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn ad_monitor.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120"]
