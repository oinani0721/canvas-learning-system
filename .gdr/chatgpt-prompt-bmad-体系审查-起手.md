# BMAD spec 体系级审查 — 给 ChatGPT 的起手 prompt

> 用法: 复制下方分隔线之间 prompt → 粘贴到 ChatGPT (Pro Deep Research / Claude Desktop 1M / Gemini 2.5 Pro DR) → 同时**上传 `research-pack-bmad-system-audit.xml`** (1.4MB / 412K tokens / 102 文件) → 发送

---

✂️ ═══════════════ 复制下方开始 ═══════════════

请对我上传的 **`research-pack-bmad-system-audit.xml`** 做 **Deep Research 深度分析**.

## 议题: Canvas Learning System BMAD spec 体系级审查 (76 spec × 10 epic)

## 用户体系疑问 (锚定)

> "我们到底按什么 spec 开发? 旧 epic/story 哪些有用? 多 session 并行开发, 怎么不冲突?"

外加 3 个用户原话锚点:
- "我选 Graphiti 看重时序图谱 + 记忆批注 + 记忆节点关系"
- "Edge 对话已经实现, 双链连节点时填关系" (ai-linked-doc.ts 已确认)
- "MVP 还有 3 项: 检验白板设置 + Graphiti 记忆系统 + 个人笔记返回系统"

## 📦 XML Bundle (1.4MB / 412K tokens / 102 文件)

- **<directory_structure>** — 76 BMAD spec + 5 新 spec + 5 audit 报告 + 12 backend + 4 plugin + sprint-status + gotcha
- **<files>** — 102 个 file 完整内容
- **末尾 <instruction>** ⭐ — 完整任务书 (6 议题 + 7 Part 输出格式 + 严格要求)

**请先读末尾 `<instruction>`** (这是完整任务书), 然后通读 `<directory_structure>` 建心智模型, 再按 instruction §3-§4 分析.

## 🎯 6 核心议题 (任务书 §3 详版)

1. **76 spec 健康度全图** — 64 ready-for-dev 真该砍多少? 哪些 Tauri 残留? 哪些代码实施但 spec 没标 done (G-FAKE-001 历史)?
2. **epic-5-graphiti-era 5 spec** 是否真覆盖 ChatGPT 5 必修? 与旧 epic-5/ BKT/FSRS 接口契约?
3. **5 session 并行可行性** — 41h 工时, Session A/B/C/D/E 真不冲突? import dependency 图?
4. **旧 64 ready-for-dev 砍清单** — 具体哪几个砍, 哪几个推 Sprint 3+?
5. **Sprint 3+ 优先级** — Sprint 2 v3 ship 后, Sprint 3 必修 6-8 spec ID?
6. **多 session 协同硬规则** — 避免 G-FAKE-001 / G-PIPE-006 历史

## 📋 7 Part 输出 (任务书 §4 详版)

请用中文回复, 必给:

- **Part 1**: 76 spec × 4 状态分布判定 + **整体健康度 X/10**
- **Part 2**: Sprint 2 v3 11 active spec 验证 (5 session import dep 图)
- **Part 3**: 旧 64 ready-for-dev 砍清单 (具体 spec ID + 理由)
- **Part 4**: 推荐重构后的 BMAD spec 体系 (epic 重新映射)
- **Part 5**: 多 session 并行验证 (波 1 / 波 2 序列推荐)
- **Part 6**: Sprint 3 具体优先级 (6-8 spec ID + 工时)
- **Part 7**: 一句话体系判定

## 📌 严格要求

- **必给具体 spec ID + epic 编号** (不能"Epic 8 大部分砍"泛泛)
- **必给 import dependency 图** 验证 5 session 真不冲突
- **必给 file:line 证据** 在 xml bundle 内
- **避免**: "体系大致 OK, 仅需小幅调整" — 无信息回答
- **重点**: 体系级真相 + 多 session 协同硬规则 + Sprint 3 优先级

开始你的 Deep Research 吧.

✂️ ═══════════════ 复制上方结束 ═══════════════

---

## 🚀 实操 (你的下一步)

### 选 A: ChatGPT Pro (Deep Research)
1. https://chatgpt.com (Plus/Pro/Enterprise)
2. + → 上传 `.gdr/research-pack-bmad-system-audit.xml` (Finder 已 reveal)
3. 切换 o1-pro 或 GPT-4o + Deep Research
4. 粘贴 prompt → 发送 → 等 30-60 min (Deep Research 大包平均耗时)

### 选 B: Claude Desktop (1M context)
1. 拖 xml 到对话框
2. 粘贴 prompt → 发送

### 选 C: Gemini 2.5 Pro Deep Research
1. https://gemini.google.com → Deep Research
2. 上传 xml → 粘贴 prompt → 等 15-30 min

## 📂 文件速查

```
XML: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.gdr/research-pack-bmad-system-audit.xml
Prompt: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.gdr/chatgpt-prompt-bmad-体系审查-起手.md
任务书: /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/2026-05-26-bmad-体系级审查-任务书-给-ChatGPT.md
```

## ❓ ChatGPT 答得不够深时追问

```
你的 Part 3 砍清单基于哪几个 spec frontmatter 证据?
请引用具体 <file path="..."> 内容支撑.

另外, 你 Part 5 的 5 session 并行图是 import dependency 图吗?
请用箭头图明确 A→B→C→D→E 谁依赖谁, 哪些可真并行.

如果你不熟 Graphiti API 实际限制, 请引用 https://github.com/getzep/graphiti 的具体 example.
```
