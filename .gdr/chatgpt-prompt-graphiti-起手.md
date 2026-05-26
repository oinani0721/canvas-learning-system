# Graphiti 设计审计 — 给 ChatGPT 的起手 prompt

> **使用方式**: 复制下方分隔线之间的 prompt → 粘贴到 ChatGPT (Pro Deep Research / Claude Desktop 1M / Gemini 2.5 Pro Deep Research) → 同时**上传 `research-pack-graphiti-design-audit.xml`** → 发送

---

✂️ ═══════════════ 复制下方开始 ═══════════════

请对我上传的 **`research-pack-graphiti-design-audit.xml`** 做 **Deep Research 模式**深度分析。

## 议题: Canvas Learning System 的 Graphiti 时序图谱设计审计

## 用户原话锚点 (不可妥协)

> "我选择 **Graphiti**, 是看重了它的**时序图谱**, 所以我觉得它记忆我的**批注**, 以及记忆我**节点和节点之间的关系**有优势."

## 📦 XML Bundle 结构 (Repomix 格式)

- **`<directory_structure>`** — 25 个文件目录树
- **`<files>`** — 25 个 `<file path="...">` 块, 含完整内容 (140K tokens / 519KB)
- **末尾 `<instruction>` 段** ⭐ — 完整任务书 (含项目背景 / 4 缺口 / 6 议题 / 7 Part 输出要求)

**请先读末尾 `<instruction>` 段** (这是给你的完整任务书), 然后通读 `<directory_structure>` 建立心智模型, 再按 instruction §3-§5 分析每个 `<file>`。

## 🎯 4 大设计缺口 (我已实证, 不重新查证 — 你直接给方案)

| Graphiti API | 设计能力 | Canvas 实际利用率 | 待审 |
|---|---|---:|---|
| `add_episode` | 时序化事件写入 | 40% (仅 callout/edge/memory) | 怎么扩到 wikilink? |
| **`valid_at / invalid_at`** | **时序追踪 (知识演化)** | **0%** (用户最在乎) | 怎么让"我以前认为 X, 后来改成 Y"真追踪? |
| **`search_facts`** | 关系查询 | **0%** | 怎么让出题时真查回历史关系? |
| **`search_communities`** | **错误模式聚类** | **0%** | 怎么让"我反复在哪类问题上犯错"真实现? |
| `relationship_sync_service` | ai-linked-doc 7 类关系 → Graphiti edge | **dry_run=True** 默认 (line 193) | 怎么改 production? |

## 🔍 已知 6 个对抗议题 (任务书 §4)

1. Graphiti 时序图谱"演化追踪"机制设计 (valid_at/invalid_at episode_body schema)
2. 节点关系 7 类 → Graphiti edge 最佳建模 (edge_name vs property vs entity_type)
3. 错误模式聚类 search_communities 产品落地 (Dashboard mockup)
4. 1h sweep 延迟 vs 即时查询的折中
5. Graphiti edge vs Neo4j edge 设计协调 (G-FAKE-001 历史)
6. group_id 隔离机制审计 (Story 2.5.Y)

## 📋 输出格式 (`<instruction>` §5 有详细版)

请用中文回复, 给出 7 个 Part:

### Part 1: Graphiti 利用率全景判定 (必)

| API | 当前 % | 用户期望覆盖 % | 设计 gap |

**整体 Graphiti 设计成熟度**: X / 10

### Part 2: 4 大设计缺口的解决方案 (必, 每个含 schema + API + 工时)

### Part 3: 6 议题具体设计方案 (必, 必引用 Zep 官方文档 + GitHub examples)

### Part 4: Graphiti 学习科学价值评估 (d 值增益)

### Part 5: 与现有 Canvas 设计的冲突/协调 (Graphiti edge vs Neo4j edge / vs LanceDB / vs Agentic RAG 6 路)

### Part 6: Sprint 优先级 (Sprint 2 / Sprint 3 / Sprint 4+)

### Part 7: 一句话产品判定

"**Graphiti 时序图谱在 Canvas 的设计 [是否] 真正服务于用户'记忆批注 + 记忆节点关系' 的核心需求? 当前主要问题是 [...], 推荐 Sprint 2 必修 [...].**"

## 📌 严格要求

- **必给具体 schema + API 调用**, 不能 "建议加强" / "需要改进" 这种废话
- **必引用 Zep 官方文档 + GitHub examples** (https://github.com/getzep/graphiti / https://help.getzep.com/graphiti)
- **必给 file:line 证据** 在 Canvas codebase 中 (XML bundle 内有)
- **重点**: 设计层真相 + 产品层用户感知 + 学习科学层 d 值影响
- **避免**: "Canvas 整体架构良好, 仅需小幅优化" — 这是无信息回答

开始你的 Deep Research 吧.

✂️ ═══════════════ 复制上方结束 ═══════════════

---

## 🚀 实操流程

### 选 A: ChatGPT (web + Deep Research)
1. https://chatgpt.com (Plus/Pro/Enterprise)
2. + → 从电脑上传 → 选 Finder 中已 reveal 的 `research-pack-graphiti-design-audit.xml`
3. 模型选 **o1-pro** 或 **GPT-4o + Deep Research**
4. 粘贴 prompt → 发送 → 等 10-30 min

### 选 B: Claude Desktop (Sonnet 4.6 / Opus 4.7)
1. 拖 xml 到对话框
2. 粘贴 prompt → 发送 (1M context 够用, 不需 Deep Research)

### 选 C: Gemini Advanced (2.5 Pro Deep Research)
1. https://gemini.google.com → Deep Research
2. 上传 xml → 粘贴 prompt → 等 5-15 min

## 📂 文件路径速查

```
XML (上传给 ChatGPT, 140K tokens / 519KB):
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.gdr/research-pack-graphiti-design-audit.xml

Prompt (复制内容到 ChatGPT):
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.gdr/chatgpt-prompt-graphiti-起手.md

Instruction 备份 (XML 内已含):
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/2026-05-26-graphiti-设计审计-任务书-给-ChatGPT.md
```

## ❓ 如果 ChatGPT 答得不够深

追问模板:
```
你的判定基于哪个 file:line 证据? 请引用具体 <file path="..."> 内容支撑.

另外, 你是否真审了 instruction §4 的 6 议题? 请对每个议题给出具体 Zep API 调用 + episode_body schema (代码块).

如果 search_communities 你不熟, 请引用 https://github.com/getzep/graphiti 的具体 example.
```

## 🎯 用户期望的 ChatGPT 价值

不是 "Graphiti 设计大致没问题, 可以优化以下几点":
- ❌ 太泛
- ❌ 不可执行
- ❌ 浪费 Deep Research 算力

而是:
- ✅ "Sprint 2 必修这 3 件: 1) valid_at 写入 schema 改为 X (代码示例) 2) search_facts 在 LITE-4-3 路线 4 用法 (具体 query) 3) relationship_sync 改 production 的 5 个步骤"
- ✅ "search_communities 用 leiden 算法, episode_body 应有 keywords 字段供聚类, Dashboard 渲染用 mermaid pie chart"
- ✅ "Zep 官方 example: github.com/getzep/graphiti/blob/main/examples/temporal/ — 应这样改你的 Canvas 实现"
