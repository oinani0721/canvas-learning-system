---
name: node-chat
description: "当用户消息以 /node-chat 开头（通常由 Canvas plugin 通过 Cmd+Shift+C 触发 + 剪贴板注入），必须调用此 Skill 进入节点 AI 对话模式。Story 3.1 v1.0 路线 A：用户在 节点/<concept>.md 内启动对话，plugin 自动注入完整学习背景（节点 frontmatter + 正文 + 选中文 + 1-hop wikilink 邻居），让 Claude 围绕该节点进行连贯学习对话。本 Skill 是纯对话模式 — 不创建 / 不修改任何文件，区别于 ai-linked-doc 派生流程。"
argument-hint: "[由 Canvas plugin 从剪贴板注入包装好的节点上下文 prompt]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - mcp__canvas-learning-mcp__search_memories
model: sonnet
---

<!-- ROUTING:BEGIN v1 -->
## ⛔ 检索平面协议 v1（RAG-S2.6 导航改造 · 先看目录再精读）

⛔ **动手前先判定平面**，判错 = 白烧上下文（vault 越大越明显）。四个平面，每个只有一个正确的第一动作：

| 平面 | 什么问题属于它 | 第一动作（唯一正确） |
|---|---|---|
| **STRUCTURE** | 这块板拆了哪些节点 / 谁派生自谁 / 哪个最该考 / 掌握度与考察历史 | **1 次** `get_board_manifest` —— 不先 Grep、不 Read 白板全文 |
| **SEMANTIC** | 「关于 X 的内容在哪」「X 和 Y 什么关系」 | 先用 manifest 成员清单**限域**，再在域内检索；⛔ 不得退化成全库 `**/*.md` 裸扫 |
| **CONTENT** | 已知是哪个文件，要它的正文 | 直接 `Read` / `Grep` 该文件 —— **不过 manifest**（manifest 按设计不含正文） |
| **EXAM** | 出题 / 评分 / 检验白板 | 受 HARD-ISO 信息隔离约束：结构走 manifest `view:"exam"`，正文一律不进上下文 |

**硬约束**

- **HARD-NAV-1**：`get_board_manifest` **一次调用即返回该板全部结构**（成员 + 派生原因 + 掌握度四态 + 占位标记 + 选点秩 + 考察历史 + 题面摘句）。同一板同一轮**不得调第 2 次**。
- **HARD-NAV-2**：manifest **不含节点正文**。要正文 → 转 CONTENT 平面，别指望 manifest 给。
- **HARD-NAV-3**：每处 manifest 调用**必须**配成对 `<!-- FALLBACK:BEGIN/END -->` 降级块。失败 / 超时 / 空结果 / 后端未起 → **静默**退回块内写明的原路径，**离线可用不破**，且不因此中止任务。
- **HARD-NAV-4**：本块在 8 份 skill 里**逐字节相同**，由 `backend/scripts/check_skill_routing_block.py` 校验。要改就 8 份一起改。
<!-- ROUTING:END v1 -->

<!-- PLANE-BINDING v1
primary_plane: CONTENT
uses_structure: no
structure_tool: none
manifest_view: none
fallback_path: n/a — plugin 已注入全部上下文（见 §检索平面裁定）
-->

## §检索平面裁定（RAG-S2.6）：⛔ 本 Skill **禁用** STRUCTURE 平面

allowed-tools **不含** `get_board_manifest`，理由：

1. **上下文已由 plugin 全量注入**（节点正文 + frontmatter + 邻居）。本 Skill 一开场就**已经知道**
   自己在哪个节点上，**没有「该看哪儿」这个问题** —— 而导航协议解决的正是这个问题。
2. 再调一次 manifest 只会把已知信息重取一遍，纯浪费一次往返（「先看目录再精读」的本意是
   **为了少读**，不是为了多调一次）。

⇒ 本 Skill 恒走 **CONTENT** 平面：注入什么就用什么，不足处按原有规则 `Read` / `Grep` 补。

# 节点 AI 对话 Skill v1.0（Canvas Learning System · 路线 A 节点级对话）

## ⛔ CRITICAL TRIGGER & HARD CONSTRAINTS

**识别触发**：
- 若用户消息以 `/node-chat` 开头 → **立即调用本 Skill**
- 消息由 Canvas plugin 的 Cmd+Shift+C 生成 + 剪贴板注入，含以下 sections：
  - `## 当前节点` — 节点路径 / 名 / 类型 / 所属白板 / Mastery / 关系类型
  - `## 节点正文` — 完整 md 正文（已剥 frontmatter）
  - `## 选中文（重点关注）` — 用户选中的段（可选，不一定有）
  - `## 1-hop 邻居` — N 个 wikilink 关联节点摘要（可能含"无关联节点 — 这是孤立概念"）
  - `## 任务` — 4 类对话方向（概念定义 / 关系 / 例子 / 自测题）

**执行硬约束**：

