# 知识库检索系统 - 使用说明

> 版本：v1.0 MVP  
> 日期：2026-06-26

---

## 一、环境要求

| 组件 | 版本 | 说明 |
|------|------|------|
| Docker | 20.10+ | 容器运行时 |
| Docker Compose | 2.0+ | 编排工具 |
| Node.js | 18.x+ | 前端开发（仅开发环境） |
| npm | 9.x+ | 包管理器 |

---

## 二、快速启动（后端）

### 2.1 首次启动

```bash
# 1. 解压项目
cd /path/to/kb-search

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，确认以下配置：
# DATABASE_URL=postgresql://kb:kb@db:5432/kb
# REDIS_URL=redis://redis:6379/0
# CELERY_BROKER_URL=redis://redis:6379/1
# SECRET_KEY=your-secret-key-here

# 3. 启动所有服务（后台运行）
docker-compose up -d

# 4. 等待数据库就绪（约10秒）
sleep 10

# 5. 初始化数据库迁移
docker-compose exec web alembic init alembic

# 6. 创建初始迁移脚本
docker-compose exec web alembic revision --autogenerate -m "init"

# 7. 执行迁移
docker-compose exec web alembic upgrade head

# 8. 验证服务状态
curl http://localhost:8000/health
# 预期返回：{"status":"ok","version":"0.1.0"}
```

### 2.2 日常操作

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f web      # 后端API日志
docker-compose logs -f worker   # 异步任务日志
docker-compose logs -f db       # 数据库日志

# 重启服务
docker-compose restart web

# 停止所有服务
docker-compose down

# 停止并删除数据卷（谨慎使用！）
docker-compose down -v
```

### 2.3 数据库管理

```bash
# 进入数据库容器
docker-compose exec db psql -U kb -d kb

# 常用SQL
\dt                          # 查看所有表
SELECT * FROM users;          # 查看用户
SELECT * FROM documents;      # 查看文档
SELECT * FROM search_logs;    # 查看搜索日志

# 手动更新全文检索向量（使用 PostgreSQL 内置 simple 分词配置）
UPDATE documents SET search_vector = to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(content, ''));

# 退出
\q
```

---

## 三、前端开发

### 3.1 启动前端开发服务器

```bash
cd frontend

# 安装依赖（首次）
npm install

# 启动开发服务器（自动代理API到 localhost:8000）
npm run serve

# 访问地址
open http://localhost:8080
```

### 3.2 构建生产包

```bash
cd frontend

# 构建（输出到 frontend/dist/）
npm run build

# 构建后的静态文件可通过 Nginx 或 FastAPI 托管
```

### 3.3 前端开发代理说明

`vue.config.js` 中已配置代理：

```javascript
devServer: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

这意味着前端开发时，所有 `/api/*` 请求自动转发到后端服务。

---

## 四、API 使用示例

### 4.1 注册/登录

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

### 4.2 上传文档

```bash
# 上传 Markdown 文件
curl -X POST "http://localhost:8000/api/v1/documents" \
  -H "Authorization: Bearer $TOKEN" \
  -F "title=Python最佳实践" \
  -F "category_id=1" \
  -F "tags=Python,后端,教程" \
  -F "file=@/path/to/your/file.md"

# 返回：{"id":1,"title":"Python最佳实践","parse_status":"pending","message":"文档已上传，正在解析中"}
```

### 4.3 搜索

```bash
# 全文搜索
curl "http://localhost:8000/api/v1/search?q=Python&sort=relevance&page=1"

# 自动补全建议
curl "http://localhost:8000/api/v1/search/suggest?q=Py"

# 热门搜索
curl "http://localhost:8000/api/v1/search/hot?limit=10"
```

### 4.4 分类管理

```bash
# 创建分类
curl -X POST "http://localhost:8000/api/v1/categories" \
  -H "Authorization: Bearer $TOKEN" \
  -d "name=技术"

# 创建子分类
curl -X POST "http://localhost:8000/api/v1/categories" \
  -H "Authorization: Bearer $TOKEN" \
  -d "name=后端&parent_id=1"

# 查看分类树
curl "http://localhost:8000/api/v1/categories?tree=true"

# 面包屑导航
curl "http://localhost:8000/api/v1/categories/2/breadcrumb"
```

---

## 五、页面功能说明

### 5.1 登录页 (/login)

- 支持登录/注册切换
- JWT Token 自动保存到 localStorage
- 登录后自动跳转到搜索页

### 5.2 搜索页 (/)

