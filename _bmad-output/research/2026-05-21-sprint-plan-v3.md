---
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
sprint: "Sprint 1+2 v3 (基于 ChatGPT v2 改判 + 3 agent 验证)"
date: "2026-05-21"
basis:
  - "ChatGPT v1 报告 (2026-05-21 第一次对抗审查 — 22-30 人日 4 主线)"
  - "ChatGPT v2 报告 (2026-05-21 第二次对抗审查 — 5 问题答复 + 改判)"
  - "Agent A 验证 ChatGPT 10 个新发现 (9 对 1 错)"
  - "Agent B 4 方对照 (4 agent + v1 + v2 + 我 v1)"
  - "Agent C Sprint Plan 重写"
total_estimate: "52h (Sprint 1 26h + Sprint 2 26h)"
status: "ready-to-execute-pending-5-decisions"
supersedes: "2026-05-21-sprint-1-2-backlog.md (v1)"
---

# Sprint Plan v3 — canvas-obsidian-hybrid 接通工作

## Context

ChatGPT 第 2 次对抗审查 (2026-05-21) 给出 5 个核心改判 + 7 个新 DEAD CODE 发现。Agent A 验证后：
- ✅ 9 个发现真实 (含 7 个新 DEAD CODE + main.py 空 stub + docker-compose 路径错配)
- ❌ 1 个误判 (SCORE_SUBMITTED 订阅其实存在于 `handlers.py:35-100 + 400-405`)

Agent B 4 方对照 (4 agent + ChatGPT v1 + ChatGPT v2 + 我 v1) 后整合最终 3 类清单 v3。Agent C 重写 Sprint Plan。

**核心改判**: Sprint Day 1 第 1 个 Story 从 INFRA-001 (EventBus bug) 改为 **INFRA-002 (app_factory 装路由)**。理由：main.py 只 `/healthz`, 不先装路由修 EventBus 也无 endpoint 调用。

---

## Sprint 1 — Week 1, 5 工作日, 26h

> 主线: **入口收敛 + 契约锁定**

### Day 1 (Mon, 6h)

| 优先级 | Story ID | 标题 | 估时 | 文件 |
|---|---|---|---|---|
| ⭐ P0-1 | **INFRA-002** | **app_factory + APIRouter 装配** (第 1 优先) | 4h | 新建 `backend/app/app_factory.py` + 改 `backend/app/main.py` |
| P0-2 | INFRA-001 | grading.py EventBus 签名修复 | 1h | `backend/app/domain/exam/grading.py:96` |
| P0-3 | INFRA-004 | pyproject.toml 加真实 deps | 1h | `backend/pyproject.toml` |

**Day 1 验收**:
- `uvicorn app.main:app --reload` 启动
- `curl GET /api/v1/health` 返回 200
- `curl POST /api/v1/exam/start` 不再 404
- 评分调 grade_answer() 不抛 TypeError

### Day 2 (Tue, 6h)

| 优先级 | Story ID | 标题 | 估时 | 文件 |
|---|---|---|---|---|
| P0-4 | INFRA-003 | docker-compose healthcheck 路径修复 | 1h | `backend/docker-compose.yml`, `interfaces/api/health.py` |
| P0-5 | EXAM-001 | POST /api/v1/exam/grade endpoint | 3h | `backend/app/interfaces/api/exam.py` + 注册 |
| P0-6 | EXAM-002 | POST /api/v1/exam/quick endpoint | 2h | 同上 |

**Day 2 验收**:
- `curl POST /api/v1/exam/grade {...}` 返回 4 维 `AutoScoreResult`
- `curl POST /api/v1/exam/quick {...}` 返回 `question_id + tip 引用题目`
- `docker compose ps` 显示 backend healthy

### Day 3 (Wed, 6h)

| 优先级 | Story ID | 标题 | 估时 | 文件 |
|---|---|---|---|---|
| P1-1 | INFRA-005 | _stubs.py 改 fail-loud (改 warning log) | 1h | `backend/app/_stubs.py` |
| ⭐ P1-2 | **TEST-001** | 解除 contract test skip (提前) | 4h | 新建 `tests/contract/test_exam_endpoints.py` + `test_vault_endpoints.py` |
| P1-3 | PLUGIN-001 | 抽取 plugin/src/backend-client.ts | 1h | 新建 `plugin/src/backend-client.ts` + 改 `main.ts::callBackend()` |

**Day 3 验收**:
- `pytest -m contract` 至少 8 个真测试 pass
- scope creep 调用在 logs 出现 `[_stubs] WARNING:` 标记
- tests/auth-headers.test.ts 直接 `import buildBackendHeaders` 生产 helper

### Day 4 (Thu, 5h)

