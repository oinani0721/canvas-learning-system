"""
Unit tests for Path Manager module
Epic 9 - Canvas System Robustness Enhancement
Story 9.6 - Integration Testing and Validation
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from canvas_utils.path_manager import (
        PathManager,
        PathResolutionResult,
        PathType,
        PathError,
        PathValidationError
    )
    CANVAS_UTILS_AVAILABLE = True
except ImportError:
    CANVAS_UTILS_AVAILABLE = False
    PathManager = Mock
    PathType = Mock


@pytest.mark.skipif(not CANVAS_UTILS_AVAILABLE, reason="canvas_utils.path_manager not available")
class TestPathManager:
    """Test suite for PathManager"""

    @pytest.fixture
    def path_manager(self):
        """Create PathManager instance for testing"""
        return PathManager()

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing"""
        temp_dir = tempfile.mkdtemp()
        workspace = Path(temp_dir)

        # Create typical directory structure
        (workspace / "Canvas").mkdir()
        (workspace / "Canvas" / "TestCanvas").mkdir()
        (workspace / "Canvas" / "TestCanvas" / "Docs").mkdir()

        yield str(workspace)

        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def sample_canvas_path(self):
        """Sample canvas file path"""
        return "C:/Users/ROG/托福/笔记库/数学/微积分.canvas"

    def test_initialization(self, path_manager):
        """Test PathManager initialization"""
        assert path_manager is not None
        assert hasattr(path_manager, 'current_canvas')
        assert hasattr(path_manager, 'workspace_root')
        assert hasattr(path_manager, 'path_cache')

    def test_set_current_canvas(self, path_manager, sample_canvas_path):
        """Test setting current canvas"""
        path_manager.set_current_canvas(sample_canvas_path)
        assert path_manager.current_canvas == sample_canvas_path
        assert path_manager.canvas_name == "微积分"

    def test_set_current_canvas_with_path_object(self, path_manager, sample_canvas_path):
        """Test setting current canvas with Path object"""
        canvas_path = Path(sample_canvas_path)
        path_manager.set_current_canvas(canvas_path)
        assert str(path_manager.current_canvas) == sample_canvas_path

    def test_generate_consistent_path(self, path_manager, temp_workspace):
        """Test generating consistent paths"""
        path_manager.set_current_canvas(f"{temp_workspace}/Canvas/TestCanvas/TestCanvas.canvas")

        # Generate path for markdown document
        doc_path = path_manager.generate_consistent_path("费曼学习法.md")

        # Should include canvas name and timestamp
        assert "TestCanvas" in doc_path
        assert "费曼学习法" in doc_path
        assert doc_path.endswith(".md")

    def test_generate_consistent_path_with_timestamp(self, path_manager, temp_workspace):
        """Test generating paths with timestamp"""
        path_manager.set_current_canvas(f"{temp_workspace}/Canvas/TestCanvas/TestCanvas.canvas")

        # Mock datetime
        with patch('canvas_utils.path_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20251028120000"

            doc_path = path_manager.generate_consistent_path("test.md")

            # Should contain timestamp
            assert "20251028120000" in doc_path

    def test_generate_consistent_path_custom_type(self, path_manager, temp_workspace):
        """Test generating paths for different file types"""
        path_manager.set_current_canvas(f"{temp_workspace}/Canvas/TestCanvas/TestCanvas.canvas")

        # Test different file types
        pdf_path = path_manager.generate_consistent_path("document.pdf")
        json_path = path_manager.generate_consistent_path("data.json")

        assert pdf_path.endswith(".pdf")
        assert json_path.endswith(".json")

    def test_resolve_relative_path(self, path_manager, temp_workspace):
        """Test resolving relative paths"""
        path_manager.set_current_canvas(f"{temp_workspace}/Canvas/TestCanvas/TestCanvas.canvas")

        # Resolve relative path
        relative_path = "./Docs/document.md"
        resolved = path_manager.resolve_relative_path(relative_path)

        assert "TestCanvas" in resolved
        assert "Docs" in resolved
        assert not resolved.startswith("./")

    def test_resolve_relative_path_absolute(self, path_manager):
        """Test resolving absolute path"""
        absolute_path = "C:/Users/Documents/test.md"
        resolved = path_manager.resolve_relative_path(absolute_path)

        # Should return as-is
        assert resolved == absolute_path

    def test_validate_path_exists(self, path_manager, temp_workspace):
        """Test validating existing path"""
        # Create a test file
        test_file = Path(temp_workspace) / "test.txt"
        test_file.write_text("test content")

        result = path_manager.validate_path(str(test_file))
        assert result.is_valid
        assert result.exists
        assert result.path_type == PathType.FILE

    def test_validate_path_not_exists(self, path_manager, temp_workspace):
        """Test validating non-existent path"""
        non_existent = Path(temp_workspace) / "non_existent.txt"

        result = path_manager.validate_path(str(non_existent))
        assert not result.is_valid
        assert not result.exists
        assert "not found" in result.error.lower()

    def test_validate_path_directory(self, path_manager, temp_workspace):
        """Test validating directory path"""
        result = path_manager.validate_path(temp_workspace)
        assert result.is_valid
        assert result.exists
        assert result.path_type == PathType.DIRECTORY

    def test_validate_and_fix_path(self, path_manager, temp_workspace):
        """Test validating and fixing broken paths"""
        path_manager.set_current_canvas(f"{temp_workspace}/Canvas/TestCanvas/TestCanvas.canvas")

        # Create a test file with correct name but wrong timestamp
        test_file = Path(temp_workspace) / "Canvas" / "TestCanvas" / "Test-文档-20251028120000.md"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("Test content")

        # Try to find with different timestamp
        broken_path = "./Test-文档-20251028123000.md"
        fixed_path = path_manager.validate_and_fix_path(broken_path)

        # Should find the existing file
        assert "20251028120000" in fixed_path
        assert Path(fixed_path).exists()

    def test_validate_and_fix_path_not_found(self, path_manager, temp_workspace):
        """Test fixing path when file doesn't exist"""
        path_manager.set_current_canvas(f"{temp_workspace}/Canvas/TestCanvas/TestCanvas.canvas")

        broken_path = "./NonExistent-文档-20251028120000.md"
        fixed_path = path_manager.validate_and_fix_path(broken_path)

        # Should return original path if not found
        assert fixed_path == broken_path

    def test_extract_canvas_name(self, path_manager):
        """Test extracting canvas name from path"""
        canvas_path = "C:/Users/ROG/托福/笔记库/数学/微积分.canvas"
        name = path_manager._extract_canvas_name(canvas_path)
        assert name == "微积分"

        # Test with Path object
        canvas_path = Path(canvas_path)
        name = path_manager._extract_canvas_name(canvas_path)
        assert name == "微积分"

    def test_extract_canvas_name_invalid(self, path_manager):
        """Test extracting canvas name from invalid path"""
        with pytest.raises(PathValidationError):
            path_manager._extract_canvas_name("invalid_path")

    def test_sanitize_filename(self, path_manager):
        """Test filename sanitization"""
        # Test with invalid characters
        invalid_name = "文件名<>:\"|?*"
        sanitized = path_manager._sanitize_filename(invalid_name)

        assert "<" not in sanitized
        assert ">" not in sanitized
        assert ":" not in sanitized
        assert '"' not in sanitized
        assert "|" not in sanitized
        assert "?" not in sanitized
        assert "*" not in sanitized

    def test_create_directory_structure(self, path_manager, temp_workspace):
        """Test creating directory structure"""
        path_manager.set_current_canvas(f"{temp_workspace}/Canvas/TestCanvas/TestCanvas.canvas")

        doc_path = path_manager.generate_consistent_path("Docs/test.md")

        # Directory should be created when path is generated
        directory = Path(doc_path).parent
        assert directory.exists()

    def test_get_canvas_directory(self, path_manager, temp_workspace):
        """Test getting canvas directory"""
        canvas_path = f"{temp_workspace}/Canvas/TestCanvas/TestCanvas.canvas"
        path_manager.set_current_canvas(canvas_path)

        canvas_dir = path_manager.get_canvas_directory()
        assert canvas_dir == str(Path(canvas_path).parent)

    def test_get_relative_to_canvas(self, path_manager, temp_workspace):
        """Test getting path relative to canvas"""
        canvas_path = f"{temp_workspace}/Canvas/TestCanvas/TestCanvas.canvas"
        path_manager.set_current_canvas(canvas_path)

        target_path = f"{temp_workspace}/Canvas/TestCanvas/Docs/document.md"
        relative = path_manager.get_relative_to_canvas(target_path)

        assert relative.startswith("./")
        assert "Docs" in relative

    def test_find_similar_files(self, path_manager, temp_workspace):
        """Test finding similar files"""
        path_manager.set_current_canvas(f"{temp_workspace}/Canvas/TestCanvas/TestCanvas.canvas")

        # Create test files
        canvas_dir = Path(temp_workspace) / "Canvas" / "TestCanvas"
        test_files = [
            "Test-概念-20251028120000.md",
            "Test-概念-20251028121000.md",
            "Test-其他-20251028120000.md"
        ]

        for file in test_files:
            (canvas_dir / file).write_text("content")

        # Find similar files
        similar = path_manager.find_similar_files("Test-概念-20251028123000.md")

        assert len(similar) >= 2
        assert any("概念" in s for s in similar)

    def test_cleanup_old_files(self, path_manager, temp_workspace):
        """Test cleaning up old files"""
        path_manager.set_current_canvas(f"{temp_workspace}/Canvas/TestCanvas/TestCanvas.canvas")

        canvas_dir = Path(temp_workspace) / "Canvas" / "TestCanvas"

        # Create old and new files
        old_file = canvas_dir / "Old-文档-20250101120000.md"
        new_file = canvas_dir / "New-文档-20251028120000.md"

        old_file.write_text("old content")
        new_file.write_text("new content")

        # Set old file modification time
        import time
        old_time = time.time() - (30 * 24 * 60 * 60)  # 30 days ago
        os.utime(old_file, (old_time, old_time))

        # Cleanup files older than 7 days
        cleaned = path_manager.cleanup_old_files(days_old=7)
        assert cleaned >= 1
        assert not old_file.exists()
        assert new_file.exists()

    def test_get_path_statistics(self, path_manager, temp_workspace):
        """Test getting path statistics"""
        path_manager.set_current_canvas(f"{temp_workspace}/Canvas/TestCanvas/TestCanvas.canvas")

        # Create some files
        canvas_dir = Path(temp_workspace) / "Canvas" / "TestCanvas"
        (canvas_dir / "file1.md").write_text("content1")
        (canvas_dir / "file2.md").write_text("content2")
        (canvas_dir / "subdir").mkdir()
        (canvas_dir / "subdir" / "file3.md").write_text("content3")

        stats = path_manager.get_path_statistics()

        assert 'total_files' in stats
        assert 'total_directories' in stats
        assert 'total_size' in stats
        assert stats['total_files'] >= 3
        assert stats['total_directories'] >= 1

    def test_backup_path(self, path_manager, temp_workspace):
        """Test creating path backup"""
        path_manager.set_current_canvas(f"{temp_workspace}/Canvas/TestCanvas/TestCanvas.canvas")

        # Create a test file
        original_path = path_manager.generate_consistent_path("test.md")
        Path(original_path).write_text("test content")

        # Create backup
        backup_path = path_manager.backup_path(original_path)

        assert backup_path != original_path
        assert "backup" in backup_path
        assert Path(backup_path).exists()
        assert Path(backup_path).read_text() == "test content"

    def test_restore_from_backup(self, path_manager, temp_workspace):
        """Test restoring from backup"""
        path_manager.set_current_canvas(f"{temp_workspace}/Canvas/TestCanvas/TestCanvas.canvas")

        # Create original file
        original_path = path_manager.generate_consistent_path("test.md")
        Path(original_path).write_text("original content")

        # Create backup
        backup_path = path_manager.backup_path(original_path)

        # Modify original
        Path(original_path).write_text("modified content")

        # Restore from backup
        restored = path_manager.restore_from_backup(backup_path)

        assert restored
        assert Path(original_path).read_text() == "original content"

    def test_path_normalization(self, path_manager):
        """Test path normalization"""
        # Test with different path separators
        path1 = "C:/Users/Test\\File.md"
        path2 = "C:\\Users\\Test/File.md"

        normalized1 = path_manager._normalize_path(path1)
        normalized2 = path_manager._normalize_path(path2)

        assert normalized1 == normalized2

    def test_is_valid_filename(self, path_manager):
        """Test filename validation"""
        # Valid filenames
        valid_names = [
            "document.md",
            "文件名.txt",
            "file_with_underscores.pdf",
            "file-with-dashes.json"
        ]

        for name in valid_names:
            assert path_manager._is_valid_filename(name)

        # Invalid filenames
        invalid_names = [
            "file<name>.txt",
            "file|name.txt",
            "file?.txt",
            "file*.txt",
            "file\".txt",
            "CON.txt",  # Windows reserved name
            "file\t.txt"  # Contains tab
        ]

        for name in invalid_names:
            assert not path_manager._is_valid_filename(name)

    def test_error_handling(self, path_manager):
        """Test error handling"""
        # Test with None path
        with pytest.raises(PathValidationError):
            path_manager.set_current_canvas(None)

        # Test with empty path
        with pytest.raises(PathValidationError):
            path_manager.set_current_canvas("")

    def test_caching(self, path_manager, temp_workspace):
        """Test path caching mechanism"""
        path_manager.set_current_canvas(f"{temp_workspace}/Canvas/TestCanvas/TestCanvas.canvas")

        # Generate path first time
        path1 = path_manager.generate_consistent_path("test.md")

        # Generate same path second time (should use cache)
        path2 = path_manager.generate_consistent_path("test.md")

        assert path1 == path2
        assert path_manager._is_cached("test.md")


if __name__ == '__main__':
    # Run tests when script is executed directly
    pytest.main([__file__, '-v'])