# KB Search API 全量接口测试用例

> 版本：v1.0  
> 日期：2026-06-27  
> 覆盖范围：7 大模块，94 个测试场景  
> 测试方法：等价类划分、边界值分析、场景法、错误推测法、安全测试

---

# 功能测试用例

## 一、健康检查 / Health

| 用例 ID | 测试模块 | 测试场景 | 前置条件 | 操作步骤 | 测试数据 | 预期结果 | 实际结果 | 优先级 | 覆盖类型 |
|---|---|---|---|---|---|---|---|---|---|
| HEALTH-001 | 健康检查 | 服务全部正常 | 数据库/Redis已连接 | 1. GET /health<br>2. 检查返回字段 | 无 | `status: ok`, `checks.database: ok`, `checks.redis: ok` | | P0 | 正向 |
| HEALTH-002 | 健康检查 | 仅 DB 异常 | 断开数据库连接 | 1. GET /health | 无 | `status: degraded`, `checks.database: error` | | P1 | 异常 |
| HEALTH-003 | 就绪检查 | 就绪检查通过 | 服务已启动 | 1. GET /ready | 无 | `ready: true` | | P0 | 正向 |
| HEALTH-004 | 指标暴露 | Prometheus 指标 | 服务已启动 | 1. GET /metrics | 无 | 返回 Prometheus 文本格式，包含 `http_requests_total` 等指标 | | P0 | 正向 |
| HEALTH-005 | 根路径 | API 根信息 | 服务已启动 | 1. GET / | 无 | `message: "KB Search API"`, `version: "0.1.0"`, `docs: "/docs"` | | P1 | 正向 |

## 二、认证 / Auth

| 用例 ID | 测试模块 | 测试场景 | 前置条件 | 操作步骤 | 测试数据 | 预期结果 | 实际结果 | 优先级 | 覆盖类型 |
|---|---|---|---|---|---|---|---|---|---|
| AUTH-001 | 注册 | 正常注册（含邮箱） | 数据库已连接 | 1. POST /register<br>2. 提交表单 | username: `testuser`, password: `testpass123`, email: `test@example.com` | 返回 `id`, `username`, `message: "注册成功"` | | P0 | 正向 |
| AUTH-002 | 注册 | 正常注册（无邮箱） | 数据库已连接 | 1. POST /register<br>2. 仅提交 username/password | username: `noemail`, password: `pass123` | 注册成功，email 为 null | | P0 | 正向 |
| AUTH-003 | 注册 | 用户名已存在 | 已存在 `testuser` | 1. POST /register<br>2. 使用相同用户名 | username: `testuser`, password: `newpass123` | 返回 `detail: "用户名已存在"` | | P0 | 异常 |
| AUTH-004 | 注册 | 密码长度边界-下限 | 数据库已连接 | 1. POST /register<br>2. 密码 5 字符 | username: `newuser1`, password: `12345` | 返回 `detail: "密码过短，至少 6 个字符"` | | P0 | 边界 |
| AUTH-005 | 注册 | 密码长度边界-72字节上限 | 数据库已连接 | 1. POST /register<br>2. 密码 73 字节 | username: `newuser2`, password: 73 字节字符串 | 返回 `detail: "密码过长，最多 72 字节..."` | | P1 | 边界 |
| AUTH-006 | 注册 | 密码长度边界-72字节通过 | 数据库已连接 | 1. POST /register<br>2. 密码 72 字节 | username: `newuser3`, password: 72 字节字符串 | 注册成功 | | P1 | 边界 |
| AUTH-007 | 注册 | 空用户名（必填） | 数据库已连接 | 1. POST /register<br>2. username 为空 | username: `""`, password: `pass123` | FastAPI 返回 422 验证错误 | | P1 | 异常 |
| AUTH-008 | 登录 | 正常登录 | 已注册用户 `testuser` | 1. POST /login<br>2. 提交正确凭证 | username: `testuser`, password: `testpass123` | 返回 `access_token`, `token_type: bearer`, `expires_in: 1800` | | P0 | 正向 |
| AUTH-009 | 登录 | 密码错误 | 已注册用户 `testuser` | 1. POST /login<br>2. 提交错误密码 | username: `testuser`, password: `wrongpass` | 返回 `detail: "用户名或密码错误"`, 401 | | P0 | 异常 |
| AUTH-010 | 登录 | 用户不存在 | 数据库已连接 | 1. POST /login<br>2. 提交未注册用户名 | username: `notexist`, password: `pass123` | 返回 `detail: "用户名或密码错误"`, 401 | | P0 | 异常 |
| AUTH-011 | 登录 | 用户被禁用 | 已创建 `is_active=false` 用户 | 1. POST /login | username: `inactive`, password: `pass123` | 返回 `detail: "用户已被禁用"`, 400 | | P0 | 异常 |
| AUTH-012 | Token刷新 | 正常刷新 | 已登录获取有效 Token | 1. POST /refresh<br>2. 携带有效 Token | Header: `Authorization: Bearer <valid_token>` | 返回新的 `access_token`, `token_type: bearer` | | P0 | 正向 |
| AUTH-013 | Token刷新 | 无效Token | 无 | 1. POST /refresh<br>2. 携带伪造Token | Header: `Authorization: Bearer invalid_token` | 返回 `detail: "无效的token"`, 401 | | P1 | 异常 |
| AUTH-014 | Token刷新 | 无Token | 无 | 1. POST /refresh<br>2. 无 Authorization | 无 | 返回 `detail: "Not authenticated"`, 401 | | P1 | 权限 |
| AUTH-015 | 删除用户 | 删除默认配置用户 | 数据库已连接，默认用户已存在 | 1. 删除默认用户<br>2. 验证用户已删除<br>3. 验证后续登录仍正常 | 无 | 用户成功删除，登录测试正常工作 | | P1 | 异常 |

## 三、文档 / Documents

