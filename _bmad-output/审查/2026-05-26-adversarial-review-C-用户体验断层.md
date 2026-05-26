---
review_id: "C-用户体验断层"
date: "2026-05-26"
reviewer: "Adversarial UX Reviewer (Carlzon MOT + Nielsen + 5-Second Test)"
scope: "Obsidian Hybrid 降级后用户首次打开能否 5 秒内说'明天再打开'"
anchor_quote: "2026-05-13 用户原话: 批注+双链探索+个人记忆系统+极其针对性考察"
verdict: "FAIL (5 秒测试通过率预估 = 20%)"
---

# 审查 C — 用户体验断层 (Obsidian Hybrid 降级后)

## 执行摘要

**5 秒测试通过率预估 = 20%**

降级到 Obsidian Hybrid 后，4 个 MVP 的代码层 100% 已 done (sprint-status 1-16~1-19 全绿 + MVP-α v1.2 ship)，但 **用户首次打开 Obsidian 看 Dashboard.md 的 5 秒内**，命中"我能用它做什么"的概率约 20%。原因不在功能缺失，在于：

1. **零 onboarding tour** — Dashboard.md 开头是 DataviewJS 代码块渲染的"📊 平均精通度"指标，但首次打开 `节点/` 为空、`原白板/` 为空，用户看到 4 个 `0/0/0/0` 的指标 + "🌱 暂无原白板"提示，无法 5 秒内回答"这是什么 / 我能做什么"。
2. **4 个 hotkey (Cmd+Shift+A/D/Q + Claudian /chat) 全部隐式** — 用户不打开 `_bmad-output/验收单/Story-MVP-α-end-to-end.md` 读 30 分钟，根本不知道这 4 键存在。Dashboard.md 不暴露入口。
3. **"个人记忆系统"完全不可感知** — MVP-α v1.2 已诚实化承认 Graphiti 零接入，但用户视角的"AI 看到我之前说过什么"这种 felt-sense 时刻没有 UI 反馈。

---

## 4 MVP × Moments of Truth 表

| MVP | MOT 触发 | 30 秒成功捷径 | 卡点 | 流畅度 (1-10) |
|---|---|---|---|---|
| **1. 批注 hotkey (1-16)** | Cmd+Shift+A → FuzzySuggestModal 7 选项 | 选中文字 → A → ↑↓ 选 → Enter | **7 个 callout 类型 (question/tip/error/hint/note/warning/info) 用户不知道哪个对应什么场景**，二级 Modal "🤔 模糊 / 😐 一般 / 😊 清晰" 又再加一层选择。两层 modal = 5 次点击才完成一条批注 | **5/10** |
| **2. AI 双链 (1-17 Cmd+Shift+D)** | 选中文字 → D → 自动建节点 + wikilink | 用户不知道这个 hotkey 存在 (Dashboard 0 提示) | **首次使用必须先 reload Obsidian + 自己绑 hotkey** (MVP-α 验收单"起跑前 30 秒"承认了)。首次成功率估 < 30% | **4/10** |
| **3. 原白板配置 Skill (1-19)** | Claudian 侧栏输 `/configure-whiteboard` | 输命令 → AskUserQuestion 4 modal 引导 | **Claudian 侧栏图标位置非显著 (右上角 paperclip-like icon)**，新用户不知道侧栏存在。Skill 触发后还要分清 ①建空 ②建+种子 ③追加 3 模式 | **5/10** |
| **4. Dashboard 一键考察 (1-18)** | 打开 Dashboard.md → 点 🚀 启动考察 | 首屏看到表格 + 按钮 | **vault 空时看到 "🌱 暂无原白板"** — 用户首次 = 100% 触发空状态。空状态没给"先做什么"的 next-step 提示 (应有 "→ 点这里建第一个白板") | **3/10** |

**MOT 综合**: 4 个 MVP 平均 4.25/10 — 卡点不在功能 bug，在**入口隐藏 + 空状态荒漠 + 隐式 hotkey**。

---

## 用户 4 支柱 Obsidian 下实现度

| 支柱 (用户 2026-05-13 原话) | Obsidian Hybrid 实现 | 流畅度 |
|---|---|---|
| **批注** | ✅ Cmd+Shift+A FuzzySuggestModal — 真实写入 frontmatter tips[] (Story 2.4)，properties 面板可见 | ⚠️ 7 选项 + 二级 modal = 流程长但完整 |
| **双链探索** | ⚠️ Obsidian 原生 `[[wikilink]]` + 反向链接面板**真实可用**，但**status-bar 显示"递归 → factorial" 路径仅前端展示，不上传 backend** (MVP-α v1.2 已诚实化) — 用户感知到"被记录"是假象 | ⚠️ UI 有，记忆无 |
| **个人记忆系统** | ❌ **Graphiti 零接入** (MVP-α v1.2 第 4 步 Claude 回应原文承认: "MVP-α-1 完全跳过 Graphiti / ACP / 拆解路程上传")。Story 1.16-callout-graphiti-hook 仍 `ready-for-dev` 未实施。LanceDB 笔记检索仅 backend 内部，用户视角 0 信号 | ❌ 完全断层 |
| **极其针对性考察** | ⚠️ MVP-α-1 出题 LLM **真引用 frontmatter tips 原话** (LLM "看到"了)，但 LITE-4-3 V-08+V-10 修复仍 `ready-for-dev` — wikilink 邻居层 + 评分对象一致性两个 CRITICAL 漏洞未修，**评分按 node content 评，不按真实题面评** (`exam_tools.py:435-454`) | ❌ 出题真，评分假 |

