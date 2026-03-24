# ACP 考察读取路径 — 技术设计文档

> 设计目标：Graphiti --> ACP 数据包 --> AI 精准出题的完整读取路径

---

## 1. ACP 数据包 Pydantic Schema（增强版）

现有 `ACPData`（`backend/app/models/exam_models.py` L173-192）已有基础字段，但缺少：
- Graphiti 误解历史（Observer 写入的 Misconception/ProblemTrap）
- FSRS 复习状态（due/overdue/fresh）
- BKT 详细参数（P_T, P_S, P_G）
- 错误类型分布统计
- Token 预算元数据

### 增强 Schema 定义

```python
# backend/app/models/exam_models.py — 新增/替换 ACPData

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FsrsReviewStatus(str, Enum):
    """FSRS 复习状态分类."""
    FRESH = "fresh"          # R > 0.9, 刚复习过
    DUE = "due"              # 0.5 < R <= 0.9, 即将到期
    OVERDUE = "overdue"      # R <= 0.5, 已过期
    NEW = "new"              # 从未复习


class MistakeRecord(BaseModel):
    """单条误解/错误记录 — 从 Graphiti EntityNode 读取."""
    error_type: str = Field(
        ...,
        description="4类错误之一: problem_framing | reasoning_fallacy | knowledge_gap | superficial"
    )
    description: str = Field(..., description="错误描述")
    remedy_strategy: str = Field(
        default="",
        description="对应补救策略: same_structure_new_problem | find_error_counterexample | backtrack_definition | discrimination_transfer"
    )
    source: str = Field(
        default="graphiti",
        description="数据来源: graphiti(Observer写入) | error_classifier(Agent record_error) | memory_service"
    )
    recorded_at: str = Field(default="", description="记录时间 ISO 格式")
    session_context: str = Field(default="", description="错误发生时的对话片段（截断到200字）")


class ErrorTypeDistribution(BaseModel):
    """错误类型分布统计 — 帮助 AI 识别系统性弱点模式."""
    problem_framing: int = 0
    reasoning_fallacy: int = 0
    knowledge_gap: int = 0
    superficial: int = 0
    total: int = 0

    @property
    def dominant_type(self) -> Optional[str]:
        """返回占比最高的错误类型，用于出题策略决策."""
        counts = {
            "problem_framing": self.problem_framing,
            "reasoning_fallacy": self.reasoning_fallacy,
            "knowledge_gap": self.knowledge_gap,
            "superficial": self.superficial,
        }
        if self.total == 0:
            return None
        max_type = max(counts, key=counts.get)
        return max_type if counts[max_type] > 0 else None


class BktParams(BaseModel):
    """BKT 四参数 — 暴露给 AI 做出题策略判断."""
    p_mastery: float = Field(0.1, description="P(L_n): 当前掌握概率")
    p_transit: float = Field(0.2, description="P(T): 每次练习的学习概率")
    p_guess: float = Field(0.2, description="P(G): 猜对概率 — 高值说明易猜对，需出更开放的题")
    p_slip: float = Field(0.1, description="P(S): 失误概率 — 高值说明已掌握但不稳定")


class FsrsState(BaseModel):
    """FSRS 记忆状态 — 决定是否需要复习型考察."""
    stability: float = Field(0.0, description="记忆稳定性（天数）")
    difficulty: float = Field(0.0, description="FSRS 难度参数")
    retrievability: float = Field(1.0, description="当前可提取性 R (0-1)")
    review_status: FsrsReviewStatus = Field(
        FsrsReviewStatus.NEW,
        description="复习状态分类"
    )
    next_review: Optional[str] = Field(None, description="下次复习日期 ISO 格式")
    reps: int = Field(0, description="复习次数")
    lapses: int = Field(0, description="遗忘次数 — 高值说明反复遗忘")


class ACPDataEnhanced(BaseModel):
    """Assessment Context Package (增强版) — 考察模式专用.

    汇聚 6 个数据源为 AI 出题提供完整学生画像。
    Token 预算: 全包 <= 4K tokens (~12K chars mixed CN/EN).

    数据源:
        1. MasteryStore (Neo4j EntityNode) -> bkt_params, fsrs_state
        2. MemoryService (episodes)        -> student_tips, legacy errors
        3. Neo4j (Cypher)                  -> edge_reasons, neighbor_summaries
        4. Graphiti (EntityNode)           -> mistake_history (Observer写入)
        5. CanvasService                   -> node_content, node_type
        6. ConversationArchive             -> conversation_summary
    """

    # --- 节点基本信息 (Source: CanvasService) ---
    node_id: str
    node_content: str = Field(default="", description="节点文本内容，截断到1000字")
    node_type: str = Field(
        default="knowledge_point",
        description="knowledge_point | problem_type — 影响出题策略"
    )

    # --- 精通度：BKT (Source: MasteryStore) ---
    bkt_params: BktParams = Field(default_factory=BktParams)

    # --- 记忆状态：FSRS (Source: MasteryStore + MasteryEngine) ---
    fsrs_state: FsrsState = Field(default_factory=FsrsState)

    # --- 综合精通度 (Source: MasteryEngine.effective_proficiency) ---
    effective_proficiency: float = Field(
        0.0, description="BKT+FSRS+override 融合后的有效精通度 (0-1)"
    )
    mastery_label: str = Field(
        "Not Assessed",
        description="5级标签: Not Assessed | Shaky | Developing | Proficient | Mastered"
    )

    # --- 学生标注 Tips (Source: MemoryService + LearningMemoryClient) ---
    student_tips: List[str] = Field(
        default_factory=list,
        description="学生自己的理解笔记，最多5条"
    )

    # --- 误解历史 (Source: Graphiti EntityNode + MemoryService) ---
    mistake_history: List[MistakeRecord] = Field(
        default_factory=list,
        description="历史误解记录，按时间倒序，最多8条"
    )
    error_distribution: ErrorTypeDistribution = Field(
        default_factory=ErrorTypeDistribution,
        description="错误类型分布统计"
    )

    # --- 概念关系 (Source: Neo4j edges) ---
    edge_reasons: List[str] = Field(
        default_factory=list,
        description="与其他节点的关系理由，最多5条"
    )

    # --- 邻居上下文 (Source: Neo4j 1-hop) ---
    neighbor_summaries: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="1-hop邻居摘要 [{name, mastery_level, edge_reason}]，最多5个"
    )

    # --- 对话历史摘要 (Source: ConversationArchive) ---
    conversation_summary: str = Field(
        default="",
        description="最近对话摘要，截断到500字"
    )

    # --- Token 预算元数据 ---
    estimated_tokens: int = Field(0, description="估算 token 数")
    budget_exceeded: bool = Field(False, description="是否触发了截断")
```

