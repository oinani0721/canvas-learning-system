# Canvas Learning System 学习效果落地审计 — 给 ChatGPT 的起手 prompt

> **使用方式**: 把以下分隔线**之间**的内容复制 → 粘贴到 ChatGPT (web / Claude Desktop / Gemini) 输入框 → 同时**上传 `research-pack-learning-effect-audit.xml`** → 发送 → 进入 Deep Research 模式

---

✂️ ═══════════════ 复制下方开始 ═══════════════

请对我上传的 **`research-pack-learning-effect-audit.xml`** 做 **Deep Research 模式**深度分析。

## 📦 XML Bundle 结构 (Repomix 格式)

- **`<directory_structure>`** — 55 个文件的目录树
- **`<files>`** — 55 个 `<file path="...">` 块，每个含完整内容 (487K tokens)
- **末尾 `<instruction>` 段** ⭐ — 12.7KB 详细分析议题 + 方法 + 输出格式

**请先读末尾的 `<instruction>` 段** (这是我给你的完整审计任务书)，然后通读 `<directory_structure>` 建立心智模型，再按 instruction 指引逐项分析每个 `<file>`。

## 🎯 任务速览 (`<instruction>` 内有详细版)

**议题**: Canvas Learning System (Obsidian Hybrid 学习应用) 的 **5 个新 BMAD spec** + **现有 backend 28 服务** + **plugin α-5** + **4 MVP 已 done** 全部落地后, 是否能实现 PRD/EPIC 锁定的 **9 大学习效果目标**:

1. PRD §1.1 检验白板 d=1.50 (Karpicke 2011)
2. PRD §1.3 Edge 对话 EI+SE d=0.55-0.73
3. PRD §1.5 **两个记忆系统** (LanceDB 笔记检索 + Graphiti 学习历程)
4. PRD §1.10 元认知 2x2 矩阵 (已砍)
5. PRD §2.3 三路融合出题 (canvas_type + Bloom)
6. PRD §2.4 三重隔离保证 (reference_answer=None)
7. EPIC 4 检验白板灵魂
8. EPIC 5 BKT+FSRS 掌握度
9. 用户 2026-05-13 核心闭环原话: "批注+双链探索+个人记忆系统+极其针对性的考察"

## ⭐ 关键约束 (必读)

- **视角**: 学习科学 + 产品 UX 宏观判定, **不是技术细节是否合理**
- **重点找**: "**落地后学习效果会打折扣**"的隐藏漏洞
- **核心 UX 锚点**: 我们用 **Obsidian 及其优秀的双向链接 (`[[wikilink]]`) 功能** 落地学习闭环。请重点审 wikilink 在 4 处的真实角色:
  1. LITE-4-3 出题时是否真利用节点 wikilink 邻居?
  2. STORY-2-10 是否真把 wikilink 关系同步进 Graphiti KG?
  3. Story 1.16-hook 是否记录 callout 所在节点的 wikilink 上下文?
  4. LITE-5-7 路线 B `search_facts` 是否能查到 wikilink 双链关系?
- **不审什么**: Sprint v3 plan 整体合理性 (已审过)、Sprint 1 接通任务、4 MVP 已 done 重审
- **专审什么**: 5 个新 spec + 现有架构落地后的**学习效果是否达成**

## 🔍 我已知 6 个漏洞 (不重复, 找 #7+)

1. LITE-5-7 `blocks` 反向 (已修正 v2)
2. LITE-5-6 估时 2h 低估
3. STORY-2-10 缺 Story 2.5.Y `depends_on`
4. LITE-5-7 v1 line 109 决策追溯 bug (已修正 v2)
5. PRD §1.5 三层记忆全砍是否过激
6. PRD §1.3 Edge 对话 EI+SE 完全缺失

## 📋 输出格式 (`<instruction>` 内有详细版)

请用中文回复, 给出 6 个 Part:

### Part 1: 学习效果守恒矩阵 (必)

| # | PRD 目标 | d 值 | 落地度 ✅⚠️❌🔴 | 证据 file:line | 漏洞 | 学习效果损失 % | 修复建议 |

### Part 2: 新漏洞清单 #7+ (必)

每个含: ID / 严重度 (CRITICAL/HIGH/MEDIUM/LOW) / 影响目标 / 学习效果损失 % / 证据 / 修复建议

### Part 3: 学习科学社区最佳实践差距

对照 Karpicke (2011) / Roediger & Pyc (2012) / Dunlosky (2013) / Nuthall (2007) / Bjork (Desirable Difficulty) 等实验, 判断"我们的设计妥协版是否仍能维持 d > 0.50 学习效应量"

### Part 4: 改善建议清单

按 **"Sprint 2 立刻修 / Sprint 3 加 / Sprint 4+ / 永不做"** 分组

### Part 5: 量化验证指标 (3-5 个)

Sprint v3 后 4 周, 用户该如何**实证验证**学习效果实际达成? 设计可观察指标

### Part 6: 执行总结 (300 字)

- 整体学习效果落地度 % (**单数字**)
- 必须 Sprint 2 修复的 critical 数
- 可推迟到 Sprint 3+ 的 medium 数
- **给我一句话的"产品能否 ship 给 CS 61B 学生用"判断**

## 📌 严格要求

- **必给数字** (% / h / 优先级排序), 避免模糊的 "可能" / "也许"
- **引用 `<file path="..."> + 行号`** 作为证据 (不能泛泛而谈)
- **必须先读 `<instruction>` 段** (位于 XML 末尾) 才能理解完整任务

开始你的 Deep Research 吧.

✂️ ═══════════════ 复制上方结束 ═══════════════

---

## 🚀 实操流程 (你的下一步)

### 选 A: ChatGPT (web 版 + Deep Research)

1. 打开 https://chatgpt.com (要 Plus / Pro / Enterprise 账号才有 Deep Research)
2. 点 **+** → **从电脑上传** → 选 Finder 中已选中的 `research-pack-learning-effect-audit.xml`
3. 复制上方分隔线之间的 prompt 文本到输入框
4. (可选) 切换模式: 选模型为 **o1-pro** 或 **GPT-4o + Deep Research mode**
5. 发送 → 等 10-30 min 出报告 (Deep Research 平均耗时)

### 选 B: Claude Desktop (Sonnet 4.6 / Opus 4.7)

1. 打开 Claude Desktop app
2. **拖拽** Finder 中的 XML 到对话框 (或点 + 上传)
3. 复制 prompt 粘贴
4. 发送 (Claude 不需要 Deep Research 模式，1M context 够)

### 选 C: Gemini Advanced (2.5 Pro Deep Research)

1. https://gemini.google.com → **Deep Research** 模式
2. 上传 XML
3. 复制 prompt
4. 发送 → 平均 5-15 min

---

## 📂 文件路径速查

```
XML (上传给 ChatGPT):
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.gdr/research-pack-learning-effect-audit.xml

Prompt (复制内容到 ChatGPT 输入框):
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.gdr/chatgpt-prompt-起手.md

Instruction 备份 (XML 内已含, 备份给人类读):
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/.gdr/instruction-learning-effect-audit.md
```

---

## ❓ 如果 ChatGPT 答得不够深

追问模板 (复制粘贴):

```
你的判断"落地度 X%"基于哪个 file:line 证据?
请引用具体 <file path="..."> 内容支撑.

另外, 你是否真审了 instruction 末尾的 4 个 wikilink 重点验证点?
请逐一回答这 4 个 wikilink 在代码中的真实角色 (引用 file:line).
```
