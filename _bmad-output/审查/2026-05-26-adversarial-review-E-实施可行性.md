---
title: "对抗审查 E — Sprint 2 末 (Day 10) Karpicke d=1.50 灰度 ship 可行性"
date: 2026-05-26
reviewer: "Claude Adversarial Implementation Auditor (independent agent)"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
audit_source:
  - "_bmad-output/research/2026-05-21-sprint-plan-v3.md"
  - "_bmad-output/implementation-artifacts/sprint-status.yaml (sprint_v3_obsidian_hybrid 段)"
  - "_bmad-output/审查/2026-05-26-chatgpt-v7-v8-v10-v11-修复回应.md"
  - "_decisions/CURRENT_TASK.md"
  - "docs/known-gotchas.md (37 条, 32 已修)"
  - "git log --since='2026-04-01' (337 commits)"
  - "backend/tests/unit/ pytest collect (3517 tests, 1 collection error)"
verdict: "NO-GO 灰度 ship · 概率 18%"
---

# 执行摘要

**Sprint 2 末 (Day 10) 真 ship Karpicke d=1.50 灰度版本成功概率 = 18%**.

证据链: (1) Sprint v3 plan 假设 26h/sprint 但近 7 天实际产出 = 1 commit, velocity 与 plan 脱节; (2) Sprint 1 Day 1 三 commit (`548d14d` / `769d59a`) **不在当前 worktree git log 中**, CURRENT_TASK 自己标注 "⚠️ 若 commit 不在 git log → 当前 worktree 没拉到 chat history 的实施 commit, 需用户介入确认"; (3) `backend/app/app_factory.py` 不存在, `backend/app/domains/exam/` 只有 `gateway.py + __init__.py` 两文件, INFRA-002 名义 done 实际产物缺失 → Sprint 1 起点已塌; (4) ChatGPT V-07/V-08/V-10 三 CRITICAL 修复方案 5.5h 仅 spec 级别落地, 触及的 `exam_tools.py:435-454` "Story 3.2 fix" 老妥协代码 + `wikilink-context.ts` plugin 新文件全部 0% 实施; (5) Day 6 起手任务 STORY-2-10 在新 session 无独立 ready-for-dev spec 路径打通, 5 min 启动 SOP 在 commit hash 失配场景下立即 halt.

# 1. 历史 velocity 推算表 (近 7 周)

| 周区间 | commit 数 | 主线工作 | 平均/工作日 |
|---|---:|---|---:|
| 2026-04-01 → 04-08 | 107 | Phase 0-1 架构理清 + S33 修复风暴 | 21.4 |
| 2026-04-08 → 04-15 | 44  | Round 4-7 Obsidian QA + 双 vault 决策 | 8.8 |
| 2026-04-15 → 04-22 | 29  | Round 8-12 决策 + EPIC 1 v2 完成 | 5.8 |
| 2026-04-22 → 04-29 | 0   | (空档期, 用户决策窗) | 0 |
| 2026-04-29 → 05-06 | 51  | Story 2.1-2.3 ship + ChatGPT 多轮 audit | 10.2 |
| 2026-05-06 → 05-13 | 75  | Story 2.2+2.9 wave 1-5 ship | 15.0 |
| 2026-05-13 → 05-20 | 30  | Story 2.4 callout + Plan-A 回退 | 6.0 |
| **2026-05-20 → 05-27** | **1** | **sprint-v3 BMAD 化 + ChatGPT 修复回应 (1 commit `16b648d`)** | **0.2** |

**关键事实**: Plan v3 假设 6h/day × 10 工作日 = 60h. 但近一周 velocity 已坍缩到 **0.2 commit/day**, 与 Plan 假设差 30x. 同期产出全部是文档 + spec, 0 backend 代码 commit. INFRA-002/001/004 标 done 的 commit hash (`548d14d` / `769d59a`) **在当前 worktree `git log` 中查不到** — sprint-status 头部 `commit: "548d14d"  # plan brief 提供; 当前 git log 未含, 验证待新 session 拉取` 明确招供该 commit 是"plan brief 提供" 非真实落地.

# 2. INFRA-002 名实背离 (Sprint 1 Day 1 起点已塌)

| 检查项 | 期望 | 实际 |
|---|---|---|
| `backend/app/app_factory.py` 存在 | ✅ 必有 (Sprint 1 Day 1 P0-1 deliverable) | ❌ 文件不存在 |
| `backend/app/interfaces/api/` 目录 | ✅ 含 18 router | ❌ 整目录不存在 |
| `backend/app/domains/exam/` 完整 | ✅ 含 question_generator + grader + scorer | ❌ 只有 `gateway.py` + `__init__.py` |
| `git log` 含 commit `548d14d` | ✅ Sprint 1 Day 1 完成证据 | ❌ 不在当前分支 |
| Plan 文件提及"接通"范围 | INFRA-002 = 4h | 实际等同于"重建后端框架" >> 4h |

