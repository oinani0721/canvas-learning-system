# Codex 复核 — CARD-NEO4J-REPLAY-WIRE（BATCH-2026-09-11-第十四批 / 车道 T6 / **round-3**）

## ① 背景与最小读取面

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j`
分支 `card/t6-neo4j`。**本轮审查 SHA = `d90f5a67`（当前 HEAD）**。

轮次链：round-1 审 `cd1b5ae9`（B0/H0/M4/L1）→ 整改 `d9fa0774` → round-2 审 `d9fa0774`（B0/**H1**/M3/L2）→ 整改 `d90f5a67` → 本轮。
本轮之所以存在：round-2 报了 1 个 HIGH，按 D-15「最后一轮必须 BLOCKER=0 且 HIGH=0」必须整改重送。

**最小读取面（只读这些）**：

1. **本轮整改 diff**：`git diff d9fa0774 d90f5a67 -- . ':(exclude)_bmad-output'`（4 文件、79 增 12 删）
2. 本卡全量改动面：`git diff 310eef31 d90f5a67 -- . ':(exclude)_bmad-output'`
3. `backend/tests/integration/test_neo4j_replay_wire_t6b.py` 全文
4. `backend/tests/support/live_port_guard.py` 的 `canonical_target_ports`（约 :1072-1216）与 `ALLOWED_TEST_PORTS`（:183）
5. `backend/app/main.py:378-470`（回填门全段）
6. `backend/app/services/fallback_sync_service.py:1-200`
7. `backend/app/api/v1/endpoints/traces.py` 新增 POST 端点全段
8. round-2 存档：`_bmad-output/审查/codex-review-CARD-NEO4J-REPLAY-WIRE-r2.md`

## ② 作者自述（请独立核对，不要采信）

round-2 五条的处置：

- **HIGH-1 现网端口保护可被绕过** → 已改。字符串判据 `":7691" not in uri` 换成 `live_port_guard.canonical_target_ports()` + **正向白名单** `ALLOWED_TEST_PORTS`；解析失败 fail-closed；routing scheme 的多地址逐个校验。可执行契约 `test_gate_never_targets_live_7691` 同步升级，并在用例内嵌了针对 `bolt://127.0.0.1:07691` 的负控自证。作者实测对照：`:07691` / `:007691` / 无端口 / `:0` 旧判据全放行（驱动解析后分别 7691/7691/7687/7687），新判据全拒绝。
- **MEDIUM-2 空异常文本被误判为成功** → 已改：`v.get("error")` 换成 `"error" in v`。
- **MEDIUM-4 清理查询越界删除** → 已改：兜底那条加 `e.group_id IS NOT NULL AND e.group_id ENDS WITH '<本门 canvas 名>'`。用 ENDS WITH 而非 vault 前缀，因为 group 解析成 `vault:<active_vault>:<canvas>` 后 vault 段随环境变。
- **LOW-5 JSON 计数异常遗漏** → 已改：两个计数 helper 的捕获集收敛为 `(OSError, ValueError)`，一次覆盖 `JSONDecodeError`、`UnicodeDecodeError` 两个子类与整数位数上限抛的普通 `ValueError`。
- **LOW-6 端点 description 与 learning 链口径冲突** → 已改：description 改为分链如实陈述（failed_writes / canvas_events 会轮转故第二次 0；learning_memories 不轮转故全量重放、图上幂等但计数不归零）。
- **MEDIUM-3（round-1 ⓪ 的验收缺口）未改码**，作为「本卡未证明什么」登记：端到端门走 `ASGITransport` 不跑 lifespan，启动接线与真实工厂装配仍是门未覆盖的路径。

## ③ 问题（按重要性排序）

⓪ **HIGH-1 的修复是否真的关上了那个面？** 具体请核：(a) `canonical_target_ports` 是否真是驱动口径（而不是又一个平行解析器）；(b) 正向白名单 + fail-closed 的组合是否还有未被拦下的输入（例如解析成功但端口元组为空、非 `bolt/neo4j` scheme、带 userinfo 的 URI、IPv6 字面量、大小写或空白变体）；(c) 探针与可执行契约两处是否都改到了，有没有第三处仍在用字符串判据。

① **`"error" in v` 是否足够？** `sync_all_fallbacks` 是否存在「出了错但 result 里连 `error` 键都没有」的路径（例如某个子同步内部吞掉异常后返回普通 stats）？若有，摘要仍会报成功。

② **清理查询的新身份约束是否既不越界也不漏删？** `ENDS WITH '<canvas 名>'` 在 group 被 punycode 化、或 canvas 名成为另一个 group 的后缀时会怎样？另外该约束加在兜底那条上，前面几条按 name/id/path 前缀删的是否仍可能删到别的门的数据？

③ **`(OSError, ValueError)` 这个捕获集是否过宽或仍有遗漏？** 过宽会不会吞掉本该暴露的编程错误（例如 `data.get` 的参数问题）？仍遗漏的是否只剩 `RecursionError` / `MemoryError` 这类？另，`Path.exists()` 在两个 `try` 之外——作者已把「3.14 抑制权限类 OSError 返回 False，因而这一支不记 warning」登记为已知缺口，请判断该登记是否恰当，还是应当算缺陷。

④ **本卡全量改动面（`310eef31..d90f5a67`）是否还有前两轮未覆盖的问题？**

⑤ round-2 曾指出幂等计数查询 `labels(n)[0]` 只取一个标签、`count(e)` 没去重、游离 Episode 与连错 Node 的 Episode 是门未覆盖的路径。作者本轮**未改**该查询（它挡住了 round-2 点名的那个负控输入，且首轮已钉成绝对值）。请判断这个不改的决定是否可接受；若不可接受，请说明具体的对照输入。

## ④ 输出格式

逐条给出：`BLOCKER / HIGH / MEDIUM / LOW` + `file:line` + 一句复现思路。
措辞请用：**负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**。
末尾给一个计数汇总（各级各几条）。

## ⑤ 边界

- 只读审查，不要改任何文件，不要连任何数据库。
- 不评 T6-C 的面：四暂存文件的写侧有界/轮转、`/traces` 积压数与最老时间字段、`dead_letter_episodes.jsonl` 的残片策略。
- 不评 `backend/app/security.py` 与 `backend/tests/support/live_port_guard.py` 本身的设计（别卡地盘，本卡只调用）。
- `backend/openapi.json` 未再生是刻意的（主 session 集成期统一再生），不必作为缺陷提出。
