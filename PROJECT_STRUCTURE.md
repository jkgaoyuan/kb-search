# 知识库检索系统 - 项目结构说明

> 版本：v1.0 MVP  
> 日期：2026-06-26  
> 技术栈：FastAPI + Vue3 + PostgreSQL + Redis + Celery

---

## 一、整体架构

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
        │      │  simple tokenizer│     │ 队列/缓存│
        │      └─────────┘     └─────────┘
        │
   ┌────▼────────────────────────────────────┐
   │ 前端开发服务器代理规则                      │
   │ /api/*  -> http://localhost:8000          │
   │ /*      -> 前端静态资源                    │
   └───────────────────────────────────────────┘
```

---

## 二、后端结构 (app/)

```
app/
├── __init__.py
├── main.py                 # FastAPI 入口，路由注册，生命周期管理
├── config.py              # Pydantic Settings 配置（环境变量+默认值）
├── database.py            # SQLModel engine + Session 依赖注入
│
├── models/                # 数据模型（SQLModel = SQLAlchemy + Pydantic）
│   ├── __init__.py
│   ├── user.py            # 用户表：username, auth_type(预留SSO), is_admin
│   ├── category.py        # 分类表：name, parent_id, path(物化路径)
│   ├── document.py        # 文档表：title, content, content_html, search_vector(tsvector)
│   └── search_log.py      # 搜索日志：query, user_id, result_count
│
├── routers/               # API 路由层（Controller）
│   ├── __init__.py
│   ├── auth.py            # POST /auth/register, /auth/login, /auth/refresh
│   ├── documents.py       # 文档CRUD + 上传 + 状态查询
│   ├── search.py          # GET /search, /search/suggest, /search/hot
│   └── categories.py      # 分类树 + 面包屑 + 创建
│
├── services/              # 业务逻辑层（Service）
│   ├── __init__.py
│   ├── document_parser.py # Markdown/HTML/DOCX 解析器
│   ├── search_service.py  # 全文搜索 + 搜索建议 + 热门排行
│   └── stats_service.py   # 作者排行 + 文档热度 + 分类统计（预留）
│
├── tasks/                 # Celery 异步任务
│   ├── __init__.py
│   └── document_tasks.py  # parse_document_task, update_search_vector, clean_old_uploads
│
└── utils/                 # 工具函数
    ├── __init__.py
    ├── security.py        # JWT 生成/验证 + bcrypt 密码哈希
    └── text_utils.py      # Markdown 去标记 + 摘要生成 + 关键词高亮
```

---

## 三、前端结构 (frontend/)

```
frontend/
├── public/
│   └── index.html         # HTML 入口
│
├── src/
│   ├── main.js            # Vue3 应用入口：Pinia + Router + ElementPlus
│   ├── App.vue            # 根组件（仅 router-view）
│   │
│   ├── router/
│   │   └── index.js       # 路由表：/login, /search, /document/:id, /upload, /categories
│   │
│   ├── store/
│   │   └── user.js        # Pinia Store：token, userInfo, login/logout
│   │
│   ├── utils/
│   │   ├── request.js     # Axios 封装：baseURL, JWT拦截, 错误处理
│   │   └── common.js      # 防抖(debounce) + 节流(throttle)
│   │
│   ├── api/               # API 接口层（按模块拆分）
│   │   ├── auth.js        # 登录/注册/刷新Token
│   │   ├── document.js    # 上传/列表/详情/状态/更新/删除
│   │   ├── search.js      # 搜索/建议/热门
│   │   └── category.js    # 分类树/面包屑/创建
│   │
│   └── views/             # 页面组件
│       ├── LoginView.vue      # 登录/注册页（标签切换）
│       ├── LayoutView.vue     # 主布局：Header + Sidebar + Main
│       ├── SearchView.vue     # 核心搜索页：搜索框 + 热搜 + 结果列表
│       ├── DocumentDetailView.vue  # 文档详情：HTML渲染 + 元信息
│       ├── UploadView.vue     # 上传页：表单 + 文件选择 + 解析进度轮询
│       └── CategoryView.vue   # 分类浏览：树形菜单 + 面包屑 + 文档列表
│
├── package.json           # 依赖：vue3, element-plus, pinia, axios, highlight.js
└── vue.config.js          # 开发代理：/api -> localhost:8000
```

---

## 四、部署配置

```
├── docker-compose.yml     # 四容器编排：web(512M) + worker(512M) + db(1G) + redis(256M)
├── Dockerfile             # Python 3.11 + 系统依赖 + pip安装
├── requirements.txt       # 18个 Python 依赖包
├── pyproject.toml         # 项目元数据 + 依赖声明
├── alembic.ini            # 数据库迁移配置
├── alembic/               # 迁移脚本目录
│   ├── env.py             # 迁移环境（SQLModel metadata）
│   ├── script.py.mako     # 迁移模板
│   └── versions/          # 自动生成的迁移版本
└── .env.example           # 环境变量模板
```

---

## 五、数据流说明

### 5.1 文档上传流程

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
创建 Document 记录（status=pending）
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

### 5.2 搜索流程

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
返回结果（含高亮HTML、相关度分数、摘要）
    |
    v
前端渲染：标题高亮 + 内容摘要 + 元信息
```

### 5.3 热门搜索更新

```
每次搜索 -> SearchService._log_search() 写入 search_logs 表
    |
    v
GET /api/v1/search/hot 查询最近24小时搜索频率
    |
    v
GROUP BY query ORDER BY COUNT(*) DESC LIMIT 10
    |
    v
前端首页展示热搜标签云
```

---

## 六、关键设计决策

| 决策 | 方案 | 理由 |
|------|------|------|
| 全文检索 | PostgreSQL tsvector (simple config) | 1万文档量级够用，免运维ES |
| 异步解析 | Celery + Redis | DOCX解析可能耗时，不阻塞用户请求 |
| 文件存储 | /tmp (MVP) | 解析后删除原始文件，节省50GB磁盘 |
| 前端状态 | Pinia (非Vuex) | Vue3官方推荐，TypeScript友好 |
| 路由模式 | Hash History | 无需后端配置，部署简单 |
| 搜索建议 | 基于历史搜索前缀匹配 | 无需额外服务，数据自然积累 |

---

## 七、扩展预留点

| 扩展点 | 当前预留 | 触发条件 |
|--------|----------|----------|
| Elasticsearch | 文档元数据结构兼容 | 数据量>50万或相关性不足 |
| 对象存储 | StorageBackend 抽象接口 | /tmp不够或需要高可用 |
| SSO/LDAP | auth_type 字段 + AuthProvider 接口 | 企业接入需求 |
| 分片上传 | 前端 upload 组件预留 | 单文件>20MB场景 |
| 监控告警 | prometheus-client 已安装 | W6生产强化阶段 |

---

*本文档随项目进展持续更新*