| 优先级 | Story ID | 标题 | 估时 | 文件 |
|---|---|---|---|---|
| P1-4 | PLUGIN-002 | exam-quick.ts 升级解析 4 维 AutoScoreResult | 3h | `plugin/src/exam-quick.ts::buildFeedbackAppend()` |
| P1-5 | PLUGIN-003 | 设置页加 X-CLS-Internal-Key 输入框 | 2h | `plugin/src/main.ts::SettingsTab` |

**Day 4 验收**:
- 答题保存后反馈段显示 4 维分数 + grade + confidence
- 设置页可输入 internal API key 并 X-CLS-Internal-Key 头真发送

### Day 5 (Fri, 1h + 用户 UAT)

- 跑 `python3 .scripts/smoke_test.py` 验证 import 闭合
- 跑 `pytest -m "unit or contract"` 验证 Sprint 1 + P5-P9 全 green
- 用户 hands-on: 批注 → Cmd+Shift+Q 出题 → 答题 → Cmd+S 评分 → 看 4 维反馈
- commit `feat(sprint1-v3): infra + plugin convergence`

---

## Sprint 2 — Week 2, 5 工作日, 26h

> 主线: **协议收敛 + E2E 测试 + 用户 UAT**

### Day 6 (Mon, 7h)

| Story ID | 标题 | 估时 | 文件 |
|---|---|---|---|
| INFRA-006 | infra/llm/executor.py 统一 LLM 入口 | 4h | 新建 `backend/app/infra/llm/executor.py` |
| EXAM-003 | generator.py + scorer.py 替换 → executor | 3h | `backend/app/domain/exam/{generator,scorer}.py` |

**Day 6 验收**: `grep -r "from litellm import" backend/app/domain/` 输出 0

### Day 7 (Tue, 6h)

| Story ID | 标题 | 估时 | 文件 |
|---|---|---|---|
| MASTERY-001 | SignalRegistry 接受 V1 + V0 通过 SignalAdapter | 3h | `backend/app/domain/mastery/signals.py::SignalRegistry` |
| MASTERY-002 | mastery_engine + fusion 用 V1 接口 | 3h | `backend/app/domain/mastery/{engine,fusion}.py` |

**Day 7 验收**: 融合结果含每信号 health_score + fallback_reason metadata

### Day 8 (Wed, 5h)

