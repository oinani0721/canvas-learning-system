---
story: "CARD-A1"
title: "fsrs-new-card-none-fix"
status: "review"
version: "1"
date: "2026-08-24"
developer: "Claude Code (Fable 5)"
commit: "6a1c9a01"
---

# Story CARD-A1 验收单（给你看的版本）

> [!info]+ 这是什么
> 这是 CARD-A1（BATCH-2026-08-24-复习闭环 第一张卡）的用户验收文档，**给你（非技术）读的版本**。
> 技术档案在 `_bmad-output/implementation-artifacts/goal-cards/2026-08-24-第一批小goal卡-复习闭环.md` 的 CARD-A1 节（Claude 读的）。
> 这份文档里没有技术术语，只有你能看到、摸到、点击的行为。

---

## 🎯 这个 Story 要做到什么

修好一个隐蔽的老毛病：**每一个你新加进白板、还没复习过的概念，记忆系统都会悄悄放弃对它做智能排期**，退回到最原始的固定周期表——而且不报错、不提示，表面一切正常。修好后，新概念从第一天起就用和老概念一样的智能记忆算法来安排复习。

---

## 📖 用户故事（你的视角）

**作为** 用白板管理学习的学生，
**我想** 新加的概念从一开始就被记忆系统认真对待、按我的真实记忆状态安排复习，
**以便** 不会出现「新学的东西反而被系统用最笨的方式排期」这种暗坑。

---

## 🖥️ 你会看到的交互（一步一步）

```
1. 你在白板里新建一个概念（像平时一样，什么都不用多做）
       ↓
2. 系统在后台第一次「认识」这个概念时，不再悄悄出错
       ↓
3. 这个概念从第一次复习起就走智能排期（和老概念同一套算法）
       ↓
4. 你在复习清单里看到它按正常节奏出现，不多不少
```

（这张卡是纯后台修复：你的界面不会长出新按钮，变化发生在「看不见但一直在跑」的排期引擎里。）

---

## 🤖 Claude 已代验（你不用跑，给你看证据用）

> [!success]+ 这一段是 Claude 自动跑完贴证据
> **你不用跑也不用懂**。出现以下任何关键词不算 bug，是 Claude 应该处理的：`curl` / `docker` / `HTTP 200` / `JSON` / `schema` / `:端口号` / `pytest` / `endpoint` / `.env`。
> 你只看右边"结果"列是不是 ✅。

| # | 技术验证项 | 结果 |
|---|---|---|
| 1 | 新增回归测试先跑确认「4 个崩溃点全红」（真实 fsrs 6.3.1 库对象，零 mock） | ✅ 修复前 4 failed / 2 passed，全部命中预期 TypeError |
| 2 | 修复后新增回归测试全绿（真实库 fail-closed 门禁 / serialize roundtrip / card_to_state / get_fsrs_state found=True / schedule_review algorithm=="fsrs-4.5"） | ✅ 7 passed |
| 3 | 裁判命令全绿：`pytest tests/regression/test_fsrs_new_card_none_serialization.py tests/unit/test_fsrs_manager.py tests/unit/test_fsrs_state_query.py tests/unit/test_story_38_3_fsrs_init_guarantee.py tests/unit/test_review_service_fsrs.py tests/regression/test_fsrs_bridge.py -q` | ✅ 128 passed（修复前基线 121 + 新增 7；加 API 契约文件超集 140 passed） |
| 4 | 冒烟：真实新卡序列化输出 JSON，`stability/difficulty` 是 `null` 而非写死 `0.0` | ✅ `{"due": "...", "stability": null, "difficulty": null, "state": 1, ...}` |
| 5 | None 语义分层核验：持久化 JSON 保 null 可 roundtrip；API 展示字段走 Story 38.3 AC-4 默认卡契约（stability=1.0, difficulty=5.0）；概念熟练度存储沿用其既有 `0.0=未学` 约定 | ✅ 回归测试逐层断言锁定 |
| 6 | 靠本 bug 维持绿灯的旧断言（found=False，与 Story 38.3 AC-4 矛盾）已修正并注明原因 | ✅ tests/unit/test_fsrs_state_query.py 更新 |
| 7 | ruff lint 全绿；改动范围仅卡片档案列出的 5 个文件 | ✅ All checks passed!（注：整文件格式化漂移为存量问题，未混入本卡） |
| 8 | Codex 独立交叉审查（gpt-5.6-sol，ultra 档，只读沙箱）：0 BLOCKER / 3 HIGH / 2 MEDIUM | ✅ 5 条全部处置（HIGH-1/3 与两条 MEDIUM 代码修复；HIGH-2 实测根因 + 测试隔离 + 移交下批），处置后裁判命令复跑 128 passed，详见 `_bmad-output/审查/codex-review-CARD-A1.md` 处置记录 |
| 9 | Git commit 含批次标记 BATCH-2026-08-24-复习闭环 / CARD-A1，未 push | ✅ commit `6a1c9a01`（核心修复+测试）+ 审查修复收尾 commit（含审查存档+验收单） |

