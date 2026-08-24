---
story: "CARD-A2"
title: "复习到期口径统一"
status: "review"
version: "1"
date: "2026-08-24"
developer: "Claude Code (Fable 5)"
commit: "card/a2-projection 分支（BATCH-2026-08-24-复习闭环 / CARD-A2）"
---

# CARD-A2 验收单（给你看的版本）

> [!info]+ 这是什么
> 这是 CARD-A2「到期数字打架」修复的用户验收文档，**给你（非技术）读的版本**。
> 技术档案在 `_bmad-output/implementation-artifacts/goal-cards/2026-08-24-第一批小goal卡-复习闭环.md` 的 CARD-A2 节（Claude 读的）。

---

## 🎯 这个卡要做到什么

Dashboard 说今天到期 13 个、每日推荐说 6 个——两边各算各的。修完后**全系统只有一个裁判**：每日推荐脚本算一次，Dashboard 直接读它的结果，所有地方显示同一个数字；还没写定义的占位节点单独列成「待剖析积压」，不再糊进到期数里。

---

## 📖 用户故事（你的视角）

**作为** 每天早上看 Dashboard 决定复习什么的学习者，
**我想** Dashboard 上的到期数字和手机推送、今日复习清单完全一致，
**以便** 我不用怀疑哪个数字是真的，也能一眼看到哪些节点还欠着定义没写。

---

## 🖥️ 你会看到的交互（一步一步）

```
1. 早上 9:05 后打开 Obsidian，点开 Dashboard
       ↓
2. 「⏰ FSRS 到期」显示一个数字 + 这个数字是几点几分算出来的
       ↓
3. 数字下方（若有欠账）出现「🗂️ 待剖析积压」一行，
   点名列出还没写定义的占位节点，点击可直接跳过去补
       ↓
4. 打开 outputs/今日复习 页面对照 —— 到期数字和 Dashboard 一致
```

---

## 🤖 Claude 已代验（你不用跑，给你看证据用）

> [!success]+ 这一段是 Claude 自动跑完贴证据
> **你不用跑也不用懂**。出现以下任何关键词不算 bug，是 Claude 应该处理的：`pytest` / `JSON` / `schema` / `grep` / `git`。
> 你只看右边"结果"列是不是 ✅。

| # | 技术验证项 | 结果 |
|---|---|---|
| 1 | 回归测试先红后绿：新增 5 个测试覆盖全部 5 类口径分歧节点 + 到期边界（恰好等于当前时刻 / 一小时后 / 本地时区表示）+ 空库契约 + NaN 溢出防护，改前确认失败、改后 `pytest tests/regression/test_daily_review_pick.py -q` 15 passed | ✅ 15 passed |
| 2 | payload schema v2→v3 纯加性：既有字段一个未改名未删（推送链 daily_review_run.py / send_bark.py 只读 notification，被动兼容），新增 due_nodes 明细 + ineligible 分桶 | ✅ 加性守卫测试锁定 |
| 3 | 数字与明细自洽：stats.due_nodes 直接由 due_nodes 明细长度派生，靠构造保证不再漂移；三个分桶长度==stats 计数逐一断言 | ✅ len==stats 断言过 |
| 4 | Dashboard 独立重算已删除：`grep -c "schedCnt\|newCnt" canvas-vault/Dashboard.md` == 0；`grep -c "今日复习.json"` == 5 | ✅ 0 / 5 |
| 5 | 真实 vault 冒烟：worktree 副本跑生成脚本，schema_version=3、due=2 与明细一致、占位积压 1 张点名、测试节点 4 张单独成桶 | ✅ 自洽 True |
| 6 | JSON 缺失/损坏降级：Dashboard 三条降级路径（文件缺失 / 内容损坏 / 旧版格式）各显示灰色提示文案，其余 3 个指标照常渲染不白屏；未归板节点单独"另计"不再静默消失 | ✅ 代码路径核验 |
| 7 | 三视角对抗验证（3 个独立 agent 并行审 schema 加性 / Dashboard 降级 / 测试充分性）：0 BLOCKER、0 HIGH，2 MEDIUM 已修（未归板另计 + 到期边界锁定），LOW 项已修 4 条、其余记录在案 | ✅ 全部处理 |
| 8 | Codex 交叉审查（gpt-5.6-sol，ultra 档，只读沙箱）：初审 0 BLOCKER / 2 HIGH / 3 MEDIUM，全部 5 条已修复并重跑裁判全绿（NaN 防护、结构校验、脏日期分类、日历非法值、时区边界测试），处置记录见 `_bmad-output/审查/codex-review-CARD-A2.md` 附录 A | ✅ 5/5 已处置 |
| 9 | 硬边界遵守：未碰 backend/lib/memory/、review_service.py（A1 地盘）、daily_review_run.py（A3 地盘）；测试只 assert dict | ✅ diff 仅 3 文件 |

---

## 👤 你来验（产品使用体验 — 3 步，3 分钟内全在 Obsidian 里完成）

