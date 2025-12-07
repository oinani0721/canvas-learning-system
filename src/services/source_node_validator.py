"""
Source Node ID Validator Service

Validates sourceNodeId metadata in review canvas nodes against original canvas nodes.

Story 19.1 AC 5: sourceNodeId验证API，可检查sourceNodeId是否有效

✅ Verified from PRD FR4 (Lines 2647-2674) - sourceNodeId技术方案
✅ Verified from Story 4.9 - sourceNodeId实现规范
"""

import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SourceNodeValidationResult:
    """Validation result for a single sourceNodeId.

    Attributes:
        source_node_id: The sourceNodeId being validated
        is_valid: Whether the sourceNodeId is valid
        exists_in_original: Whether the node exists in the original canvas
        original_node_type: Type of the original node if found
        original_node_color: Color of the original node if found
        error_message: Error message if validation failed
    """
    source_node_id: str
    is_valid: bool
    exists_in_original: bool = False
    original_node_type: Optional[str] = None
    original_node_color: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class BatchValidationResult:
    """Result of batch validation for multiple sourceNodeIds.

    Attributes:
        total_count: Total number of sourceNodeIds validated
        valid_count: Number of valid sourceNodeIds
        invalid_count: Number of invalid sourceNodeIds
        results: Individual validation results
        all_valid: Whether all sourceNodeIds are valid
    """
    total_count: int
    valid_count: int
    invalid_count: int
    results: List[SourceNodeValidationResult] = field(default_factory=list)
    all_valid: bool = False


