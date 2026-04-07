# Canvas Learning System - Context Enrichment Service
# Phase 4.2: Option A - 相邻节点自动Enrichment
"""
Context Enrichment Service for Canvas nodes.

Provides multi-source context injection for AI agents:
- 1-hop adjacent node content (parent/child nodes)
- Edge label relationships
- Learning memory relations

Features:
- 1-hop adjacent node discovery (parent/child)
- Edge label extraction for relationship context
- Learning memory integration
- Enriched prompt building for agents

[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Phase-4-Context-Enhancement]
"""

import asyncio
import logging
import re

import structlog
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# Standard logger for backward compatibility
logger = structlog.get_logger(__name__)

# ✅ Verified from ADR-010:77-100 (structlog get_logger)
# 6-9 M1 fix: structlog import with fallback to standard logging
try:
    import structlog

    struct_logger = structlog.get_logger(__name__)
except ImportError:
    struct_logger = logger  # type: ignore[assignment]


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

        # Check if file is a binary/image file — return embed syntax instead of reading
        IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp"}
        file_ext = Path(file_path).suffix.lower()
        if file_ext in IMAGE_EXTENSIONS:
            struct_logger.debug(
                "image_file_node_embed", node_id=node_id, file_path=file_path
            )
            subpath = node.get("subpath", "")
            return f"![[{file_path}{subpath}]]"

        # Construct absolute path for text-based files (md, pdf, etc.)
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
            struct_logger.warning("file_not_found", node_id=node_id, path=str(abs_path))
            return ""
        except PermissionError:
            struct_logger.warning(
                "file_permission_denied", node_id=node_id, path=str(abs_path)
            )
            return ""
        except OSError as e:
            struct_logger.warning("file_read_error", node_id=node_id, error=str(e))
            return ""

    elif node_type == "link":
        return node.get("url", "")

    elif node_type == "group":
        return ""

    else:
        struct_logger.warning("unknown_node_type", node_id=node_id, node_type=node_type)
        return ""


# ═══════════════════════════════════════════════════════════════════════════════
# Round 4 Step 1: Wikilink extraction and resolution
# ═══════════════════════════════════════════════════════════════════════════════

_WIKILINK_PATTERN = re.compile(r"!?\[\[([^\]]+)\]\]")
_IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".svg",
    ".webp",
    ".mp4",
    ".mp3",
    ".wav",
    ".pdf",
}
_WIKILINK_EXCLUDED_PATTERNS = ("-explanations/", "/chunks/", "解释-", "四层次解释-")


def _extract_heading_section(content: str, heading: str, max_length: int = 500) -> str:
    """Extract a section under a specific heading from markdown content."""
    lines = content.splitlines()
    capture = False
    captured = []
    heading_lower = heading.lower().strip()

    for line in lines:
        h_match = re.match(r"^(#{1,6})\s+(.+)", line)
        if h_match:
            h_text = h_match.group(2).strip().lower()
            if h_text == heading_lower:
                capture = True
                continue
            elif capture:
                # Hit next heading at same or higher level — stop
                break
        if capture:
            captured.append(line)

    result = "\n".join(captured).strip()
    if len(result) > max_length:
        result = result[:max_length] + "..."
    return result


