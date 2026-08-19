"""
Story 2.10: Mastery Injection + Learning Memory + Multi-Query Rewrite

Implements:
- Mastery level prefix injection (Lost in Middle effect — prompt front position)
- Graphiti learning memory retrieval (Tips, errors, Q&A)
- Multi-Query + Decomposition query rewriting

Reference:
- Lost in Middle (Anthropic + Google papers): LLMs attend more to prompt start/end
- Multi-Query Retrieval: multiple query perspectives improve recall
"""

import asyncio
import logging
import re
from typing import Any, List, Optional

logger = logging.getLogger(__name__)


# =========================================================================
# Mastery Injection (AC-2)
# =========================================================================

# Mastery level descriptions (user-facing, non-technical)
_MASTERY_LEVELS = {
    "mastered": ("掌握", "该知识点已掌握，可直接给出进阶内容或拓展应用"),
    "learning": ("学习中", "对该知识点有一定了解，请给出清晰解释并适当拓展"),
    "weak": ("薄弱", "该知识点掌握薄弱，请从基础概念开始解释，多举例子"),
    "review": ("待复习", "该知识点记忆可能衰退，请简要回顾要点并加深理解"),
}


def build_mastery_prefix(
    p_mastery: Optional[float] = None,
    memory_retention: Optional[float] = None,
    has_exam_records: bool = False,
    needs_review: bool = False,
) -> str:
    """
    Story 2.10 AC-2: Build mastery-level prefix for prompt injection.

    Placed at the very beginning of the system prompt to leverage
    the "Lost in Middle" effect (LLMs pay more attention to prompt start).

    Args:
        p_mastery: BKT p_mastery value (0.0 - 1.0), None if no data.
        memory_retention: FSRS memory retention R (0.0 - 1.0).
        has_exam_records: Whether there are exam/quiz records.
        needs_review: Whether FSRS indicates review needed.

    Returns:
        Mastery prefix string, or empty string if no data.
    """
    if p_mastery is None:
        return ""

    # Determine mastery level
    if needs_review:
        level_key = "review"
    elif p_mastery >= 0.8 and (memory_retention is None or memory_retention >= 0.8):
        level_key = "mastered"
    elif p_mastery >= 0.5:
        level_key = "learning"
    elif has_exam_records:
        level_key = "weak"
    else:
        level_key = "learning"

    label, description = _MASTERY_LEVELS[level_key]
    return f"[学习者水平] 该知识点掌握度: {label}（{description}）。请据此调整解释深度和详细程度。\n"


# =========================================================================
# Graphiti Learning Memory (AC-3)
# =========================================================================


#: P1-03 (Codex 对抗审查 2026-08-19): 检索降级原因常量。
#: 返回给调用方以区分「检索失败」与「真的没有记忆」—— 这两者此前都表现为 ""。
MEMORY_DEGRADED_NO_CLIENT = "no_client"
MEMORY_DEGRADED_TIMEOUT = "timeout"
MEMORY_DEGRADED_ERROR = "error"


