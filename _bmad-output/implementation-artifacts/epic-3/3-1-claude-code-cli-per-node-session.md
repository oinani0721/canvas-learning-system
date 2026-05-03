---
story_id: "3.1"
epic_id: "3"
prd_id: "canvas-learning-system"
status: "in-progress"
priority: "P1"
estimate_hours: 12
depends_on: ["1.16","1.17","1.19"]
blocks: ["3.2","3.3","3.4"]
trace: ["FR-CONV-01","FR-CONV-02","FR-AGENT-01","FR-AGENT-02"]
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
revision: "v1.0-hybrid-claudian-mode-d-2026-05-02"
uat_sheet: "_bmad-output/验收单/Story-3.1-claude-code-cli-per-node-session.md"
unblocked_by: "1.18 v1.2 已 done (2026-05-02) — 4 MVP 闭环达成"
---

# Story 3.1: 节点 AI 对话 v1（Plugin Cmd+Shift+C → Claudian + 自动注入节点上下文）

**Epic**: 3 — 节点 AI 对话与交互
**Status**: in-progress（路线 A · 节点级 AI 对话原型 / 路线 B 后端基础先行 推迟）
**Plan**: EPIC1-BMAD-DEV-ASSESS-2026-04-17
**Priority**: P1
**Estimate**: ~12h（plugin 命令 + context 收集 + clipboard + Claudian Skill 占位）
**Dependency**: Story 1.16 + 1.17 + 1.19 全 done（4 MVP 闭环达成 2026-05-02）；Claudian 插件已装；Claude Code 订阅已登录

---

## Story

作为 学习者，
我想 在 `节点/<concept>.md` 里按 `Cmd+Shift+C`，plugin 自动收集本节点的上下文（frontmatter + 选中文 + 1-hop wikilink 邻居）写入剪贴板并切到 Claudian sidebar，我粘贴后由 `/node-chat` Skill 加载完整学习背景驱动一段连贯对话，
以便 我在节点页内即可与 AI 围绕该节点进行学习对话，无需反复粘贴 / 切窗口 / 重复说明背景。

> **架构对齐（硬约束）**：完全复用 Story 1.17 v3.0 已验证的 **Hybrid 模式（plugin clipboard → Claudian sidebar → Skill 接管）**。Plugin 仅做 deterministic 工作（context 收集 + clipboard write + Claudian invoke），LLM 由 Mode D Claude Code CLI 在 Claudian session 内承担。
>
> **来源对齐**：Story 1.17 main.ts:822 `handleAILinkedDoc` 范式 + Story 1.19 v4.1 modal 链路 + planning-artifacts/architecture.md:113 Mode D 锁定 + 用户 2026-05-02 plan 推荐"路线 A 跳过 1.2 后端 wikilink graph，先用 Claudian 现成对话能力让用户 2 周内见到 AI 价值"。

## Behavior（用户视角）

```
打开 节点/Eigenvalues.md
     ↓ (按 Cmd+Shift+C — 用户在 Obsidian Settings 自绑到 canvas:open-node-chat)
     ↓
Plugin 检查 active file 是否在 节点/ 路径
     ├─ 不在 → Notice "请先打开 节点/<concept>.md 节点页再启动对话" 退出
     └─ 在 → 进入 context 收集
              ↓
Plugin 收集 4 类上下文：
  1. 节点 frontmatter — type / source_board / mastery_score / relationships[]
  2. 节点正文 — 完整 md body
  3. 选中文（可选）— editor.getSelection()，如有则作为重点关注段
  4. 1-hop wikilink 邻居 — app.metadataCache.resolvedLinks[节点路径] 取
     前 5 个邻居，每个邻居拉 frontmatter.type 和首段 100 字摘要
              ↓
Plugin 组装 prompt 写剪贴板 (~3-8KB):
  /node-chat
  
  ## 当前节点
  路径: 节点/Eigenvalues.md
  关系类型: refines（来自 [[原白板/线性代数]]）
  Mastery: 0.30 🔴
  
  ## 节点正文
  <full md body>
  
  ## 选中文（如有）
  <selected text>
  
  ## 1-hop 邻居（5 个 wikilink 关联节点摘要）
  - [[节点/Linear-Independence]] (concept) — 线性独立性是...
  - [[原白板/线性代数]] (whiteboard) — 本节点所属源白板
  - ...
  
  ## 任务
  围绕本节点进行学习对话。我可能问的方向：
  - 概念定义 / 直觉解释
  - 与邻居节点的关系
  - 具体例子 / 反例
  - 自测题
              ↓
Plugin: Notice "已复制节点 'Eigenvalues' 上下文（4.2KB / 5 邻居）到剪贴板"
        + 调 app.commands.executeCommandById("claudian:open-view")
              ↓
用户 Cmd+V 粘贴 → Claudian 加载 /node-chat Skill (canvas-vault/.claude/skills/node-chat/SKILL.md)
              ↓
Claude Code (Mode D 订阅) 开始对话
              ↓
（用户问问题 → 回答 → 追问 → 继续...）
```