**结论**: sprint-status 把"plan brief 写的 commit hash"当成"已 ship 状态" 是治理漏洞. **Sprint 2 Day 6 起手命令 (STORY-2-10) 在新 session 跑 §1 SOP 第 2 步立即 halt** (git log 无 `548d14d` → 需用户介入确认). 5 min 接续承诺破产.

# 3. Backend test debt 阻塞 V-10 修复链路

pytest 3517 收集成功 + **1 collection error** (`test_memory_service_contextvar_leak.py` 导入崩溃) + **test_mastery_fusion::TestPearsonCorrelation::test_no_correlation 失败**. memory project_backend_test_debt 记录的 "136 failures + 38 errors" 在 2026-04-07 审计时窄化到 A11 suite 才 green, 全量未恢复.

**V-10 修复触及代码 → 顺手必修测试**:

| V-10 修复点 | 涉及测试文件 (V-07/V-08/V-10 同 spec LITE-4-3) | 修改 ripple |
|---|---|---|
| `exam_tools.py:435-454` 删 Story 3.2 fix | `test_qa_38_6_scoring_reliability_extra.py` `test_story_38_6_scoring_reliability.py` `test_scoring_scale_fix.py` `test_scoring_faithfulness_not_applicable.py` | 4 套测试假设 `find_node_across_canvases` 是评分上下文真相源, 必须重写 |
| `questions_registry` LanceDB 新表 | `test_question_generator_mastery_data.py` (+ 缺失的 questions_registry 表 schema test) | 新增 schema + fixture |
| `score_answer` 强制回读 + 抛 `ScoringContextMissingError(422)` | `test_mastery_engine_bkt.py` `test_mastery_engine_fsrs.py` `test_mastery_fusion.py` `test_degraded_flag_propagation.py` `test_mastery_state.py` `test_mastery_store.py` | 6 套 BKT/FSRS 测试需重写"422 = 不计分"路径; `test_mastery_fusion.py::test_no_correlation` 当前已失败, 改动可能放大 |
| `pipeline_token` 增加 `question_text_hash` | `test_scoring_scale_fix.py` 系列 | token schema 测试连带改 |

**保守估算**: V-10 单点修复 = 代码 1h, 修测试 ≥ 4h. LITE-4-3 spec 新 estimate 6h 已经吃紧, 加上 V-07 hook + STORY-2-10 + V-11 总 13h 一并实施时, test 调整工作量未列入 Plan v3 capacity 模型.

# 4. 三条 "Sprint 2 末无法 ship" 硬证据 (CRITICAL/HIGH)

## CRITICAL-1: INFRA-002 deliverable 不存在 (Sprint 1 Day 1 假完成)

`_decisions/CURRENT_TASK.md::§1 step 2` 明文 "若 commit 不在 git log → 当前 worktree 没拉到 chat history 的实施 commit, 需用户介入确认". 但 sprint-status `INFRA-002.status=done` 已 mark. 5 个下游 ready-for-dev (INFRA-003 / EXAM-001 / EXAM-002 / TEST-001 / PLUGIN-002) 全部 `depends_on: ["INFRA-002"]`. **依赖链零落地**.

## CRITICAL-2: V-07 V-08 V-10 三 CRITICAL 修复 ChatGPT 仅 spec 级写完, 0% 代码落地

`_bmad-output/审查/2026-05-26-chatgpt-v7-v8-v10-v11-修复回应.md::status: spec-patched`. ChatGPT 一句话判定: "**整体学习效果落地度 58%**, **不能直接 ship 给 CS 61B 学生使用**". 修复总工时 5.5h spec 内 + 实际代码 (含 `frontend/obsidian-plugin/src/wikilink-context.ts` 文件新建 — 当前不存在) + `backend/scripts/wikilink_batch_sweep.py` 扩展 + LanceDB `questions_registry` 表 schema + 删 `exam_tools.py:435-454` 老妥协 + 4-6 套 mastery test 重写 = 现实 ≥ 12-15h. Sprint 2 Day 6-10 剩 25h, 已被 INFRA-006 (4h) / EXAM-003 (3h) / MASTERY-001+002 (6h) / TEST-002 (4h) / INFRA-007 (1h) / STORY-2-10 (6h) / DOC-001 (3h) / VERIFY-001 (4h) = 31h 占满, 已超 Day 6-10 容量.

## HIGH-3: MVP-α 路径承认违反 DD-03 (in-memory ring buffer = 妥协)

