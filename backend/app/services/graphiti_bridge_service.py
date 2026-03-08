# Canvas Learning System - Graphiti Bridge Service
# Bridges Canvas plugin learning events → Claude Code-compatible Graphiti records
"""
Graphiti Bridge Service

Synchronizes learning records between Canvas plugin and Claude Code by writing
entity-typed nodes to Neo4j that Claude Code's Graphiti MCP can search.

Architecture:
  Canvas plugin (color change / agent feedback)
    → MemoryService.record_learning_event()
    → GraphitiBridgeService.bridge_to_claude_format()
    → Neo4j :EntityNode with entity_type property
    → Claude Code: mcp__graphiti-cs188__search_nodes() finds these records

Entity Types (aligned with CS188 CLAUDE.md):
  - Misconception: 知识点不理解
  - ProblemTrap: 做题思维误区
  - GuidedThinking: 引导思考记录

Classification Priority:
  1. Group label keyword matching (most reliable — reads canvas JSON, finds
     the smallest enclosing group, matches label keywords)
  2. Color mapping fallback (Canvas color "4"=Red → Misconception,
     "3"=Purple → Misconception)
  3. None → skip bridging

Color Reference (canvas_utils.py authoritative, plugin CSS remapped):
  1=Gray, 2=Green, 3=Purple, 4=Red, 5=Blue, 6=Yellow
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.memory_format import (
    ENTITY_TYPES,
    build_entity_name,
    build_episode_body,
    classify_entity_type as _classify_entity_type_unified,
    get_source_description,
)

logger = logging.getLogger(__name__)


# Obsidian Canvas color code → entity type mapping
# Authoritative color reference: canvas_utils.py (plugin CSS remapped)
# "4"=Red(不理解), "3"=Purple(似懂非懂), "6"=Yellow(个人理解), "2"=Green(已掌握)
CANVAS_COLOR_TO_ENTITY_TYPE: Dict[str, str] = {
    "4": "Misconception",  # Red = 不理解 → 知识点误解
    "3": "Misconception",  # Purple = 似懂非懂 → 部分误解
    # "6" (Yellow/个人理解) → 不自动录入，等评分后由 agent 决定
    # "2" (Green/已掌握) → 不录入
}

# Reverse mapping for querying
ENTITY_TYPE_TO_COLOR: Dict[str, str] = {v: k for k, v in CANVAS_COLOR_TO_ENTITY_TYPE.items()}


class GraphitiBridgeService:
    """
    Bridges Canvas learning events into Claude Code-compatible Graphiti format.

    Writes :EntityNode labels to Neo4j with structured episode_body matching
    the format that Claude Code's mcp__graphiti-cs188__search_nodes expects.
    """

    def __init__(self, neo4j_client, canvas_base_path: Optional[str] = None):
        """
        Args:
            neo4j_client: Neo4jClient instance (injected)
            canvas_base_path: Base path for resolving canvas files (for group label lookup)
        """
        self._neo4j = neo4j_client
        self._canvas_base_path = canvas_base_path
        self._bridge_count = 0

    async def bridge_to_claude_format(
        self,
        concept: str,
        canvas_path: str,
        node_id: str,
        node_color: Optional[str] = None,
        node_text: Optional[str] = None,
        agent_feedback: Optional[str] = None,
        score: Optional[float] = None,
        group_id: str = "cs188",
        topic: Optional[str] = None,
    ) -> bool:
        """
        Write a learning event as a Claude Code-compatible entity node.

        Creates a :EntityNode in Neo4j with entity_type, name, and episode_body
        fields that match the format used by Claude Code's Graphiti MCP.

        Args:
            concept: Concept name (e.g., "A* 搜索最优性")
            canvas_path: Canvas file path
            node_id: Canvas node ID
            node_color: Canvas color code ("4"=Red/不理解, "3"=Purple/似懂非懂)
            node_text: Full text content of the canvas node
            agent_feedback: AI agent feedback/explanation
            score: Understanding score (0-100)
            group_id: Graphiti group_id (default: "cs188")
            topic: Topic category (e.g., "Search", "MDPs")

        Returns:
            True if successfully written
        """
        # Resolve group label for better entity type classification
        group_label = None
        if self._canvas_base_path:
            try:
                group_label = await _resolve_node_group_label(
                    self._canvas_base_path, canvas_path, node_id
                )
            except Exception as e:
                logger.debug(f"Group label resolution failed: {e}")

        entity_type = classify_entity_type(node_color, score, agent_feedback, group_label=group_label)

        if entity_type is None:
            logger.debug(f"Node {node_id} color={node_color} not mapped to entity type, skipping bridge")
            return False

        # Build Claude Code-compatible name
        name = f"{entity_type}: {concept}"

        # Build structured episode_body matching CLAUDE.md format
        episode_body = _build_episode_body(
            entity_type=entity_type,
            topic=topic,
            concept=concept,
            node_text=node_text,
            agent_feedback=agent_feedback,
            score=score,
            canvas_path=canvas_path,
        )

        try:
            cypher = """
            MERGE (n:EntityNode {node_id: $nodeId, group_id: $groupId})
            ON CREATE SET
                n.name = $name,
                n.entity_type = $entityType,
                n.episode_body = $episodeBody,
                n.text = $episodeBody,
                n.canvas_path = $canvasPath,
                n.concept = $concept,
                n.source = 'canvas_plugin',
                n.source_description = $sourceDesc,
                n.created_at = $timestamp,
                n.updated_at = $timestamp
            ON MATCH SET
                n.name = $name,
                n.entity_type = $entityType,
                n.episode_body = $episodeBody,
                n.text = $episodeBody,
                n.agent_feedback = $agentFeedback,
                n.score = $score,
                n.updated_at = $timestamp
            """

            source_desc = f"{entity_type.lower()}-record"
            timestamp = datetime.now().isoformat()

            await self._neo4j.run_query(
                cypher,
                nodeId=f"canvas-{node_id}",
                groupId=group_id,
                name=name,
                entityType=entity_type,
                episodeBody=episode_body,
                canvasPath=canvas_path,
                concept=concept,
                sourceDesc=source_desc,
                agentFeedback=agent_feedback or "",
                score=score,
                timestamp=timestamp,
            )

            self._bridge_count += 1
            logger.info(f"Bridged to Claude format: {name} (group={group_id})")
            return True

        except Exception as e:
            logger.error(f"Failed to bridge learning event: {e}")
            return False

    async def search_claude_records(
        self,
        query: str,
        group_id: str = "cs188",
        entity_types: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search for entity-typed records (written by either Canvas or Claude Code).

        Args:
            query: Search query
            group_id: Graphiti group_id
            entity_types: Filter by entity types (e.g., ["Misconception", "ProblemTrap"])
            limit: Max results

        Returns:
            List of matching records
        """
        where_parts = ["n.group_id = $groupId"]
        params: Dict[str, Any] = {"groupId": group_id, "query": query, "limit": limit}

        if entity_types:
            where_parts.append("n.entity_type IN $entityTypes")
            params["entityTypes"] = entity_types

        where_clause = " AND ".join(where_parts)

        cypher = f"""
        MATCH (n)
        WHERE {where_clause}
          AND (n.text CONTAINS $query OR n.name CONTAINS $query
               OR n.episode_body CONTAINS $query OR n.concept CONTAINS $query)
        RETURN n.node_id as node_id, n.name as name, n.entity_type as entity_type,
               n.episode_body as episode_body, n.concept as concept,
               n.canvas_path as canvas_path, n.source as source,
               n.score as score, n.created_at as created_at
        ORDER BY n.updated_at DESC
        LIMIT $limit
        """

        try:
            results = await self._neo4j.run_query(cypher, **params)
            return results
        except Exception as e:
            logger.error(f"Failed to search Claude records: {e}")
            return []

    @property
    def stats(self) -> Dict[str, Any]:
        return {"bridge_count": self._bridge_count}


