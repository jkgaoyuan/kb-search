# KB Search - 知识库检索系统

支持 Markdown、HTML、DOCX 格式文档的上传、解析与全文检索。

## 快速启动

```bash
# 1. 复制环境变量
cp .env.example .env

# 2. 启动全栈（自动执行数据库迁移）
docker-compose up -d --build

# 3. 验证服务状态
curl http://localhost:8000/health

# 4. 前端访问 http://localhost:8080
# API 文档 http://localhost:8000/docs
```

## 技术栈

- **后端**：FastAPI + SQLModel + PostgreSQL 15 + Redis 7 + Celery
- **前端**：Vue 3 + Element Plus + Pinia
- **部署**：Docker Compose（目标 1核/3GB）

## 核心功能

- 用户注册/登录（JWT）
- 文档上传（MD / HTML / DOCX，最大 20MB）
- 异步解析（Celery Worker + 前端进度轮询）
- 全文搜索（PostgreSQL `tsvector` + 高亮 + 摘要）
- 分类树浏览 + 面包屑导航
- 热门搜索排行 + 自动补全建议

## 详细文档

技术架构、部署指南、API 示例、测试策略和开发路线图请参阅 [`PROJECT_DOCS.md`](PROJECT_DOCS.md)。

产品需求请参阅 [`PRD.md`](PRD.md)。
