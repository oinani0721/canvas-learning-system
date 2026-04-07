# Fix RAG Transform Completeness + Episode Cache Per-Group Isolation

## Why

经过 **4 轮代码级对抗性核实**（含 ChatGPT Deep Research 报告 #9 + 本地 Explore Agent × 4），FR-KG-04 主线问题已被现有 change `fix-fr-kg-04-schema-drift-and-sync-hardening` 大部分覆盖。但仍有 **3 个 P0/P1 残余项**未被纳入任何已 active 的 change，本 change 专项处理这些"不完整修复"和"全局缓存隔离"问题。

### 残余项 1：commit f215830 的 RAG transform 是部分修复

`commit f215830` (2026-04-06) 修复了 verification_service 读取 CONNECTS_TO 的关系类型不匹配问题，并在 `_get_rag_context_for_concept()` (verification_service.py:1832-1858) 加入了 `reranked_results → learning_history/related_concepts/common_mistakes` 的转换逻辑。**但通过逐字段审查发现这个 transform 仅完成了 1.5/3**：

| 字段 | 数据源 | 修复质量 |
|------|--------|---------|
| `learning_history` | `reranked[:3].content` 拼接 | ✅ 真实提取 |
| `related_concepts` | `meta.concept` OR `meta.source` | ⚠️ `metadata.concept` 是 Graphiti temporal 才有的非标准字段，回退到 `metadata.source` 时会返回文件路径（如 `/vault/notes/math.md`）而非概念名 |
| `common_mistakes` | 硬编码 `"无已知错误模式"` | ❌ 假修复 — commit 自己承认 "keep common_mistakes as placeholder (not separable from generic reranked content without additional LLM step)" |

**用户影响**：验证服务 LLM prompt 的"补充上下文"段中：
- `常见错误` 永远是空的（占位符）
- `相关概念` 可能显示为文件路径，让 LLM 看到 `/vault/notes/math.md` 而非 `导数`/`链式法则`

更严重的是 **测试用例完全绕过 transform** — `test_verification_service_activation.py:100-108` 的 mock 直接返回旧字段结构 (`learning_history`/`related_concepts`/`common_mistakes`)，导致 transform 逻辑改坏也不会被测试发现。

### 残余项 2：MAX_EPISODE_CACHE 是全局上限，多白板会互相挤掉

`memory_service.py:151` 定义 `MAX_EPISODE_CACHE = 2000`，但 `self._episodes` (line 167) 是**单个共享 list**，不按 `group_id` 分桶。所有 5 个 enforce 点 (line 298, 450, 1062, 1218, 1710) 都执行 `self._episodes = self._episodes[-MAX_EPISODE_CACHE:]`，全局 FIFO。

**用户影响**（实测计算）：
- 每个白板节点 ≈ 17 episodes（10 交互 + 5 导航 + 2 总结）
- 单白板：≈ 117 节点后开始 FIFO 丢数据
- 多白板（3 个）：每个白板 ≈ 39 节点后开始丢数据

`archive_scheduler` 不缓解此问题（它只归档 conversation，不管 episode 内存缓存）。Wave 1 已修复"搜索时按 group_id 过滤"(`27bbd73`)，但**存储侧仍是全局共享**，所以"过滤"只是把杂质过滤掉，不能阻止"我的 episode 被别的 group 挤掉"。

### 残余项 3：FR-KG-04 文档与代码不一致

`docs/project-status/fr-exploration/FR-KG-04/FR-KG-04.md` 第 110-131 行声称的调用链：

```
POST /api/v1/sync/batch
  ↓
canvas_service.add_edge()  [lines 901-956]
  ↓
_sync_edge_to_neo4j()      [写 CONNECTS_TO]
```

**但实际代码是**：

```
POST /api/v1/sync/batch
  ↓
SyncService.process_sync_batch()  [完全不调用 CanvasService]
  ↓
_upsert_edge()                    [写 CANVAS_EDGE]
```

文档错把"已废弃的 Path B"当成"主路径 A"描述，导致后续排障/重构都会被引导到错误方向。这是认知债务，不是 bug，但属于 P1 优先级（每次新人接手 FR-KG-04 都会被误导一次）。

### 发现来源

- 4 轮 Explore Agent 代码级核实（2026-04-05 ~ 2026-04-06）
- ChatGPT Deep Research 报告 #9 (`/Users/Heishing/Downloads/deep-research-report-9.md`)
- commit f215830 git diff 直接审阅
- 探索计划文件：`/Users/Heishing/.claude/plans/mutable-booping-cookie.md`