### 字段-数据源-优先级-Token预算 映射表

| 字段 | 数据源 | 读取方法 | 优先级 | Token预算 |
|------|--------|----------|--------|-----------|
| `node_content` | CanvasService | `find_node_across_canvases()` | P0-必须 | ~500 tokens |
| `bkt_params` | MasteryStore (Neo4j) | `get_concept()` -> ConceptState | P0-必须 | ~50 tokens |
| `fsrs_state` | MasteryStore + MasteryEngine | `get_concept()` + `get_retrievability()` | P0-必须 | ~80 tokens |
| `effective_proficiency` | MasteryEngine | `effective_proficiency(concept)` | P0-必须 | ~20 tokens |
| `mastery_label` | MasteryEngine | `mastery_level(concept)` -> label | P0-必须 | ~10 tokens |
| `mistake_history` | Graphiti (Neo4j EntityNode) | Cypher: `entity_type IN [Misconception, ProblemTrap]` | P1-关键 | ~600 tokens |
| `error_distribution` | 从 mistake_history 计算 | 内存聚合 | P1-关键 | ~30 tokens |
| `student_tips` | MemoryService + LearningMemoryClient | `search_memories()` + `search_memories()` | P1-关键 | ~300 tokens |
| `edge_reasons` | Neo4j (Cypher) | `MATCH (n)-[r]-(m) RETURN r.reason` | P2-有用 | ~200 tokens |
| `neighbor_summaries` | Neo4j (Cypher) | 1-hop query with mastery | P2-有用 | ~300 tokens |
| `conversation_summary` | ConversationArchive (Neo4j) | `EpisodicNode source_description='conversation_archive'` | P3-补充 | ~300 tokens |