零额外 API Key 配置，零独立付费，完全复用 Mode D + Story 1.17 已验证的 Hybrid 范式。

---

## Acceptance Criteria

### AC #1: Plugin 第 12 命令注册
- [ ] 命令 `canvas:open-node-chat` 注册在 Obsidian 命令面板
- [ ] 中文名: "节点对话（注入上下文 + 切 Claudian）"
- [ ] Settings → Hotkeys 搜 "Canvas" 看到 12 条（1.16-1.19 的 11 条 + 本条）
- [ ] 默认 `hotkeys: []`（用户自绑；建议 `Cmd+Shift+C`）

### AC #2: 节点路径检查 + active file 校验
- [ ] active file 是 null → Notice "请先打开 节点/<concept>.md 节点页"（3 秒）
- [ ] active file 存在但 path 不以 "节点/" 起头 → Notice "对话仅在 节点/ 下的概念页可用（当前 path: <X>）"（5 秒）
- [ ] 双重防护后不进入 context 收集 / clipboard / Claudian 切换

### AC #3: Context 收集（4 类）
- [ ] frontmatter：从 `metadataCache.getFileCache(activeFile).frontmatter` 读 `type / source_board / mastery_score / relationships`（缺字段 → 填空字符串或省略字段）
- [ ] body：`vault.read(activeFile)` 读完整 md，剥掉 frontmatter（YAML 块）后保留正文
- [ ] selection：`editor.getSelection()`，空则 prompt 中省略 "## 选中文" section
- [ ] 邻居：`metadataCache.resolvedLinks[activeFile.path]` 取 keys 列表，前 5 个为邻居路径；每个邻居读 frontmatter.type + 首 100 字摘要

### AC #4: Prompt 组装 + 剪贴板写入（< 10KB）
- [ ] 模板（中文 + Markdown）按 Behavior 段所示组装
- [ ] 总大小 ≤ 10KB（>10KB → 截断节点正文 / 邻居摘要至前 50 字 + Notice "节点过大，已截断"）
- [ ] `navigator.clipboard.writeText(prompt)` 失败 → Notice + 重试按钮（复用 1.17 v2.2 showRetryNotice 模式）

### AC #5: 触发 Claudian sidebar
- [ ] 调 `app.commands.executeCommandById("claudian:open-view")` 打开 Claudian
- [ ] Notice: "已复制节点 '<basename>' 上下文（<KB>KB / <N> 邻居）到剪贴板"（5 秒）
- [ ] Claudian 未装（`findCommand` null）→ Notice "未检测到 Claudian 插件，请先安装"（5 秒）
- [ ] Plugin 侧流程在此结束