def extract_and_resolve_wikilinks(
    text: str,
    vault_path: str,
    max_links: int = 5,
    max_content_length: int = 500,
) -> List[Dict[str, Any]]:
    """Extract [[wikilinks]] from text and resolve their content.

    Parses NoteName#Heading|DisplayText format, reads resolved files,
    and extracts heading sections when specified.

    Args:
        text: Source text containing wikilinks
        vault_path: Absolute path to Obsidian vault root
        max_links: Maximum number of links to resolve
        max_content_length: Max characters per resolved content

    Returns:
        List of dicts with keys: link, file_path, heading, content, resolved
    """
    vault = Path(vault_path)
    results: List[Dict[str, Any]] = []
    seen_links: Set[str] = set()

    for match in _WIKILINK_PATTERN.finditer(text):
        if len(results) >= max_links:
            break

        full_match = match.group(0)
        # Skip embeds of images/media
        if full_match.startswith("!"):
            inner = match.group(1)
            ext = Path(inner.split("#")[0].split("|")[0].strip()).suffix.lower()
            if ext in _IMAGE_EXTENSIONS:
                continue

        inner = match.group(1)
        # Parse: NoteName#Heading|DisplayText
        display = None
        if "|" in inner:
            inner, display = inner.rsplit("|", 1)
        heading = None
        if "#" in inner:
            file_ref, heading = inner.split("#", 1)
        else:
            file_ref = inner

        file_ref = file_ref.strip()
        if not file_ref:
            continue

        # Deduplicate
        link_key = f"{file_ref}#{heading}" if heading else file_ref
        if link_key in seen_links:
            continue
        seen_links.add(link_key)

        # Filter excluded patterns
        if any(p in file_ref for p in _WIKILINK_EXCLUDED_PATTERNS):
            continue

        # Resolve file path (try as-is, then with .md suffix)
        resolved_path = None
        for candidate in [vault / file_ref, vault / f"{file_ref}.md"]:
            if candidate.exists() and candidate.is_file():
                resolved_path = candidate
                break

        entry: Dict[str, Any] = {
            "link": full_match,
            "file_path": file_ref,
            "heading": heading,
            "content": "",
            "resolved": False,
        }

        if resolved_path:
            try:
                file_content = resolved_path.read_text(encoding="utf-8")
                if heading:
                    section = _extract_heading_section(
                        file_content, heading, max_content_length
                    )
                    entry["content"] = (
                        section if section else file_content[:max_content_length]
                    )
                else:
                    entry["content"] = file_content[:max_content_length]
                    if len(file_content) > max_content_length:
                        entry["content"] += "..."
                entry["resolved"] = True
            except (OSError, UnicodeDecodeError) as e:
                logger.debug(f"Wikilink resolution failed for {file_ref}: {e}")

        results.append(entry)

    return results


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

    # Story 12.A.3: Learning memory relations (Neo4j-backed, not graphiti-core)
    learning_relations: Optional[List[Dict]] = None
    has_learning_refs: bool = False

    # Round 4 Step 2: Wikilink references from target node text
    wikilink_context: Optional[str] = None
    has_wikilink_refs: bool = False

    # Story 12.E.5-fix: Source file path for file type nodes
    # When target node is a "file" type, this stores the absolute path to the MD file
    # Used for resolving relative image paths in MD content
    source_file_path: Optional[str] = None


