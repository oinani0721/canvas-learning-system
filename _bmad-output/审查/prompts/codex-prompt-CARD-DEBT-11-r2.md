# Codex 复核 prompt — CARD-DEBT-11（round-2 · GLM-5.3 · 协议 §2.4）

> 批次 `BATCH-2026-09-18-第十五批` · 车道 `card-p1-storage` · 卡 `CARD-DEBT-11`（5-ge-1 `CanvasGraphEpisodeV1` schema 冻结 · **零代码路径**）
> 审查绑定：`f21cd421`（r1 整改后终态）· 基线 PREV = `6f25de8b`（P1-C 末 commit）· r1 审 SHA = `27743808`
> 你的沙箱是 read-only：用 git 只读命令与读文件完成核对；不要尝试写任何文件。

---

## ① 背景 + 最小读取面（写死）

**r1 复核结论（`codex-review-CARD-DEBT-11.md`，BLOCKER=0 / HIGH=4 / MEDIUM=3 / LOW=1）与整改对照**：

| # | r1 判定 | 处置（本 commit `f21cd421`） |
|---|---|---|
| H1 | 冻结面只写数量、不逐键（edge/entity/relation、嵌套 payload、autofill 语义） | **已修**：spec「Schema 冻结声明」段逐键展开（10 边键 + 11 relation 映射 + CalloutPayload/ContextPayload 字段 + EVOLUTION 5 值 + `_autofill_event_id` 语义） |
| H2 | spec 引用的复跑证据未在绑定 commit（工作树 untracked） | **已修**：`evidence-debt11/**`（含全部裁判档）随本 commit 入库；r1 prompt/存档同 commit |
| H3 | 旧 spec 剩余面无 owner 且有漏项（1-16 Task 8 / 2-10 Task 7、8） | **部分修**：剩余面清单补漏（逐 Task）；owner = 推荐落点 + 「待登记」（本卡只能登记，不能替主 session 定 owner） |
| H4 | `status: superseded` 是 sprint-status validator 枚举外值（`_bmad/bmm/workflows/4-implementation/sprint-status/instructions.md`：Stories 合法值 = backlog/ready-for-dev/in-progress/review/done） | **已修（回退）**：两 story `status` 回 `backlog` + 保留 `superseded_by` / `superseded_at`（卡文 §四台账③ 预留路径）；旧 spec（md）frontmatter `status: "superseded"` 保留（archive 先例） |
| M1 | LITE-4-3 / LITE-5-6 依赖 superseded 的 2-10 → 不可达 | **登记**（本卡 yaml 地盘仅三块，不能改）：已写进 2-10 `superseded_reason` + UAT 台账待登记 |
| M2 | Dev Notes 架构图/File Paths 与 Task 3/4/5 裁定矛盾 | **已修**：Dev Notes 加「2026-09-18 CARD-DEBT-11 裁定后注（历史目标态）」 |
| M3 | py 注释与 spec 冻结段两份手抄、无漂移门 | **部分修**：py 注释加「以 spec 冻结段为准」；结构门归后续卡（卡文「未证明」已列） |
| L1 | spec 冻结段行号漂移 / grep 过程叙述失实 | **已修**：行号订正（Literal → :225；edge_type_map → :12/:185/:186；候选树 grep 实测 0 命中） |

**最小读取面（逐条执行，均在车道树内）**：

1. `git --no-pager diff --no-color 27743808 f21cd421 -- . ':(exclude)_bmad-output'` → 预期**仅** `backend/app/graphiti/canvas_episode.py` 的 1 行 `#` 注释。
2. `git --no-pager diff --no-color 6f25de8b f21cd421 -- _bmad-output/implementation-artifacts` → spec / sprint-status / 两旧 spec 四文件全卡 diff。
3. `git -c core.quotePath=false ls-tree -r --name-only f21cd421 | grep evidence-debt11 | wc -l` → 期望 ≥50（H2 的机器证明）。
4. `backend/app/graphiti/canvas_episode.py:1-30`（头注释块）+ `:208-277`（类全貌 + validator + autofill + compute_event_id）。
5. spec 全文：`_bmad-output/implementation-artifacts/epic-5a-graphiti-runtime/5-ge-1-canvas-graph-episode-v1.md`（重点：新「## Schema 冻结声明」段与「### 裁定 2026-09-18」段）。
6. `_bmad-output/implementation-artifacts/sprint-status.yaml:490-500,558-576,610-626,680-690`；两旧 spec 的 frontmatter（:1-10）与 `Status:` 行。
7. `backend/tests/unit/test_canvas_episode_v1.py` 全文（19 用例）。
8. 承重档（f21cd421 内，可 `git show f21cd421:<path>` 读）：`evidence-debt11/` 下 `d32-r2-*`、`negctl1-r2-*`、`negctl2-r2-*`、`territory-r2-fixed2-*`、`unit-r2-*`、`regression-r2-*`、`lint-exclude-justification-refresh2-*`、`jev-triage-f21cd421.json`。
9. ⚠️ `evidence-debt11/probe.py` = **D-32 验伪锚证据副本**（`canvas_episode.py` 的 276 行副本 + 尾部一行 `X_PROBE = 1`；位于证据目录、无任何 import 引用、非生产代码）。Jev 分诊对它出 REVIEW 标记（见下表）——请独立核此声明（对照：`git show f21cd421:backend/app/graphiti/canvas_episode.py` 与 probe.py 的 diff 应恰为一行 `X_PROBE`）。

