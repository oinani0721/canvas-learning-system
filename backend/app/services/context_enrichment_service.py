# Canvas Learning System - Context Enrichment Service
# Phase 4.2: Option A - 相邻节点自动Enrichment
# FIX-3.1: 集成教材上下文
# Story 25.3: 集成跨Canvas上下文
"""
Context Enrichment Service for Canvas nodes.

Provides multi-source context injection for AI agents:
- 1-hop adjacent node content (parent/child nodes)
- Edge label relationships
- Textbook references (from .canvas-links.json associations)
- Cross-Canvas lecture references (exercise-lecture associations)

Features:
- 1-hop adjacent node discovery (parent/child)
- Edge label extraction for relationship context
- Textbook context from associated Canvas files
- Cross-Canvas context from lecture associations
- Enriched prompt building for agents

[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Phase-4-Context-Enhancement]
[Source: FIX-3.1 集成教材上下文到后端]
[Source: Story 25.3 - Exercise-Lecture Canvas Association]
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import structlog

# Standard logger for backward compatibility
logger = logging.getLogger(__name__)

# ✅ Verified from ADR-010:77-100 (structlog get_logger)
# Structlog logger for new FILE node handling (Story 12.D.2)
struct_logger = structlog.get_logger(__name__)


def get_node_content(node: dict, vault_path: str) -> str:
    """
    Extract content from a Canvas node based on its type.

    Story 12.D.2: Backend FILE Type Node Support
    Handles all four Canvas node types defined in JSON Canvas Spec 1.0.

    Args:
        node: Canvas node dictionary with 'type' and content fields
        vault_path: Absolute path to Obsidian vault root

    Returns:
        Node content as string, empty string if unavailable

    [Source: specs/data/canvas-node.schema.json#L24-L38 - node type handling]
    [Source: ADR-001 - file paths are relative to vault root]
    """
    node_type = node.get("type", "text")
    node_id = node.get("id", "unknown")

    struct_logger.debug("get_node_content", node_id=node_id, node_type=node_type)

    if node_type == "text":
        return node.get("text", "")

    elif node_type == "file":
        file_path = node.get("file", "")
        if not file_path:
            struct_logger.warning("file_node_missing_path", node_id=node_id)
            return ""

        # Construct absolute path
        # [Source: ADR-001 - file paths are relative to vault root]
        abs_path = Path(vault_path) / file_path
        struct_logger.debug(
            "resolving_file_path", node_id=node_id, resolved_path=str(abs_path)
        )

        try:
            content = abs_path.read_text(encoding="utf-8")
            struct_logger.debug(
                "file_read_success", node_id=node_id, content_length=len(content)
            )
            return content
        except FileNotFoundError:
            struct_logger.warning(
                "file_not_found", node_id=node_id, path=str(abs_path)
            )
            return ""
        except PermissionError:
            struct_logger.warning(
                "file_permission_denied", node_id=node_id, path=str(abs_path)
            )
            return ""
        except Exception as e:
            struct_logger.warning(
                "file_read_error", node_id=node_id, error=str(e)
            )
            return ""

    elif node_type == "link":
        return node.get("url", "")

    elif node_type == "group":
        return ""

    else:
        struct_logger.warning(
            "unknown_node_type", node_id=node_id, node_type=node_type
        )
        return ""


@dataclass
class AdjacentNode:
    """
    Represents an adjacent node with its relationship.

    Attributes:
        node: Full node data from Canvas
        relation: Relationship direction ('parent' or 'child')
        edge_label: Label from the connecting edge
        hop_distance: Distance from target node (1 = direct, 2 = 2-hop)
                     [Story 12.E.3: Added for 2-hop context traversal support]
    """
    node: Dict[str, Any]
    relation: str  # 'parent' or 'child'
    edge_label: str
    hop_distance: int = 1  # Story 12.E.3: Default 1-hop (backward compatible)


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

    [Story 25.3: Cross-Canvas context fields]
        cross_canvas_context: Optional cross-canvas lecture reference context
        has_cross_canvas_refs: Whether cross-canvas references were found
        lecture_canvas_path: Path to the associated lecture Canvas
        lecture_canvas_title: Title of the associated lecture Canvas
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

    # Story 25.3: Cross-Canvas context
    cross_canvas_context: Optional[str] = None
    has_cross_canvas_refs: bool = False
    lecture_canvas_path: Optional[str] = None
    lecture_canvas_title: Optional[str] = None

    # Story 12.A.3: Graphiti relations
    graphiti_relations: Optional[List[Dict]] = None
    has_graphiti_refs: bool = False


class ContextEnrichmentService:
    """
    Service for enriching node context with adjacent node information and textbook references.

    This service supports the "Option A" enhancement from the architecture:
    automatic injection of 1-hop adjacent node content when agents analyze nodes.
    Also integrates textbook context from associated Canvas files and
    cross-Canvas lecture references from exercise-lecture associations.

    [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Phase-4-Context-Enhancement]
    [Source: FIX-3.1 集成教材上下文到后端]
    [Source: Story 25.3 - Exercise-Lecture Canvas Association]
    """

    def __init__(
        self,
        canvas_service,
        textbook_service=None,
        cross_canvas_service=None,
        graphiti_service=None
    ):
        """
        Initialize ContextEnrichmentService.

        Args:
            canvas_service: CanvasService instance for reading Canvas data
            textbook_service: Optional TextbookContextService for textbook references
            cross_canvas_service: Optional CrossCanvasService for cross-Canvas associations
            graphiti_service: Optional LearningMemoryClient for Graphiti relations

        [Story 25.3: Added cross_canvas_service parameter]
        [Story 12.A.3: Added graphiti_service parameter]
        """
        self._canvas_service = canvas_service
        self._textbook_service = textbook_service
        self._cross_canvas_service = cross_canvas_service
        self._graphiti_service = graphiti_service
        logger.debug("ContextEnrichmentService initialized")

    async def enrich_with_adjacent_nodes(
        self,
        canvas_name: str,
        node_id: str,
        hop_depth: int = 1,
        include_graphiti: bool = True
    ) -> EnrichedContext:
        """
        Get enriched context for a node including adjacent node content.

        Args:
            canvas_name: Canvas file name
            node_id: Target node ID to enrich
            hop_depth: Number of hops to traverse (default 1-hop)
            include_graphiti: Whether to include Graphiti relations (default True)

        [Story 12.A.3: Added include_graphiti parameter for Graphiti MCP integration]

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

        # Story 12.D.2: Use get_node_content() to handle all node types (text, file, link, group)
        # [Source: specs/data/canvas-node.schema.json#L24-L38]
        vault_path = self._canvas_service.canvas_base_path
        target_content = get_node_content(target_node, vault_path)

        # Story 12.D.3: Log node content resolution trace
        node_type = target_node.get("type", "text")
        file_path = target_node.get("file") if node_type == "file" else None
        content_source = "empty"
        if target_content:
            content_source = "file_read" if node_type == "file" else "json_text"
        struct_logger.info(
            "[Story 12.D.3] Node content resolved",
            node_id=node_id,
            node_type=node_type,
            file_path=file_path,
            content_source=content_source,
            content_length=len(target_content)
        )

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

        # 6. Combine textbook context
        if textbook_context_str:
            enriched_context = f"{enriched_context}\n\n{textbook_context_str}"

        # 7. Story 25.3: Get cross-canvas context (lecture references for exercise canvases)
        cross_canvas_context_str = None
        has_cross_canvas_refs = False
        lecture_canvas_path = None
        lecture_canvas_title = None

        if self._cross_canvas_service:
            try:
                # Try to get associated lecture canvas
                canvas_path = f"{canvas_name}.canvas"
                cross_ctx = await self.get_cross_canvas_context(canvas_path)

                if cross_ctx:
                    has_cross_canvas_refs = True
                    lecture_canvas_path = cross_ctx.get("lecture_canvas_path")
                    lecture_canvas_title = cross_ctx.get("lecture_canvas_title")
                    cross_canvas_context_str = self._format_cross_canvas_context(cross_ctx)
                    logger.debug(
                        f"Found cross-canvas ref: {lecture_canvas_title} "
                        f"with {len(cross_ctx.get('relevant_nodes', []))} nodes"
                    )
            except Exception as e:
                logger.warning(f"Failed to get cross-canvas context: {e}")
                # Continue without cross-canvas context

        # 8. Combine cross-canvas context
        if cross_canvas_context_str:
            enriched_context = f"{enriched_context}\n\n{cross_canvas_context_str}"

        # 9. Story 12.A.3: Get Graphiti relations if enabled
        graphiti_relations_list = []
        has_graphiti_refs = False
        graphiti_context_str = None

        if include_graphiti and self._graphiti_service:
            try:
                # Search Graphiti using target node content as query
                node_text = target_node.get("text", "")[:200]  # First 200 chars as query
                graphiti_results = await self._search_graphiti_relations(
                    query=node_text,
                    canvas_name=canvas_name,
                    node_id=node_id
                )

                if graphiti_results:
                    has_graphiti_refs = True
                    graphiti_relations_list = graphiti_results
                    graphiti_context_str = self._format_graphiti_context(graphiti_results)
                    logger.debug(
                        f"Found {len(graphiti_results)} Graphiti relations for {node_id}"
                    )
            except Exception as e:
                logger.warning(f"Failed to get Graphiti relations: {e}")
                # Continue without Graphiti context (graceful degradation)

        # 10. Combine Graphiti context
        if graphiti_context_str:
            enriched_context = f"{enriched_context}\n\n{graphiti_context_str}"

        logger.debug(
            f"Enriched context for {node_id}: "
            f"{len(adjacent_nodes)} adjacent nodes found, "
            f"textbook_refs={has_textbook_refs}, "
            f"cross_canvas_refs={has_cross_canvas_refs}, "
            f"graphiti_refs={has_graphiti_refs}, "
            f"incoming={len(incoming_edges)}, outgoing={len(outgoing_edges)}, "
            f"siblings={len(sibling_nodes_list)}"
        )

        # Story 21.2 + 25.3 + 12.A.3: Return EnrichedContext with all fields populated
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
            # Story 25.3: Cross-Canvas context
            cross_canvas_context=cross_canvas_context_str,
            has_cross_canvas_refs=has_cross_canvas_refs,
            lecture_canvas_path=lecture_canvas_path,
            lecture_canvas_title=lecture_canvas_title,
            # Story 12.A.3: Graphiti relations
            graphiti_relations=graphiti_relations_list,
            has_graphiti_refs=has_graphiti_refs,
        )

    def _find_adjacent_nodes(
        self,
        node_id: str,
        nodes: Dict[str, Dict[str, Any]],
        edges: List[Dict[str, Any]],
        hop_depth: int = 1,
        visited: Optional[Set[str]] = None,
        current_hop: int = 1
    ) -> List[AdjacentNode]:
        """
        Find all nodes adjacent to the target node up to hop_depth.

        Traverses edges to find:
        - Parent nodes: edges where target is toNode
        - Child nodes: edges where target is fromNode

        [Story 12.E.3: Implemented 2-hop recursive traversal with cycle prevention]

        Args:
            node_id: Target node ID
            nodes: Dict of all nodes keyed by ID
            edges: List of all edges
            hop_depth: Maximum traversal depth (1 = direct, 2 = 2-hop)
            visited: Set of already visited node IDs (prevents cycles)
            current_hop: Current recursion depth (internal use)

        Returns:
            List of AdjacentNode objects sorted by hop_distance
        """
        # Story 12.E.3: Initialize visited set to prevent cycles
        if visited is None:
            visited = {node_id}

        adjacent = []

        for edge in edges:
            from_node = edge.get("fromNode", "")
            to_node = edge.get("toNode", "")
            label = edge.get("label", "connects_to")

            if from_node == node_id:
                # Target → Child (outgoing edge)
                # Story 12.E.3: Check visited to prevent cycles
                if to_node not in visited:
                    child_node = nodes.get(to_node)
                    if child_node:
                        visited.add(to_node)
                        adjacent.append(AdjacentNode(
                            node=child_node,
                            relation="child",
                            edge_label=label,
                            hop_distance=current_hop
                        ))

            elif to_node == node_id:
                # Parent → Target (incoming edge)
                # Story 12.E.3: Check visited to prevent cycles
                if from_node not in visited:
                    parent_node = nodes.get(from_node)
                    if parent_node:
                        visited.add(from_node)
                        adjacent.append(AdjacentNode(
                            node=parent_node,
                            relation="parent",
                            edge_label=label,
                            hop_distance=current_hop
                        ))

        # Story 12.E.3: Recurse for 2-hop if needed
        if hop_depth >= 2 and current_hop < hop_depth:
            hop1_node_ids = [adj.node.get("id") for adj in adjacent if adj.node.get("id")]

            for hop1_node_id in hop1_node_ids:
                hop2_nodes = self._find_adjacent_nodes(
                    node_id=hop1_node_id,
                    nodes=nodes,
                    edges=edges,
                    hop_depth=hop_depth,
                    visited=visited,
                    current_hop=current_hop + 1
                )
                adjacent.extend(hop2_nodes)

        # Story 12.E.3: Sort by hop_distance (closer nodes first)
        adjacent.sort(key=lambda x: x.hop_distance)

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

        [Story 12.E.3: Updated to show hop_distance in output format]

        Args:
            target_node: The main node being analyzed
            adjacent_nodes: List of adjacent nodes with relationships

        Returns:
            Formatted context string for agent prompts
        """
        parts = []

        # Story 12.D.2: Get vault_path for FILE node content resolution
        vault_path = self._canvas_service.canvas_base_path

        # Add target node
        # Story 12.D.2: Use get_node_content() to handle all node types
        target_text = get_node_content(target_node, vault_path)
        target_color = target_node.get("color", "")
        color_desc = self._get_color_description(target_color)

        parts.append(f"[目标节点{color_desc}] {target_text}")

        # Story 12.E.3: Group adjacent nodes by relation and hop_distance
        parents_1hop = [n for n in adjacent_nodes if n.relation == "parent" and n.hop_distance == 1]
        parents_2hop = [n for n in adjacent_nodes if n.relation == "parent" and n.hop_distance == 2]
        children_1hop = [n for n in adjacent_nodes if n.relation == "child" and n.hop_distance == 1]
        children_2hop = [n for n in adjacent_nodes if n.relation == "child" and n.hop_distance == 2]

        if parents_1hop or parents_2hop:
            parts.append("\n--- 前置知识 (Parent Nodes) ---")
            # Story 12.E.3: Add 1-hop parents first
            for adj in parents_1hop:
                # Story 12.D.2: Use get_node_content() for adjacent nodes too
                node_text = get_node_content(adj.node, vault_path)[:300]  # Truncate long text
                parts.append(f"[parent|{adj.edge_label}] {node_text}")
            # Story 12.E.3: Add 2-hop parents with indicator
            for adj in parents_2hop:
                node_text = get_node_content(adj.node, vault_path)[:300]
                parts.append(f"[parent-2hop|{adj.edge_label}] {node_text}")

        if children_1hop or children_2hop:
            parts.append("\n--- 衍生概念 (Child Nodes) ---")
            # Story 12.E.3: Add 1-hop children first
            for adj in children_1hop:
                # Story 12.D.2: Use get_node_content() for adjacent nodes too
                node_text = get_node_content(adj.node, vault_path)[:300]  # Truncate long text
                parts.append(f"[child|{adj.edge_label}] {node_text}")
            # Story 12.E.3: Add 2-hop children with indicator
            for adj in children_2hop:
                node_text = get_node_content(adj.node, vault_path)[:300]
                parts.append(f"[child-2hop|{adj.edge_label}] {node_text}")

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

    async def get_cross_canvas_context(
        self,
        canvas_path: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cross-canvas context for an exercise canvas.

        Retrieves the associated lecture canvas and extracts relevant
        knowledge point nodes for context enrichment.

        [Source: Story 25.3 AC2 - Auto-retrieve lecture content when solving problems]
        [Source: Story 25.3 Task 4.1 - Add get_cross_canvas_context method]

        Args:
            canvas_path: Path to the exercise canvas (e.g., "习题-线性代数.canvas")

        Returns:
            Dict containing:
                - lecture_canvas_path: Path to the lecture canvas
                - lecture_canvas_title: Title of the lecture canvas
                - relevant_nodes: List of relevant knowledge point nodes
                - confidence: Association confidence score
            Or None if no association found
        """
        if not self._cross_canvas_service:
            return None

        # Get the associated lecture canvas for this exercise
        association = await self._cross_canvas_service.get_lecture_for_exercise(canvas_path)

        if not association:
            return None

        # Read the lecture canvas to extract relevant nodes
        lecture_path = association.target_canvas_path
        lecture_title = association.target_canvas_title

        try:
            # Extract canvas name without extension
            canvas_name = lecture_path.replace(".canvas", "")
            lecture_data = await self._canvas_service.read_canvas(canvas_name)

            # Extract text nodes from lecture canvas (knowledge points)
            relevant_nodes = []
            for node in lecture_data.get("nodes", []):
                # Only include text nodes with content
                if node.get("type") == "text" and node.get("text"):
                    node_text = node.get("text", "")[:300]  # Limit to 300 chars
                    node_color = node.get("color", "")
                    relevant_nodes.append({
                        "id": node.get("id"),
                        "text": node_text,
                        "color": node_color,
                        "x": node.get("x", 0),
                        "y": node.get("y", 0),
                    })

            # Limit to top 5 most relevant nodes (by position - earlier nodes first)
            relevant_nodes.sort(key=lambda n: (n["y"], n["x"]))
            relevant_nodes = relevant_nodes[:5]

            return {
                "lecture_canvas_path": lecture_path,
                "lecture_canvas_title": lecture_title,
                "relevant_nodes": relevant_nodes,
                "confidence": association.confidence,
                "common_concepts": association.common_concepts,
            }

        except Exception as e:
            logger.warning(f"Failed to read lecture canvas {lecture_path}: {e}")
            # Return basic info even if we can't read the lecture canvas
            return {
                "lecture_canvas_path": lecture_path,
                "lecture_canvas_title": lecture_title,
                "relevant_nodes": [],
                "confidence": association.confidence,
                "common_concepts": association.common_concepts,
            }

    def _format_cross_canvas_context(self, cross_ctx: Dict[str, Any]) -> str:
        """
        Format cross-canvas context for inclusion in enriched context.

        Formats lecture references as "参见讲座: {name} > {node}" per AC3.

        [Source: Story 25.3 AC3 - Agent prompt includes lecture knowledge point references]
        [Source: Story 25.3 Task 4.3 - Format lecture references]

        Args:
            cross_ctx: Cross-canvas context dict from get_cross_canvas_context()

        Returns:
            Formatted cross-canvas context string
        """
        from pathlib import Path

        lecture_title = cross_ctx.get("lecture_canvas_title", "未知讲座")
        lecture_path = cross_ctx.get("lecture_canvas_path", "")
        relevant_nodes = cross_ctx.get("relevant_nodes", [])
        confidence = cross_ctx.get("confidence", 0.0)
        common_concepts = cross_ctx.get("common_concepts", [])

        # Format display name
        display_name = Path(lecture_path).stem if lecture_path else lecture_title

        parts = [f"--- 参见讲座: {display_name} (置信度: {confidence:.0%}) ---"]

        # Add common concepts if available
        if common_concepts:
            concepts_str = ", ".join(common_concepts[:5])  # Limit to 5
            parts.append(f"[共同概念] {concepts_str}")

        # Add relevant knowledge point nodes
        if relevant_nodes:
            parts.append("\n--- 相关知识点 (Lecture Knowledge Points) ---")
            for node in relevant_nodes:
                node_text = node.get("text", "")
                color = node.get("color", "")
                color_desc = self._get_color_description(color)
                # Format: 参见讲座: {name} > {node}
                parts.append(f"[lecture|{display_name}]{color_desc} {node_text}")
        else:
            parts.append(f"[lecture|{display_name}] (暂无具体知识点信息)")

        return "\n".join(parts)

    async def _search_graphiti_relations(
        self,
        query: str,
        canvas_name: Optional[str] = None,
        node_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search Graphiti for related learning memories and concepts.

        Uses LearningMemoryClient.search_memories() to find relevant historical
        learning records that can provide additional context for the agent.

        [Source: Story 12.A.3 AC4 - Agent receives Graphiti-related concepts]
        [Source: Story 12.A.3 Task 2 - Integrate Graphiti MCP tool]

        Args:
            query: Search query (typically node text content)
            canvas_name: Optional filter by canvas name
            node_id: Optional filter by node ID

        Returns:
            List of related memory dicts with relevance scores
        """
        if not self._graphiti_service:
            return []

        try:
            # Initialize service if needed
            await self._graphiti_service.initialize()

            # Search for related memories
            results = await self._graphiti_service.search_memories(
                query=query,
                canvas_name=canvas_name,
                node_id=node_id,
                limit=5  # Limit to top 5 most relevant
            )

            logger.debug(f"Graphiti search for '{query[:50]}...': {len(results)} results")
            return results

        except Exception as e:
            logger.warning(f"Graphiti search failed: {e}")
            return []

    def _format_graphiti_context(self, graphiti_results: List[Dict[str, Any]]) -> str:
        """
        Format Graphiti results for inclusion in enriched context.

        Formats historical learning memories as context for the agent prompt.

        [Source: Story 12.A.3 AC4 - Format Graphiti relations for agent]

        Args:
            graphiti_results: List of memory dicts from search_memories()

        Returns:
            Formatted Graphiti context string
        """
        if not graphiti_results:
            return ""

        parts = ["--- 历史学习记忆 (Graphiti Relations) ---"]

        for memory in graphiti_results:
            concept = memory.get("concept", "未知概念")
            relevance = memory.get("relevance", 0.0)
            timestamp = memory.get("timestamp", "")[:10] if memory.get("timestamp") else ""
            score = memory.get("score")
            understanding = memory.get("user_understanding", "")

            # Format entry with relevance and optional score
            entry = f"[memory|{relevance:.0%}] {concept}"
            if timestamp:
                entry = f"[{timestamp}] " + entry
            if score is not None:
                entry += f" (得分: {score:.1f}/40)"

            parts.append(entry)

            # Add brief understanding preview if available
            if understanding:
                preview = understanding[:100] + "..." if len(understanding) > 100 else understanding
                parts.append(f"  历史理解: {preview}")

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
