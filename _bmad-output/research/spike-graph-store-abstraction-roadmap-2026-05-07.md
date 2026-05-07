---
spike_id: "spike-graph-store-abstraction"
spike_type: "post-Epic-11 backlog candidate (NOT committed Epic)"
date: "2026-05-07"
parent_decision: "D19 (Desktop DB Stack)"
parent_research:
  - "_bmad-output/research/round-22-desktop-db-decision-deep-research-2026-05-07.md"
  - "_bmad-output/research/round-22-chatgpt-dr-prompt-desktop-db-decision-2026-05-07.md"
status: "proposal"
trigger_condition: "Epic-11 Day 22 完整发布后 + 用户主动需求降低 Docker 门槛"
estimate: "4-6 人日 (阶段二) + 5-8 人日 (阶段三) = 9-14 人日"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
---

# Spike Roadmap: 图访问抽象层 + Kuzu Embedded DB 可行性预研

> **本文档不是 Epic / Story spec**，是 D19 决策落地后的 **backlog spike candidate**。Epic-11 完成后才考虑启动。
>
> **目标**: 探索"未来某天，能否让 Canvas Learning System 桌面 app 不依赖 Docker Desktop"的技术可行性，**不承诺 ship**。

---

## 1. 触发条件（如下 4 条**任一**满足才启动）

1. **用户主动需求降低安装门槛**: Epic-11 发布后用户批注"Docker 太重了，能不能去掉？"
2. **Graphiti 上游做出 driver 抽象重构**: `graphiti-core` 1.0+ 提供完整 GraphStore 接口，迁移成本断崖式下降
3. **Kuzu 0.x → 1.0 GA**: Kuzu 标记 production-ready + 自定义索引/约束完整支持
4. **Docker Desktop 商业许可改变**: Docker Desktop 对个人/教育用户的免费政策收紧（2026 年持续监控）

**触发后流程**: 启动阶段二 → 通过则进入阶段三 → 任一阶段失败回退保守路径（保留 C+）

---

## 2. 阶段二：图访问抽象层小重构（4-6 人日，不换库）

### 2.1 目标

把"具体数据库实现"从业务代码里解耦出来，**不要求换数据库**，只建立接口边界 + 统一测试夹具 + 定义最小兼容契约。

### 2.2 范围（DR 推荐 3 块）

#### Block A: Episode 写入与检索接口

**当前耦合点**:
- `backend/app/services/episode_worker.py` 直接调 `Graphiti(neo4j_uri, neo4j_user, neo4j_password).add_episode(...)`
- `backend/app/services/memory_service.py` 直接调 `record_learning_event()` 等

**抽象目标**:
```python
# 新建 backend/app/storage/episode_store.py（接口）
class EpisodeStore(Protocol):
    async def add_episode(self, group_id: str, content: str, metadata: dict) -> str
    async def search_episodes(self, group_id: str, query: str, limit: int) -> list[Episode]
    async def get_episode(self, episode_id: str) -> Episode | None

# backend/app/storage/episode_store_neo4j.py（Neo4j 实现）
class Neo4jEpisodeStore(EpisodeStore):
    def __init__(self, neo4j_uri: str, ...):
        self._graphiti = Graphiti(neo4j_uri, ...)
    # ...

# 工厂选择
def get_episode_store() -> EpisodeStore:
    backend = os.getenv("EPISODE_STORE_BACKEND", "neo4j")
    if backend == "neo4j": return Neo4jEpisodeStore(...)
    if backend == "kuzu": return KuzuEpisodeStore(...)  # 阶段三新增
```

**工作量**: 1.5-2 人日

#### Block B: Exam Session 图持久化接口

**当前耦合点**:
- `backend/app/services/exam_service.py` 4 段 Cypher（Canvas 查询、session 持久化、按 ID 回读、按 canvas_name 回读）

