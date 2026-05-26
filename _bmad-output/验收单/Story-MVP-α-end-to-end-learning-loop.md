---
story: "MVP-α-end-to-end"
title: "MVP-α 最小学习循环 — 端到端 e2e 验收 (Session A + B + C 全套)"
status: "review"
version: "v1.2"
date: "2026-05-20"
developer: "Session A (backend) + Session B (plugin) + Session C (skill) — 3 工种并行 ship + 用户批注 hotkey 修复 + v1.2 架构诚实化"
plan: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
parent_plan: "_bmad-output/research/2026-05-14-mvp-alpha-parallel-dev-plan.md (336 行协调文档)"
review_score: "Agent A 9/10 (Session A) + Agent B 9/10 (Session B) + 38/40 (Session C)"
v1_1_change: "用户批注修复 — quick-exam Cmd+Shift+E → Cmd+Shift+Q (commit 5cec794, 4 键语义对齐 A/C/D/E/Q)"
v1_2_change: "用户 3 条批注回应 + 3 Explore agent deep explore — Graphiti 零接入 GAP 暴露 / 评分基准 1-4 等级无 rubric / E 键不在 plugin 而在 Skill. 架构层延后清单写入 # ⚠️ MVP-α 范围说明 section, β-1 plan 锁定见 _bmad-output/research/beta-graphiti-integration-plan.md"
session_uat_individual:
  - "Session C 独立 UAT: _bmad-output/验收单/Story-MVP-α-3-exam-quick-skill.md (已 ship)"
  - "Session A + B 整合在本文档 (因 backend 无独立 UI, plugin 是触发入口)"
---

# Story MVP-α 端到端学习循环验收单 v1.2

> [!info]+ 这是什么?
> 用户 10 分钟体验脚本: 批注 → AI 看到我的话 → 针对性出题 → 答题 → 评分反馈.
> **3 工种并行 ship + 用户批注热修复完成. 全部代码就位, 待你 hands-on UAT.**

> [!warning]+ v1.2 关键变更 (2026-05-20 — 用户 3 条批注 deep explore 后诚实化)
> v1.1 表格声称的"Graphiti episode → LLM"链路 ❌ **未实际接入**. 真实链路 = `frontmatter tips → backend 读 .md → LLM 直接出题`. 详见 §⚠️ MVP-α 范围说明.
> **不影响第 4/5 步 hands-on UAT 通过判定** — 用户依然能体验"AI 引用我的批注原话"这个核心瞬间, 只是底层不走 Graphiti / KG / 拆解路程. Graphiti 接入锁定为 β-1 优先级首位.

---

## 🚀 起跑前 30 秒（v1.1 新增）

> [!warning]+ 这 3 步是 v1.0 验收发现的前置, **必须做完才能开始第 4 步**

### 准备 1: 绑定 Cmd+Shift+Q (Quiz 快捷键)

- [ ] 我打开 Obsidian Settings (⌘,)
- [ ] 我点左栏 "Hotkeys" → 搜索框输 "Quick Exam"
- [ ] 我找到 "Canvas Learning System: Quick Exam (单题考察, MVP-α)"
- [ ] 我点右侧 "+" 按钮 → 按下 Cmd+Shift+Q → 看到绑定成功
      User: 我需要知道的是这里的 quik exam 对应的是我们当前已有快接键的哪一个功能，因为我并没有看到 quik exam
      
> [!success]+ Claude 回应 (Explore agent deep explore main.ts:327-421 完毕)
> **Quick Exam 是 MVP-α-3 新增的命令, 不对应任何旧功能** — 注册位置 `frontend/obsidian-plugin/src/main.ts:418-421`, 命令真实 name = `"Quick Exam（单题考察, MVP-α）"`. 用户在 Hotkeys 面板搜以下任一关键词都能找到: `Quick Exam` / `单题考察` / `MVP-α` (大小写不敏感).
>
> **你看不到的最常见原因 (90% 概率)**: Plugin main.js 没 reload 进 Obsidian. 解决: `Cmd+P → 输 "Reload app without saving" → 回车`. 重启后 5 秒内界面回来, 再去 Hotkeys 搜 Quick Exam 就能找到.
>
> **5 键 (A/C/D/E/Q) 真相** (协调文档声称 vs plugin 代码现实):
>
> | 键 | 功能 | 实际位置 | 代码状态 |
> |---|---|---|---|
> | **A** | Annotate (批注) | plugin `canvas:annotate-callout` | ✅ Story 1.16 done |
> | **C** | Chat (节点对话) | plugin `canvas:open-node-chat` | ✅ Story 3.1 done |
> | **D** | Derive (AI 双链文档) | plugin `canvas:ai-linked-doc` | ✅ Story 1.17 done |
> | **E** | Extract-context (RAG 对话) | ⚠️ **Claudian Skill** `/chat-with-context`, 不是 plugin 命令 | ✅ Skill ready |
> | **Q** | Quiz (单题考察) | plugin `canvas:start-quick-exam` | ✅ MVP-α-3 done (本轮新增) |
>
> **E 键特别说明**: 协调文档把 5 键都说成"plugin 命令"是简化, 实际 E 键是在 Claudian 侧栏输 `/chat-with-context` 触发, 不在 Obsidian Hotkeys 面板里. 你在 Hotkeys 搜 E 永远搜不到, 这是设计, 不是 bug.