- **搜索框**：输入关键词，支持回车搜索
- **自动补全**：输入2字符以上显示历史搜索建议
- **热门搜索**：首页展示最近24小时热搜Top10
- **结果列表**：
  - 标题高亮匹配关键词
  - 内容摘要（含关键词高亮）
  - 相关度分数、浏览量、更新时间
  - 支持按相关度/更新时间/浏览量排序
- **分页**：超过20条自动分页

### 5.3 文档详情页 (/document/:id)

- 展示文档标题、标签、元信息
- HTML 内容渲染（Markdown/HTML/DOCX统一渲染）
- 代码块高亮、表格样式
- 浏览量自动+1

### 5.4 上传页 (/upload)

- 表单：标题 + 分类选择（级联选择器）+ 标签 + 文件
- 文件限制：.md, .html, .htm, .docx，最大20MB
- 上传后显示解析进度条（轮询状态）
- 解析完成后可搜索

### 5.5 分类浏览页 (/categories)

- 左侧树形分类菜单（技术/产品/运营三级）
- 点击分类显示面包屑导航
- 右侧展示该分类下的文档列表

---

## 六、常见问题

### Q1: 启动后访问 http://localhost:8000 返回 404？

后端 API 没有根页面，请访问：
- API 文档：`http://localhost:8000/docs`（Swagger UI）
- 健康检查：`http://localhost:8000/health`

前端页面在 `http://localhost:8080`

### Q2: 上传文件后一直显示"解析中"？

检查 Worker 是否正常运行：
```bash
docker-compose logs -f worker
```

如果 Worker 未启动，检查 Redis 连接：
```bash
docker-compose exec redis redis-cli ping
# 应返回 PONG
```

### Q3: 搜索中文无结果？

当前使用 PostgreSQL 内置 `simple` 分词配置。该模式按空格/标点切分，对中文文本**不切词**（如搜索"技术"无法匹配"技术部署"）。如需提升中文搜索质量，可：
- 使用 Python `jieba` 分词预处理文本后写入 `search_vector`
- 或评估迁移至 `pg_bigm`（N-gram 模糊匹配）
- 或文档量 > 5 万时评估 Elasticsearch + IK 分词

验证搜索向量是否正常：
```bash
docker-compose exec db psql -U kb -d kb -c "SELECT id, title, search_vector FROM documents LIMIT 1;"
```

### Q4: 前端 npm install 报错？

确保 Node.js 版本 >= 18：
```bash
node -v
# v18.x.x 或更高
```

如果版本过低，使用 nvm 切换：
```bash
nvm use 18
# 或
nvm install 18
```

### Q5: 如何修改上传文件大小限制？

编辑 `.env` 文件：
```bash
MAX_UPLOAD_SIZE=52428800  # 50MB
```

同时修改 `frontend/src/views/UploadView.vue` 中的前端限制。

---

## 七、性能调优建议

### 7.1 数据库优化

```sql
-- 为常用查询添加索引（如已存在可忽略）
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_category ON documents(category_id);
CREATE INDEX idx_documents_author ON documents(author_id);
CREATE INDEX idx_search_logs_query ON search_logs(query);
CREATE INDEX idx_search_logs_created ON search_logs(created_at);

-- 分析表（更新统计信息）
ANALYZE documents;
ANALYZE search_logs;
```

### 7.2 缓存优化

热门搜索和搜索建议已使用 Redis 缓存，无需额外配置。

如需调整缓存时间，修改 `app/services/search_service.py` 中的 TTL 值。

### 7.3 Worker 并发调整

编辑 `docker-compose.yml`：
```yaml
worker:
  command: celery -A app.tasks.document_tasks worker --loglevel=info --concurrency=4
```

根据服务器 CPU 核心数调整 concurrency（建议不超过 CPU 核心数）。

---

## 八、备份与恢复

### 8.1 数据库备份

```bash
# 备份
docker-compose exec db pg_dump -U kb -d kb > kb_backup_$(date +%Y%m%d).sql

# 恢复
cat kb_backup_20260101.sql | docker-compose exec -T db psql -U kb -d kb
```

### 8.2 Redis 备份

Redis 已配置 RDB 持久化，数据自动保存到 `redis_data` 卷。

手动备份：
```bash
docker-compose exec redis redis-cli BGSAVE
```

---

## 九、联系与支持

如有问题，请检查：
1. `docker-compose logs` 查看详细错误
2. `http://localhost:8000/docs` 查看 API 文档
3. 确认所有服务状态 `docker-compose ps`

---

*本文档随项目进展持续更新*