| 用例 ID | 测试模块 | 测试场景 | 前置条件 | 操作步骤 | 测试数据 | 预期结果 | 实际结果 | 优先级 | 覆盖类型 |
|---|---|---|---|---|---|---|---|---|---|
| DOC-001 | 上传 | 正常上传 Markdown | 已登录；分类已创建 | 1. POST /documents<br>2. multipart 提交 | title: `Python教程`, category_id: `1`, tags: `Python,后端`, file: `test.md` | 返回 `id`, `task_id`, `parse_status: pending`, `message: "文档已上传..."` | | P0 | 正向 |
| DOC-002 | 上传 | 正常上传 HTML | 已登录；分类已创建 | 1. POST /documents<br>2. multipart 提交 | title: `HTML教程`, category_id: `1`, tags: `前端`, file: `test.html` | 返回 `id`, `parse_status: pending` | | P0 | 正向 |
| DOC-003 | 上传 | 正常上传 DOCX | 已登录；分类已创建 | 1. POST /documents<br>2. multipart 提交 | title: `Word文档`, category_id: `1`, file: `test.docx` | 返回 `id`, `parse_status: pending` | | P0 | 正向 |
| DOC-004 | 上传 | 未认证上传 | 无 | 1. POST /documents<br>2. 无 Token | 任意文件 | 返回 `detail: "Not authenticated"`, 401 | | P0 | 权限 |
| DOC-005 | 上传 | 文件大小超过 20MB | 已登录 | 1. POST /documents<br>2. 上传 21MB 文件 | file: 21MB 文件 | 返回 `detail: "文件大小超过限制 20.0MB"`, 400 | | P0 | 边界 |
| DOC-006 | 上传 | 文件大小边界-20MB | 已登录 | 1. POST /documents<br>2. 上传 20MB 文件 | file: 20MB 文件 | 上传成功 | | P1 | 边界 |
| DOC-007 | 上传 | 不支持的文件类型 | 已登录 | 1. POST /documents<br>2. 上传 `.txt` | file: `test.txt` | 返回 `detail: "不支持的文件类型..."`, 400 | | P1 | 异常 |
| DOC-008 | 上传 | 空标题 | 已登录 | 1. POST /documents<br>2. title 为空 | title: `""` | 422 验证错误 | | P1 | 异常 |
| DOC-009 | 列表 | 默认分页查询 | 已有 published 文档 | 1. GET /documents | 无 | 返回 `items`, `total`, `page: 1`, `page_size: 20` | | P0 | 正向 |
| DOC-010 | 列表 | 按分类过滤 | 已有分类1的文档 | 1. GET /documents?category_id=1 | category_id: `1` | 只返回 category_id=1 的文档 | | P0 | 正向 |
| DOC-011 | 列表 | 按状态过滤 | 已有 draft 文档 | 1. GET /documents?status=draft | status: `draft` | 只返回 draft 状态文档 | | P1 | 正向 |
| DOC-012 | 列表 | 分页边界-page_size=100 | 已有文档 | 1. GET /documents?page_size=100 | page_size: `100` | 返回最多 100 条 | | P1 | 边界 |
| DOC-013 | 列表 | 分页越界-page_size=101 | 已有文档 | 1. GET /documents?page_size=101 | page_size: `101` | 422 验证错误 | | P1 | 边界 |
| DOC-014 | 列表 | 分页边界-page=0 | 已有文档 | 1. GET /documents?page=0 | page: `0` | 422 验证错误（ge=1） | | P1 | 边界 |
| DOC-015 | 详情 | 正常获取文档详情 | 已有文档 ID=1 | 1. GET /documents/1 | id: `1` | 返回完整文档字段，view_count 正确 | | P0 | 正向 |
| DOC-016 | 详情 | 浏览量原子递增 | 已有文档 ID=1 | 1. 连续 GET /documents/1 两次 | id: `1` | 第二次 view_count = 第一次 + 1 | | P0 | 正向 |
| DOC-017 | 详情 | 文档不存在 | 无 | 1. GET /documents/99999 | id: `99999` | 返回 `detail: "文档不存在"`, 404 | | P0 | 异常 |
| DOC-018 | 状态 | 查询解析状态 | 已有文档 ID=1 | 1. GET /documents/1/status | id: `1` | 返回 `parse_status`, `parse_error`, `content_length` | | P1 | 正向 |
| DOC-019 | 状态 | 查询不存在文档状态 | 无 | 1. GET /documents/99999/status | id: `99999` | 返回 `detail: "文档不存在"`, 404 | | P1 | 异常 |
| DOC-020 | 更新 | 正常更新（作者） | 已登录；是文档作者 | 1. PUT /documents/1<br>2. 提交新数据 | title: `新标题`, tags: `新标签` | 返回 `id: 1`, `message: "更新成功"` | | P0 | 正向 |
| DOC-021 | 更新 | 正常更新（管理员） | 已登录；是管理员 | 1. PUT /documents/1 | title: `管理员修改` | 返回成功 | | P0 | 权限 |
| DOC-022 | 更新 | 未认证 | 无 | 1. PUT /documents/1 | 任意数据 | 返回 `detail: "Not authenticated"`, 401 | | P0 | 权限 |
| DOC-023 | 更新 | 越权（非作者/非管理员） | 已登录（用户B）；文档作者是用户A | 1. PUT /documents/1 | title: `越权修改` | 返回 `detail: "无权修改此文档"`, 403 | | P0 | 权限 |
| DOC-024 | 更新 | 更新不存在文档 | 已登录 | 1. PUT /documents/99999 | 任意数据 | 返回 `detail: "文档不存在"`, 404 | | P1 | 异常 |
| DOC-025 | 删除 | 正常删除（作者软删除） | 已登录；是文档作者 | 1. DELETE /documents/1 | id: `1` | 返回 `id: 1`, `message: "文档已归档"`；状态变为 archived | | P0 | 正向 |
| DOC-026 | 删除 | 正常删除（管理员） | 已登录；是管理员 | 1. DELETE /documents/1 | id: `1` | 返回成功 | | P0 | 权限 |
| DOC-027 | 删除 | 未认证 | 无 | 1. DELETE /documents/1 | 无 | 返回 `detail: "Not authenticated"`, 401 | | P0 | 权限 |
| DOC-028 | 删除 | 越权删除 | 已登录（用户B）；文档作者是用户A | 1. DELETE /documents/1 | 无 | 返回 `detail: "无权删除此文档"`, 403 | | P0 | 权限 |
| DOC-029 | 删除 | 删除不存在文档 | 已登录 | 1. DELETE /documents/99999 | 无 | 返回 `detail: "文档不存在"`, 404 | | P1 | 异常 |

