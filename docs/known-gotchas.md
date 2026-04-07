# Known Gotchas — Canvas Learning System

> **Session 启动时自动注入。`/parallel-fix` 运行后自动更新。**
> Last updated: 2026-03-29 (S35: 11待修→2待修，8项审计确认已修复/误报/归档)

---

## G-FAKE: 假命名/假实现 (DD-03, DD-13)

| ID | 问题 | 根因 | 修复状态 | 防止规则 |
|----|------|------|---------|---------|
| G-FAKE-001 | ~~42+函数名含"graphiti"但从未 import graphiti-core~~ | ~~AI 混淆：写入 Neo4j ≠ 写入 Graphiti~~ | ✅ S34批量重命名：核心类(GraphitiEdgeClient→Neo4jEdgeClient等17项)、文件(graphiti_client.py→neo4j_edge_client.py等3个)、Service函数5个。32 real tests全通过。残留：API模型名+config属性（API兼容性保留） | DD-13 name-body-coherence.js 自动检测 |
| G-FAKE-002 | ~~3个函数调用不存在的方法（死代码调用链）~~ | ~~未验证调用链完整性~~ | ✅ S35审计确认：所有方法存在于GraphitiTemporalClient（search_verification_questions/add_edge_relationship/add_episode_for_edge/search_nodes）。commit 1768c19已清理原死代码 | DD-13 Certificate-Based Review |
| G-FAKE-003 | ~~Memory query API 端点全部返回空数据~~ | ~~占位实现从未被替换~~ | ✅ S33诊断纠正：7个memory端点均为真实实现，DI正确接线。返回空是因为Neo4j无数据（正确行为） | DD-03 |
| G-FAKE-004 | ~~Agent API 端点大量使用硬编码假数据~~ | ~~原型阶段占位未清理~~ | ✅ S35审计确认：全部13个agent端点调用真实服务（GeminiClient/Neo4j/RAG），无硬编码假数据。原S18审查时的占位已在后续Story中替换 | DD-03 |
| G-FAKE-005 | ~~Frontend /explain/four-level 等端点使用假实现~~ | ~~前后端分离时占位~~ | ✅ S35审计确认：后端6个explain端点全部接入真实LLM（agent_service.generate_explanation），前端为API wrapper。Story 21.1已完成集成 | DD-03 |

## G-PIPE: 管道断裂 (DD-11)

| ID | 问题 | 根因 | 修复状态 | 防止规则 |
|----|------|------|---------|---------|
| G-PIPE-001 | ~~FSRS 权重计算器已实现但无调用方~~ | ~~Phase 3 构建组件但未接线~~ | ✅ S34审计纠正：review_service.py:620 targeted 模式已调用 WeightCalculator.calculate_weakness_scores() | DD-11 |
| G-PIPE-002 | BehaviorTracker 完整实现但从未被调用 | 实现完整但无调用方 | ⚠️ S35审计：331行完整实现(src/memory/temporal/behavior_tracker.py)，TemporalMemory实例化但无调用。保留为future feature | DD-11 |
| G-PIPE-003 | ~~Graphiti Bridge 已实现但未接入学习记忆管道~~ | ~~Phase 3 构建组件但未接线~~ | ✅ S35审计确认：Phase2分布式集成已完成。memory_service.record_knowledge_entity+verification_service:717回写+review_service:1435查询。非单一Bridge类而是跨3个service的集成 | DD-11 |
| G-PIPE-004 | Phase 3 Agent Graph 完整实现但被禁用 | ENABLE_AGENT_GRAPH=false | ⚠️ S35审计：有意禁用（设计决策）。agent_graph.py 660行LangGraph完整实现，agent_service条件启用。非bug，待生产验证后启用 | DD-11 |
| G-PIPE-005 | ~~Strategy Selector 完整映射但无人调用~~ | ~~Phase 3 构建组件但未接线~~ | ✅ S35审计确认：代码已归档至_bmad-output/archive/fusion/strategy_selector.py，不在生产路径。当前fusion策略内联于retrieval service | DD-11 |
| G-PIPE-006 | ~~Verification 系统与 Retrieval 系统信息断层~~ | ~~两套系统独立开发~~ | ✅ S34修复(1f19e00)：verification_service:717调record_knowledge_entity回写exam_attempt到Neo4j，闭合反馈环 | DD-11 |
| G-PIPE-007 | S18-4 发现: progressive_scope_search/expand_neighbors 为死代码 | 并行开发文件隔离导致跨文件接线遗漏 | ✅ 已修复 | DD-11 并行Agent接线检查 |

## G-TYPE: 类型不匹配

| ID | 问题 | 根因 | 修复状态 | 防止规则 |
|----|------|------|---------|---------|
| G-TYPE-001 | 前端评分 scale mismatch: ×2.5 导致溢出 | 前后端评分范围不一致 | ✅ S27-GDA-8 确认修复 | Phase1 立即修 |
| G-TYPE-002 | 后端 1分变100分 | 评分转换逻辑错误 | ✅ S27-GDA-8 确认修复 | 同上 |

