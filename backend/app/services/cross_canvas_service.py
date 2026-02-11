# Canvas Learning System - Cross Canvas Service
# Story 25.3: Exercise-Lecture Canvas Association
# Story 36.5: 跨Canvas讲座关联持久化
"""
CrossCanvasService - Manages cross-canvas associations.

Provides:
- CRUD operations for canvas associations
- Association queries by canvas path and relation type
- Intelligent lecture canvas suggestions for exercise canvases
- Neo4j persistence for associations (Story 36.5)

[Source: Story 25.3 - Exercise-Lecture Canvas Association]
[Source: Epic 16 - 跨Canvas关联学习系统]
[Source: Story 36.5 - 跨Canvas讲座关联持久化]
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Dict, List, Optional, Set
from uuid import uuid4

if TYPE_CHECKING:
    from app.clients.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Association Type Mapping
# Story 36.5 Task 2.5: Map relationship_type to Schema enum values
# [Source: specs/data/canvas-association.schema.json]
# ═══════════════════════════════════════════════════════════════════════════════

# Schema-defined association_type enum values
VALID_ASSOCIATION_TYPES = ["prerequisite", "related", "extends", "references"]

# Mapping from legacy relationship_type to schema association_type
RELATIONSHIP_TYPE_MAPPING = {
    "exercise_lecture": "prerequisite",  # Exercise requires lecture knowledge
    "lecture_exercise": "extends",        # Exercise extends lecture content
    "prerequisite": "prerequisite",
    "related": "related",
    "extends": "extends",
    "references": "references",
    "similar": "related",
    "continuation": "extends",
}


def map_to_association_type(relationship_type: str) -> str:
    """
    Map legacy relationship_type to Schema association_type enum value.

    Story 36.5 Task 2.5: association_type到Schema枚举值的映射

    Args:
        relationship_type: Legacy relationship type string

    Returns:
        Valid Schema association_type (prerequisite|related|extends|references)

    [Source: docs/stories/36.5.story.md#Task-2.5]
    [Source: specs/data/canvas-association.schema.json]
    """
    mapped = RELATIONSHIP_TYPE_MAPPING.get(relationship_type.lower(), "related")
    if mapped not in VALID_ASSOCIATION_TYPES:
        logger.warning(
            f"Unknown relationship_type '{relationship_type}', defaulting to 'related'"
        )
        return "related"
    return mapped


def map_from_association_type(association_type: str) -> str:
    """
    Map Schema association_type back to legacy relationship_type for compatibility.

    Args:
        association_type: Schema association_type

    Returns:
        Legacy relationship_type string
    """
    # For now, return as-is since association_type values are valid relationship_types
    return association_type


# ═══════════════════════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CrossCanvasAssociation:
    """Internal representation of a cross-canvas association."""
    id: str
    source_canvas_path: str
    source_canvas_title: str
    target_canvas_path: str
    target_canvas_title: str
    relationship_type: str
    common_concepts: List[str] = field(default_factory=list)
    confidence: float = 0.5
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class CanvasAssociationSuggestion:
    """A suggested canvas association with confidence score.

    [Source: Story 25.3 AC5 - Batch association suggestions]
    """
    target_canvas_path: str
    target_canvas_title: str
    relationship_type: str
    confidence: float
    reason: str  # Why this suggestion was made


@dataclass
class AutoDiscoverySuggestion:
    """
    A suggested canvas association from auto-discovery.

    Story 36.6 AC-3: Includes confidence score and association reason.

    [Source: docs/stories/36.6.story.md#Task-3.3]
    """
    source_canvas: str
    target_canvas: str
    association_type: str
    confidence: float
    reason: str
    shared_concepts: List[str] = field(default_factory=list)
    auto_generated: bool = True


@dataclass
class AutoDiscoveryResult:
    """
    Result of auto-discovery batch scan.

    Story 36.6 AC-4: Batch auto-discovery response.

    [Source: docs/stories/36.6.story.md#Task-4.3]
    """
    suggestions: List[AutoDiscoverySuggestion] = field(default_factory=list)
    total_scanned: int = 0
    discovered_count: int = 0


@dataclass
class KnowledgePathNode:
    """Node in a knowledge learning path."""
    canvas_path: str
    canvas_title: str
    order: int
    prerequisite_concepts: List[str] = field(default_factory=list)
    mastery_level: float = 0.0
    is_completed: bool = False


@dataclass
class KnowledgePath:
    """A learning path connecting multiple canvases."""
    id: str
    name: str
    description: str
    nodes: List[KnowledgePathNode] = field(default_factory=list)
    completion_progress: float = 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# CrossCanvasService
# ═══════════════════════════════════════════════════════════════════════════════

class CrossCanvasService:
    """
    Service for managing cross-canvas associations.

    Provides:
    - CRUD operations for associations
    - Query by canvas path and relation type
    - Intelligent lecture canvas suggestions
    - Neo4j persistence for associations (Story 36.5)

    [Source: Story 25.3 - Exercise-Lecture Canvas Association]
    [Source: Story 36.5 - 跨Canvas讲座关联持久化]
    """

    # Patterns for identifying exercise vs lecture canvases
    # ✅ Verified from Story 25.3 Task 3.2: Canvas file name pattern matching
    # ✅ Enhanced in Story 36.6 Task 1.1: Extended patterns with 真题, 模拟, 知识点, 概念
    EXERCISE_PATTERNS = [
        r'题目', r'习题', r'练习', r'作业', r'exam', r'exercise', r'problem',
        r'quiz', r'test', r'期末', r'期中', r'复习题', r'真题', r'模拟'
    ]
    LECTURE_PATTERNS = [
        r'讲座', r'讲义', r'课程', r'lecture', r'lesson', r'chapter',
        r'笔记', r'notes', r'教材', r'textbook', r'知识点', r'概念'
    ]

    def __init__(
        self,
        neo4j_client: Optional["Neo4jClient"] = None,
        storage_path: Optional[str] = None
    ):
        """
        Initialize CrossCanvasService.

        Story 36.5 AC-1, AC-2: Inject Neo4jClient for persistence.

        Args:
            neo4j_client: Neo4jClient instance for persistence (Story 36.5)
            storage_path: Optional path for legacy storage (deprecated)

        [Source: docs/stories/36.5.story.md#Task-2.2]
        """
        self._neo4j_client = neo4j_client
        self._knowledge_paths: Dict[str, KnowledgePath] = {}
        self._storage_path = storage_path
        self._initialized = False

        # In-memory cache for associations (populated from Neo4j on startup)
        # Story 36.5 AC-4: Load from Neo4j at startup
        self._associations_cache: Dict[str, CrossCanvasAssociation] = {}

        logger.info(
            f"CrossCanvasService initialized, "
            f"neo4j_client={'injected' if neo4j_client else 'None'}, "
            f"storage_path={storage_path}"
        )

    async def initialize(self) -> bool:
        """
        Initialize service and load associations from Neo4j.

        Story 36.5 AC-4: 启动时从Neo4j加载已有关联

        Returns:
            True if initialization successful

        [Source: docs/stories/36.5.story.md#Task-3.1]
        """
        if self._initialized:
            return True

        if self._neo4j_client:
            try:
                await self._load_associations_from_neo4j()
                self._initialized = True
                logger.info(
                    f"CrossCanvasService initialized with {len(self._associations_cache)} "
                    f"associations loaded from Neo4j"
                )
            except Exception as e:
                logger.error(f"Failed to load associations from Neo4j: {e}")
                self._initialized = True  # Continue without Neo4j data
        else:
            self._initialized = True
            logger.warning("CrossCanvasService initialized without Neo4j client")

        return True

    async def _load_associations_from_neo4j(self) -> None:
        """
        Load all canvas associations from Neo4j into cache.

        Story 36.5 AC-4: 启动时从Neo4j加载已有关联

        [Source: docs/stories/36.5.story.md#Task-3.2]
        """
        if not self._neo4j_client:
            return

        associations = await self._neo4j_client.load_all_canvas_associations()

        for assoc_data in associations:
            association_id = assoc_data.get("association_id")
            if not association_id:
                continue

            # Convert Neo4j data to CrossCanvasAssociation dataclass
            try:
                created_at = assoc_data.get("created_at")
                updated_at = assoc_data.get("updated_at")

                # Handle datetime conversion
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                elif created_at is None:
                    created_at = datetime.now(timezone.utc)

                if isinstance(updated_at, str):
                    updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                elif updated_at is None:
                    updated_at = datetime.now(timezone.utc)

                source_path = assoc_data.get("source_canvas", "")
                target_path = assoc_data.get("target_canvas", "")

                association = CrossCanvasAssociation(
                    id=association_id,
                    source_canvas_path=source_path,
                    source_canvas_title=self.extract_canvas_title(source_path),
                    target_canvas_path=target_path,
                    target_canvas_title=self.extract_canvas_title(target_path),
                    relationship_type=map_from_association_type(
                        assoc_data.get("association_type", "related")
                    ),
                    common_concepts=assoc_data.get("shared_concepts", []),
                    confidence=assoc_data.get("confidence", 0.5),
                    created_at=created_at,
                    updated_at=updated_at
                )

                self._associations_cache[association_id] = association

            except Exception as e:
                logger.warning(f"Failed to parse association {association_id}: {e}")

        logger.info(f"Loaded {len(self._associations_cache)} associations from Neo4j")

    # ═══════════════════════════════════════════════════════════════════════════
    # Helper Methods
    # ═══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def extract_canvas_title(canvas_path: str) -> str:
        """Extract title from canvas file path."""
        if not canvas_path:
            return "Unknown Canvas"
        parts = canvas_path.replace("\\", "/").split("/")
        filename = parts[-1]
        return filename.replace(".canvas", "")

    def _is_exercise_canvas(self, canvas_path: str) -> bool:
        """Check if canvas path matches exercise patterns."""
        path_lower = canvas_path.lower()
        return any(re.search(pattern, path_lower) for pattern in self.EXERCISE_PATTERNS)

    def _is_lecture_canvas(self, canvas_path: str) -> bool:
        """Check if canvas path matches lecture patterns."""
        path_lower = canvas_path.lower()
        return any(re.search(pattern, path_lower) for pattern in self.LECTURE_PATTERNS)

    def discover_canvas_type(self, canvas_path: str) -> str:
        """
        Discover the type of canvas based on filename patterns.

        Story 36.6 Task 1.2: Canvas type discovery method.

        Checks filename against exercise and lecture patterns to determine type.
        Supports Chinese and English mixed filenames.

        Args:
            canvas_path: Canvas file path

        Returns:
            'exercise' if matches exercise patterns,
            'lecture' if matches lecture patterns,
            'unknown' if no match

        [Source: docs/stories/36.6.story.md#Task-1.2]
        """
        if self._is_exercise_canvas(canvas_path):
            return "exercise"
        elif self._is_lecture_canvas(canvas_path):
            return "lecture"
        else:
            return "unknown"

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two canvas names.

        Uses simple character-based similarity for MVP.
        Can be enhanced with semantic similarity later.
        """
        # Extract base names (remove common prefixes/suffixes)
        clean1 = re.sub(r'(题目|习题|练习|讲座|讲义|课程)[-_]?', '', name1.lower())
        clean2 = re.sub(r'(题目|习题|练习|讲座|讲义|课程)[-_]?', '', name2.lower())

        if not clean1 or not clean2:
            return 0.0

        # Simple character overlap ratio
        set1 = set(clean1)
        set2 = set(clean2)
        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def _extract_subject_from_path(self, canvas_path: str) -> Optional[str]:
        """Extract subject/topic from canvas path."""
        title = self.extract_canvas_title(canvas_path)
        # Remove common prefixes/suffixes
        subject = re.sub(
            r'(题目|习题|练习|讲座|讲义|课程|期末|期中|复习)[-_]?',
            '',
            title
        )
        return subject.strip() if subject.strip() else None

    # ═══════════════════════════════════════════════════════════════════════════
    # CRUD Operations
    # ═══════════════════════════════════════════════════════════════════════════

    async def create_association(
        self,
        source_canvas_path: str,
        target_canvas_path: str,
        relationship_type: str,
        common_concepts: Optional[List[str]] = None,
        confidence: float = 0.5
    ) -> CrossCanvasAssociation:
        """
        Create a new cross-canvas association.

        Story 36.5 AC-1, AC-2, AC-3: Persist to Neo4j with ASSOCIATED_WITH relationship.

        [Source: Story 25.3 AC1 - Create exercise-lecture Canvas association]
        [Source: docs/stories/36.5.story.md#Task-2.3]

        Args:
            source_canvas_path: Source canvas file path
            target_canvas_path: Target canvas file path
            relationship_type: Type of relationship (e.g., "exercise_lecture")
            common_concepts: List of common concepts between canvases
            confidence: Confidence score (0-1)

        Returns:
            Created CrossCanvasAssociation
        """
        association_id = f"cca-{uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        # Map relationship_type to Schema association_type
        # Story 36.5 Task 2.5
        association_type = map_to_association_type(relationship_type)

        association = CrossCanvasAssociation(
            id=association_id,
            source_canvas_path=source_canvas_path,
            source_canvas_title=self.extract_canvas_title(source_canvas_path),
            target_canvas_path=target_canvas_path,
            target_canvas_title=self.extract_canvas_title(target_canvas_path),
            relationship_type=relationship_type,
            common_concepts=common_concepts or [],
            confidence=confidence,
            created_at=now,
            updated_at=now
        )

        # Story 36.5 AC-1, AC-3: Persist to Neo4j
        if self._neo4j_client:
            try:
                await self._neo4j_client.create_canvas_association(
                    association_id=association_id,
                    source_canvas=source_canvas_path,
                    target_canvas=target_canvas_path,
                    association_type=association_type,
                    confidence=confidence,
                    shared_concepts=common_concepts,
                    bidirectional=False,
                    auto_generated=False
                )
            except Exception as e:
                logger.error(f"Failed to persist association to Neo4j: {e}")
                # Continue with in-memory storage as fallback

        # Update in-memory cache
        self._associations_cache[association_id] = association
        logger.info(
            f"Created association {association_id}: "
            f"{source_canvas_path} -[{relationship_type}]-> {target_canvas_path}"
        )

        return association

    async def get_association(self, association_id: str) -> Optional[CrossCanvasAssociation]:
        """Get association by ID from cache."""
        return self._associations_cache.get(association_id)

    async def update_association(
        self,
        association_id: str,
        relationship_type: Optional[str] = None,
        common_concepts: Optional[List[str]] = None,
        confidence: Optional[float] = None
    ) -> Optional[CrossCanvasAssociation]:
        """
        Update an existing association.

        Story 36.5 AC-3: Persist update to Neo4j.

        [Source: Story 25.3 AC4 - Support confidence scoring]
        [Source: docs/stories/36.5.story.md#Task-2.3]
        """
        if association_id not in self._associations_cache:
            return None

        association = self._associations_cache[association_id]

        # Map relationship_type to Schema association_type if provided
        association_type = None
        if relationship_type is not None:
            association.relationship_type = relationship_type
            association_type = map_to_association_type(relationship_type)

        if common_concepts is not None:
            association.common_concepts = common_concepts
        if confidence is not None:
            association.confidence = confidence

        association.updated_at = datetime.now(timezone.utc)

        # Story 36.5 AC-3: Persist update to Neo4j
        if self._neo4j_client:
            try:
                await self._neo4j_client.update_canvas_association(
                    association_id=association_id,
                    association_type=association_type,
                    confidence=confidence,
                    shared_concepts=common_concepts
                )
            except Exception as e:
                logger.error(f"Failed to persist association update to Neo4j: {e}")

        logger.info(f"Updated association {association_id}")
        return association

    async def delete_association(self, association_id: str) -> bool:
        """
        Delete an association.

        Story 36.5 AC-3: Delete from Neo4j.

        [Source: docs/stories/36.5.story.md#Task-2.3]
        """
        if association_id not in self._associations_cache:
            return False

        # Story 36.5 AC-3: Delete from Neo4j
        if self._neo4j_client:
            try:
                await self._neo4j_client.delete_canvas_association(association_id)
            except Exception as e:
                logger.error(f"Failed to delete association from Neo4j: {e}")

        del self._associations_cache[association_id]
        logger.info(f"Deleted association {association_id}")
        return True

    async def list_associations(
        self,
        canvas_path: Optional[str] = None
    ) -> List[CrossCanvasAssociation]:
        """
        List all associations, optionally filtered by canvas path.

        Args:
            canvas_path: Optional canvas path to filter by (source or target)

        Returns:
            List of associations sorted by updated_at descending
        """
        associations = list(self._associations_cache.values())

        if canvas_path:
            associations = [
                a for a in associations
                if a.source_canvas_path == canvas_path or a.target_canvas_path == canvas_path
            ]

        return sorted(associations, key=lambda a: a.updated_at, reverse=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # Query Methods
    # ═══════════════════════════════════════════════════════════════════════════

    async def get_associated_canvases(
        self,
        canvas_path: str,
        relation_type: Optional[str] = None
    ) -> List[CrossCanvasAssociation]:
        """
        Get all canvases associated with the given canvas.

        Story 36.5 AC-4: Query from cache (loaded from Neo4j at startup).

        [Source: Story 25.3 Task 2.3 - Add get_associated_canvases method]
        [Source: docs/stories/36.5.story.md#Task-2.4]

        Args:
            canvas_path: Canvas file path to find associations for
            relation_type: Optional filter by relationship type (e.g., "exercise_lecture")

        Returns:
            List of associations where canvas_path is source or target
        """
        associations = []

        for assoc in self._associations_cache.values():
            # Check if canvas is source or target
            is_match = (
                assoc.source_canvas_path == canvas_path or
                assoc.target_canvas_path == canvas_path
            )

            if not is_match:
                continue

            # Filter by relation type if specified
            if relation_type and assoc.relationship_type != relation_type:
                continue

            associations.append(assoc)

        # Sort by confidence descending
        return sorted(associations, key=lambda a: a.confidence, reverse=True)

    async def get_lecture_for_exercise(
        self,
        exercise_canvas_path: str
    ) -> Optional[CrossCanvasAssociation]:
        """
        Get the associated lecture canvas for an exercise canvas.

        Story 36.8 AC1, AC6: First tries Neo4j, falls back to in-memory.

        [Source: Story 25.3 AC2 - Auto-retrieve lecture content]
        [Source: docs/stories/36.8.story.md#Task-2.3]

        Args:
            exercise_canvas_path: Path to the exercise canvas

        Returns:
            The highest-confidence exercise_lecture association, or None
        """
        # Story 36.8 Task 2.1: Try Neo4j first
        association = await self.get_lecture_for_exercise_neo4j(exercise_canvas_path)

        if association:
            return association

        # Story 36.8 Task 2.3: Fallback to in-memory cache
        logger.debug(
            f"Neo4j lookup returned None for {exercise_canvas_path}, "
            "falling back to in-memory cache"
        )
        return await self._get_lecture_for_exercise_memory(exercise_canvas_path)

    async def get_lecture_for_exercise_neo4j(
        self,
        exercise_canvas_path: str
    ) -> Optional[CrossCanvasAssociation]:
        """
        Query Neo4j for the associated lecture canvas.

        Story 36.8 Task 2.1, 2.2: Neo4j-backed association lookup.

        Uses Cypher query to find ASSOCIATED_WITH relationship where
        the exercise canvas is the source.

        Args:
            exercise_canvas_path: Path to the exercise canvas

        Returns:
            CrossCanvasAssociation if found in Neo4j, None otherwise

        [Source: docs/stories/36.8.story.md#Task-2.1]
        [Source: docs/stories/36.8.story.md#Task-2.2]
        """
        if not self._neo4j_client:
            logger.debug("Neo4j client not available, skipping Neo4j lookup")
            return None

        try:
            # Story 36.8 Task 2.2: Cypher query for lecture association
            # Query for ASSOCIATED_WITH relationship where exercise is source
            # and association_type is 'prerequisite' (exercise requires lecture)
            query = """
            MATCH (e:Canvas {path: $exercise_path})
                  -[r:ASSOCIATED_WITH]->
                  (l:Canvas)
            WHERE r.association_type IN ['prerequisite', 'related']
              AND r.confidence >= 0.6
            RETURN l.path AS lecture_path,
                   l.title AS lecture_title,
                   r.association_id AS association_id,
                   r.association_type AS association_type,
                   r.confidence AS confidence,
                   r.shared_concepts AS common_concepts,
                   r.created_at AS created_at,
                   r.updated_at AS updated_at
            ORDER BY r.confidence DESC
            LIMIT 1
            """

            results = await self._neo4j_client.run_query(
                query,
                exercise_path=exercise_canvas_path
            )

            if results and len(results) > 0:
                result = results[0]
                lecture_path = result.get("lecture_path", "")

                # Convert Neo4j result to CrossCanvasAssociation
                association = CrossCanvasAssociation(
                    id=result.get("association_id", f"neo4j-{exercise_canvas_path[:20]}"),
                    source_canvas_path=exercise_canvas_path,
                    source_canvas_title=self.extract_canvas_title(exercise_canvas_path),
                    target_canvas_path=lecture_path,
                    target_canvas_title=result.get("lecture_title") or self.extract_canvas_title(lecture_path),
                    relationship_type="exercise_lecture",
                    common_concepts=result.get("common_concepts", []) or [],
                    confidence=result.get("confidence", 0.5)
                )

                logger.info(
                    f"Neo4j: Found lecture association for {exercise_canvas_path}: "
                    f"{lecture_path} (confidence: {association.confidence:.2f})"
                )
                return association

        except Exception as e:
            logger.warning(
                f"Neo4j query failed for lecture lookup: {e}, "
                "will fall back to in-memory cache"
            )

        return None

    async def _get_lecture_for_exercise_memory(
        self,
        exercise_canvas_path: str
    ) -> Optional[CrossCanvasAssociation]:
        """
        Fallback: Get lecture association from in-memory cache.

        Story 36.8 Task 2.3: In-memory fallback when Neo4j unavailable.

        Args:
            exercise_canvas_path: Path to the exercise canvas

        Returns:
            CrossCanvasAssociation from cache if found, None otherwise

        [Source: docs/stories/36.8.story.md#Task-2.3]
        """
        associations = await self.get_associated_canvases(
            exercise_canvas_path,
            relation_type="exercise_lecture"
        )

        # Find where exercise is the source
        for assoc in associations:
            if assoc.source_canvas_path == exercise_canvas_path:
                return assoc

        return None

    # ═══════════════════════════════════════════════════════════════════════════
    # Intelligent Suggestion Methods
    # ═══════════════════════════════════════════════════════════════════════════

    async def suggest_lecture_canvas(
        self,
        exercise_canvas_path: str,
        concept: Optional[str] = None,
        available_canvases: Optional[List[str]] = None
    ) -> List[CanvasAssociationSuggestion]:
        """
        Suggest lecture canvases for an exercise canvas.

        [Source: Story 25.3 Task 2.4 - Add suggest_lecture_canvas method]
        [Source: Story 25.3 AC5 - Batch association suggestions]

        Algorithm:
        1. Extract subject from exercise canvas name
        2. Match against lecture canvas names using pattern matching
        3. Check historical associations for similar exercises
        4. Return ranked suggestions with confidence scores

        Args:
            exercise_canvas_path: Path to the exercise canvas
            concept: Optional specific concept to focus on
            available_canvases: Optional list of available canvas paths to consider

        Returns:
            List of CanvasAssociationSuggestion sorted by confidence
        """
        suggestions: List[CanvasAssociationSuggestion] = []
        exercise_title = self.extract_canvas_title(exercise_canvas_path)
        exercise_subject = self._extract_subject_from_path(exercise_canvas_path)

        logger.info(
            f"Suggesting lecture canvases for exercise: {exercise_canvas_path}, "
            f"subject={exercise_subject}, concept={concept}"
        )

        # Strategy 1: Historical association learning
        # Look for canvases that were previously associated with similar exercises
        historical_targets = await self._find_historical_lecture_targets()

        for target_path, score in historical_targets.items():
            if self._is_lecture_canvas(target_path):
                suggestions.append(CanvasAssociationSuggestion(
                    target_canvas_path=target_path,
                    target_canvas_title=self.extract_canvas_title(target_path),
                    relationship_type="exercise_lecture",
                    confidence=min(0.6 + score * 0.2, 0.9),  # 0.6-0.9 range
                    reason="历史关联: 该讲座Canvas曾与类似练习Canvas关联"
                ))

        # Strategy 2: Name similarity matching
        if available_canvases:
            for canvas_path in available_canvases:
                # Skip self and non-lecture canvases
                if canvas_path == exercise_canvas_path:
                    continue
                if not self._is_lecture_canvas(canvas_path):
                    continue

                canvas_title = self.extract_canvas_title(canvas_path)
                similarity = self._calculate_name_similarity(exercise_title, canvas_title)

                if similarity > 0.3:  # Threshold for name similarity
                    # Check if not already suggested
                    existing = next(
                        (s for s in suggestions if s.target_canvas_path == canvas_path),
                        None
                    )
                    if existing:
                        # Update confidence if higher
                        existing.confidence = max(existing.confidence, 0.4 + similarity * 0.4)
                    else:
                        suggestions.append(CanvasAssociationSuggestion(
                            target_canvas_path=canvas_path,
                            target_canvas_title=canvas_title,
                            relationship_type="exercise_lecture",
                            confidence=0.4 + similarity * 0.4,  # 0.4-0.8 range
                            reason=f"名称相似度: {similarity:.1%}"
                        ))

        # Strategy 3: Subject/topic matching
        if exercise_subject and available_canvases:
            for canvas_path in available_canvases:
                if canvas_path == exercise_canvas_path:
                    continue

                canvas_subject = self._extract_subject_from_path(canvas_path)
                if canvas_subject and exercise_subject.lower() in canvas_subject.lower():
                    existing = next(
                        (s for s in suggestions if s.target_canvas_path == canvas_path),
                        None
                    )
                    if existing:
                        existing.confidence = max(existing.confidence, 0.7)
                        existing.reason += f"; 主题匹配: {canvas_subject}"
                    else:
                        suggestions.append(CanvasAssociationSuggestion(
                            target_canvas_path=canvas_path,
                            target_canvas_title=self.extract_canvas_title(canvas_path),
                            relationship_type="exercise_lecture",
                            confidence=0.7,
                            reason=f"主题匹配: {exercise_subject}"
                        ))

        # Sort by confidence descending
        suggestions.sort(key=lambda s: s.confidence, reverse=True)

        # Limit to top 5 suggestions
        return suggestions[:5]

    async def _find_historical_lecture_targets(self) -> Dict[str, float]:
        """
        Find lecture canvases that have been frequently associated.

        Returns:
            Dict mapping canvas_path to frequency score (0-1)
        """
        target_counts: Dict[str, int] = {}

        for assoc in self._associations_cache.values():
            if assoc.relationship_type == "exercise_lecture":
                target = assoc.target_canvas_path
                target_counts[target] = target_counts.get(target, 0) + 1

        # Normalize to 0-1
        if not target_counts:
            return {}

        max_count = max(target_counts.values())
        return {
            path: count / max_count
            for path, count in target_counts.items()
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # Auto-Discovery Methods
    # Story 36.6: 跨Canvas讲座自动发现
    # ═══════════════════════════════════════════════════════════════════════════

    def calculate_discovery_confidence(
        self,
        name_match: bool,
        common_concepts: List[str]
    ) -> float:
        """
        Calculate association confidence score for auto-discovery.

        Story 36.6 Task 3.3: Confidence calculation formula.

        Formula:
        - File name pattern match: +0.4
        - Each common concept: +0.15 (max +0.55)
        - Maximum total: 0.95

        Args:
            name_match: Whether filename patterns match (exercise-lecture pair)
            common_concepts: List of common concepts between canvases

        Returns:
            Confidence score between 0.0 and 0.95

        [Source: docs/stories/36.6.story.md#Task-3.3]
        """
        confidence = 0.0

        if name_match:
            confidence += 0.4

        # +0.15 per common concept, max +0.55
        concept_bonus = min(len(common_concepts) * 0.15, 0.55)
        confidence += concept_bonus

        return min(confidence, 0.95)

    def _generate_discovery_reason(
        self,
        name_match: bool,
        source_type: str,
        target_type: str,
        common_concepts: List[str]
    ) -> str:
        """
        Generate human-readable reason for auto-discovered association.

        Story 36.6 Task 3.4: Association reason description.

        Args:
            name_match: Whether filename patterns match
            source_type: Source canvas type (exercise/lecture/unknown)
            target_type: Target canvas type (exercise/lecture/unknown)
            common_concepts: List of common concepts

        Returns:
            Human-readable reason string

        [Source: docs/stories/36.6.story.md#Task-3.4]
        """
        reasons = []

        if name_match:
            reasons.append(f"文件名模式匹配: {source_type} + {target_type}")

        if common_concepts:
            concept_count = len(common_concepts)
            concept_preview = ", ".join(common_concepts[:3])
            if concept_count > 3:
                concept_preview += f" 等{concept_count}个"
            reasons.append(f"共同概念: [{concept_preview}]")

        return "; ".join(reasons) if reasons else "无明确关联原因"

    async def auto_discover_associations(
        self,
        canvas_paths: List[str],
        min_common_concepts: int = 3,
        include_existing: bool = False
    ) -> AutoDiscoveryResult:
        """
        Auto-discover associations between canvases.

        Story 36.6 Task 3.1, 3.2: Automatic association discovery algorithm.

        Algorithm:
        1. Identify canvas types (exercise/lecture/unknown)
        2. For each potential pair, check:
           a. Filename pattern match (exercise + lecture pair)
           b. Common concepts >= min_common_concepts
        3. Calculate confidence score
        4. Generate association suggestions

        Args:
            canvas_paths: List of canvas file paths to analyze
            min_common_concepts: Minimum common concepts for suggestion (default: 3)
            include_existing: Include already associated canvases (default: False)

        Returns:
            AutoDiscoveryResult with suggestions, total_scanned, discovered_count

        [Source: docs/stories/36.6.story.md#Task-3.1]
        """
        result = AutoDiscoveryResult(
            total_scanned=len(canvas_paths),
            discovered_count=0
        )

        if len(canvas_paths) < 2:
            return result

        # Get existing associations if we need to filter them out
        existing_pairs: Set[tuple] = set()
        if not include_existing:
            for assoc in self._associations_cache.values():
                existing_pairs.add((assoc.source_canvas_path, assoc.target_canvas_path))
                existing_pairs.add((assoc.target_canvas_path, assoc.source_canvas_path))

        # Categorize canvases by type
        exercise_canvases = []
        lecture_canvases = []
        unknown_canvases = []

        for path in canvas_paths:
            canvas_type = self.discover_canvas_type(path)
            if canvas_type == "exercise":
                exercise_canvases.append(path)
            elif canvas_type == "lecture":
                lecture_canvases.append(path)
            else:
                unknown_canvases.append(path)

        logger.info(
            f"Auto-discovery: {len(exercise_canvases)} exercise, "
            f"{len(lecture_canvases)} lecture, {len(unknown_canvases)} unknown canvases"
        )

        # Cache for concepts per canvas (for performance)
        concept_cache: Dict[str, List[str]] = {}

        async def get_concepts_cached(canvas_path: str) -> List[str]:
            if canvas_path not in concept_cache:
                if self._neo4j_client:
                    concept_cache[canvas_path] = await self._neo4j_client.get_canvas_concepts(
                        canvas_path
                    )
                else:
                    concept_cache[canvas_path] = []
            return concept_cache[canvas_path]

        # Strategy 1: Exercise-Lecture pairs (name pattern match = True)
        for exercise_path in exercise_canvases:
            for lecture_path in lecture_canvases:
                # Skip existing associations
                if (exercise_path, lecture_path) in existing_pairs:
                    continue

                # Get common concepts
                common_concepts = []
                if self._neo4j_client:
                    common_concepts = await self._neo4j_client.find_common_concepts(
                        exercise_path, lecture_path
                    )

                # Check if meets minimum common concepts or has name match
                name_match = True  # Exercise + Lecture pair
                confidence = self.calculate_discovery_confidence(name_match, common_concepts)

                # Suggest if confidence >= 0.4 (name match alone) or has enough concepts
                if confidence >= 0.4 or len(common_concepts) >= min_common_concepts:
                    suggestion = AutoDiscoverySuggestion(
                        source_canvas=exercise_path,
                        target_canvas=lecture_path,
                        association_type="prerequisite",  # Exercise requires lecture
                        confidence=confidence,
                        reason=self._generate_discovery_reason(
                            name_match, "exercise", "lecture", common_concepts
                        ),
                        shared_concepts=common_concepts[:10],  # Limit to 10
                        auto_generated=True
                    )
                    result.suggestions.append(suggestion)

        # Strategy 2: Unknown-Unknown or same-type pairs with sufficient common concepts
        all_unknown_and_same = unknown_canvases + lecture_canvases + exercise_canvases

        for i, canvas1 in enumerate(all_unknown_and_same):
            for canvas2 in all_unknown_and_same[i + 1:]:
                # Skip if already covered in Strategy 1
                type1 = self.discover_canvas_type(canvas1)
                type2 = self.discover_canvas_type(canvas2)

                if (type1 == "exercise" and type2 == "lecture") or \
                   (type1 == "lecture" and type2 == "exercise"):
                    continue

                # Skip existing associations
                if (canvas1, canvas2) in existing_pairs:
                    continue

                # Get common concepts
                common_concepts = []
                if self._neo4j_client:
                    common_concepts = await self._neo4j_client.find_common_concepts(
                        canvas1, canvas2
                    )

                # Only suggest if meets minimum common concepts threshold
                if len(common_concepts) >= min_common_concepts:
                    name_match = False
                    confidence = self.calculate_discovery_confidence(name_match, common_concepts)

                    suggestion = AutoDiscoverySuggestion(
                        source_canvas=canvas1,
                        target_canvas=canvas2,
                        association_type="related",  # Related by concepts
                        confidence=confidence,
                        reason=self._generate_discovery_reason(
                            name_match, type1, type2, common_concepts
                        ),
                        shared_concepts=common_concepts[:10],
                        auto_generated=True
                    )
                    result.suggestions.append(suggestion)

        # Sort by confidence descending
        result.suggestions.sort(key=lambda s: s.confidence, reverse=True)
        result.discovered_count = len(result.suggestions)

        logger.info(
            f"Auto-discovery complete: {result.discovered_count} suggestions found "
            f"from {result.total_scanned} canvases"
        )

        return result

    async def on_canvas_open(
        self,
        canvas_path: str,
        min_common_concepts: int = 3
    ) -> AutoDiscoveryResult:
        """
        Auto-discover associations for a single canvas when it is opened.

        Story 36.6 Fix: Provides automatic trigger on Canvas open instead of
        requiring manual API call. Delegates to auto_discover_associations()
        with a filtered canvas set (from associations cache) and returns only
        suggestions involving the opened canvas.

        Args:
            canvas_path: Path of the canvas that was just opened
            min_common_concepts: Minimum common concepts for suggestion (default: 3)

        Returns:
            AutoDiscoveryResult with suggestions relevant to the opened canvas

        [Source: Story 36.6 adversarial review F1 fix]
        """
        # Collect known canvas paths from associations cache
        known_paths: set = set()
        for assoc in self._associations_cache.values():
            known_paths.add(assoc.source_canvas_path)
            known_paths.add(assoc.target_canvas_path)

        # Add opened canvas
        known_paths.add(canvas_path)

        if len(known_paths) < 2:
            logger.debug(f"on_canvas_open: only 1 known canvas, skipping discovery")
            return AutoDiscoveryResult(total_scanned=1, discovered_count=0)

        logger.info(
            f"on_canvas_open: auto-discovering for '{canvas_path}' "
            f"against {len(known_paths) - 1} known canvases"
        )

        # Delegate to full algorithm with limited canvas set
        result = await self.auto_discover_associations(
            canvas_paths=list(known_paths),
            min_common_concepts=min_common_concepts,
            include_existing=False
        )

        # Filter: only suggestions involving the opened canvas
        result.suggestions = [
            s for s in result.suggestions
            if s.source_canvas == canvas_path or s.target_canvas == canvas_path
        ]
        result.discovered_count = len(result.suggestions)

        if result.discovered_count > 0:
            logger.info(
                f"on_canvas_open: found {result.discovered_count} suggestions "
                f"for '{canvas_path}'"
            )

        return result

    # ═══════════════════════════════════════════════════════════════════════════
    # Knowledge Path Operations
    # ═══════════════════════════════════════════════════════════════════════════

    async def create_knowledge_path(
        self,
        name: str,
        description: str,
        nodes: List[Dict]
    ) -> KnowledgePath:
        """Create a new knowledge learning path."""
        path_id = f"kp-{uuid4().hex[:12]}"

        path_nodes = []
        sorted_nodes = sorted(nodes, key=lambda n: n.get('order', 0))
        for idx, node_data in enumerate(sorted_nodes):
            path_nodes.append(KnowledgePathNode(
                canvas_path=node_data['canvas_path'],
                canvas_title=self.extract_canvas_title(node_data['canvas_path']),
                order=node_data.get('order', idx + 1),
                prerequisite_concepts=node_data.get('prerequisite_concepts', []),
                mastery_level=0.0,
                is_completed=False
            ))

        path = KnowledgePath(
            id=path_id,
            name=name,
            description=description,
            nodes=path_nodes,
            completion_progress=0.0
        )

        self._knowledge_paths[path_id] = path
        logger.info(f"Created knowledge path {path_id}: {name}")

        return path

    async def get_knowledge_path(self, path_id: str) -> Optional[KnowledgePath]:
        """Get knowledge path by ID."""
        return self._knowledge_paths.get(path_id)

    async def list_knowledge_paths(self) -> List[KnowledgePath]:
        """List all knowledge paths."""
        return list(self._knowledge_paths.values())

    async def update_node_mastery(
        self,
        path_id: str,
        canvas_path: str,
        mastery_level: float,
        is_completed: bool
    ) -> Optional[KnowledgePath]:
        """Update mastery level for a node in a knowledge path."""
        if path_id not in self._knowledge_paths:
            return None

        path = self._knowledge_paths[path_id]

        # Find and update the node
        for node in path.nodes:
            if node.canvas_path == canvas_path:
                node.mastery_level = mastery_level
                node.is_completed = is_completed
                break

        # Recalculate completion progress
        completed_count = sum(1 for n in path.nodes if n.is_completed)
        path.completion_progress = completed_count / len(path.nodes) if path.nodes else 0

        return path

    async def delete_knowledge_path(self, path_id: str) -> bool:
        """Delete a knowledge path."""
        if path_id not in self._knowledge_paths:
            return False

        del self._knowledge_paths[path_id]
        logger.info(f"Deleted knowledge path {path_id}")
        return True

    # ═══════════════════════════════════════════════════════════════════════════
    # Statistics
    # ═══════════════════════════════════════════════════════════════════════════

    async def get_statistics(self) -> Dict:
        """Get cross-canvas statistics."""
        associations = list(self._associations_cache.values())
        paths = list(self._knowledge_paths.values())

        # Count unique canvases
        linked_canvases: Set[str] = set()
        for assoc in associations:
            linked_canvases.add(assoc.source_canvas_path)
            linked_canvases.add(assoc.target_canvas_path)

        # Calculate average path completion
        avg_completion = (
            sum(p.completion_progress for p in paths) / len(paths)
            if paths else 0
        )

        return {
            "total_associations": len(associations),
            "total_paths": len(paths),
            "total_canvases_linked": len(linked_canvases),
            "average_path_completion": avg_completion,
            "neo4j_enabled": self._neo4j_client is not None
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton Instance
# ═══════════════════════════════════════════════════════════════════════════════

# Global service instance for dependency injection
_cross_canvas_service: Optional[CrossCanvasService] = None


def get_cross_canvas_service(
    neo4j_client: Optional["Neo4jClient"] = None
) -> CrossCanvasService:
    """
    Get or create the CrossCanvasService singleton.

    Story 36.5 AC-2: Inject Neo4jClient dependency for persistence.

    Args:
        neo4j_client: Optional Neo4jClient instance. If not provided,
                      will attempt to get from neo4j_client module.

    Returns:
        CrossCanvasService singleton instance

    [Source: docs/stories/36.5.story.md#Task-2.2]
    """
    global _cross_canvas_service

    if _cross_canvas_service is None:
        # Lazy import to avoid circular imports
        if neo4j_client is None:
            try:
                from app.clients.neo4j_client import get_neo4j_client
                neo4j_client = get_neo4j_client()
            except Exception as e:
                logger.warning(f"Failed to get Neo4jClient: {e}")
                neo4j_client = None

        _cross_canvas_service = CrossCanvasService(neo4j_client=neo4j_client)

    return _cross_canvas_service


def reset_cross_canvas_service() -> None:
    """
    Reset singleton instance (for testing).

    [Source: docs/stories/36.5.story.md#Testing]
    """
    global _cross_canvas_service
    _cross_canvas_service = None
