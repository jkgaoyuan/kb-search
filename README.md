# KB Search - 知识库检索工具

## 快速启动

```bash
# 1. 复制环境变量
cp .env.example .env

# 2. 启动服务
docker-compose up -d

# 3. 初始化数据库
docker-compose exec web alembic upgrade head

# 4. 访问 API 文档
http://localhost:8000/docs
```

## 项目结构

```
app/
  models/      # SQLModel 数据模型
  routers/     # FastAPI 路由
  services/    # 业务逻辑
  tasks/       # Celery 异步任务
  utils/       # 工具函数
```

## 技术栈

- FastAPI + SQLModel + PostgreSQL
- Celery + Redis 异步任务
- PostgreSQL `simple` 分词全文检索（标题/内容/标签）
- Docker Compose 部署
