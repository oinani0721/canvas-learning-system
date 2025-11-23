"""
Contract Testing Fixtures and Configuration

Provides shared fixtures for contract testing.
"""

import pytest
import json
import yaml
from pathlib import Path

# Project directories
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_DIR = PROJECT_ROOT / "specs" / "data"
API_SPEC_DIR = PROJECT_ROOT / "specs" / "api"


@pytest.fixture(scope="session")
def project_root():
    """Project root directory"""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def schema_dir():
    """JSON Schema directory"""
    return SCHEMA_DIR


@pytest.fixture(scope="session")
def api_spec_dir():
    """OpenAPI spec directory"""
    return API_SPEC_DIR


@pytest.fixture(scope="session")
def all_schemas():
    """Load all JSON schemas"""
    schemas = {}
    for schema_file in SCHEMA_DIR.glob("*.json"):
        with open(schema_file, 'r', encoding='utf-8') as f:
            schemas[schema_file.stem] = json.load(f)
    return schemas


@pytest.fixture(scope="session")
def all_api_specs():
    """Load all OpenAPI specs"""
    specs = {}
    for spec_file in API_SPEC_DIR.glob("*.yml"):
        with open(spec_file, 'r', encoding='utf-8') as f:
            specs[spec_file.stem] = yaml.safe_load(f)
    return specs


@pytest.fixture(scope="session")
def canvas_api_spec():
    """Load canvas-api.openapi.yml"""
    spec_path = API_SPEC_DIR / "canvas-api.openapi.yml"
    with open(spec_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def canvas_node_schema():
    """Load canvas-node.schema.json"""
    schema_path = SCHEMA_DIR / "canvas-node.schema.json"
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# Test data factories
@pytest.fixture
def valid_text_node():
    """Factory for creating valid text nodes"""
    def _create(text="测试节点", color="1"):
        return {
            "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "type": "text",
            "text": text,
            "x": 100,
            "y": 200,
            "width": 250,
            "height": 60,
            "color": color
        }
    return _create


@pytest.fixture
def valid_file_node():
    """Factory for creating valid file nodes"""
    def _create(file_path="笔记库/test.md"):
        return {
            "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "type": "file",
            "file": file_path,
            "x": 100,
            "y": 200,
            "width": 300,
            "height": 400
        }
    return _create


@pytest.fixture
def valid_canvas_data():
    """Factory for creating valid canvas data"""
    def _create(nodes=None, edges=None):
        return {
            "nodes": nodes or [],
            "edges": edges or []
        }
    return _create


# Markers for conditional test execution
def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line(
        "markers", "fastapi_required: mark test as requiring FastAPI server"
    )
    config.addinivalue_line(
        "markers", "schemathesis: mark test as using Schemathesis"
    )


# Skip tests based on dependencies
def pytest_collection_modifyitems(config, items):
    """Skip tests if dependencies not available"""
    skip_schemathesis = pytest.mark.skip(reason="Schemathesis not installed")

    for item in items:
        if "schemathesis" in item.keywords:
            try:
                import schemathesis
            except ImportError:
                item.add_marker(skip_schemathesis)
