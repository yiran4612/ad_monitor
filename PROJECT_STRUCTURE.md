# ad_monitor 项目结构说明

> 亿叮咚·客户广告投放监察平台 — Django 后端
> 设计原则：分层清晰、AI 可生成区域与人工控制区域边界明确

---

## 一、目录树

```
ad_monitor/
├── manage.py
├── .env.example                          # 环境变量模板（人工维护）
├── .env                                  # 实际环境变量（gitignore）
│
├── ad_monitor/                           # Django 项目配置包
│   ├── __init__.py
│   ├── settings/                         # 配置拆分
│   │   ├── __init__.py
│   │   ├── base.py                       #   基础配置（人工）
│   │   ├── dev.py                        #   开发环境覆盖（人工）
│   │   └── prod.py                       #   生产环境覆盖（人工）
│   ├── urls.py                           # 根路由（AI 注册 + 人工审查）
│   ├── celery.py                         # Celery 实例配置（人工）
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/                                 # 业务应用层（7 个 bounded context）
│   ├── __init__.py
│   ├── accounts/                         # 用户认证（29 个接口）
│   ├── adplatform/                      # 广告平台（10 个接口）
│   ├── placement/                       # 点位投放（4 个接口）
│   ├── finance/                          # 资金管理（16 个接口）
│   ├── buildings/                       # 楼宇管理
│   ├── adschedule/                       # 投放配置
│   └── sales/                            # 套餐管理（2 个接口）
│
├── services/                             # 服务层（跨 app 外部集成）
│   ├── __init__.py
│   ├── oss_service.py                    # 阿里云 OSS（STS 临时凭证）
│   ├── payment_service.py                # 微信支付
│   ├── sms_service.py                    # 阿里云短信
│   ├── wechat_service.py                 # 微信开放平台
│   └── area_service.py                   # 行政区划数据
│
├── tasks/                                # Celery 异步任务层
│   ├── __init__.py
│   ├── celery_app.py                     # Celery 实例
│   ├── video_tasks.py                    # 视频转码 / 截图
│   └── batch_tasks.py                    # 批量导入 / 定时扣费
│
├── core/                                 # 公共基础设施
│   ├── __init__.py
│   ├── response.py                        # 统一响应 { code, data, msg }
│   ├── exceptions.py                     # 自定义异常 + 全局 handler
│   ├── permissions.py                    # 权限类
│   ├── pagination.py                     # 分页类
│   ├── mixins.py                         # ViewSet mixin
│   ├── models.py                         # 抽象 Model 基类
│   └── utils.py                          # 工具函数
│
└── requirements/                         # 依赖拆分
    ├── base.txt                          # 核心依赖
    ├── dev.txt                           # 开发工具（-r base.txt）
    └── prod.txt                           # 生产部署（-r base.txt）
```

### 每个 app 内部结构（以 `apps/accounts/` 为例）

```
apps/accounts/
├── __init__.py
├── apps.py                               # AppConfig
├── models.py                             # 数据模型定义
├── serializers.py                        # DRF 序列化器
├── views.py                              # ViewSet
├── urls.py                               # 路由注册（SimpleRouter）
├── filters.py                            # django-filter 过滤器
├── admin.py                              # Django Admin 注册
├── services.py                           # app 内业务逻辑
├── migrations/
│   └── __init__.py
└── tests.py                              # 单元测试
```

---

## 二、各层职责说明

### 1. `ad_monitor/` — 项目配置包

| 文件 | 职责 |
|------|------|
| `settings/base.py` | INSTALLED_APPS、中间件链、DRF 配置、数据库引擎、时区语言 |
| `settings/dev.py` | DEBUG=True、SQLite、本地 Redis |
| `settings/prod.py` | DEBUG=False、MySQL、安全密钥从 .env 读取 |
| `urls.py` | `include()` 各 app 路由 + DRF browsable API |
| `celery.py` | Celery broker 配置、autodiscover_tasks |

### 2. `apps/` — 业务应用层

每个 app 是一个 bounded context，对应前端一个业务模块：

| App | 对应前端模块 | 核心接口前缀 | 职责 |
|-----|-------------|-------------|------|
| `accounts` | account.ts | `/user/login`, `/user/register`... | 登录/注册/密码/验证码/微信/实名认证 |
| `adplatform` | materials.ts | `/element/content/*`, `/element/advPlatform/*` | 广告素材 CRUD、广告位管理 |
| `placement` | materials.ts | `/element/position/*` | 投放详情、每日播放列表 |
| `finance` | balance.ts + account.ts | `/userAmount/*` | 充值/提现/扣费统计/余额 |
| `buildings` | materials.ts | `/user/getAllLy`, `/user/saveAdLy`... | 楼宇选择/投放楼宇管理 |
| `adschedule` | materials.ts | `/user/adElementList`, `/user/saveDateAdSet`... | 投放计划/日期配置/任务状态 |
| `sales` | materials.ts | `/sale/myLists`, `/sale/mySetsCount` | 套餐查询 |

**app 内部各文件职责：**

| 文件 | 职责 |
|------|------|
| `models.py` | 定义数据表结构、字段、关系、Meta 选项 |
| `serializers.py` | ModelSerializer，定义 API 输入/输出字段映射 |
| `views.py` | ViewSet，定义 CRUD/action 方法，调用 services |
| `urls.py` | SimpleRouter 注册 ViewSet，导出 urlpatterns |
| `filters.py` | django-filter FilterSet，定义查询参数过滤 |
| `admin.py` | Django Admin 注册，定义列表/详情/过滤器 |
| `services.py` | app 内复杂业务逻辑（跨 Model 操作、事务） |
| `tests.py` | pytest / Django TestCase 单元测试 |

