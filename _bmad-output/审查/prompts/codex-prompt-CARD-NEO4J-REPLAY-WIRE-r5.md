# Codex 复核 — CARD-NEO4J-REPLAY-WIRE（BATCH-2026-09-11-第十四批 / 车道 T6 / **round-5，配额最后一轮**）

## ① 背景与最小读取面

树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t6-neo4j`
分支 `card/t6-neo4j`。**本轮审查 SHA = `ccb1d101`（当前 HEAD）**。

轮次链：r1 `cd1b5ae9`（B0/H0/M4/L1）→ r2 `d9fa0774`（B0/**H1**/M3/L2）→ r3 `d90f5a67`（B0/H0/M2/L2）→ r4 `7bcbfc1a`（B0/**H1**/M2/L2）→ 整改 `ccb1d101` → 本轮。
**本轮是 D-15 允许的第 5 轮（上限）**：若本轮仍报 HIGH，车道按规定停下交主 session 人审，不再自行整改。

**最小读取面（只读这些）**：

1. **本轮整改 diff**：`git diff 7bcbfc1a ccb1d101 -- . ':(exclude)_bmad-output'`（3 文件、180 增 80 删）
2. 本卡全量改动面：`git diff 310eef31 ccb1d101 -- . ':(exclude)_bmad-output'`
3. `backend/app/services/fallback_sync_service.py:1-300` 与 `_load_checkpoint` / `_save_checkpoint` 全段
4. `backend/app/main.py:378-480`（回填块 + **独立成段**的回灌块）
5. `backend/tests/integration/test_neo4j_replay_wire_t6b.py` 全文
6. r4 存档：`_bmad-output/审查/codex-review-CARD-NEO4J-REPLAY-WIRE-r4.md`

## ② 作者自述（请独立核对，不要采信）

r4 五条的处置——**全部改码**：

- **HIGH（旧 checkpoint 与新分行口径不兼容）** → 已改。第一版修法是「checkpoint 缺 `line_split` 标记就一律回退 0」，**过重**，打破了既有 `test_resumes_from_checkpoint`。改成：checkpoint 带 `line_split` 标记；标记不匹配时再用传入的 `raw` **实测这个具体文件**在 `split("\n")` 与 `splitlines()` 下行数是否相同 —— 相同则安全沿用旧下标，不同才回退 0 并记 warning。`raw` 只由按行切分的 `failed_writes` 传；`canvas_events` / `learning_memories` 走 `json.loads` 得 list、下标口径与切行无关，不传即表示不受影响。作者四场景实测：含 U+2028 → 0；不含 → 50；带新标记 → 50；`canvas_events` 不传 raw → 7。
- **MEDIUM-2（清理身份仍跨 vault／并行运行）** → 已改：每次运行分配一次性 `_GATE_RUN_ID`，`GATE_CANVAS` / `_GATE_CONCEPT_PREFIX` / `_GATE_NODE_PREFIX` 全部带上它，清理与计数共用。
- **MEDIUM-3（回灌依赖回填先成功）** → 已改：回灌整段移出回填的 `try/except`，独立成段，靠 `_worker_online` 传递在线状态。该变量**默认 `False`** —— 回填块在取到 `_worker_graphiti` 之前就抛异常时在线状态未知，此时按离线处理（只做只读积压登记，不连库）。
- **LOW-4（计数未绑标签）** → 已改：逐条绑「标签 + 属性」组合，与清理面逐字对齐。
- **LOW-5（`exists()` 绕过 warning）** → 已改：直接 `read_text`，`FileNotFoundError` 静默 0、其余读取异常记 warning。

## ③ 问题（按重要性排序）

⓪ **HIGH 的新修法是否真的关上了那条路径，且没有引入新的回归？** 具体：(a) 「实测两种切法行数是否相同」这个判据本身是否可靠——存在行数相同但**切点不同**的输入吗？(b) `raw` 是在加锁读文件之后取的，与 `_load_checkpoint` 内部再算一次是否存在竞态；(c) 不传 `raw` 的两条链（`canvas_events` / `learning_memories`）确实与切行口径无关吗。

① **回灌移出回填 `try` 后，`_worker_online` 这条状态传递是否正确？** 尤其：(a) 默认 `False` 在「回填块早期抛异常」时按离线处理——这个取舍是否恰当，还是应当仍尝试回灌；(b) 移出后回灌块自己的 `except Exception` 是否覆盖了原先由回填 `except` 兜住的所有异常；(c) 移出是否改变了两段之间的**执行顺序或副作用**（例如 import 时机、单例装配次序）。

② **每次运行的 `_GATE_RUN_ID` 是否真的隔离了并行运行？** 它是模块级常量，同一进程内多次运行会共用同一个值——pytest 单进程内重复执行该文件（例如 `--count`、或 xdist 同 worker 多次收集）时是否仍成立？清理与计数是否**全部**改到了（有没有漏网的仍用旧门级前缀的查询）。

③ **本卡全量改动面（`310eef31..ccb1d101`）是否还有前四轮未覆盖的问题？** 这是最后一轮，请把范围放在「会导致数据丢失、跨 vault 污染、或让门变成假绿」这三类上。

④ 若本轮仍有 HIGH，请明确指出**最小改法**与它触碰的边界，以便主 session 人审时直接裁定。

## ④ 输出格式

逐条给出：`BLOCKER / HIGH / MEDIUM / LOW` + `file:line` + 一句复现思路。
措辞请用：**负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**。
末尾给一个计数汇总（各级各几条）。

## ⑤ 边界

- 只读审查，不要改任何文件，不要连任何数据库。
- 不评 T6-C 的面：四暂存文件的写侧有界/轮转、`/traces` 积压数与最老时间字段、`dead_letter_episodes.jsonl` 的残片策略。
- 不评 `backend/app/security.py` 与 `backend/tests/support/live_port_guard.py` 本身的设计（别卡地盘，本卡只调用）。
- `backend/openapi.json` 未再生是刻意的（主 session 集成期统一再生），不必作为缺陷提出。