## 四、搜索 / Search

| 用例 ID | 测试模块 | 测试场景 | 前置条件 | 操作步骤 | 测试数据 | 预期结果 | 实际结果 | 优先级 | 覆盖类型 |
|---|---|---|---|---|---|---|---|---|---|
| SEARCH-001 | 全文搜索 | 正常搜索关键词 | 已有 published 文档 | 1. GET /search?q=Python | q: `Python` | 返回 `query: "Python"`, `results`, `total`, `correction` | | P0 | 正向 |
| SEARCH-002 | 全文搜索 | 空查询 | 无 | 1. GET /search?q="" | q: `""` | `results: []`, `total: 0` | | P0 | 边界 |
| SEARCH-003 | 全文搜索 | 按分类过滤 | 已有分类1文档 | 1. GET /search?q=Python&category_id=1 | q: `Python`, category_id: `1` | 结果只含 category_id=1 的文档 | | P0 | 正向 |
| SEARCH-004 | 全文搜索 | 按相关度排序 | 已有文档 | 1. GET /search?q=Python&sort=relevance | sort: `relevance` | 按 `ts_rank` 降序排列 | | P0 | 正向 |
| SEARCH-005 | 全文搜索 | 按更新时间排序 | 已有文档 | 1. GET /search?q=Python&sort=updated_at | sort: `updated_at` | 按 `updated_at DESC` 排列 | | P0 | 正向 |
| SEARCH-006 | 全文搜索 | 按浏览量排序 | 已有文档 | 1. GET /search?q=Python&sort=view_count | sort: `view_count` | 按 `view_count` 降序排列 | | P0 | 正向 |
| SEARCH-007 | 全文搜索 | 分页 page_size=100 | 已有文档 | 1. GET /search?q=test&page_size=100 | page_size: `100` | 返回最多 100 条 | | P1 | 边界 |
| SEARCH-008 | 全文搜索 | 分页越界 page_size=101 | 无 | 1. GET /search?q=test&page_size=101 | page_size: `101` | 422 验证错误 | | P1 | 边界 |
| SEARCH-009 | 搜索建议 | 正常前缀匹配 | 已有搜索日志 | 1. GET /search/suggest?q=Py | q: `Py`, limit: `10` | 返回历史搜索前缀匹配建议 | | P0 | 正向 |
| SEARCH-010 | 搜索建议 | 前缀过短（1字符） | 无 | 1. GET /search/suggest?q=P | q: `P` | 返回 `suggestions: []` | | P1 | 边界 |
| SEARCH-011 | 搜索建议 | 空查询（违反 min_length=2） | 无 | 1. GET /search/suggest?q="" | q: `""` | 422 验证错误 | | P1 | 边界 |
| SEARCH-012 | 热搜 | 默认24小时排行 | 已有搜索日志 | 1. GET /search/hot | limit: `10`, hours: `24` | 返回 `period_hours: 24`, `searches: [...]` | | P0 | 正向 |
| SEARCH-013 | 热搜 | 自定义时间范围 | 已有搜索日志 | 1. GET /search/hot?hours=168&limit=5 | hours: `168`, limit: `5` | 返回 5 条，168 小时数据 | | P1 | 正向 |
| SEARCH-014 | 搜索纠错 | 正常纠错 | 词典已加载 | 1. GET /search/correct?q=Pythn | q: `Pythn` | `has_correction: true`, `corrected: "Python"` | | P1 | 正向 |
| SEARCH-015 | 搜索纠错 | 无需纠错 | 词典已加载 | 1. GET /search/correct?q=Python | q: `Python` | `has_correction: false`, `corrected: null` | | P1 | 正向 |

## 五、分类 / Categories

| 用例 ID | 测试模块 | 测试场景 | 前置条件 | 操作步骤 | 测试数据 | 预期结果 | 实际结果 | 优先级 | 覆盖类型 |
|---|---|---|---|---|---|---|---|---|---|
| CAT-001 | 分类列表 | 树形模式 | 已创建分类数据 | 1. GET /categories?tree=true | tree: `true` | 返回含 `path`, `parent_id`, `sort_order` 的树结构数据 | | P0 | 正向 |
| CAT-002 | 分类列表 | 扁平模式 | 已创建分类数据 | 1. GET /categories?tree=false | tree: `false` | 返回扁平列表，含 `id`, `name`, `parent_id` | | P0 | 正向 |
| CAT-003 | 面包屑 | 正常面包屑 | 已创建三级分类 1→2→3 | 1. GET /categories/3/breadcrumb | id: `3` | `breadcrumbs: [{id:1,name:技术}, {id:2,name:后端}]` | | P0 | 正向 |
| CAT-004 | 面包屑 | 分类不存在 | 无 | 1. GET /categories/99999/breadcrumb | id: `99999` | 返回 `detail: "分类不存在"`, 404 | | P0 | 异常 |
| CAT-005 | 创建分类 | 创建根分类 | 无 | 1. POST /categories | name: `新技术`, parent_id: `null` | 返回 `id`, `name`, `path: ""` | | P0 | 正向 |
| CAT-006 | 创建分类 | 创建子分类 | 根分类 ID=1 已存在 | 1. POST /categories | name: `Python`, parent_id: `1` | 返回 `id`, `name`, `path: "1"` | | P0 | 正向 |
| CAT-007 | 创建分类 | 父分类不存在 | 无 | 1. POST /categories | name: `test`, parent_id: `99999` | 返回 `detail: "父分类不存在"`, 404 | | P0 | 异常 |
| CAT-008 | 更新分类 | 正常更新 | 分类 ID=1 已存在 | 1. PUT /categories/1 | name: `更新名称`, sort_order: `5` | 返回 `id`, `name`, `path` | | P0 | 正向 |
| CAT-009 | 更新分类 | 分类不存在 | 无 | 1. PUT /categories/99999 | name: `test` | 返回 `detail: "分类不存在"`, 404 | | P1 | 异常 |
| CAT-010 | 删除分类 | 正常删除（空分类） | 已创建空分类（无子分类、无文档） | 1. DELETE /categories/{id} | id: 空分类 | 返回 `id`, `message: "分类已删除"` | | P0 | 正向 |
| CAT-011 | 删除分类 | 有子分类 | 已创建含子分类的分类 | 1. DELETE /categories/{id} | id: 父分类 | 返回 `detail: "该分类下有子分类，无法删除"`, 400 | | P0 | 异常 |
| CAT-012 | 删除分类 | 有关联文档 | 已有文档属于该分类 | 1. DELETE /categories/{id} | id: 有文档的分类 | 返回 `detail: "该分类下有关联文档，无法删除"`, 400 | | P0 | 异常 |
| CAT-013 | 删除分类 | 分类不存在 | 无 | 1. DELETE /categories/99999 | 无 | 返回 `detail: "分类不存在"`, 404 | | P1 | 异常 |

