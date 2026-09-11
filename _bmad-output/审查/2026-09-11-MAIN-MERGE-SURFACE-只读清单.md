# MAIN-MERGE-SURFACE：`main` ↔ feature 主干冲突面只读清单（2026-09-11）

> 来源：台账 §三.14(b)；第十一/十二/十三批均登记「main→feature 13 文件冲突面未动」。本文件 = 只读实测（`git merge-tree --write-tree`，零写入），**第十四批不排合并**（勘探 A C-12：独立前置卡或放弃，待用户裁）。
> 实测：merge-base `671ae7e7`；`main` 领先 **9** commit（`bb00ed56`…`a55db2ab`，2026-04-17 ～ 2026-08-17 的 Tauri 时期 / Epic-1 修复）；feature 领先 669 commit；`main` 相对 merge-base 改 **35** 文件，其中 **26** 也在 feature 侧改过；`git merge-tree --write-tree <feature> main` 报 **13** 个冲突（恰与台账「13 文件」一致）。

## 一、13 个真冲突文件（merge-tree 实测）

| 类型 | 文件 |
|---|---|
| content | `.gitignore` |
| content | `backend/app/api/v1/endpoints/tips.py` |
| add/add | `backend/app/graphiti/group_id_compat.py` |
| content | `backend/app/main.py` |
| content | `backend/app/services/episode_worker.py` |
| content | `backend/app/services/error_classifier.py` |
| add/add | `backend/app/services/graphiti_belief_service.py` |
| content | `backend/app/services/memory_service.py` |
| content | `backend/app/services/question_generator.py` |
| add/add | `backend/scripts/verify_targeted_exam_chain.py` |
| add/add | `backend/tests/unit/test_error_classification_mapping.py` |
| add/add | `canvas-vault/节点/my-recursion-notes.md` |
| content | `docker-compose.yml` |

## 二、`main` 领先的 9 个 commit
```
a55db2ab chore(gitignore): 排除 manifest 快照缓存与 raw 课程材料 (R11-BATCH2-2026-08-17)
2c5a4683 fix(config): 权重配置对齐生产分支 + 移除 data 挂载地雷 (R11-BATCH2-2026-08-17)
44113f54 chore(vault): T0 成员真相源单一化 — source_board 回填+测试节点清理 (RAG-S2.5-2026-08-10)
066da2a7 feat(kg): Fix-E1 节点 frontmatter relationships 同步成 CANVAS_EDGE 原因边
a4ff09f4 fix(memory): Fix-D 同步直写 node_id-keyed EpisodicNode 打通针对性考察主链
9149a73c test(exam-chain): 端到端验证 harness — 批注/节点+原因→针对性考察主链
33662d65 feat(graphiti): S2-2 belief 时序版本链 + 统一 episode schema
25f94c41 fix(backend): 恢复未提交 backend 批次 P0-1~P0-7 + Story 2.5/2.1
bb00ed56 fix(epic-6): V-10 评分对象漂移修复 — score_answer 回读真实题面
```

## 三、`main` 侧 35 文件全表（M/A/D 相对 merge-base）
M `.gitignore` · M `backend/app/api/v1/endpoints/tips.py` · M `backend/app/core/memory_format.py` · A `backend/app/graphiti/canvas_episode.py` · M `backend/app/graphiti/entity_types.py` · A `backend/app/graphiti/group_id_compat.py` · A `backend/app/graphiti/narrative_builder.py` · M `backend/app/main.py` · M `backend/app/mcp/tools/exam_tools.py` · M `backend/app/services/episode_worker.py` · M `backend/app/services/error_classifier.py` · A `backend/app/services/graphiti_belief_service.py` · M `backend/app/services/learning_context_service.py` · M `backend/app/services/memory_service.py` · A `backend/app/services/node_relationship_sync_service.py` · M `backend/app/services/question_generator.py` · A `backend/app/services/question_registry.py` · M `backend/data/reference_priority.json` · A `backend/scripts/verify_targeted_exam_chain.py` · A `backend/tests/unit/test_belief_version_chain.py` · A `backend/tests/unit/test_canvas_episode_v1.py` · A `backend/tests/unit/test_error_classification_mapping.py` · A `backend/tests/unit/test_fix_d_exam_queryable_episode.py` · A `backend/tests/unit/test_fix_e1_node_relationship_sync.py` · A `backend/tests/unit/test_question_registry.py` · M `backend/tests/unit/test_s02_entity_types.py` · A `canvas-vault/.claude/hooks/session-end-archive.py` · A `canvas-vault/检验白板/考察-Fundamentals-2026-07-16.md` · D `canvas-vault/节点/TestConceptA.md` · D `canvas-vault/节点/TestConceptB.md` · D `canvas-vault/节点/TestConceptC.md` · M `canvas-vault/节点/cs-61b-csm.md` · M `canvas-vault/节点/csm-tutoring-unit-credit.md` · A `canvas-vault/节点/my-recursion-notes.md` · M `docker-compose.yml`

## 四、处置口径（待用户裁 C-12）
- 甲：第十五批立独立前置卡「MAIN-MERGE」，先裁 9 个 commit 逐条「feature 已等价实现 / 需移植 / 放弃」，再做一次 `main` → feature 的真 merge（冲突 13 文件逐个人裁），主 session 执行。
- 乙：宣布 `main` 冻结为历史（Tauri 时期），feature 主干成为唯一开发主干，`main` 不再合入；本清单归档。
- 本批默认：**不动**（只出清单）。

## 五、本清单未证明什么
- 未逐 commit 核 9 个 `main` commit 的内容是否已在 feature 侧等价实现（add/add 冲突的 4 个文件强烈暗示两侧各自实现过同名模块）。
- 未跑任何测试；`merge-tree` 只报文本冲突，语义冲突（同名不同实现）不在其覆盖面。
