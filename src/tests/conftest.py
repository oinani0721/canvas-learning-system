# tests/conftest.py
# pytest配置文件 - 添加项目根目录到Python路径
# Includes JSON Schema validation fixtures for SDD compliance

import sys
import json
import pytest
from pathlib import Path
from typing import Any, Dict

# 将项目根目录添加到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Try to import jsonschema
try:
    import jsonschema
    from jsonschema import validate, ValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    ValidationError = Exception


# =============================================================================
# Path Fixtures
# =============================================================================

@pytest.fixture
def specs_dir() -> Path:
    """Return the specs directory."""
    return project_root.parent / "specs"


@pytest.fixture
def schemas_dir(specs_dir: Path) -> Path:
    """Return the JSON schemas directory."""
    return specs_dir / "data"


# =============================================================================
# Schema Loading Fixtures
# =============================================================================

@pytest.fixture
def load_schema(schemas_dir: Path):
    """Factory fixture to load a JSON schema by name."""
    def _load_schema(schema_name: str) -> Dict[str, Any]:
        schema_path = schemas_dir / schema_name
        if not schema_path.exists():
            pytest.skip(f"Schema not found: {schema_path}")
        with open(schema_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return _load_schema


@pytest.fixture
def canvas_node_schema(load_schema) -> Dict[str, Any]:
    """Load the canvas-node.schema.json."""
    return load_schema("canvas-node.schema.json")


@pytest.fixture
def canvas_edge_schema(load_schema) -> Dict[str, Any]:
    """Load the canvas-edge.schema.json."""
    return load_schema("canvas-edge.schema.json")


@pytest.fixture
def agent_response_schema(load_schema) -> Dict[str, Any]:
    """Load the agent-response.schema.json."""
    return load_schema("agent-response.schema.json")


# =============================================================================
# Validation Fixtures
# =============================================================================

@pytest.fixture
def validate_against_schema():
    """Factory fixture to validate data against a schema."""
    if not JSONSCHEMA_AVAILABLE:
        pytest.skip("jsonschema not installed. Run: pip install jsonschema")

    def _validate(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        try:
            validate(instance=data, schema=schema)
            return True
        except ValidationError as e:
            raise ValidationError(
                f"Schema validation failed: {e.message}\n"
                f"Path: {' -> '.join(str(p) for p in e.absolute_path)}"
            )
    return _validate


@pytest.fixture
def validate_canvas_node(canvas_node_schema, validate_against_schema):
    """Validate a canvas node against the schema."""
    def _validate(node: Dict[str, Any]) -> bool:
        return validate_against_schema(node, canvas_node_schema)
    return _validate


# =============================================================================
# Sample Data Fixtures
# =============================================================================

@pytest.fixture
def sample_canvas_node() -> Dict[str, Any]:
    """Return a sample valid canvas node."""
    return {
        "id": "node-001",
        "type": "text",
        "x": 100,
        "y": 200,
        "width": 300,
        "height": 150,
        "color": "1",
        "text": "Sample concept"
    }