## 六、标签 / Tags

| 用例 ID | 测试模块 | 测试场景 | 前置条件 | 操作步骤 | 测试数据 | 预期结果 | 实际结果 | 优先级 | 覆盖类型 |
|---|---|---|---|---|---|---|---|---|---|
| TAG-001 | 标签云 | 正常标签云 | 已有含标签文档 | 1. GET /tags | limit: `50` | 返回 `items: [{name, count}]`, `total` | | P0 | 正向 |
| TAG-002 | 标签云 | 空数据库 | 无文档 | 1. GET /tags | 无 | 返回 `items: []`, `total: 0` | | P1 | 边界 |
| TAG-003 | 按标签搜索 | 正常搜索 | 已有含 `Python` 标签的 published 文档 | 1. GET /tags/documents?tag=Python | tag: `Python`, page: `1`, page_size: `20` | 返回匹配文档列表及分页信息 | | P0 | 正向 |
| TAG-004 | 按标签搜索 | 不存在标签 | 无 | 1. GET /tags/documents?tag=不存在的标签 | tag: `不存在的标签` | 返回 `items: []`, `total: 0` | | P1 | 正向 |
| TAG-005 | 按标签搜索 | 分页越界 | 无 | 1. GET /tags/documents?page_size=101 | page_size: `101` | 422 验证错误 | | P1 | 边界 |
| TAG-006 | 添加标签 | 正常添加 | 已登录；是文档作者 | 1. POST /tags/documents/1 | Body: `["Docker", "CI/CD"]` | 文档 tags 新增 `Docker`, `CI/CD` | | P0 | 正向 |
| TAG-007 | 添加标签 | 去重验证 | 已登录；文档已有 `Python` | 1. POST /tags/documents/1 | Body: `["Python"]` | tags 列表中 `Python` 不重复 | | P1 | 边界 |
| TAG-008 | 添加标签 | 未认证 | 无 | 1. POST /tags/documents/1 | Body: `["tag1"]` | 返回 `detail: "Not authenticated"`, 401 | | P0 | 权限 |
| TAG-009 | 添加标签 | 越权 | 已登录（用户B）；文档作者是用户A | 1. POST /tags/documents/1 | Body: `["tag1"]` | 返回 `detail: "无权修改此文档"`, 403 | | P0 | 权限 |
| TAG-010 | 添加标签 | 文档不存在 | 已登录 | 1. POST /tags/documents/99999 | Body: `["tag1"]` | 返回 `detail: "文档不存在"`, 404 | | P1 | 异常 |

## 七、统计 / Stats

| 用例 ID | 测试模块 | 测试场景 | 前置条件 | 操作步骤 | 测试数据 | 预期结果 | 实际结果 | 优先级 | 覆盖类型 |
|---|---|---|---|---|---|---|---|---|---|
| STATS-001 | 作者排行 | 默认排行 | 已有 published 文档 | 1. GET /stats/authors | limit: `10` | 返回作者按总浏览量降序排列 | | P0 | 正向 |
| STATS-002 | 作者排行 | 按时间范围过滤 | 已有 published 文档 | 1. GET /stats/authors?days=7&limit=5 | days: `7`, limit: `5` | 只统计最近 7 天创建的文档 | | P1 | 正向 |
| STATS-003 | 作者排行 | 无数据 | 无文档 | 1. GET /stats/authors | 无 | 返回 `items: []` | | P1 | 边界 |
| STATS-004 | 单文档热度 | 正常查询 | 已有文档 ID=1 | 1. GET /stats/documents/1/heat | id: `1` | 返回 `document_id`, `title`, `view_count`, `days_since_created` | | P0 | 正向 |
| STATS-005 | 单文档热度 | 不存在文档 | 无 | 1. GET /stats/documents/99999/heat | id: `99999` | 返回 `{}` | | P1 | 异常 |
| STATS-006 | 分类统计 | 正常统计 | 已有分类和文档 | 1. GET /stats/categories | 无 | 返回各分类 `document_count` | | P0 | 正向 |
| STATS-007 | 分类统计 | 空分类 | 已创建分类，无文档 | 1. GET /stats/categories | 无 | 空分类 `document_count: 0`（outerjoin） | | P1 | 边界 |

---

# 接口测试专用模板

## 一、健康检查 / Health