async def _search_via_memory_service(
    node_hint: str,
    group_id: Optional[str],
    limit: int = 10,
) -> Optional[List[dict]]:
    """经 MemoryService 三层融合检索取学习记忆 (P1-03 首选路径)。

    为什么不再直接用 GraphitiClient.search_memories:
      GraphitiClient.search_memories 转调 search_nodes 且**不传 canvas_file**,
      于是 _resolve_group_ids(None) 只返回 ["vault__x"] 单组 —— 既不含
      `__semantic` 影子组, 也不含白板级 punycode 子组。而 learning tip/error 的
      可检索文本恰好落在影子组 (episode_worker 强制给 group_id 加 __semantic
      后缀), 主图上的结构化边只把 node_id 存进 attributes 与 uuid5 身份、
      fact 文本里没有它。两边错开 → 恒空。

    MemoryService._search_graphiti 查的是 [主图, __semantic 影子组,
    + _expand_vault_subgroups(...)] 三组, 且上层 search_memories 还叠了
    Neo4j 全文与内存两层兜底 + 术语束扩展 + FSRS 加权。

    ⛔ group_id 必须传: _search_graphiti 在 group_id=None 时会**全组检索**
    (跨 vault), 与 GraphitiClient 只查单组的行为正相反。

    Returns:
        条目列表 (每项含 content 键); None 表示 MemoryService 不可用, 由调用方降级。
    """
    try:
        # lib→app 惰性 import 是本仓既定惯例 (本模块 :223 亦然), 无循环依赖:
        # app/services/memory_service.py 全文零 agentic_rag 引用。
        from app.services.memory_service import get_memory_service
    except ImportError:
        return None

    try:
        service = await get_memory_service()
    except Exception as exc:  # noqa: BLE001 — 服务不可用即降级, 不能拖垮检索链
        logger.warning("[MEMORY] MemoryService 不可用, 降级到直连 Graphiti: %s", exc)
        return None

    # 与 search_error_memories (memory_service.py:2017-2021) 同构:
    # node_hint 当**语义提示词**拼进自然语言 query, 而非可精确匹配的 key ——
    # 图上不存在任何能被字符串命中的 node 身份字段。
    #
    # ⚠️ DD-13 名实一致声明 (P1-02 复核, Codex 2026-08-19): 本函数是
    # **vault 级语义补充召回**, 不是 node 精确读。它不做、也无法做 node 过滤 ——
    # MemoryService Tier1 的条目映射 (memory_service.py:1585-1624) 丢弃了
    # attributes/node_id, 到这一层已无从按节点筛。因此返回的可能是同 vault 内
    # 其它节点的记忆。
    #
    # 真正的 node 精确读已存在: app/services/graphiti_memory_reader.py 的
    # read_node_tips / read_node_errors / read_node_edge_reasons —— 走
    # entity_uuid_for_node(node_id, gid) → EntityEdge.get_by_node_uuid,
    # 带 active-only 过滤。它需要**真实 node_id**, 而 CanvasRAGState 只有
    # canvas_file (state.py 全文无 node_id 字段)。接通它需要改调用链把节点身份
    # 传进 state —— 已列为待办, 不在本轮范围。
    hits = await service.search_memories(
        query=f"{node_hint} 提示 tip 要点 错误 误解 mistake misconception 学习笔记",
        group_id=group_id,
        max_results=max(limit * 4, 20),
    )
    return hits or []


