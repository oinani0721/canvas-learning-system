"""
Integration Tests for Epic 9 Features
Canvas System Robustness Enhancement
Story 9.6 - Integration Testing and Validation
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    # Import Epic 9 components
    from canvas_utils.model_adapter import ModelCompatibilityAdapter
    from canvas_utils.canvas_validator import CanvasValidator
    from canvas_utils.memory_recorder import MemoryRecorder
    from canvas_utils.path_manager import PathManager
    from canvas_utils.session_monitor import SessionMonitor
    from canvas_utils import CanvasJSONOperator, CanvasBusinessLogic
    CANVAS_UTILS_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    CANVAS_UTILS_AVAILABLE = False


@pytest.mark.skipif(not CANVAS_UTILS_AVAILABLE, reason="Epic 9 components not available")
@pytest.mark.asyncio
class TestEpic9Integration:
    """Integration tests for Epic 9 features"""

    @pytest.fixture
    async def test_environment(self):
        """Setup comprehensive test environment"""
        temp_dir = tempfile.mkdtemp()
        test_dir = Path(temp_dir)

        # Create directory structure
        (test_dir / "Canvas").mkdir()
        (test_dir / "Canvas" / "TestCanvas").mkdir()
        (test_dir / "Memory").mkdir()
        (test_dir / "Sessions").mkdir()

        # Create test canvas
        test_canvas = test_dir / "Canvas" / "TestCanvas" / "test.canvas"
        canvas_content = {
            "nodes": [
                {
                    "id": "q1",
                    "type": "text",
                    "x": 100,
                    "y": 100,
                    "width": 300,
                    "height": 200,
                    "color": "1",
                    "text": "什么是机器学习？"
                },
                {
                    "id": "a1",
                    "type": "text",
                    "x": 450,
                    "y": 100,
                    "width": 400,
                    "height": 200,
                    "color": "6",
                    "text": ""
                }
            ],
            "edges": [
                {
                    "id": "e1",
                    "fromNode": "q1",
                    "toNode": "a1",
                    "color": "6"
                }
            ]
        }

        with open(test_canvas, 'w', encoding='utf-8') as f:
            json.dump(canvas_content, f, ensure_ascii=False, indent='\t')

        # Test configuration
        test_config = {
            'canvas_path': str(test_canvas),
            'workspace_root': str(test_dir),
            'memory_path': str(test_dir / "Memory"),
            'session_path': str(test_dir / "Sessions"),
            'user_id': 'test_user',
            'model': 'opus-4.1'
        }

        yield test_config

        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    async def test_full_opus41_workflow(self, test_environment):
        """Test complete Opus 4.1 workflow with all Epic 9 components"""
        config = test_environment

        # 1. Initialize all components
        monitor = SessionMonitor()
        recorder = MemoryRecorder()
        validator = CanvasValidator()
        path_manager = PathManager()
        adapter = ModelCompatibilityAdapter()

        # 2. Start session monitoring
        session_id = f"test_opus_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        await monitor.start_monitoring(session_id, config)

        # 3. Record session start
        session_data = {
            'session_id': session_id,
            'canvas_path': config['canvas_path'],
            'user_id': config['user_id'],
            'model': config['model'],
            'start_time': datetime.now().isoformat(),
            'actions': []
        }

        # 4. Validate canvas structure
        canvas_data = validator.read_canvas(config['canvas_path'])
        validation_result = validator.validate_canvas_structure(canvas_data)
        assert validation_result.is_valid, "Canvas validation failed"

        # 5. Set path manager current canvas
        path_manager.set_current_canvas(config['canvas_path'])

        # 6. Add a new explanation node (simulating AI response)
        new_node = {
            'id': 'exp1',
            'type': 'text',
            'x': 100,
            'y': 350,
            'width': 400,
            'height': 200,
            'color': '5',
            'text': '机器学习是人工智能的一个分支，让计算机从数据中学习规律。'
        }

        # Validate node before adding
        node_validation = validator.validate_node(new_node)
        assert node_validation.is_valid, "Node validation failed"

        # Add node to canvas
        operator = CanvasJSONOperator()
        canvas_data['nodes'].append(new_node)
        validator.write_canvas(config['canvas_path'], canvas_data)

        # 7. Generate a document file (explanation)
        doc_path = path_manager.generate_consistent_path("机器学习解释.md")
        doc_content = """# 机器学习

机器学习是人工智能的一个分支，它使计算机能够在没有明确编程的情况下学习和改进。

## 主要类型

