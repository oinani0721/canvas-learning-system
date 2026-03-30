---
name: S4 Brainstorming 关键发现
description: S4 Config统一+StateGraph整理 brainstorming session的核心决策和社区调研发现
type: project
---

## Phase 2 Five Whys 核心结论（2026-03-12）

1. **"统一"这个词用错了** — api.config和CanvasRAGConfig字段零交集，不应合并，应保留两层+统一管理策略
2. **根因是访问模式** — _safe_get_config静默回退掩盖了config断裂，不是结构问题
3. **S4拆分为S4a+S4b** — S4a(Config清理,低风险)可先做，S4b(State/Graph整理)依赖Phase3方向
4. **env_config是死代码** — 从未被import，应直接删除

## 社区调研关键发现

1. **LangGraph v0.6.0+ Context API** — `config["configurable"]` 将废弃，迁移到 `Runtime[ContextSchema]`。当前代码用旧模式。S4应同时迁移。
2. **ContextSchema用dataclass** — LangGraph官方推荐State用TypedDict、Context用dataclass（支持默认值）。解决_safe_get_config问题。
3. **Pydantic-settings v2** — 支持嵌套模型+env_nested_delimiter，服务层config可用此管理。
4. **十二因素** — DEFAULT_CONFIG硬编码违反原则，应改为环境变量+dataclass默认值。

## Config三层分离架构

- Layer 1: ServiceConfig (Pydantic BaseSettings) — 端口/CORS/日志，启动时加载
- Layer 2: RAGContextSchema (dataclass) — 策略/参数，per-request可override，LangGraph Runtime注入
- Layer 3: Secrets — 环境变量直接读，不持久化为config对象

## ⛔ 代码对抗性审查——毁灭性发现（2026-03-12）

**最关键发现：config传递在生产环境中完全断裂。**

`agentic_rag_adapter.py:195` 用 `config={"configurable": config}` 传递config，但 LangGraph 的 `context_schema` 期望 `context=config`（扁平dict）。结果：**生产环境中所有10个 `_safe_get_config` 调用全部命中硬编码默认值**。config系统给出"可配置"的假象但完全无效。

### 各文件评级
- config.py: **需修复** — ghost field (weak_concepts_limit)、TypedDict无运行时校验、total=False使所有字段可选
- env_config.py: **死代码** — 零import、embedding模型与实际不兼容
- api/config.py: **可用** — 但与RAG config完全隔离
- state.py: **需修复** — 节点写入的字段(weak_concepts等)在schema中不存在=数据丢失、无默认值
- agentic_rag_adapter.py: **需修复(Critical)** — config传递broken、fallback是stub返回[]、性能统计mock

### _safe_get_config 统计
- 10个调用点、1个ghost field (weak_concepts_limit不在schema中)
- 生产环境中：10/10 全部命中默认值（config从未到达node）

## 待完成

- Phase 3 Morphological Analysis待执行
- Graphiti记录待补录（MCP暂时不可用）