## G-ASYNC: 异步/竞态

| ID | 问题 | 根因 | 修复状态 | 防止规则 |
|----|------|------|---------|---------|
| G-ASYNC-001 | Story 2-7: TOCTOU 竞态条件 | 文件检查和操作之间存在时间窗口 | ✅ BMAD审查修复 | 原子操作替代检查-操作模式 |
| G-ASYNC-002 | Dexie silent catch ×5 | 前端 IndexedDB 操作静默吞错 | ✅ S18审查修复 | 显式错误处理 |

## G-API: API合同违规

| ID | 问题 | 根因 | 修复状态 | 防止规则 |
|----|------|------|---------|---------|
| G-API-001 | fastapi-mcp anyOf+type schema 冲突 | MCP 工具 schema 生成不兼容 | ✅ S29 monkey-patch修复 | 自定义 schema 后处理 |
| G-API-002 | MCP route 缺少 explicit operation_id 导致工具名错误 | FastAPI 自动生成的 operation_id 不稳定 | ✅ S29 15路由全部修复 | 每个路由显式设置 operation_id |

## G-SILENT: 静默失败 (S33新增)

| ID | 问题 | 根因 | 修复状态 | 防止规则 |
|----|------|------|---------|---------|
| G-SILENT-001 | Review Schedule 在 scheduler 不可用时静默返回 200+空数据 | review_service mastery enrichment 失败时无信号 | 🟡 部分修复 (2026-04-06, OpenSpec: review-enrichment-signal-fix): schemas.py:WeightConfig 已加 enrichment_available 字段 + 4 个 schema 单测护栏 (test_review_enrichment_signal.py)。⚠️ **endpoint wiring 是独立 follow-up**: app/api/v1/endpoints/review.py:788 generate_verification_canvas 是独立内联实现，不调用 review_service.generate_verification_canvas（service 方法实质是 G-FAKE 死代码，生产路径零 caller，仅 tests/unit/test_review_mode_support.py 引用）。前端要真正收到 enrichment_available 信号，需要后续将 endpoint 接到 service 或在 endpoint 内联 enrichment 逻辑。 | API 应返回 degraded 标记 |
| G-SILENT-002 | ~~Cross-Canvas Search 硬编码返回空列表~~ | ~~cross_canvas.py:557 placeholder~~ | ✅ S35审计确认：cross_canvas_service.py已完整实现（get_associated_canvases/get_lecture_for_exercise/list_associations），原gotchas行号引用过期 | DD-03 |

## G-PARAM: 参数/类型 Bug (S33 real-DB 测试暴露，已修复)

| ID | 问题 | 根因 | 修复状态 | 防止规则 |
|----|------|------|---------|---------|
| G-PARAM-001 | search_nodes() query 参数名冲突+双WHERE | graphiti_client.py params["query"] 与 run_query(query) 冲突 | ✅ S33修复：$query→$searchTerm + WHERE合并 | real DB 测试 |
| G-PARAM-002 | MemoryService DateTime vs str 排序 TypeError | Neo4j 返回 DateTime 对象，in-memory 用 ISO string | ✅ S33修复：sort key 用 str() 统一 | real DB 测试 |
| G-PARAM-003 | conftest neo4j_test_session cleanup TypeError | 位置参数 dict 传给 **kwargs | ✅ S33修复：改为 keyword arg | real DB 测试 |

## G-PERF: 性能问题

| ID | 问题 | 根因 | 修复状态 | 防止规则 |
|----|------|------|---------|---------|
| G-PERF-001 | Story 2-7: 全文件 hash 读取 | 大文件完整读取计算 hash | ✅ BMAD审查修复 | 增量/分块读取 |
| G-PERF-002 | Windows IPC 10MB = 200ms vs macOS 5ms | Tauri IPC 在 Windows 上严重劣化 | ⚠️ GDR-P1-4 约束 | 单次 IPC <100KB + delta 更新 |

---

## 统计摘要

| 分类 | 总计 | 已修复 | 有意保留/延后 | 待修复 |
|------|------|--------|-------------|--------|
| G-FAKE | 5 | 5 | 0 | 0 |
| G-PIPE | 7 | 5 | 2 (002 future feature, 004 有意禁用) | 0 |
| G-TYPE | 2 | 2 | 0 | 0 |
| G-ASYNC | 2 | 2 | 0 | 0 |
| G-API | 2 | 2 | 0 | 0 |
| G-PERF | 2 | 1 | 1 (002 Phase4 约束) | 0 |
| G-SILENT | 2 | 1 | 0 | 1 (001 S35修复中) |
| G-PARAM | 3 | 3 | 0 | 0 |
| **合计** | **25** | **21** | **3** | **1** |
