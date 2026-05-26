---
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
title: "ChatGPT Deep Research vs 4 Agent 仓库治理判定 整合"
date: "2026-05-20"
parent_research:
  - "_bmad-output/research/2026-05-20-repo-restructuring-decision-audit.md (4 agent 产出)"
  - "用户粘贴的 ChatGPT Deep Research 报告 (无独立文件，存此文档)"
status: "ready-for-user-decision"
---

# ChatGPT Deep Research vs 4 Agent 判定整合

## Context

用户按 R4 工作流（Claude deep explore → ChatGPT 第二意见）流程，把 4 agent 产出的 `2026-05-20-repo-restructuring-decision-audit.md` 第 5 章 prompt 发给 ChatGPT Deep Research，拿回完整报告。本文档对比两方判定，识别一致点 / 分歧 / scope creep，给出最终决策路径。

## 关键发现：scope 误读

ChatGPT 报告 Context 段明确写：
> *"如果把目标用户假定为'教师 + 学生混合场景'，预算与时间均未设上限"*

这是 ChatGPT 自己做的假设，**用户从未表达过这个 scope**。用户的实际 scope：
- 单人 PM 给自己用的 Obsidian Hybrid 学习工具
- MVP 刚需 14 项不含 LMS / 协作 / 教师面板
- 最近痛点：评分基准不透明 + 代码良莠不齐 + Claude 不复用代码

所以 ChatGPT 报告的 ~20% 内容（LMS / 协作 / 课程治理）是 scope creep，不应纳入决策。

## 两方判定核心对比表

| 维度 | 4 Agent | ChatGPT | 推荐采纳哪方 |
|---|---|---|---|
| 推荐方案 | Option β Fresh Start | 模块化重构 | 两方一致（保留内核 + 重做壳层），4 agent 表述更直接 |
| 工作量 | 7-8h | 6+ 个月 | 4 agent（ChatGPT 估时含 LMS scope） |
| 目标范围 | Obsidian Hybrid 降级版 | 完整学习平台 + LMS | 4 agent（符合用户真实 scope） |
| 数据库 | Neo4j 保留 | Postgres 主库 + Neo4j 副本 | 4 agent（单人不需要事务主库） |
| 数据迁移 | 12 步路径 | 6 阶段（冻结-提取-映射-回放-双写-切换） | **ChatGPT**（更稳健） |
| 领域边界 | services/README 规范 | 按 domain/canvas/exam/mastery/integration 重组 | **ChatGPT**（更系统） |
| 插件契约 | constants.py 集中 | MasterySignal 升级 V1 接口 + SkillRegistry 升级 capability registry | **ChatGPT**（更精确） |
| 稳定 ID | 不涉及 | ConceptRef / CanvasRef / AssessmentRef 类型封装 | **ChatGPT**（必加） |
| 测试 | 增强 CI/CD | 测试金字塔（单元/契约/E2E/性能/安全/无障碍） | **ChatGPT**（更深） |
| autoscore vs exam_grade | 识别 ✅ | 识别 ✅ | 一致 |
| 6 CLAUDE.md 散乱 | 识别 ✅ | 识别 ✅ | 一致 |
| LLM import 分散 | 识别 ✅ | 识别 ✅ | 一致 |
| 绿地重写 | 推荐 | 反对（"仅在无法冻结旧仓库时考虑"） | 4 agent（一次性 cherry-pick 不丢领域语义） |
| LTI/xAPI | 不涉及 | 推荐接入 | ❌ scope creep |
| CRDT 协作 | 不涉及 | 推荐 | ❌ scope creep |
| 教师面板 | 不涉及 | 推荐 | ❌ scope creep |
| Postgres 主库 | 保留 Neo4j | 引入 Postgres | ❌ scope creep |
| Redis/Kafka | 不涉及 | 推荐引入 | ❌ scope creep |
| K8s 部署 | docker-compose | 提供 K8s 模板 | ❌ scope creep |
| WCAG/无障碍 | 不涉及 | 推荐 WCAG 2.2 AA | ❌ scope creep |
| GDPR/网信办合规 | 不涉及 | 详细分析 | ❌ scope creep |

## ChatGPT 报告中"加强 4 agent"的 5 个核心点

这些是 ChatGPT **比 4 agent 更深的部分**，应该纳入最终方案：

### 1. 按领域而非 story 组织 backend

```
app/domain/canvas/
app/domain/exam/
app/domain/mastery/
app/domain/analytics/
app/domain/integration/
app/infra/db/
app/infra/graph/
app/infra/llm/
app/infra/queue/
app/interfaces/api/
app/interfaces/mcp/
```

比 4 agent 的 "backend/app/services/README.md" 更系统。

### 2. 稳定 ID 契约

```python
class ConceptRef(BaseModel):
    id: str
    source: Literal["canvas", "kg", "exam"]

class CanvasRef(BaseModel):
    board_id: str
    node_id: Optional[str] = None

class AssessmentRef(BaseModel):
    session_id: str
    item_id: Optional[str] = None
```

避免画布节点 ID、概念 ID、考试节点 ID 隐式映射的混乱。

### 3. MasterySignal V1 接口

