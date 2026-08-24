---
story: "CARD-C3"
title: "fsrs-legacy-state-zero-fix"
status: "review"
version: "1"
date: "2026-08-25"
developer: "Claude Code (Fable 5)"
commit: "afa1cb1c"
---

# Story CARD-C3 验收单（给你看的版本）

> [!info]+ 这是什么
> 这是 CARD-C3（BATCH-2026-08-25-跨vault与收束 · 车道 2 第一张卡）的用户验收文档，**给你（非技术）读的版本**。
> 技术档案在 `_bmad-output/implementation-artifacts/goal-cards/2026-08-25-第二批小goal卡-跨vault与收束.md` 的 CARD-C3 节（Claude 读的）。
> 这份文档里没有技术术语，只有你能看到、摸到、点击的行为。

---

## 🎯 这个 Story 要做到什么

拆掉一颗还没爆的历史数据雷：**老版本记忆系统存的复习记录里有一种"状态 0"标记，新版算法读到它会直接崩掉**。现在你的数据里恰好一条都没有，但只要以后任何一条老记录、老备份或者外部导入的数据带着这个标记进来，复习引擎就会当场报错。修好后，系统读到这种老标记会自动把它翻译成新版的对应说法（"刚开始学"），复习照常进行，一条记录都不会丢。

---

## 📖 用户故事（你的视角）

**作为** 用白板管理学习的学生，
**我想** 不管是新记录还是多年前的老记录，复习系统都能认得并正常安排，
**以便** 永远不会因为"数据太老"这种我控制不了的原因，让复习功能突然坏掉。

---

## 🖥️ 你会看到的交互（一步一步）

```
1. 你像平时一样复习、评分（什么都不用多做）
       ↓
2. 如果某条记录是老版本格式，系统在读它的瞬间悄悄翻译成新格式
       ↓
3. 这条记录的复习次数、到期日等信息全部保留，排期继续
       ↓
4. 你在复习清单里完全感觉不到新老记录的区别
```

（这张卡是纯后台拆雷：界面没有任何变化，拆的是"还没爆但迟早爆"的雷。）

---

## 🤖 Claude 已代验（你不用跑，给你看证据用）

> [!success]+ 这一段是 Claude 自动跑完贴证据
> **你不用跑也不用懂**。出现以下任何关键词不算 bug，是 Claude 应该处理的：`pytest` / `JSON` / `ValueError` / `State` / `deserialize`。
> 你只看右边"结果"列是不是 ✅。

| # | 技术验证项 | 结果 |
|---|---|---|
| 1 | 官方语义查证（DD-01/DD-04）：Context7 查 py-fsrs 官方文档 + venv 实测——fsrs 6.x 的 State 枚举只剩 Learning(1)/Review(2)/Relearning(3)，官方定义 "Learning == new card being studied for the first time"，`State(0)` 实测抛 `ValueError: 0 is not a valid State` | ✅ legacy 0(New) 的唯一合法映射 = Learning(1) |
| 2 | 先红后绿两轮：第一轮新建独立回归文件 `tests/regression/test_fsrs_legacy_state_zero.py` 红 7 failed 全命中缺陷点；Codex 审查揪出 BLOCKER 后第二轮扩到 14 用例（新 5 个再红）再全绿 | ✅ 两轮红-绿链完整 |
| 3 | 裁判命令全绿：`pytest tests/regression/test_fsrs_legacy_state_zero.py tests/regression/test_fsrs_new_card_none_serialization.py tests/unit/test_fsrs_manager.py tests/regression/test_fsrs_bridge.py -q` | ✅ 68 passed（A1 契约文件零回归） |
| 4 | 复现一行命令翻绿：deserialize `state:0` 从 `ValueError: 0 is not a valid State` 翻为输出 `<State.Learning: 1>`，且 reps/due 等字段保留 | ✅ 实测输出 `<State.Learning: 1>` |
| 5 | 字段级迁移全链（Codex BLOCKER 处置）：canonical legacy 形状（状态 0 + 参数哨兵 0.0）读入 → 参数归一 → **真实调度器复习不再崩** → 落盘为合法新格式；矛盾形状（状态 0 但带正参数）保留参数 + 显式告警 | ✅ 全链实测走通（复习后 stability 2.3065） |
| 6 | 写侧全口封死：serialize_card / card_to_state / CardState 默认值与读写 / fallback 分支（含屏蔽库的隔离子进程实测）——任何路径不再产出 state=0 | ✅ 6 用例锁定 |
| 7 | fsrs_bridge（评分写侧）字段级防御：老标记 `fsrs_state: 0` 及其伴生哨兵字段（0/0.0/null）全部归一，不抛错、真实调度走通、与"刚开始学"语义一致；含 stdin CLI 实际调用形态回归 | ✅ 5 用例（真实 frontmatter 解析 + re-exec 链） |
| 8 | roundtrip 例外显式标注：deserialize_card docstring 注明字段级迁移系对 CARD-A1 严格 roundtrip 的显式例外 + 版本归因准确（legacy=py-fsrs v3/fallback，v4+ 已三态） | ✅ docstring + 写侧注释 |
| 9 | ruff lint 全绿；C4 三个裁判测试文件预跑 60 passed + 38.3 相关套件回归（本卡对相邻地盘零破坏） | ✅ All checks passed! |
| 10 | Codex 独立交叉审查（gpt-5.6-sol，ultra 档，只读沙箱）：1 BLOCKER + 2 HIGH + 3 MEDIUM + 1 LOW | ✅ BLOCKER/HIGH 清零（BLOCKER-1/HIGH-1/HIGH-2 代码修复 + 二轮测试锁定；MEDIUM-1/3 与 LOW 修复；MEDIUM-2 超范围移交后续卡），处置后裁判复跑 68 passed，详见 `_bmad-output/审查/codex-review-CARD-C3.md` 处置记录 |
| 11 | Git commit 含批次标记 BATCH-2026-08-25-跨vault与收束 / CARD-C3，未 push | ✅ commit `afa1cb1c`（核心修复+测试）+ 收尾 commit（审查存档+验收单） |