**抽象目标**:
```python
# backend/app/storage/exam_store.py（接口）
class ExamSessionStore(Protocol):
    async def find_canvas(self, canvas_name: str, group_id: str) -> Canvas | None
    async def save_session(self, session: ExamSession, group_id: str) -> str
    async def get_session(self, session_id: str, group_id: str) -> ExamSession | None
    async def list_sessions_by_canvas(self, canvas_names: list[str], group_id: str) -> list[ExamSession]
```

**工作量**: 1-1.5 人日

#### Block C: Learning Relationship / Review Suggestions 接口

**当前耦合点**:
- `backend/app/clients/neo4j_client.py` MERGE 学习关系、带/不带 group_id 的 review 查询、学习历史查询构造器

**抽象目标**:
```python
# backend/app/storage/learning_store.py（接口）
class LearningStore(Protocol):
    async def merge_learning_relation(self, user_id: str, concept_id: str, group_id: str, ...) -> None
    async def get_review_due(self, group_id: str, due_before: datetime) -> list[ConceptReview]
    async def get_learning_history(self, user_id: str, group_id: str, limit: int) -> list[LearningEvent]
```

**工作量**: 1.5-2.5 人日（neo4j_client.py 后半段被 DR 截断，实际查询数量更多）

### 2.3 group_id 语义升格（横切）

**当前位置**: `backend/app/utils/cypher_helpers.py::cypher_with_group_filter()` — 把 `WHERE n.group_id = $group_id` 注入 Cypher 字符串。

**升格目标**: 升格为 **数据库无关的过滤契约**，让 KuzuStore / Neo4jStore 实现都满足同样的 group_id 隔离语义。

```python
# backend/app/storage/filters.py
@dataclass
class GroupIdFilter:
    group_id: str  # mandatory, no fallback (Story 2.5.Y D16)

# 各 Store 实现自己翻译 GroupIdFilter 到具体后端语法
```

**工作量**: 0.5 人日（横切重构）

### 2.4 测试夹具

每个 Store 接口建对偶测试 fixture:
- `tests/storage/test_episode_store_neo4j.py` — 当前 Neo4j 实现
- `tests/storage/test_episode_store_contract.py` — 接口契约测试（任何实现必须通过）

**工作量**: 0.5-1 人日

### 2.5 阶段二退出条件

阶段二完成 = **现有所有 5 大核心功能仍然 100% 通过 Story 10.x 验收单**，且代码层有 GraphStore / EpisodeStore / ExamSessionStore / LearningStore 4 个 Protocol 接口 + Neo4j 实现 + 接口契约测试。

**不通过 = 不进入阶段三**（说明耦合面比 DR 估算更深）。

---

## 3. 阶段三：Kuzu Spike（5-8 人日，POC 不承诺上线）

### 3.1 目标

回答 3 个具体问题，每个 **PASS / FAIL** 二元判定:

#### Q1: Graphiti 的 KuzuDriver 能否替代当前 Neo4j 初始化？

**测试**:
- pip install `graphiti-core[kuzu]`
- 写 `KuzuEpisodeStore` 实现，初始化 `Graphiti(KuzuDriver(db_path))`
- 跑现有 Story 10.7 ErrorCandidate 测试（episode 写入 + 检索）

**PASS 标准**:
- ✅ Graphiti 启动无错
- ✅ `add_episode` / `search_episodes` 语义与 Neo4j 一致
- ✅ group_id 隔离行为一致

**工作量**: 1.5-2 人日

#### Q2: Review / History / Exam 查询能否在 Kuzu 方言下维持语义一致？

**测试**:
- 写 `KuzuLearningStore` + `KuzuExamSessionStore` 实现
- 跑现有 5 大核心覆盖测试套（DR 数据：阶段三需验证 10+ 段查询）

**PASS 标准**:
- ✅ MERGE 学习关系语义一致（Kuzu 不支持手工自定义索引/约束需绕开）
- ✅ Review due 时间排序一致
- ✅ Exam session 4 段查询全通

