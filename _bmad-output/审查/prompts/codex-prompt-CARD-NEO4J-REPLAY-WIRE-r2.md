# Codex 复核 — CARD-NEO4J-REPLAY-WIRE（BATCH-2026-09-11-第十四批 / 车道 T6 / **round-2**）

## ① 背景与最小读取面

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j`
分支 `card/t6-neo4j`。**本轮审查 SHA = `d9fa0774`（当前 HEAD）**。

- round-1 审的是 `cd1b5ae9`，结论 BLOCKER 0 / HIGH 0 / MEDIUM 4 / LOW 1。
- 本轮之所以存在：作者按 round-1 的 MEDIUM ①②③ 与 LOW ④ 改了代码，按 D-15「审后改代码必再送一轮」重送。

**最小读取面（只读这些）**：

1. **本轮整改 diff**：`git diff cd1b5ae9 d9fa0774 -- . ':(exclude)_bmad-output'`（只有 4 个文件、43 增 8 删）
2. 本卡全量改动面：`git diff 310eef31 d9fa0774 -- . ':(exclude)_bmad-output'`
3. `backend/app/services/fallback_sync_service.py:1-200`（`sync_all_fallbacks` 的三个 except 分支 + `count_fallback_backlog` + 两个计数 helper）
4. `backend/app/main.py:378-460`（回填门全段）
5. `backend/app/api/v1/endpoints/traces.py` 新增 POST 端点全段
6. `backend/app/security.py:64-166`（五分支矩阵；403 分支在 :135 之后、DEBUG bypass 尾在 :110 之后）
7. `backend/tests/integration/test_neo4j_replay_wire_t6b.py` 全文
8. round-1 存档：`_bmad-output/审查/codex-review-CARD-NEO4J-REPLAY-WIRE.md`

## ② 作者自述（请独立核对，不要采信）

round-1 四条的处置：

- **① 幂等门首轮未锁 Episode 数** → 已改：首轮断言从 `Concept == 1` 改为逐标签绝对值 `{"Concept":1,"Node":1,"Canvas":1,"Episode":1}`。作者认为这样「首轮自己就重复」也会被当场挡下，第二轮的相等比较才有意义。
- **② 启动摘要忽略 `error` 字段** → 已改：先算 `_failed = [k for k,v in replay.items() if isinstance(v,dict) and v.get("error")]`，非空则走 `logger.error` 点名哪几条链未回灌，否则才打原来那句 info。
- **③ 端点 docstring 声称不外带路径** → 未改返回值（卡文要求「原样返回 stats」），改 docstring 如实声明 `error`/`reason` 带 `str(e)`、`OSError` 通常内嵌绝对路径、受众靠鉴权限制而非文本过滤。
- **④ `UnicodeDecodeError` 不在捕获集** → 已改：`_count_jsonl_lines` 捕获集加 `UnicodeDecodeError`，`_count_json_list` 同样。作者的依据是 `UnicodeDecodeError` 是 `ValueError` 子类、不是 `OSError` 子类。

round-1 的 ⓪（门未覆盖启动与生产单例装配）作者未改代码，理由：那是测试覆盖面问题，已逐条登记进验收单的「本卡未证明什么」，且真跑 lifespan 会连现网 7691 并读 live vault（本卡硬边界禁止）。请判断这个理由是否成立。

## ③ 问题（按重要性排序）

⓪ **四处整改是否各自真的解决了 round-1 指出的那件事，有没有引入新的问题？** 尤其：② 的 `_failed` 判据用 `v.get("error")` 取真值 —— 若某条链的 `error` 是空字符串或 `None`，这条判据会漏掉吗？`sync_all_fallbacks` 里 `str(e)` 有可能产出空串吗？

① **① 的新断言是否过紧，会不会成为易碎门？** 逐标签钉死 `{"Concept":1,"Node":1,"Canvas":1,"Episode":1}` 依赖「一条评分条目恰好产生这四个节点」。若 `record_score_history` 或 `_replay_scoring_entry_to_neo4j` 将来多建一个节点，这条断言会红 —— 这是期望的行为，还是会变成挡路的噪音？另外 `_gate_node_count` 的计数口径（按 `name`/`id`/`path` 前缀 + 按 SCORED 反查 Episode）是否会漏数某类节点，从而让「相同」在有重复时仍成立？

② **④ 的捕获集是否仍有遗漏？** `read_text` / `json.loads` 这条链上还可能抛出哪些不在 `(OSError, UnicodeDecodeError, json.JSONDecodeError)` 里的异常？`Path.exists()` 本身呢？

③ **③ 的处置（只改文档不改返回值）是否可接受？** 若不可接受，请说明未被拦下的输入具体长什么样、后果多严重。

④ **本卡全量改动面（`310eef31..d9fa0774`）是否还有 round-1 未覆盖到的问题？** 特别是 `count_fallback_backlog` 的 `pending_total` 口径（只累加 `failed_writes` + `canvas_events`，不含 `learning_memories`，理由是后者回灌后不轮转所以其条目数不是待回灌数）是否站得住。

⑤ 作者另行实证并已登记的两件事，请核其推论是否正确：(a) `failed_writes.jsonl` 里由 `memory_service._record_structured_outbox` 落盘的 `{"kind":"knowledge_entity",…}` 条目没有 `concept`/`concept_id` 字段，会被 `_replay_scoring_entry_to_neo4j` 判「no concept」计 pending 写回文件、永不回灌（其消费者 `recover_failed_writes` 仍是零调用方）；(b) `learning_memories` 链每次回灌都全量重放，但其重放 Cypher 只有 MERGE + SET、不调 `record_score_history`，故图上幂等、不累积节点。

## ④ 输出格式

逐条给出：`BLOCKER / HIGH / MEDIUM / LOW` + `file:line` + 一句复现思路。
措辞请用：**负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**。
末尾给一个计数汇总（各级各几条）。

## ⑤ 边界

- 只读审查，不要改任何文件，不要连任何数据库。
- 不评 T6-C 的面：四暂存文件的写侧有界/轮转、`/traces` 积压数与最老时间字段、`dead_letter_episodes.jsonl` 的残片策略。
- 不评 `backend/app/security.py` 本身的设计（别卡地盘，本卡只 import）。
- `backend/openapi.json` 未再生是刻意的（主 session 集成期统一再生），不必作为缺陷提出。
