# 知识库检索系统 - 项目文档

> 本文档由 README.md、MANIFEST.md、PROJECT_STRUCTURE.md、USAGE_GUIDE.md、test_case.md 以及两个开发计划合并重组而成，按主题分层，去除重复和过时信息。

---

## 目录

1. [项目概述](#一项目概述)
2. [技术架构](#二技术架构)
3. [部署指南](#三部署指南)
4. [使用指南](#四使用指南)
5. [测试文档](#五测试文档)
6. [开发路线图](#六开发路线图)

---

## 一、项目概述

KB Search 是一款知识库检索系统，支持 Markdown、HTML、DOCX 格式文档的上传、解析与全文检索。

**核心能力**：

| 能力 | 状态 | 说明 |
|------|------|------|
| 用户注册/登录 | ✅ | JWT + bcrypt |
| 文档上传 | ✅ | 支持 MD/HTML/DOCX，最大 20MB |
| 异步解析 | ✅ | Celery Worker，前端进度轮询 |
| 全文搜索 | ✅ | PostgreSQL `tsvector` (simple) + 高亮 + 摘要 |
| 搜索排序 | ✅ | 相关度 / 时间 / 浏览量 |
| 自动补全建议 | ✅ | 基于历史搜索前缀匹配 |
| 热门搜索排行 | ✅ | 24 小时统计 |
| 分类树浏览 | ✅ | 三级分类 + 面包屑 |
| 浏览量统计 | ✅ | 原子计数器 |
| 相关推荐 | ❌ | Phase 2 待开发 |

**技术栈**：FastAPI + SQLModel + PostgreSQL 15 + Redis 7 + Celery + Vue 3 + Element Plus

**目标环境**：1核 / 3GB 内存（Docker Compose 部署）

**交付统计（MVP v1.0）**：
- 总文件数：46
- 代码总行数：~3,700
- 后端文件：24（含模型、路由、服务、任务、工具）
- 前端文件：20（含视图、API、工具、状态管理）

**前端页面**：

| 页面 | 路径 | 功能 |
|------|------|------|
| 搜索 | `/` | 核心搜索 + 热搜 + 结果列表 |
| 登录/注册 | `/login` | JWT 认证 |
| 文档详情 | `/document/:id` | 内容展示 + 浏览量 +1 + 相关推荐（Phase 2） |
| 上传 | `/upload` | 文件上传 + 解析进度轮询 |
| 分类浏览 | `/categories` | 树形导航 + 面包屑 |

**关键环境变量**：`DATABASE_URL`、`REDIS_URL`、`CELERY_BROKER_URL`、`SECRET_KEY`、`MAX_UPLOAD_SIZE`、`AUTH_TYPE`

---

## 二、技术架构

### 2.1 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户浏览器                              │
│                   http://localhost:8080                       │
└──────────────────────┬────────────────────────────────────────┘
                       │
              ┌────────▼────────┐
              │   Nginx (可选)   │
              │   反向代理       │
              └────────┬────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼────┐   ┌────▼────┐   ┌─────▼─────┐
   │ 前端     │   │ FastAPI │   │  Celery   │
   │ Vue3     │   │  Web    │   │  Worker   │
   │ :8080    │   │ :8000   │   │  (异步)   │
   └────┬────┘   └────┬────┘   └─────┬─────┘
        │             │               │
        │      ┌────┴────┐     ┌────┴────┐
        │      │PostgreSQL│     │  Redis  │
        │      │  :5432   │     │ :6379   │
        │      │  simple  │     │ 队列/缓存│
        │      │tokenizer│     └─────────┘
        │      └─────────┘
   ┌────▼────────────────────────────────────┐
   │ 前端开发服务器代理规则                      │
   │ /api/*  -> http://localhost:8000          │
   │ /*      -> 前端静态资源                    │
   └──────────────────────────────────────────┘
```

### 2.2 容器资源分配（1核3G）

| 容器 | 内存限制 | 说明 |
|------|----------|------|
| web (FastAPI + Gunicorn) | 512MB | 1 个 Uvicorn Worker |
| worker (Celery) | 512MB | 2 并发解析任务 |
| beat (Celery 调度器) | 128MB | 定时任务调度 |
| db (PostgreSQL 15) | 1GB | shared_buffers=256MB |
| redis (Redis 7) | 256MB | 开启 RDB + AOF 持久化 |
| 系统预留 | ~700MB | 缓冲余量 |

### 2.3 后端目录结构

```
app/
├── main.py                 # FastAPI 入口，路由注册，生命周期
├── config.py              # Pydantic Settings（环境变量 + 默认值）
├── database.py            # SQLModel engine + Session 依赖注入
│
├── models/                # 数据模型（SQLModel）
│   ├── user.py            # 用户表：username, auth_type, is_admin
│   ├── category.py        # 分类表：name, parent_id, path(物化路径)
│   ├── document.py        # 文档表：title, content, search_vector(tsvector)
│   └── search_log.py      # 搜索日志：query, user_id, result_count
│
├── routers/               # API 路由层
│   ├── auth.py            # 注册/登录/刷新 Token
│   ├── documents.py       # 文档 CRUD + 上传 + 状态查询
│   ├── search.py          # 搜索/建议/热门/纠错
│   └── categories.py      # 分类树 + 面包屑 + 创建
│
├── services/              # 业务逻辑层
│   ├── document_parser.py # MD/HTML/DOCX 解析器
│   ├── search_service.py  # 全文搜索 + 搜索建议 + 热门排行
│   ├── spell_corrector.py # 基于标题和历史查询的拼写纠错
│   └── stats_service.py   # 作者排行 + 文档热度 + 分类统计（预留）
│
├── tasks/                 # Celery 异步任务
│   └── document_tasks.py  # parse_document_task, update_search_vector, clean_old_uploads
│
└── utils/                 # 工具函数
    ├── security.py        # JWT 生成/验证 + bcrypt 密码哈希
    ├── text_utils.py      # Markdown 去标记 + 摘要生成 + 关键词高亮
    └── logger.py          # 结构化日志配置（structlog）
```

### 2.4 前端目录结构

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── main.js            # Vue3 入口：Pinia + Router + ElementPlus
│   ├── App.vue            # 根组件
│   ├── router/index.js    # 路由表
│   ├── store/user.js      # Pinia Store：token, userInfo, login/logout
│   ├── utils/
│   │   ├── request.js     # Axios 封装：baseURL, JWT 拦截, 错误处理
│   │   └── common.js      # 防抖/节流
│   ├── api/               # API 接口层
│   │   ├── auth.js        # 登录/注册（使用 URLSearchParams + form-urlencoded）
│   │   ├── document.js    # 上传/列表/详情/状态
│   │   ├── search.js      # 搜索/建议/热门
│   │   └── category.js    # 分类树/面包屑
│   └── views/
│       ├── LoginView.vue      # 登录/注册页
│       ├── LayoutView.vue     # 主布局
│       ├── SearchView.vue     # 核心搜索页
│       ├── DocumentDetailView.vue  # 文档详情
│       ├── UploadView.vue     # 上传页（含表单验证 + 进度轮询）
│       └── CategoryView.vue   # 分类浏览
├── package.json
└── vue.config.js          # 开发代理：/api -> localhost:8000
```

### 2.5 数据流

**文档上传流程**：

```
用户选择文件 -> UploadView.vue
    |
    v
Axios POST /api/v1/documents (multipart/form-data)
    |
    v
FastAPI documents.py: 保存原始文件到 /tmp/uploads
    |
    v
创建 Document 记录（parse_status=pending）
    |
    v
Celery delay parse_document_task(doc_id, file_path, file_type)
    |
    v
返回 {id, task_id, parse_status: "pending"}
    |
    v
前端轮询 GET /api/v1/documents/{id}/status（每2秒）
    |
    v
Worker 解析完成 -> update_search_vector -> status=completed
    |
    v
前端显示"解析完成"，用户可搜索该文档
```

**搜索流程**：

```
用户输入关键词 -> SearchView.vue
    |
    v
Axios GET /api/v1/search?q=xxx&sort=relevance
    |
    v
PostgreSQL: SELECT ... WHERE search_vector @@ plainto_tsquery('simple', 'xxx')
    |
    v
返回结果（含高亮 HTML、相关度分数、摘要）
    |
    v
前端渲染：标题高亮 + 内容摘要 + 元信息
```

### 2.6 关键设计决策

| 决策 | 方案 | 理由 |
|------|------|------|
| 全文检索 | PostgreSQL tsvector (simple) | 1万文档量级够用，免运维 ES |
| 异步解析 | Celery + Redis | DOCX 解析可能耗时，不阻塞用户请求 |
| 文件存储 | /tmp (MVP) | 解析后删除原始文件，节省磁盘 |
| 前端状态 | Pinia | Vue3 官方推荐，TypeScript 友好 |
| 搜索建议 | 基于历史搜索前缀匹配 | 无需额外服务，数据自然积累 |
| 注册请求格式 | `application/x-www-form-urlencoded` | 匹配后端 FastAPI `Form(...)` 参数 |

### 2.7 扩展预留点

| 扩展点 | 当前预留 | 触发条件 |
|--------|----------|----------|
| Elasticsearch | 文档元数据结构兼容 | 数据量 > 50万或相关性不足 |
| 对象存储 | StorageBackend 抽象接口 | /tmp 不够或需要高可用 |
| SSO/LDAP | auth_type 字段 + AuthProvider 接口 | 企业接入需求 |
| 分片上传 | 前端 upload 组件预留 | 单文件 > 20MB 场景 |
| 监控告警 | prometheus-client 已安装 | 生产强化阶段 |

---

## 三、部署指南

### 3.1 环境要求

| 组件 | 版本 | 说明 |
|------|------|------|
| Docker | 20.10+ | 容器运行时 |
| Docker Compose | 2.0+ | 编排工具 |
| Node.js | 18.x+ | 前端开发（仅开发环境） |

### 3.2 首次启动

```bash
# 1. 配置环境变量（复制模板并编辑）
cp .env.example .env

# 2. 启动全栈（后台运行）
docker-compose up -d --build

# 3. 容器自动执行数据库迁移（entrypoint.sh 内部处理）
# 如需手动执行：docker-compose exec web alembic upgrade head

# 4. 验证服务状态
curl http://localhost:8000/health
# 预期返回：{"status":"ok","version":"0.1.0"}
```

### 3.3 日常运维

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f web      # 后端 API
docker-compose logs -f worker   # 异步任务
docker-compose logs -f beat     # 定时调度

# 重启服务
docker-compose restart web

# 停止所有服务
docker-compose down

# 停止并删除数据卷（谨慎！）
docker-compose down -v
```

### 3.4 数据库管理

```bash
# 进入数据库容器
docker-compose exec db psql -U kb -d kb

# 常用 SQL
\dt                          # 查看所有表
SELECT * FROM users;          # 查看用户
SELECT * FROM documents;      # 查看文档
SELECT * FROM search_logs;    # 查看搜索日志

# 退出
\q
```

### 3.5 备份与恢复

```bash
# 数据库备份
docker-compose exec db pg_dump -U kb -d kb > kb_backup_$(date +%Y%m%d).sql

# 数据库恢复
cat kb_backup_20260101.sql | docker-compose exec -T db psql -U kb -d kb

# Redis 手动备份
docker-compose exec redis redis-cli BGSAVE
```

### 3.6 生产配置要点

`docker-compose.yml` 关键配置说明：

- `command` 统一使用**数组格式**，避免 Docker 的 `sh -c` 包装导致的 PID 1 信号转发和 `$1` 参数解析问题
- `redis` 和 `db` 均配置 `healthcheck`，所有上游服务通过 `condition: service_healthy` 等待依赖就绪
- `web` 和 `worker` 设置 `stop_grace_period: 30s`，保证优雅关闭
- `worker` 和 `beat` 添加 `PYTHONPATH=/app`，确保 Celery 能找到应用模块
- `docker/entrypoint.sh` 为 web 容器提供自动数据库就绪检测 + `alembic upgrade head`
- 迁移是 idempotent 的，跳过 celery worker/beat 容器

---

## 四、使用指南

### 4.1 前端开发环境

```bash
cd frontend

# 安装依赖（首次）
npm install

# 启动开发服务器（自动代理 API 到 localhost:8000）
npm run serve

# 访问地址
open http://localhost:8080

# 构建生产包
npm run build   # 输出到 frontend/dist/
```

### 4.2 API 使用示例

**注册/登录**（注意使用 `application/x-www-form-urlencoded`）：

```bash
# 注册
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123"

# 登录
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123"
# 返回：{"access_token":"xxx","token_type":"bearer","expires_in":1800}

# 保存 token
TOKEN="your-access-token"
```

**上传文档**：

```bash
curl -X POST "http://localhost:8000/api/v1/documents" \
  -H "Authorization: Bearer $TOKEN" \
  -F "title=Python最佳实践" \
  -F "category_id=1" \
  -F "tags=Python,后端,教程" \
  -F "file=@/path/to/your/file.md"
```

**搜索**：

```bash
# 全文搜索
curl "http://localhost:8000/api/v1/search?q=Python&sort=relevance&page=1"

# 自动补全建议
curl "http://localhost:8000/api/v1/search/suggest?q=Py"

# 热门搜索
curl "http://localhost:8000/api/v1/search/hot?limit=10"

# 搜索纠错
curl "http://localhost:8000/api/v1/search/correct?q=Pythn"
```

**分类管理**：

```bash
# 查看分类树
curl "http://localhost:8000/api/v1/categories?tree=true"

# 面包屑导航
curl "http://localhost:8000/api/v1/categories/2/breadcrumb"
```

### 4.3 常见问题

**Q1: 启动后访问 http://localhost:8000 返回 404？**

后端 API 没有根页面，请访问：
- API 文档：`http://localhost:8000/docs`（Swagger UI）
- 健康检查：`http://localhost:8000/health`

前端页面在 `http://localhost:8080`

**Q2: 上传文件后一直显示"解析中"？**

检查 Worker 是否正常运行：
```bash
docker-compose logs -f worker
```

如果 Worker 未启动，检查 Redis 连接：
```bash
docker-compose exec redis redis-cli ping
# 应返回 PONG
```

**Q3: 搜索中文无结果？**

当前使用 PostgreSQL 内置 `simple` 分词配置。该模式按空格/标点切分，对中文文本**不切词**（如搜索"技术"无法匹配"技术部署"）。如需提升中文搜索质量，可：
- 使用 Python `jieba` 分词预处理文本后写入 `search_vector`
- 或评估迁移至 `pg_bigm`（N-gram 模糊匹配）
- 或文档量 > 5 万时评估 Elasticsearch + IK 分词

**Q4: 前端 npm install 报错？**

确保 Node.js 版本 >= 18：
```bash
node -v
# v18.x.x 或更高
```

**Q5: 如何修改上传文件大小限制？**

编辑 `.env` 文件：
```bash
MAX_UPLOAD_SIZE=52428800  # 50MB
```

同时修改 `frontend/src/views/UploadView.vue` 中的前端限制。

---

## 五、测试文档

### 5.1 测试策略

`tests/` 下的测试使用 `pytest` + `TestClient`，搭配**内存 SQLite** 数据库和 `StaticPool`。通过 `app.dependency_overrides[get_session]` 注入 SQLite 会话。

**测试特点**：
- 测试无需 Docker 即可快速运行
- **无法测试 PostgreSQL 特有功能**（`TSVECTOR`、触发器、GIN 索引）
- PostgreSQL 相关行为请使用 `docker-compose exec web pytest ...` 验证

**测试覆盖**：7 大模块，94 个测试场景，100% 路由覆盖，100% HTTP 状态码覆盖（200/400/401/403/404/422）。

### 5.2 运行测试

```bash
# 本地运行（SQLite，快速）
pytest tests/ -v

# 容器内运行（PostgreSQL，验证完整功能）
docker-compose exec web pytest tests/ -v

# 运行单个测试文件
pytest tests/test_api.py -v
```

### 5.3 测试模块覆盖

| 模块 | 用例数 | 覆盖类型 |
|------|--------|----------|
| Health | 5 | 服务健康、就绪检查、Prometheus 指标 |
| Auth | 15 | 注册/登录/刷新 Token、边界值、权限校验 |
| Documents | 29 | 上传/列表/详情/更新/删除、权限控制、边界值 |
| Search | 15 | 全文搜索/建议/热门/纠错、排序、分页边界 |
| Categories | 13 | 树形/扁平列表、面包屑、创建/更新/删除约束 |
| Tags | 10 | 标签云、按标签搜索、添加标签权限 |
| Stats | 7 | 作者排行、文档热度、分类统计 |

---

## 六、开发路线图

> 状态：2026-07-01 更新 | 当前阶段：MVP 维护，第二阶段待启动

### 6.1 里程碑总览

| 里程碑 | 时间 | 交付物 |
|--------|------|--------|
| MVP 上线 | W6 结束 | 可搜索的知识库系统，支持三格式上传 |
| 功能完善 | W10 结束 | 版本历史、附件、收藏、统计看板 |
| 生产优化 | W14 结束 | 监控告警、性能达标、SSO 对接 |

### 6.2 第一阶段：MVP（W1-W6）- 已完成

- ✅ 基础设施：Docker Compose、JWT 认证、文件上传
- ✅ 文档解析：Celery Worker、MD/HTML/DOCX 解析、状态轮询
- ✅ 搜索核心：tsvector 全文检索、高亮、摘要、排序
- ✅ 浏览体验：分类树、面包屑、文档详情、标签系统
- ✅ 搜索增强：搜索日志、热门排行、自动补全、拼写纠错
- ✅ 生产就绪：Gunicorn、结构化日志、Prometheus 指标、压测
- ✅ 容器自动迁移：`entrypoint.sh` 数据库就绪检测 + `alembic upgrade head`

### 6.3 Phase 0：当前阻塞项（已解决）

以下阻塞项在 MVP 维护阶段已完成：

- [x] 认证注册修复：前端改为 `URLSearchParams` + `form-urlencoded`，后端修复 `regex` 兼容性，恢复 `structlog` 依赖
- [x] 前端错误处理：Axios 拦截器统一处理 `detail` 数组/对象；Element Plus 表单验证添加 `catch`
- [x] 分类种子数据：新增 `004_seed_categories` 迁移，解决上传页面分类下拉为空
- [x] Docker Compose 优化：`command` 改为数组格式、添加 `healthcheck`/`service_healthy`、`stop_grace_period`、`PYTHONPATH`
- [x] 端到端测试：注册 → 登录 → 上传文档 → 搜索 → 查看文档 流程验证通过

### 6.4 Phase 1：稳定性与运维加固（第二阶段启动前）

#### P1-1 认证系统完善
- [ ] 密码强度校验（数字+字母+特殊字符，或 zxcvbn 评分）
- [ ] 注册邮箱验证（SMTP 配置，发送激活邮件）
- [ ] 用户密码重置（Forgot Password / Reset Token）
- [ ] 用户资料更新接口（修改邮箱、密码）
- [ ] 统一错误响应格式（当前 `Internal Server Error` 需确保日志已打印 traceback）

#### P1-2 测试覆盖
- [ ] 补充 PostgreSQL 特有功能的集成测试（TSVECTOR、触发器、GIN 索引）—— 使用 Docker 内 pytest 或 `pytest-postgresql`
- [ ] 补充 auth 路由单元测试（注册、登录、refresh、token 过期）
- [ ] 补充文档上传/解析测试（Markdown/HTML/DOCX 解析）
- [ ] 补充搜索测试（高亮、排序、分页、热搜缓存）

#### P1-3 监控与日志
- [ ] 确认 `/metrics` 正常抓取（Prometheus 指标已存在）
- [ ] 日志告警：错误率 > 5% 或 500 错误触发告警（可选接入 Webhook）
- [ ] 健康检查接口 `/health` 增加数据库/Redis 连通性检查（不仅是 200 OK）

#### P1-4 性能基线
- [ ] 运行 `scripts/load_test.py` 建立压测基线（当前配置：1核/3GB 目标）
- [ ] 检查数据库连接池竞争（当前 `pool_size=10, max_overflow=20`，若负载高可降级为 5/10）
- [ ] 评估 Redis 缓存命中率（搜索建议、热搜）

### 6.5 Phase 2：核心功能扩展（W7-W10）

> 创建 Alembic 迁移：`alembic/versions/2025xxxxx_005_phase2.py`（`004` 已被种子数据占用）
> 参考 `PRD.md` 详细需求

#### P2-1 文档版本历史
- [ ] 模型：`DocumentVersion`（document_id, version, content, diff, created_by, created_at）
- [ ] API：文档保存时自动创建版本快照；`GET /api/v1/documents/{id}/versions`
- [ ] API：版本对比 `POST /api/v1/documents/{id}/versions/compare?from=v1&to=v2`
- [ ] 前端：版本列表页、diff 高亮对比页（diff-match-patch 或 Git diff 风格）
- [ ] 版本回滚功能（管理员权限）

**技术决策**：完整内容存储（非增量），回滚简单，20 版 × 1万文档 = 20万行，PostgreSQL 可承载；diff 算法用 Python `difflib.SequenceMatcher`。

#### P2-2 附件管理
- [ ] 模型：`Attachment`（document_id, file_name, storage_type, storage_path, size, mime_type）
- [ ] 存储抽象层：支持本地磁盘 `/tmp/attachments` 与 S3/MinIO 双后端
- [ ] API：上传附件 `POST /api/v1/documents/{id}/attachments`
- [ ] API：下载附件 `GET /api/v1/attachments/{id}`（带权限校验）
- [ ] 文档解析支持附件引用（Markdown 图片/链接替换）
- [ ] Celery 任务：附件病毒扫描（可选 ClamAV）或 MIME 类型校验

#### P2-3 用户收藏与知识库
- [ ] 模型：`UserFavorite`（user_id, document_id, folder_id, created_at）
- [ ] 模型：`UserCollection`（用户自建知识库/文件夹，支持嵌套或扁平标签）
- [ ] API：收藏/取消收藏、移动收藏、收藏夹 CRUD
- [ ] 前端：个人中心 → 我的收藏、我的知识库
- [ ] 搜索增强：可限定搜索范围为“我的收藏”或“我的知识库”

#### P2-4 统计看板（贡献与使用分析）
- [ ] 后端聚合 API：文档贡献排行（按用户/按分类）、搜索热词趋势（日/周/月）、文档浏览量 TOP N、用户活跃度（DAU/MAU）
- [ ] 前端：ECharts 看板页面（管理员/个人双视图）
- [ ] 定时 Celery 任务：每日生成统计快照（避免实时大表扫描）

#### P2-5 相关推荐
- [ ] API：`GET /api/v1/documents/{id}/related?limit=5`
- [ ] 推荐算法：基于文档分类 + 标签重叠度（Jaccard 系数）+ 标题 TSVECTOR 相似度加权排序
  - 同分类文档优先，再按标签重叠数降序
  - 标签重叠相同时，使用 PostgreSQL `ts_rank` 比较标题与当前文档标题的文本相似度
  - 排除当前文档本身，排除 `parse_status != 'completed'` 和 `status != 'published'` 的文档
  - 结果不足 5 条时，放宽至同父分类（path 前缀匹配）补充
- [ ] Redis 缓存推荐结果（TTL 1 小时），文档内容更新或分类变更时清除缓存
- [ ] 前端：DocumentDetailView.vue 底部添加"相关推荐"区块，展示标题 + 浏览量 + 标签，点击跳转

**技术决策**：复用现有 PostgreSQL `search_vector` 和 JSONB `tags` 字段，不引入 Elasticsearch 或向量数据库。单次查询范围限定为同分类，数据量可控。未来文档量 > 5 万时，可评估接入 `pg_trgm`（相似度索引）或 `pgvector`（语义向量）。

### 6.6 Phase 3：企业级与高级搜索（W11-W14）

#### P3-1 SSO 与认证扩展
- [ ] 利用现有 `auth_type` 字段，实现 OAuth2（GitHub/Google/企业微信）登录
- [ ] LDAP/AD 集成（企业内部账号体系）
- [ ] 角色权限系统（RBAC）：`Role`、`Permission` 模型，管理员/编辑/访客
- [ ] 文档权限：私有/团队/公开，分类权限继承

#### P3-2 搜索增强
- [ ] Elasticsearch 评估与可选接入（当文档 > 5 万时切换）
- [ ] 搜索建议优化：基于用户历史的个性化建议
- [ ] 语义搜索：接入向量数据库（pgvector / Milvus）实现语义相似度检索
- [ ] 搜索结果排序策略：相关度 + 热度 + 时效性加权

**搜索升级决策树**：

```
当前数据量 > 50万 或 搜索相关性投诉 > 5次/周 或 复杂聚合需求出现？
    |-- 是 --> 启动 Elasticsearch 迁移评估（2周专项）
    |-- 否 --> PostgreSQL 深度优化（权重调优、短语搜索、Keyset 分页）
```

#### P3-3 高级监控与运维
- [ ] Grafana 看板（基于 Prometheus 数据）
- [ ] 告警 Webhook：磁盘/内存/CPU、错误率、搜索响应时间 > 2s
- [ ] 日志聚合：ELK / Loki 或结构化日志直接接入云厂商日志服务
- [ ] 备份策略：PostgreSQL 定时备份、Redis AOF + RDB、附件对象存储多版本

### 6.7 里程碑与验收标准

| 里程碑 | 预期时间 | 验收标准 |
|--------|---------|---------|
| **Phase 0 完成** | 已达成 | 注册/登录 100% 通过，所有容器健康运行，端到端测试通过 |
| **Phase 1 完成** | +1 周 | 测试覆盖率 > 60%，压力测试无崩溃，错误日志可追踪 |
| **Phase 2 启动** | +1 周 | Alembic 005 迁移成功，前端可访问新版本历史页 |
| **Phase 2 完成** | +4-6 周 | 版本历史、附件管理、收藏夹、统计看板、相关推荐全部可用，有文档 |
| **Phase 3 启动** | 视需求 | 文档量 > 3 万或企业部署需求时启动 SSO/ES |

### 6.8 风险与决策点

| 风险 | 应对 |
|------|------|
| **中文搜索质量**：`simple` 分词仅按空格/标点切分，中文不切词。若质量不达标，评估 Python `jieba` 预处理、`pg_bigm` N-gram 或 Elasticsearch + IK 分词（>5万文档时） | 当前文档量 < 1万，simple 分词可接受；质量下降时按决策树执行 |
| **存储成本**：附件管理若采用本地磁盘，单节点扩容受限 | 早期抽象 `StorageBackend` 接口，预留 S3/MinIO 切换能力 |
| **1核/3GB 性能天花板**：Phase 2 上线后必须完成压测 | 若瓶颈明显，考虑读写分离或缓存预热；优先升级至 2核/4G |
| **Elasticsearch 必要性**：当前 PG TSVECTOR + GIN 在 5 万以下表现良好 | 明确触发条件（>50万文档或相关性投诉 >5次/周），避免过早引入运维复杂度 |

### 6.9 资源需求

| 阶段 | 后端 | 前端 | 测试/运维 | 服务器建议 |
|------|------|------|-----------|------------|
| MVP（W1-W6） | 2人 | 1人 | 兼职 | 1核3G |
| Phase 1-2（W7-W10） | 2人 | 1人 | 兼职 | 2核4G（附件量大/并发增加） |
| Phase 3（W11-W14） | 2人 | 1人 | 0.5人 | 2核4G（监控 + ES 评估需额外资源） |

---

*本文档随项目进展持续更新。上次更新：2026-07-01*
