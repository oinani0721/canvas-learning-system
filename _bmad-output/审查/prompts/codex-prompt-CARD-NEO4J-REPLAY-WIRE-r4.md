# Codex 复核 — CARD-NEO4J-REPLAY-WIRE（BATCH-2026-09-11-第十四批 / 车道 T6 / **round-4**）

## ① 背景与最小读取面

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j`
分支 `card/t6-neo4j`。**本轮审查 SHA = `7bcbfc1a`（当前 HEAD）**。

轮次链：r1 审 `cd1b5ae9`（B0/H0/M4/L1）→ r2 审 `d9fa0774`（B0/**H1**/M3/L2）→ r3 审 `d90f5a67`（B0/H0/M2/L2）→ 整改 `7bcbfc1a` → 本轮。
round-3 已满足 D-15 的 B/H 条件；本轮之所以存在，是因为作者仍改了代码（处理 r3 的 MEDIUM-1 与 LOW-4），按 D-15「审后改代码必再送一轮」重送。配额：本轮为第 4 轮（上限 5）。

**最小读取面（只读这些）**：

1. **本轮整改 diff**：`git diff d90f5a67 7bcbfc1a -- . ':(exclude)_bmad-output'`（2 文件、98 增 33 删）
2. 本卡全量改动面：`git diff 310eef31 7bcbfc1a -- . ':(exclude)_bmad-output'`
3. `backend/tests/integration/test_neo4j_replay_wire_t6b.py` 全文（重点：`_cleanup_queries` / `_gate_group_id` / `_gate_node_count`）
4. `backend/app/services/fallback_sync_service.py:1-280`（重点：`_count_jsonl_lines`、`_sync_failed_writes` 的初读与 finalize 重读）
5. `backend/app/main.py:378-470`
6. round-3 存档：`_bmad-output/审查/codex-review-CARD-NEO4J-REPLAY-WIRE-r3.md`

## ② 作者自述（请独立核对，不要采信）

- **r3 MEDIUM-1（清理身份跨门）** → 已改。前缀/尾缀全部换成精确身份：Canvas 路径**等值**；Concept/Node 用带分隔段的完整前缀 `t6bgate_concept_` / `t6bgate_cid_`（不再用裸 `t6bgate`，故不吃 `t6bgate2_*`）；Episode 的 group **等值**于 `_gate_group_id()` 运行时算出的真实物理 group（解析不出来则整条兜底查询跳过——宁可漏清不可越界）。全部参数化传值，不再 f-string 拼进 Cypher。`_gate_node_count` 的身份口径同步对齐（计数面比清理面宽会让清不掉的残留进计数、把幂等断言污染成假红）。
- **r3 LOW-4（U+2028）** → 已改。三处 `splitlines()` 一起换成 `split("\n")`：本卡新增的 `_count_jsonl_lines`，以及**既有** `_sync_failed_writes` 的初读与 finalize 重读（后两处靠 `len(current_lines) > len(lines)` 判断重放期间有无新追加，口径必须一致）。作者实测：改前计数 2 / 改后 1；回灌面改前该条目被切成两个非法 JSON 双双 pending、永远回灌不掉，改后 `recovered=1 pending=0` 且图内可查、文件已轮转。
- **r3 MEDIUM-2（启动接线门覆盖缺口）未改**：跑真 lifespan 会连现网 7691 并读 live vault，本卡硬边界明令禁止，已登记。
- **r3 LOW-3（`exists()` 使读取失败静默变零积压）未改**：已登记（本卡自审先于 Codex 发现）。

## ③ 问题（按重要性排序）

⓪ **本轮两处整改是否各自真的关上了 r3 指出的那件事，有没有引入新问题？** 具体：(a) 新的清理身份是否仍有跨门对照输入；(b) `_gate_group_id()` 解析失败时整条兜底跳过，会不会让残留永久滞留、进而污染后续运行的幂等断言（漏清 vs 越界的取舍是否恰当）；(c) `_cleanup_queries` 与 `_gate_node_count` 的身份口径是否真的逐字对齐。

① **`split("\n")` 的替换是否在所有既有输入上与 `splitlines()` 等价？** 作者只验了 CRLF 与 U+2028 两类差异，并认为写侧 `_atomic_write_file` 用 `\n` 拼接故生产不产生 CRLF。请核这个前提（是否存在别的写侧、或历史遗留文件带 CRLF），以及 `\r` 残留会不会让 `json.loads` 失败。

② **`_sync_failed_writes` 的两处切法改动是否破坏了 checkpoint 语义？** `checkpoint_idx` 是按 `lines` 的下标存的；若历史 checkpoint 是用 `splitlines()` 的口径写下的，换切法后下标含义会不会错位。

③ **本卡全量改动面（`310eef31..7bcbfc1a`）是否还有前三轮未覆盖的问题？**

④ 作者对 r3 MEDIUM-2 与 LOW-3 的「登记不改」是否恰当？若认为必须改，请说明最小改法与它触碰的边界。

## ④ 输出格式

逐条给出：`BLOCKER / HIGH / MEDIUM / LOW` + `file:line` + 一句复现思路。
措辞请用：**负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**。
末尾给一个计数汇总（各级各几条）。

## ⑤ 边界

- 只读审查，不要改任何文件，不要连任何数据库。
- 不评 T6-C 的面：四暂存文件的写侧有界/轮转、`/traces` 积压数与最老时间字段、`dead_letter_episodes.jsonl` 的残片策略。
- 不评 `backend/app/security.py` 与 `backend/tests/support/live_port_guard.py` 本身的设计（别卡地盘，本卡只调用）。
- `backend/openapi.json` 未再生是刻意的（主 session 集成期统一再生），不必作为缺陷提出。
