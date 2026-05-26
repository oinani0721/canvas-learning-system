# ChatGPT 功能-代码差距对抗审查 Prompt v2

> **使用方法**:
> 1. ChatGPT (推荐 GPT-5 Pro / Claude 4 Opus / 含 Deep Research)
> 2. 拖入附件: `_bmad-output/research/2026-05-21-gap-audit-chatgpt-review.xml` (917.8 KB / ~235K tokens / 64 文件)
> 3. 复制下面 prompt 全文粘贴
> 4. (可选) 让 ChatGPT 访问 https://github.com/oinani0721/canvas-obsidian-hybrid
> 5. 等 10-15 分钟拿完整三类清单审查报告

---

## Prompt 正文（复制以下全部）

```
# Tech Decision: Canvas Obsidian Hybrid 功能-代码差距全审查

## Context

我是单人 PM 在维护 Obsidian + FastAPI + Neo4j 学习工具.

**关键事实** (3 个 Claude agent + 之前一次 ChatGPT 已识别):

1. **设计层**: PRD 含 12 设计 (d=0.40-1.50) + 11 AR + 103 FR + 9 Epic + 90 Story
2. **代码层 (新仓库 canvas-obsidian-hybrid)**: 117 .py + 13 .ts + 6 Skills
3. **运行状态**: 设计 90% 完整, 实现 40% 通路断接 — 典型 P6-P7 中间态

**3 agent 已识别的 6 个 P0 bug**:
- main.py 是 P2 stub (Dockerfile 启动它但没挂任何 route)
- grading.py EventBus 签名错配 (运行时 TypeError)
- 缺 /api/v1/exam/grade endpoint
- 缺 /api/v1/exam/quick endpoint
- handlers.py 缺 SCORE_SUBMITTED 订阅
- pyproject.toml 空依赖

**当前用户实际可用功能**: 5/8 (批注/AI双链/节点对话/Dashboard/白板配置 可用; Quick Exam/复习队列 半能; 评分自动 不能)

GitHub: https://github.com/oinani0721/canvas-obsidian-hybrid (private)

## Scope 锁定

**单人自用 Obsidian Hybrid**. 不做 LMS/协作/教师面板/Postgres/K8s/WCAG/GDPR/LTI/xAPI.

## 附件说明 (917.8 KB / ~235K tokens / 64 文件)

XML 含 4 类:

1. **new-repo/** — 新仓库关键代码 (P0 bug 暴露文件 + 设计文件)
   - main.py vs main.py.original (双入口分裂)
   - _stubs.py (scope creep 优雅降级 11 个)
   - domain/exam/{grading.py, scorer.py, generator.py 51K} (P7 修复 + 完整/简化版并存)
   - domain/mastery/{v1.py 无调用, signals.py V0, fusion.py DEAD, engine.py}
   - domain/refs.py (P5 稳定 ID)
   - infra/queue/{event_bus.py, handlers.py} (event 链断点)
   - interfaces/api/{exam.py, health.py} (缺关键 endpoint)
   - plugin/src/{main.ts 87K, exam-quick.ts, status-bar.ts}

2. **new-repo/skills/** — 6 Claudian Skill + capability-registry

3. **old-repo/** — BMAD 设计 (prd.md 41K + epics.md 42K + architecture.md 68K + sprint-status.yaml + epic-4/5/6 全 Story spec)

4. **prd-anchor/** — PRD v5 §1.4 + §1.5 + §1.10 + §10 关键章节

5. **prior-research/** — 之前 5 份研究产物 (4 agent + ChatGPT v1 + Sprint Backlog + reconciliation)

## 我已经梳理出的"重编/废弃/复用"3 类初稿

请你**对抗审查**这 3 类清单 — 我的判断对不对? 有遗漏?

### 类别 1: Story 需要重编 (我标 6 个)

| Story | 我的判断 | 我的依据 |
|---|---|---|
| 5.4 pipeline_token 5 步串联 | **简化** (单人无并发) | scope 单人自用 |
| 5.6 + 8.3 学生自评 2x2 | **砍** (自评 1 维 DEAD + 0 UI) | prior-research 已确认 |
| 6.1/6.2/6.3 Edge 双策略 | **砍** (LMS 痕迹) | scope creep |
| 4.11 IRT 难度 callout | **简化** (单人无人群分布) | 用 FSRS 替代 |
| 5.8 Hot/Warm/Cold 归档 | **延后** (单人数据量小) | β-2 再说 |
| 5.5 错误分类 dual-write | **简化** (单 write 即可) | 单人无审计 |

### 类别 2: 代码废弃 应砍 (我标 19 个)

🔴 立即砍 8 个:
- 旧仓库监控类: alert_manager / metrics_collector / resource_monitor / health_monitor
- 新仓库: main.py.original / rag.py endpoint / vault_switch.py / fusion.py

🟡 stub 中保留 11 个 (scope creep 优雅降级):
- Agent Graph 4: agent_service / agent_selector / agent_routing_engine / react_agent
- Verification / topic_clustering / notification_channels
- conversation 4: archive / distiller / inheritance / archive_scheduler

### 类别 3: 代码可复用衔接 (我标 54 个)

🔴 P0 紧急接通 3 项:
- grading.py 缺 endpoint + EventBus 签名 + handler 订阅
- generator.py 缺 /exam/quick endpoint
- main.py stub → 重写

🟠 P1 衔接 38 个 (新仓库 PARTIAL 状态)

🟡 P2 旧仓库候选 16 个 (39h 工作量, 按 P0/P1/P2 排):
- HIGH 9h: candidate_service + batch_orchestrator + cross_subject_bridge
- MEDIUM 18h: intelligent_grouping + multimodal + error_rebuild + skill_registry + background_task + extraction_validator + websocket
- LOW 12h: rollback + intelligent_parallel + relationship_sync + context_enrichment + markdown_image + group_id_migration

## 请你对抗审查 5 个问题 (具体输出格式硬约束)

### 1️⃣ 重编 Story 验证 — 我的 6 个对吗?

请你**逐个**审查我标的 6 个重编候选 + **找出我遗漏的**:

| Story | 我的标签 | 你的判定 | 理由 (引用 XML 文件:行) | 你建议 |
|---|---|---|---|---|

要求:
- 至少新加 3-5 个我没标但应该重编的 Story (e.g., 4-3 三路融合可能 scope creep)
- 至少标 1 个我说"砍"但你觉得应该保留的 (附理由)
- 至少标 1 个我说"简化"但你觉得应该完整保留的

### 2️⃣ 废弃代码 deep dive — 19 个砍候选哪些遗漏?

请你**走查新仓库 117 .py + 13 .ts**, 找出我没标但确实是 DEAD CODE 的:

| 文件路径 | DEAD CODE 证据 (引用 grep / 调用链) | 立即砍 vs stub 保留 vs evaluate |
|---|---|---|

要求:
- 至少 5-8 个新发现
- 特别关注: domain/exam/generator.py 51K (是否有 dead branch)
- 特别关注: _stubs.py 是否吞了真应该报错的调用

### 3️⃣ 复用候选评估 — 16 个旧仓库候选哪些真值得迁?

请你审查我标的 16 个复用候选, 按"单人自用 scope"重新评估:

| 旧候选 | 我估时 | 你的判定: 应迁 / 砍 / 简化迁 | 真实价值 (1-5) |
|---|---|---|---|

要求:
- 砍掉 scope creep (e.g., candidate_service 多用户)
- 标 ✅ 真单人有用 vs ❌ scope creep 嫌疑
- 给一个**重新估时的 P0/P1 接通清单**

### 4️⃣ Story 推进序 — 90 Story 怎么排?

我已经在 prior-research 里有 Sprint 1+2 Backlog (10+8 = 18 Story). 请你**对抗审查**这个 Backlog:

- Sprint 1 (5 day, 24h, 10 Story) 顺序对吗?
- Sprint 2 (5 day, 25h, 8 Story) 顺序对吗?
- Sprint 3+ 该排什么?

要求:
- 至少调整 2-3 个 Story 顺序 + 给理由
- 告诉我 Sprint 1 Day 1 第一个 Story 是不是真的应该是 INFRA-001 (EventBus bug)
- 标出 Sprint 后**还剩多少个 Story 必须做 vs 永远不做 (scope creep)**

### 5️⃣ scope 锁定真假 — 还有什么 LMS 残留?

我声明 scope = 单人自用. 请你**对抗审查**找出**我假装在 scope 内但实际是 LMS 痕迹**的:

| 代码 / Story | LMS 嫌疑证据 | 我的归类 | 你建议 |
|---|---|---|---|

要求:
- 至少 5-8 个新发现
- 特别关注: candidate_service / verification_service / agent_service / multimodal / websocket
- 验证 _stubs.py 是否真覆盖所有 scope creep

## 输出格式硬约束

❌ 不要给:
- "建议考虑..." 这种空话
- 没文件:行号引用的判定
- 学术理论对比 (前两轮已做过)

✅ 必须给:
- 每个判定附 XML <file path="..."> + 行号引用
- 表格 + bullet points 结合
- 中文回答
- 末尾给一份**总判定**: 最终该重编多少 / 砍多少 / 复用多少 / Sprint 调整后 90 Story 还剩多少要做

时间预算: 你花 15-20 分钟给完整 5 个问题答复. token 不够先答问题 1+2+5 (重编 + 废弃 + LMS 残留).
```

---

## 拿到回复后给我

我会:
1. 整合 ChatGPT 这次判定 + 3 agent + 上轮 ChatGPT 报告 (4 方对照)
2. 把"3 类清单"v2 锁定 (重编 / 废弃 / 复用)
3. 调整 Sprint 1+2 Backlog
4. 立刻执行 Sprint 1 Day 1 第一个 Story