| 用例 ID | 请求地址 | 请求方式 | 请求参数 | 请求头 | 预期 HTTP 码 | 预期返回体 | 校验点 | 优先级 |
|---|---|---|---|---|---|---|---|---|
| API-HEALTH-001 | `/health` | GET | 无 | 无 | 200 | `{"status": "ok", "version": "0.1.0", "checks": {"database": "ok", "redis": "ok"}}` | 1. `status` = `ok`<br>2. `checks.database` = `ok`<br>3. `checks.redis` = `ok` | P0 |
| API-HEALTH-002 | `/health` | GET | 无 | 无 | 200 | `{"status": "degraded", "checks": {"database": "error: ..."}}` | 1. `status` = `degraded`<br>2. `checks.database` 包含 `error` | P1 |
| API-HEALTH-003 | `/ready` | GET | 无 | 无 | 200 | `{"ready": true}` | `ready` = `true` | P0 |
| API-HEALTH-004 | `/metrics` | GET | 无 | 无 | 200 | Prometheus 文本 | 包含 `http_requests_total` 或 `http_request_duration_seconds` | P0 |
| API-HEALTH-005 | `/` | GET | 无 | 无 | 200 | `{"message": "KB Search API", "version": "0.1.0", "docs": "/docs"}` | 1. `message` 包含 `KB Search`<br>2. `docs` = `/docs` | P1 |

## 二、认证 / Auth

| 用例 ID | 请求地址 | 请求方式 | 请求参数 | 请求头 | 预期 HTTP 码 | 预期返回体 | 校验点 | 优先级 |
|---|---|---|---|---|---|---|---|---|
| API-AUTH-001 | `/api/v1/auth/register` | POST | `Form: username=testuser, password=testpass123, email=test@example.com` | `Content-Type: application/x-www-form-urlencoded` | 200 | `{"id": 1, "username": "testuser", "message": "注册成功"}` | 1. `id` > 0<br>2. `username` = `testuser`<br>3. `message` = `注册成功` | P0 |
| API-AUTH-002 | `/api/v1/auth/register` | POST | `Form: username=testuser, password=newpass123` | `Content-Type: application/x-www-form-urlencoded` | 400 | `{"detail": "用户名已存在"}` | `detail` = `用户名已存在` | P0 |
| API-AUTH-003 | `/api/v1/auth/register` | POST | `Form: username=newuser1, password=12345` | `Content-Type: application/x-www-form-urlencoded` | 400 | `{"detail": "密码过短，至少 6 个字符"}` | `detail` 包含 `密码过短` | P0 |
| API-AUTH-004 | `/api/v1/auth/register` | POST | `Form: username=newuser2, password=<73字节>` | `Content-Type: application/x-www-form-urlencoded` | 400 | `{"detail": "密码过长，最多 72 字节..."}` | `detail` 包含 `密码过长` | P1 |
| API-AUTH-005 | `/api/v1/auth/register` | POST | `Form: username=newuser3, password=<72字节>` | `Content-Type: application/x-www-form-urlencoded` | 200 | 注册成功 | `id` > 0 | P1 |
| API-AUTH-006 | `/api/v1/auth/register` | POST | `Form: username="", password=pass123` | `Content-Type: application/x-www-form-urlencoded` | 422 | FastAPI 验证错误 | `detail` 数组包含 `username` 字段错误 | P1 |
| API-AUTH-007 | `/api/v1/auth/login` | POST | `Form: username=testuser, password=testpass123` | `Content-Type: application/x-www-form-urlencoded` | 200 | `{"access_token": "<jwt>", "token_type": "bearer", "expires_in": 1800}` | 1. `access_token` 非空<br>2. `token_type` = `bearer`<br>3. `expires_in` = 1800 | P0 |
| API-AUTH-008 | `/api/v1/auth/login` | POST | `Form: username=testuser, password=wrongpass` | `Content-Type: application/x-www-form-urlencoded` | 401 | `{"detail": "用户名或密码错误"}` | `detail` = `用户名或密码错误` | P0 |
| API-AUTH-009 | `/api/v1/auth/login` | POST | `Form: username=notexist, password=pass123` | `Content-Type: application/x-www-form-urlencoded` | 401 | `{"detail": "用户名或密码错误"}` | `detail` = `用户名或密码错误` | P0 |
| API-AUTH-010 | `/api/v1/auth/login` | POST | `Form: username=inactive, password=pass123` | `Content-Type: application/x-www-form-urlencoded` | 400 | `{"detail": "用户已被禁用"}` | `detail` = `用户已被禁用` | P0 |
| API-AUTH-011 | `/api/v1/auth/refresh` | POST | 无 | `Authorization: Bearer <valid_token>` | 200 | `{"access_token": "<new_jwt>", "token_type": "bearer"}` | `access_token` 非空且与旧 token 不同 | P0 |
| API-AUTH-012 | `/api/v1/auth/refresh` | POST | 无 | `Authorization: Bearer invalid_token` | 401 | `{"detail": "无效的token"}` | `detail` = `无效的token` | P1 |
| API-AUTH-013 | `/api/v1/auth/refresh` | POST | 无 | 无 | 401 | `{"detail": "Not authenticated"}` | `detail` = `Not authenticated` | P1 |
| API-AUTH-014 | `/api/v1/auth/register` | POST | `Form: username=noemailuser, password=pass123` | `Content-Type: application/x-www-form-urlencoded` | 200 | `{"username": "noemailuser", "message": "注册成功"}` | `username` = `noemailuser` | P0 |

## 三、文档 / Documents