---

## 👤 你来验（产品使用体验 — 1 步，1 分钟内完成）

> [!warning]+ 说明
> 这张卡是**纯后台修复**，界面上没有新东西可点。它的效果（新概念第一天就进智能排期）要等这批卡合并、白天部署后，在日常复习清单里逐渐体现。所以你这次只需要做一个「没坏」检查：

### 第 1 步：日常使用无感知异常

- [ ] 我像平时一样打开 Obsidian，看一眼今天的复习清单
- [ ] 我看到清单正常显示，数量没有突然暴涨或清零
- [ ] 我感觉一切如常（如果有任何突兀的变化，写在批注区）

### 主观打分（不是必填）

- [ ] **信任度**（1=担心系统在偷偷出错 / 5=放心交给它排期）：___
- [ ] 一句话告诉 Claude 你的感受：___

---

## 🚦 验收结果

**如果上面 ✅**：告诉我 "**CARD-A1 通过**"，这张卡标记完成，等待白天由你决定是否合并回主分支。

**如果有 ❌**：在下面批注区写出具体现象，Claude 根据你的反馈调整。

---

## 📝 你的批注区

> [!question]+ 你对 CARD-A1 的批注
>
> 在这里写任何疑问/建议/不满意。或者直接用 `Cmd+Shift+A` 批注上面任何一段。
>
> （空）

### 已知的已批注问题（历史追溯）

无（首次 ship）。

---

## 🔗 技术 spec 参考（给 Claude 读的，不是给你读的）

- **卡片档案**：`_bmad-output/implementation-artifacts/goal-cards/2026-08-24-第一批小goal卡-复习闭环.md` § CARD-A1
- **源代码**：
  - `backend/lib/memory/temporal/fsrs_manager.py`（serialize/deserialize/card_to_state None 语义）
  - `backend/app/services/review_service.py`（schedule_review 日志格式化 + get_fsrs_state 展示层默认值）
  - `backend/app/services/mastery_engine.py`（_fsrs_update 同款加固）
- **单元测试**：`backend/tests/regression/test_fsrs_new_card_none_serialization.py`（6 用例 / 100% 通过）+ 裁判命令 6 文件 127 passed
- **Git commit**：`6a1c9a01` — fix(fsrs): serialize new-card None as JSON null, stop silent Ebbinghaus fallback
- **完成判据 → 代码对应**：
  - 判据 #1（serialize roundtrip）→ `backend/lib/memory/temporal/fsrs_manager.py:274-341`
  - 判据 #1（card_to_state）→ `backend/lib/memory/temporal/fsrs_manager.py:345-385`
  - 判据 #1（found=True）→ `backend/app/services/review_service.py:2195-2210`
  - 判据 #1（algorithm=="fsrs-4.5"）→ `backend/app/services/review_service.py:838-870`
  - 判据 #2（矛盾断言修正）→ `backend/tests/unit/test_fsrs_state_query.py:186-249`
- **已知不修**（列入第二批候选）：
  - `fsrs_manager.py` 历史 `state:0` 数据在 fsrs v6 反序列化会抛 ValueError（State(0) 已不存在）
  - Graphiti 学习记忆镜像写侧断裂管道（`review_service.py:2055/2156` 调不存在的 `add_learning_memory`；Codex HIGH-2 定位，真修需动 `neo4j_edge_client.py` schema，超本卡白名单；文件持久化主通道正常，失败有计数器观测）
  - Story 38.3 AC-4 的 `state=New(0)` 措辞在 fsrs 6.x 下已不可达（v6 新卡即 Learning=1），建议随下张 FSRS 卡更新契约文字
  - 仓库存量 ruff format 漂移（HEAD 未改文件即过不了格式门；本卡未混入格式化变更）

---

## 📅 下一步（你批完这份单后）

1. **✅ 通过** → 说 "CARD-A1 通过" → 标记完成，白天你决定是否合并
2. **❌ 有问题** → 在批注区写清楚 → Claude 修正后更新此单 v2
3. **想暂停** → 说 "暂停 CARD-A1"，状态保持 review，可随时回来