### AC #6: Skill 文件存在 + 可发现
- [ ] `canvas-vault/.claude/skills/node-chat/SKILL.md` 存在
- [ ] Frontmatter: `name: node-chat` + `description`（"节点 AI 对话 — 从剪贴板加载节点上下文进入连贯对话"）
- [ ] Skill body 指令：从最近消息解析 prompt → 用节点上下文 + 邻居摘要做对话起点 → 不创建任何文件（纯对话，区别于 ai-linked-doc）

### AC #7: 边界 — 节点无 wikilink 邻居
- [ ] `resolvedLinks` 为空 / 节点孤立 → "## 1-hop 邻居" section 写"（无关联节点 — 这是孤立概念）"
- [ ] 不抛异常，对话仍能正常启动

### AC #8: UAT 端到端
- [ ] 用户在 `节点/Fundamentals.md` 按 Cmd+Shift+C → 见 Notice "已复制 ... 到剪贴板"
- [ ] Claudian sidebar 自动打开
- [ ] Cmd+V 粘贴 → 见 Claudian 识别 /node-chat 加载 Skill
- [ ] 用户问"什么是特征值的几何意义？"→ Claude 用节点上下文 + 邻居关系作答（不重复要求用户提供背景）

---

## Tasks

### Task 1: Plugin main.ts 加 canvas:open-node-chat 命令
- [ ] `registerCanvasCommands()` 加第 12 条 `addCommand({ id: "canvas:open-node-chat", name: "节点对话（注入上下文 + 切 Claudian）", callback: () => this.handleOpenNodeChat() })`
- [ ] 新方法 `handleOpenNodeChat()` — active file 检查（AC #2）+ context 收集（AC #3）+ prompt 组装（AC #4）+ Claudian invoke（AC #5）
- [ ] 复用 1.17 `showRetryNotice` 处理剪贴板失败

### Task 2: Context 收集函数（独立模块 src/node-chat-context.ts）
- [ ] `collectNodeContext(app, file, editor)` 返回 `{ frontmatter, body, selection?, neighbors[] }`
- [ ] `frontmatterFromCache(app, file)` — 取 `type / source_board / mastery_score / relationships`
- [ ] `extractBodyWithoutFrontmatter(content)` — 剥 YAML 块返回正文
- [ ] `collectNeighbors(app, file, max=5)` — 读 `resolvedLinks` 取前 N 个，每个拉 type + 首 100 字摘要

### Task 3: Prompt 组装 + 大小校验
- [ ] `buildNodeChatPrompt(context, options={maxBytes: 10240})` — 模板拼接
- [ ] 超过 maxBytes → 节点 body 截断到 60% / 邻居摘要 truncate 到首 50 字
- [ ] 返回 `{ prompt, sizeBytes, truncated }` 让 handler 决定是否在 Notice 提示截断

### Task 4: Skill 文件 canvas-vault/.claude/skills/node-chat/SKILL.md
- [ ] frontmatter `name: node-chat` + `description`
- [ ] body 指令 Claude Code CLI：解析剪贴板 prompt → 抽取节点上下文 + 邻居 → 进入对话模式（不写文件 / 不修改 frontmatter）
- [ ] Skill 不能调用 ai-linked-doc 派生（防止本 Story 与 1.17 混淆）

### Task 5: 单元测试 frontend/obsidian-plugin/src/__tests__/node-chat-context.test.ts
- [ ] `collectNeighbors` — empty resolvedLinks / 5+ links（截到 5）/ 邻居 frontmatter 缺字段
- [ ] `buildNodeChatPrompt` — 标准 / 超大（截断）/ 无 selection / 无邻居
- [ ] 至少 8 个 case，target 100% line coverage

### Task 6: build + deploy 验证
- [ ] `cd frontend/obsidian-plugin && npm run build`
- [ ] `cp main.js ../../canvas-vault/.obsidian/plugins/canvas-learning-system/main.js`
- [ ] main.js size 应在 73000-78000B 之间（v1.18 完后是 72731B；本次 +2-5KB）
- [ ] 105+ 单元测试 green（含本次新增 8）

---

## Dev Notes

