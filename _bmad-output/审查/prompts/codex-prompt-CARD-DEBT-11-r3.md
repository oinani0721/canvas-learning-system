# Codex 复核 prompt — CARD-DEBT-11（round-3 · GLM-5.3 · 协议 §2.4）

> 批次 `BATCH-2026-09-18-第十五批` · 车道 `card-p1-storage` · 卡 `CARD-DEBT-11`（5-ge-1 `CanvasGraphEpisodeV1` schema 冻结 · **零代码路径**）
> 审查绑定：`4cc89ab3`（r2 整改后终态）· 基线 PREV = `6f25de8b` · 前两轮：r1=`27743808` / r2=`f21cd421`
> 你的沙箱是 read-only：用 git 只读命令与读文件完成核对；不要尝试写任何文件。

---

## ① 背景 + 最小读取面（写死）

**r2 结论（BLOCKER=0 / HIGH=2 / MEDIUM=1 / LOW=2）与整改对照**：

| # | r2 判定 | 处置（本 commit `4cc89ab3`） |
|---|---|---|
| H1 | edge payload 未字段级冻结（类型/默认值/必填）+ `CANVAS_EDGE_TYPE_MAP` 键对未冻结 | **已修**：spec 冻结段 v3——每个边 payload 逐字段（类型/默认值/必填）+ MAP 唯一键对 + 键序 |
| H2 | r2 作者自述的承重档未入绑定 commit | **已修**：r2 轮全部证据（d32-r2 / negctl1-r2* / negctl2-r2* / territory-r2-fixed2 / unit-r2 / regression-r2 / episode-v1-r2-pass / jev-triage-f21cd421 + r2 prompt/archive）随本 commit 入库 |
| M | `offset` 的 anchor 描述与真实 BeliefKeyResolver 不一致 | **已修**：删去错误派生描述；改引 `graphiti_belief_service.py:62-67`（`sha256(f"{node_path}:{offset}")[:16]`），并注明 anchor/belief_key 派生**不属** C-1 冻结面 |
| L1 | probe 声明不成立（diff 非恰一行） | **已修**：probe 重生成（= 当前 prod 副本 + 尾行 `X_PROBE`），diff 此刻恰 +1 行 |
| L2 | 行号漂移（edge_type_map / episode_worker 消费方） | **已修**：`:12/:186/:187`；`episode_worker.py:620` |

**最小读取面（逐条执行，均在车道树内）**：

1. `git --no-pager diff --no-color 27743808 4cc89ab3 -- . ':(exclude)_bmad-output'` → 预期**仅** `backend/app/graphiti/canvas_episode.py` 的 1 行 `#` 注释。
2. `git --no-pager diff --no-color 6f25de8b 4cc89ab3 -- _bmad-output/implementation-artifacts` → 4 文件全卡 diff（spec 冻结段已为 v3）。
3. `git --no-pager diff --no-color f21cd421 4cc89ab3 -- backend/app | wc -l` → **0**（prod 代码自 r2 审 SHA 起逐字节未变 ⇒ r2 轮全部承重档对 `4cc89ab3` 直接成立）。
4. `git -c core.quotePath=false ls-tree -r --name-only 4cc89ab3 | grep evidence-debt11 | wc -l` → **69**。
5. 冻结面核对：spec「## Schema 冻结声明」段 vs `backend/app/graphiti/canvas_episode.py:1-30`、`:70-100`（两 payload）、`:103-190`（实体/边/映射/edge_map）、`:208-277`（类 + validator + autofill + compute_event_id）。
6. 落点核对（只读）：`episode_worker.py:596-607`、`:620`；`memory_service.py:476,645,1657`；`graphiti_belief_service.py:62-67`、`:235`；`narrative_builder.py:12`。
7. 承重档（全部在 `4cc89ab3` 内，可 `git show 4cc89ab3:<path>` 读）：`evidence-debt11/` 下 `d32-r2-*`（True）、`negctl1-r2-*`（恰 2 DID NOT RAISE）、`negctl2-r2-*`（`test_callout_added_valid` + `D32=False`）、`territory-r2-fixed2-*`（offwhite=0）、`unit-r2-*`（33 = 基线 33）、`regression-r2-*`（1913 passed）、`episode-v1-r2-pass-*`（19 passed）、`probe-refresh-*`（重生成与验伪 False）、`lint-exclude-justification-refresh2-*`。
8. probe 声明自验：`git --no-pager show 4cc89ab3:backend/app/graphiti/canvas_episode.py | diff - <(git --no-pager show 4cc89ab3:_bmad-output/审查/evidence-debt11/probe.py)` → 恰一行 `> X_PROBE = 1`。
9. Jev 分诊（§2.4.3，送审前对 `4cc89ab3` 运行；JSON 落 evidence 目录、随收尾 commit 入库；本次结果内联）：

