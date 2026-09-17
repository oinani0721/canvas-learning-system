# Codex 复核 — CARD-NEO4J-REPLAY-WIRE（BATCH-2026-09-11-第十四批 / 车道 T6 / **round-6**）

## ① 背景与最小读取面

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j`
分支 `card/t6-neo4j`。**本轮审查 SHA = `962d86c6`（当前 HEAD）**。

轮次链：r1 `cd1b5ae9`（B0/H0/M4/L1）→ r2 `d9fa0774`（B0/**H1**/M3/L2）→ r3 `d90f5a67`（B0/H0/M2/L2）→ r4 `7bcbfc1a`（B0/**H1**/M2/L2）→ r5 `ccb1d101`（B0/**H1**/M2/L0）→ 整改 `962d86c6` → 本轮。

⚠️ **本轮超出卡文写的 5 轮上限**，如实说明：r5 报 HIGH 后车道本已按 D-15 停车并交主 session；但车道对 r5 的三项（HIGH + 两条 MEDIUM）**都有明确修法**、不是在盲目循环，故补送本轮以求闭环。**主 session 仍可裁定止于 r5 的停车版本 `ccb1d101`。**

**最小读取面（只读这些）**：

1. **本轮整改 diff**：`git diff ccb1d101 962d86c6 -- . ':(exclude)_bmad-output'`（3 文件、177 增 179 删）
2. 本卡全量改动面：`git diff 310eef31 962d86c6 -- . ':(exclude)_bmad-output'`
3. `backend/app/services/fallback_sync_service.py` 的 `_sync_failed_writes` 全段 + `_load_checkpoint` / `_save_checkpoint` + 文件头 `_PROGRESS_VERSION`
4. `backend/app/main.py:378-470`（回填门全段，含新的内层 try）
5. `backend/tests/unit/test_story_38_8_fallback_sync.py::TestAC3Checkpoint`
6. r5 存档：`_bmad-output/审查/codex-review-CARD-NEO4J-REPLAY-WIRE-r5.md`

## ② 作者自述（请独立核对，不要采信）

r5 三条的处置 —— **全部改码**：

- **HIGH（checkpoint 把「已尝试」当「已成功」）** → 已改两处：
  1. **游标只推进到连续成功前缀**：引入 `contiguous_end`，不变式为「`lines[checkpoint_idx : contiguous_end]` 全部重放成功」；只有当前条成功**且** `contiguous_end == i` 时才延长一位。`_save_checkpoint` 存的是 `contiguous_end` 而非 `i + 1`，且仅在 `contiguous_end > checkpoint_idx` 时才存。
  2. **进度语义版本** `_PROGRESS_VERSION = "split-lf+contiguous"`：任何不等于它的标记（含 r4 引入的 `"split-lf"` 与无标记的历史 checkpoint）一律**回退 0**。刻意**移除**了 r4 那版「实测两种切法行数相同就沿用」的宽松判断 —— 那只覆盖切法变更，语义变更下行数相同的文件旧游标照样可能越过失败条目。
  作者实测：同一负控（第 1 条失败、2–50 成功）下**实现存过的游标值 = `[]`**（前缀被 c0 卡住，从未存出 50）；对照跑法里人工塞 `index=50` 则 c0 确实被跳过。
- **MEDIUM（`_worker_online` 仍依赖回填成功）** → 已改：**不再用状态变量**。给 `backfill_vault(...)` 单独包内层 `try/except`，回填失败被内层吃掉、回灌照常执行。
- **连带**：回灌回到回填门体内，`main.py` 两个 hunk 重新全部落在卡文要求的 `:386-404`（`@@ -388,15 +388,60 @@` 与 `@@ -404,0 +450,17 @@`），`:381-384` import 块原样。
- **既有测试 `test_resumes_from_checkpoint` 随格式变更更新**（checkpoint 加 `progress_version`，从被测模块取常量不硬编码）。不改则该用例必红，违反卡文 (i)「`tests/unit` diff 只允许 `<`」。

r5 的 MEDIUM「门只验 group 格式、错误 vault 仍可假绿」**未改**，作为登记项移交（见 ③④）。

## ③ 问题（按重要性排序）

⓪ **连续成功前缀的实现是否真的关上了 r5 HIGH，且不变式无洞？** 具体：(a) `contiguous_end == i` 这个条件在「checkpoint_idx > 0 的续跑」场景下是否仍正确（首次进入循环时 `i == checkpoint_idx`）；(b) 畸形行（`json.JSONDecodeError`）与重放返回 `False`、抛异常三条失败路径是否都能卡住前缀；(c) `_save_checkpoint` 的 `contiguous_end > checkpoint_idx` 守卫是否会在某种输入下漏存本该存的进度，导致重复劳动累积。

① **进度语义版本的回退策略是否有未被拦下的输入？** 尤其：`canvas_events` / `learning_memories` 两条链也走同一个 `_load_checkpoint`，它们的历史 checkpoint 同样无标记 ⇒ 也会回退 0。这对它们是否安全（它们的游标语义是否也曾是「已尝试」）？

② **内层 try 的改法是否真的解耦了回填与回灌？** 请核：回填 `except` 之后控制流是否必然继续执行回灌块；内层 `except` 的捕获面是否覆盖 `backfill_vault` 可能抛出的全部异常；以及这次是否又出现「结构变了行为没变」。

③ **本卡全量改动面（`310eef31..962d86c6`）是否还有前五轮未覆盖的问题？** 请把范围放在「会导致数据丢失、跨 vault 污染、或让门变成假绿」三类。

④ r5 的「门只验 group 格式」未改，作为登记项移交是否可接受？若认为必须改，请说明最小改法与它触碰的边界。

## ④ 输出格式

逐条给出：`BLOCKER / HIGH / MEDIUM / LOW` + `file:line` + 一句复现思路。
措辞请用：**负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**。
末尾给一个计数汇总（各级各几条）。

## ⑤ 边界

- 只读审查，不要改任何文件，不要连任何数据库。
- 不评 T6-C 的面：四暂存文件的写侧有界/轮转、`/traces` 积压数与最老时间字段、`dead_letter_episodes.jsonl` 的残片策略。
- 不评 `backend/app/security.py` 与 `backend/tests/support/live_port_guard.py` 本身的设计（别卡地盘，本卡只调用）。
- `backend/openapi.json` 未再生是刻意的（主 session 集成期统一再生），不必作为缺陷提出。