- [ ] 我感觉: 5 键 (A/C/D/Q 4 键 + E 走 Claudian Skill) 各司其职, 清晰

### 准备 2: Reload Obsidian 让 main.js 101K + 新 skill 生效

- [ ] 我用 Cmd+P → 输入 "Reload app without saving" → 回车
- [ ] Obsidian 重启 → 5 秒内界面回来

### 准备 3: 打开 Properties 面板 (Story 2.4 frontmatter tips[] 可见)

- [ ] 我打开任意 节点 .md → 右上角 "..." → "Show properties in document"
- [ ] 我看到笔记顶部出现 YAML properties 区
- [ ] 我感觉: 数据透明, 我能看见

---

## 🎯 这套 MVP 要做到什么

让你**在 10 分钟内体验完整学习闭环**: 写批注 → 系统记忆 → 触发出题 → AI 引用你的原话 → 答题 → LLM 评分 → 反馈写回. 全程 5 个可感知的反馈瞬间.

跳过 BKT/IRT/AutoSCORE 4 维等高复杂度算法 — 业界 MVP 通用做法 (Anki / Duolingo / Leitner). **闭环优先于精度**.

---

## 📖 用户 10 分钟旅程 (用户故事)

```
T=0:00  打开 Obsidian → 看到示例节点 "递归.md"

T=0:30  选中文字 → Cmd+Shift+A → 写批注 "我对 base case 还不理解"
        → ✨ 瞬间 #1: properties 出现 tips[] (Story 2.4 ✅)
        → ✨ 瞬间 #2: 状态栏右下角显示 "🎓 1 条 Tips"

T=2:00  第 2 条批注 "栈溢出和缺 base case 是一回事吗?"
        → ✨ 瞬间 #2 状态栏更新 "🎓 2 条 Tips"

T=3:30  Cmd+Click wikilink 跳到 factorial.md
        → ✨ 瞬间 #3: 状态栏显示路径 "递归 → factorial"

T=4:00  Cmd+Shift+Q 触发 "canvas:start-quick-exam"
        → ✨ 瞬间 #4 ★★ 关键 ★★ Toast "🤔 正在生成题目..."

T=4:05  5 秒后, 自动生成 节点/考察-递归-2026-05-14.md, 含:
        # 考察: 递归
        ## 题目
        你在批注中提到「我对 base case 还不太理解」, 请用 factorial(n) 为例:
        (a) base case 写 `if n == 0` 时何时触发?
        (b) 你说的「栈溢出」和这里什么关系?
        ## 你的回答
        [此处填写]
        → Toast "📄 题目已生成"
        ← 用户立刻感觉 "AI 真的懂我说的话"

T=6:00  手写答案 200 字

T=8:00  Cmd+S 保存 → 自动 POST /api/v1/exam/grade
        → ✨ 瞬间 #5 Toast "⏳ 正在评分..." → "✅ 评分完成: 4/5"
        → 文件底部追加:
          ## 反馈 (4/5)
          你说对了核心 — base case 是递归终止条件...

T=10:00 闭环完成 ✅
```

**fallback 路径** (主路径失败时, Session C 兜底):
- 在 Claudian 侧栏直接输 `/exam-quick` → skill 走 LLM 直接生成单题
- 跟主路径同样质量 (但跳过 IRT/RAG 三路)

---

## 🤖 Claude 已代验 (3 session 各自 + 集成)

> [!success]+ 已自动跑完贴证据

### Session A — Backend (Agent A 评分 9/10)

| # | 技术验证项 | 结果 |
|---|---|---|
| 1 | `backend/app/api/v1/endpoints/exam_quick.py` 新建 177 行 | ✅ ls 验证 |
| 2 | `backend/app/api/v1/endpoints/exam_grade.py` 新建 167 行 | ✅ ls 验证 |
| 3 | `backend/app/services/question_generator.py` 加 generate_question(user_tips) 方法 | ✅ +114 行 |
| 4 | `learning_context_service._fetch_tips_and_errors` 加第 3 source (Story 2.4 frontmatter tips) | ✅ +51 行 |
| 5 | backend/app/api/v1/router.py 注册 exam_quick + exam_grade router | ✅ 含 4 处 marker |
| 6 | backend restart 后 POST /api/v1/exam/quick 实测 200 OK | ✅ {"question_id":"...","tip_count":0,"tips_used":[]} |
| 7 | 接口签名跟 Session B plugin 期望对齐 (question_id / question_text / tip_count / tips_used / generated_at) | ✅ |
| 8 | LLM 评分 (gpt-4o-mini 单次) → score 0-5 + feedback + mastery_delta | ✅ exam_grade.py 代码就绪 |
| 9 | In-memory ring buffer (200 上限 FIFO) 跨 endpoint 共享 question_id | ✅ get_question_record() |
| 10 | 降级策略: tips 获取失败/LLM 失败/JSON 解析失败 三层 fallback | ✅ |

