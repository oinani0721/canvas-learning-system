# 独立复核请求 — CARD-RED-R（tests/unit 红条目零代码定性）

## 一 背景与最小读取面（写死，请只读这些）

本卡是**零代码**的定性卡：对 `backend/tests/unit` 长期红基线（202 条）中被归为「真实现回归」的 26 条，加上 1 条被类级 `@pytest.mark.skip` 掩盖因而不在 202 内的条目（共 27 条），逐条在**独立的临时 git worktree** 里用 `git bisect` 定位「第一个把它弄红的 commit」（first-bad），再三选一定性（回归 / 契约演进 / 测试写错）并指定接收卡。本卡不改任何生产代码与测试代码。

仓库树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u5-lance`

请读：

1. 分派表（主产物）：`_bmad-output/审查/evidence-red-r/red-r-triage-20260909.md`
2. 全部 bisect 存档：`_bmad-output/审查/evidence-red-r/*-bisect.txt`（27 份）
   以及被推翻轮次的留档：同目录 `*-r1-candidate-refuted.txt` / `*-r2-refuted-836d0986.txt` / `*-r2-checkout-failed.txt` / `*-r1-refuted-836d0986.txt`
3. first-bad 上失败身份的单点探针：`_bmad-output/审查/evidence-red-r/probe-*.txt`
4. HEAD 上 26 条的失败身份：`_bmad-output/审查/evidence-red-r/failure-identities-20260909T121755.txt` 与 `failure-identities-tbshort-*.txt`；nodeid↔身份配对：`nodeid-to-identity.txt`
5. 第 27 条解 skip 后的身份：`_bmad-output/审查/evidence-red-r/qa386-fullcycle-identity-20260909T115052.txt`
6. 分母来源（**在另一棵树上，绝对路径**）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b13/red-align-da690bf8.md` 的 `:217-248` 与 `:367-373`
7. 验收单：`_bmad-output/验收单/UAT-CARD-RED-R-2026-09-09.md`
8. 每条 first-bad 的生产改动，请用 `git show <sha> -- <path>` 自取（本树内即可）：
   - `a9304c69` — `backend/app/services/agent_service.py` / `backend/app/api/v1/endpoints/review.py` / `backend/app/api/v1/endpoints/websocket.py` / `backend/app/clients/neo4j_edge_client.py` / `backend/app/services/intelligent_parallel_service.py` / `backend/app/services/memory_service.py`
   - `836d0986` — `backend/app/api/v1/endpoints/review.py`
   - `59586af1` — `backend/app/services/memory_service.py`
   - `3d10a02b` — `backend/app/services/memory_service.py`
   - `4236b12e` — `backend/app/services/memory_service.py`
   - `43294c38` — `backend/lib/agentic_rag/retrievers/vault_notes_retriever.py`
   - `89d51dc9` — `backend/lib/agentic_rag/clients/lancedb_client.py`
   - `1768c19d` — `backend/app/services/verification_service.py`
   - 另二处佐证：`f6a55d3a` — `backend/app/services/memory_service.py`；`e6fbd337` — `backend/app/services/memory_service.py`

## 二 作者自述（请独立核对，不要采信本节结论）

- 分派表表体恰 27 行，每行恰含 1 个 nodeid，与「26 条 + 第 27 条」集合双向 `comm` 为空。
- 定性分布：回归 19 / 契约演进 8 / 测试写错 0。
- 每条定性都配了 first-bad 的 hunk 或 commit message 原文；判「契约演进」的 8 条都能引到有意声明的原文（同 commit 内的注释或 message），判「回归」的都指出了生产 hunk 行。
- 两族「—」候选（`43294c38` group_filter ×4、`89d51dc9` strip_whiteboard ×1）经真二分**证实**，候选未被推翻；另有 5 条候选**被推翻**（epic30、difficulty ×2、qa/story_38_6 族）。
- 有 6 条实测到 first-bad 上的失败身份与 HEAD 不同，已逐条标注「first-bad 是首次变红点，非当前成因」并补充当前成因的实测出处。
- 第 27 条（`test_full_cycle_recovery_fails_then_merge`）与同 class 的 `test_full_cycle_fail_record_recover_merge` 都取到了失败身份，后者只记身份不定性。
- 生产 file:line 全部在 HEAD 上重新实测，未抄卡文旧行号。

## 三 请按重要性回答的问题

1. 标为「契约演进」的 8 条，其所引的「有意声明」是否真的与该次改动同批写入（而不是事后补写的注释、或只是描述性 docstring 跟随重写）？若有任何一条的声明强度不足以支撑「有意」，应改判为「回归」——请指出是哪几行。
2. 标为「回归」的条目，其 first-bad 的 hunk 与该条**当前**的失败身份是否因果对得上？特别请检查：是否存在「hunk 改的其实是同 commit 里另一处、与本条失败无关」的情况；以及被标注「first-bad ≠ 当前成因」的 6 条，其补充的当前成因是否证据充分。
3. `a9304c69` 族有 8 条。是否有任何一条的 first-bad 实际上不该是 `a9304c69`（例如更早就红、或该条的失败路径与 except 收窄无关）？该 commit 一次改了 251 处 / 65 文件，请重点看是否存在把「同族」当成「同因」的地方。
4. 接收卡命名是否可执行：`CARD-RED-R-FIX-*` 六个卡名在台账中是否重名（作者实测为 0 命中）；把 8 条契约演进移交 `U11-B RED-C2` 是否合理（U11-B 与本卡同批并行、尚未合并）。
5. 老 commit 上跑单个 nodeid 的 good/bad 判定，是否可能被环境差异污染（conftest 形态不同、依赖版本不同、模块缺失）而给出错误结论？作者在分派表 §六 列了 10 条已实测挡下的假绿路径与对应缓解，请评估这些缓解是否足够，以及是否有被遗漏的污染面。

## 四 输出格式

按 `BLOCKER / HIGH / MEDIUM / LOW` 分级，每条给出：分派表中的行号（或证据文件名 + 行号）、一句话依据。若某级别为空请显式写「无」。

## 五 边界

- 只读复核。不要修改任何文件，不要连接任何数据库或网络服务。
- 不要评价修复方案该怎么写（那是接收卡的事），只判断本卡的定位与定性是否站得住。
- 若判断需要更多证据，请明确指出「缺哪一份证据、该用什么命令取」，而不是替作者假设。
