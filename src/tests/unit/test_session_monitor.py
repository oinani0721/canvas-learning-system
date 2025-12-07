"""
Unit tests for Session Monitor module
Epic 9 - Canvas System Robustness Enhancement
Story 9.6 - Integration Testing and Validation
"""

import asyncio
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from canvas_utils.session_monitor import (
        MonitoringEvent,
        SessionHealth,
        SessionInfo,
        SessionMetrics,
        SessionMonitor,
        SessionReport,
        SessionStatus,
    )
    CANVAS_UTILS_AVAILABLE = True
except ImportError:
    CANVAS_UTILS_AVAILABLE = False
    SessionMonitor = Mock
    SessionInfo = Mock


@pytest.mark.skipif(not CANVAS_UTILS_AVAILABLE, reason="canvas_utils.session_monitor not available")
class TestSessionMonitor:
    """Test suite for SessionMonitor"""

    @pytest.fixture
    def monitor(self):
        """Create SessionMonitor instance for testing"""
        return SessionMonitor()

    @pytest.fixture
    def sample_session_info(self):
        """Sample session info for testing"""
        return {
            'canvas_path': 'test_canvas.canvas',
            'user_id': 'test_user',
            'model': 'opus-4.1',
            'start_time': datetime.now().isoformat()
        }

    @pytest.fixture
    def temp_monitor_dir(self):
        """Create temporary directory for monitoring data"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_initialization(self, monitor):
        """Test monitor initialization"""
        assert monitor is not None
        assert hasattr(monitor, 'active_sessions')
        assert hasattr(monitor, 'session_history')
        assert hasattr(monitor, 'health_checker')
        assert len(monitor.active_sessions) == 0

    @pytest.mark.asyncio
    async def test_start_monitoring(self, monitor, sample_session_info):
        """Test starting session monitoring"""
        session_id = "test_session_001"

        result = await monitor.start_monitoring(session_id, sample_session_info)

        assert result
        assert session_id in monitor.active_sessions
        session = monitor.active_sessions[session_id]
        assert session.status == SessionStatus.ACTIVE
        assert session.canvas_path == sample_session_info['canvas_path']

    @pytest.mark.asyncio
    async def test_start_monitoring_duplicate(self, monitor, sample_session_info):
        """Test starting monitoring for duplicate session"""
        session_id = "test_session_001"

        # Start monitoring first time
        await monitor.start_monitoring(session_id, sample_session_info)

        # Try to start again with same ID
        result = await monitor.start_monitoring(session_id, sample_session_info)

        assert not result
        assert session_id in monitor.active_sessions

    @pytest.mark.asyncio
    async def test_stop_monitoring(self, monitor, sample_session_info):
        """Test stopping session monitoring"""
        session_id = "test_session_001"

        # Start monitoring
        await monitor.start_monitoring(session_id, sample_session_info)

        # Stop monitoring
        report = await monitor.stop_monitoring(session_id)

        assert report is not None
        assert report.session_id == session_id
        assert session_id not in monitor.active_sessions
        assert session_id in monitor.session_history

    @pytest.mark.asyncio
    async def test_stop_monitoring_nonexistent(self, monitor):
        """Test stopping non-existent session"""
        report = await monitor.stop_monitoring("nonexistent_session")
        assert report is None

    @pytest.mark.asyncio
    async def test_record_event(self, monitor, sample_session_info):
        """Test recording monitoring events"""
        session_id = "test_session_001"
        event_type = "node_added"
        event_data = {"node_id": "node1", "type": "text"}

        # Start monitoring
        await monitor.start_monitoring(session_id, sample_session_info)

        # Record event
        result = await monitor.record_event(session_id, event_type, event_data)

        assert result
        session = monitor.active_sessions[session_id]
        assert len(session.events) > 0
        assert session.events[-1].type == event_type
        assert session.events[-1].data == event_data

    @pytest.mark.asyncio
    async def test_record_event_nonexistent_session(self, monitor):
        """Test recording event for non-existent session"""
        result = await monitor.record_event("nonexistent", "test", {})
        assert not result

    @pytest.mark.asyncio
    async def test_update_session_health(self, monitor, sample_session_info):
        """Test updating session health"""
        session_id = "test_session_001"

        # Start monitoring
        await monitor.start_monitoring(session_id, sample_session_info)

        # Update health
        health_data = {
            'cpu_usage': 50.0,
            'memory_usage': 60.0,
            'response_time': 100,
            'error_count': 0
        }

        await monitor.update_session_health(session_id, health_data)

        session = monitor.active_sessions[session_id]
        assert session.health is not None
        assert session.health.cpu_usage == 50.0
        assert session.health.memory_usage == 60.0

    @pytest.mark.asyncio
    async def test_get_monitoring_status(self, monitor, sample_session_info):
        """Test getting monitoring status"""
        session_id = "test_session_001"

        # Start monitoring
        await monitor.start_monitoring(session_id, sample_session_info)

        # Get status
        status = await monitor.get_monitoring_status()

        assert status is not None
        assert session_id in status.session_health
        assert status.active_sessions >= 1
        assert status.timestamp is not None

    @pytest.mark.asyncio
    async def test_get_session_metrics(self, monitor, sample_session_info):
        """Test getting session metrics"""
        session_id = "test_session_001"

        # Start monitoring
        await monitor.start_monitoring(session_id, sample_session_info)

        # Record some events
        await monitor.record_event(session_id, "node_added", {"node_id": "node1"})
        await monitor.record_event(session_id, "explanation_generated", {"doc_id": "doc1"})

        # Get metrics
        metrics = await monitor.get_session_metrics(session_id)

        assert metrics is not None
        assert metrics.session_id == session_id
        assert metrics.total_events == 2
        assert metrics.event_counts["node_added"] == 1
        assert metrics.event_counts["explanation_generated"] == 1

    @pytest.mark.asyncio
    async def test_health_check_scheduler(self, monitor, sample_session_info):
        """Test health check scheduling"""
        session_id = "test_session_001"

        # Start monitoring
        await monitor.start_monitoring(session_id, sample_session_info)

        # Mock health check
        with patch.object(monitor, '_check_session_health') as mock_check:
            mock_check.return_value = asyncio.Future()
            mock_check.return_value.set_result(None)

            # Run health check
            await monitor._run_health_check()

            # Verify health check was called
            mock_check.assert_called_with(session_id)

    @pytest.mark.asyncio
    async def test_auto_save_sessions(self, monitor, sample_session_info, temp_monitor_dir):
        """Test automatic session saving"""
        session_id = "test_session_001"

        with patch('canvas_utils.session_monitor.SESSION_DATA_PATH', temp_monitor_dir):
            # Start monitoring
            await monitor.start_monitoring(session_id, sample_session_info)

            # Record events
            await monitor.record_event(session_id, "test_event", {"data": "test"})

            # Trigger auto-save
            await monitor._auto_save_sessions()

            # Verify file was created
            session_file = Path(temp_monitor_dir) / f"{session_id}.json"
            assert session_file.exists()

            # Verify content
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                assert data['session_id'] == session_id
                assert len(data['events']) > 0

    @pytest.mark.asyncio
    async def test_load_session_history(self, monitor, temp_monitor_dir):
        """Test loading session history from disk"""
        # Create a saved session file
        session_data = {
            'session_id': 'historical_session',
            'canvas_path': 'old_canvas.canvas',
            'user_id': 'old_user',
            'start_time': datetime.now().isoformat(),
            'events': [
                {
                    'type': 'test_event',
                    'timestamp': datetime.now().isoformat(),
                    'data': {'test': True}
                }
            ]
        }

        session_file = Path(temp_monitor_dir) / "historical_session.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

        # Load history
        with patch('canvas_utils.session_monitor.SESSION_DATA_PATH', temp_monitor_dir):
            await monitor.load_session_history()

            assert 'historical_session' in monitor.session_history
            history = monitor.session_history['historical_session']
            assert history.canvas_path == 'old_canvas.canvas'
            assert len(history.events) == 1

    @pytest.mark.asyncio
    async def test_generate_session_report(self, monitor, sample_session_info):
        """Test generating session report"""
        session_id = "test_session_001"

        # Start monitoring
        await monitor.start_monitoring(session_id, sample_session_info)

        # Record various events
        await monitor.record_event(session_id, "node_added", {"node_id": "node1"})
        await monitor.record_event(session_id, "explanation_generated", {"doc_id": "doc1"})
        await monitor.record_event(session_id, "error", {"error": "test error"})

        # Update health
        await monitor.update_session_health(session_id, {
            'cpu_usage': 75.0,
            'memory_usage': 80.0,
            'response_time': 150,
            'error_count': 1
        })

        # Generate report
        report = await monitor.generate_session_report(session_id)

        assert report is not None
        assert report.session_id == session_id
        assert report.total_events == 3
        assert report.error_count == 1
        assert report.avg_cpu_usage == 75.0
        assert report.avg_memory_usage == 80.0

    @pytest.mark.asyncio
    async def test_cleanup_old_sessions(self, monitor, temp_monitor_dir):
        """Test cleaning up old session data"""
        # Create old session files
        old_date = (datetime.now() - timedelta(days=30)).isoformat()

        for i in range(3):
            session_data = {
                'session_id': f'old_session_{i}',
                'end_time': old_date
            }
            session_file = Path(temp_monitor_dir) / f"old_session_{i}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f)

        with patch('canvas_utils.session_monitor.SESSION_DATA_PATH', temp_monitor_dir):
            # Cleanup sessions older than 7 days
            cleaned = await monitor.cleanup_old_sessions(days_old=7)

            assert cleaned >= 3

            # Verify files were deleted
            for i in range(3):
                session_file = Path(temp_monitor_dir) / f"old_session_{i}.json"
                assert not session_file.exists()

    def test_calculate_health_score(self, monitor):
        """Test health score calculation"""
        # Good health
        health_good = SessionHealth(
            cpu_usage=30.0,
            memory_usage=40.0,
            response_time=50,
            error_count=0
        )
        score_good = monitor._calculate_health_score(health_good)
        assert score_good >= 90

        # Poor health
        health_poor = SessionHealth(
            cpu_usage=90.0,
            memory_usage=85.0,
            response_time=500,
            error_count=10
        )
        score_poor = monitor._calculate_health_score(health_poor)
        assert score_poor < 50

    def test_session_duration(self, monitor, sample_session_info):
        """Test session duration calculation"""
        session_id = "test_session_001"

        # Create session with known start time
        start_time = datetime.now() - timedelta(minutes=30)
        session_info_copy = sample_session_info.copy()
        session_info_copy['start_time'] = start_time.isoformat()

        # Add to active sessions (simulating start_monitoring)
        session = SessionInfo(
            session_id=session_id,
            canvas_path=session_info_copy['canvas_path'],
            user_id=session_info_copy['user_id'],
            model=session_info_copy.get('model'),
            start_time=start_time,
            status=SessionStatus.ACTIVE
        )
        monitor.active_sessions[session_id] = session

        # Calculate duration
        duration = monitor._get_session_duration(session_id)
        assert duration >= timedelta(minutes=29)  # Allow for small timing differences
        assert duration <= timedelta(minutes=31)

    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, monitor, sample_session_info):
        """Test monitoring multiple concurrent sessions"""
        sessions = []

        # Start multiple sessions
        for i in range(5):
            session_id = f"concurrent_session_{i}"
            session_info = sample_session_info.copy()
            session_info['canvas_path'] = f"canvas_{i}.canvas"
            session_info['user_id'] = f"user_{i}"

            await monitor.start_monitoring(session_id, session_info)
            sessions.append(session_id)

        # Record events in all sessions
        tasks = []
        for session_id in sessions:
            for j in range(3):
                task = monitor.record_event(
                    session_id,
                    f"event_{j}",
                    {"data": f"test_{j}"}
                )
                tasks.append(task)

        await asyncio.gather(*tasks)

        # Verify all sessions have events
        for session_id in sessions:
            session = monitor.active_sessions[session_id]
            assert len(session.events) == 3

        # Stop all sessions
        reports = await asyncio.gather(
            *[monitor.stop_monitoring(sid) for sid in sessions]
        )

        assert all(r is not None for r in reports)
        assert len(set(r.session_id for r in reports)) == 5

    @pytest.mark.asyncio
    async def test_error_recovery(self, monitor, sample_session_info):
        """Test error recovery in monitoring"""
        session_id = "test_session_001"

        # Start monitoring
        await monitor.start_monitoring(session_id, sample_session_info)

        # Simulate error in event recording
        with patch.object(monitor, '_save_event_to_disk', side_effect=Exception("Disk error")):
            # Should not raise exception, but handle gracefully
            result = await monitor.record_event(session_id, "error_event", {})
            assert result  # Event should still be recorded in memory

        # Verify session is still active
        assert session_id in monitor.active_sessions

    def test_validate_session_info(self, monitor):
        """Test session info validation"""
        # Valid info
        valid_info = {
            'canvas_path': 'test.canvas',
            'user_id': 'test_user'
        }
        assert monitor._validate_session_info(valid_info)

        # Missing required fields
        invalid_info = {'user_id': 'test_user'}  # Missing canvas_path
        assert not monitor._validate_session_info(invalid_info)

        # Empty info
        assert not monitor._validate_session_info({})

    @pytest.mark.asyncio
    async def test_export_session_data(self, monitor, sample_session_info, temp_monitor_dir):
        """Test exporting session data"""
        session_id = "test_session_001"

        # Start monitoring and record events
        await monitor.start_monitoring(session_id, sample_session_info)
        await monitor.record_event(session_id, "test_event", {"data": "test"})

        # Export data
        with patch('canvas_utils.session_monitor.SESSION_DATA_PATH', temp_monitor_dir):
            export_path = await monitor.export_session_data(session_id)

            assert export_path is not None
            assert Path(export_path).exists()

            # Verify export content
            with open(export_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                assert data['session_id'] == session_id
                assert 'events' in data
                assert 'export_timestamp' in data

    @pytest.mark.asyncio
    async def test_import_session_data(self, monitor, temp_monitor_dir):
        """Test importing session data"""
        # Create export file
        export_data = {
            'session_id': 'imported_session',
            'canvas_path': 'imported.canvas',
            'user_id': 'import_user',
            'start_time': datetime.now().isoformat(),
            'events': [
                {
                    'type': 'imported_event',
                    'timestamp': datetime.now().isoformat(),
                    'data': {'imported': True}
                }
            ],
            'export_timestamp': datetime.now().isoformat()
        }

        export_file = Path(temp_monitor_dir) / "import_session.json"
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        # Import data
        with patch('canvas_utils.session_monitor.SESSION_DATA_PATH', temp_monitor_dir):
            result = await monitor.import_session_data(str(export_file))

            assert result
            assert 'imported_session' in monitor.session_history

            history = monitor.session_history['imported_session']
            assert history.canvas_path == 'imported.canvas'
            assert len(history.events) == 1


if __name__ == '__main__':
    # Run tests when script is executed directly
    pytest.main([__file__, '-v'])