## What Changes

### 目标

1. **RAG transform 字段完整化**：让 `common_mistakes` 有真实数据源、`related_concepts` 拒绝退化为文件路径
2. **RAG transform 测试覆盖**：mock 必须用 RAG 实际返回结构（`reranked_results`），断言 transform 输出非空非占位
3. **Episode 缓存按 group_id 隔离**：`self._episodes` 改为 `Dict[str, Deque[...]]`，每个 group 独立 2000 上限
4. **FR-KG-04 文档同步**：消除 `canvas_service.add_edge()` 调用链描述，改为 `SyncService` 真实路径
5. **memory event 触发补全**：`/api/v1/sync/batch` 在 Segment 3 (Edge) 提交后触发学习事件，避免离线同步的边不进入 Graphiti

### 范围

**做**：
- **Phase 1 (P0)**: Episode 缓存数据结构改造 — `List` → `Dict[group_id, Deque(maxlen=2000)]`
- **Phase 2 (P0)**: RAG transform `common_mistakes` 真实数据源 — 从 BKT lapses + verification 历史错误抽取
- **Phase 3 (P0)**: RAG transform `related_concepts` 守护 — 拒绝接受看起来像文件路径的 metadata.source（含 `/`、`.md`、`.pdf` 等）
- **Phase 4 (P1)**: 替换 `test_verification_service_activation.py` 的 RAG mock，改用真实 `reranked_results` 结构
- **Phase 5 (P1)**: 更新 `FR-KG-04.md` 的调用链描述，删除 CanvasService 路径
- **Phase 6 (P2)**: `/sync/batch` Segment 3 完成后触发 memory event（非阻塞）

**不做（延后）**：
- `_get_rag_context_for_concept` 的完整重新设计（依赖 RAG service 增加 `extract_mistake_patterns` 能力，独立 change）
- common_mistakes 用 LLM 二次抽取（成本太高，本 change 用基于已有 BKT 数据的快速方案）
- Episode 缓存的 SQLite 持久化（依赖 conversation_archive 重构）
- 删除 verification_service.py:1832-1858 的 transform 函数（该函数仍是必要的 adapter，本 change 改进它而非删除）

### 与已 active change 的协调

本 change 与 `fix-fr-kg-04-schema-drift-and-sync-hardening` 是**互补关系**：

| 关注点 | active change | 本 change |
|--------|--------------|-----------|
| schema 统一 (`{uuid}` → `{id}`) | ✅ Phase 1 | ❌ |
| sync/batch 鉴权 | ✅ Phase 2 | ❌ |
| Segment Commit + 静默失败 | ✅ Phase 3, 11 | ❌ |
| `verification_service.py:1832-1947` | ⛔ 严禁修改 | ✅ 改进 transform 字段 |
| Episode 全局上限 | ❌ | ✅ Phase 1 |
| RAG transform 测试覆盖 | ❌ | ✅ Phase 4 |
| FR-KG-04 文档不一致 | ❌ | ✅ Phase 5 |
| sync/batch memory event | ❌ | ✅ Phase 6 |

active change 写"严禁修改 verification_service.py:1832-1947"是为了避免在它进行中产生 merge 冲突，**不是永久禁止**。本 change 必须在 active change 完成 Phase 11 后再开始 Phase 2-3。

## Capabilities

### Modified Capabilities

- `algo-rag`: RAG transform 字段语义契约扩展 — `common_mistakes` 必须有真实数据源（不能是占位符），`related_concepts` 必须拒绝文件路径模式
- `algo-memory`: Episode 缓存隔离契约 — 按 `group_id` 分桶、每桶独立上限、enforce 点全部走分桶接口

### New Capabilities

无（本 change 不引入新能力，只补全已有能力的契约缺口）

## Impact

### Affected Code

**Backend services**:
- `backend/app/services/memory_service.py:151,167,297-298,449-450,1062,1218,1710` — Episode 缓存改为 `Dict[str, Deque[Dict, maxlen=2000]]`
- `backend/app/services/memory_service.py:558-562,1622-1640` — 搜索接口同步改造（已部分完成于 Wave 1 commit `27bbd73`）
- `backend/app/services/verification_service.py:1832-1858` — `_get_rag_context_for_concept` 改进
- `backend/app/services/verification_service.py` (新增私有方法) — `_extract_common_mistakes_from_bkt(concept_id)` 从 BKT lapse history 提取错误模式
- `backend/app/services/verification_service.py` (新增私有方法) — `_filter_path_like_strings(candidates)` 过滤路径退化项
- `backend/app/api/v1/endpoints/sync.py` — Segment 3 提交后触发 `memory_service.record_learning_event(event_type=EDGE_CREATED)`

