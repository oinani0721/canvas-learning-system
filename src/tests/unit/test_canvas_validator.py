"""
Unit tests for Canvas Validator module
Epic 9 - Canvas System Robustness Enhancement
Story 9.6 - Integration Testing and Validation
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from canvas_utils.canvas_validator import (
        CanvasValidator,
        ValidationRule,
        OperationResult,
        CanvasSchemaError,
        NodeValidationError,
        EdgeValidationError
    )
    CANVAS_UTILS_AVAILABLE = True
except ImportError:
    CANVAS_UTILS_AVAILABLE = False
    CanvasValidator = Mock
    ValidationRule = Mock


@pytest.mark.skipif(not CANVAS_UTILS_AVAILABLE, reason="canvas_utils.canvas_validator not available")
class TestCanvasValidator:
    """Test suite for CanvasValidator"""

    @pytest.fixture
    def validator(self):
        """Create validator instance for testing"""
        return CanvasValidator()

    @pytest.fixture
    def sample_canvas_data(self):
        """Sample canvas data for testing"""
        return {
            "nodes": [
                {
                    "id": "node1",
                    "type": "text",
                    "x": 100,
                    "y": 100,
                    "width": 300,
                    "height": 200,
                    "color": "1",
                    "text": "Question text"
                },
                {
                    "id": "node2",
                    "type": "text",
                    "x": 450,
                    "y": 100,
                    "width": 400,
                    "height": 200,
                    "color": "6",
                    "text": "Answer text"
                }
            ],
            "edges": [
                {
                    "id": "edge1",
                    "fromNode": "node1",
                    "toNode": "node2",
                    "color": "6"
                }
            ]
        }

    @pytest.fixture
    def temp_canvas_file(self, sample_canvas_data):
        """Create temporary canvas file"""
        temp_dir = tempfile.mkdtemp()
        canvas_path = Path(temp_dir) / "test.canvas"

        with open(canvas_path, 'w', encoding='utf-8') as f:
            json.dump(sample_canvas_data, f, ensure_ascii=False, indent='\t')

        yield str(canvas_path)

        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_validate_canvas_structure_valid(self, validator, sample_canvas_data):
        """Test validating valid canvas structure"""
        result = validator.validate_canvas_structure(sample_canvas_data)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_canvas_structure_missing_nodes(self, validator):
        """Test validating canvas with missing nodes"""
        invalid_data = {"edges": []}
        result = validator.validate_canvas_structure(invalid_data)
        assert not result.is_valid
        assert any("nodes" in error.lower() for error in result.errors)

    def test_validate_canvas_structure_missing_edges(self, validator, sample_canvas_data):
        """Test validating canvas with missing edges"""
        del sample_canvas_data["edges"]
        result = validator.validate_canvas_structure(sample_canvas_data)
        # Should be valid - edges are optional
        assert result.is_valid

    def test_validate_node_valid(self, validator, sample_canvas_data):
        """Test validating valid node"""
        node = sample_canvas_data["nodes"][0]
        result = validator.validate_node(node)
        assert result.is_valid

    def test_validate_node_missing_id(self, validator):
        """Test validating node with missing ID"""
        node = {"type": "text", "x": 100, "y": 100}
        result = validator.validate_node(node)
        assert not result.is_valid
        assert any("id" in error.lower() for error in result.errors)

    def test_validate_node_invalid_type(self, validator):
        """Test validating node with invalid type"""
        node = {"id": "test", "type": "invalid", "x": 100, "y": 100}
        result = validator.validate_node(node)
        assert not result.is_valid
        assert any("type" in error.lower() for error in result.errors)

    def test_validate_node_invalid_coordinates(self, validator):
        """Test validating node with invalid coordinates"""
        node = {"id": "test", "type": "text", "x": -100, "y": 100}
        result = validator.validate_node(node)
        assert not result.is_valid
        assert any("coordinate" in error.lower() or "negative" in error.lower()
                  for error in result.errors)

    def test_validate_node_invalid_dimensions(self, validator):
        """Test validating node with invalid dimensions"""
        node = {"id": "test", "type": "text", "x": 100, "y": 100, "width": 0, "height": 200}
        result = validator.validate_node(node)
        assert not result.is_valid
        assert any("dimension" in error.lower() or "width" in error.lower()
                  for error in result.errors)

    def test_validate_edge_valid(self, validator, sample_canvas_data):
        """Test validating valid edge"""
        edge = sample_canvas_data["edges"][0]
        result = validator.validate_edge(edge, sample_canvas_data["nodes"])
        assert result.is_valid

    def test_validate_edge_missing_nodes(self, validator):
        """Test validating edge with missing node references"""
        edge = {"id": "edge1", "fromNode": "nonexistent", "toNode": "node2"}
        result = validator.validate_edge(edge, [])
        assert not result.is_valid
        assert any("node" in error.lower() for error in result.errors)

    def test_validate_edge_self_reference(self, validator):
        """Test validating edge with self-reference"""
        edge = {"id": "edge1", "fromNode": "node1", "toNode": "node1"}
        result = validator.validate_edge(edge, [{"id": "node1"}])
        assert not result.is_valid
        assert any("self" in error.lower() or "reference" in error.lower()
                  for error in result.errors)

    def test_validate_operation_add_node_valid(self, validator, temp_canvas_file):
        """Test validating add node operation"""
        operation = {
            'type': 'add_node',
            'node': {
                'id': 'new_node',
                'type': 'text',
                'x': 200,
                'y': 200,
                'width': 300,
                'height': 200,
                'color': '1',
                'text': 'New node'
            }
        }
        result = validator.validate_operation('add_node', operation, temp_canvas_file)
        assert result.success

    def test_validate_operation_add_node_duplicate_id(self, validator, temp_canvas_file):
        """Test validating add node operation with duplicate ID"""
        operation = {
            'type': 'add_node',
            'node': {
                'id': 'node1',  # Existing ID
                'type': 'text',
                'x': 200,
                'y': 200,
                'width': 300,
                'height': 200,
                'color': '1'
            }
        }
        result = validator.validate_operation('add_node', operation, temp_canvas_file)
        assert not result.success
        assert 'duplicate' in result.error.lower()

    def test_validate_operation_add_edge_valid(self, validator, temp_canvas_file, sample_canvas_data):
        """Test validating add edge operation"""
        # Add a new node first
        sample_canvas_data['nodes'].append({
            'id': 'node3',
            'type': 'text',
            'x': 300,
            'y': 300,
            'width': 300,
            'height': 200,
            'color': '1'
        })

        operation = {
            'type': 'add_edge',
            'edge': {
                'id': 'edge2',
                'fromNode': 'node2',
                'toNode': 'node3',
                'color': '6'
            }
        }
        result = validator.validate_operation('add_edge', operation, temp_canvas_file)
        assert result.success

    def test_validate_operation_update_node_valid(self, validator, temp_canvas_file):
        """Test validating update node operation"""
        operation = {
            'type': 'update_node',
            'node_id': 'node1',
            'updates': {
                'text': 'Updated text',
                'x': 150
            }
        }
        result = validator.validate_operation('update_node', operation, temp_canvas_file)
        assert result.success

    def test_validate_operation_delete_node_valid(self, validator, temp_canvas_file):
        """Test validating delete node operation"""
        operation = {
            'type': 'delete_node',
            'node_id': 'node2'
        }
        result = validator.validate_operation('delete_node', operation, temp_canvas_file)
        assert result.success

    def test_validate_operation_invalid_type(self, validator, temp_canvas_file):
        """Test validating invalid operation type"""
        operation = {'type': 'invalid_operation'}
        result = validator.validate_operation('invalid_operation', operation, temp_canvas_file)
        assert not result.success
        assert 'invalid' in result.error.lower()

    def test_validate_color_code_valid(self, validator):
        """Test validating valid color codes"""
        valid_colors = ['1', '2', '3', '5', '6']
        for color in valid_colors:
            assert validator.validate_color_code(color)

    def test_validate_color_code_invalid(self, validator):
        """Test validating invalid color codes"""
        invalid_colors = ['0', '4', '7', 'red', '#FF0000']
        for color in invalid_colors:
            assert not validator.validate_color_code(color)

    def test_read_canvas_file(self, validator, temp_canvas_file, sample_canvas_data):
        """Test reading canvas file"""
        canvas_data = validator.read_canvas(temp_canvas_file)
        assert 'nodes' in canvas_data
        assert 'edges' in canvas_data
        assert len(canvas_data['nodes']) == len(sample_canvas_data['nodes'])

    def test_read_canvas_file_not_found(self, validator):
        """Test reading non-existent canvas file"""
        with pytest.raises(FileNotFoundError):
            validator.read_canvas('nonexistent.canvas')

    def test_write_canvas_file(self, validator, temp_canvas_file, sample_canvas_data):
        """Test writing canvas file"""
        # Modify data
        sample_canvas_data['nodes'].append({
            'id': 'node3',
            'type': 'text',
            'x': 300,
            'y': 300,
            'width': 300,
            'height': 200,
            'color': '1'
        })

        # Write file
        validator.write_canvas(temp_canvas_file, sample_canvas_data)

        # Verify
        updated_data = validator.read_canvas(temp_canvas_file)
        assert len(updated_data['nodes']) == 3

    def test_write_canvas_file_invalid_format(self, validator, temp_canvas_file):
        """Test writing invalid canvas format"""
        invalid_data = {'invalid': 'data'}
        with pytest.raises(CanvasSchemaError):
            validator.write_canvas(temp_canvas_file, invalid_data)

    def test_attempt_recovery_permission_denied(self, validator, temp_canvas_file):
        """Test recovery from permission denied error"""
        failed_operations = [
            OperationResult(type='add_node', success=False, error='Permission denied')
        ]

        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            recovery_result = validator.attempt_recovery(failed_operations, temp_canvas_file)
            assert recovery_result is not None
            assert recovery_result.get('recovered_operations') >= 0

    def test_attempt_recovery_invalid_node_id(self, validator, temp_canvas_file):
        """Test recovery from invalid node ID error"""
        failed_operations = [
            OperationResult(type='add_node', success=False, error='Invalid node ID')
        ]

        recovery_result = validator.attempt_recovery(failed_operations, temp_canvas_file)
        assert recovery_result is not None
        assert 'suggestions' in recovery_result

    def test_batch_validate_operations(self, validator, temp_canvas_file):
        """Test batch validation of operations"""
        operations = [
            {
                'type': 'add_node',
                'node': {
                    'id': 'batch1',
                    'type': 'text',
                    'x': 100,
                    'y': 100,
                    'width': 300,
                    'height': 200,
                    'color': '1'
                }
            },
            {
                'type': 'add_node',
                'node': {
                    'id': 'batch2',
                    'type': 'text',
                    'x': 500,
                    'y': 100,
                    'width': 300,
                    'height': 200,
                    'color': '6'
                }
            }
        ]

        results = validator.batch_validate_operations(operations, temp_canvas_file)
        assert len(results) == 2
        assert all(r.success for r in results)

    def test_get_validation_rules(self, validator):
        """Test getting validation rules"""
        rules = validator.get_validation_rules()
        assert isinstance(rules, dict)
        assert 'node' in rules
        assert 'edge' in rules
        assert 'canvas' in rules

    def test_add_custom_validation_rule(self, validator):
        """Test adding custom validation rule"""
        def custom_rule(node):
            if node.get('type') == 'custom' and 'custom_field' not in node:
                return False, "Custom node requires custom_field"
            return True, ""

        validator.add_validation_rule('node', 'custom_field_required', custom_rule)

        # Test the rule
        node = {'id': 'test', 'type': 'custom', 'x': 100, 'y': 100}
        result = validator.validate_node(node)
        assert not result.is_valid
        assert any('custom_field' in error for error in result.errors)

    def test_validate_canvas_performance(self, validator, sample_canvas_data):
        """Test canvas validation performance"""
        import time

        # Create large canvas
        large_canvas = {
            'nodes': [],
            'edges': []
        }

        for i in range(100):
            large_canvas['nodes'].append({
                'id': f'node_{i}',
                'type': 'text',
                'x': i * 100,
                'y': (i // 10) * 100,
                'width': 300,
                'height': 200,
                'color': '1'
            })

            if i > 0:
                large_canvas['edges'].append({
                    'id': f'edge_{i}',
                    'fromNode': f'node_{i-1}',
                    'toNode': f'node_{i}',
                    'color': '6'
                })

        # Measure validation time
        start_time = time.time()
        result = validator.validate_canvas_structure(large_canvas)
        validation_time = time.time() - start_time

        assert result.is_valid
        assert validation_time < 0.1  # Should validate in < 100ms


if __name__ == '__main__':
    # Run tests when script is executed directly
    pytest.main([__file__, '-v'])