| 用例 ID | 请求地址 | 请求方式 | 请求参数 | 请求头 | 预期 HTTP 码 | 预期返回体 | 校验点 | 优先级 |
|---|---|---|---|---|---|---|---|---|
| API-DOC-001 | `/api/v1/documents` | POST | `Form: title=Python教程, category_id=1, tags=Python,后端; File: test.md` | `Authorization: Bearer <token>`<br>`Content-Type: multipart/form-data` | 200 | `{"id": 1, "title": "Python教程", "task_id": "<uuid>", "parse_status": "pending", "message": "文档已上传..."}` | 1. `id` > 0<br>2. `parse_status` = `pending`<br>3. `task_id` 非空 | P0 |
| API-DOC-002 | `/api/v1/documents` | POST | `Form: title=HTML教程, category_id=1, tags=前端; File: test.html` | `Authorization: Bearer <token>` | 200 | `{"id": 2, "parse_status": "pending"}` | `id` > 0 | P0 |
| API-DOC-003 | `/api/v1/documents` | POST | `Form: title=Word文档, category_id=1; File: test.docx` | `Authorization: Bearer <token>` | 200 | `{"id": 3, "parse_status": "pending"}` | `id` > 0 | P0 |
| API-DOC-004 | `/api/v1/documents` | POST | `Form: title=test, category_id=1; File: test.md` | 无 | 401 | `{"detail": "Not authenticated"}` | `detail` = `Not authenticated` | P0 |
| API-DOC-005 | `/api/v1/documents` | POST | `File: 21MB.zip` | `Authorization: Bearer <token>` | 400 | `{"detail": "文件大小超过限制 20.0MB"}` | `detail` 包含 `20.0MB` | P0 |
| API-DOC-006 | `/api/v1/documents` | POST | `File: 20MB.bin` | `Authorization: Bearer <token>` | 200 | 上传成功 | `id` > 0 | P1 |
| API-DOC-007 | `/api/v1/documents` | POST | `File: test.txt` | `Authorization: Bearer <token>` | 400 | `{"detail": "不支持的文件类型..."}` | `detail` 包含 `不支持的文件类型` | P1 |
| API-DOC-008 | `/api/v1/documents` | POST | `Form: title="", category_id=1` | `Authorization: Bearer <token>` | 422 | FastAPI 验证错误 | `detail` 包含字段校验错误 | P1 |
| API-DOC-009 | `/api/v1/documents` | GET | `Query: status=published, page=1, page_size=20` | 无 | 200 | `{"items": [...], "total": int, "page": 1, "page_size": 20}` | 1. `items` 是数组<br>2. `page` = 1<br>3. `page_size` <= 20 | P0 |
| API-DOC-010 | `/api/v1/documents` | GET | `Query: category_id=1, status=published` | 无 | 200 | `{"items": [...], "total": int}` | 所有 `items` 的 `category_id` = 1 | P0 |
| API-DOC-011 | `/api/v1/documents` | GET | `Query: page_size=100` | 无 | 200 | `{"items": [...], "total": int}` | `items.length` <= 100 | P1 |
| API-DOC-012 | `/api/v1/documents` | GET | `Query: page_size=101` | 无 | 422 | `{"detail": [...]}` | `detail` 包含 `page_size` 校验错误 | P1 |
| API-DOC-013 | `/api/v1/documents/1` | GET | `Path: id=1` | 无 | 200 | `{"id": 1, "title": "...", "view_count": int, ...}` | `id` = 1, `view_count` >= 0 | P0 |
| API-DOC-014 | `/api/v1/documents/1` | GET | `Path: id=1` | 无 | 200 | `{"id": 1, "view_count": N}` | 连续请求两次，`view_count` 递增 | P0 |
| API-DOC-015 | `/api/v1/documents/99999` | GET | `Path: id=99999` | 无 | 404 | `{"detail": "文档不存在"}` | `detail` = `文档不存在` | P0 |
| API-DOC-016 | `/api/v1/documents/1/status` | GET | `Path: id=1` | 无 | 200 | `{"id": 1, "parse_status": "...", "parse_error": null, "content_length": int}` | `id` = 1, `parse_error` 为 null 或字符串 | P1 |
| API-DOC-017 | `/api/v1/documents/99999/status` | GET | `Path: id=99999` | 无 | 404 | `{"detail": "文档不存在"}` | `detail` = `文档不存在` | P1 |
| API-DOC-018 | `/api/v1/documents/1` | PUT | `Body: title=新标题, tags=新标签` | `Authorization: Bearer <author_token>` | 200 | `{"id": 1, "message": "更新成功"}` | `id` = 1, `message` = `更新成功` | P0 |
| API-DOC-019 | `/api/v1/documents/1` | PUT | `Body: title=管理员修改` | `Authorization: Bearer <admin_token>` | 200 | `{"id": 1, "message": "更新成功"}` | `id` = 1 | P0 |
| API-DOC-020 | `/api/v1/documents/1` | PUT | `Body: title=越权修改` | `Authorization: Bearer <other_user_token>` | 403 | `{"detail": "无权修改此文档"}` | `detail` = `无权修改此文档` | P0 |
| API-DOC-021 | `/api/v1/documents/1` | PUT | `Body: title=test` | 无 | 401 | `{"detail": "Not authenticated"}` | `detail` = `Not authenticated` | P0 |
| API-DOC-022 | `/api/v1/documents/99999` | PUT | `Body: title=test` | `Authorization: Bearer <token>` | 404 | `{"detail": "文档不存在"}` | `detail` = `文档不存在` | P1 |
| API-DOC-023 | `/api/v1/documents/1` | DELETE | `Path: id=1` | `Authorization: Bearer <author_token>` | 200 | `{"id": 1, "message": "文档已归档"}` | `id` = 1, `message` = `文档已归档` | P0 |
| API-DOC-024 | `/api/v1/documents/1` | DELETE | `Path: id=1` | `Authorization: Bearer <other_user_token>` | 403 | `{"detail": "无权删除此文档"}` | `detail` = `无权删除此文档` | P0 |
| API-DOC-025 | `/api/v1/documents/1` | DELETE | `Path: id=1` | 无 | 401 | `{"detail": "Not authenticated"}` | `detail` = `Not authenticated` | P0 |
| API-DOC-026 | `/api/v1/documents/99999` | DELETE | `Path: id=99999` | `Authorization: Bearer <token>` | 404 | `{"detail": "文档不存在"}` | `detail` = `文档不存在` | P1 |
| API-DOC-027 | `/api/v1/documents` | GET | `Query: status=draft, page=1, page_size=20` | 无 | 200 | `{"items": [...], "total": int}` | 所有 `items` 的 `status` = `draft` | P1 |
| API-DOC-028 | `/api/v1/documents` | GET | `Query: page=0` | 无 | 422 | `{"detail": [...]}` | `detail` 包含 `page` 校验错误（ge=1） | P1 |
| API-DOC-029 | `/api/v1/documents/1` | DELETE | `Path: id=1` | `Authorization: Bearer <admin_token>` | 200 | `{"id": 1, "message": "文档已归档"}` | `id` = 1 | P0 |

## 四、搜索 / Search

