"""
Tests for Profile API source ID serialization (Feature 1.2).

Verifies that TipItem and WeaknessItem Pydantic models include
source_canvas_id and source_node_id fields, and that the
/profile/{node_id}/tips and /profile/{node_id}/weaknesses endpoints
return these fields in their responses.

Phase 3 PRD Feature 1.2: Backend Serialization of Source IDs.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.api.v1.endpoints.profile import (
    TipItem,
    WeaknessItem,
    get_profile_tips,
    get_profile_weaknesses,
)

# ============================================================================
# Pydantic Model Unit Tests
# ============================================================================


class TestTipItemSourceFields:
    """TipItem model must accept and serialize source_canvas_id and source_node_id."""

    def test_tip_item_accepts_source_canvas_id(self):
        tip = TipItem(
            tip_id="tip-001",
            content="Use memoization for recursive problems",
            category="optimization",
            annotated_at="2026-03-30T12:00:00Z",
            source_canvas_id="canvas-abc",
        )
        assert tip.source_canvas_id == "canvas-abc"

    def test_tip_item_accepts_source_node_id(self):
        tip = TipItem(
            tip_id="tip-002",
            content="Dynamic programming tip",
            category="technique",
            annotated_at="2026-03-30T12:00:00Z",
            source_node_id="node-xyz",
        )
        assert tip.source_node_id == "node-xyz"

    def test_tip_item_source_fields_default_to_none(self):
        tip = TipItem(
            tip_id="tip-003",
            content="Some tip",
            annotated_at="2026-03-30T12:00:00Z",
        )
        assert tip.source_canvas_id is None
        assert tip.source_node_id is None

    def test_tip_item_model_dump_includes_source_fields(self):
        tip = TipItem(
            tip_id="tip-004",
            content="Serialization test",
            annotated_at="2026-03-30T12:00:00Z",
            source_canvas_id="canvas-123",
            source_node_id="node-456",
        )
        dumped = tip.model_dump()
        assert dumped["source_canvas_id"] == "canvas-123"
        assert dumped["source_node_id"] == "node-456"

    def test_tip_item_model_dump_none_when_absent(self):
        tip = TipItem(
            tip_id="tip-005",
            content="No source info",
            annotated_at="2026-03-30T12:00:00Z",
        )
        dumped = tip.model_dump()
        assert "source_canvas_id" in dumped
        assert dumped["source_canvas_id"] is None
        assert "source_node_id" in dumped
        assert dumped["source_node_id"] is None


class TestWeaknessItemSourceFields:
    """WeaknessItem model must accept and serialize source_canvas_id and source_node_id."""

    def test_weakness_item_accepts_source_canvas_id(self):
        weakness = WeaknessItem(
            direction="Confusion between BFS and DFS",
            frequency=3,
            source_canvas_id="canvas-abc",
        )
        assert weakness.source_canvas_id == "canvas-abc"

    def test_weakness_item_accepts_source_node_id(self):
        weakness = WeaknessItem(
            direction="Off-by-one errors in recursion",
            frequency=2,
            source_node_id="node-xyz",
        )
        assert weakness.source_node_id == "node-xyz"

    def test_weakness_item_source_fields_default_to_none(self):
        weakness = WeaknessItem(
            direction="Some weakness",
            frequency=1,
        )
        assert weakness.source_canvas_id is None
        assert weakness.source_node_id is None

    def test_weakness_item_model_dump_includes_source_fields(self):
        weakness = WeaknessItem(
            direction="Test direction",
            frequency=5,
            source_canvas_id="canvas-789",
            source_node_id="node-012",
        )
        dumped = weakness.model_dump()
        assert dumped["source_canvas_id"] == "canvas-789"
        assert dumped["source_node_id"] == "node-012"


# ============================================================================
# Endpoint Handler Tests (mock Neo4j, test serialization logic)
# ============================================================================


def _mock_neo4j_client():
    """Create a mock Neo4j client for endpoint testing."""
    mock_client = MagicMock()
    mock_client.run_query = AsyncMock(return_value=[])
    return mock_client


class TestTipsEndpointSourceFields:
    """get_profile_tips must include source_canvas_id and source_node_id in response."""

    @pytest.mark.asyncio
    async def test_tips_response_includes_source_fields_when_present(self):
        """Tips with source metadata should serialize source_canvas_id and source_node_id."""
        mock_records = [
            {
                "tip_id": "tip-e2e-001",
                "content": "Use two pointers for sorted arrays",
                "category": "technique-tip",
                "annotated_at": "2026-03-30T10:00:00Z",
                "context": "From a conversation about arrays",
                "source_canvas_id": "canvas-study-001",
                "source_node_id": "node-arrays-101",
            }
        ]
        mock_client = _mock_neo4j_client()
        mock_client.run_query = AsyncMock(return_value=mock_records)

        with patch(
            "app.api.v1.endpoints.profile._get_neo4j_client",
            return_value=mock_client,
        ):
            result = await get_profile_tips(
                node_id="node-arrays-101",
                group_id="test-group",
            )

        assert result["total"] == 1
        tip = result["tips"][0]
        assert tip["source_canvas_id"] == "canvas-study-001"
        assert tip["source_node_id"] == "node-arrays-101"

    @pytest.mark.asyncio
    async def test_tips_response_source_fields_null_when_empty_string(self):
        """Tips with empty source metadata should have null source fields (graceful degradation)."""
        mock_records = [
            {
                "tip_id": "tip-legacy-001",
                "content": "Legacy tip without source info",
                "category": "general",
                "annotated_at": "2026-01-15T08:00:00Z",
                "context": "",
                "source_canvas_id": "",
                "source_node_id": "",
            }
        ]
        mock_client = _mock_neo4j_client()
        mock_client.run_query = AsyncMock(return_value=mock_records)

        with patch(
            "app.api.v1.endpoints.profile._get_neo4j_client",
            return_value=mock_client,
        ):
            result = await get_profile_tips(
                node_id="some-node",
                group_id="test-group",
            )

        assert result["total"] == 1
        tip = result["tips"][0]
        # Empty strings from Cypher COALESCE should become None
        assert tip["source_canvas_id"] is None
        assert tip["source_node_id"] is None

    @pytest.mark.asyncio
    async def test_tips_response_empty_when_no_data(self):
        """Endpoint returns empty list when no tips exist (no regression)."""
        mock_client = _mock_neo4j_client()
        mock_client.run_query = AsyncMock(return_value=[])

        with patch(
            "app.api.v1.endpoints.profile._get_neo4j_client",
            return_value=mock_client,
        ):
            result = await get_profile_tips(
                node_id="no-tips-node",
                group_id="test-group",
            )

        assert result["tips"] == []
        assert result["total"] == 0


class TestWeaknessesEndpointSourceFields:
    """get_profile_weaknesses must include source_canvas_id and source_node_id in response."""

    @pytest.mark.asyncio
    async def test_weaknesses_response_includes_source_fields_when_present(self):
        """Weaknesses with source metadata should serialize source_canvas_id and source_node_id."""
        mock_records = [
            {
                "direction": "Confuses stack and queue operations",
                "frequency": 4,
                "last_seen": "2026-03-28T14:00:00Z",
                "source_canvas_id": "canvas-ds-001",
                "source_node_id": "node-stack-201",
            }
        ]
        mock_client = _mock_neo4j_client()
        mock_client.run_query = AsyncMock(return_value=mock_records)

        with patch(
            "app.api.v1.endpoints.profile._get_neo4j_client",
            return_value=mock_client,
        ):
            result = await get_profile_weaknesses(
                node_id="node-stack-201",
                group_id="test-group",
            )

        assert result["total"] == 1
        weakness = result["weaknesses"][0]
        assert weakness["source_canvas_id"] == "canvas-ds-001"
        assert weakness["source_node_id"] == "node-stack-201"

    @pytest.mark.asyncio
    async def test_weaknesses_response_source_fields_null_when_empty_string(self):
        """Weaknesses with empty source metadata should have null source fields."""
        mock_records = [
            {
                "direction": "Legacy weakness",
                "frequency": 2,
                "last_seen": "2026-02-01T10:00:00Z",
                "source_canvas_id": "",
                "source_node_id": "",
            }
        ]
        mock_client = _mock_neo4j_client()
        mock_client.run_query = AsyncMock(return_value=mock_records)

        with patch(
            "app.api.v1.endpoints.profile._get_neo4j_client",
            return_value=mock_client,
        ):
            result = await get_profile_weaknesses(
                node_id="some-node",
                group_id="test-group",
            )

        assert result["total"] == 1
        weakness = result["weaknesses"][0]
        assert weakness["source_canvas_id"] is None
        assert weakness["source_node_id"] is None

    @pytest.mark.asyncio
    async def test_weaknesses_response_empty_when_no_data(self):
        """Endpoint returns empty list when no weaknesses exist (no regression)."""
        mock_client = _mock_neo4j_client()
        mock_client.run_query = AsyncMock(return_value=[])

        with patch(
            "app.api.v1.endpoints.profile._get_neo4j_client",
            return_value=mock_client,
        ):
            result = await get_profile_weaknesses(
                node_id="no-weakness-node",
                group_id="test-group",
            )

        assert result["weaknesses"] == []
        assert result["total"] == 0
