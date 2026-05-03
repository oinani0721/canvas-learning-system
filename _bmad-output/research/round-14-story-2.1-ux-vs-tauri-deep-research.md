---
type: deep-research-prompt
decision_id: epic-2/story-2.1-vs-tauri-ux-alignment
date: 2026-05-03
target: ChatGPT Deep Research (GitHub connector + web fetch)
worktree_branch: worktree-feature-obsidian-hybrid-dev
github_repo: https://github.com/oinani0721/canvas-learning-system
status: ready-to-send
---

# Round 14 · Deep Research · Story 2.1 UX 对齐 Tauri 原设计审查

> **目的**：评估 Canvas Learning System 从 Tauri v0 降级到 Obsidian Hybrid 后，**Story 2.1 "AI 对话 + 邻居上下文注入"** 在用户使用层面是否真正满足 Tauri 时代 PRD 的核心 UX 需求。
>
> **使用方法**：
> 1. 复制下方 ` ```deep-research-prompt ``` ` 整段
> 2. 粘贴到 ChatGPT Deep Research（Pro 模式 / Run deep research）
> 3. 等 ChatGPT 反馈 [Q1]/[Q2] 追问 或 [FINAL] 最终建议
> 4. 把 [FINAL] 结果回传给 Claude Code → Claude 输出 `[DECISION-TECH-FINAL]` + 归档 Graphiti

---

## 提示词正文（直接复制下方代码块）