| Story ID | 标题 | 估时 | 文件 |
|---|---|---|---|
| TEST-002 | 解除 1 个 E2E 黄金路径 skip | 4h | `backend/tests/e2e/test_golden_path.py::test_full_exam_workflow` |
| INFRA-007 | XML 打包脚本补全 (含 main.py / interfaces/api/* / event_bus.py / tests/*) | 1h | `.scripts/pack_review.py` |

**Day 8 验收**: E2E 至少 1 条真实 pass (批注→出题→评分→mastery 更新)

### Day 9 (Thu, 3h)

| Story ID | 标题 | 估时 | 文件 |
|---|---|---|---|
| DOC-001 | sprint-status.yaml 更新 + 6 Lite Story spec | 3h | `_bmad-output/implementation-artifacts/sprint-status.yaml` + 新建 6 Lite spec |

### Day 10 (Fri, 4h)

| Story ID | 标题 | 估时 |
|---|---|---|
| VERIFY-001 | 用户 hands-on UAT 完整黄金路径 + NPS 评分 | 4h |

**Sprint 2 验收**: 用户 NPS ≥ 8 + 一句话感受

---

## 不做清单 v3 (9 个，4 方共识砍掉)

| # | Story ID | 砍掉理由 |
|---|---|---|
| 1 | Story 8.3 元认知 2x2 矩阵 | 统计视图产品，单人样本少 |
| 2 | Story 6.1/6.2/6.3 Edge 讨论 EI+SE | LMS 痕迹，单人无双策略价值 |
| 3 | Story 5.8 Hot/Warm/Cold 异步归档 | 单人数据量 <10MB，过早优化 |
| 4 | Story 9.1 多模态考察 | scope 扩展，不在主线 |
| 5 | Story 8.7 操作审计日志 | 平台运维，单人 debug 即可 |
| 6 | candidate_service (旧仓库) | 多用户嫌疑 + 附件无实现 |
| 7 | batch_orchestrator (旧仓库) | 只 health 探针用 |
| 8 | cross_subject_bridge (旧仓库) | 附件无实现，价值不明 |
| 9 | Agent Graph 全部 (agent_service / verification_service / topic_clustering / conversation_*) | 已明确不迁 |

总砍 ~40-50h 工作量。

---

## Lite 重编清单 (6 个，Sprint 3+ 做)

需在 BMAD 新建 spec 替代原 Story:

| 新 Story ID | 替代原 Story | 简化范围 | 估时 |
|---|---|---|---|
| STORY-LITE-4.3 | 4.3 三路融合 | 只允许"当前节点 + frontmatter + 最近 3 tips"，禁 Graphiti/Graphify | 3h (vs 原 6h) |
| STORY-LITE-5.6 | 5.6 + 4.9 merge | 只保留 accurate/too_high/too_low/skip 投票 + 本地回写 | 2h (vs 原 5h) |
| STORY-LITE-5.7 | 5.7 三层记忆 | 只读最近上下文，禁 Layer 1/2/3 调度 | 2h (vs 原 5h) |
| STORY-LITE-4.11 | 4.11 IRT | 保留 callout 快速入口，砍 IRT 连续校准 | 1h (vs 原 4h) |
| STORY-LITE-5.4 | 5.4 pipeline_token | grade_answer() 内顺序调用，去 token 防篡改 | 1h (vs 原 3h) |
| STORY-LITE-5.5 | 5.5 错误分类 dual-write | single-write 模型 | 1h (vs 原 2h) |

Lite 重编总估时 10h (vs 原 25h，节省 60%)

---

## 5 个用户待确认决策 (锁定后立刻进 Day 1)

| # | 决策 | 选项 A | 选项 B | 我推荐 |
|---|---|---|---|---|
| 1 | **Sprint Day 1 第 1 个 Story** | INFRA-001 (我 v1) | INFRA-002 (ChatGPT v2 + 3 agent) | **B** (先挂路由) |
| 2 | **Story 5.6 处理** | 完全砍 (我 v1) | 保留 lite 版 (ChatGPT v2) | **B** (单人 calibration 有价值) |
| 3 | **_stubs.py 处理** | silent 优雅降级 | fail-loud warning | **B** (silent 吞 bug) |
| 4 | **Story 4.3 处理** | 完整三路融合 | 简化为 4.3-lite | **B** (scope creep) |
| 5 | **canvas-vault 归属** | 同仓库 | git submodule | **B** (数据隔离) |

---

## 关键里程碑

| Week | Day | Owner | 完成目标 |
|---|---|---|---|
| W1 | Mon (D1) | Claude | ✅ app_factory 装配 + 路由可访问 + EventBus 修复 |
| | Tue (D2) | Claude | ✅ /grade + /quick endpoint 接通, 4 维返回 |
| | Wed (D3) | Claude | ✅ contract test 8+ pass, plugin client 抽取 |
| | Thu (D4) | Claude | ✅ 插件反馈 4 维显示 + auth 头发送 |
| | Fri (D5) | **User** | ✅ hands-on 黄金路径跑通 |
| W2 | Mon (D6) | Claude | ✅ LLM executor 统一 |
| | Tue (D7) | Claude | ✅ Mastery V1 fusion 接通 |
| | Wed (D8) | Claude | ✅ E2E 黄金路径 pass |
| | Thu (D9) | Claude | ✅ Lite Story spec + sprint-status 更新 |
| | Fri (D10) | **User** | ✅ NPS ≥ 8 |

---

## v1 vs v3 关键改判对照

| 维度 | v1 (我 2026-05-21 早) | v3 (ChatGPT v2 + 3 agent 验证) |
|---|---|---|
| Sprint Day 1 第 1 | INFRA-001 (EventBus) | **INFRA-002 (app_factory)** |
| TEST-001 时机 | Day 4 | **Day 3 (提前)** |
| _stubs.py | 优雅降级 | **fail-loud** |
| Story 5.6 | 砍 | **保留 lite** |
| Story 4.3 | 未标 | **简化为 lite** |
| 总估时 | 49h | **52h (更精准)** |
| 砍掉 Story | 6 个 | **9 个 + 6 Lite** |
| 复用估时 | 39h | **27-29h (P0+P1)** |

---

## 高风险点 + 缓解

| 风险 | 缓解 |
|---|---|
| INFRA-002 装路由后 import 链断 | Day 1 立刻跑 smoke_test.py |
| EXAM-001/002 设计跟 PLUGIN-002 解析不匹配 | Day 3 TEST-001 提前锁 schema |
| Day 5 用户 UAT 发现新 bug | 预留 Sprint 3 buffer week |
| LLM executor 性能延迟 >30s | Day 6 加 performance baseline test |
| canvas-vault submodule 学习成本 | 用户决策 5 选项前可先用同仓库 |

---

## 下一步 (4 方收敛后等用户拍板)

立刻可做:
1. **用户确认 5 个决策**（上方表格）
2. 决策完后 Claude 立刻进 **Day 1 INFRA-002**
3. Day 5 + Day 10 用户 hands-on UAT

**最快路径**: 用户简单回 "按推荐 5 个 B" → Claude 立刻开干 INFRA-002 (4h)。