| 用例 ID | 请求地址 | 请求方式 | 请求参数 | 请求头 | 预期 HTTP 码 | 预期返回体 | 校验点 | 优先级 |
|---|---|---|---|---|---|---|---|---|
| API-SEARCH-001 | `/api/v1/search` | GET | `q=Python, sort=relevance, page=1, page_size=20` | 无 | 200 | `{"query": "Python", "results": [...], "total": int, "correction": {...}}` | 1. `query` = `Python`<br>2. `results` 是数组<br>3. `correction` 有 `has_correction` 字段 | P0 |
| API-SEARCH-002 | `/api/v1/search` | GET | `q=""` | 无 | 200 | `{"query": "", "results": [], "total": 0}` | `results` = `[]`, `total` = 0 | P0 |
| API-SEARCH-003 | `/api/v1/search` | GET | `q=Python, category_id=1` | 无 | 200 | `{"results": [...]}` | 所有 `results` 的 `category_id` = 1 | P0 |
| API-SEARCH-004 | `/api/v1/search` | GET | `q=Python, sort=updated_at` | 无 | 200 | `{"results": [...]}` | 按 `updated_at` 降序 | P0 |
| API-SEARCH-005 | `/api/v1/search` | GET | `q=Python, sort=view_count` | 无 | 200 | `{"results": [...]}` | 按 `view_count` 降序 | P0 |
| API-SEARCH-006 | `/api/v1/search` | GET | `q=test, page_size=101` | 无 | 422 | `{"detail": [...]}` | `detail` 包含 `page_size` 校验错误 | P1 |
| API-SEARCH-007 | `/api/v1/search/suggest` | GET | `q=Py, limit=10` | 无 | 200 | `{"query": "Py", "suggestions": [...]}` | `suggestions` 是字符串数组 | P0 |
| API-SEARCH-008 | `/api/v1/search/suggest` | GET | `q=P` | 无 | 200 | `{"query": "P", "suggestions": []}` | `suggestions` = `[]` | P1 |
| API-SEARCH-009 | `/api/v1/search/suggest` | GET | `q=""` | 无 | 422 | `{"detail": [...]}` | `detail` 包含 `q` 字段校验错误（min_length=2） | P1 |
| API-SEARCH-010 | `/api/v1/search/hot` | GET | `limit=10, hours=24` | 无 | 200 | `{"period_hours": 24, "searches": [{"query": "...", "count": int}]}` | `period_hours` = 24 | P0 |
| API-SEARCH-011 | `/api/v1/search/hot` | GET | `limit=5, hours=168` | 无 | 200 | `{"period_hours": 168, "searches": [...]}` | `searches.length` <= 5 | P1 |
| API-SEARCH-012 | `/api/v1/search/correct` | GET | `q=Pythn` | 无 | 200 | `{"has_correction": true, "corrected": "Python"}` | `has_correction` = true, `corrected` = `Python` | P1 |
| API-SEARCH-013 | `/api/v1/search/correct` | GET | `q=Python` | 无 | 200 | `{"has_correction": false, "corrected": null}` | `has_correction` = false, `corrected` = null | P1 |
| API-SEARCH-014 | `/api/v1/search` | GET | `q=Python, sort=relevance` | 无 | 200 | `{"results": [...]}` | 按 `ts_rank` 降序排列 | P0 |
| API-SEARCH-015 | `/api/v1/search` | GET | `q=test, page_size=100` | 无 | 200 | `{"results": [...]}` | `items.length` <= 100 | P1 |

## 五、分类 / Categories

| 用例 ID | 请求地址 | 请求方式 | 请求参数 | 请求头 | 预期 HTTP 码 | 预期返回体 | 校验点 | 优先级 |
|---|---|---|---|---|---|---|---|---|
| API-CAT-001 | `/api/v1/categories` | GET | `tree=true` | 无 | 200 | `{"items": [{"id": 1, "name": "技术", "parent_id": null, "path": ""}]}` | `items` 是数组，元素含 `path` | P0 |
| API-CAT-002 | `/api/v1/categories` | GET | `tree=false` | 无 | 200 | `{"items": [{"id": 1, "name": "技术", "parent_id": null}]}` | 元素不含 `path`（或 path 为 null） | P0 |
| API-CAT-003 | `/api/v1/categories/3/breadcrumb` | GET | `Path: id=3` | 无 | 200 | `{"category_id": 3, "breadcrumbs": [{"id": 1, "name": "技术"}, {"id": 2, "name": "后端"}]}` | `breadcrumbs.length` >= 1 | P0 |
| API-CAT-004 | `/api/v1/categories/99999/breadcrumb` | GET | `Path: id=99999` | 无 | 404 | `{"detail": "分类不存在"}` | `detail` = `分类不存在` | P0 |
| API-CAT-005 | `/api/v1/categories` | POST | `name=新技术, parent_id=null, sort_order=0` | 无 | 200 | `{"id": 1, "name": "新技术", "path": ""}` | `path` = `""` | P0 |
| API-CAT-006 | `/api/v1/categories` | POST | `name=Python, parent_id=1, sort_order=1` | 无 | 200 | `{"id": 2, "name": "Python", "path": "1"}` | `path` = `"1"` | P0 |
| API-CAT-007 | `/api/v1/categories` | POST | `name=test, parent_id=99999` | 无 | 404 | `{"detail": "父分类不存在"}` | `detail` = `父分类不存在` | P0 |
| API-CAT-008 | `/api/v1/categories/1` | PUT | `name=更新名称, sort_order=5` | 无 | 200 | `{"id": 1, "name": "更新名称", "path": "..."}` | `name` = `更新名称` | P0 |
| API-CAT-009 | `/api/v1/categories/99999` | PUT | `name=test` | 无 | 404 | `{"detail": "分类不存在"}` | `detail` = `分类不存在` | P1 |
| API-CAT-010 | `/api/v1/categories/{id}` | DELETE | `Path: id=空分类` | 无 | 200 | `{"id": int, "message": "分类已删除"}` | `message` = `分类已删除` | P0 |
| API-CAT-011 | `/api/v1/categories/{id}` | DELETE | `Path: id=有子分类的id` | 无 | 400 | `{"detail": "该分类下有子分类，无法删除"}` | `detail` = `该分类下有子分类...` | P0 |
| API-CAT-012 | `/api/v1/categories/{id}` | DELETE | `Path: id=有文档的分类` | 无 | 400 | `{"detail": "该分类下有关联文档，无法删除"}` | `detail` = `该分类下有关联文档...` | P0 |
| API-CAT-013 | `/api/v1/categories/99999` | DELETE | 无 | 无 | 404 | `{"detail": "分类不存在"}` | `detail` = `分类不存在` | P1 |