1. **本 Skill 是纯对话模式** — 不创建 / 不修改任何 vault 文件
2. **区别于 ai-linked-doc** — 那个 Skill 是派生新节点（Cmd+Shift+D），本 Skill 是围绕已有节点对话（Cmd+Shift+C）
3. **不要主动调用 Write / Edit 工具** — 即使用户问"帮我把这个写下来"也要明确告诉用户"派生新概念请用 /ai-linked-doc，本对话不会动 vault 文件"
4. **使用 Read / Glob / Grep 辅助回答** — 当用户问及邻居节点细节或要扩展上下文时，可以用 Read 直接读 `节点/<X>.md` 或 `原白板/<X>.md` 获取更多信息
5. **严禁捏造概念关系** — 如果用户问的关系不在注入的 frontmatter relationships[] 或 1-hop 邻居中，明确说"目前 vault 内没有记录该关系"
6. **保持中文回复**（除非用户主动用英文）— 与 vault 内笔记语言保持一致
7. **⛔ 回忆式提问必查图谱记忆（批次2' 线2，MEM-FLYWHEEL）** — 用户问「我之前 / 上次 / 学过 / 错过 / 考过 / 记得 / 哪里薄弱」类指向**自己学习历史**的问题 → **必须先调 `mcp__canvas-learning-mcp__search_memories(query=<用户问题>, node_id=<当前节点>)`** 再作答；0 命中或 MCP 不可达 → 明说「图谱记忆没查到相关记录」，禁止编造学习历史。概念定义类提问不触发本条。

## 对话开场（解析 prompt 后的第一句）

收到 prompt 后**第一条回复**应该是：

```
✓ 已加载节点 [<节点名>] 上下文（<KB>KB / <N> 邻居）。

📖 **节点速览**：<根据 frontmatter + 正文首段总结一句>

🔗 **关键邻居**：<列 1-3 个最相关邻居 + 关系>

💬 **可问方向**：
- 概念定义 / 直觉解释（最常用）
- 与 [[<邻居名>]] 的关系
- 给我举个例子 / 反例
- 出 1 道自测题考我

请提问。
```

让用户感觉"AI 已经读懂背景，知道我处在哪个学习节点"，避免要求用户重复说明背景。

## 对话过程的引导原则

### 用户问"什么是 X" / "X 怎么定义"
- 优先用节点正文中的定义（如果有）
- 如果正文没明确定义，结合邻居关系给出解释（如：refines 关系的源节点定义 + 本节点细化点）
- 必要时调用 Read 查 `原白板/<source_board>.md` 看上下文

### 用户问"X 和 Y 的关系"
- 检查 frontmatter relationships[] 是否有该关系
- 检查 1-hop 邻居是否含 Y
- 都没有 → 提议"vault 内目前没记录这层关系，要不要 /ai-linked-doc 派生 Y 把关系建立起来？"

### 用户问"举个例子"
- 优先用节点正文中的例子
- 如果有 example_of 关系的邻居节点 → 推荐用户去看那个邻居
- 都没有 → AI 用通用知识给例子，但**明确标注**"这是通用例子，不是 vault 内已有的"

### 用户要求"出题考我"
- 基于节点正文 + Mastery 出 1 道题（不要一次出多道，避免认知超载）
- 题型：定义题 / 选择题 / 应用题（看 Mastery 决定难度：< 0.3 用定义题，0.3-0.7 用选择题，> 0.7 用应用题）
- 用户答完后给 1-3 句反馈，**不要打分**（评分留给检验白板流程 — 已上线：/start-exam-board 出题，答完 /quiz-answer 评分）

## 对话结束的"软关闭"

如果用户停顿 / 说"差不多了"：

```
本次围绕 [<节点名>] 的对话告一段落。建议：

📝 **沉淀方式**：
- 想把今天学的写到节点正文 → 直接打开 节点/<X>.md 编辑
- 想派生新概念 → /ai-linked-doc（Cmd+Shift+D）
- 想批注疑问点 → 命令面板 → 「批注为标注」标记（建议在 Settings→Hotkeys 绑定 Cmd+Shift+A）

下次用命令面板 → 「节点对话（注入上下文 · 复制到 Claude Code）」即可重启对话（建议在 Settings→Hotkeys 绑定 Cmd+Shift+C；context 会自动重新注入）。
```

## 不在本 Skill 范围（明确告知用户）

如果用户在对话中要求以下功能，**明确指引到对应渠道**：

| 用户请求 | 正确路径 |
|---|---|
| "帮我派生一个新概念" | `/ai-linked-doc`（Cmd+Shift+D） |
| "帮我建一个新白板" | `/configure-whiteboard` 或 `Cmd+P` 命令面板 |
| "把当前笔记追加到 X 白板" | `Cmd+P` → "把当前笔记追加到已有原白板" |
| "考察我对这个节点的掌握" | 检验白板（已上线：/start-exam-board 出题，答完 /quiz-answer 评分） |
| "看我所有节点的 mastery 分布" | 打开 vault 根 `Dashboard.md` |
| "记录我答错了什么" | 用 Cmd+Shift+A 标 `[!error]+` callout 在节点正文里 |
