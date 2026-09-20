> 批次: BATCH-2026-09-18-第十五批 · 车道 card-p1-storage · 卡 CARD-DEBT-11 round-1
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-DEBT-11.md)"`
> 审查绑定: `27743808`（本卡 commit ①；r1 送审时 HEAD 即此）
> 会话头自证（抄自 codex-review-CARD-DEBT-11.stderr，行号括注；stderr 不入库）:
> `2:OpenAI Codex v0.153.3` / `5:model: glm-5.3` / `9:reasoning effort: max`
---
**裁决（结论先行）**：代码面约束成立：`27743808^ == 6f25de8b`，除 `_bmad-output` 外唯一代码改动就是 `canvas_episode.py` +11 行注释，我独立复算 `ast.dump(PREV) == ast.dump(HEAD)` 为 `True`。但“schema 已冻结”和“旧需求已安全 supersede”这两个文档/治理目标目前是 **PARTIAL**：冻结清单不足以唯一定义契约，旧剩余面没有 owner，sprint-status 也会被 BMAD validator 判 invalid。

## 问题（按重要性）

- `[HIGH] _bmad-output/implementation-artifacts/epic-5a-graphiti-runtime/5-ge-1-canvas-graph-episode-v1.md:147-152 — 冻结面不能唯一定义 V1：edge/entity/relation 只写数量，不列逐键身份与映射；`CalloutPayload`/`ContextPayload`/各 edge payload 子模型未冻结；`event_id` 只冻结 hash 公式，未冻结 anchor 选择与 autofill 语义；负控输入：把 `Causes` 改名、把 `depends_on` 改映射、给 nested payload 增删字段、或把 `_autofill_event_id` 的 `belief_key or node_id` 改掉而保持 10/11 计数与公式文本不变，对照输入是当前代码逐键/嵌套 schema，这些均是未被拦下的输入。

- `[HIGH] _bmad-output/implementation-artifacts/epic-5a-graphiti-runtime/5-ge-1-canvas-graph-episode-v1.md:155 — spec 声称复跑证据在 evidence-debt11，但该目录完全没有进入绑定 commit `27743808`，当前只存在于工作树 untracked 状态；负控输入：`git -c core.quotePath=false ls-tree -r --name-only 27743808 | grep evidence-debt11` 为空，对照输入是当前工作树可读到的证据文件，fresh checkout / final-SHA binding 是门未覆盖的路径。

- `[HIGH] _bmad-output/implementation-artifacts/epic-1/1-16-callout-graphiti-hook.md:8 — 两旧 spec 的未并入剩余面只是“归属待登记”，没有新 owner 卡/队列项，且清单本身还有漏项（1-16 Task 8 e2e；2-10 Task 7 failed_events / Task 8 e2e 至少需显式裁定归属）；负控输入：grep sprint-status 与 live specs 中 `callout-sync.ts` / `wikilink-sync.ts` / endpoint / table / sweep，只剩 superseded 旧 entry 和“待登记”文字，对照输入是 5-ge-1 只冻结 schema 且 Task 3 移交，需求从 active queue 消失是未被拦下的输入。

- `[HIGH] _bmad-output/implementation-artifacts/sprint-status.yaml:495 — sprint-status 首次引入 story `status: superseded`（`:563` 同），但 BMAD sprint-status validator 的合法 story status 只有 `backlog/ready-for-dev/in-progress/review/done`（`_bmad/bmm/workflows/4-implementation/sprint-status/instructions.md:213-221`），当前文件会被 validate mode 判 invalid；负控输入：同 entry 改回任一合法 status，对照输入是当前 `superseded`，本卡未实际运行 validator 是门未覆盖的路径。

