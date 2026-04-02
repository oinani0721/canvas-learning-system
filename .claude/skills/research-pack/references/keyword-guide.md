# 7 组关键词扩展指南

从用户议题生成 **7 组搜索输入**。关键词总预算控制在 **40-55 个**，避免查询漂移。

---

## 1. 直接关键词（中英文）
议题中明确提到的术语。
- 例："MagicMock 迁移" → `MagicMock`, `mock`, `neo4j`, `conftest`, `migration`

## 2. 扩展关键词
语义近义、框架术语、实现层面的术语。
- 例："性能优化" → `cache`, `memoize`, `lazy`, `index`, `pool`, `batch`, `async`, `concurrent`, `@lru_cache`, `Redis`
- 例："安全审计" → `auth`, `token`, `CORS`, `sanitize`, `inject`, `XSS`, `CSRF`, `password`, `secret`, `.env`
- 例："测试迁移" → `MagicMock`, `AsyncMock`, `patch`, `fixture`, `conftest`, `pytest.mark`, `integration`, `docker`

## 3. 路径模式
可能涉及的目录/文件名 Glob 模式。
- 例：`**/auth/**`, `**/*cache*`, `backend/tests/**/conftest.py`

## 4. 排除模式
明确不相关的目录。
- 例：议题是纯后端 → 排除 `frontend/src/components/`
- 例：议题是纯前端 → 排除 `backend/app/services/`

## 5. 技术栈专属词
框架/库特有的 API 名称。
- 例："认证" → `Depends(get_current_user)`, `@UseGuards`, `passport`, `JWT`
- 例："数据库" → `Neo4jClient`, `AsyncSession`, `LanceModel`, `Cypher`
- 例："状态管理" → `useStore`, `zustand`, `create(`, `set(`, `get(`

## 6. 代码模式模板
正则/结构化搜索模式。
- 例："API端点" → `@router.get`, `@app.post`, `@router.delete`
- 例："React组件" → `export default function`, `export const.*=.*=>`
- 例："Tauri命令" → `invoke(`, `#[tauri::command]`

## 7. 上下文信号
配置键、环境变量、错误码、注释标记。
- 例："认证" → `AUTH_SECRET`, `401`, `UNAUTHORIZED`, `@login_required`
- 例："性能" → `TODO:.*perf`, `FIXME:.*slow`, `@cache`, `TTL`
