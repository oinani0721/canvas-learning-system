"""
Learning Context Service - Tier 1/2 context assembly for Claude CLI injection.

Story 3.4: Learning Context Auto-Injection
- AC-1: Assemble node context for --append-system-prompt
- AC-2: Three-tier context management (Tier 1 full, Tier 2 summary, Tier 3 on-demand)
- AC-4: Dynamic update (re-assemble each call, no stale frontend cache)

Data sources:
- MasteryStore (Neo4j EntityNode): p_mastery, fsrs_stability, next_review
- MemoryService (in-memory _episodes): tips (learning_tip) and errors (misconception)
- Neo4jClient (Cypher): edge reasons, 1-hop neighbor summaries

[Source: _bmad-output/implementation-artifacts/3-4-learning-context-auto-injection.md]
"""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Token budget: Tier 1 + Tier 2 combined must stay under 4K tokens.
# Conservative estimate: 1 token ~ 2 chars for mixed Chinese/English.
MAX_TOTAL_TOKENS = 4000
CHARS_PER_TOKEN = 2
MAX_TOTAL_CHARS = MAX_TOTAL_TOKENS * CHARS_PER_TOKEN  # 8000 chars
TIER1_CHAR_BUDGET = 6000  # ~3K tokens
TIER2_CHAR_BUDGET = 2000  # ~1K tokens

# Limits for data fetching
MAX_TIPS = 20
MAX_ERRORS = 10
MAX_NEIGHBORS = 10


def _estimate_tokens(text: str) -> int:
    """Estimate token count for mixed Chinese/English text."""
    return len(text) // CHARS_PER_TOKEN


# ═══════════════════════════════════════════════════════════════════════════════
# Data Containers (plain dicts to avoid circular imports with endpoint models)
# ═══════════════════════════════════════════════════════════════════════════════


