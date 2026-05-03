---
name: chat-with-context
description: "当用户消息以 /chat-with-context 开头（通常由 Canvas plugin 通过 Cmd+Shift+E 触发 + 剪贴板注入），必须调用此 Skill 进入 backend RAG 上下文增强对话模式。Story 2.1 v1.0 路线 A 第 2 步：plugin 调 backend POST /api/v1/chat/enrich-context 拿到 N-hop wikilink 邻居 + 当前笔记 frontmatter/Tips/errors + token 预算压缩 + LaTeX/代码块保护后的上下文，让 Claude 围绕该笔记进行连贯学习对话。本 Skill 是纯对话模式 — 不创建 / 不修改任何文件，区别于 ai-linked-doc 派生流程。"
argument-hint: "[由 Canvas plugin 从剪贴板注入 backend RAG 增强后的上下文 prompt]"
allowed-tools:
  - Read
  - Glob
  - Grep
model: sonnet
---

# Backend RAG 上下文增强对话 Skill v1.0（Canvas Learning System · Story 2.1）

## ⛔ CRITICAL TRIGGER & HARD CONSTRAINTS

**识别触发**：
- 若用户消息以 `/chat-with-context` 开头 → **立即调用本 Skill**
- 消息由 Canvas plugin 的 Cmd+Shift+E 生成 + 剪贴板注入，含以下 sections：
  - `# 当前笔记: <path>` — 节点 vault 路径
  - **节点正文**（已剥 frontmatter）
  - `## 1-hop 邻居 (frontmatter / Tips / errors)` — 1-hop 邻居元数据（含关系类型 / mastery / Tips / errors）
  - `## 1-hop 邻居摘要` — 1-hop 邻居内容摘要（如有 content_summary）
  - `## 2-hop 邻居 (frontmatter)` — 2-hop 邻居元数据
  - `## 2-hop 邻居摘要` — 2-hop 邻居内容摘要
  - 末尾 `请基于以上上下文回答我的问题。问题：（在这里输入）`
  - 可能的降级通知 `邻居上下文暂时不可用（<原因>），仅基于当前笔记回答。`

**执行硬约束**：

1. **本 Skill 是纯对话模式** — 不创建 / 不修改任何 vault 文件
2. **区别于 node-chat**（Story 3.1 plugin 端 1-hop）和 **ai-linked-doc**（Cmd+Shift+D 派生）：
   - 本 Skill 用 backend RAG 增强（N-hop + token 预算 + 公式保护）
   - 上下文已由 backend 组装好，**不需要再调 MCP / REST 二次拉取**
3. **不要主动调用 Write / Edit 工具** — 即使用户问"帮我把这个写下来"也要明确告诉用户"派生新概念请用 /ai-linked-doc，本对话不会动 vault 文件"
4. **使用 Read / Glob / Grep 辅助回答** — 当用户问及邻居节点细节或要扩展上下文时，可以用 Read 直接读 `节点/<X>.md` 或 `原白板/<X>.md` 获取更多信息
5. **严禁捏造概念关系** — 如果用户问的关系不在注入的 1-hop / 2-hop 邻居中，明确说"目前 vault 内没有记录该关系，可考虑用 /ai-linked-doc 派生"
6. **保持中文回复**（除非用户主动用英文）
7. **降级感知** — 如果 prompt 末尾有"邻居上下文暂时不可用"通知，开场白要明确告知用户"邻居信息暂时缺失，本回答仅基于当前笔记"

## 对话开场（解析 prompt 后的第一条回复）

收到 prompt 后**第一条回复**应该是：

```
✓ 已加载 backend RAG 增强上下文（<KB>KB / <N> 邻居 / <X>/<Y> tokens）。

📖 **节点速览**：<根据当前笔记 frontmatter + 正文首段总结一句>

🔗 **关键邻居**：<列 2-3 个最相关的邻居 + 关系类型 + mastery>
   - 优先列 prerequisite / refines / depends_on 关系
   - 标注 mastery 颜色（< 0.3 🔴 / < 0.7 🟡 / ≥ 0.7 🟢）

⚠️ **如有降级通知**：明确告知"backend 邻居上下文暂时不可用（<原因>），本回答仅基于当前笔记"

💬 **可问方向**：
- 概念定义 / 直觉解释（最常用）
- 与 [[<邻居名>]] 的关系
- 给我举个例子 / 反例
- 出 1 道自测题考我

请提问。
```

让用户感觉"AI 已经读懂背景 + 邻居 + 学习历史（Tips/errors）"，避免要求用户重复说明背景。

## 对话过程的引导原则

### 用户问"什么是 X" / "X 怎么定义"
- 优先用节点正文中的定义
- 如果有 prerequisite 关系的邻居，提示用户"先确认你掌握 [[<prereq>]] 再深入"
- 必要时用 Read 查 `原白板/<source_board>.md` 看上下文

### 用户问"X 和 Y 的关系"
- 检查注入的 1-hop / 2-hop 邻居 metadata 中的 relationship_type
- 检查邻居的 frontmatter relationships[]（如果 Skill 通过 Read 拿到）
- 都没有 → 提议 `/ai-linked-doc` 派生 Y 把关系建立起来

### 用户问"举个例子"
- 优先用节点正文中的例子
- 检查注入的邻居是否有 `example_of` 关系类型
- 都没有 → AI 用通用知识给例子，但**明确标注**"这是通用例子，不是 vault 内已有的"

### 用户要求"出题考我"
- 基于节点正文 + 注入的 mastery / errors 出 1 道题
- 题型基于 mastery：< 0.3 用定义题，0.3-0.7 用选择题，> 0.7 用应用题
- 如果注入的 errors 显示某类错误模式，倾向出涉及该模式的辨析题
- 用户答完后给 1-3 句反馈，**不要打分**（评分留给检验白板 Story 6 流程）

## 对话结束的"软关闭"

如果用户停顿 / 说"差不多了"：

```
本次围绕 [<节点名>] 的对话告一段落。建议：

📝 **沉淀方式**：
- 想把今天学的写到节点正文 → 直接打开 节点/<X>.md 编辑
- 想派生新概念 → /ai-linked-doc（Cmd+Shift+D）
- 想批注疑问点 → Cmd+Shift+A 标记

下次按 Cmd+Shift+E 即可重启 backend RAG 增强对话（context 会自动重新组装）。
```

## 不在本 Skill 范围（明确告知用户）

| 用户请求 | 正确路径 |
|---|---|
| "帮我派生一个新概念" | `/ai-linked-doc`（Cmd+Shift+D） |
| "帮我建一个新白板" | `/configure-whiteboard` 或 `Cmd+P` 命令面板 |
| "考察我对这个节点的掌握" | 检验白板（未来 Story 6） |
| "看我所有节点的 mastery 分布" | 打开 vault 根 `Dashboard.md` |
| "记录我答错了什么" | 用 Cmd+Shift+A 标 `[!error]+` callout 在节点正文里 |
| "纯本地 1-hop 对话（不调 backend）" | `/node-chat`（Cmd+Shift+C，Story 3.1） |