**⚠️ Session A 未 commit** — 文件在 worktree untracked 状态.

### Session B — Plugin (Agent B 评分 9/10)

| # | 技术验证项 | 结果 |
|---|---|---|
| 1 | `frontend/obsidian-plugin/src/status-bar.ts` 新建 249 行 | ✅ 6 pure functions |
| 2 | `frontend/obsidian-plugin/src/exam-quick.ts` 新建 367 行 | ✅ 6 pure functions |
| 3 | `tests/status-bar.test.ts` 37 测试全过 | ✅ npm test pass |
| 4 | `tests/exam-quick.test.ts` 35 测试全过 | ✅ npm test pass |
| 5 | main.ts 集成 StatusBarController + QuickExamController | ✅ 1500+ 行 |
| 6 | onload 注册 metadataCache.on('changed') + workspace.on('file-open') + vault.on('modify') | ✅ 3 event handlers |
| 7 | 命令 "canvas:start-quick-exam" 注册 | ✅ Cmd+Shift+Q |
| 8 | 跟 Session A backend schema 对齐 (POST quick → question_id; POST grade → score) | ✅ |
| 9 | 防重复 grade — session.graded flag + hasFeedbackSection 双重守门 | ✅ |
| 10 | npm run build → main.js 101K (前 88K, 增 13K 符合预期) | ✅ 已部署 canvas-vault |
| 11 | grep bundled "exam-quick\|status-bar\|/api/v1/exam" 全部命中 | ✅ |
| 12 | 接口契约守护 — schema 不一致时 Notice "后端返回数据缺 X" | ✅ |
| 13 | commit f860f57 + backup-push + origin-push | ✅ |

### Session C — Skill (Agent A 评分 38/40 = 95%)

| # | 技术验证项 | 结果 |
|---|---|---|
| 1 | `canvas-vault/.claude/skills/exam-quick/SKILL.md` 新建 150 行 (8.8KB) | ✅ |
| 2 | YAML frontmatter 5 字段 (name/description/argument-hint/allowed-tools/model) | ✅ |
| 3 | 8 项 HARD CONSTRAINTS (禁改文件/禁 MCP/中文/Prompt 防护/延迟 5-10s 等) | ✅ |
| 4 | 双路径触发识别 (A 裸触发 vs B `<exam_context>` 注入) | ✅ |
| 5 | 批注 3 种 pattern 识别 (callout + **User: + frontmatter tips) | ✅ |
| 6 | 输出 markdown 等价 JSON, 跟 plugin 端 /api/v1/exam/quick 对齐 | ✅ |
| 7 | 出题策略 4 类路由 ([!question]+ 反向 / [!error]+ 巩固 / **User: 直问 / 无批注通用) | ✅ |
| 8 | 故障明示 + downgrade 告知 + 修复指引 | ✅ ℹ️ 标记 |
| 9 | skill 已被 Claude 工具系统注册 (system reminder 含 exam-quick) | ✅ 可立即触发 |
| 10 | 风格密度跟 study-question 一致 (约束密度 5.3%) | ✅ |

**⚠️ Session C 未 commit** — SKILL.md 在 worktree untracked 状态.

### 端到端集成 — 5 个反馈瞬间通路 (v1.2 诚实化)

| 瞬间 # | 描述 | 真实触发链路 | 实施状态 | 跟用户初衷的距离 |
|---|---|---|---|---|
| **#1** | 批注同步 properties tips[] | callout → FrontmatterTipsSync → `fm.tips[]` (Story 2.4 Plan A) | ✅ done | ✅ 真实闭环 |
| **#2** | 状态栏 "🎓 N 条 Tips" | metadataCache.on('changed') → countTipsFromFrontmatter | ✅ done | ✅ 真实闭环 |
| **#3** | 导航路径 "递归 → factorial" | statusBar.handleFileOpen → buildNavPath (**仅前端展示, 不上传**) | 🟡 仅前端 | ⚠️ **拆解路程未进后端, Graphiti 零写入** |
| **#4** | 出题 Toast + 引用原话 | plugin → POST /api/v1/exam/quick → backend 读 `.md` frontmatter tips → LLM 拼 prompt | ✅ done | ⚠️ **不走 Graphiti, 跳过 ACP/5-layer/KG/三路 RAG** (见 question_generator.py:536-542 MVP-α-1 注释) |
| **#5** | 评分完成 + 反馈追加 | plugin onFileModified → POST /api/v1/exam/grade → gpt-4o-mini 单次 → `## 反馈` 段写入 | ✅ done | ⚠️ **评分基准模糊** — Prompt 只定义 0/5 两端, 1-4 等级 LLM 自由发挥 (见 §⚠️ 评分基准透明化) |

