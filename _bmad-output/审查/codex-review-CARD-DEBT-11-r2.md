> 批次: BATCH-2026-09-18-第十五批 · 车道 card-p1-storage · 卡 CARD-DEBT-11 round-2
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-DEBT-11-r2.md)"`
> 审查绑定: `f21cd421`（本卡 commit ②；r2 送审时 HEAD 即此）
> 会话头自证（抄自 codex-review-CARD-DEBT-11-r2.stderr，行号括注；stderr 不入库）:
> `2:OpenAI Codex v0.153.3` / `5:model: glm-5.3` / `9:reasoning effort: max`
---
**裁决（结论先行）：PARTIAL，不建议以当前材料关闭 round-2。**  
`f21cd421` 的最终 SHA 绑定、零代码 AST 等价、r1 spec 所引用证据入库、sprint-status 枚举回退、旧 spec 剩余面补漏这些主轴成立；但 **H1 的冻结面仍不足以唯一定义 edge payload 契约**，且 **round-2 作者自述依赖的多数承重档仍是 f21 后未跟踪文件**。因此不能把 r1 整改判定为全绿。

## 独立核对通过 / 不作为缺陷

- **绑定与零代码**：当前 HEAD 就是 `f21cd4217375af62a7b05bef58633ed51a0244d1`，其父提交正是 r1 SHA `2774380842708660b63c64bff08a8193711f3962`；`6f25de8b` 与 `27743808` 均为祖先。排除 `_bmad-output` 后，`27743808→f21cd421` 仅 `backend/app/graphiti/canvas_episode.py` 新增 1 行 `#` 注释。我独立复算 `ast.dump(PREV) == ast.dump(HEAD)` 为 **True**。
- **实施 artifact 范围**：`6f25de8b→f21cd421` 在 `_bmad-output/implementation-artifacts` 下仅改 4 个预期文件：两旧 spec、5-ge-1 spec、sprint-status。
- **H2 的 f21/spec 引用面**：`evidence-debt11` 在 f21 中恰有 **50** 个 tracked 条目；spec 引用的 `episode-v1-open-*` / `episode-v1-close-*` 均在 f21 内，存档均显示 19 passed。
- **H4 回退**：两 story 在 sprint-status 中均为合法 `status: backlog`，保留 `superseded_by` / `superseded_at`；`grep -c 'status: superseded' sprint-status.yaml` 实测 **0**。旧 spec md frontmatter 的 `superseded` 不受本次 sprint-status validator 枚举约束。
- **H3 剩余面**：1-16 Task 1/1.5/2、3/4、5-7、8 均已列入；2-10 Task 1/2、3/4、5/9/10、7、8 均已列入。Task 6 的旧 batch episode body/helper 被 unified schema 取代，按“已并入/废弃”解释不算漏项。
- **⓪ probe.py 实质结论**：未发现仓库内 import / pytest / pyright / lefthook 自动执行路径；`pytest` rootdir 在 backend 且 `testpaths=tests`，pyright include 不含 `_bmad-output`，python-lint glob 只覆盖 `{backend,src,scripts}/*.py`。去掉尾部 `X_PROBE` 后，probe 与 f21 production AST 相等。因此 Jev 的 api_contract 风险是复制副本造成的 churn 误标，不是生产可达面。
- **候选树 grep**：`canvas_graph_events` 与 `event/canvas-graph` 在 `backend/app` 下实测均 0 命中，rc=1；该裁定成立。

## 问题（按重要性）

- `[HIGH] _bmad-output/implementation-artifacts/epic-5a-graphiti-runtime/5-ge-1-canvas-graph-episode-v1.md:152 — H1 仍未完全闭环：edge payload 只冻结键名/+字段名，未冻结 statement/strength/callout_type/error_type/vote 的类型、默认值与必填性，也未显式冻结 CANVAS_EDGE_TYPE_MAP 的唯一 ("CanvasNode","CanvasNode") pair；负控输入：把 Prerequisite.strength 默认 "strong" 改 "weak" 或改类型、把 SelfAnnotation.callout_type 改必填、或改 CANVAS_EDGE_TYPE_MAP pair，现有测试只断言 10 数量和两个成员名，这些都是未被拦下的输入（对照输入是 canvas_episode.py:113-188 的完整字段/默认值）。`
- `[HIGH] _bmad-output/审查/evidence-debt11/d32-r2-20260920T003218.txt:1 — round-2 作者自述的多数承重档没有进入绑定 commit f21cd421，当前只是工作树 untracked（d32-r2、negctl1/2-r2、territory-r2-fixed2、unit-r2、regression-r2、episode-v1-r2-pass、Jev f21 分诊均不在 f21；仅 lint refresh2 已入库）；负控输入：`git -c core.quotePath=false ls-tree -r --name-only f21cd421 | grep '^_bmad-output/审查/evidence-debt11/' | grep -E 'd32-r2|negctl1-r2|negctl2-r2|territory-r2-fixed2|unit-r2|regression-r2|jev-triage-f21'` 为空，对照输入是当前工作树文件，fresh checkout / final-SHA binding 是门未覆盖的路径。`
- `[MEDIUM] _bmad-output/implementation-artifacts/epic-5a-graphiti-runtime/5-ge-1-canvas-graph-episode-v1.md:154 — CalloutPayload.offset 的“anchor = sha256(node_path+offset)”未写分隔符和截断，与真实 BeliefKeyResolver 语义不一致；负控输入：node_path="a"、offset=1 时按 spec 直接拼 "a1" 求完整 SHA-256，对照输入是 graphiti_belief_service.py:63-65 的 `sha256(f"{node_path}:{offset}")[:16]`，按错误锚生成 belief_key 是未被拦下的输入。`
- `[LOW] _bmad-output/审查/evidence-debt11/probe.py:276 — “与 f21 canvas_episode.py diff 恰一行 X_PROBE”的声明不成立：f21 diff 实际同时缺少新增的 :26 “以 spec 为准”注释并追加 X_PROBE；复现思路：对照输入是 `git diff f21cd421:backend/app/graphiti/canvas_episode.py f21cd421:_bmad-output/审查/evidence-debt11/probe.py`（1 insertion + 1 deletion），对照输入是 `27743808` 源文件时才恰为 +X_PROBE，最终 SHA 对齐核对是门未覆盖的路径。`
- `[LOW] _bmad-output/implementation-artifacts/epic-5a-graphiti-runtime/5-ge-1-canvas-graph-episode-v1.md:167 — L1 只部分修复：edge_type_map 实际命中是 :12/:186/:187 而非 :12/:185/:186，且 :160 的 episode_worker 消费方实际 import 在 :620 而非 :618；复现思路：对照输入是 `git show f21cd421:<path> | nl -ba` 逐行复核，Literal :225 与候选树 0 命中已正确，剩余行号漂移是门未覆盖的路径。`

## 边界与限制

- 本次保持只读；未连接 7691/7687/7692，未复跑 pytest / pyright / ruff，也未执行任何 mutation。测试结论只区分“f21 内存档可复核”与“round-2 unclaimed/untracked 自述不可绑定”。
- 未评审且不作为缺陷：P2 outbox 的 `episode_worker.py` / `memory_service.py` 设计、DEBT-12 facade、5-ge-3 spec 改法、未实现 Task 3、零代码路径本身、无结构门本身。

BLOCKER=0 HIGH=2 MEDIUM=1 LOW=2


