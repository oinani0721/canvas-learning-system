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

## ✅ 验收清单（{N} 步 UAT — 你一步步跑，勾掉每一项）

> [!tip]+ 怎么用这份清单
> 每跑完一步，**点击对应的 `- [ ]` 切换为 `[x]`**（Obsidian 原生支持）。
> 发现不对劲 → **选中那一行 → `Cmd+Shift+A` → ❌ 错误 + ❌ 不懂**，把问题批到这个文档里，Claude 会看到。

### 第 0 步：前置（必须做）

- [ ] 已经按 `Cmd+Q` 完全关闭 Obsidian 再重开（加载新 main.js）
- [ ] {PREREQ_2_IF_NEEDED}
- [ ] 知道 `Cmd+E` 可以在编辑/阅读视图之间切换

### 第 1 步：{UAT_STEP_1_NAME}

- [ ] {UAT_STEP_1_ACTION}
- [ ] {UAT_STEP_1_EXPECTED}

### 第 2 步：{UAT_STEP_2_NAME}

- [ ] {UAT_STEP_2_ACTION}
- [ ] {UAT_STEP_2_EXPECTED}

{...更多步骤...}

### 第 N 步：边界测试（Esc 取消）

- [ ] {BOUNDARY_ACTION}
- [ ] {BOUNDARY_EXPECTED_NO_SIDE_EFFECT}

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
1. cp _bmad-output/templates/uat-sheet-template.md canvas-vault/验收单/Story-{id}-{kebab-title}.md
2. 全文替换 {PLACEHOLDER} 为实际值
3. UAT 步骤条数按实际情况 (一般 5-10 步)
4. 历史追溯段若是首次 ship 写"无"，correct-course 后追加 [!error]+ callout

correct-course 触发时:
1. 覆盖原文件（不新建）
2. version 字段 ++
3. 追加历史追溯 callout
4. 新增 vN-1 → vN 变化表
5. UAT 步骤按新交互重写
-->