### 3. `services/` — 服务层（跨 app 外部集成）

不依赖任何 app 的 Model，封装第三方 SDK 调用：

| 文件 | 职责 |
|------|------|
| `oss_service.py` | 阿里云 OSS STS 临时凭证签发、文件 URL 生成 |
| `payment_service.py` | 微信支付 Native 下单、支付状态查询 |
| `sms_service.py` | 阿里云短信验证码发送 |
| `wechat_service.py` | 微信扫码登录、用户信息获取 |
| `area_service.py` | 行政区域树形数据查询 |

### 4. `tasks/` — Celery 异步任务层

| 文件 | 职责 |
|------|------|
| `celery_app.py` | Celery 实例创建、配置、autodiscover |
| `video_tasks.py` | 视频上传后异步处理：转码、截图、参数校验 |
| `batch_tasks.py` | 批量楼宇导入、定时扣费计算、投放任务状态轮询 |

### 5. `core/` — 公共基础设施

| 文件 | 职责 |
|------|------|
| `response.py` | 统一响应格式 `ResponseData(code, data, msg)` + APIResponse 工具函数 |
| `exceptions.py` | 业务异常基类 `BizError` + DRF 全局 exception_handler |
| `permissions.py` | IsOwnerOrReadOnly 等自定义权限 |
| `pagination.py` | 统一分页类（page_size, page_query_param） |
| `mixins.py` | ViewSet mixin（如软删除、逻辑删除） |
| `models.py` | 抽象基类 `TimeStampedModel`（created_at, updated_at, is_deleted） |
| `utils.py` | MD5 哈希、随机字符串、日期格式化等纯函数 |

### 6. `requirements/` — 依赖拆分

| 文件 | 内容 |
|------|------|
| `base.txt` | Django + DRF + 依赖库（生产也需要） |
| `dev.txt` | `-r base.txt` + ipdb, django-debug-toolbar, pytest-django, factory_boy |
| `prod.txt` | `-r base.txt` + gunicorn, mysqlclient |

---

## 三、AI 自动生成 vs 人工控制

### AI 可自动生成（模板化、可从 Model 推导）

以下文件遵循固定模式，AI 可根据 `models.py` 定义自动生成：

| 目录/文件 | 生成依据 | 说明 |
|-----------|---------|------|
| `apps/*/serializers.py` | models.py 字段 | ModelSerializer 字段映射 |
| `apps/*/views.py` | models.py + serializers.py | ViewSet CRUD 模板 |
| `apps/*/urls.py` | views.py | SimpleRouter 注册 |
| `apps/*/filters.py` | models.py 字段 | FilterSet 查询参数 |
| `apps/*/admin.py` | models.py | Admin 注册 + list_display |
| `apps/*/tests.py` | models.py + views.py | CRUD 测试用例 |
| `apps/*/migrations/` | models.py | `makemigrations` 自动生成 |
| `core/response.py` | 固定约定 | 统一响应格式 |
| `core/pagination.py` | 固定约定 | 分页参数 |
| `core/permissions.py` | 固定模式 | 权限类模板 |

### 人工控制（架构决策 / 业务逻辑 / 安全敏感）

以下文件涉及架构决策或安全敏感信息，必须由人工编写或审查：

| 目录/文件 | 原因 |
|-----------|------|
| `apps/*/models.py` | 数据模型是核心架构决策，字段/关系/索引需人工设计 |
| `apps/*/services.py` | 复杂业务逻辑（事务、跨表操作、业务规则）需人工实现 |
| `ad_monitor/settings/` | 安全密钥、中间件链、数据库配置不可自动生成 |
| `services/*.py` | 第三方 SDK 集成涉及密钥和业务流程，需人工编写 |
| `tasks/*.py` | 异步任务流程设计需人工定义 |
| `core/exceptions.py` | 业务异常体系需人工设计 |
| `.env` | 包含密钥，不可自动生成 |
| `requirements/` | 依赖版本锁定需人工决策 |

### 混合模式（AI 生成草稿 + 人工审查）

| 文件 | AI 负责 | 人工负责 |
|------|---------|---------|
| `ad_monitor/urls.py` | 生成 `include()` 注册代码 | 审查路由前缀和顺序 |
| `ad_monitor/celery.py` | 生成 Celery 配置模板 | 确认 broker 和队列配置 |
| `core/utils.py` | 生成工具函数 | 审查安全相关函数 |

---

## 四、请求流转路径

```
HTTP Request
  │
  ▼
ad_monitor/urls.py ── include() ──▶ apps/<app>/urls.py
                                        │
                                        ▼
                                  apps/<app>/views.py (ViewSet)
                                        │
                                        ▼
                                  apps/<app>/services.py (业务逻辑)
                                        │                    │
                                        ▼                    ▼
                                  apps/<app>/models.py   services/*.py (外部集成)
                                        │                    │
                                        ▼                    ▼
                                     Database            OSS / 微信支付 / 短信
                                        │
                                        ▼
                                  core/response.py
                                  { code: 200, data, msg }
```

---

## 五、AI 协作约定

1. **Model 先行** — 人工设计 `models.py` 后，AI 依据字段定义批量生成 serializer / view / filter / admin / test
2. **文件名固定** — 每个 app 内部文件名必须一致，不可自定义命名
3. **响应统一** — 所有 view 返回 `core.response.APIResponse`，不可直接返回 dict
4. **异常统一** — 业务错误抛 `core.exceptions.BizError`，全局 handler 统一捕获
5. **不跨层调用** — view 不直接操作 Model（除简单 CRUD），复杂逻辑走 services
6. **migrations 不手写** — 由 `makemigrations` 自动生成，不可手动编辑
