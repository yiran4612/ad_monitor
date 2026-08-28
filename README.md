# AdMonitor · 广告监测系统

基于 **Django 5.2 + Django REST Framework + Celery** 的广告内容合规监测系统。

支持：广告主 / 营销活动 / 广告素材管理、基于关键词规则的内容审核、异步视频检测任务、定时扫描调度。

---

## 📁 项目结构
ad_monitor/

├── ad_monitor/          # 项目配置（settings / urls / celery / wsgi）

│   ├── init.py

│   ├── celery.py        # Celery app

│   ├── settings/

│   │   ├── dev.py       # 开发环境

│   │   └── docker.py    # Docker 环境

│   └── urls.py

├── core/                # 核心配置（公共 settings）

├── apps/

│   └── ads/             # 业务应用

│       ├── models/      # Advertiser / Campaign / Creative / Violation / MonitorRule

│       ├── serializers/

│       ├── services/    # Service 层（含 DetectionService）

│       ├── views/

│       ├── tasks.py     # Celery 任务（scan_campaigns / detect_video）

│       └── urls.py

├── tests/               # pytest 测试（28 用例）

├── requirements/        # 依赖拆分（base / docker ...）

├── requirements.txt

├── Dockerfile

├── docker-compose.yml

├── .env.example

└── manage.py

---

## 🚀 快速开始

### 方式一：本地开发
bash

1. 创建虚拟环境

python -m venv .venv

.venv\Scripts\activate        # Windows

source .venv/bin/activate # Linux/Mac
2. 安装依赖

pip install -r requirements.txt

3. 配置环境变量（可选，有默认值）

cp .env.example .env

4. 迁移数据库

python manage.py makemigrations ads

python manage.py migrate

5. 启动开发服务器

python manage.py runserver

6. 运行测试

pytest -v

### 方式二：Docker（推荐）
bash

1. 准备环境变量

cp .env.example .env

2. 一键构建并启动（web + worker + beat + redis）

docker compose up -d --build

3. 查看服务状态

docker compose ps

4. 验证

curl http://localhost:8000/api/ads/creatives/

docker compose exec redis redis-cli ping   # 期望 PONG

5. 停止

docker compose down          # 保留数据 volume

docker compose down -v     # ⚠️ 会删除数据库，慎用

---

## 🔧 核心组件

| 组件 | 说明 |
|------|------|
| **Web (Django + DRF)** | RESTful API，端口 8000 |
| **Celery Worker** | 消费异步检测任务（`--pool=solo` 兼容 Windows） |
| **Celery Beat** | 定时调度，每 10 分钟扫描活跃 Campaign |
| **Redis** | Broker + Result Backend，端口 6379 |

### 主要 Celery 任务

- `ads.scan_campaigns`：扫描 `RUNNING` 状态的 Campaign，对其中视频素材触发检测
- `ads.detect_video`：执行单条视频检测（关键词规则匹配）
- `ads.process_creative`：素材处理

---

## 🔐 环境变量（`.env`）

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DEBUG` | 调试模式 | `True` |
| `SECRET_KEY` | Django 密钥（生产务必更换，≥32 字节） | — |
| `JWT_SIGNING_KEY` | SimpleJWT 签名密钥（≥32 字节） | — |
| `ALLOWED_HOSTS` | 允许的主机 | `localhost,127.0.0.1` |
| `CELERY_BROKER_URL` | Celery Broker | `redis://redis:6379/0`（Docker）/ `redis://192.168.175.3:6379/0`（本地） |
| `CELERY_RESULT_BACKEND` | 结果后端 | 同上 |
| `VIDEO_DETECTION_BACKEND` | 视频检测后端 | `placeholder` |

---

## 📝 API 参考

> 统一返回格式：`{code, msg, data}`
> 认证：`Authorization: Bearer <access_token>`（注册/登录除外）
> 交互文档：http://localhost:8000/api/docs/ （Swagger UI）
> 管理后台：http://localhost:8000/admin/

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/users/register/` | 注册 |
| POST | `/api/users/login/` | 登录，返回 access + refresh token |

### 广告主 `/api/ads/advertisers/`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 列表 |
| POST | `/` | 创建 |
| GET | `/{id}/` | 详情 |
| PATCH | `/{id}/` | 更新 |
| DELETE | `/{id}/` | 删除 |

### 营销活动 `/api/ads/campaigns/`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 列表 |
| POST | `/` | 创建 |
| GET | `/{id}/` | 详情 |
| PATCH | `/{id}/` | 更新 |
| DELETE | `/{id}/` | 删除 |
| POST | `/{id}/status/` | 更新状态（draft/running/paused/ended） |

### 素材 `/api/ads/creatives/`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 列表（支持 `?campaign={id}` 过滤） |
| POST | `/` | 创建 |
| GET | `/{id}/` | 详情 |
| PATCH | `/{id}/` | 更新 |
| DELETE | `/{id}/` | 删除（软删） |

### 监测规则 `/api/ads/monitor-rules/`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 列表 |
| POST | `/` | 创建 |
| GET | `/{id}/` | 详情 |
| PATCH | `/{id}/` | 更新 |
| DELETE | `/{id}/` | 删除 |

### 违规记录 `/api/ads/violations/`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 列表（支持 `?status=` 过滤） |
| POST | `/` | 创建 |
| GET | `/{id}/` | 详情 |
| PATCH | `/{id}/` | 更新 |
| DELETE | `/{id}/` | 删除 |
| POST | `/{id}/resolve/` | 处理违规 |

### 检测任务 `/api/tasks/`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 列表 |
| POST | `/` | 触发检测 |
| GET | `/{id}/` | 查询任务状态 |

---

## 🧪 测试

pytest -v

| 模块 | 用例数 | 说明 |
|------|--------|------|
| test_advertiser.py | 5 | CRUD |
| test_auth.py | 3 | 注册 / 登录 / 错误密码 |
| test_task.py | 2 | 触发检测 / 查询状态（Celery mocked） |
| test_violation.py | 4 | CRUD + 处理 |
| test_creative.py | 7 | CRUD + 审批/驳回 |
| test_e2e_detection.py | 7 | 端到端扫描链路（真实写 DB，不下载） |
| **合计** | **28** | ✅ 全绿 |

---

## 🐳 Docker 服务说明

`docker-compose.yml` 编排 4 个服务：

| 服务 | 镜像 | 说明 |
|------|------|------|
| `web` | 本地构建（`python:3.11-slim`） | gunicorn，端口 8000 |
| `celery-worker` | 本地构建 | 消费任务，`--pool=solo` |
| `celery-beat` | 本地构建 | 定时调度 |
| `redis` | `redis:7-alpine` | Broker，端口 6379 |

数据持久化：`sqlite_data` 命名 volume 挂载到 `/app/docker-data`。

---

## 🔮 后续规划

- [ ] **真实视频检测**：替换 `DetectionService.fetch_video_text` 占位逻辑（OCR/ASR/模型），当前为元数据关键词匹配
- [ ] **PostgreSQL 切换**：`docker.py` 已留配置分支，compose 加 postgres 服务即可
- [ ] **CI/CD**：GitHub Actions 自动跑 pytest + check
- [ ] **生产部署**：nginx 反代、HTTPS、Sentry、日志收集

---

## 📄 License

私有项目，仅供学习/内部使用。