```deep-research-prompt
# ChatGPT Deep Research 任务：Canvas Learning System Story 2.1 UX 审查

## 你的角色与任务

你是 **ChatGPT Deep Research**，需要审查 Canvas Learning System 项目的 **Story 2.1 "AI 对话 + 邻居上下文注入"** 在用户使用层面是否真正满足 Tauri v0 时代 PRD 的核心 UX 需求。

项目设计哲学：**"learning effect conservation"**（学习效果守恒，非 UI 1:1 还原）。

请优先 fetch 下方 GitHub 链接获取完整代码 + 文档上下文，然后做对比审查。

## 项目 GitHub 仓库

- **仓库**：https://github.com/oinani0721/canvas-learning-system
- **Default branch（GitHub connector 默认读这个）**：`main`
- **本次审查目标分支**：`worktree-feature-obsidian-hybrid-dev`（Obsidian 降级开发线，已 push 含 Story 2.1 完整实施）
- **可见性**：Public

⚠️ **重要**：如果你只能通过 GitHub connector 读 default branch（main），main 分支会含 Tauri 历史 + Obsidian 降级混合内容。请通过下方**直链 URL fetch**（带 `/tree/<branch>/path` 路径）来精确读取 worktree 分支的最新代码。

## 关键文件 GitHub 直链（请 fetch）

### 1. PRD v0（Tauri 原始设计需求 — 真相源 1）
https://github.com/oinani0721/canvas-learning-system/blob/main/_bmad-output/planning-artifacts/prd-v0-original-tauri.md

重点关注：
- FR-CONV-01（节点级对话触发，第 746 行附近）
- FR-CONV-03（1-hop 上下文自动注入，第 749 行）
- FR-CONV-04（Skill 命令调用，第 750 行）
- FR-CONV-10（跨节点 Edge 语义检索，第 755 行）
- FR-CONV-11（三层上下文窗口管理，第 756 + 311-315 行）
- FR-AGENT-02（Per-node 独立 Session，第 870 行）
- FR-TRACE-02（Tips 溯源，第 836 行）
- 视觉示例（第 433 行节点详情面板描述）

### 2. PRD 当前版（Obsidian Hybrid 重写版 — 真相源 2）
https://github.com/oinani0721/canvas-learning-system/blob/main/_bmad-output/planning-artifacts/prd.md

### 3. Story 2.1 完整 Spec（worktree 分支）
https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/epic-2/2-1-ai-dialog-context-injection.md

### 4. Story 2.1 验收单（用户视角的 UAT 文档）
https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/_bmad-output/%E9%AA%8C%E6%94%B6%E5%8D%95/Story-2.1-ai-dialog-context-injection.md

### 5. Backend 实施代码（4 个核心文件）
- wikilink_context_service.py（N-hop 邻居遍历 + 降级处理）：
  https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/backend/app/services/wikilink_context_service.py
- chat_context_assembler.py（5 优先级 token 预算 + 公式保护）：
  https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/backend/app/services/chat_context_assembler.py
- chat.py（FastAPI endpoint）：
  https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/backend/app/api/v1/endpoints/chat.py
- main.ts（Obsidian plugin handleChatWithContext）：
  https://github.com/oinani0721/canvas-learning-system/blob/worktree-feature-obsidian-hybrid-dev/frontend/obsidian-plugin/src/main.ts

### 6. Architecture 文档（架构约束）
https://github.com/oinani0721/canvas-learning-system/blob/main/_bmad-output/planning-artifacts/architecture.md

## 项目背景速读（避免你重新推断）

- **原架构 Tauri v0**（已 archived 到 archive/legacy-tauri-v0/）：React + ReactFlow + Rust backend，节点是 React 组件，**点击节点弹独立对话窗口**
- **现架构 Obsidian Hybrid**：Obsidian plugin（TS）+ Claudian sidebar（Claude Code CLI 内嵌）+ FastAPI backend
- 节点 = `节点/<concept>.md` markdown 文件（扁平池）
- 白板 = `原白板/<board>.md` markdown 文件
- 节点间关系 = wikilink（`[[X]]`）+ frontmatter `relationships[]`
- LLM = Mode D（architecture.md:113 锁定）：Claude Code CLI（用户订阅，Claudian sidebar 内执行 Skills），零 backend LLM 成本
- 降级原因：Tauri+React 工程复杂度过高 / Obsidian 复用社区生态降本
- **设计哲学**：用户学习效果守恒（Effect Conservation），不强求 UI 1:1，但学习闭环不能丢

## Tauri v0 原始 UX 需求（来自 PRD v0，逐条引用）

- **FR-CONV-01**：用户**点击任意节点**可以打开**该节点的独立 AI 对话窗口**（per-node 隔离，一键触发）
- **FR-CONV-03**：AI 对话时自动注入用户在该节点及其 **1-hop** 邻居节点的学习上下文（**Tips、错误记录、Edge 理由**等）
- **FR-CONV-04**：用户可以在对话中使用 `/命令` 调用已注册的 Agent 技能
- **FR-CONV-10**：用户切换到新节点对话时，系统通过 **Edge 语义检索**相关的**前序节点对话摘要**，自动注入新节点对话上下文（Phase 2）
- **FR-CONV-11**：**三层上下文窗口管理**：
  - Tier 1 全量注入（当前节点完整对话历史）
  - Tier 2 摘要注入（1-hop 邻居节点对话摘要）
  - Tier 3 按需检索（远端节点按需检索）
  - > 5 个邻居 → 按**查询相关性、交互时间、精通度缺口**优先排序，受 ACP token 预算约束
- **FR-AGENT-02**：Agent 对话支持 **per-node 独立 Session**（createSession / resumeSession），切换节点时**保持独立对话上下文**
- **FR-TRACE-02**：学习档案展示用户标注的所有 Tips，可**展开查看来源对话上下文**

### 视觉示例（PRD v0 line 433）
> 面板顶部通过颜色和描述性标签显示掌握状态（如"需要加强"/"基本掌握"），下方"建议复习 admissibility 相关内容"。面板上有"启动单节点考察"按钮，可对该节点直接发起专项考察。接着是他之前标注的 3 条 Tips —— 每条 Tips 都可以展开看当时的对话上下文。

## Obsidian Story 2.1 v1.0 实施现状（已 ship review 待 UAT）

### 触发流程

```
打开 节点/<concept>.md（必须先打开节点页）
  ↓
按 Cmd+Shift+E（用户在 Settings → Hotkeys 自绑）
  ↓
plugin 检查 active file 在 节点/ 路径
  ↓
plugin 收集 current_note (path + 正文 + frontmatter)
  ↓
POST /api/v1/chat/enrich-context（max_hops=2, token_budget=8192）
  ↓
backend wikilink_context_service.enrich_from_wikilink_graph
  → wikilink_graph_service.get_neighbors(node_path, hop=2) [NetworkX BFS, 200ms 超时]
  → NeighborNote × N → WikilinkNeighborContext（含 relationship_type 提取）
  ↓
