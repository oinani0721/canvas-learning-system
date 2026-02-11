# Story 35.10: Multimodal Path Traversal Security Tests
# [Source: docs/stories/35.10.story.md#AC-35.10.1, AC-35.10.2]
"""
Tests for path traversal defense in MultimodalService.

AC 35.10.1: upload_file() rejects path traversal filenames
AC 35.10.2: upload_from_url() rejects path traversal filenames
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.multimodal_service import (
    MultimodalService,
    MultimodalServiceError,
    reset_multimodal_service,
)


@pytest.fixture
def tmp_storage(tmp_path):
    """Create a temporary storage directory with media subdirs."""
    for subdir in ("image", "pdf", "audio", "video"):
        (tmp_path / subdir).mkdir()
    return tmp_path


@pytest.fixture
def service(tmp_storage):
    """Create a fresh MultimodalService with tmp storage."""
    reset_multimodal_service()
    svc = MultimodalService(storage_base_path=str(tmp_storage))
    svc._initialized = True
    try:
        yield svc
    finally:
        reset_multimodal_service()


# =============================================================================
# AC 35.10.1 + 35.10.2: _validate_safe_path unit tests
# =============================================================================


class TestValidateSafePath:
    """Direct tests for _validate_safe_path method."""

    def test_valid_path_within_storage(self, service, tmp_storage):
        """Normal file path within storage should pass."""
        file_path = Path(tmp_storage) / "image" / "20260209_abc123.png"
        result = service._validate_safe_path(file_path)
        assert result == file_path.resolve()

    def test_path_traversal_unix_style(self, service, tmp_storage):
        """Unix-style ../.. path traversal should be rejected."""
        file_path = Path(tmp_storage) / "image" / "../../etc/passwd"
        with pytest.raises(MultimodalServiceError, match="path traversal"):
            service._validate_safe_path(file_path)

    def test_path_traversal_windows_style(self, service, tmp_storage):
        """Windows-style ..\\.. path traversal should be rejected."""
        file_path = Path(tmp_storage) / "image" / "..\\..\\windows\\system32\\config"
        with pytest.raises(MultimodalServiceError, match="path traversal"):
            service._validate_safe_path(file_path)

    def test_path_traversal_deep_nested(self, service, tmp_storage):
        """Deep nested ../../../.. traversal should be rejected."""
        file_path = Path(tmp_storage) / "image" / "../../../../../../../tmp/evil"
        with pytest.raises(MultimodalServiceError, match="path traversal"):
            service._validate_safe_path(file_path)

    def test_path_traversal_mixed(self, service, tmp_storage):
        """Mixed normal/../../../evil.txt should be rejected."""
        file_path = Path(tmp_storage) / "image" / "normal/../../../evil.txt"
        with pytest.raises(MultimodalServiceError, match="path traversal"):
            service._validate_safe_path(file_path)

    def test_path_within_subdirectory(self, service, tmp_storage):
        """Path within a valid subdirectory should pass."""
        file_path = Path(tmp_storage) / "pdf" / "20260209_doc.pdf"
        result = service._validate_safe_path(file_path)
        assert result == file_path.resolve()

    def test_error_code_is_path_traversal(self, service, tmp_storage):
        """Error should have PATH_TRAVERSAL_ERROR code."""
        file_path = Path(tmp_storage) / "image" / "../../etc/passwd"
        with pytest.raises(MultimodalServiceError) as exc_info:
            service._validate_safe_path(file_path)
        assert exc_info.value.error_code == "PATH_TRAVERSAL_ERROR"


# =============================================================================
# AC 35.10.1: upload_file path traversal integration
# =============================================================================


class TestUploadFilePathTraversal:
    """Test that upload_file calls _validate_safe_path."""

    # Minimal valid PNG magic bytes (8-byte signature)
    VALID_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

    @pytest.mark.asyncio
    @pytest.mark.parametrize("malicious_filename", [
        "../../etc/passwd",
        "..\\..\\windows\\system32\\config",
        "normal/../../../evil.txt",
        "../../../../../../../tmp/evil",
    ])
    async def test_upload_file_rejects_traversal(
        self, service, malicious_filename
    ):
        """upload_file should reject path traversal filenames via _validate_safe_path."""
        # _generate_unique_filename sanitizes filenames, so we test via
        # direct _validate_safe_path mock to verify it's called
        with patch.object(service, "_validate_safe_path", side_effect=MultimodalServiceError(
            "Invalid file path: path traversal detected", "PATH_TRAVERSAL_ERROR"
        )) as mock_validate:
            with pytest.raises(MultimodalServiceError, match="path traversal"):
                await service.upload_file(
                    file_bytes=self.VALID_PNG_BYTES,
                    filename=malicious_filename,
                    content_type="image/png",
                    file_size=len(self.VALID_PNG_BYTES),
                    related_concept_id="test-concept",
                )
            mock_validate.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_file_calls_validate_safe_path(self, service, tmp_storage):
        """upload_file must call _validate_safe_path before writing."""
        call_order = []
        original_validate = service._validate_safe_path

        def tracking_validate(path):
            call_order.append("validate")
            return original_validate(path)

        with patch.object(service, "_validate_safe_path", side_effect=tracking_validate):
            with patch("builtins.open", create=True) as mock_open:
                mock_open.return_value.__enter__ = MagicMock()
                mock_open.return_value.__exit__ = MagicMock(return_value=False)
                try:
                    await service.upload_file(
                        file_bytes=self.VALID_PNG_BYTES,
                        filename="safe.png",
                        content_type="image/png",
                        file_size=len(self.VALID_PNG_BYTES),
                        related_concept_id="test-concept",
                    )
                except Exception:
                    pass  # We only care that validate was called

        assert "validate" in call_order


# =============================================================================
# AC 35.10.2: upload_from_url path traversal integration
# =============================================================================


class TestUploadFromUrlPathTraversal:
    """Test that upload_from_url calls _validate_safe_path."""

    @pytest.mark.asyncio
    async def test_upload_from_url_calls_validate_safe_path(self, service):
        """upload_from_url must call _validate_safe_path before writing."""
        with patch.object(service, "_validate_safe_path", side_effect=MultimodalServiceError(
            "Invalid file path: path traversal detected", "PATH_TRAVERSAL_ERROR"
        )) as mock_validate:
            # Mock httpx response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "image/png"}
            mock_response.content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client.get = AsyncMock(return_value=mock_response)
                mock_client_cls.return_value = mock_client

                from app.models.multimodal_schemas import MultimodalUploadUrlRequest
                request = MultimodalUploadUrlRequest(
                    url="https://example.com/image.png",
                    related_concept_id="test-concept",
                )

                with pytest.raises(MultimodalServiceError, match="path traversal"):
                    await service.upload_from_url(request)

            mock_validate.assert_called_once()


# =============================================================================
# Real defense chain tests (no mocking _validate_safe_path)
# [Code Review H-2]: Verify the actual defense chain without mocks
# =============================================================================


class TestRealDefenseChain:
    """
    Test the real path traversal defense chain WITHOUT mocking _validate_safe_path.

    These tests verify that:
    1. _generate_unique_filename() sanitizes filenames (primary defense)
    2. _validate_safe_path() catches any remaining traversal (secondary defense)
    3. The two defenses work together end-to-end
    """

    VALID_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

    def test_validate_safe_path_real_blocks_crafted_path(self, service, tmp_storage):
        """Directly calling _validate_safe_path with a traversal path rejects it."""
        evil_path = Path(tmp_storage) / "image" / "../../etc/passwd"
        with pytest.raises(MultimodalServiceError, match="path traversal"):
            service._validate_safe_path(evil_path)

    @pytest.mark.asyncio
    async def test_upload_file_real_chain_safe_filename_generated(
        self, service, tmp_storage
    ):
        """
        Real defense chain: upload_file with malicious filename
        generates a safe unique filename, so _validate_safe_path passes.

        This proves the primary defense (_generate_unique_filename) works.
        """
        call_log = []
        original_validate = service._validate_safe_path

        def spy_validate(path):
            call_log.append(("validate", str(path)))
            return original_validate(path)

        with patch.object(service, "_validate_safe_path", side_effect=spy_validate):
            with patch("builtins.open", create=True) as mock_open:
                mock_open.return_value.__enter__ = MagicMock()
                mock_open.return_value.__exit__ = MagicMock(return_value=False)
                try:
                    await service.upload_file(
                        file_bytes=self.VALID_PNG_BYTES,
                        filename="../../etc/passwd.png",
                        content_type="image/png",
                        file_size=len(self.VALID_PNG_BYTES),
                        related_concept_id="test-concept",
                    )
                except Exception:
                    pass

        # _validate_safe_path was called
        assert len(call_log) > 0
        # The path passed to it does NOT contain ".." because
        # _generate_unique_filename replaced the filename
        validated_path = call_log[0][1]
        assert ".." not in validated_path, (
            f"_generate_unique_filename should have sanitized the path, "
            f"but got: {validated_path}"
        )

    def test_generate_unique_filename_strips_path_components(self, service):
        """_generate_unique_filename produces a safe name regardless of input."""
        from app.models.multimodal_schemas import MultimodalMediaType

        malicious_names = [
            "../../etc/passwd",
            "..\\..\\windows\\system32\\config.png",
            "normal/../../../evil.png",
            "a/b/c/d/e.png",
        ]
        for name in malicious_names:
            result = service._generate_unique_filename(name, MultimodalMediaType.IMAGE)
            assert "/" not in result, f"Generated filename contains /: {result}"
            assert "\\" not in result, f"Generated filename contains \\: {result}"
            assert ".." not in result, f"Generated filename contains ..: {result}"
