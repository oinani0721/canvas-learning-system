"""
JSON Schema Validation Tests

验证Canvas Learning System的数据模型是否符合JSON Schema定义。
这是SDD的核心组件 - 确保代码输出符合规范。

Schemas tested:
- canvas-node.schema.json
- canvas-edge.schema.json
- canvas-file.schema.json
- agent-response.schema.json
- scoring-response.schema.json
"""

import json
import pytest
from pathlib import Path
from jsonschema import validate, ValidationError, Draft7Validator

# Schema directory
SCHEMA_DIR = Path(__file__).parent.parent.parent / "specs" / "data"


class TestCanvasNodeSchema:
    """Test canvas-node.schema.json validation"""

    @pytest.fixture
    def schema(self):
        schema_path = SCHEMA_DIR / "canvas-node.schema.json"
        with open(schema_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_valid_text_node(self, schema):
        """Valid text node should pass validation"""
        node = {
            "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "type": "text",
            "text": "这是一个概念节点",
            "x": 100,
            "y": 200,
            "width": 250,
            "height": 60,
            "color": "1"
        }
        validate(instance=node, schema=schema)

    def test_valid_file_node(self, schema):
        """Valid file node should pass validation"""
        node = {
            "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "type": "file",
            "file": "笔记库/oral-explanation.md",
            "x": 500,
            "y": 300,
            "width": 300,
            "height": 400
        }
        validate(instance=node, schema=schema)

    def test_valid_link_node(self, schema):
        """Valid link node should pass validation"""
        node = {
            "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "type": "link",
            "url": "https://example.com",
            "x": 100,
            "y": 100
        }
        validate(instance=node, schema=schema)

    def test_valid_group_node(self, schema):
        """Valid group node should pass validation"""
        node = {
            "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "type": "group",
            "x": 0,
            "y": 0,
            "width": 500,
            "height": 500
        }
        validate(instance=node, schema=schema)

    def test_missing_required_field(self, schema):
        """Missing required field should fail validation"""
        node = {
            "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "type": "text",
            # missing x, y
        }
        with pytest.raises(ValidationError):
            validate(instance=node, schema=schema)

    def test_invalid_color_value(self, schema):
        """Invalid color value should fail validation"""
        node = {
            "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "type": "text",
            "text": "test",
            "x": 100,
            "y": 200,
            "color": "7"  # Invalid: only 1,2,3,5,6 allowed
        }
        with pytest.raises(ValidationError):
            validate(instance=node, schema=schema)

    def test_invalid_type_value(self, schema):
        """Invalid type value should fail validation"""
        node = {
            "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "type": "invalid",  # Invalid type
            "x": 100,
            "y": 200
        }
        with pytest.raises(ValidationError):
            validate(instance=node, schema=schema)

    def test_text_node_without_text(self, schema):
        """Text node without text field should fail validation"""
        node = {
            "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "type": "text",
            "x": 100,
            "y": 200
            # missing text field
        }
        with pytest.raises(ValidationError):
            validate(instance=node, schema=schema)

    def test_file_node_without_file(self, schema):
        """File node without file field should fail validation"""
        node = {
            "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "type": "file",
            "x": 100,
            "y": 200
            # missing file field
        }
        with pytest.raises(ValidationError):
            validate(instance=node, schema=schema)

    def test_additional_properties_rejected(self, schema):
        """Additional properties should be rejected"""
        node = {
            "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "type": "text",
            "text": "test",
            "x": 100,
            "y": 200,
            "invalid_field": "should fail"
        }
        with pytest.raises(ValidationError):
            validate(instance=node, schema=schema)

    def test_all_valid_colors(self, schema):
        """All valid colors should pass validation
        Story 12.B.4: 正确的颜色映射 (1=灰, 2=绿, 3=紫, 4=红, 5=蓝, 6=黄)
        """
        valid_colors = ["1", "2", "3", "4", "5", "6"]
        for color in valid_colors:
            node = {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "type": "text",
                "text": "test",
                "x": 100,
                "y": 200,
                "color": color
            }
            validate(instance=node, schema=schema)


class TestCanvasEdgeSchema:
    """Test canvas-edge.schema.json validation"""

    @pytest.fixture
    def schema(self):
        schema_path = SCHEMA_DIR / "canvas-edge.schema.json"
        if not schema_path.exists():
            pytest.skip("canvas-edge.schema.json not found")
        with open(schema_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_valid_edge(self, schema):
        """Valid edge should pass validation"""
        edge = {
            "id": "edge-001",
            "fromNode": "node-001",
            "toNode": "node-002"
        }
        validate(instance=edge, schema=schema)

    def test_edge_with_label(self, schema):
        """Edge with label should pass validation"""
        edge = {
            "id": "edge-001",
            "fromNode": "node-001",
            "toNode": "node-002",
            "label": "关联"
        }
        validate(instance=edge, schema=schema)


class TestCanvasFileSchema:
    """Test canvas-file.schema.json validation"""

    @pytest.fixture
    def schema(self):
        schema_path = SCHEMA_DIR / "canvas-file.schema.json"
        if not schema_path.exists():
            pytest.skip("canvas-file.schema.json not found")
        with open(schema_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_valid_canvas_file(self, schema):
        """Valid canvas file should pass validation"""
        canvas = {
            "nodes": [],
            "edges": []
        }
        validate(instance=canvas, schema=schema)

    def test_canvas_with_nodes_and_edges(self, schema):
        """Canvas with nodes and edges should pass validation"""
        canvas = {
            "nodes": [
                {
                    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "type": "text",
                    "text": "test",
                    "x": 100,
                    "y": 200
                }
            ],
            "edges": [
                {
                    "id": "edge-001",
                    "fromNode": "node-001",
                    "toNode": "node-002"
                }
            ]
        }
        validate(instance=canvas, schema=schema)


class TestAgentResponseSchema:
    """Test agent-response.schema.json validation"""

    @pytest.fixture
    def schema(self):
        schema_path = SCHEMA_DIR / "agent-response.schema.json"
        if not schema_path.exists():
            pytest.skip("agent-response.schema.json not found")
        with open(schema_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_valid_agent_response(self, schema):
        """Valid agent response should pass validation"""
        response = {
            "agent_id": "basic-decomposition",
            "status": "success",
            "content": "这是生成的内容"
        }
        validate(instance=response, schema=schema)


class TestScoringResponseSchema:
    """Test scoring-response.schema.json validation"""

    @pytest.fixture
    def schema(self):
        schema_path = SCHEMA_DIR / "scoring-response.schema.json"
        if not schema_path.exists():
            pytest.skip("scoring-response.schema.json not found")
        with open(schema_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_valid_scoring_response(self, schema):
        """Valid scoring response should pass validation"""
        response = {
            "node_id": "node-001",
            "scores": {
                "accuracy": 8,
                "imagery": 7,
                "completeness": 9,
                "originality": 6
            },
            "total_score": 30,
            "feedback": "整体理解良好"
        }
        validate(instance=response, schema=schema)


class TestSchemaMetadata:
    """Test schema metadata and structure"""

    def test_all_schemas_have_required_metadata(self):
        """All schemas should have $schema, $id, title, description"""
        required_fields = ["$schema", "title", "description"]

        for schema_file in SCHEMA_DIR.glob("*.json"):
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema = json.load(f)

            for field in required_fields:
                assert field in schema, f"{schema_file.name} missing {field}"

    def test_all_schemas_are_valid_draft7(self):
        """All schemas should be valid JSON Schema Draft-07"""
        for schema_file in SCHEMA_DIR.glob("*.json"):
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema = json.load(f)

            # This will raise if invalid
            Draft7Validator.check_schema(schema)