async def retrieve_learning_memories(
    node_id: str,
    max_tokens: int = 1000,
    graphiti_client: Optional[Any] = None,
    group_id: Optional[str] = None,
) -> tuple[str, Optional[str]]:
    """
    Story 2.10 AC-3: Retrieve learning memories.

    Queries for Tips, error records, and key Q&A related to the node.
    Total output limited to max_tokens.

    ⛔ P1-03 (Codex 对抗审查 2026-08-19) 两处改动:

    1. **返回值加降级信号**。此前无论「检索失败」还是「真的没有记忆」都返回 ""，
       调用方无法区分 —— 正是那个 .search() AttributeError 潜伏三个月的机制。
       现在返回 (text, degraded_reason)，成功时 reason 为 None。

    2. **检索路径改走 MemoryService**。原实现拼伪 key 串 `learning node:{id}`
       调 GraphitiClient.search_memories，而图上 node 身份只存在于
       uuid5(node_id:group_id) 与边的 attributes 里、fact 文本中没有它；
       且读侧只查主组而写侧落在 `__semantic` 影子组 —— 没有任何字符串形态
       能命中。详见 _search_via_memory_service 的 docstring。

    Args:
        node_id: 节点身份提示词。注意按新范式它只作为**语义线索**参与检索，
                 不是可精确匹配的 key，因此传 canvas_file 也能工作（只是线索
                 内容不同）。
        max_tokens: Max token budget for memories.
        graphiti_client: 降级路径用的 Graphiti 客户端（MemoryService 不可用时）。
        group_id: ⛔ 强烈建议传入。缺省时 MemoryService 会**跨 vault 全组检索**。

    Returns:
        (formatted_text, degraded_reason)。degraded_reason 为 None 表示检索
        正常完成（此时空串 = 确实没有记忆）；非 None 表示检索未能正常完成。
    """
    memories: Optional[List[dict]] = None

    try:
        memories = await asyncio.wait_for(
            _search_via_memory_service(node_id, group_id),
            timeout=5.0,
        )
    except asyncio.TimeoutError:
        logger.warning("[MEMORY] MemoryService 检索超时 (5s), 尝试降级路径")
        memories = None
    except Exception as exc:  # noqa: BLE001
        logger.warning("[MEMORY] MemoryService 检索异常, 尝试降级路径: %s", exc)
        memories = None

    if memories is None:
        # 降级路径: 直连 Graphiti。召回面窄（单组），但聊胜于无。
        if not graphiti_client:
            logger.error(
                "[MEMORY] MemoryService 与 Graphiti 客户端均不可用 —— 学习记忆注入为空，这**不等于**该节点没有记忆"
            )
            return "", MEMORY_DEGRADED_NO_CLIENT
        try:
            # ⛔ 方法名契约 (2026-08-15 修复): 必须是 search_memories，不是 search。
            # GraphitiClient 只暴露 search_nodes / search_memories；调用 .search()
            # 会抛 AttributeError 并被吞成静默空串。
            memories = await asyncio.wait_for(
                graphiti_client.search_memories(f"{node_id} 学习 提示 错误", num_results=10),
                timeout=3.0,
            )
        except asyncio.TimeoutError:
            logger.error("[MEMORY] 降级路径也超时 (3s) — 返回 degraded 而非静默空串")
            return "", MEMORY_DEGRADED_TIMEOUT
        except Exception as exc:  # noqa: BLE001
            logger.error("[MEMORY] 降级路径失败: %s — 返回 degraded 而非静默空串", exc)
            return "", MEMORY_DEGRADED_ERROR

    try:
        if not memories:
            # 检索本身成功, 只是没有命中 —— 这是「真的没有记忆」, reason=None
            return "", None

        tips_parts: List[str] = []
        error_parts: List[str] = []
        qa_parts: List[str] = []

        for mem in memories:
            content = ""
            if isinstance(mem, dict):
                content = mem.get("content", "") or mem.get("fact", "")
            elif hasattr(mem, "content"):
                content = mem.content or ""
            elif hasattr(mem, "fact"):
                content = mem.fact or ""

            if not content:
                continue

            content_lower = content.lower()
            if "tip" in content_lower or "提示" in content_lower:
                tips_parts.append(content[:200])
            elif "错误" in content_lower or "error" in content_lower or "mistake" in content_lower:
                error_parts.append(content[:200])
            else:
                qa_parts.append(content[:200])

        # Build formatted output
        sections: List[str] = []
        if tips_parts:
            tips_text = "\n".join(f"  {i + 1}. {t}" for i, t in enumerate(tips_parts[:3]))
            sections.append(f"[历史 Tips]\n{tips_text}")
        if error_parts:
            errors_text = "\n".join(f"  - {e}" for e in error_parts[:3])
            sections.append(f"[历史错误]\n{errors_text}")
        if qa_parts:
            qa_text = "\n".join(f"  - {q}" for q in qa_parts[:3])
            sections.append(f"[相关问答]\n{qa_text}")

        if not sections:
            # 有条目但全被内容过滤掉 —— 仍属「检索成功、无可用记忆」
            return "", None

        result = "\n".join(sections)

        # Token truncation
        from agentic_rag.compression import _count_tokens_approx

        while _count_tokens_approx(result) > max_tokens and sections:
            sections.pop()
            result = "\n".join(sections)

        return result, None

    except asyncio.TimeoutError:
        # P1-03: 升 warning → error, 且返回 degraded 而非静默空串
        logger.error("[MEMORY] 学习记忆格式化阶段超时 — 返回 degraded")
        return "", MEMORY_DEGRADED_TIMEOUT
    except Exception as e:
        logger.error("[MEMORY] 学习记忆格式化失败: %s — 返回 degraded 而非静默空串", e)
        return "", MEMORY_DEGRADED_ERROR


# =========================================================================
# Multi-Query + Decomposition Rewrite (AC-5)
# =========================================================================


def _classify_query_complexity(query: str) -> str:
    """
    Classify query complexity for rewrite strategy selection.

    Returns: "simple", "medium", or "complex".
    """
    # Simple: short, single concept
    if len(query) < 20 and not any(w in query for w in ["和", "以及", "同时", "如何", "为什么", "and", "how"]):
        return "simple"

    # Complex: contains conjunctions or multi-part structure
    complex_markers = [
        "和",
        "以及",
        "同时",
        "另外",
        "还有",
        "如何.*同时",
        "比较.*区别",
        "and",
        "also",
        "compare",
        "difference",
    ]
    for marker in complex_markers:
        if re.search(marker, query, re.IGNORECASE):
            return "complex"

    return "medium"