**总预算**: 4K tokens (~12K chars)

**截断优先级**（超预算时从后向前截断）：
1. conversation_summary -> 截到200字
2. neighbor_summaries -> 截到3个
3. edge_reasons -> 截到3条
4. student_tips -> 截到3条
5. mistake_history -> 截到5条
6. node_content -> 截到500字
7. bkt_params/fsrs_state/effective_proficiency -> 不截断

---

## 2. Graphiti 误解读取逻辑

### 2.1 数据写入路径回顾

误解数据通过两条路径写入 Neo4j：

**路径 A: Agent record_error MCP 工具**
```
Agent 检测到错误 -> record_error() -> ErrorClassifier.classify()
  -> Misconception entity -> MemoryService.record_learning_event()
  -> Neo4j EpisodicNode (source_description='error_record')
```

**路径 B: GraphitiBridge Observer**
```
Canvas 节点颜色变化(Red/Purple) -> MemoryService.record_learning_event()
  -> GraphitiBridgeService.bridge_to_claude_format()
  -> Neo4j EntityNode (entity_type='Misconception'|'ProblemTrap')
```

### 2.2 读取策略：Neo4j Cypher 直查（不走 search_memory_facts）

**理由**：
- `search_memory_facts` 是 Graphiti MCP 的语义搜索接口，适合模糊查询
- 考察场景需要**按 node_id 精确查询 + 按时间排序**，Cypher 直查更高效准确
- 已有代码（`question_generator.py` L582-609）已经在用 Cypher 直查 EpisodicNode

### 2.3 查询实现