class SourceNodeValidator:
    """
    Validates sourceNodeId metadata in review canvas nodes.

    Ensures that sourceNodeId fields in review canvas nodes reference
    valid nodes in the original canvas.

    [Source: docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md:2647-2674]

    Example:
        >>> validator = SourceNodeValidator()
        >>> result = validator.validate_source_node_id(
        ...     canvas_path="path/to/original.canvas",
        ...     source_node_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        ... )
        >>> print(result.is_valid)
        True
    """

    def __init__(self):
        """Initialize the SourceNodeValidator."""
        self._canvas_cache: Dict[str, Dict[str, Any]] = {}

    def _is_valid_uuid(self, value: str) -> bool:
        """
        Check if a string is a valid UUID format.

        Note: Obsidian Canvas uses 8-character hex IDs (not full UUIDs),
        so we accept both formats.

        Args:
            value: String to validate

        Returns:
            True if valid UUID or 8-char hex ID
        """
        if not value:
            return False

        # Accept 8-character hex IDs (Obsidian Canvas format)
        if len(value) == 8:
            try:
                int(value, 16)
                return True
            except ValueError:
                pass

        # Accept full UUIDs
        try:
            uuid.UUID(value)
            return True
        except ValueError:
            return False

    def _load_canvas(self, canvas_path: str) -> Optional[Dict[str, Any]]:
        """
        Load and cache a canvas file.

        Args:
            canvas_path: Path to the canvas file

        Returns:
            Canvas data dict or None if failed to load
        """
        # Check cache first
        if canvas_path in self._canvas_cache:
            return self._canvas_cache[canvas_path]

        path = Path(canvas_path)
        if not path.exists():
            return None

        try:
            with open(path, 'r', encoding='utf-8') as f:
                canvas_data = json.load(f)
                self._canvas_cache[canvas_path] = canvas_data
                return canvas_data
        except (json.JSONDecodeError, IOError):
            return None

    def _get_node_by_id(
        self,
        canvas_data: Dict[str, Any],
        node_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find a node by ID in canvas data.

        Args:
            canvas_data: Loaded canvas data
            node_id: Node ID to find

        Returns:
            Node dict or None if not found
        """
        nodes = canvas_data.get('nodes', [])
        for node in nodes:
            if node.get('id') == node_id:
                return node
        return None

    def validate_source_node_id(
        self,
        canvas_path: str,
        source_node_id: str
    ) -> SourceNodeValidationResult:
        """
        Validate a single sourceNodeId against the original canvas.

        Checks:
        1. sourceNodeId is in valid UUID/hex format
        2. Corresponding node exists in the original canvas

        Args:
            canvas_path: Path to the original canvas file
            source_node_id: The sourceNodeId to validate

        Returns:
            SourceNodeValidationResult with validation details

        [Source: docs/stories/19.1.story.md - AC 5]
        """
        # Check UUID format
        if not self._is_valid_uuid(source_node_id):
            return SourceNodeValidationResult(
                source_node_id=source_node_id,
                is_valid=False,
                exists_in_original=False,
                error_message=f"Invalid ID format: '{source_node_id}' is not a valid UUID or 8-char hex ID"
            )

        # Load canvas
        canvas_data = self._load_canvas(canvas_path)
        if canvas_data is None:
            return SourceNodeValidationResult(
                source_node_id=source_node_id,
                is_valid=False,
                exists_in_original=False,
                error_message=f"Cannot load canvas file: '{canvas_path}'"
            )

        # Find node in original canvas
        node = self._get_node_by_id(canvas_data, source_node_id)
        if node is None:
            return SourceNodeValidationResult(
                source_node_id=source_node_id,
                is_valid=False,
                exists_in_original=False,
                error_message=f"Node '{source_node_id}' not found in original canvas"
            )

        # Valid!
        return SourceNodeValidationResult(
            source_node_id=source_node_id,
            is_valid=True,
            exists_in_original=True,
            original_node_type=node.get('type'),
            original_node_color=node.get('color')
        )

    def validate_batch(
        self,
        canvas_path: str,
        source_node_ids: List[str]
    ) -> BatchValidationResult:
        """
        Validate multiple sourceNodeIds against the original canvas.

        Args:
            canvas_path: Path to the original canvas file
            source_node_ids: List of sourceNodeIds to validate

        Returns:
            BatchValidationResult with all validation details

        [Source: docs/stories/19.1.story.md - Task 3]
        """
        results = []
        valid_count = 0

        for source_node_id in source_node_ids:
            result = self.validate_source_node_id(canvas_path, source_node_id)
            results.append(result)
            if result.is_valid:
                valid_count += 1

        total = len(source_node_ids)
        return BatchValidationResult(
            total_count=total,
            valid_count=valid_count,
            invalid_count=total - valid_count,
            results=results,
            all_valid=(valid_count == total)
        )

    def validate_review_canvas(
        self,
        review_canvas_path: str,
        original_canvas_path: str
    ) -> BatchValidationResult:
        """
        Validate all sourceNodeIds in a review canvas against the original.

        Extracts all sourceNodeId fields from the review canvas nodes
        and validates each one against the original canvas.

        Args:
            review_canvas_path: Path to the review canvas file
            original_canvas_path: Path to the original canvas file

        Returns:
            BatchValidationResult with validation details for all sourceNodeIds

        Example:
            >>> validator = SourceNodeValidator()
            >>> result = validator.validate_review_canvas(
            ...     review_canvas_path="review-离散数学-20250115.canvas",
            ...     original_canvas_path="离散数学.canvas"
            ... )
            >>> print(f"Valid: {result.valid_count}/{result.total_count}")
            Valid: 12/15

        [Source: docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md:2662-2682]
        """
        # Load review canvas
        review_data = self._load_canvas(review_canvas_path)
        if review_data is None:
            return BatchValidationResult(
                total_count=0,
                valid_count=0,
                invalid_count=0,
                results=[],
                all_valid=False
            )

        # Extract all sourceNodeIds
        source_node_ids = []
        for node in review_data.get('nodes', []):
            source_id = node.get('sourceNodeId')
            if source_id:
                source_node_ids.append(source_id)

        if not source_node_ids:
            return BatchValidationResult(
                total_count=0,
                valid_count=0,
                invalid_count=0,
                results=[],
                all_valid=True  # No sourceNodeIds means nothing to validate
            )

        # Validate all
        return self.validate_batch(original_canvas_path, source_node_ids)

    def clear_cache(self):
        """Clear the canvas cache to free memory."""
        self._canvas_cache.clear()