def _build_rewrite_prompt(query: str, complexity: str) -> str:
    """Build the rewrite prompt using PromptRegistry template with inline fallback.

    Story 2.13 Task 1.1: Externalized prompt loaded via PromptRegistry.
    Loads the full template content (including quality requirements) and
    selects the appropriate strategy section based on query complexity.
    Falls back to inline prompt if PromptRegistry unavailable (e.g. standalone usage).
    """
    try:
        from app.services.prompt_registry import get_prompt_registry

        registry = get_prompt_registry()
        template_content = registry.get("query_rewrite")

        if not template_content or not template_content.strip():
            logger.warning(
                "[Story 2.13] PromptRegistry returned empty content for 'query_rewrite', using inline fallback"
            )
            raise ValueError("Empty template content")

        # Use full template with placeholder replacement.
        # Select the relevant strategy section but keep quality requirements.
        if complexity == "medium":
            # Strategy 1: Multi-Query rewrite
            # Extract from start through Strategy 1 + quality requirements,
            # skip Strategy 2 body
            section2_marker = "## 策略二"
            quality_marker = "## 质量要求"
            idx_s2 = template_content.find(section2_marker)
            idx_quality = template_content.find(quality_marker)

            if idx_s2 >= 0 and idx_quality >= 0:
                # Keep everything before Strategy 2 + quality requirements section
                prompt = template_content[:idx_s2].rstrip() + "\n\n" + template_content[idx_quality:]
            else:
                # If markers not found, use full template
                prompt = template_content
        else:
            # Strategy 2: Decomposition
            # Extract Strategy 2 section + quality requirements
            section2_marker = "## 策略二"
            quality_marker = "## 质量要求"
            idx_s2 = template_content.find(section2_marker)
            idx_quality = template_content.find(quality_marker)

            if idx_s2 >= 0 and idx_quality >= 0:
                # Keep header + Strategy 2 + quality requirements
                # Find the header (everything before Strategy 1)
                section1_marker = "## 策略一"
                idx_s1 = template_content.find(section1_marker)
                header = template_content[:idx_s1].rstrip() if idx_s1 >= 0 else ""
                prompt = (
                    header
                    + "\n\n"
                    + template_content[idx_s2:idx_quality].rstrip()
                    + "\n\n"
                    + template_content[idx_quality:]
                )
            else:
                prompt = template_content

        # Replace {{query}} placeholder with actual query
        prompt = prompt.replace("{{query}}", query)
        return prompt

    except Exception as e:
        # Fallback: use inline prompt when PromptRegistry is not available
        logger.warning(
            "[Story 2.13] Failed to load 'query_rewrite' via PromptRegistry: %s. Using inline fallback.",
            e,
        )
        if complexity == "medium":
            return f"请从不同角度改写以下查询，生成2-3个等价查询。每行一个查询，不要编号，不要解释。\n原始查询：{query}"
        else:
            return f"请将以下复杂查询拆分为2-3个独立的子问题。每行一个子问题，不要编号，不要解释。\n原始查询：{query}"


async def multi_query_rewrite(
    query: str,
    model: str = "gemini/gemini-2.0-flash",
    enabled: bool = True,
) -> List[str]:
    """
    Story 2.10 AC-5: Multi-Query + Decomposition rewrite.

    Strategy:
    - Simple query (< 20 chars, no conjunctions): no rewrite
    - Medium: Multi-Query (2-3 rephrased queries)
    - Complex (conjunctions, multi-part): Decomposition (sub-questions)

    3-second timeout, fallback to original query.

    Args:
        query: Original user query.
        model: LLM model for rewriting.
        enabled: Whether rewriting is enabled.

    Returns:
        List of queries (always includes original).
    """
    if not enabled:
        return [query]

    complexity = _classify_query_complexity(query)
    if complexity == "simple":
        return [query]

    try:
        import litellm

        litellm.set_verbose = False
    except ImportError:
        logger.warning("[MULTI-QUERY] litellm not installed, skipping rewrite")
        return [query]

    # Story 2.13: Load prompt template via PromptRegistry
    prompt = _build_rewrite_prompt(query, complexity)

    try:
        response = await asyncio.wait_for(
            litellm.acompletion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.5,
            ),
            timeout=3.0,
        )

        raw = response.choices[0].message.content.strip()
        lines = [line.strip() for line in raw.split("\n") if line.strip()]

        # Always include original query first
        queries = [query]
        for line in lines:
            # Remove numbering if present
            cleaned = re.sub(r"^\d+[\.\)]\s*", "", line).strip()
            if cleaned and cleaned != query and len(cleaned) > 3:
                queries.append(cleaned)

        # Cap at 4 total queries
        queries = queries[:4]

        logger.info(
            f"[MULTI-QUERY] complexity={complexity}, original='{query[:40]}', generated {len(queries) - 1} variants"
        )
        return queries

    except asyncio.TimeoutError:
        logger.warning("[MULTI-QUERY] LLM rewrite timed out (3s), using original query")
        return [query]
    except Exception as e:
        logger.warning(f"[MULTI-QUERY] Rewrite failed: {e}, using original query")
        return [query]