```python
# backend/app/services/acp_assembler.py — 新增文件

async def fetch_mistake_history(
    node_id: str,
    group_id: str,
    max_records: int = 8,
) -> tuple[list[MistakeRecord], ErrorTypeDistribution]:
    """从 Graphiti (Neo4j) 读取节点的历史误解记录.

    合并两个数据源：
    1. EntityNode (entity_type IN ['Misconception', 'ProblemTrap', 'LogicalFallacy'])
       — GraphitiBridge Observer 写入
    2. EpisodicNode (source_description = 'error_record')
       — Agent record_error 工具写入

    Args:
        node_id: Canvas 节点 ID
        group_id: 学科隔离命名空间
        max_records: 最大返回条数（时间倒序 top-N）

    Returns:
        (mistake_records, error_distribution)
    """
    from app.clients.neo4j_client import get_neo4j_client
    client = get_neo4j_client()

    records: list[MistakeRecord] = []

    # Source 1: GraphitiBridge 写入的 EntityNode
    entity_query = """
    MATCH (n:EntityNode)
    WHERE (n.node_id = $nodeIdCanvas OR n.concept = $nodeId)
      AND n.group_id = $groupId
      AND n.entity_type IN ['Misconception', 'ProblemTrap', 'LogicalFallacy']
    RETURN n.entity_type AS entity_type,
           n.episode_body AS description,
           n.source_description AS source_desc,
           n.created_at AS created_at,
           n.concept AS concept
    ORDER BY n.updated_at DESC
    LIMIT $limit
    """
    try:
        results = await client.run_query(
            entity_query,
            nodeIdCanvas=f"canvas-{node_id}",
            nodeId=node_id,
            groupId=group_id,
            limit=max_records,
        )
        for row in results or []:
            data = row if isinstance(row, dict) else row.data()
            entity_type = data.get("entity_type", "")
            # Map entity_type to error_type
            error_type = _entity_type_to_error_type(entity_type)
            records.append(MistakeRecord(
                error_type=error_type,
                description=_truncate(data.get("description", ""), 200),
                remedy_strategy=_error_type_to_remedy(error_type),
                source="graphiti",
                recorded_at=data.get("created_at", ""),
            ))
    except Exception as e:
        logger.warning("Failed to fetch EntityNode mistakes for %s: %s", node_id, e)

    # Source 2: Agent record_error 写入的 EpisodicNode
    episodic_query = """
    MATCH (e:EpisodicNode)
    WHERE e.source_description = 'error_record'
      AND e.node_id = $nodeId
    RETURN e.error_type AS error_type,
           e.description AS description,
           e.created_at AS created_at,
           e.content AS content
    ORDER BY e.created_at DESC
    LIMIT $limit
    """
    try:
        results = await client.run_query(
            episodic_query,
            nodeId=node_id,
            limit=max_records,
        )
        for row in results or []:
            data = row if isinstance(row, dict) else row.data()
            error_type = data.get("error_type", "unknown")
            desc = data.get("description", "") or data.get("content", "")
            records.append(MistakeRecord(
                error_type=error_type,
                description=_truncate(desc, 200),
                remedy_strategy=_error_type_to_remedy(error_type),
                source="error_classifier",
                recorded_at=data.get("created_at", ""),
            ))
    except Exception as e:
        logger.warning("Failed to fetch EpisodicNode mistakes for %s: %s", node_id, e)

    # 去重（按 description 前100字去重）+ 按时间排序
    seen = set()
    unique_records = []
    for rec in records:
        key = rec.description[:100]
        if key not in seen:
            seen.add(key)
            unique_records.append(rec)
    unique_records.sort(key=lambda r: r.recorded_at, reverse=True)
    unique_records = unique_records[:max_records]

    # 统计错误类型分布
    dist = ErrorTypeDistribution()
    for rec in unique_records:
        if rec.error_type == "problem_framing":
            dist.problem_framing += 1
        elif rec.error_type == "reasoning_fallacy":
            dist.reasoning_fallacy += 1
        elif rec.error_type == "knowledge_gap":
            dist.knowledge_gap += 1
        elif rec.error_type == "superficial":
            dist.superficial += 1
    dist.total = len(unique_records)

    return unique_records, dist


def _entity_type_to_error_type(entity_type: str) -> str:
    """Map Graphiti entity_type to 4-type error classification."""
    mapping = {
        "Misconception": "knowledge_gap",
        "ProblemTrap": "problem_framing",
        "LogicalFallacy": "reasoning_fallacy",
    }
    return mapping.get(entity_type, "superficial")


def _error_type_to_remedy(error_type: str) -> str:
    """Map error_type to remedy_strategy."""
    mapping = {
        "problem_framing": "same_structure_new_problem",
        "reasoning_fallacy": "find_error_counterexample",
        "knowledge_gap": "backtrack_definition",
        "superficial": "discrimination_transfer",
    }
    return mapping.get(error_type, "")


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    last_break = max(text.rfind("。", 0, max_len), text.rfind(".", 0, max_len))
    if last_break > max_len * 0.5:
        return text[:last_break + 1]
    return text[:max_len] + "..."
```

### 2.4 查询节点说明

```
Node ID 匹配策略（兼容两种写入路径）:

EntityNode: WHERE n.node_id = 'canvas-{node_id}' OR n.concept = '{node_id}'
  — GraphitiBridge 用 'canvas-' 前缀写入 node_id
  — concept 字段存原始概念名

EpisodicNode: WHERE e.node_id = '{node_id}'
  — Agent record_error 直接用 node_id
```

---

## 3. ACP 完整组装流程

