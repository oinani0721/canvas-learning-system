"""
Unit Tests for Source Node ID Validator Service

Story 19.1 AC 7: 验证所有代码有文档来源标注
Tests for: src/services/source_node_validator.py

✅ Verified from pytest documentation (Context7)
"""

import json

import pytest
from src.services.source_node_validator import (
    SourceNodeValidator,
)


@pytest.fixture
def validator():
    """Create a fresh validator instance."""
    return SourceNodeValidator()


@pytest.fixture
def sample_canvas_file(tmp_path):
    """Create a sample canvas file for testing."""
    canvas_data = {
        "nodes": [
            {
                "id": "a1b2c3d4",
                "type": "text",
                "text": "Test node 1",
                "x": 0,
                "y": 0,
                "width": 100,
                "height": 50,
                "color": "4"
            },
            {
                "id": "e5f6a7b8",
                "type": "text",
                "text": "Test node 2",
                "x": 150,
                "y": 0,
                "width": 100,
                "height": 50,
                "color": "2"
            },
            {
                "id": "12345678",
                "type": "text",
                "text": "Test node 3 - numeric hex",
                "x": 300,
                "y": 0,
                "width": 100,
                "height": 50,
                "color": "1"
            }
        ],
        "edges": []
    }

    canvas_path = tmp_path / "test.canvas"
    with open(canvas_path, 'w', encoding='utf-8') as f:
        json.dump(canvas_data, f)

    return str(canvas_path)


@pytest.fixture
def review_canvas_file(tmp_path, sample_canvas_file):
    """Create a review canvas with sourceNodeId references."""
    review_data = {
        "nodes": [
            {
                "id": "q1",
                "type": "text",
                "text": "Question for node 1",
                "x": 0,
                "y": 100,
                "width": 100,
                "height": 50,
                "color": "4",
                "sourceNodeId": "a1b2c3d4"  # Valid reference
            },
            {
                "id": "q2",
                "type": "text",
                "text": "Question for node 2",
                "x": 150,
                "y": 100,
                "width": 100,
                "height": 50,
                "color": "2",
                "sourceNodeId": "e5f6a7b8"  # Valid reference
            },
            {
                "id": "q3",
                "type": "text",
                "text": "Question for invalid node",
                "x": 300,
                "y": 100,
                "width": 100,
                "height": 50,
                "color": "4",
                "sourceNodeId": "invalid12"  # Invalid reference
            }
        ],
        "edges": []
    }

    review_path = tmp_path / "test-review.canvas"
    with open(review_path, 'w', encoding='utf-8') as f:
        json.dump(review_data, f)

    return str(review_path)


class TestSourceNodeValidatorUUID:
    """Test UUID format validation."""

    def test_valid_8char_hex_id(self, validator):
        """8-character hex IDs should be valid (Obsidian format)."""
        assert validator._is_valid_uuid("a1b2c3d4") is True
        assert validator._is_valid_uuid("12345678") is True
        assert validator._is_valid_uuid("abcdef00") is True

    def test_valid_full_uuid(self, validator):
        """Full UUIDs should be valid."""
        assert validator._is_valid_uuid("a1b2c3d4-e5f6-7890-abcd-ef1234567890") is True
        assert validator._is_valid_uuid("550e8400-e29b-41d4-a716-446655440000") is True

    def test_invalid_formats(self, validator):
        """Invalid formats should be rejected."""
        assert validator._is_valid_uuid("") is False
        assert validator._is_valid_uuid("invalid") is False
        assert validator._is_valid_uuid("12345") is False  # Too short
        assert validator._is_valid_uuid("gggggggg") is False  # Non-hex chars