`backend/app/api/v1/endpoints/exam_quick.py:9` 文件头 docstring 招供:
> `# 闭环优先于精度: in-memory ring buffer, 重启清空 (与 Anki/Duolingo 第一版同思路).`

行 41-47:
```
_QUESTION_STORE: Dict[str, Dict[str, Any]] = {}
_QUESTION_STORE_MAX = 200  # FIFO ring buffer; 重启清空 MVP 故意为之
```

mock-import-guard.js hook 只阻 `from unittest.mock` / `MagicMock(`, **不阻 in-memory dict 假持久化**. DD-03 "禁 stub / fake API / 空函数" 字面允许了"故意 MVP" 这条逃逸通道, 但题目要求 "Karpicke d=1.50 灰度" 即 testing effect 长期记忆增强, 后端重启=数据丢=学习信号断裂, 与 d=1.50 学术目标直接冲突. 灰度试用 ≥ 1 周, 后端任何重启 (Docker 更新 / 配置切换 / 崩溃) 都让 `question_id` lookup 全 404, 评分链断裂.

# 5. DD-03 mock 妥协清单 (MVP-α 路径)

| 文件 | 妥协形式 | 影响 | 触发 hook? |
|---|---|---|---|
| `backend/app/api/v1/endpoints/exam_quick.py:41-54` | `_QUESTION_STORE` in-memory ring buffer + `_evict_if_full()` FIFO 200 题 | 重启清空, 灰度试用期评分链断 | ❌ 不触 (hook 只查 unittest.mock 关键字) |
| `backend/app/api/v1/endpoints/exam_grade.py:28` | `from app.api.v1.endpoints.exam_quick import get_question_record` | exam_grade 完全依赖 in-memory store, 重启后所有题不可评 | ❌ 不触 |
| `backend/app/api/v1/endpoints/exam_grade.py:37-46` | `_GRADE_SYSTEM_PROMPT` 单 prompt 简化 AutoSCORE 4 维 ×3 投票 → 单 LLM call 0-5 整数 | 评分粒度从 4 维降到 1 维, BKT 信号丢失 | ❌ 不触 |
| `backend/app/mcp/tools/exam_tools.py:435-454` | "Story 3.2 fix": 用 `find_node_across_canvases(node_id)` 取 node content 当 scoring context | V-10 SCORING_TARGET_DRIFT, 评分按节点正文非题面 | ❌ 不触 |
| `backend/app/services/question_generator.py` | `generate_question()` 走 ACP 但 LITE-4-3 简化版砍 wikilink 邻居 | V-08 WIKILINK_NOT_IN_EXAM_PATH, 出题只考"单节点回忆" | ❌ 不触 |

**结论**: 现有 `.claude/hooks/mock-import-guard.js` 只阻 `unittest.mock` import, 完全漏过"in-memory dict 假持久化" 和"老妥协代码注释招供" 两类 DD-03 真实违规. MVP-α 路径名义没 mock, 实质是 5 处妥协叠加.

# 6. G-FAKE / G-PIPE 风险撞车

V-07 修复要让 callout → Graphiti episode 写入. `docs/known-gotchas.md::G-FAKE-001` 标注 32 函数已 S34 重命名 (`GraphitiEdgeClient → Neo4jEdgeClient`), 但 "残留：API 模型名+config 属性 (API 兼容性保留)". STORY-1-16-callout-graphiti-hook 新增 `callout_events` LanceDB 表 + 复用 STORY-2-10 `events_queue + sweep cron`, 名义调 `add_episode` 进 Graphiti, 实际管道:

- callout 写 plugin `callout-sync.ts` (新文件, 不存在) → 
- backend `event.py` (新增 endpoint, 不存在) → 
- `events_queue` LanceDB 表 → 
- `wikilink_batch_sweep.py` cron (扩展) →
- `episode_worker.py` 调 `add_episode_for_edge` (G-FAKE-002 标已修, 但回归测试是否覆盖 callout 路径未知)

**G-PIPE 风险**: STORY-2-10 + STORY-1-16-hook 是 Sprint 2 末才同期实施的 **两条新管道**, 共用 events_queue + sweep, 两边任一断点 = callout 写不进 Graphiti, search_facts 查不出探索路径 = V-07 修复 0 效果. Plan v3 没列 "管道接通验证" task, DoD-1 "tests 通过" 在新管道零测试覆盖时形同虚设.

# 7. 结论

**Sprint 2 末无法 ship 灰度试用. INFRA-002 deliverable 不存在 + ChatGPT 3 CRITICAL 仅 spec 修 0 代码 + 近 7 天 velocity 0.2 commit/day, 三者叠加把 18% 概率打到地板. 建议先用 1 周补 Sprint 1 真实落地 (INFRA-002~005 + EXAM-001/002 接通) 再讨论 d=1.50 灰度.**