```
FILE                                   CHURN    URG   REVIEW  TEST  RISK          VERDICT
evidence-debt11/probe.py                +1/-0   0.05  0.23    0.35  test_or_docs  pass（零 flag）
（code_files=1，无 REVIEW 标记）
```

## ② 作者自述（请独立核对，勿直接采信）

1. r2-H1 已修：冻结段 v3 覆盖 1 实体 + 10 边 payload 逐字段（类型/默认值/必填）+ 2 嵌套 payload + 1 MAP 键对 + 11 relation 映射 + EVOLUTION 5 值 + autofill 语义——与 `canvas_episode.py:70-190` 逐字对得上。
2. r2-H2 已修：r2 自述的全部承重档 + r2 prompt/archive 均已在 `4cc89ab3`（计数 69；读取面 4 自验）。
3. r2-M 已修：offset/anchor 描述改为引 `graphiti_belief_service.py:62-67` 的真实语义（带 `:` 分隔与 `[:16]` 截断），并注明派生不属 C-1。
4. r2-L1 已修：probe = 当前 prod 副本 + `X_PROBE = 1`（读取面 8 自验）。
5. r2-L2 已修：`:12/:186/:187`、`episode_worker.py:620`、Literal `:225`。
6. 零代码保持：`6f25de8b→4cc89ab3` 的 prod 面仅 `canvas_episode.py` 12 行 `#`；D-32 `True`（r2 轮档内）；prod 自 r2 审 SHA 起逐字节未变（读取面 3）。
7. 已知偏差保持（连续两轮复核已接受）：`ruff format --check` 对 `canvas_episode.py` 报警为 PREV 既有漂移（D-40 整仓 462 之一；交集证据多件在档）；commit 仅排除 `python-lint`；⛔ **未**排除 `python-typecheck`。

## ③ 按重要性排序的问题（逐项给结论）

- ⓪ 冻结段 v3 是否仍有未钉死的面：逐字段核对（含默认值/必填性；`CANVAS_EDGE_TYPE_MAP` 键对与键序）。
- ① probe.py 声明（读取面 8）是否成立；若在任何执行面可达，照报。
- ② offset/anchor 引文是否准确（`:62-67` 与 `sha256(f"{node_path}:{offset}")[:16]`）。
- ③ 行号类复核（`:186/:187`、`:620`、`:225`）。
- ④ 其它真问题按 ④ 格式照报。「零代码路径 / 未实现 Task 3 / 无结构门」仍属既定范围，仅在认为裁定不成立时报。

## ④ 输出格式

- 每条：`[BLOCKER|HIGH|MEDIUM|LOW] <file>:<line> — <一句话说明>；<一句复现思路>`；
- 复现思路的措辞必须用：**负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**；
- 结论先行；末尾一行自检：`BLOCKER=<n> HIGH=<n> MEDIUM=<n> LOW=<n>`；用中文输出。

## ⑤ 边界

- 只读（sandbox read-only；不写文件、不连库、不连 7691/7687/7692）；
- 不评：P2 outbox 的 `episode_worker.py` / `memory_service.py` 改动设计；DEBT-12 facade 设计；5-ge-3 spec 改法；
- 不要求本卡实现 Task 3；不把「零代码 / 无新测试」本身当缺陷（卡文既定）。
