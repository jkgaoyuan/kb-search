# KB Search 开发计划

> 状态：2026-06-27 更新 | 当前阶段：MVP 维护，第二阶段待启动

---

## Phase 0: 当前阻塞项（必须完成）

### P0-1 认证注册修复验证
- [ ] 重建 web 镜像（`requirements.txt` 已新增 `bcrypt==3.2.2`，必须 `--no-cache` 构建）
- [ ] 验证注册接口：`POST /api/v1/auth/register` 正常返回用户 ID
- [ ] 验证登录接口：`POST /api/v1/auth/login` 正常返回 access_token
- [ ] 验证密码边界：超长密码（>72 字节）被截断/拒绝，过短密码（<6 字符）被 400 拒绝
- [ ] 运行本地测试：`pytest tests/ -v`（SQLite 测试集，验证 auth 路由）

### P0-2 基础设施整备
- [ ] 移除 `docker-compose.yml` 废弃的 `version: '3.8'` 行（消除启动警告）
- [ ] 确认 Alembic 迁移已执行（`docker-compose exec web alembic upgrade head`）
- [ ] 运行数据库迁移（`docker-compose exec web alembic upgrade head`）
- [ ] 运行一次完整端到端测试：注册 → 登录 → 上传文档 → 搜索 → 查看文档

---

## Phase 1: 稳定性与运维加固（第二阶段启动前）

### P1-1 认证系统完善
- [ ] 密码强度校验（数字+字母+特殊字符，或 zxcvbn 评分）
- [ ] 注册邮箱验证（SMTP 配置，发送激活邮件）
- [ ] 用户密码重置（Forgot Password / Reset Token）
- [ ] 用户资料更新接口（修改邮箱、密码）
- [ ] 统一错误响应格式（当前 `Internal Server Error` 未暴露具体错误到日志，需确认日志已打印 traceback）

### P1-2 测试覆盖
- [ ] 补充 PostgreSQL 特有功能的集成测试（TSVECTOR、触发器、GIN 索引）—— 使用 Docker 内 pytest 或 `pytest-postgresql`
- [ ] 补充 auth 路由单元测试（注册、登录、refresh、token 过期）
- [ ] 补充文档上传/解析测试（Markdown/HTML/DOCX 解析）
- [ ] 补充搜索测试（高亮、排序、分页、热搜缓存）

### P1-3 监控与日志
- [ ] 当前 Prometheus 指标已存在，确认 `/metrics` 正常抓取
- [ ] 日志告警：错误率 > 5% 或 500 错误触发告警（可选接入 Webhook）
- [ ] 健康检查接口 `/health` 增加数据库/Redis 连通性检查（不仅是 200 OK）

### P1-4 性能基线
- [ ] 运行 `scripts/load_test.py` 建立压测基线（当前配置：1核/3GB 目标）
- [ ] 检查数据库连接池竞争（当前 `pool_size=10, max_overflow=20`，若负载高可降级为 5/10）
- [ ] 评估 Redis 缓存命中率（搜索建议、热搜）

---

## Phase 2: 核心功能扩展（文档与知识管理）

> 创建 Alembic 迁移：`alembic/versions/20250627_004_phase2.py`
> 参考 `PRD.md` 详细需求

### P2-1 文档版本历史
- [ ] 模型：`DocumentVersion`（document_id, version, content, diff, created_by, created_at）
- [ ] API：文档保存时自动创建版本快照；`GET /api/v1/documents/{id}/versions`
- [ ] API：版本对比 `POST /api/v1/documents/{id}/versions/compare?from=v1&to=v2`
- [ ] 前端：版本列表页、diff 高亮对比页（diff-match-patch 或 Git diff 风格）
- [ ] 版本回滚功能（管理员权限）

### P2-2 附件管理
- [ ] 模型：`Attachment`（document_id, file_name, storage_type, storage_path, size, mime_type）
- [ ] 存储抽象层：支持本地磁盘 `/tmp/attachments` 与 S3/MinIO 双后端
- [ ] API：上传附件 `POST /api/v1/documents/{id}/attachments`
- [ ] API：下载附件 `GET /api/v1/attachments/{id}`（带权限校验）
- [ ] 文档解析支持附件引用（Markdown 图片/链接替换）
- [ ] Celery 任务：附件病毒扫描（可选 ClamAV）或 MIME 类型校验

