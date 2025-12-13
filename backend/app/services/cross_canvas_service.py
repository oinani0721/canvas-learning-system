# Canvas Learning System - Cross Canvas Service
# Story 25.3: Exercise-Lecture Canvas Association
"""
CrossCanvasService - Manages cross-canvas associations.

Provides:
- CRUD operations for canvas associations
- Association queries by canvas path and relation type
- Intelligent lecture canvas suggestions for exercise canvases

[Source: Story 25.3 - Exercise-Lecture Canvas Association]
[Source: Epic 16 - 跨Canvas关联学习系统]
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
from uuid import uuid4

logger = logging.getLogger(__name__)


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

    [Source: Story 25.3 - Exercise-Lecture Canvas Association]
    """

    # Patterns for identifying exercise vs lecture canvases
    # ✅ Verified from Story 25.3 Task 3.2: Canvas file name pattern matching
    EXERCISE_PATTERNS = [
        r'题目', r'习题', r'练习', r'作业', r'exam', r'exercise', r'problem',
        r'quiz', r'test', r'期末', r'期中', r'复习题'
    ]
    LECTURE_PATTERNS = [
        r'讲座', r'讲义', r'课程', r'lecture', r'lesson', r'chapter',
        r'笔记', r'notes', r'教材', r'textbook'
    ]

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize CrossCanvasService.

        Args:
            storage_path: Optional path for persistent storage (future use)
        """
        self._associations: Dict[str, CrossCanvasAssociation] = {}
        self._knowledge_paths: Dict[str, KnowledgePath] = {}
        self._storage_path = storage_path
        logger.info(f"CrossCanvasService initialized, storage_path={storage_path}")

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

        [Source: Story 25.3 AC1 - Create exercise-lecture Canvas association]

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

        self._associations[association_id] = association
        logger.info(
            f"Created association {association_id}: "
            f"{source_canvas_path} -[{relationship_type}]-> {target_canvas_path}"
        )

        return association

    async def get_association(self, association_id: str) -> Optional[CrossCanvasAssociation]:
        """Get association by ID."""
        return self._associations.get(association_id)

    async def update_association(
        self,
        association_id: str,
        relationship_type: Optional[str] = None,
        common_concepts: Optional[List[str]] = None,
        confidence: Optional[float] = None
    ) -> Optional[CrossCanvasAssociation]:
        """
        Update an existing association.

        [Source: Story 25.3 AC4 - Support confidence scoring]
        """
        if association_id not in self._associations:
            return None

        association = self._associations[association_id]

        if relationship_type is not None:
            association.relationship_type = relationship_type
        if common_concepts is not None:
            association.common_concepts = common_concepts
        if confidence is not None:
            association.confidence = confidence

        association.updated_at = datetime.now(timezone.utc)

        logger.info(f"Updated association {association_id}")
        return association

    async def delete_association(self, association_id: str) -> bool:
        """Delete an association."""
        if association_id not in self._associations:
            return False

        del self._associations[association_id]
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
        associations = list(self._associations.values())

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

        [Source: Story 25.3 Task 2.3 - Add get_associated_canvases method]

        Args:
            canvas_path: Canvas file path to find associations for
            relation_type: Optional filter by relationship type (e.g., "exercise_lecture")

        Returns:
            List of associations where canvas_path is source or target
        """
        associations = []

        for assoc in self._associations.values():
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

        [Source: Story 25.3 AC2 - Auto-retrieve lecture content]

        Args:
            exercise_canvas_path: Path to the exercise canvas

        Returns:
            The highest-confidence exercise_lecture association, or None
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

        for assoc in self._associations.values():
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
        associations = list(self._associations.values())
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
            "average_path_completion": avg_completion
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton Instance
# ═══════════════════════════════════════════════════════════════════════════════

# Global service instance for dependency injection
_cross_canvas_service: Optional[CrossCanvasService] = None


def get_cross_canvas_service() -> CrossCanvasService:
    """Get or create the CrossCanvasService singleton."""
    global _cross_canvas_service
    if _cross_canvas_service is None:
        _cross_canvas_service = CrossCanvasService()
    return _cross_canvas_service
