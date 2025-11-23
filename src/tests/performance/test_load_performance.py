"""
Load Performance Tests
Epic 9 - Canvas System Robustness Enhancement
Story 9.6 - Integration Testing and Validation
"""

import pytest
import asyncio
import json
import time
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import sys
import os
from concurrent.futures import ThreadPoolExecutor
import psutil

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from canvas_utils.model_adapter import ModelCompatibilityAdapter
    from canvas_utils.canvas_validator import CanvasValidator
    from canvas_utils.memory_recorder import MemoryRecorder
    from canvas_utils.path_manager import PathManager
    from canvas_utils.session_monitor import SessionMonitor
    from canvas_utils import CanvasJSONOperator, CanvasBusinessLogic
    CANVAS_UTILS_AVAILABLE = True
except ImportError:
    CANVAS_UTILS_AVAILABLE = False


@pytest.mark.skipif(not CANVAS_UTILS_AVAILABLE, reason="Canvas components not available")
@pytest.mark.performance
class TestLoadPerformance:
    """Load performance tests for Canvas system"""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing"""
        temp_dir = tempfile.mkdtemp()
        workspace = Path(temp_dir)

        # Create directory structure
        (workspace / "Canvas").mkdir()
        (workspace / "Memory").mkdir()
        (workspace / "Sessions").mkdir()

        yield str(workspace)

        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def large_canvas_data(self):
        """Generate large canvas data for load testing"""
        canvas = {
            "nodes": [],
            "edges": []
        }

        # Create 500 nodes
        for i in range(500):
            canvas["nodes"].append({
                "id": f"node_{i}",
                "type": "text",
                "x": (i % 20) * 100,
                "y": (i // 20) * 150,
                "width": 300,
                "height": 200,
                "color": str((i % 5) + 1),
                "text": f"Node {i} content" * 10  # Longer text
            })

            # Add edges to create a connected graph
            if i > 0:
                canvas["edges"].append({
                    "id": f"edge_{i}",
                    "fromNode": f"node_{i-1}",
                    "toNode": f"node_{i}",
                    "color": "6"
                })

        return canvas

    @pytest.mark.asyncio
    async def test_concurrent_sessions_load(self, temp_workspace):
        """Test system under concurrent session load"""
        monitor = SessionMonitor()
        recorder = MemoryRecorder()

        session_count = 50
        sessions = []
        start_time = time.time()

        # Start concurrent sessions
        tasks = []
        for i in range(session_count):
            session_id = f"load_test_{i}"
            session_info = {
                'canvas_path': f'{temp_workspace}/Canvas/load_test_{i}.canvas',
                'user_id': f'user_{i}',
                'model': 'opus-4.1'
            }
            tasks.append(monitor.start_monitoring(session_id, session_info))
            sessions.append(session_id)

        # Measure startup time
        startup_results = await asyncio.gather(*tasks)
        startup_time = time.time() - start_time

        # Verify all sessions started
        assert all(startup_results), "Not all sessions started successfully"
        assert startup_time < 10.0, f"Session startup too slow: {startup_time}s for {session_count} sessions"

        # Perform concurrent operations
        operation_start = time.time()
        operation_tasks = []

        for session_id in sessions:
            # Record multiple events per session
            for j in range(10):
                task = monitor.record_event(
                    session_id,
                    f"operation_{j}",
                    {"data": f"load_test_data_{j}", "timestamp": time.time()}
                )
                operation_tasks.append(task)

            # Record to memory
            session_data = {
                'session_id': session_id,
                'canvas_path': f'canvas_{session_id}.canvas',
                'actions': [{'type': 'load_test', 'data': {'load': True}}] * 5
            }
            task = recorder.record_session(session_data)
            operation_tasks.append(task)

        # Wait for all operations
        operation_results = await asyncio.gather(*operation_tasks)
        operation_time = time.time() - operation_start

        # Verify performance
        assert all(operation_results), "Some operations failed"
        assert operation_time < 30.0, f"Operations too slow: {operation_time}s"

        # Check memory usage
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        assert memory_mb < 500, f"Memory usage too high: {memory_mb}MB"

        # Stop all sessions
        stop_start = time.time()
        stop_tasks = [monitor.stop_monitoring(sid) for sid in sessions]
        stop_results = await asyncio.gather(*stop_tasks)
        stop_time = time.time() - stop_start

        assert all(r is not None for r in stop_results)
        assert stop_time < 5.0, f"Session stop too slow: {stop_time}s"

        print(f"Concurrent sessions test results:")
        print(f"  - Sessions: {session_count}")
        print(f"  - Startup time: {startup_time:.2f}s")
        print(f"  - Operation time: {operation_time:.2f}s")
        print(f"  - Stop time: {stop_time:.2f}s")
        print(f"  - Memory usage: {memory_mb:.1f}MB")

    def test_canvas_validation_load(self, large_canvas_data, temp_workspace):
        """Test canvas validation performance under load"""
        validator = CanvasValidator()

        # Test single large canvas validation
        start_time = time.time()
        result = validator.validate_canvas_structure(large_canvas_data)
        validation_time = time.time() - start_time

        assert result.is_valid, "Large canvas validation failed"
        assert validation_time < 1.0, f"Large canvas validation too slow: {validation_time}s"

        # Test batch validation of multiple canvases
        canvas_count = 100
        canvases = [large_canvas_data.copy() for _ in range(canvas_count)]

        # Modify each canvas slightly
        for i, canvas in enumerate(canvases):
            for node in canvas['nodes']:
                node['id'] = f"{node['id']}_batch_{i}"

        start_time = time.time()
        results = validator.batch_validate_canvases(canvases)
        batch_time = time.time() - start_time

        assert len(results) == canvas_count
        assert all(r.is_valid for r in results)
        assert batch_time < 10.0, f"Batch validation too slow: {batch_time}s for {canvas_count} canvases"

        print(f"Canvas validation test results:")
        print(f"  - Single canvas ({len(large_canvas_data['nodes'])} nodes): {validation_time:.3f}s")
        print(f"  - Batch validation ({canvas_count} canvases): {batch_time:.2f}s")
        print(f"  - Avg per canvas: {batch_time/canvas_count:.3f}s")

    def test_path_manager_load(self, temp_workspace):
        """Test path manager performance under load"""
        path_manager = PathManager()
        path_manager.set_current_canvas(f'{temp_workspace}/Canvas/test.canvas')

        # Test path generation speed
        path_count = 1000
        start_time = time.time()

        generated_paths = []
        for i in range(path_count):
            path = path_manager.generate_consistent_path(f"document_{i}.md")
            generated_paths.append(path)

        generation_time = time.time() - start_time
        avg_time = generation_time / path_count

        assert generation_time < 1.0, f"Path generation too slow: {generation_time}s for {path_count} paths"
        assert avg_time < 0.001, f"Average path generation too slow: {avg_time}s"

        # Test path resolution speed
        start_time = time.time()
        for path in generated_paths[:100]:  # Test subset
            resolved = path_manager.resolve_relative_path(path)
            assert resolved is not None

        resolution_time = time.time() - start_time
        avg_resolution = resolution_time / 100

        assert resolution_time < 0.5, f"Path resolution too slow: {resolution_time}s"
        assert avg_resolution < 0.005, f"Average path resolution too slow: {avg_resolution}s"

        print(f"Path manager test results:")
        print(f"  - Generated {path_count} paths: {generation_time:.3f}s")
        print(f"  - Average generation time: {avg_time*1000:.2f}ms")
        print(f"  - Resolved 100 paths: {resolution_time:.3f}s")
        print(f"  - Average resolution time: {avg_resolution*1000:.2f}ms")

    def test_model_adapter_load(self):
        """Test model adapter performance under load"""
        adapter = ModelCompatibilityAdapter()

        # Test model detection speed
        test_responses = [
            {'model': 'claude-opus-4-1-20250805'},
            {'model': 'claude-3-5-sonnet-20241022'},
            {'model': 'glm-4.6'},
            {'model': 'unknown-model'}
        ]

        detection_count = 10000
        start_time = time.time()

        detected_models = []
        for i in range(detection_count):
            response = test_responses[i % len(test_responses)]
            detected = adapter.detect_model(response)
            detected_models.append(detected)

        detection_time = time.time() - start_time
        avg_detection = detection_time / detection_count

        assert detection_time < 5.0, f"Model detection too slow: {detection_time}s for {detection_count} detections"
        assert avg_detection < 0.0005, f"Average detection too slow: {avg_detection*1000:.2f}ms"

        # Test processor retrieval speed
        start_time = time.time()
        for i in range(1000):
            model = detected_models[i % len(detected_models)]
            processor = adapter.get_processor(model)
            assert processor is not None

        processor_time = time.time() - start_time
        avg_processor = processor_time / 1000

        assert processor_time < 0.1, f"Processor retrieval too slow: {processor_time}s"
        assert avg_processor < 0.0001, f"Average processor retrieval too slow: {avg_processor*1000:.3f}ms"

        print(f"Model adapter test results:")
        print(f"  - Detected {detection_count} models: {detection_time:.3f}s")
        print(f"  - Average detection time: {avg_detection*1000:.3f}ms")
        print(f"  - Retrieved 1000 processors: {processor_time:.3f}s")
        print(f"  - Average retrieval time: {avg_processor*1000:.3f}ms")

    @pytest.mark.asyncio
    async def test_memory_recorder_load(self, temp_workspace):
        """Test memory recorder performance under load"""
        recorder = MemoryRecorder()

        # Test concurrent recording
        session_count = 100
        tasks = []

        start_time = time.time()

        for i in range(session_count):
            session_data = {
                'session_id': f'load_session_{i}',
                'canvas_path': f'canvas_{i}.canvas',
                'user_id': f'user_{i}',
                'actions': [
                    {
                        'type': f'action_{j}',
                        'timestamp': time.time(),
                        'data': {'test': True, 'index': j}
                    }
                    for j in range(20)  # 20 actions per session
                ]
            }
            task = recorder.record_session(session_data)
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        recording_time = time.time() - start_time

        assert all(r.success for r in results), "Some recordings failed"
        assert recording_time < 30.0, f"Recording too slow: {recording_time}s for {session_count} sessions"

        # Test retrieval performance
        retrieval_start = time.time()
        retrieval_tasks = []

        for i in range(session_count):
            task = recorder.retrieve_session(f'load_session_{i}')
            retrieval_tasks.append(task)

        retrieved_sessions = await asyncio.gather(*retrieval_tasks)
        retrieval_time = time.time() - retrieval_start

        assert all(s is not None for s in retrieved_sessions), "Some retrievals failed"
        assert retrieval_time < 10.0, f"Retrieval too slow: {retrieval_time}s"

        print(f"Memory recorder test results:")
        print(f"  - Recorded {session_count} sessions: {recording_time:.2f}s")
        print(f"  - Average recording time: {recording_time/session_count:.3f}s")
        print(f"  - Retrieved {session_count} sessions: {retrieval_time:.2f}s")
        print(f"  - Average retrieval time: {retrieval_time/session_count:.3f}s")

    def test_canvas_operations_load(self, large_canvas_data, temp_workspace):
        """Test canvas operations performance under load"""
        # Create test canvas file
        canvas_path = Path(temp_workspace) / "large_test.canvas"
        with open(canvas_path, 'w', encoding='utf-8') as f:
            json.dump(large_canvas_data, f, ensure_ascii=False, indent='\t')

        operator = CanvasJSONOperator()
        validator = CanvasValidator()

        # Test read performance
        read_count = 100
        start_time = time.time()

        for _ in range(read_count):
            canvas_data = operator.read_canvas(str(canvas_path))
            assert len(canvas_data['nodes']) > 0

        read_time = time.time() - start_time
        avg_read = read_time / read_count

        assert read_time < 5.0, f"Canvas reading too slow: {read_time}s for {read_count} reads"
        assert avg_read < 0.05, f"Average read time too slow: {avg_read*1000:.1f}ms"

        # Test node operations
        operation_count = 1000
        start_time = time.time()

        canvas_data = operator.read_canvas(str(canvas_path))
        initial_node_count = len(canvas_data['nodes'])

        # Add nodes
        for i in range(operation_count // 2):
            new_node = {
                "id": f"load_test_node_{i}",
                "type": "text",
                "x": i * 50,
                "y": 2000,
                "width": 300,
                "height": 200,
                "color": "1",
                "text": f"Load test node {i}"
            }
            canvas_data['nodes'].append(new_node)

        # Validate and write
        validator.write_canvas(str(canvas_path), canvas_data)

        # Remove nodes
        canvas_data = operator.read_canvas(str(canvas_path))
        for i in range(operation_count // 2):
            node_id = f"load_test_node_{i}"
            canvas_data['nodes'] = [n for n in canvas_data['nodes'] if n.get('id') != node_id]

        validator.write_canvas(str(canvas_path), canvas_data)

        operation_time = time.time() - start_time
        avg_operation = operation_time / operation_count

        assert operation_time < 10.0, f"Node operations too slow: {operation_time}s"
        assert avg_operation < 0.01, f"Average operation time too slow: {avg_operation*1000:.1f}ms"

        print(f"Canvas operations test results:")
        print(f"  - Read {read_count} times: {read_time:.3f}s")
        print(f"  - Average read time: {avg_read*1000:.2f}ms")
        print(f"  - Node operations ({operation_count}): {operation_time:.3f}s")
        print(f"  - Average operation time: {avg_operation*1000:.2f}ms")

    @pytest.mark.asyncio
    async def test_system_stress_test(self, temp_workspace):
        """Comprehensive system stress test"""
        # Initialize all components
        monitor = SessionMonitor()
        recorder = MemoryRecorder()
        validator = CanvasValidator()
        path_manager = PathManager()
        adapter = ModelCompatibilityAdapter()

        # Stress parameters
        session_count = 20
        operations_per_session = 50
        canvas_size = 100

        start_time = time.time()

        # Create sessions
        session_tasks = []
        for i in range(session_count):
            session_id = f"stress_session_{i}"
            session_info = {
                'canvas_path': f'{temp_workspace}/Canvas/stress_{i}.canvas',
                'user_id': f'stress_user_{i}',
                'model': 'opus-4.1'
            }
            session_tasks.append(monitor.start_monitoring(session_id, session_info))

        await asyncio.gather(*session_tasks)

        # Create large canvases for each session
        canvas_tasks = []
        for i in range(session_count):
            canvas_path = Path(temp_workspace) / f"stress_{i}.canvas"
            canvas_data = {
                "nodes": [
                    {
                        "id": f"stress_node_{i}_{j}",
                        "type": "text",
                        "x": (j % 10) * 100,
                        "y": (j // 10) * 150,
                        "width": 300,
                        "height": 200,
                        "color": str((j % 5) + 1),
                        "text": f"Stress test node {i}-{j}" * 5
                    }
                    for j in range(canvas_size)
                ],
                "edges": []
            }

            with open(canvas_path, 'w', encoding='utf-8') as f:
                json.dump(canvas_data, f, ensure_ascii=False, indent='\t')

        # Perform operations
        operation_tasks = []
        for i in range(session_count):
            session_id = f"stress_session_{i}"

            for j in range(operations_per_session):
                # Record events
                task = monitor.record_event(
                    session_id,
                    f"stress_operation_{j}",
                    {"data": f"stress_data_{i}_{j}", "load": True}
                )
                operation_tasks.append(task)

                # Record to memory
                if j % 10 == 0:  # Record every 10th operation to memory
                    session_data = {
                        'session_id': session_id,
                        'canvas_path': f'stress_{i}.canvas',
                        'actions': [{'type': 'stress_test', 'data': {'batch': j // 10}}]
                    }
                    task = recorder.record_session(session_data)
                    operation_tasks.append(task)

        # Wait for all operations
        await asyncio.gather(*operation_tasks)

        # Generate reports
        report_tasks = []
        for i in range(session_count):
            session_id = f"stress_session_{i}"
            task = monitor.generate_session_report(session_id)
            report_tasks.append(task)

        reports = await asyncio.gather(*report_tasks)

        # Stop all sessions
        stop_tasks = []
        for i in range(session_count):
            session_id = f"stress_session_{i}"
            task = monitor.stop_monitoring(session_id)
            stop_tasks.append(task)

        await asyncio.gather(*stop_tasks)

        total_time = time.time() - start_time

        # Verify results
        assert all(r is not None for r in reports), "Some reports failed"
        assert total_time < 120.0, f"Stress test too slow: {total_time}s"

        # Check system resources
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        cpu_percent = process.cpu_percent()

        assert memory_mb < 1000, f"Memory usage too high: {memory_mb}MB"
        assert cpu_percent < 80, f"CPU usage too high: {cpu_percent}%"

        print(f"\nStress test results:")
        print(f"  - Sessions: {session_count}")
        print(f"  - Operations per session: {operations_per_session}")
        print(f"  - Canvas size: {canvas_size} nodes")
        print(f"  - Total time: {total_time:.2f}s")
        print(f"  - Memory usage: {memory_mb:.1f}MB")
        print(f"  - CPU usage: {cpu_percent:.1f}%")
        print(f"  - Operations per second: {(session_count * operations_per_session) / total_time:.1f}")


if __name__ == '__main__':
    # Run tests when script is executed directly
    pytest.main([__file__, '-v', '-m', 'performance'])