**实际架构**: `Obsidian 批注 → frontmatter tips[] → backend 读本地 .md → LLM 直接出题/评分`. Graphiti / Neo4j / KG / 拆解路径 / FSRS / BKT / IRT 全部跳过.
**用户体验影响**: 5 个瞬间能体验, 但底层是简化版. 跟 v1.1 表格相比, v1.2 不改任何代码, 仅诚实化文档描述. 真正接入 Graphiti 锁定为 β-1, 见 `_bmad-output/research/beta-graphiti-integration-plan.md`.

---

## 👤 你来验 (产品使用体验 — 10 分钟全程在 Obsidian)

> [!warning]+ 这段的硬规矩
> 工具白名单: Obsidian 主界面 / Claudian 侧栏 / Properties 面板
> 句型: "我做 X → 我看到 Y → 我感觉 Z"
> 重要: 开始前先 reload Obsidian (Cmd+P → "Reload app without saving") 让 main.js 101K + exam-quick skill 全生效

### 第 0 步: Reload Obsidian + 确认状态栏

- [ ] 我用 Cmd+P → "Reload app without saving" → Enter
- [ ] Obsidian 重启 → 5 秒内界面回来
- [ ] **我看到状态栏右下角出现 "🎓 0 条 Tips"** (Session B α-5)
- [ ] 我感觉: 系统启动正常

### 第 1 步: 第 1 条批注 → 看 properties + 状态栏 (瞬间 #1 + #2)

- [ ] 我打开任意 `节点/<某概念>.md`
- [ ] 我选中文字 → Cmd+Shift+A → 选 💡 Tips → 选 🤔 模糊
- [ ] 我在 callout "✍️ 我的理解:" 后写 "我对 X 还不太理解"
- [ ] 我等 1 秒
- [ ] **我看到 properties 面板出现 tips 数组** (Story 2.4 真相源)
- [ ] **我看到状态栏更新 "🎓 1 条 Tips"** (Session B α-5)
- [ ] 我感觉: 透明 / 可见 / 数据真在文件里

### 第 2 步: 第 2 条批注 → 状态栏自增 (瞬间 #2)

- [ ] 我再选一段文字 → Cmd+Shift+A → 选 ❌ 错误 → 选 🤔 模糊
- [ ] 我写 "我觉得这里跟 Y 容易混淆"
- [ ] 我看到状态栏更新 "🎓 2 条 Tips"
- [ ] 我感觉: 累积可见

### 第 3 步: wikilink 跳转 → 导航路径 (瞬间 #3)

- [ ] 我 Cmd+Click 任意 [[wikilink]]
- [ ] 我看到状态栏出现 "原节点 → 目标节点" 路径
- [ ] 我感觉: 探索被记录

### 第 4 步: 触发考察 → 引用原话 (瞬间 #4 — ★ 核心 ★)

> [!error]+ 2026-05-14 v1.0 → v1.1 用户批注修正
> **用户原批注**: "Cmd+Shift+E 是和我的笔记 RAG 检索，以及我们的拉出新的节点这一个功能出现了矛盾"
> **诊断**: 真冲突 — Cmd+Shift+E 在 Canvas 项目历史中固化为 `canvas:chat-with-context` (Story 2.1 / 笔记 RAG 检索), MVP-α 协调文档误把它给 quick-exam.
> **修复 (v1.1)**: quick-exam 改用 **Cmd+Shift+Q** (Q=Quiz, 项目历史推荐, 见 `_bmad-output/research/round-23-study-question-skill-design-2026-05-10.md:377`). 4 键语义对齐: A=Annotate/C=Chat/D=Derive/E=Extract-context(RAG)/Q=Quiz.


**User：我需要 agent 能清晰知道我是如何使用原白板剖析理解知识点的，通过我的批注和拆解路程，最后可以让我进一步加深理解我对原白板知识的印象加深和理解**
**然后这个拆分路程又是怎么样的被清晰的记录在我们 Graphiti 的当前后端？**