- `[MEDIUM] _bmad-output/implementation-artifacts/sprint-status.yaml:529 — `STORY-LITE-4-3` 仍依赖 `STORY-2-10-wikilink-graphiti-sync`，`:543` 的 `STORY-LITE-5-6` 同；被依赖项已变 `superseded` 但依赖方未改写或显式裁依赖，按“依赖全 done”规则会永久不可达；负控输入：对这两个 story 跑依赖可达性检查，对照输入是当前 superseded 依赖，未被拦下的输入是“superseded 被静默视为可满足/可忽略”。

- `[MEDIUM] _bmad-output/implementation-artifacts/epic-5a-graphiti-runtime/5-ge-1-canvas-graph-episode-v1.md:117-123 — Dev Notes 架构图仍要求 plugin POST `/api/v1/event/canvas-graph`、`canvas_graph_events` 表、worker“含 edge_type_map”，与 Task 3 移交 / Task 4-5 废弃裁定相矛盾；`:129-132` File Paths 也继续列 endpoint、worker、lancedb init；负控输入：未来开发者按 Dev Notes 实现旧端点/表/透传，对照输入是 Tasks/裁定段，这是未被拦下的输入。

- `[MEDIUM] backend/app/graphiti/canvas_episode.py:18-23 — py 头注释与 spec `:147-152` 各自复制一份冻结清单，且无机器一致性门，天然会漂移；负控输入：只改 py 清单或只改 spec 清单，对照输入是当前两边刚好一致，这是门未覆盖的路径。

- `[LOW] _bmad-output/implementation-artifacts/epic-5a-graphiti-runtime/5-ge-1-canvas-graph-episode-v1.md:145 — 冻结段多处引用/命中叙述已漂移：`:145` 写 `canvas_episode.py:214` 但 HEAD 的 `schema_version` 在 `:225`；`:161` 写 edge map 命中 `:174/:175` 但 HEAD 实际定义在 `:185-187`；`:162` 称 table/endpoint grep 命中两条 Source 注释，实测 `git grep -F` 对 `canvas_graph_events` / `event/canvas-graph` 均为 0（结论“零存在”仍成立，过程叙述不成立）；负控输入：逐条 `nl` / `git grep` 复算，对照输入是 spec 文字，这是文档核对门未覆盖的路径。

## 已核对通过 / 不作为缺陷

- **绑定与零代码**：`27743808` 的父提交确为 `6f25de8b`；commit 改动面为 5 个文件；排除 `_bmad-output` 后仅 `canvas_episode.py +11/-0`，全部为 `#` 注释；我独立 AST 比对结果 `True`。
- **顶层 schema 事实**：`CanvasGraphEpisodeV1` 当前 15 字段、`EventType` 7 值、edge dict 10 键、relation map 11 键，与 spec 的数量/顶层字段描述相符；问题在上面指出的“未逐项钉死”。
- **Task 3 移交事实**：`EpisodeTask` 只有 `entity_types`/`edge_types`（`episode_worker.py:85-86`），`_call_add_episode` kwargs 到 `:615` 仍无 `edge_type_map`；`memory_service.py:475-476,644-645,1656-1657` 也只传 entity/edge types。移交裁定本身成立。
- **Task 4/5 事实**：绑定 commit 的 `backend/app` 中无 `canvas_graph_events` 表、无 `/event/canvas-graph` 端点实现；“废弃于本 story”有代码事实支撑。
- **未接线本体冻结是否误导**：spec `:153` 明写“本次冻结 = schema 契约层；custom ontology 真生效不在完成度内”，这句足以防止把冻结误读为生产接线完成；不另报缺陷。
- **测试与负控存档内容**：测试文件确有 19 个 `test_`；open/close 存档均显示 19 passed。负控①红在两个 narrative `DID NOT RAISE`；负控②红在 `test_callout_added_valid` 且 `D32-AST-EQUAL=False`；meta 存档显示 mutation 前后文件 sha 一致。问题是这些证据未进 commit。
- **lint 偏差**：存档显示 worktree 与 PREV 的 format check 均 rc=1，format 想改的旧行段与本卡新增 `15-25` 行无交集，`ruff check` 绿；`python-typecheck` 未被排除且有 0 errors 存档。按第十四批 §一.1.7 口径，该偏差本身可接受。

BLOCKER=0 HIGH=4 MEDIUM=3 LOW=1