```python
# backend/app/services/acp_assembler.py — assemble_exam_acp 方法

async def assemble_exam_acp(
    node_id: str,
    group_id: str | None = None,
) -> ACPDataEnhanced:
    """组装考察模式专用 ACP 数据包.

    并行获取 6 个数据源，合并为 ACPDataEnhanced.
    失败的数据源静默降级，不阻塞其他源。

    调用链:
        generate_question(exam_id=...) -> QuestionGenerator.assemble_acp()
          -> 替换为 assemble_exam_acp()
    """
    import asyncio
    from app.config import DEFAULT_GROUP_ID
    if group_id is None:
        group_id = DEFAULT_GROUP_ID

    acp = ACPDataEnhanced(node_id=node_id)

    # 并行获取所有数据源
    (
        node_data,
        mastery_result,
        tips_errors,
        mistakes_result,
        edge_reasons,
        neighbor_records,
        conv_summary,
    ) = await asyncio.gather(
        _fetch_node_content(node_id),                                # Source 1: Canvas
        _fetch_mastery_full(node_id, group_id),                      # Source 2: MasteryStore+Engine
        _fetch_tips_and_legacy_errors(node_id),                      # Source 3: MemoryService
        fetch_mistake_history(node_id, group_id, max_records=8),     # Source 4: Graphiti
        _fetch_edge_reasons_for_acp(node_id),                        # Source 5: Neo4j edges
        _fetch_neighbor_summaries(node_id),                          # Source 6a: Neo4j neighbors
        _fetch_conversation_summary(node_id),                        # Source 6b: Archive
        return_exceptions=True,
    )

    # 1. 节点内容
    if isinstance(node_data, dict):
        acp.node_content = _truncate(node_data.get("text", ""), 1000)
        k_sig, p_sig = _classify_content(acp.node_content)
        if p_sig > k_sig:
            acp.node_type = "problem_type"

    # 2. 精通度
    if isinstance(mastery_result, dict):
        acp.bkt_params = BktParams(
            p_mastery=mastery_result["p_mastery"],
            p_transit=mastery_result["p_transit"],
            p_guess=mastery_result["p_guess"],
            p_slip=mastery_result["p_slip"],
        )
        acp.fsrs_state = FsrsState(
            stability=mastery_result["fsrs_stability"],
            difficulty=mastery_result["fsrs_difficulty"],
            retrievability=mastery_result["retrievability"],
            review_status=mastery_result["review_status"],
            next_review=mastery_result.get("next_review"),
            reps=mastery_result["fsrs_reps"],
            lapses=mastery_result["fsrs_lapses"],
        )
        acp.effective_proficiency = mastery_result["effective_proficiency"]
        acp.mastery_label = mastery_result["mastery_label"]

    # 3. Tips
    if isinstance(tips_errors, tuple):
        tips, _legacy_errors = tips_errors
        acp.student_tips = [t.get("content", "") for t in tips[:5] if t.get("content")]

    # 4. 误解历史 (Graphiti)
    if isinstance(mistakes_result, tuple):
        mistake_records, error_dist = mistakes_result
        acp.mistake_history = mistake_records
        acp.error_distribution = error_dist

    # 5. Edge 理由
    if isinstance(edge_reasons, list):
        acp.edge_reasons = edge_reasons[:5]

    # 6. 邻居摘要
    if isinstance(neighbor_records, list):
        acp.neighbor_summaries = neighbor_records[:5]

    # 7. 对话历史摘要
    if isinstance(conv_summary, str):
        acp.conversation_summary = _truncate(conv_summary, 500)

    # Token 预算执行
    _enforce_exam_token_budget(acp)

    return acp


async def _fetch_mastery_full(node_id: str, group_id: str) -> dict:
    """获取完整精通度数据（BKT 四参数 + FSRS 状态 + 有效精通度）."""
    from app.services.mastery_store import get_mastery_store
    from app.services.mastery_engine import get_mastery_engine
    from app.models.mastery_state import DEFAULT_BKT_PARAMS

    store = get_mastery_store()
    engine = get_mastery_engine()
    concept = await store.get_concept(node_id, group_id)

    if concept is None:
        return {
            "p_mastery": 0.1, "p_transit": 0.2, "p_guess": 0.2, "p_slip": 0.1,
            "fsrs_stability": 0.0, "fsrs_difficulty": 0.0,
            "retrievability": 1.0, "review_status": "new",
            "fsrs_reps": 0, "fsrs_lapses": 0,
            "effective_proficiency": 0.0, "mastery_label": "Not Assessed",
        }

    bkt_defaults = DEFAULT_BKT_PARAMS.get(concept.bkt_difficulty, DEFAULT_BKT_PARAMS["medium"])
    R = engine.get_retrievability(concept)

    # 确定复习状态
    if concept.fsrs_reps == 0:
        review_status = "new"
    elif R > 0.9:
        review_status = "fresh"
    elif R > 0.5:
        review_status = "due"
    else:
        review_status = "overdue"

    next_review = None
    if concept.last_interaction_ts and concept.fsrs_stability > 0:
        from datetime import timedelta
        next_dt = concept.last_interaction_ts + timedelta(days=concept.fsrs_stability)
        next_review = next_dt.isoformat()

    return {
        "p_mastery": concept.p_mastery,
        "p_transit": bkt_defaults["P_T"],
        "p_guess": bkt_defaults["P_G"],
        "p_slip": bkt_defaults["P_S"],
        "fsrs_stability": concept.fsrs_stability,
        "fsrs_difficulty": concept.fsrs_difficulty,
        "retrievability": R,
        "review_status": review_status,
        "next_review": next_review,
        "fsrs_reps": concept.fsrs_reps,
        "fsrs_lapses": concept.fsrs_lapses,
        "effective_proficiency": engine.effective_proficiency(concept),
        "mastery_label": engine.mastery_label(concept),
    }
```

