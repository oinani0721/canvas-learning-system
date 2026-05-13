---
title: "Story 2.3 UAT 操作指引"
status: "active"
version: "1.0"
date: "2026-05-13"
related_commits: ["d9a7164", "438666d"]
related_uat: "_bmad-output/验收单/Story-2.3-historical-error-reminder.md"
---

# Story 2.3 UAT 操作指引（给你看的版本）

> [!info]+ 这是什么
> 你拿到这份文档时，本 session 已 ship 两个 commit：
> - `d9a7164` — Story 2.3 历史误解主动提醒（**需要你跑 UAT**）
> - `438666d` — Wave-5 Stage B follow-up `index.py` ContextVar 注入（**不需要你 UAT**，原因见末尾）
>
> 本文档帮你**完整跑通 Story 2.3 UAT**，包括 (1) 测试数据准备的 3 种选择 (2) 4 步用户验证 (3) 反馈通道。

---

## 🎯 跑 Story 2.3 UAT 的核心条件

要让 AI 提醒"你之前标记过……"，你的 vault 需要满足：

1. ✅ 至少一个概念笔记（如 `节点/my-recursion-notes.md`）已存在 — **你已有 10 个节点**
2. ✅ Claudian 侧栏可用 — **你已有 `Claudian: open view` 命令**
3. ⚠️ **该节点过去累积过历史误解记录** — **你需要决定怎么准备这部分数据**

下面的"📦 数据准备 3 选 1"部分就是给你选的。

---

## 📦 数据准备 — 3 种路径，3 选 1

### Path A：用现有 vault 数据直接跑（Phase A 精简 UAT）

**适用场景**：你想最快跑通，先验 AI 的"无历史误解"行为是否符合预期。

**做什么**：直接打开 Obsidian，跑下面 **段 4-B 第 2/3/4 步**（跳过第 1 步）。这能验证：
- ✅ AC #5 空记录时 AI 不输出冗余提示
- ✅ AC #4 服务降级时对话照常
- ⚠️ AC #1/#2（有历史误解时主动提醒）**无法验证**

**时长**：3-5 min

---

### Path B：你跟 AI 对话**自然**产生误解（Phase B 完整 UAT — 推荐 ⭐）

**适用场景**：你想验完整 5 个 AC，且想模拟真实学习流程。

**做什么**：
1. 在 Obsidian 打开 `节点/my-recursion-notes.md`（已有节点）
2. Cmd+P → "Claudian: open view" 开 AI 侧栏
3. 在 AI 侧栏故意问一个**会答错**的问题（如"递归一定比迭代慢吗？"）
4. 让 AI 给出回答后，在 Obsidian 用 `Cmd+Shift+A` 把你**自己注意到的误解点**批注成 `[!error]+` callout（这是 Story 1.16 的 hotkey 功能 — 已 ship）
5. **等 Story 2.5 plugin hook 触发** — 这会把你刚批注的误解写入 Graphiti（`episode_type='misconception'`）

**已知阻塞**：Story 2.5 plugin hook 集成是 `review` 状态（未实施 plugin 端 hook）。所以 **Path B 当前不可用** — 等 Story 2.5 plugin hook done 后才能跑。

**时长**：10-15 min（一旦 Story 2.5 plugin hook 就绪）

---

### Path C：授权 Claude 帮你 seed 3 条测试 misconception episode（最快但非真实路径）

**适用场景**：你想立刻验完整 5 个 AC，不等 Story 2.5 集成。

**做什么**：告诉 Claude **"授权 seed 3 条 recursion misconception 到 my-recursion-notes 节点 + group_id=vault:canvas_vault"**。Claude 会用 docker exec + Python script 调用 `memory_service.record_temporal_event` 写入 3 条 episode（production path，非伪数据）。

**会写入的内容**（你可以预览再决定授权）：

| # | error_type | description | corrected_at |
|---|---|---|---|
| 1 | misconception | 递归忘记 base case 导致无限循环 — 写 factorial 时漏了 if n==0 return 1 的终止条件 | 2026-05-10 |
| 2 | misconception | 把 recursion 和 iteration 的时间复杂度搞混 — 误以为 recursion 一定 O(n²) | 2026-05-11 |
| 3 | misconception | 尾递归 vs 普通递归优化没分清 — 以为 Python 会自动尾递归优化(实际没有) | 2026-05-12 |

**这 3 条 seed 后可以删除**（也告诉 Claude 即可）。

**时长**：1 min seed + 5-10 min UAT

---

## 🤖 Claude 已代验（你不用跑，参考 `Story-2.3-historical-error-reminder.md` 段 4-A）

本指引不重复列 21 项技术代验项（已在主验收单 line 56-90 详列）。简要：87/87 tests pass + DoD-3 D3-A 禁词 0 命中 + commit `d9a7164` 在位 + Wave-5 Stage B follow-up commit `438666d` ship。

---

## 👤 你来验（4 步用户验证 — 参考主验收单段 4-B）

> [!warning]+ 句型 + 工具白名单
> ✅ 句型："**我做 X → 我看到 Y → 我感觉 Z**"
> ✅ 工具白名单：Obsidian 主界面（点击/输入/Cmd+P 命令面板）
> ⛔ 全程不需要打开终端、命令行、浏览器开发者工具

### 第 1 步：问一个能勾起历史误解的问题（**需 Path B 或 Path C 完成数据准备**）

- [ ] 我做：在 Obsidian 打开 `节点/my-recursion-notes.md` + Cmd+P 唤起 Claudian + 问 "什么是 base case，为什么 recursion 需要它？"
- [ ] 我看到：AI 回答里**自然地**提到 "你之前标记过递归忘记 base case 导致无限循环……"
- [ ] 我感觉：像被一个记得我功课的私教指点（**期待 / 被照顾**），而不是金鱼记忆的助手

