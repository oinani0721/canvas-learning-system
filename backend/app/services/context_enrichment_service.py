# Canvas Learning System - Context Enrichment Service
# Phase 4.2: Option A - 相邻节点自动Enrichment
# FIX-3.1: 集成教材上下文
"""
Context Enrichment Service for Canvas nodes.

Provides multi-source context injection for AI agents:
- 1-hop adjacent node content (parent/child nodes)
- Edge label relationships
- Textbook references (from .canvas-links.json associations)

Features:
- 1-hop adjacent node discovery (parent/child)
- Edge label extraction for relationship context
- Textbook context from associated Canvas files
- Enriched prompt building for agents

[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Phase-4-Context-Enhancement]
[Source: FIX-3.1 集成教材上下文到后端]
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AdjacentNode:
    """
    Represents an adjacent node with its relationship.

    Attributes:
        node: Full node data from Canvas
        relation: Relationship direction ('parent' or 'child')
        edge_label: Label from the connecting edge
    """
    node: Dict[str, Any]
    relation: str  # 'parent' or 'child'
    edge_label: str


@dataclass
class EnrichedContext:
    """
    Contains enriched context for a target node.

    Attributes:
        target_node: The node being analyzed
        target_content: Text content of the target node
        adjacent_nodes: List of connected nodes with relationships
        enriched_context: Combined context string for agent prompts
        textbook_context: Optional textbook reference context
        has_textbook_refs: Whether textbook references were found

    [Story 21.2: Extended fields for position, edges, and neighbors]
        x, y, width, height: Position information
        incoming_edges: Edges pointing TO this node
        outgoing_edges: Edges FROM this node
        edge_labels: Unique labels from all connected edges
        parent_nodes: Nodes connected via incoming edges
        child_nodes: Nodes connected via outgoing edges
        sibling_nodes: Nodes sharing the same parent
    """
    target_node: Dict[str, Any]
    adjacent_nodes: List[AdjacentNode]
    enriched_context: str
    textbook_context: Optional[str] = None
    has_textbook_refs: bool = False

    # Story 21.2: Position information
    target_content: str = ""
    x: int = 0
    y: int = 0
    width: int = 400
    height: int = 200

    # Story 21.2: Edge relationships
    incoming_edges: Optional[List[Dict]] = None
    outgoing_edges: Optional[List[Dict]] = None
    edge_labels: Optional[List[str]] = None

    # Story 21.2: Neighbor categorization
    parent_nodes: Optional[List[Dict]] = None
    child_nodes: Optional[List[Dict]] = None
    sibling_nodes: Optional[List[Dict]] = None


class ContextEnrichmentService:
    """
    Service for enriching node context with adjacent node information and textbook references.

    This service supports the "Option A" enhancement from the architecture:
    automatic injection of 1-hop adjacent node content when agents analyze nodes.
    Also integrates textbook context from associated Canvas files.

    [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Phase-4-Context-Enhancement]
    [Source: FIX-3.1 集成教材上下文到后端]
    """

    def __init__(self, canvas_service, textbook_service=None):
        """
        Initialize ContextEnrichmentService.

        Args:
            canvas_service: CanvasService instance for reading Canvas data
            textbook_service: Optional TextbookContextService for textbook references
        """
        self._canvas_service = canvas_service
        self._textbook_service = textbook_service
        logger.debug("ContextEnrichmentService initialized")

    async def enrich_with_adjacent_nodes(
        self,
        canvas_name: str,
        node_id: str,
        hop_depth: int = 1
    ) -> EnrichedContext:
        """
        Get enriched context for a node including adjacent node content.

        Args:
            canvas_name: Canvas file name
            node_id: Target node ID to enrich
            hop_depth: Number of hops to traverse (default 1-hop)

        Returns:
            EnrichedContext with target node, adjacent nodes, and combined context

        Raises:
            ValueError: If node not found in Canvas

        Example:
            ```python
            enrichment = ContextEnrichmentService(canvas_service)
            context = await enrichment.enrich_with_adjacent_nodes(
                "离散数学", "node123", hop_depth=1
            )
            # context.enriched_context contains:
            # [目标节点] 逆否命题的内容...
            # [parent|prerequisite] 命题逻辑的内容...
            # [child|explains] 反证法的内容...
            ```

        [Story 21.2: Extended to populate position, edges, and neighbors]
        """
        # 1. Read Canvas data
        canvas_data = await self._canvas_service.read_canvas(canvas_name)
        nodes = {n.get("id"): n for n in canvas_data.get("nodes", [])}
        edges = canvas_data.get("edges", [])

        # 2. Find target node
        target_node = nodes.get(node_id)
        if not target_node:
            raise ValueError(f"Node not found: {node_id}")

        # Story 21.2: Extract position information
        x = int(target_node.get("x", 0))
        y = int(target_node.get("y", 0))
        width = int(target_node.get("width", 400))
        height = int(target_node.get("height", 200))
        target_content = target_node.get("text", "")

        # Story 21.2: Extract edge relationships
        incoming_edges = []
        outgoing_edges = []
        edge_labels_set = set()
        parent_node_ids = set()
        child_node_ids = set()

        for edge in edges:
            from_node = edge.get("fromNode", "")
            to_node = edge.get("toNode", "")
            label = edge.get("label", "")

            if from_node == node_id:
                # Outgoing edge: target → child
                outgoing_edges.append(edge)
                child_node_ids.add(to_node)
                if label:
                    edge_labels_set.add(label)
            elif to_node == node_id:
                # Incoming edge: parent → target
                incoming_edges.append(edge)
                parent_node_ids.add(from_node)
                if label:
                    edge_labels_set.add(label)

        # Story 21.2: Build neighbor node lists
        parent_nodes_list = [nodes[nid] for nid in parent_node_ids if nid in nodes]
        child_nodes_list = [nodes[nid] for nid in child_node_ids if nid in nodes]

        # Story 21.2: Find sibling nodes (nodes sharing the same parent)
        sibling_node_ids = set()
        for parent_id in parent_node_ids:
            for edge in edges:
                if edge.get("fromNode") == parent_id:
                    sibling_id = edge.get("toNode", "")
                    if sibling_id != node_id and sibling_id in nodes:
                        sibling_node_ids.add(sibling_id)
        sibling_nodes_list = [nodes[nid] for nid in sibling_node_ids]

        # 3. Find adjacent nodes (1-hop) - existing logic
        adjacent_nodes = self._find_adjacent_nodes(
            node_id, nodes, edges, hop_depth
        )

        # 4. Build enriched context string (adjacent nodes)
        enriched_context = self._build_enriched_context(
            target_node, adjacent_nodes
        )

        # 5. FIX-3.1: Get textbook context if service available
        textbook_context_str = None
        has_textbook_refs = False

        if self._textbook_service:
            try:
                # Use node content as query for textbook search
                node_text = target_node.get("text", "")[:200]  # First 200 chars as query
                textbook_ctx = await self._textbook_service.get_textbook_context(
                    f"{canvas_name}.canvas",
                    node_text
                )

                if textbook_ctx and (textbook_ctx.contexts or textbook_ctx.prerequisites):
                    has_textbook_refs = True
                    textbook_context_str = self._format_textbook_context(textbook_ctx)
                    logger.debug(
                        f"Found {len(textbook_ctx.contexts)} textbook refs, "
                        f"{len(textbook_ctx.prerequisites)} prerequisites"
                    )
            except Exception as e:
                logger.warning(f"Failed to get textbook context: {e}")
                # Continue without textbook context

        # 6. Combine all context
        if textbook_context_str:
            enriched_context = f"{enriched_context}\n\n{textbook_context_str}"

        logger.debug(
            f"Enriched context for {node_id}: "
            f"{len(adjacent_nodes)} adjacent nodes found, "
            f"textbook_refs={has_textbook_refs}, "
            f"incoming={len(incoming_edges)}, outgoing={len(outgoing_edges)}, "
            f"siblings={len(sibling_nodes_list)}"
        )

        # Story 21.2: Return EnrichedContext with all fields populated
        return EnrichedContext(
            target_node=target_node,
            adjacent_nodes=adjacent_nodes,
            enriched_context=enriched_context,
            textbook_context=textbook_context_str,
            has_textbook_refs=has_textbook_refs,
            # Story 21.2: Position information
            target_content=target_content,
            x=x,
            y=y,
            width=width,
            height=height,
            # Story 21.2: Edge relationships
            incoming_edges=incoming_edges,
            outgoing_edges=outgoing_edges,
            edge_labels=list(edge_labels_set),
            # Story 21.2: Neighbor categorization
            parent_nodes=parent_nodes_list,
            child_nodes=child_nodes_list,
            sibling_nodes=sibling_nodes_list,
        )

    def _find_adjacent_nodes(
        self,
        node_id: str,
        nodes: Dict[str, Dict[str, Any]],
        edges: List[Dict[str, Any]],
        hop_depth: int = 1
    ) -> List[AdjacentNode]:
        """
        Find all nodes adjacent to the target node.

        Traverses edges to find:
        - Parent nodes: edges where target is toNode
        - Child nodes: edges where target is fromNode

        Args:
            node_id: Target node ID
            nodes: Dict of all nodes keyed by ID
            edges: List of all edges
            hop_depth: Not fully implemented yet (reserved for future n-hop)

        Returns:
            List of AdjacentNode objects
        """
        adjacent = []

        for edge in edges:
            from_node = edge.get("fromNode", "")
            to_node = edge.get("toNode", "")
            label = edge.get("label", "connects_to")

            if from_node == node_id:
                # Target → Child (outgoing edge)
                child_node = nodes.get(to_node)
                if child_node:
                    adjacent.append(AdjacentNode(
                        node=child_node,
                        relation="child",
                        edge_label=label
                    ))

            elif to_node == node_id:
                # Parent → Target (incoming edge)
                parent_node = nodes.get(from_node)
                if parent_node:
                    adjacent.append(AdjacentNode(
                        node=parent_node,
                        relation="parent",
                        edge_label=label
                    ))

        return adjacent

    def _build_enriched_context(
        self,
        target_node: Dict[str, Any],
        adjacent_nodes: List[AdjacentNode]
    ) -> str:
        """
        Build a combined context string from target and adjacent nodes.

        Format:
            [目标节点] {target_text}

            [parent|{edge_label}] {parent_text}
            [child|{edge_label}] {child_text}
            ...

        Args:
            target_node: The main node being analyzed
            adjacent_nodes: List of adjacent nodes with relationships

        Returns:
            Formatted context string for agent prompts
        """
        parts = []

        # Add target node
        target_text = target_node.get("text", "")
        target_color = target_node.get("color", "")
        color_desc = self._get_color_description(target_color)

        parts.append(f"[目标节点{color_desc}] {target_text}")

        # Add adjacent nodes grouped by relation
        parents = [n for n in adjacent_nodes if n.relation == "parent"]
        children = [n for n in adjacent_nodes if n.relation == "child"]

        if parents:
            parts.append("\n--- 前置知识 (Parent Nodes) ---")
            for adj in parents:
                node_text = adj.node.get("text", "")[:300]  # Truncate long text
                parts.append(f"[parent|{adj.edge_label}] {node_text}")

        if children:
            parts.append("\n--- 衍生概念 (Child Nodes) ---")
            for adj in children:
                node_text = adj.node.get("text", "")[:300]  # Truncate long text
                parts.append(f"[child|{adj.edge_label}] {node_text}")

        return "\n\n".join(parts)

    def _get_color_description(self, color: str) -> str:
        """
        Get Chinese description for node color.

        Args:
            color: Obsidian color code ("1"-"6")

        Returns:
            Formatted color description
        """
        color_map = {
            "1": " (🔴红色-未理解)",
            "2": " (🟠橙色)",
            "3": " (🟡黄色-待填写)",
            "4": " (🟢绿色-已掌握)",
            "5": " (🔵蓝色)",
            "6": " (🟣紫色-部分理解)",
        }
        return color_map.get(color, "")

    def _format_textbook_context(self, textbook_ctx) -> str:
        """
        Format textbook context for inclusion in enriched context.

        [Source: FIX-3.1 集成教材上下文到后端]

        Args:
            textbook_ctx: FullTextbookContext from TextbookContextService

        Returns:
            Formatted textbook context string
        """
        from pathlib import Path

        parts = ["--- 相关教材参考 (Textbook References) ---"]

        # Add textbook contexts
        for ctx in textbook_ctx.contexts:
            display_name = Path(ctx.textbook_canvas).stem
            parts.append(f"[textbook|{display_name}] {ctx.section_name}")
            parts.append(f"  预览: {ctx.content_preview}...")

        # Add prerequisites
        if textbook_ctx.prerequisites:
            parts.append("\n--- 建议先复习 (Prerequisites) ---")
            for prereq in textbook_ctx.prerequisites:
                display_name = Path(prereq.source_canvas).stem if prereq.source_canvas else "未知"
                importance_map = {
                    'required': '必修',
                    'recommended': '推荐',
                    'optional': '可选'
                }
                importance_str = importance_map.get(prereq.importance, '')
                parts.append(f"[prerequisite|{importance_str}] {prereq.concept_name} ({display_name})")

        return "\n".join(parts)

    def build_agent_prompt(
        self,
        base_prompt: str,
        context: Optional[EnrichedContext]
    ) -> str:
        """
        Build an enriched agent prompt with adjacent node context.

        Args:
            base_prompt: Original prompt for the agent
            context: EnrichedContext from enrich_with_adjacent_nodes()

        Returns:
            Enhanced prompt with context section

        Example:
            ```python
            enriched_prompt = service.build_agent_prompt(
                "请评估用户对此概念的理解程度",
                context
            )
            # Result:
            # 请评估用户对此概念的理解程度
            #
            # ## 上下文信息 (Canvas相邻节点)
            # [目标节点] 逆否命题...
            # [parent|prerequisite] 命题逻辑...
            ```
        """
        if not context or not context.adjacent_nodes:
            return base_prompt

        sections = [base_prompt]
        sections.append("\n## 上下文信息 (Canvas相邻节点)")
        sections.append(context.enriched_context)
        sections.append("\n请在分析时参考上述相邻节点的上下文关系。")

        return "\n".join(sections)