**FAIL 风险**: Kuzu Cypher 方言 ~95% 兼容 Neo4j，剩 ~5% 差异（自定义索引/约束、APOC 函数名）可能阻断。但 DR 实读发现**没有 APOC.* 运行期调用**，降低了风险。

**工作量**: 2-3 人日（含语义差异 mapping）

#### Q3: 启动体积与首启速度是否明显优于 B4 内置 Neo4j JVM？

**测试**:
- PyInstaller bundle FastAPI + Kuzu + 依赖
- 测 .app 包体积 vs B4 替代品（含 JRE）
- 测首启冷启动时间（用户点击 → 后端 ready）

**PASS 标准**:
- ✅ 包体积 < 250MB（明显优于 B4 ~400MB）
- ✅ 首启冷启动 < 5s（明显优于 B4 ~8-10s）
- ✅ 内存占用 < 500MB

**工作量**: 1.5-3 人日（含跨平台测试 macOS arm64/x64）

### 3.2 阶段三退出条件

**3 项里 2 项 PASS** → 启动正式切换 Story（独立 Epic-12 候选）
**3 项里 ≤ 1 项 PASS** → 停止 no-Docker 正式化，保持 C+ 主路径

---

## 4. 完整正式切换（不在 spike 范围）

如果阶段二 + 阶段三全 PASS，**才**考虑启动正式切换 Epic（DR 估算 20-35 人日），核心动作:

- 把 5 大核心全部实现迁移到 Kuzu 实现
- 重写所有 5 大核心相关测试
- Electron 直接 spawn FastAPI subprocess（不用 Docker）
- 跨平台代码签名 + notarize（macOS / Windows / Linux）
- Web 模式保留 Docker Compose（双轨并存，参考 D18 NEG-3）
- Migration 工具：现有 Neo4j 数据 → Kuzu 数据（用户 Web 模式数据迁过来）

**这部分不在本 spike 提案范围**，待阶段二 + 阶段三验证完后单独立项。

---

## 5. 风险地图

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| Graphiti `KuzuDriver` 在我们 episode 模式下不工作 | 中 | 高 | Q1 直接验证，FAIL 即停 |
| Kuzu Cypher 方言差异超过 5% | 低 | 中 | DR 实读无 APOC.*，降低风险；Q2 mapping |
| PyInstaller bundle Kuzu native 库失败 | 低 | 中 | 上游已有 Python wheel；fallback 用 onedir 模式 |
| 阶段二抽象层引入 bug 破坏 5 大核心 | 中 | 高 | 接口契约测试 + 渐进式重构（一个 Block 一个 Block） |
| Spike 拖延阻塞 Epic-11 | 低 | 中 | **Spike 触发条件明确：Epic-11 完整发布后才启动**，不阻塞主线 |

---

## 6. 决策追溯

- **D19**: `_bmad-output/决策批注/D19-desktop-db-stack-2026-05-07.md`（主决策 C+ + 本 spike 立项）
- **DR 报告**: `_bmad-output/research/round-22-desktop-db-decision-deep-research-2026-05-07.md`（推荐路径源）
- **DR 提示词**: `_bmad-output/research/round-22-chatgpt-dr-prompt-desktop-db-decision-2026-05-07.md`（升级触发条件）

---

## 7. 触发本 Spike 的下一步动作

如未来满足触发条件之一，启动方式:

```bash
# 1. 创建 spike Story
mkdir -p _bmad-output/implementation-artifacts/spike-graph-store-abstraction/
# 2. 写 Story spec（参考本文档 §2 + §3 拆 Tasks）
# 3. 跑 BMAD bmad-bmm-create-story
# 4. 实施阶段二（4-6 人日）
# 5. 阶段二 PASS → 跑阶段三（5-8 人日）
# 6. 阶段三 ≥ 2 项 PASS → 立 Epic-12 提案
```

**当前状态**: ⏸️ **等待触发条件满足**。Epic-11 优先交付 C+ 路径。

---

*Spike 提案，非 commit。BMAD R4 工作流：用户决策大方向 → Claude 实施技术细节。*
