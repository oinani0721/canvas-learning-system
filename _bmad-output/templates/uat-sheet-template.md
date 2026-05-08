---
story: "{STORY_ID}"
title: "{KEBAB_TITLE}"
status: "review"
version: "{V_NUMBER}"
date: "{YYYY-MM-DD}"
developer: "Claude Code ({MODEL_NAME})"
commit: "{GIT_COMMIT_SHA_SHORT}"
---

# Story {STORY_ID} 验收单（给你看的版本）

> [!info]+ 这是什么
> 这是 Story {STORY_ID} 的用户验收文档，**给你（非技术）读的版本**。
> 技术 spec 在 `_bmad-output/implementation-artifacts/epic-{EPIC_ID}/{STORY_ID_KEBAB}-*.md`（Claude 读的）。
> 这份文档里没有技术术语，只有你能看到、摸到、点击的行为。

---

## 🎯 这个 Story 要做到什么

{ONE_SENTENCE_GOAL_NON_TECHNICAL}

---

## 📖 用户故事（你的视角）

**作为** {USER_ROLE}，
**我想** {USER_WANT_PLAIN_ENGLISH}，
**以便** {USER_BENEFIT_WHY_MATTERS}。

---

## 🖥️ 你会看到的交互（一步一步）

```
1. {STEP_1_USER_ACTION}
       ↓
2. {STEP_2_USER_ACTION}
       ↓
3. {STEP_3_SYSTEM_RESPONSE}
       ↓
4. {FINAL_VISIBLE_RESULT}
```

{OPTIONAL_SCREENSHOT_OR_ASCII_DIAGRAM}

---

## 🤖 Claude 已代验（你不用跑，给你看证据用）

> [!success]+ 这一段是 Claude 自动跑完贴证据
> **你不用跑也不用懂**。出现以下任何关键词不算 bug，是 Claude 应该处理的：`curl` / `docker` / `HTTP 200` / `JSON` / `schema` / `:端口号` / `pytest` / `build_time_ms` / `endpoint` / `adapter` / `.env`。
> 你只看右边"结果"列是不是 ✅。

| # | 技术验证项 | 结果 |
|---|---|---|
| 1 | {TECH_VALIDATION_1} | ✅ {EVIDENCE_SHORT} |
| 2 | {TECH_VALIDATION_2} | ✅ {EVIDENCE_SHORT} |
| 3 | {TECH_VALIDATION_3} | ✅ {EVIDENCE_SHORT} |
| ... | ... | ... |

> 典型代验项：API endpoint status / 数据库写入计数 / docker 容器健康度 / pytest 单测全过 / Pydantic schema 验证 / LLM cost 计数 / 文件路径就位 / git commit ID 等

---

## 👤 你来验（产品使用体验 — {N} 步，{T} 分钟内全在浏览器/Obsidian 里完成）

> [!warning]+ 这段的硬规矩（Claude 写之前自检 5 题）
> ✅ 句型："**我做 X → 我看到 Y → 我感觉 Z**"（动作 + 视觉 + felt-sense）
> ✅ 工具白名单：浏览器主窗口 / Obsidian 主界面 / macOS Finder（仅看 vault 内文件）
> ⛔ 禁词：`curl` / `docker` / `:端口号` / `HTTP` / `JSON` / `.env` / `endpoint` / `adapter` / `pydantic` / `schema` / `pytest` / `容器` / `daemon` / `git` / `cd` / `mkdir` / `DevTools` / 命令行
> ⛔ 禁工具：终端 / Terminal / iTerm / DevTools (Cmd+Option+I) / Docker Desktop（除"启动 app + 看图标"）
> 不确定该写哪段 → 默认归"🤖 Claude 已代验"。

### 第 0 步：First 5 seconds（产品骨架 + 第一印象）

> [!info]+ 5-Second Test 起手 — 打开 5 秒后凭印象答（用户先关掉再答会更准）

- [ ] 我打开 {APP_ENTRY_PLAIN — 例 "浏览器输入 localhost 那个网址"}，5 秒内看到 {FIRST_VISIBLE_THING — 例 "DeepTutor 主界面，左侧 Books 菜单"}
- [ ] 5 秒后我感觉这是 (a) 严肃学习工具 (b) 还在调试的玩具 (c) 看不出来 — 选: ___
- [ ] 一眼能看出我现在在哪一页吗？(是 / 不能 / 模糊)

### 第 1 步：{USER_FACING_FEATURE_NAME — 不带技术词，用大白话}

- [ ] 我 {USER_ACTION_PLAIN — 例 "点 Books 列表里的第一本"}
- [ ] 我看到 {USER_EXPECTED_VISIBLE — 例 "新页面，左边一列章节标题"}
- [ ] 我感觉 {FELT_SENSE — 例 "流畅 / 期待看更多内容"}（如卡顿/困惑/失望，写下来）

### 第 2 步：{NEXT_USER_FACING_STEP}

- [ ] 我 {USER_ACTION_PLAIN}
- [ ] 我看到 {USER_EXPECTED_VISIBLE}
- [ ] 我感觉 {FELT_SENSE}

{...更多用户步骤...}

### 第 N 步：边界（如果我做错会怎样）

- [ ] 我故意 {WRONG_USER_ACTION — 例 "点一个还没内容的章节"}
- [ ] 我看到 {GRACEFUL_FALLBACK — 例 "灰色提示'内容稍后填充'，不是英文报错弹窗"}
- [ ] 不会闪退 / 不会白屏 / 不会出现红色英文 stack trace

### 主观打分（Felt-sense — Sean Ellis-lite）

填数字（不是必填，但能帮 Claude 判断）：