---

## 4. 考察模式 System Prompt 模板

### 4.1 与对话模式的核心区别

| 维度 | 对话模式 (conversation) | 考察模式 (exam) |
|------|------------------------|----------------|
| 角色 | 学习助手 → 解答 + 教学 | 考官 → 提问 + 评估 |
| 数据注入 | Tier1+Tier2 markdown (format_as_markdown) | ACP 完整数据包 (结构化) |
| 知识透露 | 主动分享知识 | 禁止透露答案 |
| 误解数据 | 展示为"历史错误"供学生参考 | 作为出题靶向依据（学生不可见） |
| BKT 参数 | 只展示 p_mastery | 暴露完整四参数驱动策略 |
| FSRS 状态 | 只展示 next_review | 暴露 R/stability/review_status 驱动时机 |

### 4.2 5 层 Prompt 架构（增强 Layer 3）

现有 5 层架构（`question_generator.py` L246-283）不变，增强 Layer 3 的 ACP 注入：

```
Layer 1 (static):  考官角色定义        <- layer1_role.md (不变)
Layer 2 (dynamic): 考察模式            <- layer2_mode.md (不变)
Layer 3 (dynamic): ACP 学生数据 ★增强  <- 新的 _format_exam_acp_layer()
Layer 4 (static):  出题规则            <- layer4_rules.md (不变)
Layer 5 (static):  评分预设            <- layer5_scoring_preset.md (不变)
```

### 4.3 增强版 Layer 3 格式化