**4 支柱总评**: 1 ✅ + 2 ⚠️ + 2 ❌ = 用户 2026-05-13 锁定的核心闭环在 Obsidian Hybrid 下**只达成 ~37.5%**。

---

## 3 个 UX 断层

### 🔴 CRITICAL #1 — 空状态荒漠 (Dashboard.md 首屏)

**断层**: 用户首次打开 vault，Dashboard.md 用 DataviewJS 算 `nodes.length` = 0、`boards.length` = 0 → 渲染 "🌱 暂无原白板。Cmd+P → 搜「建/配置原白板」从零建第一个" 一行字。**没有可点击的引导按钮，没有视频示例，没有 sample data，没有 "5 分钟教学" 链接**。
**对照原 Tauri 方案**: ReactFlow 拖拽 Canvas 是空的可以拖一个节点出来，至少**视觉上**有交互信号。Obsidian Hybrid 下空 vault = 文本 wasteland。
**Carlzon MOT**: 第一个真理时刻 (打开 app) 直接 fail — 用户 5 秒内无法回答"我能做什么"。
**修复**: Dashboard.md 加 "## 🚀 5 分钟上手" 段，含 ① 这是 Canvas / ② 第一步点这里建白板 / ③ 第二步选段文字按 Cmd+Shift+A / ④ 第三步按 Cmd+Shift+Q 出题。**不依赖任何 plugin 功能，纯 markdown + obsidian:// URI 链接**。

### 🔴 CRITICAL #2 — Graphiti 零接入但 UI 假装在记 (个人记忆系统支柱断)

**断层**: MVP-α v1.2 验收单第 4 步 Claude 回应**已承认** "拆解路程 0 上传 backend, Graphiti 全链路 0 调用"，但前端 status-bar.ts **仍显示** "🎓 1 条 Tips" + "递归 → factorial" 路径 — 用户视角是**系统在记**，实际是**前端缓存到内存 + 重启清空**。这是用户期望 vs 实现之间的 **最大欺骗** (用户 2026-05-13 原话四支柱里"个人记忆系统"权重最高，被 status-bar fake 掉)。
**对照原 Tauri 方案**: Inspector 数据面板直接显示 Neo4j 节点数 / Graphiti episode 数 — 假不了。
**Nielsen Heuristic #1 (Visibility of System Status)** 违反: 用户以为有记忆系统，实际是 in-memory placeholder。
**修复**: 在 Dashboard.md 加 "🧠 记忆系统状态" 区块，**真调** `/api/v1/health/graphiti` 显示 episode 数。如果 0 → 标 "⚠️ 记忆系统未启用 (Story 1.16 ready-for-dev)" — **诚实 > 装样**。

### 🟠 HIGH #3 — 4 个 hotkey 隐式 + 首次必 reload (onboarding 黑洞)

**断层**: MVP-α 验收单"起跑前 30 秒"已暴露此问题 — 用户首次必须：① 打开 Settings → Hotkeys → 搜 "Quick Exam" → 自己绑 Cmd+Shift+Q (因为 plugin `hotkeys: []` 让用户自绑) ② Cmd+P → "Reload app without saving" (让 main.js 101K 生效)。**这 2 步任何一步漏，第 4 步 hotkey 触发 0 反应**。
**对照原 Tauri 方案**: Tauri toolbar + MCP toolbar 是**视觉可见的按钮**，用户不需要记快捷键。
**JTBD 反例**: 用户的 job 是 "学习"，不是 "学 Obsidian hotkey 绑定"。
**修复**: plugin manifest.json 改 `hotkeys: [{ modifiers: ["Mod", "Shift"], key: "q" }]` 默认绑定 (允许冲突时 Obsidian 自动提示用户改) — 而不是 0 绑定让用户摸黑。同时 Dashboard.md 顶部加 "⌨️ 4 键速查" sticky 区块 (A 批注 / D 派生 / Q 考察 / `/chat-with-context` RAG)。

---

## 结论 (一句话)

**用户能否 5 秒内说"明天再打开"** → **不能** — Dashboard.md 首屏空状态 + Graphiti 零接入但 UI 装样 + 4 hotkey 隐式绑定，3 个断层任一独立都会让首次用户在 10 秒内关闭 Obsidian。用户 2026-05-13 锁定的"批注+双链探索+个人记忆系统+极其针对性考察"四支柱目前在 Hybrid 下**仅实现 1.5/4** (批注真实 + 双链 UI 真实但记忆假) — 在 Story 1.16-callout-graphiti-hook + LITE-4-3 V-08/V-10 三个 ready-for-dev 实施完成前，**不建议向真实用户 ship**。