- [ ] **流畅度**（1=卡顿到想关 / 5=如丝般顺滑）：___
- [ ] **易学性**（1=不看教程没法用 / 5=看一眼就会）：___
- [ ] **明天我会再打开它的可能性**（0-10 NPS-style）：___
- [ ] 一句话告诉 Claude，让你打这个分的最主要原因是：___

---

## 🚦 验收结果

**如果所有步骤 ✅**：告诉我 "**Story {STORY_ID} 通过**"，Claude 会 mark as **done**，自动启动 Story {NEXT_STORY_ID}（{NEXT_STORY_TITLE}）。

**如果有任何一步 ❌**：在下面批注区写出具体哪一步 + 你看到的实际现象，Claude 根据你反馈 `bmad-bmm-correct-course` 调整。

---

## 📝 你的批注区

> [!question]+ 你对 Story {STORY_ID} 的批注
>
> 在这里写任何疑问/建议/不满意。或者直接用 `Cmd+Shift+A` 批注上面任何一段。
>
> （空）

### 已知的已批注问题（历史追溯）

{HISTORICAL_ANNOTATIONS_WITH_TIMESTAMPS_OR_EMPTY}

<!--
Claude 在 correct-course 后在此处追加 [!error]+ v{N} → v{N+1} 修复 callout:

> [!error]+ {YYYY-MM-DD} — v{N}→v{N+1} 修复记录
> **你的原批注**：{USER_ANNOTATION_VERBATIM}
> **根因**：{ROOT_CAUSE_ANALYSIS_PLAIN_LANGUAGE}
> **已修复**：{FIX_SUMMARY_WHAT_CHANGED}
-->

### v{N-1} → v{N} 你将看到的变化（仅 correct-course 后存在）

| 维度 | v{N-1}（已淘汰） | v{N}（现在） |
|---|---|---|
| {DIM_1} | {OLD_BEHAVIOR} | **{NEW_BEHAVIOR}** |
| {DIM_2} | {OLD_BEHAVIOR} | **{NEW_BEHAVIOR}** |

---

## 🔗 技术 spec 参考（给 Claude 读的，不是给你读的）

- **Story spec**：`_bmad-output/implementation-artifacts/epic-{EPIC_ID}/{STORY_ID_KEBAB}-*.md`
- **源代码**：
  - {FILE_PATH_1}
  - {FILE_PATH_2}
- **单元测试**：{TEST_PATH}（{N_CASES} 用例 / {PASS_RATE} 通过）
- **Git commit**：`{COMMIT_SHA}` — {COMMIT_SUBJECT}
- **AC → 代码对应**（AC 编号 → 文件:行号）：
  - AC #1 → {FILE}:{LINE}
  - AC #2 → {FILE}:{LINE}

---

## 📅 下一步（你批完这份单后）

1. **全部 ✅** → 说 "通过" → Claude 立即 mark done → 启动 Story {NEXT_STORY_ID}
2. **部分 ❌** → 在批注区写清楚，或者选中那几行用 `Cmd+Shift+A` 批 `❌ 错误 + ❌ 不懂` → Claude 跑 `bmad-bmm-correct-course` 再次修正
3. **想暂停这个 Story** → 告诉 Claude "暂停 Story {STORY_ID}"，状态保持 `review`，可随时回来

---

<!--
## 模板使用说明（Claude 内部）

每次 dev-story 完成后:
1. cp _bmad-output/templates/uat-sheet-template.md _bmad-output/验收单/Story-{id}-{kebab-title}.md
2. 全文替换 {PLACEHOLDER} 为实际值
3. UAT 步骤条数按实际情况 (一般 3-5 步用户段，{N}_技术 任意)
4. 历史追溯段若是首次 ship 写"无"，correct-course 后追加 [!error]+ callout

correct-course 触发时:
1. 覆盖原文件（不新建）
2. version 字段 ++
3. 追加历史追溯 callout
4. 新增 vN-1 → vN 变化表
5. UAT 步骤按新交互重写

## ⛔ Claude 写完此验收单后必跑的 5 题自检（口头自答，不通过 = 重写）

来自 2026-05-07 5-agent deep explore 收敛（Moments of Truth + JTBD + Nielsen + 5-Second Test）：

1. 我"👤 你来验"段里有没有出现 `curl` / `docker` / `:端口号` / `HTTP` / `JSON` / `.env` / `endpoint` / `adapter` / `pydantic` / `schema` / `pytest` / `git` / `cd` / `mkdir` / `DevTools` 任何一个？→ 有 = ❌（必须移到"🤖 Claude 已代验"段）
2. 我"👤 你来验"每一条 checkbox，一个 60 岁不会编程的人能不能一次性照做？→ 不能 = ❌
3. 每条 UAT step 是不是用了"我做 X → 我看到 Y → 我感觉 Z"三段式？→ 缺 felt-sense = ❌
4. 我"🤖 Claude 已代验"段是不是真的 Claude 自己跑了拿证据，不是叫用户跑？→ 不是 = ❌
5. 我"🖥️ 交互流程"画的是用户屏幕变化，还是后端架构（`backend → endpoint → 容器`）？→ 后端流 = ❌

5/5 通过 → ship 给用户。任一 ❌ → 重写对应段。

## 方法论分层（不同 Phase 用不同 UAT 重点）

- **Phase A（产品骨架，page 内容空）**：用 5-Second Test + Moments of Truth — 测"你愿不愿意明天再打开"
- **Phase B（功能可用，内容填充）**：用 JTBD + Nielsen Heuristic-Lite — 测"用户能否完成 job"
- **Day 7+（产品成熟）**：用 NPS + Sean Ellis 40% PMF test — 测"明天消失你会非常失望吗"
-->