class TestSourceNodeValidatorSingle:
    """Test single sourceNodeId validation."""

    def test_valid_source_node_id(self, validator, sample_canvas_file):
        """Valid sourceNodeId should pass validation."""
        result = validator.validate_source_node_id(
            canvas_path=sample_canvas_file,
            source_node_id="a1b2c3d4"
        )

        assert result.is_valid is True
        assert result.exists_in_original is True
        assert result.original_node_type == "text"
        assert result.original_node_color == "4"
        assert result.error_message is None

    def test_invalid_format_source_node_id(self, validator, sample_canvas_file):
        """Invalid format should fail validation."""
        result = validator.validate_source_node_id(
            canvas_path=sample_canvas_file,
            source_node_id="invalid"
        )

        assert result.is_valid is False
        assert result.exists_in_original is False
        assert "Invalid ID format" in result.error_message

    def test_nonexistent_source_node_id(self, validator, sample_canvas_file):
        """Non-existent node ID should fail validation."""
        result = validator.validate_source_node_id(
            canvas_path=sample_canvas_file,
            source_node_id="ffffffff"  # Valid format but doesn't exist
        )

        assert result.is_valid is False
        assert result.exists_in_original is False
        assert "not found in original canvas" in result.error_message

    def test_nonexistent_canvas_file(self, validator, tmp_path):
        """Non-existent canvas file should fail validation."""
        result = validator.validate_source_node_id(
            canvas_path=str(tmp_path / "nonexistent.canvas"),
            source_node_id="a1b2c3d4"
        )

        assert result.is_valid is False
        assert "Cannot load canvas file" in result.error_message


class TestSourceNodeValidatorBatch:
    """Test batch validation."""

    def test_batch_all_valid(self, validator, sample_canvas_file):
        """Batch with all valid IDs should pass."""
        result = validator.validate_batch(
            canvas_path=sample_canvas_file,
            source_node_ids=["a1b2c3d4", "e5f6a7b8"]
        )

        assert result.total_count == 2
        assert result.valid_count == 2
        assert result.invalid_count == 0
        assert result.all_valid is True

    def test_batch_some_invalid(self, validator, sample_canvas_file):
        """Batch with some invalid IDs should report correctly."""
        result = validator.validate_batch(
            canvas_path=sample_canvas_file,
            source_node_ids=["a1b2c3d4", "invalid12"]
        )

        assert result.total_count == 2
        assert result.valid_count == 1
        assert result.invalid_count == 1
        assert result.all_valid is False

    def test_batch_empty_list(self, validator, sample_canvas_file):
        """Empty batch should return empty result."""
        result = validator.validate_batch(
            canvas_path=sample_canvas_file,
            source_node_ids=[]
        )

        assert result.total_count == 0
        assert result.valid_count == 0
        assert result.all_valid is True  # Vacuously true


class TestSourceNodeValidatorReviewCanvas:
    """Test review canvas validation."""

    def test_validate_review_canvas(
        self, validator, sample_canvas_file, review_canvas_file
    ):
        """Review canvas should be validated against original."""
        result = validator.validate_review_canvas(
            review_canvas_path=review_canvas_file,
            original_canvas_path=sample_canvas_file
        )

        assert result.total_count == 3
        assert result.valid_count == 2
        assert result.invalid_count == 1
        assert result.all_valid is False

        # Check individual results
        valid_ids = [r.source_node_id for r in result.results if r.is_valid]
        assert "a1b2c3d4" in valid_ids
        assert "e5f6a7b8" in valid_ids

    def test_validate_empty_review_canvas(self, validator, sample_canvas_file, tmp_path):
        """Review canvas with no sourceNodeIds should pass."""
        empty_review = {
            "nodes": [{"id": "q1", "type": "text", "text": "No source"}],
            "edges": []
        }
        review_path = tmp_path / "empty-review.canvas"
        with open(review_path, 'w') as f:
            json.dump(empty_review, f)

        result = validator.validate_review_canvas(
            review_canvas_path=str(review_path),
            original_canvas_path=sample_canvas_file
        )

        assert result.total_count == 0
        assert result.all_valid is True


class TestSourceNodeValidatorCache:
    """Test caching behavior."""

    def test_cache_reuse(self, validator, sample_canvas_file):
        """Canvas should be loaded from cache on repeated access."""
        # First call loads from file
        validator.validate_source_node_id(sample_canvas_file, "a1b2c3d4")
        assert sample_canvas_file in validator._canvas_cache

        # Second call should use cache
        validator.validate_source_node_id(sample_canvas_file, "e5f6a7b8")
        # Cache should still have only one entry
        assert len(validator._canvas_cache) == 1

    def test_clear_cache(self, validator, sample_canvas_file):
        """Cache should be clearable."""
        validator.validate_source_node_id(sample_canvas_file, "a1b2c3d4")
        assert len(validator._canvas_cache) == 1

        validator.clear_cache()
        assert len(validator._canvas_cache) == 0
