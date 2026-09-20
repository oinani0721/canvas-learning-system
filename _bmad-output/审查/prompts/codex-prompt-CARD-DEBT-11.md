# Codex 复核 prompt — CARD-DEBT-11（round-1 · GLM-5.3 · 协议 §2.4）

> 批次 `BATCH-2026-09-18-第十五批` · 车道 `card-p1-storage` · 卡 `CARD-DEBT-11`（5-ge-1 `CanvasGraphEpisodeV1` schema 冻结 · **零代码路径**）
> 审查绑定：`27743808`（本卡唯一 commit）· PREV = `6f25de8b`（P1-C 末 commit）
> 你的沙箱是 read-only：用 git 只读命令与读文件完成核对；不要尝试写任何文件。

---

## ① 背景 + 最小读取面（写死）

**卡的目标（零代码冻结卡）**：把 C-1 写入契约 `CanvasGraphEpisodeV1`（`backend/app/graphiti/canvas_episode.py:208`；2026-06-03 后零改动；3 个生产消费方在用）**正式冻结**：

1. 裁 Task 3/4/5 归属（Task 3 落点全在 P2 地盘 ⇒ 移交；Task 4/5 表/端点候选树零存在 ⇒ 废弃）；
2. 复跑 `test_canvas_episode_v1.py` 19 用例存档；
3. py 头注释 + spec 写冻结声明（版本 + 15 字段 + 禁改规则）；
4. spec `in-progress`→`review`、sprint-status `ready-for-dev`→`review`、两旧 spec `1-16-callout-graphiti-hook` / `2-10-wikilink-graphiti-sync` 改 `superseded`。

**默认零代码**：唯一 .py 改动 = `canvas_episode.py` 的 11 行 `#` 注释；D-32 用 `ast.dump` 机器比对前后逐字同（`True`），diff 非 `#` 行 = 0（证据在下）。

**最小读取面（逐条执行，均在车道树内）**：

1. `git --no-pager diff --no-color 6f25de8b 27743808 -- . ':(exclude)_bmad-output'` → 预期**只有** `backend/app/graphiti/canvas_episode.py` 的 `#` 行（+11/−0）。
2. `git --no-pager diff --no-color 6f25de8b 27743808 -- _bmad-output/implementation-artifacts` → spec / sprint-status / 两旧 spec 四文件。
3. `backend/app/graphiti/canvas_episode.py:1-30`（头注释块含冻结声明）+ `:208-265`（`CanvasGraphEpisodeV1` 全貌 + `compute_event_id`）。
4. spec 全文：`_bmad-output/implementation-artifacts/epic-5a-graphiti-runtime/5-ge-1-canvas-graph-episode-v1.md`（含新增「## Schema 冻结声明（2026-09-18，CARD-DEBT-11）」与「### 裁定 2026-09-18 (CARD-DEBT-11)」）。
5. `_bmad-output/implementation-artifacts/sprint-status.yaml:490-500,558-572,605-625,680-690`。
6. `backend/app/services/episode_worker.py:85-86,596-613`（Task 3 移交证据；只读——本卡对该文件**零改动**）。
7. `_bmad-output/implementation-artifacts/epic-5a-graphiti-runtime/5-ge-3-query-time-flush.md:28-36`（Task 4/5 互指证据；只读，本卡零改动）。
8. `backend/tests/unit/test_canvas_episode_v1.py` 全文（19 用例）。
9. 证据：`_bmad-output/审查/evidence-debt11/` 下 `d32-ast-equivalence-*.txt`、`negctl1-narrative-*.txt`、`negctl1-meta-*.txt`、`negctl2-literal-*.txt`、`negctl2-ast-*.txt`、`negctl2-meta-*.txt`、`lint-exclude-justification-*.txt`、`format-diff-*.txt`。
10. 第十四批裁定书 `_bmad-output/审查/2026-09-15-第十四批复核裁定与待裁决登记.md` 中 D-32 / D-15 段落（口径背景）。

**Jev 分诊表（本卡 diff，urgency 降序；仅供 ③ 排序参考）**：

```
FILE                                        CHURN    URG   REVIEW  TEST  RISK          VERDICT
backend/app/graphiti/canvas_episode.py      +11/-0   0.41  0.51    0.44  test_or_docs  pass
（code_files=1；零 REVIEW 标记 ⇒ ③ 按卡文风险序列问）
```