---

## ⏸️ 待你确认节：桥接脚本的正式部署

> [!warning]+ 这一步 Claude 故意没做，等你点头
> 本卡改了评分桥接脚本（`fsrs_bridge.py`）的**开发副本**（在这条开发车道的隔离目录里）。你日常真正在用的那两份副本（live vault 一份、主仓一份）**没有动**——按批次纪律，凡是碰你日常环境的部署一律等你确认。
>
> **你确认后 Claude 会做的事**：把改好的脚本复制到两个正式位置（一条命令的事，不影响任何笔记内容）。
> **不部署的影响**：你日常评分完全不受影响（正式副本里目前也没有"状态 0"数据）；只是这颗雷在正式环境还没拆。
>
> - [ ] 我同意把拆雷后的脚本部署到正式环境（回复 "C3 部署" 即可）
> - [ ] 我想先等这批卡全部验收完一起部署

---

## 👤 你来验（产品使用体验 — 1 步，1 分钟内完成）

> [!warning]+ 说明
> 这张卡是**纯后台拆雷**，界面上没有新东西可点，你的数据里现在也没有会触雷的老记录。所以你只需要做一个「没坏」检查：

### 第 1 步：日常使用无感知异常

- [ ] 我像平时一样打开 Obsidian，答一道题并让系统评分
- [ ] 我看到评分流程和之前一样顺畅走完，没有多出报错或卡顿
- [ ] 我感觉一切如常，安心（如果有任何突兀的变化，写在批注区）

### 主观打分（不是必填）

- [ ] **放心度**（1=担心老数据哪天炸雷 / 5=相信新老数据都稳）：___
- [ ] 一句话告诉 Claude 你的感受：___

---

## 🚦 验收结果

**如果上面 ✅**：告诉我 "**CARD-C3 通过**"（想连部署一起做就说 "C3 通过 + 部署"）。

**如果有 ❌**：在下面批注区写出具体现象，Claude 根据你的反馈调整。

---

## 📝 你的批注区

> [!question]+ 你对 CARD-C3 的批注
>
> 在这里写任何疑问/建议/不满意。或者直接用 `Cmd+Shift+A` 批注上面任何一段。
>
> （空）

### 已知的已批注问题（历史追溯）

无（首次 ship）。

---

## 🔗 技术 spec 参考（给 Claude 读的，不是给你读的）

- **卡片档案**：`_bmad-output/implementation-artifacts/goal-cards/2026-08-25-第二批小goal卡-跨vault与收束.md` § CARD-C3
- **源代码**：
  - `backend/lib/memory/temporal/fsrs_manager.py`（deserialize_card 读取层 0→Learning 映射 + docstring 例外标注；serialize_card/card_to_state 写侧 else 兜底 0→1）
  - `canvas-vault/.claude/scripts/fsrs_bridge.py`（review() 内 frontmatter fsrs_state:0 防御映射；仅 worktree 副本，live 双副本部署待确认）
- **测试**：
  - `backend/tests/regression/test_fsrs_legacy_state_zero.py`（新建，14 用例：canonical 全链 + 矛盾形状告警 + 合法态不受例外影响 + roundtrip 改写 + 写侧封口×3 + CardState + fallback 隔离子进程 + bridge×4 + 真实库门禁）
  - `backend/tests/regression/test_fsrs_bridge.py`（增 2 例：frontmatter 真实解析路径 + stdin CLI legacy 全链）
- **裁判命令**：`cd backend && .venv/bin/pytest tests/regression/test_fsrs_legacy_state_zero.py tests/regression/test_fsrs_new_card_none_serialization.py tests/unit/test_fsrs_manager.py tests/regression/test_fsrs_bridge.py -q` → 68 passed
- **已知不修（列入后续卡候选，Codex MEDIUM-2 及附注）**：
  - review_service/schemas API 展示层的 state 0 兜底与 "0=New" 描述（超 C3 白名单；`ConceptState.fsrs_state=0` 是"无 card_data"独立哨兵，Codex 维度 3 确认不宜本卡盲改）
  - fallback serialize_card 不支持 datetime due 的既有缺陷（与 state 无关）
  - 缺库 fail-closed（直接走 Ebbinghaus 不再生成 fallback 卡）需动 review_service 工厂，归未来"静默降级根治"卡
- **复现命令（翻绿证明）**：`cd backend && .venv/bin/python -c "import sys; sys.path.insert(0, 'lib'); from memory.temporal.fsrs_manager import FSRSManager; print(repr(FSRSManager().deserialize_card('{\"state\": 0, \"reps\": 2}').state))"` → 修复前 `ValueError: 0 is not a valid State`，修复后 `<State.Learning: 1>`
- **Codex 审查存档**：`_bmad-output/审查/codex-review-CARD-C3.md`
- **Git commit**：`afa1cb1c` — fix(fsrs): migrate legacy state:0 records field-level to Learning
- **待确认部署**：live vault 与主仓的 `canvas-vault/.claude/scripts/fsrs_bridge.py` 双副本 cp（wrapper cmp 门会拦版本偏差，部署时需同步）

---

## 📅 下一步（你批完这份单后）

1. **✅ 通过** → 说 "CARD-C3 通过"（可加 "+ 部署"）→ 标记完成，白天你决定是否合并
2. **❌ 有问题** → 在批注区写清楚 → Claude 修正后更新此单 v2
3. **想暂停** → 说 "暂停 CARD-C3"，状态保持 review，可随时回来