class ContextEnrichmentService:
    """
    Service for enriching node context with adjacent node information.

    This service supports the "Option A" enhancement from the architecture:
    automatic injection of 1-hop adjacent node content when agents analyze nodes.
    Also integrates learning memory relations.

    [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Phase-4-Context-Enhancement]
    """

    def __init__(
        self,
        canvas_service,
        learning_memory_service=None,
    ):
        """
        Initialize ContextEnrichmentService.

        Args:
            canvas_service: CanvasService instance for reading Canvas data
            learning_memory_service: Optional LearningMemoryClient for learning memory relations

        [Story 12.A.3: Added learning_memory_service parameter (was graphiti_service)]
        """
        self._canvas_service = canvas_service
        self._learning_memory_service = learning_memory_service

        logger.debug("ContextEnrichmentService initialized")

    # ═══════════════════════════════════════════════════════════════════════════════
    # Story 36.8 Task 1: Exercise Canvas Detection
    # ═══════════════════════════════════════════════════════════════════════════════

    # Story 36.8 AC4: Patterns for identifying exercise canvases
    # [Source: docs/stories/36.8.story.md#Task-1.1]
    EXERCISE_PATTERNS = [
        r"题目",
        r"习题",
        r"练习",
        r"作业",
        r"exam",
        r"exercise",
        r"problem",
        r"quiz",
        r"test",
        r"期末",
        r"期中",
        r"复习题",
        r"真题",
        r"模拟",
    ]

    def is_exercise_canvas(self, canvas_path: str) -> bool:
        """
        Check if a canvas path matches exercise patterns.

        Story 36.8 Task 1.1: Add is_exercise_canvas() method.

        Checks canvas filename against EXERCISE_PATTERNS to determine if
        this is an exercise canvas that should trigger cross-canvas injection.

        Args:
            canvas_path: Canvas file path (e.g., "线性代数-习题.canvas")

        Returns:
            True if canvas matches exercise patterns

        [Source: docs/stories/36.8.story.md#Task-1.1]
        [Source: specs/api/agent-api.openapi.yml#L205-L260]
        """
        path_lower = canvas_path.lower()
        return any(re.search(pattern, path_lower) for pattern in self.EXERCISE_PATTERNS)

    # ═══════════════════════════════════════════════════════════════════════════════
    # Story 36.8 Task 3: Top 5 Knowledge Point Extraction
    # ═══════════════════════════════════════════════════════════════════════════════

    # Story 36.8 AC2: Color priority scoring (canvas_utils.py authoritative)
    # green(2) > purple(3) > yellow(6) > red(4) > gray(1)
    COLOR_PRIORITY_SCORES = {
        "2": 4.0,  # Green - mastered, highest priority for reference
        "3": 3.0,  # Purple - partial understanding
        "6": 2.5,  # Yellow - personal understanding area
        "4": 1.5,  # Red - not understood
        "1": 1.0,  # Gray - no special meaning
        "5": 2.0,  # Blue - AI generated content
    }

    def _calculate_color_priority(self, color: str) -> float:
        """
        Calculate priority score based on node color.

        Story 36.8 Task 3.2: Color-based prioritization.

        Green (mastered) concepts are prioritized for reference.

        Args:
            color: Obsidian color code ("1"-"6" or empty)

        Returns:
            Priority score (0-4, higher = more relevant)

        [Source: docs/stories/36.8.story.md#Task-3.2]
        """
        return self.COLOR_PRIORITY_SCORES.get(color, 0.5)

    def _calculate_text_similarity(self, exercise_text: str, node_text: str) -> float:
        """
        Calculate semantic similarity between exercise and node text.

        Story 36.8 Task 3.2: Semantic similarity scoring (MVP: word overlap).

        Uses simple word overlap ratio for MVP implementation.
        Can be enhanced with embeddings in future iterations.

        Args:
            exercise_text: Text content from exercise node
            node_text: Text content from lecture node

        Returns:
            Similarity score (0-1)

        [Source: docs/stories/36.8.story.md#Task-3.2]
        """
        if not exercise_text or not node_text:
            return 0.0

        # Simple word-based overlap for MVP
        # Normalize: lowercase, split by whitespace and punctuation
        exercise_words = set(re.findall(r"[\u4e00-\u9fff]+|\w+", exercise_text.lower()))
        node_words = set(re.findall(r"[\u4e00-\u9fff]+|\w+", node_text.lower()))

        if not exercise_words or not node_words:
            return 0.0

        # Jaccard similarity
        intersection = len(exercise_words & node_words)
        union = len(exercise_words | node_words)

        return intersection / union if union > 0 else 0.0

    def _calculate_position_score(self, y_position: int, max_y: int) -> float:
        """
        Calculate position score (earlier nodes = higher score).

        Story 36.8 Task 3.2: Position-based prioritization.

        Earlier concepts (smaller Y) are foundational and prioritized.

        Args:
            y_position: Node Y coordinate
            max_y: Maximum Y coordinate in canvas

        Returns:
            Position score (0-1, higher = earlier in canvas)

        [Source: docs/stories/36.8.story.md#Task-3.2]
        """
        if max_y <= 0:
            return 0.5

        # Normalize to 0-1, invert so smaller Y = higher score
        return 1.0 - (y_position / max_y) if max_y > 0 else 0.5

    def extract_top_knowledge_points(
        self,
        lecture_nodes: List[Dict[str, Any]],
        exercise_content: str = "",
        max_nodes: int = 5,
        max_content_length: int = 300,
    ) -> List[Dict[str, Any]]:
        """
        Extract top N most relevant knowledge points from lecture nodes.

        Story 36.8 Task 3.1, 3.2, 3.3: Intelligent knowledge point extraction.

        Scoring algorithm combines:
        - Semantic similarity to exercise content (40% weight)
        - Position in lecture - earlier = foundational (30% weight)
        - Color status - green/mastered prioritized (30% weight)

        Args:
            lecture_nodes: List of nodes from lecture canvas
            exercise_content: Content from exercise node for relevance scoring
            max_nodes: Maximum nodes to return (default: 5 per AC2)
            max_content_length: Max chars per node content (default: 300 per Task 3.3)

        Returns:
            List of top N relevant knowledge point dicts, each containing:
            - id: Node ID
            - text: Node content (truncated to max_content_length)
            - color: Node color
            - x, y: Position
            - relevance_score: Combined relevance score

        [Source: docs/stories/36.8.story.md#Task-3.1]
        [Source: docs/stories/36.8.story.md#Task-3.2]
        [Source: docs/stories/36.8.story.md#Task-3.3]
        """
        if not lecture_nodes:
            return []

        # Filter to text nodes with content
        text_nodes = [
            node
            for node in lecture_nodes
            if node.get("type") == "text" and node.get("text")
        ]

        if not text_nodes:
            return []

        # Find max Y for position normalization
        max_y = max(node.get("y", 0) for node in text_nodes) if text_nodes else 1

        scored_nodes = []
        for node in text_nodes:
            node_text = node.get("text", "")
            node_color = node.get("color", "")
            y_pos = node.get("y", 0)

            # Calculate component scores
            similarity_score = self._calculate_text_similarity(
                exercise_content, node_text
            )
            position_score = self._calculate_position_score(y_pos, max_y)
            color_score = (
                self._calculate_color_priority(node_color) / 4.0
            )  # Normalize to 0-1

            # Story 36.8 Task 3.2: Weighted combination
            # Similarity: 40%, Position: 30%, Color: 30%
            relevance_score = (
                similarity_score * 0.4 + position_score * 0.3 + color_score * 0.3
            )

            scored_nodes.append(
                {
                    "id": node.get("id"),
                    "text": node_text[
                        :max_content_length
                    ],  # Task 3.3: Limit content length
                    "color": node_color,
                    "x": node.get("x", 0),
                    "y": y_pos,
                    "relevance_score": round(relevance_score, 3),
                }
            )

        # Sort by relevance score descending
        scored_nodes.sort(key=lambda n: n["relevance_score"], reverse=True)

        # Return top N nodes
        top_nodes = scored_nodes[:max_nodes]

        struct_logger.debug(
            "knowledge_points_extracted",
            total_nodes=len(text_nodes),
            selected_nodes=len(top_nodes),
            top_scores=[n["relevance_score"] for n in top_nodes],
        )

        return top_nodes

    async def enrich_with_adjacent_nodes(
        self,
        canvas_name: str,
        node_id: str,
        hop_depth: int = 1,
        include_learning_memory: bool = True,
    ) -> EnrichedContext:
        """
        Get enriched context for a node including adjacent node content.

        Args:
            canvas_name: Canvas file name
            node_id: Target node ID to enrich
            hop_depth: Number of hops to traverse (default 1-hop)
            include_learning_memory: Whether to include learning memory relations (default True)

        [Story 12.A.3: Added include_learning_memory parameter for learning memory integration]

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
            content_length=len(target_content),
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
        adjacent_nodes = self._find_adjacent_nodes(node_id, nodes, edges, hop_depth)

        # 4. Build enriched context string (adjacent nodes)
        enriched_context = self._build_enriched_context(target_node, adjacent_nodes)

        # 5. Story 12.A.3: Get learning memory relations if enabled
        learning_relations_list = []
        has_learning_refs = False
        learning_context_str = None

        if include_learning_memory and self._learning_memory_service:
            try:
                # Search learning memory using target node content as query
                node_text = target_node.get("text", "")[
                    :200
                ]  # First 200 chars as query
                learning_results = await self._search_learning_relations(
                    query=node_text, canvas_name=canvas_name, node_id=node_id
                )

                if learning_results:
                    has_learning_refs = True
                    learning_relations_list = learning_results
                    learning_context_str = self._format_learning_context(
                        learning_results
                    )
                    logger.debug(
                        f"Found {len(learning_results)} learning memory relations for {node_id}"
                    )
            except (RuntimeError, asyncio.TimeoutError, AttributeError) as e:
                logger.warning(f"Failed to get learning memory relations: {e}")
                # Continue without learning memory context (graceful degradation)

        # 8. Combine learning memory context
        if learning_context_str:
            enriched_context = f"{enriched_context}\n\n{learning_context_str}"

        # 9. Round 4 Step 2: Resolve wikilinks in target node text
        wikilink_context_str = None
        has_wikilink_refs = False
        if target_content and vault_path:
            try:
                wikilink_results = extract_and_resolve_wikilinks(
                    target_content, vault_path
                )
                resolved = [w for w in wikilink_results if w["resolved"]]
                if resolved:
                    has_wikilink_refs = True
                    parts = ["--- 引用内容 (Wikilink References) ---"]
                    for w in resolved:
                        htag = f"#{w['heading']}" if w.get("heading") else ""
                        parts.append(
                            f"[wikilink|{w['file_path']}{htag}] {w['content']}"
                        )
                    wikilink_context_str = "\n\n".join(parts)
                    enriched_context = f"{enriched_context}\n\n{wikilink_context_str}"
                    logger.debug(
                        f"Resolved {len(resolved)} wikilinks from target node {node_id}"
                    )
            except (OSError, ValueError, AttributeError) as e:
                logger.warning(f"Wikilink resolution failed for {node_id}: {e}")

        logger.debug(
            f"Enriched context for {node_id}: "
            f"{len(adjacent_nodes)} adjacent nodes found, "
            f"learning_refs={has_learning_refs}, "
            f"wikilink_refs={has_wikilink_refs}, "
            f"incoming={len(incoming_edges)}, outgoing={len(outgoing_edges)}, "
            f"siblings={len(sibling_nodes_list)}"
        )

        # Story 21.2 + 12.A.3: Return EnrichedContext with all fields populated
        return EnrichedContext(
            target_node=target_node,
            adjacent_nodes=adjacent_nodes,
            enriched_context=enriched_context,
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
            # Story 12.A.3: Learning memory relations
            learning_relations=learning_relations_list,
            has_learning_refs=has_learning_refs,
            # Round 4 Step 2: Wikilink references
            wikilink_context=wikilink_context_str,
            has_wikilink_refs=has_wikilink_refs,
        )

    def _find_adjacent_nodes(
        self,
        node_id: str,
        nodes: Dict[str, Dict[str, Any]],
        edges: List[Dict[str, Any]],
        hop_depth: int = 1,
        visited: Optional[Set[str]] = None,
        current_hop: int = 1,
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
                        adjacent.append(
                            AdjacentNode(
                                node=child_node,
                                relation="child",
                                edge_label=label,
                                hop_distance=current_hop,
                            )
                        )

            elif to_node == node_id:
                # Parent → Target (incoming edge)
                # Story 12.E.3: Check visited to prevent cycles
                if from_node not in visited:
                    parent_node = nodes.get(from_node)
                    if parent_node:
                        visited.add(from_node)
                        adjacent.append(
                            AdjacentNode(
                                node=parent_node,
                                relation="parent",
                                edge_label=label,
                                hop_distance=current_hop,
                            )
                        )

        # Story 12.E.3: Recurse for 2-hop if needed
        if hop_depth >= 2 and current_hop < hop_depth:
            hop1_node_ids = [
                adj.node.get("id") for adj in adjacent if adj.node.get("id")
            ]

            for hop1_node_id in hop1_node_ids:
                hop2_nodes = self._find_adjacent_nodes(
                    node_id=hop1_node_id,
                    nodes=nodes,
                    edges=edges,
                    hop_depth=hop_depth,
                    visited=visited,
                    current_hop=current_hop + 1,
                )
                adjacent.extend(hop2_nodes)

        # Story 12.E.3: Sort by hop_distance (closer nodes first)
        adjacent.sort(key=lambda x: x.hop_distance)

        return adjacent

    def _build_enriched_context(
        self, target_node: Dict[str, Any], adjacent_nodes: List[AdjacentNode]
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
        parents_1hop = [
            n for n in adjacent_nodes if n.relation == "parent" and n.hop_distance == 1
        ]
        parents_2hop = [
            n for n in adjacent_nodes if n.relation == "parent" and n.hop_distance == 2
        ]
        children_1hop = [
            n for n in adjacent_nodes if n.relation == "child" and n.hop_distance == 1
        ]
        children_2hop = [
            n for n in adjacent_nodes if n.relation == "child" and n.hop_distance == 2
        ]

        if parents_1hop or parents_2hop:
            parts.append("\n--- 前置知识 (Parent Nodes) ---")
            # Story 12.E.3: Add 1-hop parents first
            for adj in parents_1hop:
                # Story 12.D.2: Use get_node_content() for adjacent nodes too
                node_text = get_node_content(adj.node, vault_path)[
                    :300
                ]  # Truncate long text
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
                node_text = get_node_content(adj.node, vault_path)[
                    :300
                ]  # Truncate long text
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

    async def _search_learning_relations(
        self,
        query: str,
        canvas_name: Optional[str] = None,
        node_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search learning memory for related concepts and historical records.

        Uses LearningMemoryClient.search_memories() (Neo4j-backed) to find
        relevant historical learning records for additional agent context.

        [Source: Story 12.A.3 AC4 - Agent receives learning memory concepts]
        [Source: Story 12.A.3 Task 2 - Integrate learning memory service]

        Args:
            query: Search query (typically node text content)
            canvas_name: Optional filter by canvas name
            node_id: Optional filter by node ID

        Returns:
            List of related memory dicts with relevance scores
        """
        if not self._learning_memory_service:
            logger.warning(
                "_search_learning_relations: learning_memory_service not available, returning empty"
            )
            return []

        try:
            # Initialize service if needed
            await self._learning_memory_service.initialize()

            # Search for related memories
            results = await self._learning_memory_service.search_memories(
                query=query,
                canvas_name=canvas_name,
                node_id=node_id,
                limit=5,  # Limit to top 5 most relevant
            )

            logger.debug(
                f"Learning memory search for '{query[:50]}...': {len(results)} results"
            )
            return results

        except (RuntimeError, asyncio.TimeoutError, AttributeError) as e:
            logger.warning(f"Learning memory search failed: {e}")
            return []

    def _format_learning_context(self, learning_results: List[Dict[str, Any]]) -> str:
        """
        Format learning memory results for inclusion in enriched context.

        Formats historical learning memories as context for the agent prompt.

        FR-KG-04 Phase 9 Task 9.4: scan every chunk's user_understanding
        preview through ``check_input`` before concatenation. Because these
        chunks originate from historical user notes and may be attacker-
        controlled when shared vaults enter the picture, we cannot trust
        them as "internal" data. Any chunk that trips the injection
        classifier is replaced with a ``[filtered: suspicious content]``
        marker so the downstream agent prompt never ingests it.

        [Source: Story 12.A.3 AC4 - Format learning memory relations for agent]

        Args:
            learning_results: List of memory dicts from search_memories()

        Returns:
            Formatted learning memory context string
        """
        if not learning_results:
            return ""

        # FR-KG-04 Phase 9 Task 9.4: import lazily to avoid circular imports
        from app.middleware.prompt_injection_guard import check_input

        parts = ["--- 历史学习记忆 (Learning Memory) ---"]

        for memory in learning_results:
            concept = memory.get("concept", "未知概念")
            relevance = memory.get("relevance", 0.0)
            timestamp = (
                memory.get("timestamp", "")[:10] if memory.get("timestamp") else ""
            )
            score = memory.get("score")
            understanding = memory.get("user_understanding", "")

            # Format entry with relevance and optional score
            entry = f"[memory|{relevance:.0%}] {concept}"
            if timestamp:
                entry = f"[{timestamp}] " + entry
            if score is not None:
                entry += f" (得分: {score:.1f}/40)"

            parts.append(entry)

            # Add brief understanding preview if available.
            # Phase 9 Task 9.4: scan before concatenation. The chunk may be
            # attacker-controlled in shared-vault or imported-note flows.
            if understanding:
                understanding_check = check_input(understanding)
                if understanding_check.is_blocked:
                    parts.append("  历史理解: [filtered: suspicious content]")
                else:
                    preview = (
                        understanding[:100] + "..."
                        if len(understanding) > 100
                        else understanding
                    )
                    parts.append(f"  历史理解: {preview}")

        return "\n".join(parts)

    def build_agent_prompt(
        self, base_prompt: str, context: Optional[EnrichedContext]
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