## ② 作者自述（请独立核对，勿直接采信）

1. 冻结面与代码**逐字对得上**：15 字段（名/类型/必填性）、`EventType` 7 值、`CANVAS_GRAPH_EDGE_TYPES` 10 键、`RELATION_TYPE_TO_EDGE_NAME` 11 键、`compute_event_id` 公式 —— spec 冻结段 vs `canvas_episode.py` 实测。
2. Task 3 = 移交：落点 `episode_worker.py:596-607` kwargs / `EpisodeTask:85-86` / `memory_service.py:476,645,1657` 全在 P2 地盘（本卡零实现、零改动）。
3. Task 4/5 = 废弃：`canvas_graph_events` 表 / `POST /api/v1/event/canvas-graph` 在候选树零存在（grep 只命中 `[Source:]` 注释）；5-ge-3 :32 与 5-ge-1 D5 互指无 owner，只登记不改。
4. 旧 spec supersede 的「剩余面」列举完整（1-16：plugin `callout-sync.ts` 采集/双链上下文/端点/表/sweep/时序/重试；2-10：plugin `wikilink-sync.ts` 采集/端点/表/hourly sweep/分块/性能）。
5. D-32：`ast.dump(6f25de8b:py) == ast.dump(worktree py)` → `True`；`git diff` 非 `#` 行 = 0；验伪锚 `probe.py`（加一行真代码）→ `False`。
6. 承重档：复跑门 19 passed（开工/收工各一次）；unit 目录级对基线 diff 只 `<`；regression 1913 passed；pyright `0 errors` ×3；ruff rc=0 + F821 锚 rc=1。
7. ⚠️ 已知偏差（如实登记）：`ruff format --check` 对 `canvas_episode.py` 报警为 **PREV 既有漂移**（D-40 整仓 462 漂移之一；交集证据 = `lint-exclude-justification-*.txt` 三件），故 commit 用了 `LEFTHOOK_EXCLUDE=python-lint`；⛔ **未**排除 `python-typecheck`（hook 实际跑过并绿）。

## ③ 按重要性排序的问题（逐项给结论）

- ⓪ 冻结声明是否把「就地改 V1」的每条路（字段 / enum 值 / 边类 / relation map / event_id 公式）都堵在文字里，还是留了口子？
- ① Task 3 移交后 `edge_type_map` 零透传：冻结一个未接线本体是否合理？spec 冻结段已明写「本次冻结 = schema 契约层；custom ontology 真生效不在完成度内」——请核这句是否防止误读。
- ② 旧 spec 标 `superseded` 后其**未被并入**的剩余需求（plugin 采集 / sweep）是否真有 owner，还是从登记面消失？
- ③ sprint-status 首次引入 `status: superseded` 对 dev-story / sprint-status 工具链的解析风险（本卡只 grep，未跑那两个工具）。
- ④ 负控两段是否各自只拆一层、红在指定断言、还原可证（看 negctl 存档：段① `DID NOT RAISE`×2；段② `test_callout_added_valid` + `D32-AST-EQUAL=False`）。
- ⑤ 冻结清单两份（py 注释 vs spec 冻结段）是否会漂移（是否应只在一处列字段、另一处引用）？
- ⑥ 你若发现其它真问题，按 ④ 格式照报。**注意**：本卡是既定零代码冻结卡，「未实现 Task 3 / 无结构门」属已裁定范围，仅当你认为裁定本身不成立时才报。

## ④ 输出格式

- 每条：`[BLOCKER|HIGH|MEDIUM|LOW] <file>:<line> — <一句话说明>；<一句复现思路>`；
- 复现思路的措辞必须用：**负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**；
- 结论先行（一两句裁决）；末尾一行自检：`BLOCKER=<n> HIGH=<n> MEDIUM=<n> LOW=<n>`（某级为 0 也写）；
- 用中文输出。

## ⑤ 边界

- 只读（sandbox read-only；不写文件、不连库、不连 7691/7687/7692）；
- 不评：P2 outbox 的 `episode_worker.py` / `memory_service.py` 改动设计；DEBT-12 facade 设计；5-ge-3 spec 改法（本卡无权改）；
- 不要求本卡实现 Task 3；不把「零代码 / 无新测试」本身当缺陷（卡文既定）。