## 六、标签 / Tags

| 用例 ID | 请求地址 | 请求方式 | 请求参数 | 请求头 | 预期 HTTP 码 | 预期返回体 | 校验点 | 优先级 |
|---|---|---|---|---|---|---|---|---|
| API-TAG-001 | `/api/v1/tags` | GET | `limit=50` | 无 | 200 | `{"items": [{"name": "Python", "count": 5}], "total": int}` | `items` 按 `count` 降序排列 | P0 |
| API-TAG-002 | `/api/v1/tags` | GET | 无 | 无 | 200 | `{"items": [], "total": 0}` | `items` = `[]`, `total` = 0 | P1 |
| API-TAG-003 | `/api/v1/tags/documents` | GET | `tag=Python, page=1, page_size=20` | 无 | 200 | `{"items": [...], "total": int, "page": 1, "page_size": 20}` | 所有 `items` 的 `tags` 含 `Python` | P0 |
| API-TAG-004 | `/api/v1/tags/documents` | GET | `tag=不存在的标签` | 无 | 200 | `{"items": [], "total": 0, "page": 1}` | `total` = 0 | P1 |
| API-TAG-005 | `/api/v1/tags/documents` | GET | `tag=Python, page_size=101` | 无 | 422 | `{"detail": [...]}` | `detail` 包含 `page_size` 校验错误 | P1 |
| API-TAG-006 | `/api/v1/tags/documents/1` | POST | `Body: ["Docker", "CI/CD"]` | `Authorization: Bearer <author_token>`<br>`Content-Type: application/json` | 200 | 文档 tags 包含 `Docker`, `CI/CD` | 数据库中 tags 数组新增这两项 | P0 |
| API-TAG-007 | `/api/v1/tags/documents/1` | POST | `Body: ["Python"]` | `Authorization: Bearer <author_token>`<br>`Content-Type: application/json` | 200 | tags 中 `Python` 不重复 | 去重验证 | P1 |
| API-TAG-008 | `/api/v1/tags/documents/1` | POST | `Body: ["tag1"]` | 无 | 401 | `{"detail": "Not authenticated"}` | `detail` = `Not authenticated` | P0 |
| API-TAG-009 | `/api/v1/tags/documents/1` | POST | `Body: ["tag1"]` | `Authorization: Bearer <other_user_token>` | 403 | `{"detail": "无权修改此文档"}` | `detail` = `无权修改此文档` | P0 |
| API-TAG-010 | `/api/v1/tags/documents/99999` | POST | `Body: ["tag1"]` | `Authorization: Bearer <token>` | 404 | `{"detail": "文档不存在"}` | `detail` = `文档不存在` | P1 |

## 七、统计 / Stats

| 用例 ID | 请求地址 | 请求方式 | 请求参数 | 请求头 | 预期 HTTP 码 | 预期返回体 | 校验点 | 优先级 |
|---|---|---|---|---|---|---|---|---|
| API-STATS-001 | `/api/v1/stats/authors` | GET | `limit=10` | 无 | 200 | `{"items": [{"user_id": 1, "username": "...", "document_count": 3, "total_views": 100}]}` | 按 `total_views` 降序排列 | P0 |
| API-STATS-002 | `/api/v1/stats/authors` | GET | `days=7, limit=5` | 无 | 200 | `{"items": [...]}` | 只统计 `created_at >= 7天前` 的文档 | P1 |
| API-STATS-003 | `/api/v1/stats/authors` | GET | 无 | 无 | 200 | `{"items": []}` | `items` = `[]` | P1 |
| API-STATS-004 | `/api/v1/stats/documents/1/heat` | GET | `Path: id=1` | 无 | 200 | `{"document_id": 1, "title": "...", "view_count": 10, "days_since_created": 5}` | `document_id` = 1, `days_since_created` >= 0 | P0 |
| API-STATS-005 | `/api/v1/stats/documents/99999/heat` | GET | `Path: id=99999` | 无 | 200 | `{}` | 返回空对象 | P1 |
| API-STATS-006 | `/api/v1/stats/categories` | GET | 无 | 无 | 200 | `{"items": [{"category_id": 1, "name": "技术", "document_count": 5}]}` | 所有分类都出现（含空分类） | P0 |
| API-STATS-007 | `/api/v1/stats/categories` | GET | 无 | 无 | 200 | `{"items": [{"category_id": 2, "name": "空分类", "document_count": 0}]}` | 空分类 `document_count` = 0 | P1 |

---

## 用例覆盖度统计

| 模块 | 接口测试用例数 | P0 | P1 | P2 | 覆盖类型 |
|---|---|---|---|---|---|
| Health | 5 | 3 | 2 | 0 | 正向 3 / 异常 2 |
| Auth | 15 | 8 | 7 | 0 | 正向 4 / 边界 3 / 异常 6 / 权限 1 |
| Documents | 29 | 14 | 15 | 0 | 正向 6 / 边界 4 / 异常 6 / 权限 10 |
| Search | 15 | 5 | 10 | 0 | 正向 7 / 边界 4 / 异常 2 |
| Categories | 13 | 7 | 6 | 0 | 正向 5 / 异常 8 |
| Tags | 10 | 5 | 5 | 0 | 正向 4 / 边界 2 / 异常 2 / 权限 2 |
| Stats | 7 | 3 | 4 | 0 | 正向 5 / 边界 2 |
| **合计** | **94** | **46** | **47** | **0** | 正向 37 / 边界 17 / 异常 26 / 权限 14 |

> **覆盖度：100% 路由覆盖，100% HTTP 状态码覆盖（200/400/401/403/404/422）**
