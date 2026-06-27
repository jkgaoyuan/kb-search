# CLAUDE.md

本文档为 Claude Code (claude.ai/code) 提供本仓库代码的工作指引。

> **当前阶段：** MVP 已完成。第二阶段（版本历史、附件管理、收藏夹、统计看板）尚未开始。

## 项目概览

KB Search 是一款知识库检索系统。后端：FastAPI + SQLModel + PostgreSQL 15 + Redis 7 + Celery。前端：Vue 3 + Element Plus + Pinia。通过 Docker Compose 部署（目标环境：1核 / 3GB）。

## 常用命令

### 后端（Docker）

```bash
# 从仓库根目录启动全栈
docker-compose up -d --build

# 数据库迁移（首次启动或 schema 变更后执行）
docker-compose exec web alembic upgrade head

# 安装 zhparser 扩展（一次性操作，中文全文检索必需）
docker-compose exec db sh -c "echo 'CREATE EXTENSION IF NOT EXISTS zhparser;' | psql -U kb -d kb"

# 查看日志
docker-compose logs -f web
docker-compose logs -f worker
docker-compose logs -f beat

# 在容器内运行测试
docker-compose exec web pytest tests/ -v

# 手动触发搜索日志清理（默认保留 30 天）
docker-compose exec worker celery -A app.tasks.document_tasks call app.tasks.document_tasks.clean_old_search_logs
```

### 后端（本地开发，无需 Docker）

需要本地安装 PostgreSQL 和 Redis。

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 API 服务（开发模式）
uvicorn app.main:app --reload --port 8000

# 启动 Celery Worker（另一个终端）
celery -A app.tasks.document_tasks worker --loglevel=info --concurrency=2

# 启动 Celery Beat 调度器（另一个终端，执行定时任务）
celery -A app.tasks.document_tasks beat --loglevel=info

# 本地运行测试
pytest tests/ -v