### 第 2 步：问一个跟历史误解无关的问题（Path A/B/C 都可验）

- [ ] 我做：在同一个笔记里换问 "递归在生活中有什么类比？"
- [ ] 我看到：AI 正常回答，**不**插入"你之前标记过"的提醒
- [ ] 我感觉：AI 有分寸（不会一次对话反复念旧错），不被冗余提醒分心

### 第 3 步：打开一个**全新、未批注过任何误解**的笔记（Path A/B/C 都可验）

- [ ] 我做：打开 `节点/TestConceptA.md`（你的测试节点，无历史误解）+ 问 AI 任意问题
- [ ] 我看到：AI 给出正常回答，**完全没有**任何"无历史误解"之类的冗余说明
- [ ] 我感觉：AI 安静、不啰嗦

### 第 4 步：边界（如果记忆服务暂时不可用，Path A/B/C 都可验）

- [ ] 我做：继续在 Obsidian 里向 AI 提问（即使后台的记忆服务暂时挂掉，你完全无感）
- [ ] 我看到：AI 照常回答（这次只是没有历史误解提醒，但回答本身正常）
- [ ] 我感觉：AI **不会卡住、不会弹出红色英文报错、不会显示"记忆服务不可用"**

### 主观打分（Felt-sense — Sean Ellis-lite）

- [ ] **被照顾感**（1=AI 完全不记得我学过什么 / 5=像有一个记得我功课的私教）：___
- [ ] **不打扰感**（1=反复念旧错让人烦 / 5=有分寸只在该提的时候提）：___
- [ ] **明天我会再打开它的可能性**（0-10 NPS-style）：___
- [ ] 一句话告诉 Claude，让你打这个分的最主要原因是：___

---

## 🚦 验收反馈

### 跑完后的 3 种反馈方式

| 你的情况 | 你说什么 | Claude 会怎么做 |
|---|---|---|
| 第 1-4 步全 ✅ | "**Story 2.3 通过**" | mark `done` + 启动 Story 5.1 BKT（CURRENT_TASK 8-Session plan S3） |
| 部分 ❌ | 在批注区写哪一步 + 实际现象（用 `Cmd+Shift+A` 批 `❌`） | 跑 `bmad-bmm-correct-course` 调整 |
| 想暂停 | "暂停 Story 2.3" | 状态保持 `review`，可随时回来 |

---

## 🤖 关于 `438666d` (Wave-5 Stage B follow-up `index.py`)

**为什么不需要你跑 UAT**：

| 维度 | 说明 |
|---|---|
| 改了什么 | `DELETE /api/v1/index/{vault_id}` 加 ContextVar 注入（防未来 silent 串库回归） |
| 业务逻辑 | **零变更** — `drop_vault_tables(vault_id)` 仍接 raw vault_id，behavior 完全一致 |
| 用户可见性 | **零** — 这是 backend admin endpoint，Obsidian plugin 端不调用此 endpoint |
| 触发场景 | 只有运维（curl/postman/admin script）才会触发，普通学习流程永远不到这条路径 |
| 已验收 | 35/35 单元测试 pass（3 新 + 32 现有零回归） |

**DoD-3 D3-B "60 岁照做"原则**：用户层 UAT 只验产品体验。这个 patch 完全在 backend 层，**用户透明** — 你打开 Obsidian 跑任何操作都不会感知它存在。

如果你**真的想验证它工作**（仅限好奇心），告诉 Claude "演示 wave-5 followup"，Claude 会跑 docker exec + curl 给你看 ContextVar 注入前后的 log 差异。

---

## 📍 我建议的下一步

按 Boris 工作流"设计先于代码"原则，**最 reasonable 的顺序**：

1. **立即跑 Path A**（3-5 min）— 验 AC #3/#4/#5，让你对 Story 2.3 的"边界与降级"有信心
2. **决定 Path B 还是 Path C**：
   - 想等 Story 2.5 plugin hook done 后跑真实路径 → 等 Path B 就绪（Story 2.5 后续 session）
   - 想现在就完整验 → 授权 Claude 走 Path C（1 min seed + 5-10 min UAT）
3. **不要跑 `438666d` UAT**（无用户可见行为）

---

## 🔗 技术参考（给 Claude 读的）

- Story 2.3 验收单（含完整段 4-A 21 项 Claude 代验）：`_bmad-output/验收单/Story-2.3-historical-error-reminder.md`
- Story spec：`_bmad-output/implementation-artifacts/epic-2/2-3-historical-error-reminder.md`
- 源代码：`backend/app/services/memory_service.py:search_error_memories` + `backend/app/services/chat_context_assembler.py:_format_historical_errors` + `backend/app/api/v1/endpoints/chat.py:historical_errors` + `backend/app/api/v1/endpoints/index.py:delete_vault_index`
- 测试：`backend/tests/unit/test_story_2_3_error_reminders.py`（21 用例）+ `backend/tests/unit/test_wave5_stageb_continued_vault_id_injection.py`（含 3 新 index endpoint 用例）
- Commits：`d9a7164` (Story 2.3) + `438666d` (Wave-5 Stage B followup)


**User：你这里关于我在 path B 使用原白板的过程，会在节点打下批注，你举的例子是我标记的这个批注是 error，那么关于批注本身以及批注怎么产出的原因是怎么记录下来的，关于批注的理解程度和熟练程度又是怎么记忆下来的，然后关于节点本身又是怎么记录下来的，然后节点和节点之间的双向链接关系又是怎么记录下来的，我需要明确知道你的后端是怎么运行的，以及你的后端中的 Graphiti 又是怎么运行的**