```python
def _format_exam_acp_layer(acp: ACPDataEnhanced) -> str:
    """将 ACPDataEnhanced 格式化为 Layer 3 prompt 文本.

    设计原则:
    - 结构化 markdown 让 LLM 易于解析
    - 每个 section 有明确的策略指引（不是裸数据）
    - 误解历史是出题靶向核心
    """
    parts: list[str] = []

    # --- 目标节点 ---
    parts.append(f"**目标节点**: {acp.node_content[:300]}")
    parts.append(f"**节点类型**: {acp.node_type}")

    # --- 精通度综合判断 ---
    prof_section = (
        f"**精通度**: {acp.mastery_label} "
        f"(effective={acp.effective_proficiency:.2f})\n"
    )
    bkt = acp.bkt_params
    prof_section += f"  - BKT: P(掌握)={bkt.p_mastery:.2f}, P(学习)={bkt.p_transit:.2f}, P(猜对)={bkt.p_guess:.2f}, P(失误)={bkt.p_slip:.2f}\n"

    # P(S) 高 → 已掌握但不稳定 → 出压力题
    if bkt.p_slip > 0.12:
        prof_section += "  - ⚠ P(失误)偏高：学生可能已掌握但不稳定，建议出需要精确推理的题验证\n"
    # P(G) 高 → 容易猜对 → 出开放题
    if bkt.p_guess > 0.22:
        prof_section += "  - ⚠ P(猜对)偏高：建议出开放式解释题，减少猜测空间\n"

    parts.append(prof_section)

    # --- FSRS 记忆状态 ---
    fsrs = acp.fsrs_state
    fsrs_section = (
        f"**记忆状态**: {fsrs.review_status.upper()}\n"
        f"  - 可提取性 R={fsrs.retrievability:.2f}, "
        f"稳定性={fsrs.stability:.1f}天, "
        f"复习{fsrs.reps}次, 遗忘{fsrs.lapses}次\n"
    )
    if fsrs.review_status == "overdue":
        fsrs_section += "  - ⚠ 记忆已过期：先出基础回忆题确认是否遗忘，再决定难度\n"
    elif fsrs.review_status == "fresh":
        fsrs_section += "  - 记忆新鲜：可直接出匹配精通度的题目\n"
    if fsrs.lapses >= 3:
        fsrs_section += f"  - ⚠ 反复遗忘{fsrs.lapses}次：此概念是顽固弱点，需要变换角度出题\n"

    parts.append(fsrs_section)

    # --- 误解历史（出题靶向核心）---
    if acp.mistake_history:
        mistake_section = "**历史误解（出题靶向）**:\n"
        for i, rec in enumerate(acp.mistake_history[:5], 1):
            mistake_section += (
                f"  {i}. [{rec.error_type}] {rec.description}\n"
                f"     补救策略: {rec.remedy_strategy}\n"
            )

        # 错误模式总结
        dist = acp.error_distribution
        if dist.dominant_type:
            type_labels = {
                "problem_framing": "破题错误",
                "reasoning_fallacy": "推理谬误",
                "knowledge_gap": "知识点缺失",
                "superficial": "似懂非懂",
            }
            mistake_section += (
                f"  **错误模式**: 主要为「{type_labels.get(dist.dominant_type, dist.dominant_type)}」"
                f"({getattr(dist, dist.dominant_type)}/{dist.total})\n"
                f"  **出题策略**: 重点针对此错误模式设计考察题\n"
            )
        parts.append(mistake_section)

    # --- 学生标注 ---
    if acp.student_tips:
        tips_str = "\n".join(f"  - {t}" for t in acp.student_tips[:5])
        parts.append(f"**学生自己的理解笔记**:\n{tips_str}")

    # --- 概念关系 ---
    if acp.edge_reasons:
        edges_str = "; ".join(acp.edge_reasons[:5])
        parts.append(f"**概念关系**: {edges_str}")

    # --- 对话历史 ---
    if acp.conversation_summary:
        parts.append(f"**最近对话摘要**: {acp.conversation_summary[:300]}")

    return "\n\n".join(parts)
```

### 4.4 出题策略决策树（BKT + FSRS + 错误历史综合）

```
输入: ACPDataEnhanced

                      FSRS review_status?
                     /         |         \
                  overdue      due       fresh/new
                   |            |            |
          先出基础回忆题    正常难度匹配    正常难度匹配
          确认是否遗忘
                   |
            学生回忆成功?
           /            \
         Yes             No
          |               |
     按 effective_    回退到 Bloom
     proficiency      Remember 级
     正常出题

                effective_proficiency?
              /      |       |        \
          < 0.3   0.3-0.5  0.5-0.7   > 0.7
            |       |        |          |
         Bloom    Bloom    Bloom      Bloom
        Remember Understand Apply    Evaluate
            |       |        |          |
        基础定义  解释比较  应用分析   评价创造

                  有 mistake_history?
                 /                  \
               Yes                   No
                |                     |
        按 dominant_type          通用出题
        选择对应策略:
          problem_framing → 同结构新题
          reasoning_fallacy → 找错/反例题
          knowledge_gap → 回退定义题
          superficial → 辨析/迁移题

                BKT P(S) > 0.12?
               /              \
             Yes               No
              |                 |
        出精确推理题          正常策略
        验证稳定性

                BKT P(G) > 0.22?
               /              \
             Yes               No
              |                 |
        出开放解释题          允许选择题
        减少猜测空间
```

### 4.5 完整 System Prompt 模板（考察模式）

