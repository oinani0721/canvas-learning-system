---
story: "CARD-C4"
title: "fake-graphiti-mirror-decommission"
status: "review"
version: "1"
date: "2026-08-25"
developer: "Claude Code (Fable 5)"
commit: "d23c6dc3"
---

# Story CARD-C4 验收单（给你看的版本）

> [!info]+ 这是什么
> 这是 CARD-C4（BATCH-2026-08-25-跨vault与收束 · 车道 2 第二张卡）的用户验收文档，**给你（非技术）读的版本**。
> 技术档案在 `_bmad-output/implementation-artifacts/goal-cards/2026-08-25-第二批小goal卡-跨vault与收束.md` 的 CARD-C4 节（Claude 读的）。
> 这份文档里没有技术术语，只有你能看到、摸到、点击的行为。

---

## 🎯 这个 Story 要做到什么

让系统不再对自己说谎：勘探实锤，复习系统里有一段代码**声称**"已把你的复习状态存入长期记忆图谱"——但它调用的那个存储方法**从系统诞生起就从未存在过**，底层也根本不是记忆图谱而是一个本地文件，且这类复习状态记录**从来没有成功存进去过一条**：每次失败都被悄悄吞掉、返回值却始终报"成功"，源码里还留着一句永远走不到的"存储成功"日志。这张卡把这段说谎的代码安全下线：删掉假动作、改掉假话术，顺手把"文件保存失败也谎报成功"的老毛病一起治了（审查员揪出来的），**真实在用的读取功能一行不动**。将来真要接记忆图谱，等主干工程就位后用一张新卡光明正大地接。

---

## 📖 用户故事（你的视角）

**作为** 依赖这套系统安排每日复习的学生，
**我想** 系统日志和系统行为完全一致——说存了就是真存了，没存就明说，
**以便** 我能信任它报告的每一句话，不会在未来某天发现"以为存了五个月的记录其实是空的"。

---

## 🖥️ 你会看到的交互（一步一步）

```
1. 你像平时一样复习、评分（什么都不用多做）
       ↓
2. 复习状态照常保存（真实通道从来是本地文件，这次没变）
       ↓
3. 系统不再产生"已存入记忆图谱"的假消息
       ↓
4. 你日常的复习清单、历史记录、掌握度显示全部照旧
```

（这张卡是纯诚实性修复：删的全是"从未成功过的假动作"，你的任何数据和日常体验零变化。）

---

## 🤖 Claude 已代验（你不用跑，给你看证据用）

> [!success]+ 这一段是 Claude 自动跑完贴证据
> **你不用跑也不用懂**。出现以下任何关键词不算 bug，是 Claude 应该处理的：`grep` / `pytest` / `JSON` / `warning`。
> 你只看右边"结果"列是不是 ✅。

| # | 技术验证项 | 结果 |
|---|---|---|
| 1 | 幻影调用删除：两处调用"从未存在的方法"的代码、每次必失败的后台任务、永远查不到数据的读取死块、无人看的失败计数器——全部下线 | ✅ 约 130 行假动作移除 |
| 2 | 裁判 grep 双清零：幻影方法名在后端业务代码 0 命中；"已存入/读自 Graphiti"虚假日志 0 命中（修复前基线 2 + 4 处） | ✅ 双零 |
| 3 | 真实在用的读路径一行未动：get_learning_history 的全部调用与存储客户端本体保留（下线前逐一核对调用方；Codex 审查维度 1 独立确认 PASS——历史读取五处、memory 端点链、真实边写全部与改前逐字节一致） | ✅ 双重验证 |
| 4 | 五个测试文件适配后 0 fail（goal 指定 3 个 + 存量套件里锁着已删行为的第 4/5 个）；防复活测试锁 4 个（计数器 / 后台任务 / load-save 零外部访问 / 文件失败诚实返回） | ✅ 裁判 3 文件 + A1 契约 = 69 passed；38.3 两文件 32 passed |
| 5 | 冒烟（档案判据④）：新概念查询复习状态 → 正常自动建卡、无任何持久化失败警告、本地文件通道真实写入 1 条 | ✅ found=True，日志干净 |
| 6 | 处置记录写入 `docs/known-gotchas.md` G-FAKE-007（含"真接 Graphiti 须等 epic-5a C-1/C-2 契约"防复发条款）+ 统计表更新 | ✅ 已记录 |
| 7 | 附带修复（Codex HIGH-1）：文件保存失败时不再谎报成功——保存结果如实返回，不可写目标回归测试锁定 | ✅ 最小闭环，不动禁区 |
| 8 | ruff lint 全绿 | ✅ All checks passed! |
| 9 | Codex 独立交叉审查（gpt-5.6-sol，ultra 档，只读沙箱，重点审"是否误删真实在用的读路径"）：0 BLOCKER + 1 HIGH + 3 MEDIUM + 3 LOW | ✅ BLOCKER/HIGH 清零（HIGH-1 与全部 MEDIUM/LOW 处置完毕），详见 `_bmad-output/审查/codex-review-CARD-C4.md` 处置记录 |
| 10 | Git commit 含批次标记 BATCH-2026-08-25-跨vault与收束 / CARD-C4，未 push | ✅ commit `d23c6dc3`（核心下线+测试+gotcha）+ 收尾 commit（审查存档+验收单） |