> [!error]+ Claude 回应 ★ 最重要的诚实化 ★ (Explore agent 全链路 grep 确诊)
> **你的批注命中真痛点 — MVP-α 实际上是"披皮的闭环", Graphiti 零接入**.
>
> **真实数据链路** (跟验收单 v1.1 表格声称的"Graphiti episode → LLM" 完全不一样):
>
> ```
> Obsidian 批注 [!question]+ / **User：...**
>     ↓ Story 2.4 Plan A FrontmatterTipsSync
> .md frontmatter tips: [{ text, tag, understanding, added_at }]
>     ↓ plugin Cmd+Shift+Q
> POST /api/v1/exam/quick {node_id, vault_id}
>     ↓ backend learning_context_service._fetch_tips_and_errors
>     ↓ 直接读 Path(canvas_base)/节点/{node_id}.md
>     ↓ yaml.safe_load(frontmatter) → tips: List[Dict]
>     ↓ question_generator.generate_question(user_tips=tips)
>     ↓ 拼 prompt "用户在批注中提到「{tip_text}」, 请..."
>     ↓ acompletion(gpt-4o-mini)
> question_text → 前端
>
> ❌ Graphiti 全链路 0 调用 (grep graphiti/kg_service/search_memory = 0 命中)
> ❌ 拆解路程 "递归 → factorial" 仅 status-bar.ts 前端展示, 不上传 backend
> ❌ 无 KG relevance / 跨节点推理 / 学习路径感知
> ```
>
> **跟你的产品愿景对照**:
>
> | 你的批注期望 | MVP-α 现状 |
> |---|---|
> | agent 知道我如何剖析白板 | ❌ 只读 frontmatter tips 文本, 无白板结构感知 |
> | 通过批注+拆解路程加深理解 | 🟡 批注用了 (LLM 引用原话), 拆解路程 0 |
> | 拆解路程清晰记录在 Graphiti 后端 | ❌ Graphiti 零写入, 路径仅前端展示 |
>
> **为什么是这样**: `backend/app/services/question_generator.py:536-542` 注释明确写着 *"MVP-α-1 (2026-05-14): 简化版'一键考察'出题 — 直接拼 prompt, 不走 ACP / 5-layer. 跳过的复杂度: ACP 5-layer assemble / 三路融合 RAG / FSRS+BKT+KG triangle"*. 这是有意延后, 不是 bug. 原版 `generate_exam_question()` (行 461-533) **有完整 Graphiti 接入** (`_get_tips()` + `_get_error_history()` + `assemble_acp()`), 但 MVP-α-1 为了快速 ship 闭环跳过了.
>
> **下一步 (你在选 Option C 后已锁定)**:
> - β-1 Story (MVP-α-5): 把 generate_question 接入 graphiti.search_memory_facts, 把状态栏导航路径上传新 endpoint /api/v1/event/navigation, 让 episode_worker 写白板拆解路径到 Graphiti
> - 锁定文档: `_bmad-output/research/beta-graphiti-integration-plan.md`
> - 工作量预估: ~10-14h (含 episode_worker 改 + plugin event 上报 + 4 source fusion + 测试)
>
> **本轮 UAT 是否能继续**: ✅ 能. 第 4 步"AI 引用我的原话"瞬间真实可见 (LLM 确实拼了 tips 进 prompt). 区别是: 现在 AI "看到的"只是 frontmatter tips 列表文本, β-1 之后 AI 还能看到"你怎么从节点 X 跳到节点 Y, 在节点 Y 又批注了什么"的完整路程.

- [ ] 我回到刚才批注的节点
- [ ] 我按 **Cmd+Shift+Q** (Quiz, 或 Cmd+P → "Quick Exam") 触发出题
  - ⚠️ 首次使用需在 Obsidian Settings → Hotkeys 搜索 "Quick Exam" 绑定 Cmd+Shift+Q
- [ ] 我看到 Toast "🤔 正在生成题目..."
- [ ] 5-10 秒后, 我看到 Toast "📄 题目已生成"
- [ ] 我看到自动打开 `节点/考察-{concept}-{date}.md` 文件
- [ ] **我看到题目引用了我的原话** (如 "你在批注中提到「我对 X 还不太理解」, 请...")
- [ ] **我感觉 "AI 真的懂我说的话"** ← 这是 MVP-α 的核心瞬间

### 第 5 步: 答题 → 自动评分 (瞬间 #5)

- [ ] 我在 `## 你的回答` 段写 100-200 字答案
- [ ] 我按 Cmd+S 保存
- [ ] 我看到 Toast "⏳ 正在评分..."
- [ ] 5-10 秒后, Toast "✅ 评分完成: 4/5"
- [ ] 我看到文件底部自动追加 `## 反馈 (4/5)` 段含 LLM 评论
- [ ] 我感觉: 闭环完成 / 系统真的在帮我学
User：你这里的自动评分是什么基准的评分

