# Canvas Learning System - Story 30.19 API Tests
# Metadata Subject Mapping API Endpoint Integration Tests
"""
Story 30.19 - SubjectMapping 学科映射配置 UI 验证与测试补全

Task 2: Metadata API endpoint integration tests
- GET /config/subject-mapping
- POST /config/subject-mapping/add
- DELETE /config/subject-mapping/remove
- PUT /config/subject-mapping
- GET /metadata?canvas_path=...

[Source: docs/epics/EPIC-30-MEMORY-SYSTEM-COMPLETE-ACTIVATION.md]
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from fastapi.testclient import TestClient

from app.models.metadata_models import SubjectMappingConfig, SubjectMappingRule
from app.services.subject_resolver import SubjectResolver


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def test_config_path(tmp_path):
    """Create a temporary YAML config for API tests."""
    config_data = {
        "mappings": [
            {"pattern": "Math 54/**", "subject": "math54", "category": "math"},
            {"pattern": "Physics 7A/**", "subject": "physics7a", "category": "physics"},
        ],
        "category_rules": {
            "math": ["math*", "数学*"],
            "physics": ["physics*", "物理*"],
        },
        "defaults": {"subject": "general", "category": "general"},
        "skip_directories": [".obsidian", ".git"],
    }
    config_path = tmp_path / "test_subject_mapping.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, allow_unicode=True, sort_keys=False)
    return str(config_path)


@pytest.fixture
def test_resolver(test_config_path):
    """Create a test SubjectResolver."""
    return SubjectResolver(config_path=test_config_path)


@pytest.fixture
def client(test_resolver):
    """Create a test client with DI overrides."""
    from app.main import app
    from app.api.v1.endpoints.metadata import get_resolver

    app.dependency_overrides[get_resolver] = lambda: test_resolver

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.pop(get_resolver, None)


# =============================================================================
# Task 2.1: GET /config/subject-mapping
# =============================================================================


class TestGetSubjectMapping:
    """AC-30.19.2: GET /config/subject-mapping returns current config."""

    def test_get_returns_200(self, client):
        """GET should return 200 with current config."""
        response = client.get("/api/v1/canvas-meta/config/subject-mapping")
        assert response.status_code == 200

    def test_get_returns_mappings(self, client):
        """Response should include mappings from config."""
        response = client.get("/api/v1/canvas-meta/config/subject-mapping")
        data = response.json()
        assert "mappings" in data
        assert len(data["mappings"]) == 2

    def test_get_returns_correct_mapping_structure(self, client):
        """Each mapping should have pattern, subject, category."""
        response = client.get("/api/v1/canvas-meta/config/subject-mapping")
        data = response.json()
        first_mapping = data["mappings"][0]
        assert "pattern" in first_mapping
        assert "subject" in first_mapping
        assert "category" in first_mapping

    def test_get_returns_category_rules(self, client):
        """Response should include category_rules."""
        response = client.get("/api/v1/canvas-meta/config/subject-mapping")
        data = response.json()
        assert "category_rules" in data
        assert "math" in data["category_rules"]

    def test_get_returns_defaults(self, client):
        """Response should include defaults."""
        response = client.get("/api/v1/canvas-meta/config/subject-mapping")
        data = response.json()
        assert "defaults" in data
        assert data["defaults"]["subject"] == "general"


# =============================================================================
# Task 2.2: POST /config/subject-mapping/add
# =============================================================================


class TestAddSubjectMapping:
    """AC-30.19.2: POST /config/subject-mapping/add adds mapping rule."""

    def test_add_returns_200(self, client):
        """POST add should return 200."""
        response = client.post(
            "/api/v1/canvas-meta/config/subject-mapping/add",
            params={
                "pattern": "Biology/**",
                "subject": "bio",
                "category": "biology",
            },
        )
        assert response.status_code == 200

    def test_add_includes_new_mapping_in_response(self, client):
        """Response should include the newly added mapping."""
        client.post(
            "/api/v1/canvas-meta/config/subject-mapping/add",
            params={
                "pattern": "Chemistry/**",
                "subject": "chem",
                "category": "chemistry",
            },
        )
        # Verify via GET
        response = client.get("/api/v1/canvas-meta/config/subject-mapping")
        data = response.json()
        patterns = [m["pattern"] for m in data["mappings"]]
        assert "Chemistry/**" in patterns

    def test_add_duplicate_updates_existing(self, client):
        """Adding duplicate pattern should update, not create new."""
        # Add first time
        client.post(
            "/api/v1/canvas-meta/config/subject-mapping/add",
            params={
                "pattern": "Math 54/**",
                "subject": "math54-v2",
                "category": "math-v2",
            },
        )

        response = client.get("/api/v1/canvas-meta/config/subject-mapping")
        data = response.json()

        # Should still have same number of mappings (2, not 3)
        math54_mappings = [
            m for m in data["mappings"]
            if m["pattern"].lower() == "math 54/**"
        ]
        assert len(math54_mappings) == 1
        assert math54_mappings[0]["subject"] == "math54-v2"

    def test_add_requires_all_params(self, client):
        """POST add should require pattern, subject, and category."""
        response = client.post(
            "/api/v1/canvas-meta/config/subject-mapping/add",
            params={"pattern": "Test/**"},
        )
        assert response.status_code == 422


# =============================================================================
# Task 2.3: DELETE /config/subject-mapping/remove
# =============================================================================


class TestRemoveSubjectMapping:
    """AC-30.19.2: DELETE /config/subject-mapping/remove removes rule."""

    def test_remove_existing_returns_200(self, client):
        """Removing existing mapping should return 200."""
        response = client.delete(
            "/api/v1/canvas-meta/config/subject-mapping/remove",
            params={"pattern": "Physics 7A/**"},
        )
        assert response.status_code == 200

    def test_remove_reflects_in_config(self, client):
        """Removed mapping should not appear in subsequent GET."""
        client.delete(
            "/api/v1/canvas-meta/config/subject-mapping/remove",
            params={"pattern": "Physics 7A/**"},
        )

        response = client.get("/api/v1/canvas-meta/config/subject-mapping")
        data = response.json()
        patterns = [m["pattern"] for m in data["mappings"]]
        assert "Physics 7A/**" not in patterns

    def test_remove_nonexistent_returns_404(self, client):
        """Removing non-existent mapping should return 404."""
        response = client.delete(
            "/api/v1/canvas-meta/config/subject-mapping/remove",
            params={"pattern": "NonExistent/**"},
        )
        assert response.status_code == 404


# =============================================================================
# Task 2.4: PUT /config/subject-mapping
# =============================================================================


class TestUpdateSubjectMapping:
    """AC-30.19.2: PUT /config/subject-mapping bulk update."""

    def test_update_returns_200(self, client):
        """PUT should return 200."""
        new_config = {
            "mappings": [
                {"pattern": "NewPattern/**", "subject": "new", "category": "new"},
            ],
            "category_rules": {"new": ["new*"]},
            "defaults": {"subject": "default-new", "category": "default-new"},
        }
        response = client.put(
            "/api/v1/canvas-meta/config/subject-mapping",
            json=new_config,
        )
        assert response.status_code == 200

    def test_update_replaces_config(self, client):
        """PUT should replace entire config."""
        new_config = {
            "mappings": [
                {"pattern": "Only/**", "subject": "only", "category": "only"},
            ],
            "category_rules": {},
            "defaults": {"subject": "only-default", "category": "only-default"},
        }
        client.put("/api/v1/canvas-meta/config/subject-mapping", json=new_config)

        response = client.get("/api/v1/canvas-meta/config/subject-mapping")
        data = response.json()
        assert len(data["mappings"]) == 1
        assert data["mappings"][0]["pattern"] == "Only/**"


# =============================================================================
# Task 2.5: GET /metadata?canvas_path=...
# =============================================================================


class TestGetMetadata:
    """AC-30.19.2: GET /metadata returns correct subject resolution."""

    def test_metadata_config_match(self, client):
        """Canvas path matching config should return CONFIG source."""
        response = client.get(
            "/api/v1/canvas-meta/metadata",
            params={"canvas_path": "Math 54/离散数学.canvas"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["subject"] == "math54"
        assert data["category"] == "math"
        assert data["source"] == "config"
        assert "group_id" in data

    def test_metadata_default_fallback(self, client):
        """Unmatched path should return DEFAULT source."""
        response = client.get(
            "/api/v1/canvas-meta/metadata",
            params={"canvas_path": "random.canvas"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "default"
        assert data["subject"] == "general"

    def test_metadata_ignores_extra_params(self, client):
        """Extra query params (subject/category) are ignored by endpoint."""
        response = client.get(
            "/api/v1/canvas-meta/metadata",
            params={
                "canvas_path": "Math 54/test.canvas",
                "subject": "custom",
                "category": "custom-cat",
            },
        )
        assert response.status_code == 200
        data = response.json()
        # API endpoint only accepts canvas_path, ignores subject/category
        assert data["source"] == "config"
        assert data["subject"] == "math54"

    def test_metadata_requires_canvas_path(self, client):
        """GET /metadata without canvas_path should return 422."""
        response = client.get("/api/v1/canvas-meta/metadata")
        assert response.status_code == 422

    def test_metadata_group_id_format(self, client):
        """group_id should be subject:canvas_name format."""
        response = client.get(
            "/api/v1/canvas-meta/metadata",
            params={"canvas_path": "Math 54/线性代数.canvas"},
        )
        data = response.json()
        assert data["group_id"] == "math54:线性代数"
