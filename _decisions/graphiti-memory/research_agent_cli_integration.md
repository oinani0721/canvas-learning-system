---
name: Agent CLI 集成调研结论
description: Claude Code/OpenCode 嵌入 Obsidian 的可行性调研结果 — 推荐 Mode D MCP Server 暴露方案（2026-03-15）
type: project
---

Session：PRD Review | 背景：用户提出是否可用 Claude Code/OpenCode 作为对话系统核心引擎兜底

## 调研结论（3 个并行 Agent 调研）

### 社区现状
- 10+ 独立项目已将 Claude Code/OpenCode 嵌入 Obsidian 侧边栏
- Obsidian 1.12 CLI + Obsidian Skills 官方支持 Agent 集成（2026-02）
- Claudian（Claude Agent SDK 嵌入）是最成熟方案，版本 1.3.68
- Neo4j MCP Server 和 LanceDB MCP Server 已存在

### 技术可行性
- Claude Agent SDK TypeScript 可直接嵌入 Obsidian Plugin
- Session 管理映射 per-node 独立对话
- 流式输出支持自定义 UI
- 成本：Agent CLI 是直接 API 的 3-5 倍

### 架构推荐：Mode D（MCP Server 暴露）
- Mode A 完全替代：❌ FSRS/BKT 等确定性算法不能 Agent 化
- Mode B 兜底叠加：⚠️ 双重复杂度
- Mode C 混合拆分：⚠️ 边界维护成本高
- **Mode D MCP 暴露：✅ 推荐 — FastAPI 不变，新增 MCP 接口**

### 算法影响
- 🟢 Agent 增强（4/13）：自适应出题、ACP、检验白板递归、Edge 对话
- 🔴 Agent 会搞坏（5/13）：FSRS、BKT、五维向量、三角协作、十信号融合
- ⚪ 不受影响（4/13）：KG、多维模型、Graphiti、三温度计

### 行业验证
- 零教育系统用 Agent CLI 替代后端
- 行业共识："LLM 增强确定性算法，不替代后端"
- LECTOR(2025)、GenMentor(2025) 论文支持

**Why:** 用户担心自建 13 算法管道稳定性，希望强力 Agent 兜底
**How to apply:** 如果用户确认 Mode D，需更新 PRD 增加 MCP Server 层（Phase 2）
**决策状态：待用户确认**