**Tests**:
- `backend/tests/unit/test_verification_service_activation.py:100-108` — 替换 mock 为真实 `reranked_results` 结构
- `backend/tests/unit/test_memory_episode_per_group.py` (新) — 每个 group 独立 2000 上限、互不挤掉、删除某 group 不影响其他
- `backend/tests/unit/test_rag_transform_field_completeness.py` (新) — common_mistakes 非占位、related_concepts 不含文件路径

**Documentation**:
- `docs/project-status/fr-exploration/FR-KG-04/FR-KG-04.md:110-131` — 调用链描述修正
- `docs/project-status/fr-exploration/FR-KG-04/FR-KG-04.md:245-254` — 移除 "Path B 是死代码" 表述（active change 已彻底删除）

### Affected APIs

- 无 API breaking change
- `_get_rag_context_for_concept` 是私有方法，return shape 不变（仍为 `{learning_history, related_concepts, common_mistakes}`），只改进字段内容质量

### Affected Dependencies

- 无新增 Python 依赖

### Systems

- **MemoryService 内存模型**：从单 list 改为 dict-of-deque，所有现有 enforce 点必须更新；老用户重启后内存缓存会重建（数据来源于 Neo4j 持久化层）
- **Neo4j**：无 schema 变更
- **IndexedDB**：无变更

### Not Changing

- `verification_service.py:1832-1858` 的 return shape — 必须保持 3 字段契约不变
- `rag_service.py` — 不修改 RAG 返回结构（active change 已确认 `reranked_results` 是正确契约）
- `memory_service.py` 的 Neo4j 持久化路径 — 只改内存缓存层
- `archive_scheduler.py` — 不参与本 change，conversation 归档另说

### Rollback

- **Phase 1 (Episode per-group)**：数据结构改造可独立 revert，回退到全局 list 不影响 Neo4j 持久化层；但 `27bbd73` 的搜索过滤代码需要同步还原
- **Phase 2 (common_mistakes 真实数据源)**：新 helper 方法可独立 revert，transform 退回到硬编码占位符（即 commit f215830 状态）
- **Phase 3 (related_concepts 守护)**：guard 函数可独立 revert
- **Phase 4 (测试改造)**：新 mock 与旧 mock 共存（用 fixture 分支），可任一启用
- **Phase 5 (文档)**：纯文档改动，git revert 即可
- **Phase 6 (memory event 触发)**：可用 feature flag `SYNC_BATCH_TRIGGER_MEMORY_EVENT` 控制开关

### Risk

- **per-group dict 内存上界**：理论最坏情况下每个 group 2000 条 × group 数量。若用户创建 50 个白板，总内存上界从 2000 → 100,000 episode。需要监控并设置 max_groups 守卫（Phase 1 task 1.6）
- **common_mistakes 数据源选择**：从 BKT lapses 抽取虽然真实但语义偏窄（只反映"答错过的题"），不能表达"常见错误模式"。本 change 接受这个限制，未来若有 LLM 二次抽取再升级
- **related_concepts 守护过严**：可能误杀真实概念名（如有用户用 `concept.md` 命名节点）。Phase 3 的过滤规则需要测试覆盖边界 case
- **测试 mock 改造可能暴露其他失败**：原 mock 用旧字段结构，可能掩盖了其他依赖该返回值的代码 bug，改造后会暴露出来——这是好事但需要预留排查时间

## 探索记录

详细探索过程见：
- `/Users/Heishing/.claude/plans/mutable-booping-cookie.md`（4 轮 Explore Agent 报告）
- `/Users/Heishing/Downloads/deep-research-report-9.md`（ChatGPT Deep Research 报告）
- commit `f215830` 的 git diff（部分修复的实际代码）

### 未在本 change 范围内的探索发现（仅作记录）

- **FSRS 难度阈值是 0.3/0.5/0.7（基于 effective_proficiency），不是 60/80（基于 raw score）** — 这是文档准确性问题，而非 bug，可在 FR-KG-04.md 修正时一起更新
- **question_generator.py:45-47 的 W_MASTERY=0.4 / W_RETRIEVABILITY=0.3 / W_KG_RELEVANCE=0.3 公式确实存在** — 不是 bug，是正确的 fusion 实现
- **CanvasService 路径 B (CONNECTS_TO) 死代码** — 已被 active change Phase 6 处理