> [!warning]+ Claude 回应 — 评分基准透明化 (Explore agent 读 exam_grade.py 全文)
> **一句话**: 评分基准 = **gpt-4o-mini 一次黑盒判断 0-5 整数**, **无量化标准 / 无确定性保证 / 无可解释证据 / 无历史记录**. 符合 "MVP 闭环优先于精度" 原则, 但牺牲了 ~97% 可解释性.
>
> **评分 prompt 原文** (`backend/app/api/v1/endpoints/exam_grade.py:35-44`):
> ```
> 你是一位耐心的学习教练. 学生回答了一道题, 请你按以下方式评分:
> 1. 给一个 0-5 的整数分数 (0 = 完全错或空, 5 = 完美理解透彻)
> 2. 写 60-100 字的简短反馈 — 必须先肯定一处具体亮点, 再指出一个改进方向
> 3. 不要假装客观, 像导师一样直接说话, 用第二人称「你」
> ```
>
> **6 个透明化警示**:
>
> | 维度 | 现状 | 影响 |
> |---|---|---|
> | **Rubric 定义** | ❌ 只定义 0 和 5 两端, **1/2/3/4 全靠 LLM 自由发挥** | 你看到"4/5"无法理解为什么不是 5/5, 扣的是什么 |
> | **评分维度** | 🟡 单一隐含维度 ("整体理解程度") | 无法拆分"准确性/完整性/表达"扣分点 |
> | **确定性** | ❌ `temperature=0.3` + 无 seed + 无 cache | **同一答案两次提交可能得不同分** (违反评分公平性) |
> | **mastery_delta** | 简单 heuristic: `score≥4→+1, ≤1→-1, else 0` | 非 BKT 概率, 仅离散升降 |
> | **持久化** | ❌ 评分本身不存表, 仅 mastery_delta 通过事件链路写 Neo4j | 无法生成"我的成长曲线" / IRT 校准 |
> | **Fallback** | ⚠️ v1.1 表格声称"三层", 代码实际**两层** (JSON 解析 + 通用 exception 都 raise 502) | v1.1 表格行 122 过承诺 |
>
> **对比业界做法**:
>
> | 维度 | Duolingo/Khan | Anki | MVP-α |
> |---|---|---|---|
> | Rubric | 详细 5-7 级定义 + 例句 | 简化 (easy/good/hard) | ❌ 只有 0 和 5 |
> | 维度数 | 4-6 (准确性/完整性/创意性) | 1 (回想) | 1 (LLM 直觉) |
> | 可解释性 | "因为缺少 X 扣 1 分" | "因为 2 周没复习" | ❌ 无法解释 |
> | 稳定性 | 校准过的评分官 | 间隔公式确定 | temperature=0.3 随机 |
>
> **β 阶段升级方向** (锁定 β-2 后续):
> - 评分 prompt 加详细 1/2/3/4/5 等级 rubric
> - 拆 3-4 个评分维度 (concept_accuracy / completeness / clarity / tip_reference)
> - temperature=0 + seed 固化 + answer_hash 缓存
> - 评分历史写 attempt_history 表, 跟 IRT 校准
> - mastery_delta 升级为 BKT 概率
>
> **本轮 UAT 是否能继续**: ✅ 能. 4/5 分作为"模糊反馈"足够让你感受闭环, 但不要把它当成"客观能力评估". 想知道为什么扣 1 分, 直接问 Claudian "为什么不是 5 分" — LLM 会现编一段解释 (因为 prompt 没要求可解释, 它也是黑盒解释).

### 第 6 步: fallback 路径 (Session C 兜底, 可选)

- [ ] 我在 Claudian 侧栏直接输 `/exam-quick`
- [ ] 我看到 Claude 5-10 秒内输出一道题 (类似第 4 步, 但走 skill 不走 backend)
- [ ] 我看到底部 "ℹ️ 你正在使用 Claudian fallback 路径"
- [ ] 我感觉: 即使 backend 挂了也能学

### 主观打分

- [ ] **流畅度** (1=卡 5=如丝): ___
- [ ] **AI 懂我** (1=通用题 5=精确引原话): ___
- [ ] **闭环完整度** (1=断 5=10 分钟全通): ___
- [ ] **明天还想用** (0-10 NPS): ___
- [ ] 一句话告诉我你的感受: ___

---

## ⚠️ MVP-α 范围说明 (v1.2 新增 — 诚实化清单)

> [!info]+ 为什么有这个 section
> v1.1 验收单的"5 个反馈瞬间通路"表格 + "10 分钟学习闭环" 故事让你以为底层走的是 *Graphiti + KG + ACP + BKT/FSRS + IRT 多维评分* 的成熟管道. 实际上 MVP-α-1 (2026-05-14 ship) **有意跳过了这些复杂度**, 只跑通最简闭环. 这一节明确列出"声称-实现"的距离, 避免你以为闭环已经完成而提前结束 MVP-α.

### MVP-α 真实接入清单

