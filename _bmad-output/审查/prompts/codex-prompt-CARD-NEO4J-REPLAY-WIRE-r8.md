# Codex 复核 — CARD-NEO4J-REPLAY-WIRE（BATCH-2026-09-11-第十四批 / 车道 T6 / **round-8**）

## ① 背景与最小读取面

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j`
分支 `card/t6-neo4j`。**本轮审查 SHA = `a66316df`（当前 HEAD）**。

轮次：r1 `cd1b5ae9`(H0) → r2 `d9fa0774`(**H1**) → r3 `d90f5a67`(H0) → r4 `7bcbfc1a`(**H1**) → r5 `ccb1d101`(**H1**) → r6 `962d86c6`(**H3**) → r7 `1028bea7`(**H5**, 含既知 G2-2 项 1) → 整改 `a66316df` → 本轮。

⚠️ **已远超卡文 5 轮上限**，如实说明：车道曾两次按 D-15 停车并交主 session，但流程判定「(n) 未闭环」而要求继续整改至 `HIGH = 0`。**主 session 仍可裁定止于任一版本。** r7 自己也写明「不撤销 r5 停车裁定，也不替主 session 决定继续整改」。
⚠️ 本轮审查期间车道**不改任何代码**（r6 曾因车道中途提交而失绑，此后已纠正）。

**最小读取面（只读这些）**：

1. **本轮整改 diff**：`git diff 1028bea7 a66316df -- . ':(exclude)_bmad-output'`（1 文件）
2. `backend/app/services/fallback_sync_service.py` 全文
3. 本卡全量改动面：`git diff 310eef31 a66316df -- . ':(exclude)_bmad-output'`
4. r7 存档：`_bmad-output/审查/codex-review-CARD-NEO4J-REPLAY-WIRE-r7.md`

## ② 作者自述（请独立核对，不要采信）

r7 五条 HIGH 的处置 —— **前四条全部按你给的最小改法改码，第五条保持移交**：

- **HIGH-1 + HIGH-2（canvas 位置游标未绑快照 / 旧游标带当前标记被接受）** → **禁用 canvas 的位置 checkpoint**（`_load_checkpoint` / `_save_checkpoint` 在该链已全部移除）。理由采纳你的原话：该链重放前 `sort(key=timestamp)`，「第 i 条」不是稳定身份。代价：崩溃后本链从头重放（重放走 MERGE 身份键，图上幂等；写侧另有 `_max_fallback_events = 10000` 上限）。
- **HIGH-3（canvas finalize 完全不重读）** → 改为**重读 + 按内容指纹差集**：新增 `_event_fingerprint()`（`json.dumps(sort_keys=True, separators=(",",":"))`），当前文件里凡不在初读快照中的一律保留。**未照搬** failed_writes 的按长度截取（你已指出该链会排序、位置对不上）。重读失败则放弃改写、保留原文件。作者实测：重放期间追加一条**时间戳更早**的 z，x 成功 y 失败 ⇒ 文件剩余 `['y','z']`（两者都在）；注入 `OSError` ⇒ 文件逐字节原封不动。
- **HIGH-4（`record_score_history` 失败仍返回 `True`）** → 异常时返回 `False` 留 pending；客户端以**返回值**表达失败的分支（group 解析 fail-closed 返 `False`）同样判失败。作者实测：`recovered=0 / pending=1` 且文件未轮转。
- **HIGH-5（重放用当前 vault）** → **不改**：你已标注「既知 G2-2 移交风险，非本轮新增」「源码已经明确承认并移交此风险」。最小止血（来源无法证明的历史条目一律保留待处理）等于关掉整条回灌功能，车道判断这属于 G2-2 的范围决策。

r7 三条 MEDIUM 未改，继续登记移交（模块级 `asyncio.Lock` 跨循环 / finalize 提前返回缺 `error` 键 / 错误 vault 归属门可假绿）。

## ③ 问题（按重要性排序）

⓪ **前四条修复是否各自真的关上了那条路径，有没有引入新的丢失/重复路径？** 具体：(a) 禁用 canvas 位置游标后，大文件（接近 10000 条）崩溃重启的全量重放是否会引入新的实际问题；(b) `_event_fingerprint` 用 `sort_keys` JSON 作身份，**同一条事件被写入两次**（内容完全相同）时会被当成同一条 —— 这在本链的语义下是否可接受；(c) HIGH-4 返回 `False` 后整条重放，`_replay_scoring_entry_to_neo4j` 的 LEARNED 部分被重复执行是否确实幂等。

① **`learning_memories` 链是否还有同型问题？** 本轮只改了 canvas 与评分历史。该链不写回不轮转，你在 r7 已说明「没有 canvas 的同型 finalize 删除路径」，请确认本轮改动没有改变这个结论。

② **本卡全量改动面（`310eef31..a66316df`）是否还有剩余的数据丢失 / 跨 vault 污染 / 门假绿路径？** 请把 HIGH 严格限定在这三类。

③ 若仍有 HIGH，请标明它是「本卡引入/暴露的」还是「既有算法的、应归入独立重写卡」，以便主 session 裁定止血边界。

## ④ 输出格式

逐条给出：`BLOCKER / HIGH / MEDIUM / LOW` + `file:line` + 一句复现思路。
措辞请用：**负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**。
末尾给一个计数汇总（各级各几条），并请**单独标出**其中属于「既知移交项 / 既有算法应归重写卡」的条数。

## ⑤ 边界

- 只读审查，不要改任何文件，不要连任何数据库。
- 不评 T6-C 的面：四暂存文件的写侧有界/轮转、`/traces` 积压数与最老时间字段、`dead_letter_episodes.jsonl` 的残片策略。
- 不评 `backend/app/security.py` 与 `backend/tests/support/live_port_guard.py` 本身的设计。
- `backend/openapi.json` 未再生是刻意的，不必作为缺陷提出。