> [!warning]+ 前提
> 下面的体验要等「live vault 部署」（见下一节）执行后才能在你日常用的库里看到。部署前想先睹为快，可以让 Claude 把开发副本的 Dashboard 展示给你。

### 第 1 步：到期数字只有一个了

- [ ] 我打开 Obsidian 的 Dashboard 页面
- [ ] 我看到「⏰ FSRS 到期」是一个数字，后面括号里写着"投影生成于 某年某月某日几点"
- [ ] 我感觉这个数字终于有出处了，不再是凭空冒出来的

### 第 2 步：两边数字对得上

- [ ] 我打开 outputs 文件夹里的「今日复习」页面，看顶部的"到期="数字
- [ ] 我看到它和 Dashboard 上的到期数字**完全一样**
- [ ] 我感觉系统各处终于说的是同一件事，可信

### 第 3 步：欠的定义账单独列出来了

- [ ] 我在 Dashboard 到期数字下方看到「🗂️ 待剖析积压」一行（如果我有还没写定义的占位节点）
- [ ] 我点其中一个名字，直接跳到那张节点，能看到它还是"你的 1-2 句精准定义"的占位状态
- [ ] 我感觉欠的账清清楚楚，不会再混进"今天要复习"的数字里吓我一跳

### 第 4 步：边界（如果清单还没生成会怎样）

- [ ] 早上 9:05 之前（当天清单还没自动生成时）打开 Dashboard
- [ ] 我看到「⏳ 投影未生成」的灰色提示，告诉我几点会自动生成
- [ ] 不会闪退 / 不会白屏 / 不会出现红色英文报错

### 主观打分（不是必填，但能帮 Claude 判断）

- [ ] **数字可信度**（1=还是不敢信 / 5=完全信）：___
- [ ] **待剖析积压这个信息对你有用吗**（1=多余 / 5=正好想要）：___
- [ ] 一句话告诉 Claude 打分原因：___

---

## 🚨 live vault 部署待用户确认（重要）

> [!warning]+ 这次改动只落在开发副本，你日常用的库还没动
> 按纪律，Claude 本轮**只改了开发副本**（worktree）里的 Dashboard 和生成脚本，**没有碰**你日常使用的 `canvas-learning-system/canvas-vault/`。
>
> 所以现在你日常库里的 Dashboard 还是旧的两套算法。**等你白天说一句"可以部署"**，再单独执行：
> 1. 把新版 Dashboard.md 复制到你日常用的库；
> 2. 重新生成一次当天的今日复习清单（让新版数据格式落地）；
> 3. 两处数字当场对一遍给你看。
>
> 不确认就永远不会动你的日常库。

---

## 🚦 验收结果

**如果所有步骤 ✅**：告诉我 "**CARD-A2 通过**"，本卡 mark done，串行的下一张卡 A3（当天重学卡刷新）才能开工——它要用本卡定好的数据格式。

**如果有任何一步 ❌**：在下面批注区写出具体哪一步 + 你看到的实际现象。

---

## 📝 你的批注区

> [!question]+ 你对 CARD-A2 的批注
>
> 在这里写任何疑问/建议/不满意。或者直接用 `Cmd+Shift+A` 批注上面任何一段。
>
> （空）

### 已知的已批注问题（历史追溯）

无（首次 ship）。

---

## 🔗 技术 spec 参考（给 Claude 读的，不是给你读的）

- **卡片档案**：`_bmad-output/implementation-artifacts/goal-cards/2026-08-24-第一批小goal卡-复习闭环.md` CARD-A2 节
- **源代码**：
  - `scripts/daily_review_pick.py`（schema v3：due_nodes 明细 + ineligible 分桶，scan_nodes 三桶点名）
  - `canvas-vault/Dashboard.md`（FSRS 块改投影消费 + 三降级路径 + 待剖析积压段）
- **回归测试**：`backend/tests/regression/test_daily_review_pick.py`（15 用例 / 全过；新增 5 个：5 类分歧全覆盖 + 到期边界锁定、v2 契约加性守卫、空库契约键恒在、NaN 溢出进 corrupt 桶、本地时区边界不漂移）
- **审查存档**：`_bmad-output/审查/codex-review-CARD-A2.md`
- **完成判据 → 代码对应**：
  - 判据 (1) schema v3 加性 → scripts/daily_review_pick.py:build_payload
  - 判据 (2) Dashboard 消费投影 → canvas-vault/Dashboard.md「三大核心指标」块
  - 判据 (3) 5 类分歧测试 → test_daily_review_pick.py:test_projection_v3_due_nodes_and_ineligible_buckets

---

## 📅 下一步（你批完这份单后）

1. **全部 ✅ 且说"可以部署"** → Claude 执行 live vault 部署三步 + 当场对数
2. **部分 ❌** → 在批注区写清楚，Claude 修正后更新本单 v2
3. **A3 排队中** → 本卡合入后才开工（数据格式依赖）
