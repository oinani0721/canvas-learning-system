# Known Gotchas — Canvas Learning System

> **Session 启动时自动注入。`/parallel-fix` 运行后自动更新。**
> Last updated: 2026-03-27

---

## G-FAKE: 假命名/假实现 (DD-03, DD-13)

| ID | 问题 | 根因 | 修复状态 | 防止规则 |
|----|------|------|---------|---------|
| G-FAKE-001 | 42+函数名含"graphiti"但从未 import graphiti-core，实际调用 Neo4j Cypher | AI 混淆：写入 Neo4j ≠ 写入 Graphiti | ⛔ GDA-S24审计发现，12C+13H | DD-13 name-body-coherence.js 自动检测 |
| G-FAKE-002 | 3个函数调用不存在的方法（死代码调用链） | 未验证调用链完整性 | ⛔ 需修复 | DD-13 Certificate-Based Review |
| G-FAKE-003 | Memory query API 端点全部返回空数据 | 占位实现从未被替换 | ⛔ 需真实查询 Neo4j/LanceDB | DD-03 pretool-guard.js 阻断空返回 |
| G-FAKE-004 | Agent API 端点大量使用硬编码假数据 | 原型阶段占位未清理 | ⛔ S18审查发现 | DD-03 |
| G-FAKE-005 | Frontend /explain/four-level 等端点使用假实现 | 前后端分离时占位 | ⛔ 需接入真实 LLM | DD-03 |

## G-PIPE: 管道断裂 (DD-11)

| ID | 问题 | 根因 | 修复状态 | 防止规则 |
|----|------|------|---------|---------|
| G-PIPE-001 | FSRS 权重计算器已实现但无调用方 | Phase 3 构建组件但未接线 | ⛔ 需接入评分管道 | DD-11 新函数必须有调用方 |
| G-PIPE-002 | BehaviorTracker 完整实现但从未被调用 | 同上 | ⛔ 需接入 | DD-11 |
| G-PIPE-003 | Graphiti Bridge 已实现但未接入学习记忆管道 | 同上 | ⛔ Phase2 已部分接入 | DD-11 |
| G-PIPE-004 | Phase 3 Agent Graph 完整实现但被禁用 | 开发完成后未激活 | ⛔ 需评估是否启用 | DD-11 |
| G-PIPE-005 | Strategy Selector 完整映射但无人调用 | 同上 | ⛔ 需接入路由层 | DD-11 |
| G-PIPE-006 | Verification 系统与 Retrieval 系统信息断层 | 两套系统独立开发 | ⛔ 需接口对齐 | DD-11 |
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

## G-PERF: 性能问题

| ID | 问题 | 根因 | 修复状态 | 防止规则 |
|----|------|------|---------|---------|
| G-PERF-001 | Story 2-7: 全文件 hash 读取 | 大文件完整读取计算 hash | ✅ BMAD审查修复 | 增量/分块读取 |
| G-PERF-002 | Windows IPC 10MB = 200ms vs macOS 5ms | Tauri IPC 在 Windows 上严重劣化 | ⚠️ GDR-P1-4 约束 | 单次 IPC <100KB + delta 更新 |

---

## 统计摘要

| 分类 | 总计 | 已修复 | 待修复 |
|------|------|--------|--------|
| G-FAKE | 5 | 0 | 5 |
| G-PIPE | 7 | 1 | 6 |
| G-TYPE | 2 | 2 | 0 |
| G-ASYNC | 2 | 2 | 0 |
| G-API | 2 | 2 | 0 |
| G-PERF | 2 | 1 | 1 |
| **合计** | **20** | **8** | **12** |
