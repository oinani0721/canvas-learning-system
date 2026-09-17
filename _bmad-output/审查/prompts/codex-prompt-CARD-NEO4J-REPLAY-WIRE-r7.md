# Codex 复核 — CARD-NEO4J-REPLAY-WIRE（BATCH-2026-09-11-第十四批 / 车道 T6 / **round-7**）

## ① 背景与最小读取面

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j`
分支 `card/t6-neo4j`。**本轮审查 SHA = `1028bea7`（当前 HEAD）**。

轮次链：r1 `cd1b5ae9`(B0/H0/M4/L1) → r2 `d9fa0774`(B0/**H1**/M3/L2) → r3 `d90f5a67`(B0/H0/M2/L2) → r4 `7bcbfc1a`(B0/**H1**/M2/L2) → r5 `ccb1d101`(B0/**H1**/M2/L0) → r6 `962d86c6`(B0/**H3**/M1/L0) → 整改 `c667b1eb` + `1028bea7` → 本轮。

⚠️ **已远超卡文的 5 轮上限，如实说明**：r5 后车道曾按 D-15 停车并交主 session，但因流程判定停车不算闭环而继续整改。**主 session 仍可裁定止于任一版本。** r6 自己也写明「不替主 session 撤销 r5 停车裁定」。
⚠️ **r6 已对最终 HEAD 失绑**：它审 `962d86c6` 期间车道提交了 `c667b1eb`（车道第三次踩「审查对象须冻结」）。本轮绑 `1028bea7`，审查期间车道不再改任何代码。

**最小读取面（只读这些）**：

1. **两次整改 diff**：`git diff 962d86c6 1028bea7 -- . ':(exclude)_bmad-output'`
2. 本卡全量改动面：`git diff 310eef31 1028bea7 -- . ':(exclude)_bmad-output'`
3. `backend/app/services/fallback_sync_service.py` 全文（重点：模块级 `_sync_all_lock`、`sync_all_fallbacks` / `_sync_all_fallbacks_locked`、三个 `_sync_*` 的 `contiguous_end`、`_sync_failed_writes` 的 finalize 段、`_load_checkpoint` / `_save_checkpoint` / `_clear_checkpoint`）
4. `backend/app/main.py:378-470`
5. r6 存档：`_bmad-output/审查/codex-review-CARD-NEO4J-REPLAY-WIRE-r6.md`

## ② 作者自述（请独立核对，不要采信）

r6 三条 HIGH **全部改码**，另有一条自查修复：

- **HIGH-2 并发回灌覆盖** → 加模块级 `asyncio.Lock`（`_sync_all_lock`）把**整次回灌**串行化：`sync_all_fallbacks` 取锁后转调 `_sync_all_fallbacks_locked`。作者实测两个并发调用的执行序列为 `['enter','exit']`（未交叠）。**声明未覆盖面**：进程内互斥；跨进程 / 多 worker 并发未覆盖。
- **HIGH-3 finalize 重读失败仍覆盖** → 原 `except OSError: current_lines = []` 改为：记 error 日志并**直接返回**，保留原文件 + 保留 checkpoint。作者实测注入 `OSError` 后文件逐字节原封不动。
- **HIGH-1 文件代际错配** → `_clear_checkpoint` 移到改写/轮转**之前**；`_clear_checkpoint` 不再静默吞 `OSError`（JSON 解析失败仍吞，因为随后会 `unlink` 整个文件）；清不掉则调用方放弃改写并返回。
- **自查（`c667b1eb`，非 Codex 提出）**：r5 的「连续成功前缀」只施加在 `failed_writes`；`canvas_events` 逐字同构、**同样会丢数据**（它的 `still_pending` 也写回文件），一并改；`learning_memories` 后果不同（不写回不轮转、跳过不会丢）但口径统一。

r6 的 MEDIUM「门只验 group 格式、错误 vault 仍可假绿」**仍未改**，继续作为开放项移交。

## ③ 问题（按重要性排序）

⓪ **三条 HIGH 的修复是否各自真的关上了那条路径，有没有引入新的丢失/阻塞路径？** 具体：(a) `_sync_all_lock` 是模块级 `asyncio.Lock`，在「多个事件循环」（如 TestClient portal + 主循环）下是否会绑错循环或死锁；(b) HIGH-3 的提前返回是否遗漏了任何本该执行的收尾（`_cleanup_old_synced_files`、`_clear_checkpoint` 的语义）；(c) HIGH-1 的「先清游标后改写」在清成功但改写失败时留下什么状态，是否比原先更糟。

① **`canvas_events` / `learning_memories` 的 finalize 是否也有 HIGH-3 同型问题？** 本卡只改了 `failed_writes` 的 finalize。

② **本卡全量改动面（`310eef31..1028bea7`）是否还有前六轮未覆盖的数据丢失 / 跨 vault 污染 / 门假绿路径？** 这是重点。

③ 若仍有 HIGH，请明确指出**最小改法**与边界，以便主 session 裁定；并请判断：这个文件（Story 38.8 既有算法）是否已到「应独立排一张重写卡」的程度，而非继续在本接线卡上打补丁。

## ④ 输出格式

逐条给出：`BLOCKER / HIGH / MEDIUM / LOW` + `file:line` + 一句复现思路。
措辞请用：**负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**。
末尾给一个计数汇总（各级各几条）。

## ⑤ 边界

- 只读审查，不要改任何文件，不要连任何数据库。
- 不评 T6-C 的面：四暂存文件的写侧有界/轮转、`/traces` 积压数与最老时间字段、`dead_letter_episodes.jsonl` 的残片策略。
- 不评 `backend/app/security.py` 与 `backend/tests/support/live_port_guard.py` 本身的设计。
- `backend/openapi.json` 未再生是刻意的，不必作为缺陷提出。