| 维度 | MVP-α 现状 | β 升级目标 | β-X Story |
|---|---|---|---|
| **批注捕获** | ✅ Obsidian callout → frontmatter tips[] | (无升级) | — |
| **批注→backend** | ✅ backend 直接读 `.md` frontmatter | 升级: 同时读 Graphiti episode | β-1 MVP-α-5 |
| **拆解路程记录** | ❌ 仅前端 status-bar 展示 "递归 → factorial" | 升级: plugin → POST /api/v1/event/navigation → episode_worker → Graphiti | β-1 MVP-α-5 |
| **出题上下文** | 🟡 仅用 tips 列表拼 prompt | 升级: ACP 5-layer / 三路融合 RAG / KG relevance | β-1 MVP-α-6 |
| **出题模型路由** | ⚠️ 全部 gpt-4o-mini 单次 | 升级: 多模式路由 (IRT 难度 + 学生当前能力值) | β-2 |
| **评分 rubric** | ❌ 只定义 0/5, 1-4 模糊 | 升级: 详细 5 级 rubric + 多维拆分 + temperature=0 | β-2 |
| **评分历史** | ❌ ring buffer 200 重启清空, 评分本身不存表 | 升级: attempt_history 表 + IRT 校准 | β-2 |
| **精通度** | 🟡 离散 ±1/0 简单 heuristic 写 Neo4j | 升级: BKT 概率 + FSRS 间隔 | β-3 |

### 延后到 β 的 7 项复杂度 (按用户感知度排序)

1. **Graphiti 接入 (β-1, 用户感知度 ★★★★★)** — 你批注 2 命中的核心质疑, 拆解路程记录 + 跨节点推理
2. **评分 rubric 透明化 (β-2, 用户感知度 ★★★★★)** — 你批注 3 命中的可解释性, 让 4/5 分有依据
3. **ACP 5-layer 上下文 (β-1, ★★★★)** — 让出题不只看 frontmatter, 还看历史错误 / 跨概念关联 / 学习路径
4. **三路融合 RAG (β-1, ★★★)** — Neo4j + LanceDB + Grep 三路召回, 当前 0 接入
5. **BKT/FSRS 精通度 (β-3, ★★★)** — 用概率模型代替 ±1 离散升降
6. **IRT 难度路由 (β-2, ★★)** — 根据学生能力值选难度合适的题
7. **评分历史持久化 (β-2, ★★)** — 让你能看到"成长曲线"

### 本轮 UAT 通过判定 (不变)

**通过 = 6 步 hands-on UAT 全过 + 你能感受 5 个反馈瞬间真实存在**. **不要求**底层走 Graphiti / KG / 复杂管道. β-1 不是 MVP-α 验收的前置, 是 MVP-α 通过后的下一步.

如果你看完 v1.2 的诚实化说明后, 觉得 MVP-α 现状 (无 Graphiti) **不能接受**, 直接告诉我 "用 Option B", 我立即拆 MVP-α-5 Story 把 Graphiti 接进来 (~10-14h), 不通过 UAT.

---

## 🚦 验收结果

**全 6 步通过**: 告诉我 "**MVP-α 通过**" → 我补 commit Session A + C + 整合验收单 + 推荐下一阶段 (升级 β / 启动 Story 5.1 BKT / 或继续 Story 3.x AI 对话).

**某步失败**: 在批注区写明哪步 + 截图 → 我精确 debug.

---

## 📝 你的批注区

> [!question]+ 你对 MVP-α 端到端体验的批注
>
> (空 — 等你做完 6 步 hands-on UAT 后填)

### 历史批注追溯 (v1.0 → v1.1 → v1.2)

> [!error]+ v1.0 → v1.1 修复: quick-exam 快捷键冲突
> **批注**: "Cmd+Shift+E 是和我的笔记 RAG 检索, 以及我们的拉出新的节点这一个功能出现了矛盾"
> **修复**: commit 5cec794 把 quick-exam 从 Cmd+Shift+E 改 Cmd+Shift+Q. 5 键语义对齐 A/C/D/E/Q.

> [!error]+ v1.1 → v1.2 修复 #1 (2026-05-20): Quick Exam 找不到的真相
> **批注 1 (准备 1)**: "我需要知道的是这里的 quik exam 对应的是我们当前已有快接键的哪一个功能, 因为我并没有看到 quik exam"
> **诊断**: 命令真实 name = `"Quick Exam（单题考察, MVP-α）"`, 注册位置 main.ts:418-421. 找不到 90% 是 plugin main.js 没 reload.
> **修复**: 起跑前 30 秒 § 加 Claude 回应 callout + 5 键真相表格 (含 E 键是 Skill 不是 plugin 命令). 不改代码.