# 运行单个测试文件
pytest tests/test_api.py -v
```

### 前端

```bash
cd frontend
npm install
npm run serve        # 开发服务器，代理到 localhost:8000
npm run build        # 生产构建，输出到 frontend/dist/
npm run lint         # ESLint 检查
```

### 压测

```bash
python scripts/load_test.py -u 20 -n 200 --url http://localhost:8000
```

## 高层架构

### 后端分层

- `app/models/` — SQLModel 表定义。核心模型：`Document`（含 `TSVECTOR` 字段）、`Category`（物化路径 `path`）、`SearchLog`、`User`。
- `app/routers/` — FastAPI 路由处理器。业务逻辑保持轻量，委托给服务层。
- `app/services/` — 核心业务逻辑。`SearchService` 处理全文排序/高亮/摘要；`DocumentParser` 处理 MD/HTML/DOCX；`StatsService` 已预置但仅通过 `stats.py` 路由接入。
- `app/tasks/` — Celery 任务。`parse_document_task` 异步解析上传文件并触发 `update_search_vector`。另包含通过 Celery Beat 执行的定时清理任务。
- `app/utils/` — JWT/安全、文本处理、Redis 客户端、结构化日志配置。

### 数据流：文档上传

1. `POST /api/v1/documents` 将原始文件保存到 `/tmp/uploads`，创建 `Document` 记录（`parse_status = pending`），并投递 `parse_document_task`。
2. Celery Worker 解析文件（Markdown→`mistune`，HTML→`BeautifulSoup+bleach`，DOCX→`python-docx`），写入 `content`（纯文本）和 `content_html`。
3. `update_search_vector` 任务（或数据库触发器）为全文检索填充 `TSVECTOR` 列。
4. 客户端轮询 `GET /api/v1/documents/{id}/status` 获取进度。

### 数据流：搜索

1. `GET /api/v1/search?q=...` 使用 `plainto_tsquery('zh_cn', ...)` 对 `Document.search_vector` 进行全文检索，并以 `ts_rank` 计算相关度。
2. `SearchService` 将查询记录到 `SearchLog`，计算高亮片段，返回分页结果。
3. 热搜和搜索建议使用 Redis 缓存（`search:hot:*`、`search:suggest:*`）并设置 TTL，Redis 不可用时回退到 PostgreSQL 查询。
4. `GET /api/v1/search/correct` 基于文档标题和历史查询词提供拼写纠错。

### 分类树

分类使用物化路径字符串存储（如 `"1.2.3"`）。`GET /api/v1/categories?tree=true` 返回扁平列表，前端负责构建树形菜单。面包屑通过将 `path` 按 `"."` 分割并逐级查询节点生成。

**注意：** 当分类的 `parent_id` 变更时，必须级联更新所有子孙节点的 `path`。该逻辑目前在应用层处理，非数据库级联。

## 数据库架构与性能

### 迁移文件

Alembic 迁移位于 `alembic/versions/`：

| 迁移文件 | 用途 |
|---------|------|
| `20250626_001_init.py` | 创建表：`users`、`categories`、`documents`、`search_logs`。包含带 `ON DELETE` 的外键、`CHECK` 约束和索引。 |
| `20250626_002_add_tsvector_trigger.py` | PostgreSQL 函数 + 触发器，在 INSERT/UPDATE 时自动更新 `documents.search_vector`。 |
| `20250626_003_fix_indexes_and_constraints.py` | **性能迁移。** 为 `tags` 添加 GIN 索引、为列表查询添加复合索引、`view_count` 索引、路径前缀索引、`updated_at` 自动更新触发器。 |

### 索引策略

**documents 表：**
- `ix_documents_title` — B-tree（标题查询）
- `ix_documents_category_id` — B-tree（分类过滤）
- `ix_documents_author_id` — B-tree（作者过滤）
- `idx_documents_status` — B-tree（状态过滤）
- `idx_documents_created_at` — B-tree（时间排序）
- `idx_documents_updated_at` — B-tree（最近文档排序）
- `idx_documents_view_count` — B-tree（热度排序）
- `idx_documents_status_updated_at` — 复合索引 `(status, updated_at DESC)`（列表查询）
- `idx_documents_category_status_updated` — 复合索引 `(category_id, status, updated_at DESC)`（分类列表）
- `idx_documents_category_status_views` — 复合索引 `(category_id, status, view_count DESC)`（分类热度）
- `idx_documents_search_vector` — GIN（`TSVECTOR` 全文检索）
- `idx_documents_tags_gin` — GIN（JSONB `@>` 包含查询，用于标签筛选）

**categories 表：**
- `ix_categories_name` — B-tree
- `ix_categories_parent_id` — B-tree
- `ix_categories_path` — B-tree
- `idx_categories_path_pattern` — B-tree + `text_pattern_ops`（前缀搜索，用于子树查询）

**search_logs 表：**
- `ix_search_logs_query` — B-tree（建议前缀匹配）
- `ix_search_logs_user_id` — B-tree
- `ix_search_logs_created_at` — B-tree
- `idx_search_logs_created_at_query` — 复合索引 `(created_at, query)`（热搜聚合）
- `idx_search_logs_ip_address` — B-tree（分析/异常检测）

### 约束

- `CHECK` 约束在数据库层强制枚举值：
  - `users.auth_type` ∈ `('local', 'ldap', 'oauth2')`
  - `documents.status` ∈ `('draft', 'published', 'archived')`
  - `documents.parse_status` ∈ `('pending', 'processing', 'completed', 'failed')`
  - `documents.file_type` ∈ `('markdown', 'html', 'docx')`
- 外键使用 `ON DELETE RESTRICT`（documents → categories/users），防止误删被引用的行。
- `search_logs.user_id` 使用 `ON DELETE SET NULL`，用户删除时保留分析历史。

### 自动更新触发器

PostgreSQL 触发器 `trg_users_updated_at` 和 `trg_documents_updated_at` 在每次 `UPDATE` 时自动刷新 `updated_at`，因此**应用层无需手动设置该字段**。

### 连接池

`app/database.py` 配置为 `pool_size=10, max_overflow=20, pool_pre_ping=True`。若 1核 目标在负载下出现连接竞争，可降级为 `pool_size=5, max_overflow=10`。

## 定时任务（Celery Beat）

`beat` 服务运行 Celery 周期性任务调度器。配置的任务（`app/tasks/document_tasks.py`）：

| 任务 | 周期 | 用途 |
|------|------|------|
| `clean_old_search_logs` | 每 1 小时 | 删除超过 30 天的 `search_logs` 记录，防止表膨胀。 |
| `clean_old_uploads` | 每 24 小时 | 清理 `/tmp/uploads` 中不再被 `documents.file_path` 引用的孤儿文件。 |

## 测试策略

`tests/` 下的测试使用 `pytest` + `TestClient`，搭配**内存 SQLite** 数据库和 `StaticPool`。通过 `app.dependency_overrides[get_session]` 注入 SQLite 会话。测试无需 Docker 即可快速运行，但**无法测试 PostgreSQL 特有功能**（`TSVECTOR`、`zhparser`、触发器、GIN 索引）。PostgreSQL 相关行为请使用 `docker-compose exec web pytest ...` 验证。

## 部署说明

- **Gunicorn** 配置在 `gunicorn.conf.py`，使用 `uvicorn.workers.UvicornWorker`。
- **Docker Compose** 定义了 5 个服务：`web`（FastAPI）、`worker`（Celery）、`beat`（Celery 调度器）、`db`（PostgreSQL 15）、`redis`（Redis 7）。内存限制：512MB / 512MB / 128MB / 1GB / 256MB。
- **Alembic** 迁移位于 `alembic/versions/`。拉取新代码后执行 `docker-compose exec web alembic upgrade head`。
- **环境变量** 通过 `app.config.Settings`（Pydantic Settings）加载，读取 `.env` 文件。关键变量：`DATABASE_URL`、`REDIS_URL`、`CELERY_BROKER_URL`、`SECRET_KEY`、`MAX_UPLOAD_SIZE`、`AUTH_TYPE`。
- **Prometheus 指标** 在 `/metrics` 暴露，供 `web` 服务抓取。

## 性能模式

### 计数查询（分页）

始终使用 `func.count()` 标量执行，禁止 `len(session.exec(...).all())`：

```python
total = session.exec(
    select(func.count(Document.id)).where(Document.status == "published")
).one()
```

### 原子计数器更新

使用 SQL `UPDATE ... SET col = col + 1` 替代读取-修改-写入，避免并发丢失更新：

```python
from sqlalchemy import update
session.exec(
    update(Document)
    .where(Document.id == doc_id)
    .values(view_count=Document.view_count + 1)
)
session.commit()
```

### Redis 缓存回退

热搜和建议写入 Redis 并设置 TTL。Redis 不可用时自动回退到 PostgreSQL 查询。该模式在 `SearchService`（`app/services/search_service.py`）中实现。

## 前端说明

- `frontend/vue.config.js` 在开发模式下将 `/api` 代理到 `http://localhost:8000`。
- 使用 `axios` 进行 HTTP 请求，`highlight.js` 高亮文档详情中的代码块。
- 项目中包含 `marked` 但后端解析 Markdown 实际使用 `mistune`。