backend chat_context_assembler.assemble_context（5 优先级填充 token 预算）
  → P1 当前笔记全文 / P2 1-hop frontmatter+Tips+errors / P3 1-hop content_summary
  → P4 2-hop frontmatter / P5 2-hop content_summary
  → tiktoken cl100k_base 计 token / 公式($$/$/```) atomic 块保护
  ↓
plugin 写剪贴板（prompt = /chat-with-context + enriched_context + "请基于以上上下文回答…"）
  + 切 Claudian sidebar
  ↓
用户 Cmd+V 粘贴 → Claudian 加载 chat-with-context Skill → Claude 给开场白 + 对话
```

### 5 AC 实施

- AC #1: 2-hop wikilink 遍历 ✅
- AC #2: frontmatter + Tips + errors 注入 ✅
- AC #3: token 预算压缩 + 公式/代码块 atomic 保护 ✅
- AC #4: 首 token < 5s（待用户实测）
- AC #5: 降级处理（graph_not_built / timeout / error → degraded=True + 通知）✅

### 测试覆盖
- backend 50 单元测试 / plugin 98 单元测试，全 green
- 集成 / 性能测试推迟到 Task 5.4

## 关键差异表（请评估每条是否"使用层面等价"）

| 维度 | Tauri v0 原设计 | Obsidian 实施 | 用户感知差异 |
|---|---|---|---|
| 触发 | **点击节点**（视觉一键）| **Cmd+Shift+E hotkey + 必须先打开节点页** | 步数 1 → 4 |
| 对话窗口 | 节点旁独立窗口（per-node） | Claudian sidebar（**全局共享**） | 视觉聚焦丢失？|
| 邻居 hop | **1-hop**（FR-CONV-03） | **2-hop**（升级）| 上下文更广 |
| 上下文窗口管理 | **三层 Tier 1/2/3** + 按"相关性/交互时间/精通度缺口"排序 | **5 优先级 token 预算** + 按"hop_distance + 字段类型"排序（**无相关性/时间/精通度排序**）| 邻居选择有偏？|
| Edge 语义检索前序对话（FR-CONV-10） | Phase 2 计划 | **未实施**（依赖 Story 2.6 对话归档 + Graphiti） | 推迟可接受？|
| Per-node 独立 Session（FR-AGENT-02） | createSession / resumeSession **持久化** | **每次 Cmd+Shift+E 重新组装 context**（不含 prior 对话历史） | 重大丢失？|
| Tips 溯源（FR-TRACE-02） | 学习档案点 Tips → 看对话原文 | **未实施** | 推迟可接受？|
| 节点视觉聚焦 | 节点旁面板（mastery 颜色 + Tips 列表 + 单节点考察按钮）| Obsidian frontmatter（mastery 字段）+ Cmd+P 命令面板 + Dashboard.md | 视觉散布认知负担？|
| 启动单节点考察 | 节点旁按钮（FR-EXAM-17） | Cmd+Shift+C/E 后再 Cmd+P → 考察命令 | 步数 1 → 3 |

## 待你验证的具体问题（核心 7 问）

1. **使用层面真等价吗？** Tauri "点击节点" vs Obsidian "Cmd+Shift+E + 必须打开节点页 + 剪贴板粘贴" — 这是否破坏了 PRD v0 的"learning effect conservation"原则？

2. **per-node Session 持久化丢失影响有多大？** Tauri 是 createSession/resumeSession 持久化对话历史（用户回到旧节点能 resume）；Obsidian 每次都是新对话（context 含静态 Tips/errors 但**不含 prior 对话历史**）。对**复习时回到旧节点连贯思考**的用户体验是否致命？

3. **三层 Tier vs 5 优先级**：FR-CONV-11 强调按"**查询相关性 / 交互时间 / 精通度缺口**"排序邻居，但 Story 2.1 实施按"hop_distance + 字段类型"排序。是否会导致 token 预算用在不重要邻居上？是否需要 v1.1 加排序逻辑？

4. **节点视觉聚焦丢失**：Tauri 节点旁有 mastery 颜色 / Tips 列表 / 单节点考察按钮 — Obsidian 这些散在 frontmatter / 命令面板 / Dashboard 内。用户**学习心流**是否被打断？是否需要 Obsidian plugin 加 sidebar widget？

5. **缺失的 FR**（FR-CONV-10 / FR-AGENT-02 / FR-TRACE-02）：是 OK 推迟到后续 Story（2.6 对话归档 / 3.7 dialog-pullout-node / 5.x Tips 溯源）？还是 Story 2.1 不应该被标 review until 这些至少有 stub？

6. **从 Tauri 学习者迁移到 Obsidian 的"学习效果守恒"实际度**：用户原来在 Tauri 一键点击就能进入"Eigenvalues 节点的对话 + 历史 + 邻居 + Tips 全景"，现在需要 "打开节点 + Cmd+Shift+E + 剪贴板 + Claudian + 粘贴 + 提问" 6 步操作。这种 UX 退化是否符合**学习效果守恒**？还是已经从"效果守恒"滑落到"功能阉割"？

7. **降级路径的可发现性**：Tauri 节点旁 mastery 颜色 / Tips 列表是**视觉触发**（看到 = 想要对话），Obsidian 这些信息要 Cmd+P 查 / Dashboard 看。**主动查找认知负担**是否过高？是否会导致用户**忘记使用** Tips（学习闭环断裂）？

## 已知约束（请勿建议这些方案）

- Obsidian 无法实现"点击节点弹独立窗口"（Obsidian 是 markdown 编辑器，节点 = .md 文件，无 React 节点的视觉概念）
- Per-node Session 持久化需要 Story 3.7 dialog-pullout-node 实施（未启动）
- Edge 语义检索需要 Story 2.6 对话归档 + Graphiti（未启动）
- Mode D 用 Claudian sidebar 共享 session 是 architecture.md:113 锁定的（用户订阅 Claude Code CLI，零 backend LLM 成本，不可改）
- 不可改用 Tauri / Electron / 自建 React UI

## 应答格式

### 如果信息充分 → 直接 [FINAL]：
```
[FINAL]

## 最终判断
（"使用层面等价" / "部分等价 + N 处需补强" / "已实质偏离 PRD v0"）

## 关键依据
- 学术证据（如 Karpicke 2011 Retrieval Practice / 学习心流文献 / 任务步数 vs 学习效率研究）
- 行业证据（如 Aider/Cursor/OpenCode 上下文管理对照 / Anki / Obsidian 学习者社区案例）
- Tauri PRD v0 vs Obsidian Story 2.1 的具体逐条对比

## Story 2.1 处置建议
- 应继续 review 通过 / 回炉重做 / 加 stub 后通过
- 哪些 FR（10/11/AGENT-02/TRACE-02）必须在 Epic 2 完成前补 stub
- 是否需要 Story 2.1 v1.1（加邻居优先级排序 + sidebar widget）

## 实施注意事项
- 具体 1-3 个执行建议（不超过 3 句话）

## 与项目约束兼容性
- 你的建议是否符合"不改 Mode D / 不引入 Tauri" 等约束
```

### 如果信息不足 → 用 [Q1]/[Q2] 反提问：
```
[Q1] 你的具体追问
[Q2] 你的具体追问
```

或 `[Q-USER]` 直问用户（如"团队对 4 步 vs 1 步触发的容忍度"）。

## 双向通信协议

- 我（项目作者）会通过 Claude Code 接力你的回复
- 如果你给 [Q1]/[Q2]，我会用 [A1]/[A2] 回答 + 给新的上下文块
- 如果你给 [FINAL]，我会归档到 Graphiti 并相应调整 Story 2.1 实施
- 预期总往返：1-3 轮

## 项目约束（你的回复必须遵守）

- 不要建议"改用 Tauri / Electron / 自建 React UI"（已 archived，不可逆）
- 不要建议"切换 LLM provider"（Mode D 锁定）
- 不要建议"重构整个开发流程"（OpenSpec / BMAD 是项目流程基石）
- 聚焦：**Story 2.1 的 UX 实施 vs Tauri PRD v0 的对齐度**，给具体补强建议
```

---

## 复制到 ChatGPT 后的预期流程

1. **第 1 轮**：ChatGPT fetch 上述 GitHub URL → 阅读 Tauri PRD v0 + Story 2.1 spec/验收单/代码 → 给 [FINAL] 或 [Q1]/[Q2] 追问
2. **第 2 轮**（如有 [Q]）：你把 ChatGPT 追问粘贴回 Claude Code，Claude 给 [A1]/[A2] + 新上下文块
3. **第 3 轮**（最终）：ChatGPT 给 [FINAL]，你粘贴回 Claude Code，Claude 输出 `[DECISION-TECH-FINAL:epic-2/story-2.1-vs-tauri-ux-alignment]` + 归档到 Graphiti

## 文档状态

- **创建时间**：2026-05-03
- **决策 ID**：epic-2/story-2.1-vs-tauri-ux-alignment
- **status**：ready-to-send（提示词已准备好，等待用户复制到 ChatGPT Deep Research）
- **预期归档**：完成后 → Graphiti `canvas-dev` group + 决策内容写回此文档"## 最终决定" section