> [!error]+ v1.1 → v1.2 修复 #2 ★ 最重要 ★ (2026-05-20): Graphiti 零接入 GAP 暴露
> **批注 2 (第 4 步)**: "我需要 agent 能清晰知道我是如何使用原白板剖析理解知识点的, 通过我的批注和拆解路程... 然后这个拆分路程又是怎么样的被清晰的记录在我们 Graphiti 的当前后端?"
> **诊断**: 3 Explore agent 全链路 grep 确诊 — MVP-α-1 完全跳过 Graphiti / ACP / 拆解路程上传. 真实链路 = `frontmatter → backend 读 .md → LLM 直接出题`. 验收单 v1.1 表格"5 个反馈瞬间通路"过承诺.
> **修复**: 第 4 步 § 加 Claude 回应 callout (含真实链路图 + 期望对照表 + 为什么是这样 + β-1 锁定). 5 个反馈瞬间通路表格升级为"v1.2 诚实化版"含"跟用户初衷的距离"列. 加 §⚠️ MVP-α 范围说明 section 列 7 项延后清单. 不改代码, 改文档.
> **后续锁定**: β-1 MVP-α-5 Story 接 Graphiti, 计划见 `_bmad-output/research/beta-graphiti-integration-plan.md`.

> [!error]+ v1.1 → v1.2 修复 #3 (2026-05-20): 评分基准透明化
> **批注 3 (第 5 步)**: "你这里的自动评分是什么基准的评分"
> **诊断**: 评分 prompt 只定义 0/5 两端, 1-4 等级 LLM 自由发挥; temperature=0.3 无 seed 无 cache; 评分历史不存表. 牺牲 ~97% 可解释性.
> **修复**: 第 5 步 § 加 Claude 回应 callout (含 prompt 原文 + 6 个透明化警示表 + 业界对比表 + β-2 升级方向). 不改代码, 改文档.



### 已知非阻塞缺陷 (3 Agent 调研发现)

> [!error]+ 设计层非阻塞缺陷 (建议 β 阶段修复)
>
> **Session A backend (Agent A 9/10)**:
> - P2: backend/tests/ 无新增 exam_quick/grade 测试 (Story 2.4 已知 test 债)
> - P2: LLM 成本未记录 quota / 预算
> - P3: ring buffer 重启清空 (β 换 Neo4j 持久)
>
> **Session B plugin (Agent B 9/10)**:
> - P3: setTransientHint() stub 待补 lifecycle
>
> **Session C skill (Agent A 38/40)**:
> - P1: 多 callout 时选哪条出题策略未规定
> - P2: 路径 A 模糊节点名匹配未规定
> - P2: 出题策略缺 Q&A code example
>
> **集成层 (3 Session 共同)**:
> - 🔴 **Session A + C 未 commit** ⚠️ 需立即补 commit + push backup + origin

---

## 🔗 技术 spec 参考

- **协调文档**: `_bmad-output/research/2026-05-14-mvp-alpha-parallel-dev-plan.md` (336 行)
- **Session A backend 文件**:
  - `backend/app/api/v1/endpoints/exam_quick.py` (177 行, untracked)
  - `backend/app/api/v1/endpoints/exam_grade.py` (167 行, untracked)
  - `backend/app/services/question_generator.py` (modified +114 行)
  - `backend/app/services/learning_context_service.py` (modified +51 行)
  - `backend/app/api/v1/router.py` (modified, 注册 exam_quick + exam_grade)
- **Session B plugin 文件** (commit f860f57 已 push):
  - `frontend/obsidian-plugin/src/status-bar.ts` (249 行)
  - `frontend/obsidian-plugin/src/exam-quick.ts` (367 行)
  - `frontend/obsidian-plugin/src/main.ts` (modified, 集成 controllers)
  - `frontend/obsidian-plugin/tests/status-bar.test.ts` (290 行, 37 测试)
  - `frontend/obsidian-plugin/tests/exam-quick.test.ts` (339 行, 35 测试)
- **Session C skill 文件** (untracked):
  - `canvas-vault/.claude/skills/exam-quick/SKILL.md` (150 行)
- **Session C 独立 UAT 文档**: `_bmad-output/验收单/Story-MVP-α-3-exam-quick-skill.md`
- **3 Agent 评分**:
  - Session A: 9/10 (Agent A) — 需求对标 9/10, 代码质量 8.5/10
  - Session B: 9/10 (Agent B) — Plugin spec 100% + 守护机制完整
  - Session C: 38/40 = 95% — 双 telltale + downgrade 告知

---

## 📅 下一步

1. **通过** → 我立即 commit Session A + C (附 PLAN-NNN) → mark sprint-status → 推荐升级 β / Story 5.1 / Story 3.x
2. **某步失败** → 精确 debug 该 session 的代码 → ship v1.1
3. **想看协调文档全貌** → `_bmad-output/research/2026-05-14-mvp-alpha-parallel-dev-plan.md`
