---
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
sprint: "Sprint 1 + Sprint 2 (Week 1+2 of canvas-obsidian-hybrid post-P9)"
date: "2026-05-21"
basis:
  - "ChatGPT Deep Research 对抗审查报告 (含 6 真 bug 命中)"
  - "4 Agent Fresh Start 决策 (2026-05-20)"
  - "PRD §1.4 AutoSCORE + §1.5 5 信号融合 + §10 实施路线"
total_estimate: "49h (Sprint 1 24h + Sprint 2 25h)"
status: "ready-to-execute"
---

# Sprint 1+2 Backlog — canvas-obsidian-hybrid 接通工作

## Context

ChatGPT 对抗审查报告（2026-05-21）暴露 6 个真实运行时 bug + 8 个结构性漂移问题，需立刻接通新仓库 P1-P9 的 stub 化代码到可运行状态。

**核心原则**: 先消灭结构性漂移（入口/契约/协议），再优化学习科学能力本身。

**ChatGPT 报告关键发现**:
1. `main.py` 只挂 `/healthz`, endpoints/* 没装路由 → 主流程全 404
2. `grading.py` EventBus 签名错配 → 评分成功后立即 TypeError
3. docker-compose healthcheck 路径错配 → 容器一直 unhealthy
4. `X-CLS-Internal-Key` 认证头缺失 → 生产模式 403
5. Quick Exam 4 维契约漂移 → 插件丢失维度信息
6. `pyproject.toml` 空依赖 → 新环境不可重现

---

## Sprint 1 — Week 1, 5 工作日, 24h

> 主线: **入口收敛 + 客户端收敛 + 关键 bug 修复**

### Day 1 (Mon, ~6h)

| Story ID | 标题 | 估时 | 改的文件 |
|---|---|---|---|
| **INFRA-001** | 修复 grading.py EventBus 签名错配 | 1h | `backend/app/domain/exam/grading.py:_publish_score_submitted()` |
| **INFRA-004** | pyproject.toml 加真实 deps | 1h | `backend/pyproject.toml` |
| **INFRA-002** | app_factory.py + APIRouter 装配 | 4h | 新建 `backend/app/app_factory.py`, 改 `backend/app/main.py` |

**Day 1 验收**: `uvicorn app.main:app` 启动 + `/api/v1/exam/grade` `/api/v1/vault/current` 可访问 + 评分不再 TypeError

### Day 2 (Tue, ~6h)

| Story ID | 标题 | 估时 | 改的文件 |
|---|---|---|---|
| **INFRA-003** | docker-compose healthcheck 修复 | 1h | `backend/docker-compose.yml`, `backend/app/interfaces/api/health.py` |
| **EXAM-001** | POST /api/v1/exam/grade 接 grading.py | 3h | `backend/app/interfaces/api/exam.py` (新增 endpoint), `backend/app/app_factory.py` (注册路由) |
| **EXAM-002** | POST /api/v1/exam/quick 接 generator.py | 3h (重叠 EXAM-001) | 同上 |

**Day 2 验收**: `curl POST /api/v1/exam/grade` 返回 4 维 AutoScoreResult + `curl POST /api/v1/exam/quick` 返回 tip 引用题目 + `docker compose ps` 显示 healthy

### Day 3 (Wed, ~6h)

| Story ID | 标题 | 估时 | 改的文件 |
|---|---|---|---|
| **PLUGIN-001** | 抽取 plugin/src/backend-client.ts | 3h | 新建 `plugin/src/backend-client.ts`, 改 `plugin/src/main.ts::callBackend()` 用新 client |
| **PLUGIN-002** | exam-quick.ts 升级解析 4 维 AutoScoreResult | 3h | `plugin/src/exam-quick.ts::buildFeedbackAppend()` + `onFileModified()` |

**Day 3 验收**: 插件设置页输 `X-CLS-Internal-Key` 后真发送 + Cmd+Shift+Q 触发后反馈段显示 4 维分数

### Day 4 (Thu, ~5h)

| Story ID | 标题 | 估时 | 改的文件 |
|---|---|---|---|
| **TEST-001** | 解除 contract test skip | 4h | `backend/tests/contract/test_openapi_schema.py`, 新建 `test_exam_endpoints.py` |
| **INFRA-005** | _stubs.py 暴露 warning | 1h | `backend/app/_stubs.py` |

**Day 4 验收**: `pytest -m contract` 至少 8 个真测试 pass + scope creep 调用在 logs 可见

### Day 5 (Fri, ~1h buffer + Sprint 1 验收)

- 跑 smoke test (existing `.scripts/smoke_test.py`) 验证 import 闭合
- 跑 `pytest -m "unit or contract"` 验证 P1-P9 + Sprint 1 全 green
- commit `feat(sprint1): infra + plugin convergence (P0-P1 bugs fixed)`

---

## Sprint 2 — Week 2, 5 工作日, 25h

> 主线: **协议收敛 + 测试治理 + 用户验收**

### Day 6 (Mon, ~7h)

| Story ID | 标题 | 估时 | 改的文件 |
|---|---|---|---|
| **INFRA-006** | infra/llm/executor.py 统一 LLM 入口 | 4h | 新建 `backend/app/infra/llm/executor.py` |
| **EXAM-003** | generator.py + scorer.py 替换 → executor | 3h | `backend/app/domain/exam/{generator,scorer}.py` |

**Day 6 验收**: `grep -r "from litellm import" backend/app/domain/` 输出 0 + 评分 + 出题仍 work

### Day 7 (Tue, ~6h)

| Story ID | 标题 | 估时 | 改的文件 |
|---|---|---|---|
| **MASTERY-001** | SignalRegistry 接受 V1 + V0 通过 SignalAdapter | 3h | `backend/app/domain/mastery/signals.py::SignalRegistry` |
| **MASTERY-002** | mastery_engine + fusion 用 V1 接口 | 3h | `backend/app/domain/mastery/{engine,fusion}.py` |

**Day 7 验收**: 融合结果含每信号 health metadata + fallback_reason 在 logs 可追踪

### Day 8 (Wed, ~5h)

| Story ID | 标题 | 估时 | 改的文件 |
|---|---|---|---|
| **TEST-002** | 解除 1 个 E2E 黄金路径 skip | 4h | `backend/tests/e2e/test_golden_path.py` |
| **INFRA-007** | XML 打包脚本补全 + scope 标记 | 1h | `.scripts/pack_review.py` |

**Day 8 验收**: E2E 至少 1 条真实 pass (批注→出题→评分→反馈) + 下次 XML 含 runtime-critical 文件

### Day 9 (Thu, ~3h)

| Story ID | 标题 | 估时 | 改的文件 |
|---|---|---|---|
| **DOC-001** | PRD/EPIC 改动清单按 ChatGPT 7 行变更 | 3h | `_bmad-output/planning-artifacts/{epics.md,prd.md}`, `_bmad-output/implementation-artifacts/sprint-status.yaml` |

**Day 9 验收**: sprint-status 反映 Sprint 1+2 的 Story + 砍掉 6 个 scope creep Story

### Day 10 (Fri, ~4h Sprint 2 用户验收)

| Story ID | 标题 | 估时 |
|---|---|---|
| **VERIFY-001** | 用户验收 Sprint 1+2 + 跑 6 步 UAT (含 4 维评分体验) | 4h |

**Day 10 验收**: 用户填主观打分 + NPS 8+ + 一句话感受

---

## 不做清单 (scope creep — ChatGPT 也确认)

| # | Story ID | 砍掉理由 |
|---|---|---|
| 1 | Story 5.4 pipeline_token 5 步串联 | 单人无并发，过度工程 |
| 2 | Story 5.6 校准投票 + Story 8.3 2x2 矩阵 | 学生自评 1 维 DEAD CODE, 单人元认知价值低 |
| 3 | Story 6.1/6.2/6.3 Edge 讨论 | LMS 痕迹, 单人不需要双策略讨论 |
| 4 | Story 4.11 IRT 难度 callout | 单人无人群分布, IRT 无数据基础 |
| 5 | Story 5.8 Hot/Warm/Cold 归档 | 单人数据量小, 过早优化 |
| 6 | Story 5.5 错误分类 dual-write | 单人无审计需求 |

总砍 6 个 Story = ~40-50h 节省。

---

## 跨 Sprint 风险点

| 风险 | 严重度 | 缓解 |
|---|---|---|
| INFRA-002 app_factory 接路由后某 endpoint import 链断 | 🟠 中 | 用 Sprint 1 Day 1-2 跑 smoke_test.py 提前暴露 |
| EXAM-001 grade endpoint 调 grading.py 返回 4 维, 但 PLUGIN-002 还没升级 → 临时 plugin 报错 | 🟡 低 | Sprint 1 Day 2-3 顺序: backend ready 后立刻接 plugin |
| LLM executor 性能开销大 (retry / log) → 评分延迟超 30s | 🟡 低 | Sprint 2 Day 6 加性能基线 (performance test) |
| 用户 Sprint 2 Day 10 UAT 发现新问题 → Sprint 3 必须 | 🟡 中 | 预留 Sprint 3 buffer week |

---

## Sprint 3 buffer (如需要)

如 Day 10 UAT 失败，进 Sprint 3 修复:
- 用户报的具体 bug
- ChatGPT 提到的 LLM executor 高级 feature (cache / model 路由)
- β-1 Graphiti 接入计划开始

---

## 立刻开始 Story-INFRA-001 (Sprint 1 Day 1 第 1 个)

### Story-INFRA-001: 修复 grading.py EventBus 签名错配

**问题** (ChatGPT 命中):
- 旧代码: `await event_bus.publish("SCORE_SUBMITTED", payload)` (P7 commit 61caa95)
- 实际 EventBus.publish() 签名接受 `LearningEvent` 单对象
- 评分成功后立即抛 TypeError, mastery 链断

**修复**:
```python
# backend/app/domain/exam/grading.py:_publish_score_submitted()

# 旧 (ERROR):
await event_bus.publish("SCORE_SUBMITTED", payload)

# 新:
from app.infra.queue.events import LearningEvent  # 路径需 verify
event = LearningEvent(
    event_type="SCORE_SUBMITTED",
    payload=payload,
    timestamp=datetime.now(timezone.utc),
)
await event_bus.publish(event)
```

**验收**:
1. Reread `backend/app/infra/queue/event_bus.py` 确认 publish() 签名
2. 改 `backend/app/domain/exam/grading.py:96`
3. 跑 `pytest tests/unit/test_grading.py -v` 验证 6 testcase 仍 pass
4. 改 `test_grading.py` mock 用 LearningEvent 而非 (event_type, payload) tuple

**估时**: 1h (含 mock 改造)