### P2-3 用户收藏与知识库
- [ ] 模型：`UserFavorite`（user_id, document_id, folder_id, created_at）
- [ ] 模型：`UserCollection`（用户自建知识库/文件夹，支持嵌套或扁平标签）
- [ ] API：收藏/取消收藏、移动收藏、收藏夹 CRUD
- [ ] 前端：个人中心 → 我的收藏、我的知识库
- [ ] 搜索增强：可限定搜索范围为“我的收藏”或“我的知识库”

### P2-4 统计看板（贡献与使用分析）
- [ ] 后端聚合 API：
  - 文档贡献排行（按用户/按分类）
  - 搜索热词趋势（日/周/月）
  - 文档浏览量 TOP N
  - 用户活跃度（DAU/MAU）
- [ ] 前端：ECharts 看板页面（管理员/个人双视图）
- [ ] 定时 Celery 任务：每日生成统计快照（避免实时大表扫描）

---

## Phase 3: 企业级与高级搜索

### P3-1 SSO 与认证扩展
- [ ] 利用现有 `auth_type` 字段，实现 OAuth2（GitHub/Google/企业微信）登录
- [ ] LDAP/AD 集成（企业内部账号体系）
- [ ] 角色权限系统（RBAC）：`Role`、`Permission` 模型，管理员/编辑/访客
- [ ] 文档权限：私有/团队/公开，分类权限继承

### P3-2 搜索增强
- [ ] Elasticsearch 评估与可选接入（当文档 > 5 万时切换）
- [ ] 搜索建议优化：基于用户历史的个性化建议
- [ ] 语义搜索：接入向量数据库（pgvector / Milvus）实现语义相似度检索
- [ ] 搜索结果排序策略：相关度 + 热度 + 时效性加权

### P3-3 高级监控与运维
- [ ] Grafana 看板（基于 Prometheus 数据）
- [ ] 告警 Webhook：磁盘/内存/CPU、错误率、搜索响应时间 > 2s
- [ ] 日志聚合：ELK / Loki 或结构化日志直接接入云厂商日志服务
- [ ] 备份策略：PostgreSQL 定时备份、Redis AOF + RDB、附件对象存储多版本

---

## 里程碑与验收标准

| 里程碑 | 预期时间 | 验收标准 |
|--------|---------|---------|
| **Phase 0 完成** | 立即 | 注册/登录 100% 通过，所有容器健康运行，端到端测试通过 |
| **Phase 1 完成** | +1 周 | 测试覆盖率 > 60%，压力测试无崩溃，错误日志可追踪 |
| **Phase 2 启动** | +1 周 | Alembic 004 迁移成功，前端可访问新版本历史页 |
| **Phase 2 完成** | +4-6 周 | 版本历史、附件管理、收藏夹、统计看板全部可用，有文档 |
| **Phase 3 启动** | 视需求 | 文档量 > 3 万或企业部署需求时启动 SSO/ES |

---

## 风险与决策点

1. **中文搜索质量**：当前使用 `simple` 分词配置，仅按空格/标点切分，中文不切词。若文档量增长或质量不达标，可评估：
   - Python `jieba` 分词预处理
   - `pg_bigm`（N-gram 模糊匹配）
   - Elasticsearch + IK 分词（文档 > 5 万时）
2. **存储成本**：附件管理若采用本地磁盘，单节点扩容受限；建议早期抽象 S3/MinIO 接口
3. **1核/3GB 性能天花板**：Phase 2 上线后必须完成压测，若瓶颈明显，需考虑读写分离或缓存预热
4. **Elasticsearch 必要性**：当前 PostgreSQL TSVECTOR + GIN 在 5 万以下文档表现良好，ES 引入增加运维复杂度，需有明确触发条件

---

## 下一步行动（建议立即执行）

```bash
# 1. 启动容器（验证当前修复）
docker-compose up -d
docker-compose build --no-cache web  # 若 bcrypt 修复未生效

# 2. 验证注册
curl -X POST http://localhost:8000/api/v1/auth/register \
  -d "username=testuser" -d "password=testpass123"

# 3. 验证登录
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=testuser" -d "password=testpass123"

# 4. 全量测试
pytest tests/ -v

# 5. 清理废弃 version 字段（可选）
# 编辑 docker-compose.yml 删除第 1 行 `version: '3.8'`
```