## 关键文件速查

- `app/main.py` — FastAPI 工厂。注册所有路由、Prometheus 指标中间件、结构化日志中间件。
- `app/database.py` — `create_engine` 连接池配置和 `init_db()`（调用 `SQLModel.metadata.create_all`）。
- `app/config.py` — Pydantic Settings，读取 `.env`。
- `app/tasks/document_tasks.py` — Celery 应用配置、任务定义、Beat 定时调度。
- `docker-compose.yml` — 生产编排定义（5 个服务）。
- `app/services/search_service.py` — 全文检索、高亮、建议、热搜、拼写纠错。
- `app/routers/documents.py` — 文档上传（异步）、状态轮询、原子浏览量计数。
- `alembic/versions/` — 数据库迁移。**003** 为性能优化迁移。

## 第二阶段待办（尚未开始）

以下功能已规划，但仓库中**无任何代码**：

- 文档版本历史（`DocumentVersion` 模型、diff 对比页面）
- 附件管理（`Attachment` 模型、S3/MinIO 存储抽象层）
- 用户收藏/知识库（`UserFavorite`、`UserCollection` 模型）
- 贡献统计看板（前端 ECharts、聚合统计 API）
- Elasticsearch 评估（对比 `tsvector` 与 ES，适用于 >5万 文档场景）
- SSO 集成（通过 `auth_type` 字段对接 OAuth2/LDAP）
- 高级监控（Grafana 看板、告警 Webhook）

启动第二阶段时，创建 `alembic/versions/2025xxxxx_004_phase2.py` 存放新表，详细需求参考 `PRD.md`。