```python
class MasterySignalV1(Protocol):
    version: str
    signal_name: str
    def get_value(self, node_id: str) -> Optional[float]: ...
    def get_weight(self, node_id: str) -> float: ...
    def get_reliability(self, node_id: str) -> float: ...
    def describe(self) -> dict: ...
```

比 4 agent 的 constants.py 集中更精确。

### 4. 6 阶段数据迁移（替代 12 步）

| 阶段 | 动作 |
|---|---|
| 冻结期 | 暂停新增大功能，冻结旧 schema |
| 提取期 | 从 `.canvas` / Dexie / Neo4j 抽取原始快照 |
| 映射期 | 建 `legacy_id → canonical_id` 映射表 |
| 回放期 | 把 sync_outbox / 评分历史 / 掌握度变化重放为事件 |
| 双写期 | 新系统写主库，同时投影 Neo4j |
| 切换期 | 前端只读旧层，写入新层 |

比 4 agent 的 12 步更稳健（4 agent 是"一次性 cherry-pick"，ChatGPT 是"分阶段迁移"）。

### 5. 测试金字塔

| 层 | 内容 |
|---|---|
| 单元 | 掌握度、评分、信号融合、推荐器、prompt 防护 |
| 契约 | REST OpenAPI、MCP tool schema |
| E2E | 创作 → 对话 → 检验 → 评分 → 复习黄金路径 |
| 性能 | 1k/5k/10k 节点画布、并发评分 |
| 安全 | prompt injection、越权、留存策略 |

比 4 agent 仅提"CI/CD"更深。

## 最终推荐：Option β-modified

```
4 Agent Option β (Fresh Start)
        ⊕
ChatGPT 加强的 5 点
        ⊖
ChatGPT scope creep 部分
        =
最终方案 Option β-modified
```

### 范围（明确）

#### ✅ 做
- 开新 GitHub 仓库（Option β 维持）
- 按 domain/* + infra/* + interfaces/* 重组 backend（ChatGPT 加强）
- 加 ConceptRef / CanvasRef / AssessmentRef 稳定 ID（ChatGPT 加强）
- MasterySignal V1 + SkillRegistry capability registry（ChatGPT 加强）
- 6 阶段数据迁移（ChatGPT 替代 4 agent 12 步）
- 测试金字塔 5 层（ChatGPT 加强）
- 单一 CLAUDE.md + service README + constants.py（4 agent 推荐）
- 接通 autoscore.py（4 agent + ChatGPT 一致）
- canvas-vault 用 git submodule 独立管理（4 agent 推荐）

#### ❌ 不做（scope creep）
- LTI 1.3 / xAPI 接入
- CRDT 协作 / Presence
- 教师 Dashboard / 课程级分析
- Postgres 主库（保留 Neo4j 为核心）
- Redis / Kafka / RabbitMQ
- K8s 部署模板
- WCAG 2.2 AA 无障碍验收
- GDPR / 网信办合规
- 多用户 / 多租户 / 权限模型

### 工作量预估

| Phase | 内容 | 工作量 |
|---|---|---|
| P1 | 新 GitHub repo + 单一 CLAUDE.md + README | 1h |
| P2 | backend 按 domain/* 重组（含 6 阶段迁移）| 4-6h |
| P3 | plugin cherry-pick + 简化 | 1-2h |
| P4 | Skills cherry-pick + capability registry | 1h |
| P5 | ConceptRef / CanvasRef / AssessmentRef 类型封装 | 1-2h |
| P6 | MasterySignal V1 升级 | 1h |
| P7 | 接通 autoscore.py | 1h |
| P8 | 测试金字塔 5 层基线 | 2-3h |
| P9 | 验证 smoke test | 1h |
| **总计** | | **13-18h** |

比 4 agent 的 7-8h 多 6-10h（加了 ChatGPT 5 点）。
比 ChatGPT 的 6 个月少 99%（去掉 scope creep）。

## 决策点（用户最终确认）

请你确认或修改:

1. **是否同意 Option β-modified**？（开新仓库 + 整合 ChatGPT 5 点 + 去 scope creep）
2. **是否同意不做 LMS/协作/Postgres/K8s 等 scope creep**？
3. **canvas-vault 用 git submodule 还是同仓库**？
4. **新仓库名字**？候选：
   - `canvas-obsidian-hybrid`（ChatGPT/4 agent 都用这个）
   - `canvas-learning-os`（更产品化）
   - `cls-hybrid`（缩写更短）
   - 你的其他建议

## 风险点

1. **ChatGPT 报告是基于"假设的 LMS scope"，4 agent 报告是基于"真实的单人工具 scope"**——如果未来你的 scope 升级为 LMS，需要重新做架构决策。
2. **6 阶段迁移比 12 步迁移慢**——但更稳健。如果时间紧，可走 4 agent 的 12 步路径。
3. **MasterySignal V1 升级跟现有代码兼容性**——需要先确认现有 signals 数量 + 改造工作量再定。

## 下一步

按用户决策，进入执行阶段：
- 选 Option β-modified → 我立即执行 P1-P9
- 选 4 agent 原版 Option β → 我执行原 12 步
- 选 ChatGPT 全套 → 你需要重新明确 LMS scope，6 个月计划
- 选 D（不动）→ 把这两份报告归档，先跑 MVP-α UAT
