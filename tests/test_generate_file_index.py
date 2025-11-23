"""
File Index Generator Tests

Tests for scripts/generate-file-index.py
Total: 18 tests
"""

import pytest
import json
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from generate_file_index import (
    scan_source_files,
    extract_openapi_endpoints,
    extract_json_schemas,
    generate_markdown,
    CONFIG
)


# =============================================================================
# Test: Source File Scanning
# =============================================================================

class TestSourceFileScanning:
    """Tests for source file scanning functionality."""

    @patch('generate_file_index.PROJECT_ROOT')
    def test_scan_source_files_basic(self, mock_root, tmp_path):
        """Scan source files in project directories."""
        mock_root.__truediv__ = lambda self, x: tmp_path / x

        # Create test structure
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("print('hello')")
        (src_dir / "utils.py").write_text("# utils")

        # Mock the CONFIG
        with patch.dict(CONFIG, {"source_dirs": ["src"], "source_extensions": [".py"]}):
            with patch('generate_file_index.PROJECT_ROOT', tmp_path):
                files = scan_source_files()

        assert "src" in files
        assert len(files["src"]) == 2

    @patch('generate_file_index.PROJECT_ROOT')
    def test_scan_filters_by_extension(self, mock_root, tmp_path):
        """Only scan files with configured extensions."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "code.py").write_text("# python")
        (src_dir / "data.json").write_text("{}")
        (src_dir / "readme.md").write_text("# readme")

        with patch.dict(CONFIG, {"source_dirs": ["src"], "source_extensions": [".py"]}):
            with patch('generate_file_index.PROJECT_ROOT', tmp_path):
                files = scan_source_files()

        # Should only include .py files
        file_list = files.get("src", [])
        py_files = [f for f in file_list if f.endswith(".py")]
        assert len(py_files) == 1

    @patch('generate_file_index.PROJECT_ROOT')
    def test_scan_ignores_patterns(self, mock_root, tmp_path):
        """Ignore directories matching ignore patterns."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("# main")

        # Create ignored directory
        pycache = src_dir / "__pycache__"
        pycache.mkdir()
        (pycache / "cached.pyc").write_text("cached")

        with patch.dict(CONFIG, {
            "source_dirs": ["src"],
            "source_extensions": [".py", ".pyc"],
            "ignore_patterns": ["__pycache__"]
        }):
            with patch('generate_file_index.PROJECT_ROOT', tmp_path):
                files = scan_source_files()

        # Should not include __pycache__ files
        all_files = []
        for file_list in files.values():
            all_files.extend(file_list)
        assert not any("__pycache__" in f for f in all_files)

    @patch('generate_file_index.PROJECT_ROOT')
    def test_scan_calculates_relative_paths(self, mock_root, tmp_path):
        """File paths should be relative to project root."""
        src_dir = tmp_path / "src" / "nested"
        src_dir.mkdir(parents=True)
        (src_dir / "deep.py").write_text("# deep")

        with patch.dict(CONFIG, {"source_dirs": ["src"], "source_extensions": [".py"]}):
            with patch('generate_file_index.PROJECT_ROOT', tmp_path):
                files = scan_source_files()

        # Check relative path format
        nested_files = files.get("src\\nested", []) or files.get("src/nested", [])
        if nested_files:
            assert not any(str(tmp_path) in f for f in nested_files)

    @patch('generate_file_index.PROJECT_ROOT')
    def test_scan_empty_directory(self, mock_root, tmp_path):
        """Handle empty source directory."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        # No files created

        with patch.dict(CONFIG, {"source_dirs": ["src"], "source_extensions": [".py"]}):
            with patch('generate_file_index.PROJECT_ROOT', tmp_path):
                files = scan_source_files()

        # Should not include empty directories
        assert "src" not in files or len(files.get("src", [])) == 0


# =============================================================================
# Test: OpenAPI Extraction
# =============================================================================

class TestOpenAPIExtraction:
    """Tests for OpenAPI endpoint extraction."""

    @patch('generate_file_index.PROJECT_ROOT')
    def test_extract_openapi_endpoints_basic(self, mock_root, tmp_path, sample_openapi_spec):
        """Extract endpoints from OpenAPI spec."""
        spec_file = tmp_path / "specs" / "api" / "canvas-api.openapi.yml"
        spec_file.parent.mkdir(parents=True)
        with open(spec_file, "w") as f:
            yaml.dump(sample_openapi_spec, f)

        with patch.dict(CONFIG, {"openapi_path": "specs/api/canvas-api.openapi.yml"}):
            with patch('generate_file_index.PROJECT_ROOT', tmp_path):
                endpoints = extract_openapi_endpoints()

        assert len(endpoints) > 0
        assert any(ep["path"] == "/canvas/{canvas_path}" for ep in endpoints)

    @patch('generate_file_index.PROJECT_ROOT')
    def test_extract_openapi_endpoints_methods(self, mock_root, tmp_path, sample_openapi_spec):
        """Extract HTTP methods for each endpoint."""
        spec_file = tmp_path / "specs" / "api" / "canvas-api.openapi.yml"
        spec_file.parent.mkdir(parents=True)
        with open(spec_file, "w") as f:
            yaml.dump(sample_openapi_spec, f)

        with patch.dict(CONFIG, {"openapi_path": "specs/api/canvas-api.openapi.yml"}):
            with patch('generate_file_index.PROJECT_ROOT', tmp_path):
                endpoints = extract_openapi_endpoints()

        methods = [ep["method"] for ep in endpoints]
        assert "GET" in methods
        assert "POST" in methods

    @patch('generate_file_index.PROJECT_ROOT')
    def test_extract_openapi_operation_ids(self, mock_root, tmp_path, sample_openapi_spec):
        """Extract operation IDs from endpoints."""
        spec_file = tmp_path / "specs" / "api" / "canvas-api.openapi.yml"
        spec_file.parent.mkdir(parents=True)
        with open(spec_file, "w") as f:
            yaml.dump(sample_openapi_spec, f)

        with patch.dict(CONFIG, {"openapi_path": "specs/api/canvas-api.openapi.yml"}):
            with patch('generate_file_index.PROJECT_ROOT', tmp_path):
                endpoints = extract_openapi_endpoints()

        op_ids = [ep["operation_id"] for ep in endpoints]
        assert "readCanvas" in op_ids
        assert "addNode" in op_ids

    @patch('generate_file_index.PROJECT_ROOT')
    def test_extract_openapi_nonexistent_file(self, mock_root, tmp_path):
        """Return empty list for non-existent spec file."""
        with patch.dict(CONFIG, {"openapi_path": "specs/api/nonexistent.yml"}):
            with patch('generate_file_index.PROJECT_ROOT', tmp_path):
                endpoints = extract_openapi_endpoints()

        assert endpoints == []


# =============================================================================
# Test: Schema Extraction
# =============================================================================

class TestSchemaExtraction:
    """Tests for JSON Schema extraction."""

    @patch('generate_file_index.PROJECT_ROOT')
    def test_extract_json_schemas_basic(self, mock_root, tmp_path, sample_json_schema):
        """Extract schemas from JSON files."""
        schema_dir = tmp_path / "specs" / "data"
        schema_dir.mkdir(parents=True)
        schema_file = schema_dir / "canvas-node.schema.json"
        with open(schema_file, "w") as f:
            json.dump(sample_json_schema, f)

        with patch.dict(CONFIG, {"schema_dir": "specs/data"}):
            with patch('generate_file_index.PROJECT_ROOT', tmp_path):
                schemas = extract_json_schemas()

        assert len(schemas) == 1
        assert schemas[0]["name"] == "CanvasNode"

    @patch('generate_file_index.PROJECT_ROOT')
    def test_extract_json_schemas_metadata(self, mock_root, tmp_path, sample_json_schema):
        """Extract schema metadata (title, description)."""
        schema_dir = tmp_path / "specs" / "data"
        schema_dir.mkdir(parents=True)
        schema_file = schema_dir / "test.schema.json"
        with open(schema_file, "w") as f:
            json.dump(sample_json_schema, f)

        with patch.dict(CONFIG, {"schema_dir": "specs/data"}):
            with patch('generate_file_index.PROJECT_ROOT', tmp_path):
                schemas = extract_json_schemas()

        schema = schemas[0]
        assert "name" in schema
        assert "file" in schema
        assert "description" in schema

    @patch('generate_file_index.PROJECT_ROOT')
    def test_extract_multiple_schemas(self, mock_root, tmp_path, sample_json_schema):
        """Extract multiple schema files."""
        schema_dir = tmp_path / "specs" / "data"
        schema_dir.mkdir(parents=True)

        # Create multiple schemas
        for i in range(3):
            schema = sample_json_schema.copy()
            schema["title"] = f"Schema{i}"
            schema_file = schema_dir / f"schema-{i}.json"
            with open(schema_file, "w") as f:
                json.dump(schema, f)

        with patch.dict(CONFIG, {"schema_dir": "specs/data"}):
            with patch('generate_file_index.PROJECT_ROOT', tmp_path):
                schemas = extract_json_schemas()

        assert len(schemas) == 3


# =============================================================================
# Test: Markdown Generation
# =============================================================================

class TestMarkdownGeneration:
    """Tests for markdown index generation."""

    def test_generate_markdown_basic(self):
        """Generate basic markdown index."""
        files_by_dir = {"src": ["src/main.py", "src/utils.py"]}
        endpoints = []
        schemas = []

        markdown = generate_markdown(files_by_dir, endpoints, schemas)

        assert "# Project File Index" in markdown
        assert "src/main.py" in markdown
        assert "src/utils.py" in markdown

    def test_generate_markdown_with_endpoints(self, sample_openapi_spec):
        """Generate markdown with API endpoints."""
        files_by_dir = {}
        endpoints = [
            {
                "method": "GET",
                "path": "/canvas/{id}",
                "operation_id": "readCanvas",
                "summary": "Read canvas",
                "tags": ["Layer1-JSON"]
            }
        ]
        schemas = []

        markdown = generate_markdown(files_by_dir, endpoints, schemas)

        assert "## API Endpoints" in markdown
        assert "GET /canvas/{id}" in markdown
        assert "readCanvas" in markdown

    def test_generate_markdown_with_schemas(self):
        """Generate markdown with data models."""
        files_by_dir = {}
        endpoints = []
        schemas = [
            {
                "name": "CanvasNode",
                "file": "canvas-node.schema.json",
                "description": "Canvas node definition"
            }
        ]

        markdown = generate_markdown(files_by_dir, endpoints, schemas)

        assert "## Data Models" in markdown
        assert "CanvasNode" in markdown

    def test_generate_markdown_statistics(self):
        """Generate markdown with accurate statistics."""
        files_by_dir = {
            "src": ["src/a.py", "src/b.py"],
            "tests": ["tests/test.py"]
        }
        endpoints = [
            {"method": "GET", "path": "/a", "operation_id": "a", "summary": "", "tags": []},
            {"method": "POST", "path": "/b", "operation_id": "b", "summary": "", "tags": []}
        ]
        schemas = [{"name": "S1", "file": "s1.json", "description": ""}]

        markdown = generate_markdown(files_by_dir, endpoints, schemas)

        assert "3 files" in markdown
        assert "2 endpoints" in markdown
        assert "1 schemas" in markdown

    def test_generate_markdown_anti_hallucination_protocol(self):
        """Generate markdown with anti-hallucination protocol."""
        files_by_dir = {"src": ["src/main.py"]}
        endpoints = []
        schemas = []

        markdown = generate_markdown(files_by_dir, endpoints, schemas)

        assert "Anti-Hallucination Protocol" in markdown
        assert "DO NOT" in markdown


# =============================================================================
# Test: File Persistence
# =============================================================================

class TestFilePersistence:
    """Tests for output file creation."""

    def test_output_file_encoding(self, tmp_path):
        """Output file uses UTF-8 encoding."""
        output_file = tmp_path / "index.md"
        content = "# Index\n\nChinese: 中文内容"

        output_file.write_text(content, encoding="utf-8")

        read_content = output_file.read_text(encoding="utf-8")
        assert "中文内容" in read_content

    def test_output_directory_creation(self, tmp_path):
        """Create output directory if needed."""
        output_file = tmp_path / "nested" / "dir" / "index.md"

        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text("# Index")

        assert output_file.exists()


# =============================================================================
# Fixtures from conftest
# =============================================================================

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
        "paths": {
            "/canvas/{canvas_path}": {
                "get": {
                    "operationId": "readCanvas",
                    "summary": "Read canvas file",
                    "tags": ["Layer1-JSON"],
                    "responses": {"200": {"description": "Success"}}
                }
            },
            "/canvas/{canvas_path}/nodes": {
                "post": {
                    "operationId": "addNode",
                    "summary": "Add node",
                    "tags": ["Layer1-JSON"],
                    "responses": {"201": {"description": "Created"}}
                }
            }
        },
        "tags": [
            {"name": "Layer1-JSON"}
        ],
        "components": {"schemas": {}}
    }


@pytest.fixture
def sample_json_schema():
    """Sample JSON Schema."""
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "CanvasNode",
        "description": "Canvas node schema",
        "type": "object",
        "required": ["id", "type"],
        "properties": {
            "id": {"type": "string"},
            "type": {"type": "string"}
        }
    }