```markdown
<!-- 已有 Layer 1: layer1_role.md — 不变 -->
你是一位经验丰富的学习考官...

---

<!-- 已有 Layer 2: layer2_mode.md — 不变 -->
当前考察模式: {{exam_mode}}
...

---

### 学生数据（ACP）

<!-- Layer 3: 动态注入 — 由 _format_exam_acp_layer() 生成 -->

**目标节点**: 贝叶斯定理——条件概率的逆运算，P(A|B)=P(B|A)P(A)/P(B)...
**节点类型**: knowledge_point

**精通度**: Developing (effective=0.45)
  - BKT: P(掌握)=0.35, P(学习)=0.20, P(猜对)=0.20, P(失误)=0.10

**记忆状态**: DUE
  - 可提取性 R=0.62, 稳定性=5.3天, 复习3次, 遗忘1次

**历史误解（出题靶向）**:
  1. [knowledge_gap] 混淆先验概率和后验概率的区别
     补救策略: backtrack_definition
  2. [superficial] 能写出公式但不能解释每个符号的含义
     补救策略: discrimination_transfer
  **错误模式**: 主要为「知识点缺失」(1/2)
  **出题策略**: 重点针对此错误模式设计考察题

**学生自己的理解笔记**:
  - 贝叶斯定理就是"更新信念"的过程
  - P(A|B) 不等于 P(B|A) 这点容易搞混

**概念关系**: 前置→条件概率; 应用→朴素贝叶斯分类; 对比→频率学派

**最近对话摘要**: 上次讨论了贝叶斯定理在垃圾邮件分类中的应用...

---

<!-- 已有 Layer 4: layer4_rules.md — 不变 -->
### 基本出题规则
1. 一次只出一道题
2. 从学生的弱点出题...
...

---

<!-- 已有 Layer 5: layer5_scoring_preset.md — 不变 -->
出题时需考虑后续评分要求...
```

---

## 5. 接入点与调用链

### 现有 generate_question 入口改造

```
exam_tools.py generate_question(exam_id=...)
  -> QuestionGenerator.generate_exam_question()
     -> select_target_node()           # 不变
     -> assemble_acp(node_id)          # ★ 替换为 assemble_exam_acp()
     -> build_5_layer_prompt(acp)      # ★ Layer 3 用 _format_exam_acp_layer()
     -> _call_llm_for_question()       # 不变
```

### 需要修改的文件

| 文件 | 改动 |
|------|------|
| `backend/app/models/exam_models.py` | 新增 `ACPDataEnhanced` + 子模型 |
| `backend/app/services/acp_assembler.py` | **新增** — `assemble_exam_acp()` + `fetch_mistake_history()` |
| `backend/app/services/question_generator.py` | `assemble_acp()` 改为调用 `assemble_exam_acp()` + `_format_acp_layer()` 改为 `_format_exam_acp_layer()` |

### 不需要修改的文件

- `learning_context_service.py` — 对话模式的 Tier1+Tier2 保持不变
- `context.py` endpoint — 对话注入路径不变
- `exam_tools.py` — 入口签名不变，内部调用链自动切换
- `layer1_role.md` / `layer2_mode.md` / `layer4_rules.md` / `layer5_scoring_preset.md` — 静态层不变

---

## 6. 降级策略

| 数据源失败 | 降级行为 | 影响 |
|-----------|---------|------|
| MasteryStore 不可用 | BKT 使用 medium 默认参数，FSRS 标记为 new | AI 出中等难度题 |
| Graphiti/Neo4j EntityNode 查询失败 | mistake_history 为空 | AI 无靶向信息，出通用题 |
| EpisodicNode 查询失败 | 同上 | 同上 |
| MemoryService 不可用 | student_tips 为空 | AI 缺少学生笔记视角 |
| CanvasService 不可用 | node_content 为空 | AI 只能基于 ID 出题 |
| ConversationArchive 不可用 | conversation_summary 为空 | AI 缺少对话上下文 |
| 所有源均失败 | 返回只有 node_id 的最小 ACP | 模板 fallback 出题 |
