"""
Planning Iteration Testing Fixtures

Shared fixtures for planning iteration tests.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime


# =============================================================================
# Directory Fixtures
# =============================================================================

@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory with basic structure."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create basic structure
    (project_dir / "docs" / "prd").mkdir(parents=True)
    (project_dir / "docs" / "architecture").mkdir(parents=True)
    (project_dir / "docs" / "epics").mkdir(parents=True)
    (project_dir / "specs" / "api").mkdir(parents=True)
    (project_dir / "specs" / "data").mkdir(parents=True)
    (project_dir / ".bmad-core" / "planning-iterations" / "snapshots").mkdir(parents=True)

    return project_dir


@pytest.fixture
def temp_git_repo(temp_project_dir):
    """Initialize a git repository in the temp project directory."""
    import subprocess

    subprocess.run(
        ["git", "init"],
        cwd=temp_project_dir,
        capture_output=True,
        check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=temp_project_dir,
        capture_output=True,
        check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=temp_project_dir,
        capture_output=True,
        check=True
    )

    return temp_project_dir


# =============================================================================
# Sample File Fixtures
# =============================================================================

@pytest.fixture
def sample_prd_content():
    """Sample PRD markdown content with frontmatter."""
    return '''---
title: "Epic 1 - Core Learning System"
version: "1.0.0"
status: "approved"
last_updated: "2025-01-15"
---

# Epic 1: Core Learning System

## Overview
This epic covers the core learning system functionality.

## User Stories
- Story 1.1: Basic node creation
- Story 1.2: Color assignment
'''


@pytest.fixture
def sample_architecture_content():
    """Sample architecture markdown content."""
    return '''---
title: "Canvas Layer Architecture"
version: "2.0.0"
---

# Canvas Layer Architecture

## Layer 1: JSON Operations
Basic CRUD operations on canvas files.

## Layer 2: Business Logic
Color-based workflow management.
'''


@pytest.fixture
def sample_openapi_spec():
    """Sample OpenAPI specification."""
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Canvas API",
            "version": "1.0.0",
            "description": "Canvas Learning System API"
        },
        "servers": [
            {"url": "http://localhost:8000/api/v1"}
        ],
        "paths": {
            "/canvas/{canvas_path}": {
                "get": {
                    "operationId": "readCanvas",
                    "summary": "Read canvas file",
                    "tags": ["Layer1-JSON"],
                    "parameters": [
                        {
                            "name": "canvas_path",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Canvas data",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/CanvasData"}
                                }
                            }
                        }
                    }
                }
            },
            "/canvas/{canvas_path}/nodes": {
                "post": {
                    "operationId": "addNode",
                    "summary": "Add node to canvas",
                    "tags": ["Layer1-JSON"],
                    "responses": {
                        "201": {"description": "Node created"}
                    }
                }
            }
        },
        "tags": [
            {"name": "Layer1-JSON", "description": "JSON operations"},
            {"name": "Layer2-Business", "description": "Business logic"},
            {"name": "Layer3-Orchestrator", "description": "Agent orchestration"},
            {"name": "Layer4-Knowledge", "description": "Knowledge graph"}
        ],
        "components": {
            "schemas": {
                "CanvasData": {
                    "type": "object",
                    "properties": {
                        "nodes": {"type": "array"},
                        "edges": {"type": "array"}
                    }
                },
                "CanvasNode": {
                    "type": "object",
                    "required": ["id", "type", "x", "y", "width", "height"],
                    "properties": {
                        "id": {"type": "string"},
                        "type": {"type": "string", "enum": ["text", "file", "group", "link"]},
                        "x": {"type": "number"},
                        "y": {"type": "number"},
                        "width": {"type": "number"},
                        "height": {"type": "number"},
                        "color": {"type": "string", "enum": ["1", "2", "3", "5", "6"]}
                    }
                },
                "NodeInput": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "text": {"type": "string"}
                    }
                }
            }
        }
    }


@pytest.fixture
def sample_json_schema():
    """Sample JSON Schema for canvas node."""
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "CanvasNode",
        "description": "Canvas node schema",
        "type": "object",
        "required": ["id", "type", "x", "y", "width", "height"],
        "properties": {
            "id": {
                "type": "string",
                "pattern": "^[a-f0-9-]{36}$"
            },
            "type": {
                "type": "string",
                "enum": ["text", "file", "group", "link"]
            },
            "x": {"type": "number"},
            "y": {"type": "number"},
            "width": {"type": "number"},
            "height": {"type": "number"},
            "color": {
                "type": "string",
                "enum": ["1", "2", "3", "5", "6"]
            },
            "text": {"type": "string"},
            "file": {"type": "string"}
        }
    }


# =============================================================================
# Snapshot Fixtures
# =============================================================================

@pytest.fixture
def sample_snapshot():
    """Sample iteration snapshot."""
    return {
        "iteration": 1,
        "timestamp": "2025-01-15T10:00:00",
        "git_sha": "abc123def456",
        "description": "Initial iteration",
        "files": {
            "prd": [
                {
                    "path": "docs/prd/epic-1.md",
                    "hash": "sha256:abc123...",
                    "version": "1.0.0",
                    "size": 1024
                }
            ],
            "architecture": [
                {
                    "path": "docs/architecture/canvas-layer.md",
                    "hash": "sha256:def456...",
                    "version": "2.0.0",
                    "size": 2048
                }
            ],
            "api_specs": [
                {
                    "path": "specs/api/canvas-api.openapi.yml",
                    "hash": "sha256:ghi789...",
                    "version": "1.0.0",
                    "endpoints": 12
                }
            ],
            "schemas": [
                {
                    "path": "specs/data/canvas-node.schema.json",
                    "hash": "sha256:jkl012...",
                    "title": "CanvasNode"
                }
            ]
        },
        "statistics": {
            "total_files": 4,
            "total_endpoints": 12,
            "total_schemas": 1
        }
    }


@pytest.fixture
def previous_snapshot(sample_snapshot):
    """Previous iteration snapshot for comparison."""
    return sample_snapshot


@pytest.fixture
def current_snapshot(sample_snapshot):
    """Current iteration snapshot with changes."""
    snapshot = sample_snapshot.copy()
    snapshot["iteration"] = 2
    snapshot["timestamp"] = "2025-01-16T10:00:00"
    snapshot["git_sha"] = "xyz789abc012"
    snapshot["description"] = "Updated iteration"

    # Update file hashes and versions
    snapshot["files"] = {
        "prd": [
            {
                "path": "docs/prd/epic-1.md",
                "hash": "sha256:updated123...",
                "version": "1.1.0",
                "size": 1124
            }
        ],
        "architecture": [
            {
                "path": "docs/architecture/canvas-layer.md",
                "hash": "sha256:def456...",  # Same
                "version": "2.0.0",
                "size": 2048
            }
        ],
        "api_specs": [
            {
                "path": "specs/api/canvas-api.openapi.yml",
                "hash": "sha256:newspec...",
                "version": "1.1.0",
                "endpoints": 14  # Added 2 endpoints
            }
        ],
        "schemas": [
            {
                "path": "specs/data/canvas-node.schema.json",
                "hash": "sha256:jkl012...",
                "title": "CanvasNode"
            }
        ]
    }

    return snapshot


@pytest.fixture
def breaking_change_snapshot(sample_snapshot):
    """Snapshot with breaking changes (deleted endpoint, removed field)."""
    import copy
    snapshot = copy.deepcopy(sample_snapshot)
    snapshot["iteration"] = 2
    snapshot["files"]["api_specs"][0]["endpoints"] = 10  # Deleted 2 endpoints
    return snapshot


# =============================================================================
# Validation Rules Fixtures
# =============================================================================

@pytest.fixture
def sample_validation_rules():
    """Sample iteration validation rules."""
    return {
        "version": "1.0",
        "rules": {
            "prd": {
                "version_must_increment": True,
                "file_deletion_is_breaking": True
            },
            "architecture": {
                "version_must_increment": True
            },
            "api_specs": {
                "endpoint_deletion_is_breaking": True,
                "required_field_removal_is_breaking": True
            },
            "schemas": {
                "required_field_removal_is_breaking": True,
                "enum_value_removal_is_breaking": True
            }
        }
    }


# =============================================================================
# Helper Functions
# =============================================================================

@pytest.fixture
def create_prd_file(temp_project_dir, sample_prd_content):
    """Factory fixture to create PRD files."""
    def _create(filename="epic-1.md", content=None):
        file_path = temp_project_dir / "docs" / "prd" / filename
        file_path.write_text(content or sample_prd_content, encoding="utf-8")
        return file_path
    return _create


@pytest.fixture
def create_architecture_file(temp_project_dir, sample_architecture_content):
    """Factory fixture to create architecture files."""
    def _create(filename="canvas-layer.md", content=None):
        file_path = temp_project_dir / "docs" / "architecture" / filename
        file_path.write_text(content or sample_architecture_content, encoding="utf-8")
        return file_path
    return _create


@pytest.fixture
def create_openapi_file(temp_project_dir, sample_openapi_spec):
    """Factory fixture to create OpenAPI spec files."""
    import yaml

    def _create(filename="canvas-api.openapi.yml", spec=None):
        file_path = temp_project_dir / "specs" / "api" / filename
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(spec or sample_openapi_spec, f, allow_unicode=True)
        return file_path
    return _create


@pytest.fixture
def create_schema_file(temp_project_dir, sample_json_schema):
    """Factory fixture to create JSON schema files."""
    def _create(filename="canvas-node.schema.json", schema=None):
        file_path = temp_project_dir / "specs" / "data" / filename
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(schema or sample_json_schema, f, indent=2)
        return file_path
    return _create


@pytest.fixture
def create_snapshot_file(temp_project_dir, sample_snapshot):
    """Factory fixture to create snapshot files."""
    def _create(iteration=1, snapshot_data=None):
        file_path = (
            temp_project_dir / ".bmad-core" / "planning-iterations" /
            "snapshots" / f"iteration-{iteration:03d}.json"
        )
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(snapshot_data or sample_snapshot, f, indent=2)
        return file_path
    return _create


# =============================================================================
# Pytest Configuration
# =============================================================================

def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests"
    )
    config.addinivalue_line(
        "markers", "planning: Planning iteration tests"
    )