---

## 👤 你来验（产品使用体验 — 1 步，1 分钟内完成）

> [!warning]+ 说明
> 这张卡删的是**从未成功过的假动作**，你的界面和数据零变化。所以你只需要做一个「没坏」检查：

### 第 1 步：日常使用无感知异常

- [ ] 我像平时一样打开 Obsidian，答一道题并让系统评分
- [ ] 我看到评分流程照常走完，复习清单和掌握度显示都和昨天一样
- [ ] 我感觉系统一切如常，甚至更踏实了——它不再对我报假喜（有任何突兀变化写批注区）

### 主观打分（不是必填）

- [ ] **信任度**（1=不知道它还在哪说谎 / 5=报什么信什么）：___
- [ ] 一句话告诉 Claude 你的感受：___

---

## 🚦 验收结果

**如果上面 ✅**：告诉我 "**CARD-C4 通过**"，这张卡标记完成，车道 2 两卡收官。

**如果有 ❌**：在下面批注区写出具体现象，Claude 根据你的反馈调整。

---

## 📝 你的批注区

> [!question]+ 你对 CARD-C4 的批注
>
> 在这里写任何疑问/建议/不满意。或者直接用 `Cmd+Shift+A` 批注上面任何一段。
>
> （空）

### 已知的已批注问题（历史追溯）

无（首次 ship）。

---

## 🔗 技术 spec 参考（给 Claude 读的，不是给你读的）

- **卡片档案**：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/2026-08-25-第二批小goal卡-跨vault与收束.md` § CARD-C4（档案在主开发 worktree，本 worktree 无副本）
- **源代码**：`backend/app/services/review_service.py`
  - `load_card_state`：读侧死块（原 :1981-2014，永远 None——canonical schema 从不承载 card_data）删除，只留内存缓存 + 文件通道
  - `save_card_state`：幻影写块（原 :2046-2079，含 :2065 幻影调用）删除；返回值改为如实反映文件通道结果（Codex HIGH-1）
  - `_save_card_states`：返回 bool（捕获模式零变化，只暴露结果）
  - `get_fsrs_state`：`_persist_auto_created_card` fire-and-forget 后台任务（原 :2142-2184，含 :2166 幻影调用）删除
  - `__init__`：`_auto_persist_failures` 计数器（原 :309）删除；孤儿 `contextvars` import 删除
  - **保留**：`get_learning_history` 读调用（:1137/:1362/:1616/:1717/:1882 + memory endpoint 链）、LearningMemoryClient 本体、`self.graphiti_client` 其余真实用途（边写 :1437-1448/历史查询）——Codex 维度 1 逐字节核对 PASS
- **测试**：
  - `tests/unit/test_fsrs_state_query.py`：`_get_state_cancelling_bg` 防御帮助函数删除（防御对象已不存在），4 处调用改直接 await；新增 `test_get_fsrs_state_spawns_no_background_tasks` 防复活锁
  - `tests/unit/test_review_service_fsrs.py`：`TestAutoPersistFailureCounter` → `TestAutoPersistCounterRemoved`（计数器移除断言 + load/save 零外部访问锁 + 文件失败返回 False 锁）
  - `tests/integration/test_review_singleton_di.py`：计数器存在断言翻转为移除断言
  - `tests/unit/test_story_38_3_fsrs_init_guarantee.py`：原"锁定必须派生后台任务"两用例翻转为防复活锁（只 patch create_task，文件通道真实执行）
  - `tests/unit/test_story_38_3_edge_cases.py`：load_card_state mock 补 `assert_awaited_once_with`（Codex LOW-2）
- **裁判命令**：
  - `grep -rn "add_learning_memory" backend/app` → 0 命中（基线 2）
  - `grep -rn "card state to Graphiti\|card state from Graphiti" backend/app` → 0 命中（基线 4）
  - `cd backend && .venv/bin/pytest tests/unit/test_fsrs_state_query.py tests/unit/test_review_service_fsrs.py tests/integration/test_review_singleton_di.py -q` → 0 fail（goal 指定 3 文件）
  - 扩展验证：+ test_story_38_3_fsrs_init_guarantee.py + test_story_38_3_edge_cases.py + A1 契约文件 → 0 fail
- **Gotcha 登记**：`docs/known-gotchas.md` G-FAKE-007（双重假实锤 + 处置 + 防复发规则）
- **Codex 审查存档**：`_bmad-output/审查/codex-review-CARD-C4.md`
- **Git commit**：`d23c6dc3` — refactor(review): decommission phantom Graphiti card-state mirror

---

## 📅 下一步（你批完这份单后）

1. **✅ 通过** → 说 "CARD-C4 通过" → 车道 2（C3+C4）收官，白天你决定是否合并
2. **❌ 有问题** → 在批注区写清楚 → Claude 修正后更新此单 v2
3. **想暂停** → 说 "暂停 CARD-C4"，状态保持 review，可随时回来
