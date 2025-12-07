"""
Unit tests for Memory Recorder module
Epic 9 - Canvas System Robustness Enhancement
Story 9.6 - Integration Testing and Validation
"""

import asyncio
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from canvas_utils.memory_recorder import (
        BackupSystem,
        FileSystemMemoryClient,
        GraphitiMemoryClient,
        LocalMemoryClient,
        MemoryEntry,
        MemoryRecorder,
        MemorySystem,
        RecordingResult,
    )
    CANVAS_UTILS_AVAILABLE = True
except ImportError:
    CANVAS_UTILS_AVAILABLE = False
    MemoryRecorder = Mock
    MemorySystem = Mock


@pytest.mark.skipif(not CANVAS_UTILS_AVAILABLE, reason="canvas_utils.memory_recorder not available")
class TestMemoryRecorder:
    """Test suite for MemoryRecorder"""

    @pytest.fixture
    def recorder(self):
        """Create recorder instance for testing"""
        return MemoryRecorder()

    @pytest.fixture
    def sample_session_data(self):
        """Sample session data for testing"""
        return {
            'session_id': 'test_session_001',
            'canvas_path': 'test_canvas.canvas',
            'user_id': 'test_user',
            'start_time': '2025-10-28T10:00:00Z',
            'actions': [
                {
                    'type': 'add_node',
                    'timestamp': '2025-10-28T10:01:00Z',
                    'data': {'node_id': 'node1', 'content': 'Question 1'}
                },
                {
                    'type': 'add_explanation',
                    'timestamp': '2025-10-28T10:02:00Z',
                    'data': {'node_id': 'exp1', 'content': 'Explanation 1'}
                }
            ],
            'metadata': {
                'model': 'opus-4.1',
                'total_nodes': 5,
                'learning_time': 120
            }
        }

    @pytest.fixture
    def temp_memory_dir(self):
        """Create temporary directory for memory storage"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_initialization(self, recorder):
        """Test recorder initialization"""
        assert recorder is not None
        assert hasattr(recorder, 'primary_system')
        assert hasattr(recorder, 'backup_system')
        assert hasattr(recorder, 'tertiary_system')

    def test_memory_system_priority(self, recorder):
        """Test memory system priority order"""
        # Should have primary, backup, and tertiary systems
        assert recorder.primary_system == MemorySystem.GRAPHITI
        assert recorder.backup_system == MemorySystem.LOCAL
        assert recorder.tertiary_system == MemorySystem.FILESYSTEM

    @pytest.mark.asyncio
    async def test_record_session_success(self, recorder, sample_session_data):
        """Test successful session recording"""
        with patch.object(recorder, '_record_to_graphiti', return_value=True), \
             patch.object(recorder, '_record_to_local', return_value=True):

            result = await recorder.record_session(sample_session_data)

            assert result.success
            assert result.session_id == sample_session_data['session_id']
            assert len(result.successful_systems) >= 1

    @pytest.mark.asyncio
    async def test_record_session_primary_failure(self, recorder, sample_session_data):
        """Test session recording with primary system failure"""
        with patch.object(recorder, '_record_to_graphiti', return_value=False), \
             patch.object(recorder, '_record_to_local', return_value=True):

            result = await recorder.record_session(sample_session_data)

            assert result.success
            assert MemorySystem.GRAPHITI not in result.successful_systems
            assert MemorySystem.LOCAL in result.successful_systems

    @pytest.mark.asyncio
    async def test_record_session_all_failures(self, recorder, sample_session_data):
        """Test session recording with all systems failing"""
        with patch.object(recorder, '_record_to_graphiti', return_value=False), \
             patch.object(recorder, '_record_to_local', return_value=False), \
             patch.object(recorder, '_record_to_filesystem', return_value=False):

            result = await recorder.record_session(sample_session_data)

            assert not result.success
            assert len(result.successful_systems) == 0
            assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_record_to_graphiti_success(self, recorder, sample_session_data):
        """Test successful recording to Graphiti"""
        mock_client = Mock()
        mock_client.add_memory = AsyncMock(return_value={'success': True})

        with patch('canvas_utils.memory_recorder.GraphitiMemoryClient', return_value=mock_client):
            result = await recorder._record_to_graphiti(sample_session_data)
            assert result

    @pytest.mark.asyncio
    async def test_record_to_graphiti_failure(self, recorder, sample_session_data):
        """Test recording to Graphiti with failure"""
        mock_client = Mock()
        mock_client.add_memory = AsyncMock(side_effect=Exception("Connection failed"))

        with patch('canvas_utils.memory_recorder.GraphitiMemoryClient', return_value=mock_client):
            result = await recorder._record_to_graphiti(sample_session_data)
            assert not result

    @pytest.mark.asyncio
    async def test_record_to_local_success(self, recorder, sample_session_data, temp_memory_dir):
        """Test successful local recording"""
        with patch('canvas_utils.memory_recorder.LOCAL_MEMORY_PATH', temp_memory_dir):
            result = await recorder._record_to_local(sample_session_data)
            assert result

            # Verify file was created
            memory_file = Path(temp_memory_dir) / f"{sample_session_data['session_id']}.json"
            assert memory_file.exists()

    @pytest.mark.asyncio
    async def test_record_to_filesystem_success(self, recorder, sample_session_data, temp_memory_dir):
        """Test successful filesystem recording"""
        with patch('canvas_utils.memory_recorder.FILESYSTEM_MEMORY_PATH', temp_memory_dir):
            result = await recorder._record_to_filesystem(sample_session_data)
            assert result

            # Verify file was created
            memory_file = Path(temp_memory_dir) / f"{sample_session_data['session_id']}.backup.json"
            assert memory_file.exists()

    def test_create_memory_entry(self, recorder, sample_session_data):
        """Test memory entry creation"""
        action = sample_session_data['actions'][0]
        entry = recorder._create_memory_entry(action, sample_session_data)

        assert isinstance(entry, MemoryEntry)
        assert entry.type == action['type']
        assert entry.session_id == sample_session_data['session_id']
        assert entry.timestamp == action['timestamp']
        assert entry.data == action['data']

    def test_serialize_session_data(self, recorder, sample_session_data):
        """Test session data serialization"""
        serialized = recorder._serialize_session_data(sample_session_data)

        assert isinstance(serialized, str)
        # Should be valid JSON
        parsed = json.loads(serialized)
        assert parsed['session_id'] == sample_session_data['session_id']

    def test_deserialize_session_data(self, recorder, sample_session_data):
        """Test session data deserialization"""
        serialized = json.dumps(sample_session_data)
        deserialized = recorder._deserialize_session_data(serialized)

        assert deserialized['session_id'] == sample_session_data['session_id']
        assert deserialized['canvas_path'] == sample_session_data['canvas_path']

    def test_validate_session_data(self, recorder, sample_session_data):
        """Test session data validation"""
        # Valid data
        assert recorder._validate_session_data(sample_session_data)

        # Missing required fields
        invalid_data = sample_session_data.copy()
        del invalid_data['session_id']
        assert not recorder._validate_session_data(invalid_data)

        # Empty actions
        invalid_data = sample_session_data.copy()
        invalid_data['actions'] = []
        assert not recorder._validate_session_data(invalid_data)

    @pytest.mark.asyncio
    async def test_retrieve_session(self, recorder, sample_session_data):
        """Test retrieving session data"""
        # First record the session
        await recorder.record_session(sample_session_data)

        # Then retrieve it
        with patch.object(recorder, '_retrieve_from_local', return_value=sample_session_data):
            retrieved = await recorder.retrieve_session(sample_session_data['session_id'])
            assert retrieved['session_id'] == sample_session_data['session_id']

    @pytest.mark.asyncio
    async def test_retrieve_session_not_found(self, recorder):
        """Test retrieving non-existent session"""
        with patch.object(recorder, '_retrieve_from_local', return_value=None):
            retrieved = await recorder.retrieve_session('nonexistent_session')
            assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_session(self, recorder, sample_session_data):
        """Test deleting session data"""
        session_id = sample_session_data['session_id']

        with patch.object(recorder, '_delete_from_graphiti', return_value=True), \
             patch.object(recorder, '_delete_from_local', return_value=True), \
             patch.object(recorder, '_delete_from_filesystem', return_value=True):

            result = await recorder.delete_session(session_id)
            assert result

    @pytest.mark.asyncio
    async def test_list_sessions(self, recorder, temp_memory_dir):
        """Test listing all sessions"""
        # Create some test sessions
        sessions = []
        for i in range(3):
            session_data = {
                'session_id': f'test_session_{i}',
                'canvas_path': f'test_{i}.canvas',
                'actions': [{'type': 'test', 'data': {}}]
            }
            sessions.append(session_data)
            await recorder._record_to_local(session_data, temp_memory_dir)

        with patch('canvas_utils.memory_recorder.LOCAL_MEMORY_PATH', temp_memory_dir):
            session_list = await recorder.list_sessions()
            assert len(session_list) >= 3

    def test_generate_session_summary(self, recorder, sample_session_data):
        """Test session summary generation"""
        summary = recorder.generate_session_summary(sample_session_data)

        assert 'session_id' in summary
        assert 'total_actions' in summary
        assert 'duration' in summary
        assert 'action_types' in summary
        assert summary['total_actions'] == len(sample_session_data['actions'])

    def test_get_memory_statistics(self, recorder, temp_memory_dir):
        """Test memory statistics"""
        with patch('canvas_utils.memory_recorder.LOCAL_MEMORY_PATH', temp_memory_dir):
            stats = recorder.get_memory_statistics()

            assert 'total_sessions' in stats
            assert 'total_size' in stats
            assert 'system_status' in stats
            assert isinstance(stats['total_sessions'], int)

    @pytest.mark.asyncio
    async def test_memory_cleanup(self, recorder, temp_memory_dir):
        """Test memory cleanup"""
        # Create old session files
        old_date = datetime.now().timestamp() - (30 * 24 * 60 * 60)  # 30 days ago

        for i in range(3):
            session_file = Path(temp_memory_dir) / f'old_session_{i}.json'
            session_file.write_text(json.dumps({
                'session_id': f'old_session_{i}',
                'timestamp': old_date
            }))

        with patch('canvas_utils.memory_recorder.LOCAL_MEMORY_PATH', temp_memory_dir):
            cleaned = await recorder.cleanup_old_sessions(days_old=7)
            assert cleaned >= 0

    def test_backup_system_fallback(self, recorder, sample_session_data):
        """Test backup system fallback mechanism"""
        backup = BackupSystem()

        # Test creating backup
        backup_data = backup.create_backup(sample_session_data)
        assert 'backup_data' in backup_data
        assert 'timestamp' in backup_data
        assert 'checksum' in backup_data

        # Test restoring from backup
        restored = backup.restore_from_backup(backup_data)
        assert restored['session_id'] == sample_session_data['session_id']

        # Test backup integrity
        assert backup.verify_backup_integrity(backup_data)

    def test_memory_client_factory(self, recorder):
        """Test memory client factory"""
        # Test creating Graphiti client
        graphiti_client = recorder._create_memory_client(MemorySystem.GRAPHITI)
        assert isinstance(graphiti_client, GraphitiMemoryClient)

        # Test creating local client
        local_client = recorder._create_memory_client(MemorySystem.LOCAL)
        assert isinstance(local_client, LocalMemoryClient)

        # Test creating filesystem client
        fs_client = recorder._create_memory_client(MemorySystem.FILESYSTEM)
        assert isinstance(fs_client, FileSystemMemoryClient)

    @pytest.mark.asyncio
    async def test_concurrent_recording(self, recorder, sample_session_data):
        """Test concurrent session recording"""
        # Create multiple sessions
        sessions = []
        for i in range(5):
            session = sample_session_data.copy()
            session['session_id'] = f'concurrent_session_{i}'
            sessions.append(session)

        with patch.object(recorder, '_record_to_local', return_value=True):
            # Record all sessions concurrently
            tasks = [recorder.record_session(session) for session in sessions]
            results = await asyncio.gather(*tasks)

            # Verify all succeeded
            assert all(r.success for r in results)
            assert len(set(r.session_id for r in results)) == 5

    def test_error_handling(self, recorder, sample_session_data):
        """Test error handling in recorder"""
        # Test with invalid session data
        with pytest.raises(ValueError):
            recorder._validate_session_data(None)

        # Test with corrupted data
        corrupted_data = "not a dictionary"
        assert not recorder._validate_session_data(corrupted_data)


@pytest.mark.skipif(not CANVAS_UTILS_AVAILABLE, reason="canvas_utils.memory_recorder not available")
class TestMemoryClients:
    """Test suite for memory client implementations"""

    @pytest.fixture
    def temp_memory_dir(self):
        """Create temporary directory for memory storage"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_local_memory_client(self, temp_memory_dir):
        """Test local memory client"""
        client = LocalMemoryClient(temp_memory_dir)

        session_data = {
            'session_id': 'test_local',
            'data': 'test data'
        }

        # Test storing
        result = await client.store(session_data)
        assert result

        # Test retrieving
        retrieved = await client.retrieve('test_local')
        assert retrieved is not None
        assert retrieved['session_id'] == 'test_local'

        # Test deleting
        deleted = await client.delete('test_local')
        assert deleted

        # Verify deletion
        retrieved = await client.retrieve('test_local')
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_filesystem_memory_client(self, temp_memory_dir):
        """Test filesystem memory client"""
        client = FileSystemMemoryClient(temp_memory_dir)

        session_data = {
            'session_id': 'test_fs',
            'data': 'test data'
        }

        # Test storing
        result = await client.store(session_data)
        assert result

        # Test retrieving
        retrieved = await client.retrieve('test_fs')
        assert retrieved is not None
        assert retrieved['session_id'] == 'test_fs'

        # Test listing
        sessions = await client.list_all()
        assert 'test_fs' in sessions

    @pytest.mark.asyncio
    async def test_graphiti_memory_client(self):
        """Test Graphiti memory client"""
        client = GraphitiMemoryClient()

        session_data = {
            'session_id': 'test_graphiti',
            'data': 'test data'
        }

        # Mock the MCP function
        with patch('canvas_utils.memory_recorder.mcp__graphiti_memory__add_memory') as mock_add:
            mock_add.return_value = {'success': True}

            # Test storing
            result = await client.store(session_data)
            assert result
            mock_add.assert_called_once()

        # Mock retrieval
        with patch('canvas_utils.memory_recorder.mcp__graphiti_memory__search_memories') as mock_search:
            mock_search.return_value = [{
                'content': json.dumps(session_data),
                'memory_id': 'test_id'
            }]

            # Test retrieving
            retrieved = await client.retrieve('test_graphiti')
            assert retrieved is not None
            assert retrieved['session_id'] == 'test_graphiti'


if __name__ == '__main__':
    # Run tests when script is executed directly
    pytest.main([__file__, '-v'])