def _empty_context(node_id: str) -> dict:
    """Return a minimal context dict for a node with no learning history."""
    return {
        "node_id": node_id,
        "node_name": node_id,
        "tier1": {
            "node_name": node_id,
            "mastery": {"p_mastery": None, "stability": None, "next_review": None},
            "tips": [],
            "errors": [],
            "edge_reasons": [],
        },
        "tier2": {"neighbors": []},
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Tier 1 Assembly
# ═══════════════════════════════════════════════════════════════════════════════


async def _fetch_mastery(node_id: str, group_id: str) -> dict:
    """Fetch mastery data from MasteryStore via Neo4j EntityNode.

    Returns dict with keys: node_name, p_mastery, stability, next_review.
    Degrades gracefully: returns defaults if MasteryStore unavailable.
    """
    result = {
        "node_name": node_id,
        "p_mastery": None,
        "stability": None,
        "next_review": None,
    }
    try:
        from app.clients.neo4j_client import get_neo4j_client
        from app.services.mastery_store import MasteryStore

        neo4j = get_neo4j_client()
        store = MasteryStore(neo4j)
        concept = await store.get_concept(concept_id=node_id, group_id=group_id)
        if concept is not None:
            result["node_name"] = concept.name or concept.topic or node_id
            result["p_mastery"] = concept.p_mastery
            result["stability"] = concept.fsrs_stability
            # Format next review from last_interaction_ts + stability if available
            if concept.last_interaction_ts and concept.fsrs_stability > 0:
                from datetime import timedelta

                next_dt = concept.last_interaction_ts + timedelta(days=concept.fsrs_stability)
                result["next_review"] = next_dt.isoformat()
        else:
            # Fallback: try to get node name from Neo4j directly
            try:
                records = await neo4j.run_query(
                    "MATCH (n:EntityNode) "
                    "WHERE n.mastery_concept_id = $cid OR n.name = $cid "
                    "RETURN n.name AS name LIMIT 1",
                    cid=node_id,
                )
                if records:
                    result["node_name"] = records[0].get("name") or node_id
            except Exception:
                pass
    except Exception as e:
        logger.warning("Failed to fetch mastery for %s: %s", node_id, e)
    return result


async def _fetch_tips_and_errors(node_id: str) -> tuple[list[dict], list[dict]]:
    """Fetch tips and error records from MemoryService episodes.

    Tips are episodes with episode_type="learning_tip" and matching node_id.
    Errors are episodes with episode_type="misconception" and matching node_id.

    Returns (tips_list, errors_list) of dicts.
    """
    tips: list[dict] = []
    errors: list[dict] = []

    try:
        from app.services.memory_service import get_memory_service

        memory_svc = await get_memory_service()

        # Use public search_memories() API instead of accessing private _episodes
        episodes = await memory_svc.search_memories(
            query=node_id,
            max_results=MAX_TIPS + MAX_ERRORS,
        )
        for episode in episodes:
            ep_node_id = episode.get("node_id") or episode.get("metadata", {}).get("node_id", "")
            if ep_node_id != node_id:
                continue

            ep_type = episode.get("episode_type", "")
            content = episode.get("content", "")
            meta = episode.get("metadata", {})
            timestamp = episode.get("timestamp", "")

            if ep_type == "learning_tip" and len(tips) < MAX_TIPS:
                tips.append(
                    {
                        "content": meta.get("content") or content,
                        "category": (", ".join(meta["tags"]) if meta.get("tags") else "general"),
                        "annotated_at": meta.get("created_at") or timestamp,
                    }
                )
            elif ep_type == "misconception" and len(errors) < MAX_ERRORS:
                errors.append(
                    {
                        "error_type": meta.get("error_type", "misconception"),
                        "description": meta.get("description") or content,
                        "remedy": meta.get("remedy", ""),
                    }
                )
    except Exception as e:
        logger.warning("Failed to fetch tips/errors for %s: %s", node_id, e)

    # Also try LearningMemoryClient as secondary source
    try:
        from app.clients.graphiti_client import get_learning_memory_client

        lm_client = get_learning_memory_client()
        memories = await lm_client.search_memories(node_id=node_id, limit=MAX_TIPS)
        for mem in memories:
            # Avoid duplicates: skip if content already in tips
            existing_contents = {t["content"] for t in tips}
            mem_content = mem.get("user_understanding") or mem.get("concept", "")
            if mem_content and mem_content not in existing_contents and len(tips) < MAX_TIPS:
                tips.append(
                    {
                        "content": mem_content,
                        "category": "learning_memory",
                        "annotated_at": mem.get("timestamp", ""),
                    }
                )
    except Exception as e:
        logger.debug("LearningMemoryClient unavailable for %s: %s", node_id, e)

    return tips, errors


async def _fetch_edge_reasons(node_id: str) -> list[dict]:
    """Fetch edge reasons (relationships from/to this node) from Neo4j.

    Returns list of dicts with keys: neighbor_name, reason.
    """
    reasons: list[dict] = []
    try:
        from app.clients.neo4j_client import get_neo4j_client

        client = get_neo4j_client()
        records = await client.run_query(
            "MATCH (n:EntityNode)-[r]-(m:EntityNode) "
            "WHERE n.mastery_concept_id = $cid OR n.name = $cid "
            "RETURN m.name AS neighbor, r.reason AS reason, "
            "r.label AS label "
            "LIMIT $lim",
            cid=node_id,
            lim=MAX_NEIGHBORS,
        )
        for rec in records or []:
            neighbor = rec.get("neighbor")
            if neighbor:
                reasons.append(
                    {
                        "neighbor_name": neighbor,
                        "reason": rec.get("reason") or rec.get("label") or "",
                    }
                )
    except Exception as e:
        logger.warning("Failed to fetch edge reasons for %s: %s", node_id, e)
    return reasons


async def assemble_tier1(node_id: str, group_id: str) -> dict:
    """Assemble Tier 1: full context for the current node.

    AC-2 Tier 1: All tips + all errors + mastery + edge reasons.
    """
    mastery_data = await _fetch_mastery(node_id, group_id)
    tips, errors = await _fetch_tips_and_errors(node_id)
    edge_reasons = await _fetch_edge_reasons(node_id)

    return {
        "node_name": mastery_data["node_name"],
        "mastery": {
            "p_mastery": mastery_data["p_mastery"],
            "stability": mastery_data["stability"],
            "next_review": mastery_data["next_review"],
        },
        "tips": tips,
        "errors": errors,
        "edge_reasons": edge_reasons,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Tier 2 Assembly
# ═══════════════════════════════════════════════════════════════════════════════


async def assemble_tier2(node_id: str) -> dict:
    """Assemble Tier 2: 1-hop neighbor summaries.

    AC-2 Tier 2: Neighbor title + mastery level + edge reason.
    """
    neighbors: list[dict] = []
    try:
        from app.clients.neo4j_client import get_neo4j_client

        client = get_neo4j_client()
        records = await client.run_query(
            "MATCH (n:EntityNode)-[r]-(m:EntityNode) "
            "WHERE n.mastery_concept_id = $cid OR n.name = $cid "
            "RETURN m.name AS name, m.p_mastery AS mastery, "
            "m.effective_proficiency AS eff_prof, "
            "r.reason AS reason, r.label AS label "
            "LIMIT $lim",
            cid=node_id,
            lim=MAX_NEIGHBORS,
        )
        for rec in records or []:
            name = rec.get("name")
            if name:
                neighbors.append(
                    {
                        "name": name,
                        "mastery_level": rec.get("mastery") or rec.get("eff_prof"),
                        "edge_reason": rec.get("reason") or rec.get("label") or "",
                    }
                )
    except Exception as e:
        logger.warning("Failed to fetch neighbors for %s: %s", node_id, e)

    return {"neighbors": neighbors}


# ═══════════════════════════════════════════════════════════════════════════════
# Full Context Assembly
# ═══════════════════════════════════════════════════════════════════════════════


async def get_node_context(
    node_id: str,
    group_id: Optional[str] = None,
) -> dict:
    """Assemble full learning context (Tier 1 + Tier 2) for a node.

    AC-1: Structured for --append-system-prompt injection.
    AC-2: Tier 1 full + Tier 2 summary.
    AC-4: Called fresh each time (no stale cache in service layer;
           endpoint layer handles 30s TTL cache).

    Optimization: Tier 1 edge_reasons and Tier 2 neighbors share the same
    Neo4j neighbor query, so we fetch once and reuse.

    Args:
        node_id: Canvas node identifier.
        group_id: Subject isolation namespace.  Falls back to DEFAULT_GROUP_ID.

    Returns:
        Dict matching ContextResponse schema.
    """
    if group_id is None:
        from app.config import DEFAULT_GROUP_ID

        group_id = DEFAULT_GROUP_ID

    # Fetch mastery, tips/errors, and neighbors in parallel.
    # Reuse the same neighbor query for both Tier 1 edge_reasons and Tier 2 neighbors
    # to avoid duplicate Neo4j queries.
    mastery_data = await _fetch_mastery(node_id, group_id)
    tips, errors = await _fetch_tips_and_errors(node_id)

    # Single neighbor query for both tiers
    neighbor_records = await _fetch_neighbor_records(node_id)

    # Tier 1: edge reasons extracted from neighbor records
    edge_reasons = [
        {"neighbor_name": rec["name"], "reason": rec.get("reason") or rec.get("label") or ""}
        for rec in neighbor_records
        if rec.get("name")
    ]

    tier1 = {
        "node_name": mastery_data["node_name"],
        "mastery": {
            "p_mastery": mastery_data["p_mastery"],
            "stability": mastery_data["stability"],
            "next_review": mastery_data["next_review"],
        },
        "tips": tips,
        "errors": errors,
        "edge_reasons": edge_reasons,
    }

    # Tier 2: neighbor summaries from same query
    neighbors = [
        {
            "name": rec["name"],
            "mastery_level": rec.get("mastery") or rec.get("eff_prof"),
            "edge_reason": rec.get("reason") or rec.get("label") or "",
        }
        for rec in neighbor_records
        if rec.get("name")
    ]
    tier2 = {"neighbors": neighbors}

    return {
        "node_id": node_id,
        "node_name": tier1["node_name"],
        "tier1": tier1,
        "tier2": tier2,
    }


async def _fetch_neighbor_records(node_id: str) -> list[dict]:
    """Fetch neighbor records from Neo4j (shared by Tier 1 and Tier 2).

    Returns raw dicts with keys: name, mastery, eff_prof, reason, label.
    """
    records_out: list[dict] = []
    try:
        from app.clients.neo4j_client import get_neo4j_client

        client = get_neo4j_client()
        records = await client.run_query(
            "MATCH (n:EntityNode)-[r]-(m:EntityNode) "
            "WHERE n.mastery_concept_id = $cid OR n.name = $cid "
            "RETURN m.name AS name, m.p_mastery AS mastery, "
            "m.effective_proficiency AS eff_prof, "
            "r.reason AS reason, r.label AS label "
            "LIMIT $lim",
            cid=node_id,
            lim=MAX_NEIGHBORS,
        )
        for rec in records or []:
            records_out.append(dict(rec))
    except Exception as e:
        logger.warning("Failed to fetch neighbors for %s: %s", node_id, e)
    return records_out


# ═══════════════════════════════════════════════════════════════════════════════
# Markdown Formatting (for --append-system-prompt)
# ═══════════════════════════════════════════════════════════════════════════════


def format_as_markdown(ctx: dict) -> str:
    """Convert a ContextResponse dict to structured Markdown for system prompt.

    AC-1: Markdown format Agent can parse.
    AC-2: Token budget < 4K tokens — truncates Tier 2 first, then Tier 1 tips.

    Omits empty sections (spec: "新节点无历史时不注入空 section").

    Args:
        ctx: ContextResponse dict from get_node_context().

    Returns:
        Markdown string ready for --append-system-prompt.
    """
    tier1 = ctx.get("tier1", {})
    tier2 = ctx.get("tier2", {})
    sections: list[str] = []

    # Header
    node_name = tier1.get("node_name") or ctx.get("node_name", "Unknown")
    sections.append(f"## 当前节点：{node_name}")

    # Mastery section
    mastery = tier1.get("mastery", {})
    mastery_lines: list[str] = []
    if mastery.get("p_mastery") is not None:
        mastery_lines.append(f"- BKT掌握概率: {mastery['p_mastery']:.2f}")
    if mastery.get("stability") is not None:
        mastery_lines.append(f"- FSRS记忆稳定性: {mastery['stability']:.1f}")
    if mastery.get("next_review"):
        # Format date nicely
        try:
            dt = datetime.fromisoformat(mastery["next_review"])
            mastery_lines.append(f"- 下次复习: {dt.strftime('%Y-%m-%d')}")
        except (ValueError, TypeError):
            mastery_lines.append(f"- 下次复习: {mastery['next_review']}")
    if mastery_lines:
        sections.append("### 精通度\n" + "\n".join(mastery_lines))

    # Tips section
    tips = tier1.get("tips", [])
    if tips:
        tip_lines = [f"- {t.get('content', '')}" for t in tips if t.get("content")]
        if tip_lines:
            sections.append("### 关键笔记 (Tips)\n" + "\n".join(tip_lines))

    # Errors section
    errors = tier1.get("errors", [])
    if errors:
        error_lines = []
        for e in errors:
            desc = e.get("description", "")
            etype = e.get("error_type", "error")
            remedy = e.get("remedy", "")
            line = f"- [{etype}] {desc}"
            if remedy:
                line += f" → 建议: {remedy}"
            error_lines.append(line)
        if error_lines:
            sections.append("### 历史错误\n" + "\n".join(error_lines))

    # Edge reasons (part of Tier 1)
    edge_reasons = tier1.get("edge_reasons", [])
    if edge_reasons:
        reason_lines = [
            f"- {er.get('neighbor_name', '?')}: {er.get('reason', '')}"
            for er in edge_reasons
            if er.get("neighbor_name")
        ]
        if reason_lines:
            sections.append("### 连线关系\n" + "\n".join(reason_lines))

    # Tier 2: Neighbors
    neighbors = tier2.get("neighbors", [])
    if neighbors:
        neighbor_lines = []
        for nb in neighbors:
            name = nb.get("name", "?")
            reason = nb.get("edge_reason", "")
            mastery_val = nb.get("mastery_level")
            line = f"- {name}"
            if reason:
                line += f": {reason}"
            if mastery_val is not None:
                line += f" (精通度: {mastery_val:.2f})"
            neighbor_lines.append(line)
        if neighbor_lines:
            sections.append("### 相关节点\n" + "\n".join(neighbor_lines))

    full_text = "\n\n".join(sections)

    # Token budget enforcement
    estimated_tokens = _estimate_tokens(full_text)
    if estimated_tokens > MAX_TOTAL_TOKENS:
        full_text = _truncate_to_budget(sections, MAX_TOTAL_CHARS)

    return full_text


def _truncate_to_budget(sections: list[str], max_chars: int) -> str:
    """Truncate sections to fit within character budget.

    Priority: keep header + mastery, then tips, then errors, then neighbors.
    Truncates from the end (neighbors first, then errors, then tips).
    When cutting within a section, truncates at the nearest sentence boundary
    (。！？.!?) to avoid mid-sentence breaks.
    """
    result = "\n\n".join(sections)
    if len(result) <= max_chars:
        return result

    # Try removing sections from the end until within budget
    while len(sections) > 1 and len("\n\n".join(sections)) > max_chars:
        sections.pop()

    result = "\n\n".join(sections)

    # If still over budget, truncate the last section at a sentence boundary
    if len(result) > max_chars:
        # Find the last sentence-ending punctuation before the limit
        truncated = result[:max_chars]
        # Look for Chinese/English sentence boundaries
        last_sentence_end = -1
        for i in range(len(truncated) - 1, max(0, len(truncated) - 200), -1):
            if truncated[i] in "。！？.!?\n":
                last_sentence_end = i + 1
                break
        if last_sentence_end > max_chars // 2:
            # Found a reasonable sentence boundary in the latter half
            result = truncated[:last_sentence_end] + "\n\n[...上下文因长度限制被截断]"
        else:
            # No good sentence boundary found, hard truncate
            result = truncated + "\n\n[...上下文因长度限制被截断]"

    return result
