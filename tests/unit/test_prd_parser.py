"""
Unit tests for PRD Parser

Tests for automatic Story ID extraction from PRD files:
- Story ID extraction from various PRD formats
- Story coverage validation
- Epic PRD file discovery
- Epic ID extraction from Story ID

Author: Canvas Learning System Team
Created: 2025-12-12
Epic: 20 (PRD Auto-extraction Fix)
"""

import tempfile
from pathlib import Path

import pytest

from src.bmad_orchestrator.prd_parser import (
    extract_stories_from_prd,
    find_epic_prd_file,
    get_epic_id_from_story,
    validate_story_coverage,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory with PRD structure"""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # Create docs/prd directory
        prd_dir = base / "docs" / "prd"
        prd_dir.mkdir(parents=True)

        yield base


@pytest.fixture
def sample_prd_heading_format(temp_project_dir):
    """Create a sample PRD file using ### Story X.Y: format"""
    prd_content = """# EPIC-20: Backend Stability Multi-Provider

## Overview

This epic implements multi-provider architecture.

## Stories

### Story 20.1: Multi-Provider Architecture

Implement provider factory pattern.

### Story 20.2: ProviderFactory Startup Integration

Initialize providers on app startup.

### Story 20.3: AgentService Provider Integration

Replace GeminiClient with ProviderFactory.

### Story 20.4: Background Health Check Service

Implement health monitoring.
"""
    prd_file = temp_project_dir / "docs" / "prd" / "EPIC-20-BACKEND-STABILITY.md"
    prd_file.write_text(prd_content, encoding="utf-8")
    return prd_file


@pytest.fixture
def sample_prd_story_id_format(temp_project_dir):
    """Create a sample PRD file using **Story ID**: Story-X.Y format"""
    prd_content = """# EPIC-21: Agent E2E Flow Fix

## Stories

### Feature 1

**Story ID**: Story-21.1
**Title**: Fix Agent Initialization

### Feature 2

**Story ID**: Story-21.2
**Title**: Add Error Handling

### Feature 3

**Story ID**: Story 21.3
**Title**: Improve Logging

### Feature 4

**Story ID**: Story-21.4
**Title**: Add Tests

### Feature 5

**Story ID**: Story-21.5
**Title**: Update Documentation

### Feature 6

**Story ID**: Story 21.6
**Title**: Performance Optimization
"""
    prd_file = temp_project_dir / "docs" / "prd" / "EPIC-21-AGENT-E2E-FLOW-FIX.md"
    prd_file.write_text(prd_content, encoding="utf-8")
    return prd_file


@pytest.fixture
def sample_prd_mixed_format(temp_project_dir):
    """Create a sample PRD file using mixed formats"""
    prd_content = """# EPIC-22: Memory System

## Stories

### Story 22.1: Neo4j Integration

Story ID: Story-22.1

**Description**: Integrate Neo4j database.

### Story-22.2: Graphiti Setup

| Story 22.2 | Medium Priority |

**Description**: Setup Graphiti framework.

### Story 22.3: Query Interface

**Story ID**: Story 22.3

**Description**: Build query interface.
"""
    prd_file = temp_project_dir / "docs" / "prd" / "EPIC-22-MEMORY-SYSTEM.md"
    prd_file.write_text(prd_content, encoding="utf-8")
    return prd_file


@pytest.fixture
def sample_prd_empty(temp_project_dir):
    """Create an empty PRD file with no stories"""
    prd_content = """# EPIC-99: Empty Epic

## Overview

This epic has no stories defined yet.

## TODO

- Define stories
"""
    prd_file = temp_project_dir / "docs" / "prd" / "EPIC-99-EMPTY.md"
    prd_file.write_text(prd_content, encoding="utf-8")
    return prd_file


# ============================================================================
# Test: extract_stories_from_prd
# ============================================================================


class TestExtractStoriesFromPrd:
    """Tests for extract_stories_from_prd function"""

    def test_extract_heading_format(self, sample_prd_heading_format):
        """Test extraction from ### Story X.Y: format"""
        stories = extract_stories_from_prd(sample_prd_heading_format)

        assert len(stories) == 4
        assert stories == ["20.1", "20.2", "20.3", "20.4"]

    def test_extract_story_id_format(self, sample_prd_story_id_format):
        """Test extraction from **Story ID**: Story-X.Y format"""
        stories = extract_stories_from_prd(sample_prd_story_id_format)

        assert len(stories) == 6
        assert stories == ["21.1", "21.2", "21.3", "21.4", "21.5", "21.6"]

    def test_extract_mixed_format(self, sample_prd_mixed_format):
        """Test extraction from mixed formats"""
        stories = extract_stories_from_prd(sample_prd_mixed_format)

        assert len(stories) == 3
        assert stories == ["22.1", "22.2", "22.3"]

    def test_extract_empty_prd(self, sample_prd_empty):
        """Test extraction from PRD with no stories"""
        stories = extract_stories_from_prd(sample_prd_empty)

        assert len(stories) == 0
        assert stories == []

    def test_extract_nonexistent_file(self, temp_project_dir):
        """Test extraction from non-existent file"""
        nonexistent = temp_project_dir / "docs" / "prd" / "NONEXISTENT.md"
        stories = extract_stories_from_prd(nonexistent)

        assert len(stories) == 0
        assert stories == []

    def test_stories_are_sorted(self, temp_project_dir):
        """Test that stories are returned in sorted order"""
        prd_content = """# EPIC-23: Test Sorting

### Story 23.10: Tenth
### Story 23.2: Second
### Story 23.1: First
### Story 23.3: Third
"""
        prd_file = temp_project_dir / "docs" / "prd" / "EPIC-23-SORTING.md"
        prd_file.write_text(prd_content, encoding="utf-8")

        stories = extract_stories_from_prd(prd_file)

        # Should be sorted numerically, not alphabetically
        assert stories == ["23.1", "23.2", "23.3", "23.10"]


# ============================================================================
# Test: validate_story_coverage
# ============================================================================


class TestValidateStoryCoverage:
    """Tests for validate_story_coverage function"""

    def test_complete_coverage(self, sample_prd_heading_format):
        """Test when all stories are requested"""
        coverage = validate_story_coverage(
            sample_prd_heading_format,
            ["20.1", "20.2", "20.3", "20.4"]
        )

        assert coverage["is_complete"] is True
        assert coverage["prd_stories"] == ["20.1", "20.2", "20.3", "20.4"]
        assert coverage["requested_stories"] == ["20.1", "20.2", "20.3", "20.4"]
        assert coverage["missing_stories"] == []
        assert coverage["extra_stories"] == []

    def test_partial_coverage(self, sample_prd_heading_format):
        """Test when some stories are missing"""
        coverage = validate_story_coverage(
            sample_prd_heading_format,
            ["20.1"]
        )

        assert coverage["is_complete"] is False
        assert coverage["prd_stories"] == ["20.1", "20.2", "20.3", "20.4"]
        assert coverage["requested_stories"] == ["20.1"]
        assert coverage["missing_stories"] == ["20.2", "20.3", "20.4"]
        assert coverage["extra_stories"] == []

    def test_extra_stories_requested(self, sample_prd_heading_format):
        """Test when extra stories are requested that don't exist in PRD"""
        coverage = validate_story_coverage(
            sample_prd_heading_format,
            ["20.1", "20.2", "20.3", "20.4", "20.5", "20.6"]
        )

        assert coverage["is_complete"] is False
        assert coverage["missing_stories"] == []
        assert coverage["extra_stories"] == ["20.5", "20.6"]

    def test_empty_request(self, sample_prd_heading_format):
        """Test when no stories are requested"""
        coverage = validate_story_coverage(
            sample_prd_heading_format,
            []
        )

        assert coverage["is_complete"] is False
        assert coverage["requested_stories"] == []
        assert coverage["missing_stories"] == ["20.1", "20.2", "20.3", "20.4"]

    def test_none_request(self, sample_prd_heading_format):
        """Test when None is passed as requested stories"""
        coverage = validate_story_coverage(
            sample_prd_heading_format,
            None
        )

        assert coverage["is_complete"] is False
        assert coverage["requested_stories"] == []
        assert coverage["missing_stories"] == ["20.1", "20.2", "20.3", "20.4"]

    def test_empty_prd_coverage(self, sample_prd_empty):
        """Test coverage validation on empty PRD"""
        coverage = validate_story_coverage(
            sample_prd_empty,
            ["99.1", "99.2"]
        )

        assert coverage["is_complete"] is False
        assert coverage["prd_stories"] == []
        assert coverage["missing_stories"] == []
        assert coverage["extra_stories"] == ["99.1", "99.2"]


# ============================================================================
# Test: find_epic_prd_file
# ============================================================================


class TestFindEpicPrdFile:
    """Tests for find_epic_prd_file function"""

    def test_find_uppercase_epic(self, sample_prd_heading_format):
        """Test finding EPIC-XX format file"""
        base = sample_prd_heading_format.parent.parent.parent
        prd_file = find_epic_prd_file(base, 20)

        assert prd_file is not None
        assert prd_file.name == "EPIC-20-BACKEND-STABILITY.md"

    def test_find_lowercase_epic(self, temp_project_dir):
        """Test finding epic-XX format file"""
        prd_content = "# epic-25: Test\n\n### Story 25.1: Test"
        prd_file = temp_project_dir / "docs" / "prd" / "epic-25-test.md"
        prd_file.write_text(prd_content, encoding="utf-8")

        found = find_epic_prd_file(temp_project_dir, 25)

        assert found is not None
        assert found.name == "epic-25-test.md"

    def test_find_mixed_case_epic(self, temp_project_dir):
        """Test finding Epic-XX format file"""
        prd_content = "# Epic-26: Test\n\n### Story 26.1: Test"
        prd_file = temp_project_dir / "docs" / "prd" / "Epic-26-test.md"
        prd_file.write_text(prd_content, encoding="utf-8")

        found = find_epic_prd_file(temp_project_dir, 26)

        assert found is not None
        assert found.name == "Epic-26-test.md"

    def test_find_nonexistent_epic(self, temp_project_dir):
        """Test finding non-existent epic"""
        found = find_epic_prd_file(temp_project_dir, 999)

        assert found is None

    def test_find_without_prd_dir(self, temp_project_dir):
        """Test finding when docs/prd doesn't exist"""
        # Remove prd directory
        import shutil
        shutil.rmtree(temp_project_dir / "docs")

        found = find_epic_prd_file(temp_project_dir, 20)

        assert found is None


# ============================================================================
# Test: get_epic_id_from_story
# ============================================================================


class TestGetEpicIdFromStory:
    """Tests for get_epic_id_from_story function"""

    def test_valid_story_id(self):
        """Test extraction from valid story ID"""
        assert get_epic_id_from_story("20.1") == 20
        assert get_epic_id_from_story("21.5") == 21
        assert get_epic_id_from_story("1.1") == 1
        assert get_epic_id_from_story("100.10") == 100

    def test_invalid_story_id(self):
        """Test extraction from invalid story ID"""
        assert get_epic_id_from_story("invalid") is None
        assert get_epic_id_from_story("") is None
        assert get_epic_id_from_story("abc.def") is None

    def test_edge_cases(self):
        """Test edge cases"""
        # No decimal point
        assert get_epic_id_from_story("20") == 20

        # Multiple decimal points (takes first part)
        assert get_epic_id_from_story("20.1.1") == 20


# ============================================================================
# Integration Tests
# ============================================================================


class TestPrdParserIntegration:
    """Integration tests for PRD parser workflow"""

    def test_complete_workflow_epic_20(self, sample_prd_heading_format):
        """Test complete workflow: find file -> extract stories -> validate"""
        base = sample_prd_heading_format.parent.parent.parent

        # Step 1: Find PRD file
        prd_file = find_epic_prd_file(base, 20)
        assert prd_file is not None

        # Step 2: Extract stories
        stories = extract_stories_from_prd(prd_file)
        assert stories == ["20.1", "20.2", "20.3", "20.4"]

        # Step 3: Validate coverage (simulating manual --stories "20.1")
        coverage = validate_story_coverage(prd_file, ["20.1"])
        assert coverage["is_complete"] is False
        assert coverage["missing_stories"] == ["20.2", "20.3", "20.4"]

        # Step 4: Validate coverage (with auto-discover, all stories)
        coverage_full = validate_story_coverage(prd_file, stories)
        assert coverage_full["is_complete"] is True
        assert coverage_full["missing_stories"] == []

    def test_auto_discover_simulation(self, sample_prd_story_id_format):
        """Simulate --auto-discover flag behavior"""
        base = sample_prd_story_id_format.parent.parent.parent

        # Find PRD
        prd_file = find_epic_prd_file(base, 21)
        assert prd_file is not None

        # Auto-discover: extract all stories
        auto_discovered = extract_stories_from_prd(prd_file)
        assert len(auto_discovered) == 6

        # Validate complete coverage
        coverage = validate_story_coverage(prd_file, auto_discovered)
        assert coverage["is_complete"] is True

        # Verify all Epic IDs are correct
        for story_id in auto_discovered:
            epic_id = get_epic_id_from_story(story_id)
            assert epic_id == 21