1. **监督学习** - 从标记的数据中学习
2. **无监督学习** - 从未标记的数据中发现模式
3. **强化学习** - 通过奖励和惩罚学习

## 应用领域

- 图像识别
- 自然语言处理
- 推荐系统
- 自动驾驶
"""

        Path(doc_path).parent.mkdir(parents=True, exist_ok=True)
        Path(doc_path).write_text(doc_content, encoding='utf-8')

        # 8. Add file reference node
        file_node = {
            'id': 'file1',
            'type': 'file',
            'x': 550,
            'y': 350,
            'width': 200,
            'height': 100,
            'color': '5',
            'file': doc_path
        }

        file_validation = validator.validate_node(file_node)
        assert file_validation.is_valid, "File node validation failed"

        canvas_data['nodes'].append(file_node)
        canvas_data['edges'].append({
            'id': 'e2',
            'fromNode': 'a1',
            'toNode': 'exp1',
            'color': '5'
        })
        canvas_data['edges'].append({
            'id': 'e3',
            'fromNode': 'exp1',
            'toNode': 'file1',
            'color': '5'
        })

        validator.write_canvas(config['canvas_path'], canvas_data)

        # 9. Record all actions in session
        session_data['actions'].extend([
            {
                'type': 'add_node',
                'timestamp': datetime.now().isoformat(),
                'data': {'node_id': 'exp1', 'node_type': 'explanation'}
            },
            {
                'type': 'generate_document',
                'timestamp': datetime.now().isoformat(),
                'data': {'doc_path': doc_path, 'doc_type': 'explanation'}
            },
            {
                'type': 'add_file_reference',
                'timestamp': datetime.now().isoformat(),
                'data': {'node_id': 'file1', 'file_path': doc_path}
            }
        ])

        # 10. Update session health
        await monitor.update_session_health(session_id, {
            'cpu_usage': 45.0,
            'memory_usage': 60.0,
            'response_time': 120,
            'error_count': 0
        })

        # 11. Record session to memory
        memory_result = await recorder.record_session(session_data)
        assert memory_result.success, "Session recording failed"

        # 12. Generate session report
        report = await monitor.generate_session_report(session_id)
        assert report is not None, "Report generation failed"
        assert report.total_events >= 3

        # 13. Stop monitoring
        final_report = await monitor.stop_monitoring(session_id)
        assert final_report is not None, "Failed to stop monitoring"

        # 14. Verify all components worked together
        # - Canvas should have 4 nodes and 3 edges
        final_canvas = validator.read_canvas(config['canvas_path'])
        assert len(final_canvas['nodes']) == 4
        assert len(final_canvas['edges']) == 3

        # - Document file should exist
        assert Path(doc_path).exists()
        assert Path(doc_path).stat().st_size > 0

        # - Session should be in history
        assert session_id in monitor.session_history

        # - Memory should have recorded session
        retrieved_session = await recorder.retrieve_session(session_id)
        assert retrieved_session is not None
        assert len(retrieved_session['actions']) >= 3

    async def test_model_adaptation_flow(self, test_environment):
        """Test model adaptation across different AI models"""
        config = test_environment

        adapter = ModelCompatibilityAdapter()
        validator = CanvasValidator()

        # Test responses from different models
        model_responses = {
            'opus-4.1': {
                'model': 'claude-opus-4-1-20250805',
                'content': [{'type': 'text', 'text': 'Opus 4.1 response'}],
                'usage': {'input_tokens': 100, 'output_tokens': 50}
            },
            'sonnet-3.5': {
                'model': 'claude-3-5-sonnet-20241022',
                'content': [{'type': 'text', 'text': 'Sonnet 3.5 response'}],
                'stop_reason': 'end_turn'
            },
            'glm-4.6': {
                'model': 'glm-4.6',
                'choices': [{
                    'message': {'content': 'GLM-4.6 response'},
                    'finish_reason': 'stop'
                }]
            }
        }

        processed_results = {}

        # Process each model response
        for model_name, response in model_responses.items():
            # Detect model
            detected = adapter.detect_model(response)
            assert detected == model_name, f"Model detection failed for {model_name}"

            # Get appropriate processor
            processor = adapter.get_processor(detected)

            # Process response
            processed = await processor.process_response(response)
            processed_results[model_name] = processed

            # Verify processing
            assert processed['model'] == model_name
            assert 'content' in processed

        # Verify all models produced consistent structure
        for result in processed_results.values():
            assert 'content' in result
            assert result['model'] in model_responses.keys()

    async def test_error_recovery_pipeline(self, test_environment):
        """Test comprehensive error recovery across all components"""
        config = test_environment

        validator = CanvasValidator()
        recorder = MemoryRecorder()
        path_manager = PathManager()

        # Test 1: Canvas validation failure recovery
        invalid_node = {
            'id': 'invalid',
            'type': 'invalid_type',
            'x': -100,  # Invalid coordinate
            'y': 100,
            'width': 0,  # Invalid dimension
            'height': 200
        }

        node_validation = validator.validate_node(invalid_node)
        assert not node_validation.is_valid

        # Attempt recovery by fixing invalid values
        fixed_node = invalid_node.copy()
        fixed_node['type'] = 'text'
        fixed_node['x'] = 100
        fixed_node['width'] = 300

        fixed_validation = validator.validate_node(fixed_node)
        assert fixed_validation.is_valid

        # Test 2: Memory recording failure recovery
        session_data = {
            'session_id': 'recovery_test',
            'canvas_path': config['canvas_path'],
            'actions': [{'type': 'test', 'data': {}}]
        }

        # Simulate primary system failure
        with patch.object(recorder, '_record_to_graphiti', return_value=False):
            result = await recorder.record_session(session_data)
            assert result.success  # Should succeed with backup systems

        # Test 3: Path resolution failure recovery
        path_manager.set_current_canvas(config['canvas_path'])

        # Create a test file
        test_file = Path(config['workspace_root']) / "Canvas" / "TestCanvas" / "Test-文档-20251028120000.md"
        test_file.write_text("Test content")

        # Try to find with wrong timestamp
        broken_path = "./Test-文档-20251028123000.md"
        fixed_path = path_manager.validate_and_fix_path(broken_path)

        assert Path(fixed_path).exists()
        assert "20251028120000" in fixed_path

    async def test_concurrent_operations(self, test_environment):
        """Test handling of concurrent operations across components"""
        config = test_environment

        monitor = SessionMonitor()
        recorder = MemoryRecorder()
        validator = CanvasValidator()

        # Start multiple concurrent sessions
        sessions = []
        tasks = []

        for i in range(5):
            session_id = f"concurrent_{i}"
            session_config = config.copy()
            session_config['user_id'] = f"user_{i}"
            session_config['canvas_path'] = f"canvas_{i}.canvas"

            # Create individual canvas for each session
            canvas_path = Path(config['workspace_root']) / session_config['canvas_path']
            canvas_content = {
                "nodes": [
                    {
                        "id": f"q{i}",
                        "type": "text",
                        "x": 100,
                        "y": 100,
                        "width": 300,
                        "height": 200,
                        "color": "1",
                        "text": f"Question {i}"
                    }
                ],
                "edges": []
            }

            with open(canvas_path, 'w', encoding='utf-8') as f:
                json.dump(canvas_content, f, ensure_ascii=False, indent='\t')

            # Start monitoring
            task = monitor.start_monitoring(session_id, session_config)
            tasks.append(task)
            sessions.append(session_id)

        # Wait for all sessions to start
        await asyncio.gather(*tasks)

        # Perform concurrent operations
        operation_tasks = []

        for i, session_id in enumerate(sessions):
            # Record events
            for j in range(3):
                task = monitor.record_event(
                    session_id,
                    f"operation_{j}",
                    {"data": f"test_data_{i}_{j}"}
                )
                operation_tasks.append(task)

            # Record to memory
            session_data = {
                'session_id': session_id,
                'canvas_path': f"canvas_{i}.canvas",
                'actions': [
                    {'type': 'test_action', 'data': f'action_{i}'}
                ]
            }
            task = recorder.record_session(session_data)
            operation_tasks.append(task)

        # Wait for all operations
        results = await asyncio.gather(*operation_tasks)

        # Verify all operations succeeded
        assert all(results), "Some concurrent operations failed"

        # Stop all sessions
        stop_tasks = [monitor.stop_monitoring(sid) for sid in sessions]
        reports = await asyncio.gather(*stop_tasks)

        assert all(r is not None for r in reports)

        # Verify session integrity
        for session_id in sessions:
            assert session_id in monitor.session_history
            metrics = await monitor.get_session_metrics(session_id)
            assert metrics.total_events >= 3

    async def test_performance_under_load(self, test_environment):
        """Test system performance under significant load"""
        import time

        config = test_environment
        validator = CanvasValidator()
        path_manager = PathManager()
        adapter = ModelCompatibilityAdapter()

        # Performance test 1: Canvas validation speed
        large_canvas = {
            'nodes': [],
            'edges': []
        }

        # Create large canvas with 1000 nodes
        start_time = time.time()
        for i in range(1000):
            large_canvas['nodes'].append({
                'id': f'node_{i}',
                'type': 'text',
                'x': (i % 10) * 400,
                'y': (i // 10) * 300,
                'width': 300,
                'height': 200,
                'color': str((i % 5) + 1)
            })

            if i > 0:
                large_canvas['edges'].append({
                    'id': f'edge_{i}',
                    'fromNode': f'node_{i-1}',
                    'toNode': f'node_{i}',
                    'color': '6'
                })

        validation_time = time.time() - start_time
        assert validation_time < 1.0, f"Canvas validation too slow: {validation_time}s"

        # Validate large canvas
        start_time = time.time()
        result = validator.validate_canvas_structure(large_canvas)
        validation_time = time.time() - start_time

        assert result.is_valid
        assert validation_time < 0.5, f"Large canvas validation too slow: {validation_time}s"

        # Performance test 2: Path generation speed
        path_manager.set_current_canvas(config['canvas_path'])

        start_time = time.time()
        for i in range(100):
            path = path_manager.generate_consistent_path(f"doc_{i}.md")
            assert path is not None
        path_generation_time = time.time() - start_time

        assert path_generation_time < 0.1, f"Path generation too slow: {path_generation_time}s"

        # Performance test 3: Model detection speed
        test_response = {'model': 'claude-opus-4-1-20250805'}

        start_time = time.time()
        for i in range(1000):
            detected = adapter.detect_model(test_response)
            assert detected == 'opus-4.1'
        detection_time = time.time() - start_time

        avg_detection_time = detection_time / 1000
        assert avg_detection_time < 0.001, f"Model detection too slow: {avg_detection_time}s"

    async def test_data_integrity(self, test_environment):
        """Test data integrity across all components"""
        config = test_environment

        recorder = MemoryRecorder()
        validator = CanvasValidator()
        path_manager = PathManager()

        # Test data integrity through round-trip operations
        original_session = {
            'session_id': 'integrity_test',
            'canvas_path': config['canvas_path'],
            'user_id': config['user_id'],
            'model': config['model'],
            'start_time': datetime.now().isoformat(),
            'actions': [
                {
                    'type': 'add_node',
                    'timestamp': datetime.now().isoformat(),
                    'data': {
                        'node_id': 'test_node',
                        'content': 'Test content with 特殊字符',
                        'metadata': {'tags': ['test', '测试']}
                    }
                }
            ],
            'metadata': {
                'total_nodes': 5,
                'learning_time': 1800,
                'model_confidence': 0.95
            }
        }

        # Record session
        result = await recorder.record_session(original_session)
        assert result.success

        # Retrieve session
        retrieved = await recorder.retrieve_session('integrity_test')
        assert retrieved is not None

        # Verify data integrity
        assert retrieved['session_id'] == original_session['session_id']
        assert retrieved['user_id'] == original_session['user_id']
        assert len(retrieved['actions']) == len(original_session['actions'])
        assert retrieved['actions'][0]['data']['node_id'] == 'test_node'
        assert retrieved['actions'][0]['data']['content'] == 'Test content with 特殊字符'
        assert retrieved['metadata']['model_confidence'] == 0.95

        # Test Canvas data integrity
        path_manager.set_current_canvas(config['canvas_path'])
        doc_path = path_manager.generate_consistent_path("数据完整性测试.md")

        test_content = """# 数据完整性测试

测试中文内容
- 项目1
- 项目2
- 特殊符号: !@#$%^&*()

```python
def test():
    print("代码块测试")
```
"""

        Path(doc_path).write_text(test_content, encoding='utf-8')

        # Read back and verify
        read_content = Path(doc_path).read_text(encoding='utf-8')
        assert read_content == test_content

        # Verify file reference in canvas
        file_node = {
            'id': 'integrity_file',
            'type': 'file',
            'x': 100,
            'y': 100,
            'width': 200,
            'height': 100,
            'color': '5',
            'file': doc_path
        }

        canvas_data = validator.read_canvas(config['canvas_path'])
        canvas_data['nodes'].append(file_node)
        validator.write_canvas(config['canvas_path'], canvas_data)

        # Verify file reference persists
        updated_canvas = validator.read_canvas(config['canvas_path'])
        file_nodes = [n for n in updated_canvas['nodes'] if n.get('id') == 'integrity_file']
        assert len(file_nodes) == 1
        assert Path(file_nodes[0]['file']).exists()


if __name__ == '__main__':
    # Run tests when script is executed directly
    pytest.main([__file__, '-v'])