def classify_entity_type(
    node_color: Optional[str],
    score: Optional[float],
    agent_feedback: Optional[str],
    group_label: Optional[str] = None,
) -> Optional[str]:
    """
    Classify a learning event into a Claude Code-compatible entity type.

    Delegates to memory_format.classify_entity_type for unified logic.
    Priority: group label keywords → text keywords → color mapping.
    """
    # Use agent_feedback as text signal for keyword matching
    text = agent_feedback or ""
    return _classify_entity_type_unified(
        text=text, color=node_color, group_label=group_label
    )


async def _resolve_node_group_label(
    canvas_base_path: Optional[str],
    canvas_path: str,
    node_id: str
) -> Optional[str]:
    """
    Read canvas JSON, find which group contains the target node by bounding box.

    Returns the group's label or None.
    """
    if not canvas_base_path:
        return None

    import os
    # Try multiple path resolutions
    full_path = None
    candidates = [
        os.path.join(canvas_base_path, canvas_path),
        os.path.join(canvas_base_path, f"{canvas_path}.canvas") if not canvas_path.endswith('.canvas') else None,
        canvas_path,  # absolute path
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            full_path = c
            break

    if not full_path:
        return None

    try:
        content = await asyncio.to_thread(_read_json_file, full_path)
        if not content:
            return None

        nodes = content.get("nodes", [])

        # Find target node position
        target = None
        for n in nodes:
            if n.get("id") == node_id:
                target = n
                break

        if not target:
            return None

        tx, ty = target.get("x", 0), target.get("y", 0)

        # Find groups containing this node (by bounding box)
        matching_groups = []
        for n in nodes:
            if n.get("type") != "group":
                continue
            gx = n.get("x", 0)
            gy = n.get("y", 0)
            gw = n.get("width", 0)
            gh = n.get("height", 0)

            if gx <= tx <= gx + gw and gy <= ty <= gy + gh:
                area = gw * gh
                matching_groups.append((area, n.get("label", "")))

        if not matching_groups:
            return None

        # Take smallest area (most specific group)
        matching_groups.sort(key=lambda x: x[0])
        return matching_groups[0][1] or None

    except Exception as e:
        logger.debug(f"Failed to resolve group label for node {node_id}: {e}")
        return None


def _read_json_file(path: str) -> Optional[dict]:
    """Sync helper to read JSON file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def _build_episode_body(
    entity_type: str,
    topic: Optional[str],
    concept: str,
    node_text: Optional[str],
    agent_feedback: Optional[str],
    score: Optional[float],
    canvas_path: str,
) -> str:
    """
    Build episode_body using unified memory_format templates.

    Delegates to memory_format.build_episode_body for consistent formatting
    across Canvas backend and Claude Code MCP.
    """
    topic_str = topic or "Unknown"
    source = f"canvas:{canvas_path}"
    content = node_text or concept
    feedback = agent_feedback or "待AI分析"

    if entity_type == "Misconception":
        return build_episode_body(
            "Misconception", topic=topic_str, error=content,
            correct=feedback, source=source,
        )
    elif entity_type == "ProblemTrap":
        return build_episode_body(
            "ProblemTrap", topic=topic_str, problem=concept,
            wrong=content, correct=feedback, insight="", source=source,
        )
    elif entity_type == "LogicalFallacy":
        return build_episode_body(
            "LogicalFallacy", topic=topic_str, flawed=content,
            why=feedback, correct="",
        )
    elif entity_type == "GuidedThinking":
        grade = "deep" if score and score >= 80 else "partial" if score and score >= 50 else "surface"
        return build_episode_body(
            "GuidedThinking", question=concept, answer=node_text or "未记录",
            correct_answer=feedback, grade=grade, next_steps="继续练习",
        )
    else:
        return build_episode_body(
            entity_type, topic=topic_str, concept=concept,
            definition=content, relations=source,
        )


# Singleton
_bridge_instance: Optional[GraphitiBridgeService] = None


async def get_graphiti_bridge(neo4j_client=None, canvas_base_path: Optional[str] = None) -> GraphitiBridgeService:
    """Get or create GraphitiBridgeService singleton."""
    global _bridge_instance
    if _bridge_instance is None:
        if neo4j_client is None:
            from app.clients.neo4j_client import get_neo4j_client
            neo4j_client = get_neo4j_client()
        _bridge_instance = GraphitiBridgeService(neo4j_client, canvas_base_path)
    return _bridge_instance
