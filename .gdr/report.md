# GDR 调研全景报告：前端工具调用 UI + 可观测性闭环

**研究主题**: 前端工具调用UI + 可观测性闭环（参考 Claudian/Claude Code）
**执行 Agent 数**: 16（Wave1×4 + Wave2×10 + Wave3×2）
**Graphiti MCP**: graphiti-canvas | Group ID: canvas-dev
**日期**: 2026-03-24

---

## 核心决策状态

| 决策 | 原状态 | 新状态 | 依据 |
|------|--------|--------|------|
| GDR-P0-1 事件传输 | 无决策(FR-AGENT-01系统性遗漏) | ✅ sidecar→Tauri Channel→React | Solo IDE同架构生产验证 |
| GDR-P0-2 工具调用UI | 无决策 | ✅ Claudian 4态状态机 | 10竞品对标+Claudian源码验证 |
| GDR-P0-3 Observer触发 | prompt-based(触发率低) | ✅ PostToolUse hook-based | 社区共识+hook触发率≈100% |
| GDR-P0-4 安全修复 | graphiti-core>=0.6.0(漏洞) | ✅ >=0.28.2 + effort:high | CVE-2026-32247 + SDK #214 |
| Agent SDK sidecar | ACTIVE | 验证(18限制识别) | W2-H发现2 CRITICAL+7 HIGH |
| stream-json事件驱动 | ACTIVE | 验证+修正假设 | W2-F证实CLI有完整tool事件 |
| fire-and-forget | 需升级 | → fire-and-track Outbox | 社区+学术双重共识 |

---

## 冲突发现（共 4 个）

| # | 冲突 | 解决方案 |
|---|------|---------|
| C1 | Windows IPC 200ms延迟 | 用Tauri Channel(非Event)，小JSON事件无影响 |
| C2 | 5型weakness分类不MECE | 后续从Bloom+CDM重新推导(P1-2) |
| C3 | SDK 12s冷启动 | 应用启动时预热+心跳保活(P1-3) |
| C4 | Windows child.kill()不可靠 | Rust侧进程组杀死+stdin关闭检测(P2-4) |

## 新发现（共 16 个，关键 6 项）

| # | 发现 | 来源 | 影响 |
|---|------|------|------|
| N1 | 学习注解：工具调用附带"为什么调用" | W2-G竞品(无竞品做)+W2-E AgentTrace | 唯一差异化 |
| N2 | BEA 2025四维度Observer提取模板 | W2-D Survey | 结构化>自由文本 |
| N3 | LLM摘要显著提升可观测性UX | W2-D(实证) | 折叠卡片用LLM生成摘要 |
| N4 | 小模型LoRA可超大模型做误解检测 | W2-E GRR论文 | Observer可用Ollama本地模型 |
| N5 | pendingTools Map批量渲染 | W2-I Claudian源码 | 多工具调用减少DOM抖动 |
| N6 | Graphiti双时态+Outbox天然协同 | W2-D+W2-C | 迟到事件通过ingestion-time处理 |

## 过期预警（共 3 个）

| # | 项目 | 问题 | 紧急度 |
|---|------|------|--------|
| 1 | graphiti-core | CVE-2026-32247 Cypher注入 | 🔴 立即 |
| 2 | Agent SDK | effort:medium静默注入 | 🔴 立即 |
| 3 | fire-and-forget | Observer数据丢失风险 | 🟡 P1 |

---

## 推荐架构（用户已确认）

```
用户交互 (React + shadcn/ui)
    ↓ 聊天消息
Tauri Shell → spawn Node.js sidecar
    ↓ Agent SDK query() async generator
Node.js sidecar 解析 SDKMessage (21种类型)
    ↓ Tauri Channel (NDJSON事件)
React 前端接收事件:
    ├─ text → ChatRenderer (markdown流式渲染)
    ├─ tool_use → ToolCallRenderer (4态: pending→running→completed/error/blocked)
    │   ├─ PreToolUse hook → 权限检查 (allow/deny/ask)
    │   ├─ 10+ 工具专属渲染器 (Bash/Read/Write/Edit/Grep/WebSearch等)
    │   ├─ 折叠块 (Companion模式 + LLM摘要)
    │   └─ 学习注解 ("为什么调用" — 唯一差异化)
    ├─ tool_result → PostToolUse hook → Observer 触发
    │   ├─ BEA 4维度提取 (识别/定位/指导/可操作)
    │   ├─ 原子学习事件 (A-MEM风格)
    │   └─ fire-and-track: SQLite WAL → 异步 Graphiti 写入
    └─ error/rate_limit → 状态指示器

可观测性层 (OTel GenAI spans):
    ├─ Operational: 工具调用计时、成功/失败
    ├─ Cognitive: 为什么agent选择这个工具 (AgentTrace)
    └─ Contextual: 当前学习状态、掌握度
```

## 关键参考项目

| 优先级 | 项目 | Stars | 参考价值 |
|--------|------|-------|---------|
| 1 | Claudian | 5k | Agent SDK wrapper + message transform + hooks 最完整参考 |
| 2 | opcode | 21k | Tauri 2 + React 架构直接对标 |
| 3 | assistant-ui | 9k | ToolGroup/ToolFallback/Collapsible 组件直接可用 |
| 4 | Vercel AI SDK | 23k | 三态状态机模型 + message.parts 渲染模式 |
| 5 | Cline | 59k | Stream→Task→Executor→View 分层架构 |
| 6 | AG-UI Protocol | 13k | 事件类型定义参考 |

## 关键论文

| 论文 | 影响 |
|------|------|
| AgentTrace (2602.10133) | 三层日志架构 → Observer write 设计 |
| XAgen (2512.17896) | 工具调用UI参考 → 日志可视化+反馈闭环 |
| Misconception GRR (2602.02414) | 误解检测管道 → Observer 提取方法 |
| Visibility into AI Agents (2401.13138) | 工具调用UI框架 → identifier+monitoring+logging |

## 下一步行动

### 立即执行
- [ ] graphiti-core 升级 >=0.28.2 (CVE修复)
- [ ] Agent SDK sidecar.js 添加 effort:"high"
- [ ] Commit + Push

### 下一个 Session
- [ ] DD-05: Pencil 创建工具调用UI范式（折叠块+4态状态机+权限确认）
- [ ] 参考 Claudian ToolCallRenderer + assistant-ui ToolGroup 实现前端组件
- [ ] PostToolUse hook 注册 Observer 触发逻辑
- [ ] Outbox WAL 写入管道搭建

### 后续 P1/P2
- [ ] P1-1 学习注解（工具调用附带"为什么"）
- [ ] P1-3 SDK冷启动预热策略
- [ ] P1-5 Agent SDK effort:high 一行修复
- [ ] P2-1 OTel GenAI 集成
- [ ] P2-4 Windows进程组杀死