### 架构对齐
- **Mode D（订阅额度）**：planning-artifacts/architecture.md:113 已锁。Plugin 不调 Anthropic API / Claude API；所有 LLM 调用通过 Claudian session 在用户登录的 Claude Code CLI 内执行
- **Hybrid 范式（Story 1.17 v3.0 已验证）**：Plugin clipboard write + Claudian invoke 是 Cross-process 通信的成熟模式，零依赖独立 API
- **Vault 级 .claude/skills/**：Story 1.19 已验证 Claudian 自动扫描 `<vault>/.claude/skills/<name>/SKILL.md`

### 文件锚点
- **现有范式**：`frontend/obsidian-plugin/src/main.ts:822-882` — `handleAILinkedDoc()` 是 hybrid 模式的最完整范例（context 收集 → modal → clipboard → Claudian invoke）
- **Context 收集类似实现**：`frontend/obsidian-plugin/src/main.ts:843-862` — 1.17 已实现"读 frontmatter / extractBoardName / extractSourceBoardFromFrontmatter"
- **resolvedLinks 用法范例**：`frontend/obsidian-plugin/src/main.ts:514-525` — 1.19 v4.0 反向引用检测
- **showRetryNotice 范式**：`frontend/obsidian-plugin/src/main.ts:792-805` — 剪贴板失败重试

### Resolution Rules
- **节点孤立（无邻居）**：仍能启动对话，prompt 注明"这是孤立概念"
- **节点超大（body > 50KB）**：截断到首 30KB + 标记"[...原文还有 X 字]"
- **路径含中文**（如 `节点/特征值.md`）：UTF-8 安全（Story 1.19 v4 已验证 OK）

### 不在本 Story 范围
- ❌ Backend `/api/v1/agents/dialog/session/{node_id}` endpoint — 留待 Story 3.2
- ❌ Per-node session 持久化（对话历史落地）— 留待 Story 3.7 dialog-pullout-node
- ❌ Token tracking / quota — 留待 Story 3.10 / 3.12
- ❌ wikilink graph multi-hop（NetworkX BFS）— 留待 Story 1.2（路线 B）

---

## Dev Agent Record

### File List
（dev-story 实施时填）

### Change Log
（dev-story 实施时填）

### Pitfalls + 诊断矩阵
| 偏离信号 | 可能根因 | 排查命令 |
|---|---|---|
| Cmd+Shift+C 触发后无 Notice | 命令未注册 / hotkey 没绑 | Cmd+P 搜"节点对话"看是否存在 |
| Notice "请先打开 节点/" 但当前是节点 | path 大小写 / 中文目录编码 | Console: `app.workspace.getActiveFile().path` |
| Claudian 不打开 | Claudian 未装 / 命令 ID 变化 | Console: `app.commands.findCommand("claudian:open-view")` |
| 粘贴后 Claudian 不识别 /node-chat | Skill 文件缺失 / frontmatter 错 | `ls canvas-vault/.claude/skills/node-chat/SKILL.md` |
| 邻居为空但应有 wikilink | metadataCache 没 resolve / 文件路径不对 | Console: `app.metadataCache.resolvedLinks[file.path]` |

---

## Trace

- **FR-CONV-01**: 节点 AI 对话 — Cmd+Shift+C 触发对话
- **FR-CONV-02**: 上下文自动注入 — frontmatter + body + selection + 1-hop 邻居
- **FR-AGENT-01**: Mode D Claude Code CLI 调用（Claudian session）
- **FR-AGENT-02**: 用户订阅额度（无独立 API Key）

---

## Notes

- 本 Story 是路线 A 第 1 个 Story（用户 2026-05-02 plan 选定）
- 路线 A 推荐理由：4 MVP 闭环达成后用户最缺 AI 对话价值；Epic 3.1 用 Claudian 现成能力，不需 1.2 wikilink graph 也能跑
- 验收通过后启动路线 B（Story 1.2 wikilink-graph-build + 1.3 wikilink-context-assembly），把 1-hop 邻居升级为 multi-hop（context 质量提升 ~5x）