**Jev 分诊表（f21cd421，urgency 降序；③ 排序依据）**：

```
FILE                                   CHURN    URG   REVIEW  TEST  RISK          VERDICT
evidence-debt11/probe.py（证据副本）     +276/-0  2.72  0.75    0.52  api_contract  REVIEW(flag)
backend/app/graphiti/canvas_episode.py  +1/-0    0.03  0.17    0.39  test_or_docs  pass
```

## ② 作者自述（请独立核对，勿直接采信）

1. H1 已修：spec 冻结段现在逐键写死（边 10 键名 / relation 11 映射 / 嵌套 payload 字段 / EVOLUTION 5 值 / autofill anchor 语义）——与 `canvas_episode.py` 逐字对得上。
2. H2 已修：`ls-tree f21cd421` 含全部 `evidence-debt11/**`；spec 引用的复跑档均在绑定 commit 内。
3. H3 部分修：1-16 剩余面补 Task 8（e2e）；2-10 补 Task 7（failed_events）/ Task 8（e2e）；owner 写明「推荐落点 + 待登记」（正式归属需主 session，本卡无权定）。
4. H4 已修（回退）：两 story `status: backlog` + `superseded_by` / `superseded_at`；`grep -c 'status: superseded' sprint-status.yaml` = **0**（r1 前=2；回退依据 = validator 枚举 + 卡文预留路径）。
5. M1 登记（LITE-4-3/5-6 依赖重定向需主 session）；M2 已修（Dev Notes 注记）；M3 部分修（以 spec 为准注记；结构门 = 后续卡）。
6. L1 已修：spec 内行号现为 :225（Literal）/ :12、:185、:186（edge_type_map）；候选树 grep 实测 0 命中（rc=1）。
7. ② 后承重重验：D-32 AST `True` + diff 非 `#` = 0；复跑门 19 passed；unit 33 failed = 基线 33（nodeid diff 空；含已知 flaky `test_candidate_service::test_accept_candidate_already_accepted_returns_422`，其红档同时是 `blocked=1` 的来源——guard 归因 `owner=…test_candidate_service…`）；regression 1913 passed；pyright 0 errors；ruff rc=0 + F821 锚 rc=1；negctl① 恰 2 `DID NOT RAISE`、negctl② 恰 `test_callout_added_valid` + `D32-AST-EQUAL=False`，两段还原 shasum 前后逐字同；地盘 offwhite = 0、services/openapi = 0。
8. ⚠️ 保持的已知偏差：`ruff format --check` 对 `canvas_episode.py` 报警为 PREV 既有漂移（D-40 整仓 462 之一；交集证据 3 件在 `lint-exclude-justification*`），commit 用 `LEFTHOOK_EXCLUDE=python-lint`；⛔ 未排除 `python-typecheck`。

## ③ 按重要性排序的问题（逐项给结论）

- ⓪ Jev 分诊头名 `probe.py`（urgency 2.72 / REVIEW）：核实「D-32 验伪锚证据副本、无执行路径」的声明是否成立（对照输入：与 `canvas_episode.py` 的 diff 应恰一行）；若不成立或在哪个执行面可达，照报。
- ① r1 四条 HIGH 的处置是否到位：冻结面逐键枚举是否与代码**逐字**一致（含大小写/兜底语义）；证据入库是否完整；旧 spec 清单是否仍有漏；回退是否丢失必要信息。
- ② 冻结面还有漏吗：`EVOLUTION_EVENT_TYPES` 归类、`edge_name_for_relation` 的 lower()/兜底、`compute_event_id` 的 anchor 语义、`CalloutPayload.offset` 语义。
- ③ 旧 spec 剩余面清单（本轮补漏后）是否逐 Task 完整？
- ④ 其它真问题按 ④ 格式照报；「零代码路径本身 / 未实现 Task 3 / 无结构门」仍属既定范围，仅在认为裁定不成立时报。

## ④ 输出格式

- 每条：`[BLOCKER|HIGH|MEDIUM|LOW] <file>:<line> — <一句话说明>；<一句复现思路>`；
- 复现思路的措辞必须用：**负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**；
- 结论先行；末尾一行自检：`BLOCKER=<n> HIGH=<n> MEDIUM=<n> LOW=<n>`；用中文输出。

## ⑤ 边界

- 只读（sandbox read-only；不写文件、不连库、不连 7691/7687/7692）；
- 不评：P2 outbox 的 `episode_worker.py` / `memory_service.py` 改动设计；DEBT-12 facade 设计；5-ge-3 spec 改法；
- 不要求本卡实现 Task 3；不把「零代码 / 无新测试」本身当缺陷（卡文既定）。
