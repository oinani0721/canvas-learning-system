# 独立审查请求 round-2 — CARD-RED-A1-sentinel（BATCH-2026-09-07-第十三批）

仓库根: `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u10-red-a`
分支: `card/u10-red-a`

---

## 〇 本轮的由来

round-1 的结论是 **BLOCKER 0 / HIGH 0**（2 MEDIUM + 3 LOW），已达停轮条件。但其中三条 LOW 指出的是
「作者把推断写成了事实」，属名实不符，作者选择逐条改正而不是登记了事 —— 改动了代码，所以按本项目的
轮次规则必须再送一轮。**本轮请重点复核这些整改本身是否成立、有没有引入新问题。**

- round-1 绑定: `b8017248c59d6091c2827d5772cd20718502e6d1`
- **本轮绑定（当前 HEAD）**: `e74757c5`（`git log --oneline -1` 自证）
- 本卡起点 `U0` = `0acea4e3`；阶段一（未 merge 候选树）⇒ 本卡 diff 面 = 单段 `0acea4e3..HEAD`，共 2 个 commit
- round-1 全文见 `_bmad-output/审查/codex-review-CARD-RED-A1-sentinel.md`（已入库）

---

## 一 逐条整改，请独立核对

| # | round-1 指出 | 作者的整改 | 请你核对什么 |
|---|---|---|---|
| L3 | 「进程终态逐项相同」不成立（`_last_health_check` 时间戳真路径写、`AsyncMock` 不写） | 两个 fixture 的 docstring 改为「**连接控制状态**相同」，并写明差异项与「它不参与是否再连的判定」 | 新措辞是否**恰好**等于可证事实，没有把范围重新放大；`neo4j_client.py:431/467/534/554` 的行号引用是否仍准确 |
| L4① | 「真实声明变异必然执行端点体、会连 7691」不成立 | 探针补了**负控 B**：保留鉴权依赖，只在真实 `app.routes` 上删 403 声明 + 清 `app.openapi_schema` 缓存 + **原样重跑观测**，再还原并第三次观测 | 负控 B 的实现是否真的达成它声称的效果；还原是否完全（会不会给同进程后续留下副作用）；`VERDICT` 的合成条件是否有漏 |
| L4② | 「还没走到 schema 校验就超时」依据不足 | 改写为「只能确证最终判定被 `DeadlineExceeded` 占据，存档里没有任何 `status_code_conformance` 结论」 | 新措辞是否还有过度推断 |
| L5 | 「format-dirty **文件集合**相同 ⇒ 零新增违规」不成立 | 判据换成 **hunk 内容多重集**对照（U0 vs 收工，`ruff format --diff` 的 ±行内容去行号后排序比集合）；并把本卡新增的三处块整理成 ruff 偏好写法，存量行不动 | 新判据是否真的能看见「已脏文件里新增的违规」；有没有可能仍存在它看不见的新增违规（例如 hunk 内容恰好与存量重复） |
| M1 | 悬空 security 引用被本卡从 2 扩到 16 | 不改（地盘外），但把验收单里「只是把同一模式扩大」改写为「那 14 个原先继承有效全局声明、现被无效局部声明覆盖」，并带 17→31 / 2→16 两个数字移交 | 改写后的表述是否准确；移交而不修在本卡边界下是否恰当 |
| M2 | 装机档不能宣布验收通过；「没有 key 就 403」不准确 | 验收单 4-B 第 2 条改写为按后端配置分档，并明确「本卡不宣布该项验收通过」 | 表述是否仍有误导 |

作者另记了一处**自己在 round-1 prompt 里写错的数字**：把「202 基线 → 定稿减 53」误写成「减 12」
（12 是「开工 161 → 定稿 149」的差）。验收单正文两处一直是分开写的。

---

## 二 本轮整改后重跑的裁判（请核对结论与存档是否一致）

- `tests/unit`：`120 failed, 4810 passed, 48 skipped, 29 errors`；对 202 条红基线**零 `>` 行**；
  与整改前红集 `diff` 为空（`same_rc=0`）。存档 `unit-r1fix-*.txt` / `red-diff-r1fix-*.txt`
- 五文件两种收集顺序：各 `72 passed`，FAILED 集合为空，哨兵串计数 **0**。存档 `five-r1fix-order-a|b-*.txt`
- `tests/api`：`268 passed`，`NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0`。存档 `api-r1fix-*.txt`
- 探针 v2：正判 16/16 PASS、负控 A 成立、**负控 B 成立**（16/16 变红）、还原自证再次全绿，`VERDICT=PASS`。
  存档 `status-conformance-v2-*.txt`
- `ruff format` hunk 多重集：7 个文件逐条相同（97/122/84/0/0/0/0）；`ruff check` All checks passed。
  存档 `ruff-format-hunk-multiset-*.txt`

---

## 三 请按重要性排序回答

1. **整改本身有没有引入新缺陷？** 尤其是探针的负控 B —— 它在进程内改真实路由对象，请判断还原是否干净，
   以及「还原后再次全绿」这条自证是否足够。
2. **新的 hunk 多重集判据是否有它自己的盲区？**
3. **两个 fixture 的新 docstring 有没有仍然不实的地方？**
4. round-1 未展开的那条：`test_verification_service_activation.py:221` 作为冷首触候选，
   在**当前**代码下是否真的可能承担首拨？如果是，本卡是否应当处理，还是确属既有隔离边界？
5. 还有没有 round-1 与本轮都没发现的 BLOCKER / HIGH？

---

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给：一句话结论 + `file:line`（当前树真实行号）+ 依据。
若某条整改你核对后认为不成立，请直接指出。若确认无 BLOCKER / HIGH，请明确写出来。

---

## 五 边界（请不要评的）

- 不评端口门本身的设计（`backend/tests/support/live_port_guard.py` / `backend/tests/conftest.py:153-172`）。
- 不评 `backend/tests/support/authed_client.py`、`backend/tests/unit/conftest.py`、
  `test_system_endpoint_auth.py`、`test_sync_batch_auth.py`、`test_agent_templates_smoke.py`、
  `app/services/agent_service.py` —— 分属别的卡。
- 不评 `app/api/v1/system.py` 既有的 7 条 pyright 报错、以及 `ruff format` 的存量违规。
- 不评 `_archive/` 与 `_bmad-archive/`。
- `backend/tests/contract/**` 本卡只跑不改，不评其内容。

---

## 六 最小读取面

- 本轮增量：`git diff b8017248 e74757c5 -- . ':(exclude)_bmad-output'`
- 全卡：`git diff 0acea4e3 e74757c5 -- . ':(exclude)_bmad-output'`
- `backend/app/api/v1/system.py:26..:50`
- `backend/tests/unit/test_mock_degradation_transparency.py:26..:60`
- `backend/tests/unit/test_review_mode_support.py:22..:52`
- `backend/app/clients/neo4j_client.py:378..:470`、`:501..:536`、`:545..:560`
- `_bmad-output/审查/evidence-red-a1-sentinel/status_conformance_probe.py`（全文）
- `_bmad-output/审查/evidence-red-a1-sentinel/` 下：`status-conformance-v2-*.txt`、
  `ruff-format-hunk-multiset-*.txt`、`unit-r1fix-*.txt`、`red-diff-r1fix-*.txt`、
  `five-r1fix-order-a|b-*.txt`、`api-r1fix-*.txt`
- 验收单：`_bmad-output/验收单/UAT-CARD-RED-A1-sentinel-2026-09-09.md`（§4.3 是 r1 逐条处置表）
