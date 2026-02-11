"""
Story 31.A.7: TTLCache 会话存储降级透明化测试

验证 VerificationService 的内存存储局限性对开发者和运维完全透明。
"""

import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestTTLCacheTransparency:
    """Story 31.A.7: TTLCache 透明化测试"""

    def test_startup_warning_logged(self, caplog):
        """AC-31.A.7.1: 启动时输出 WARNING 日志声明存储模式"""
        from app.services.verification_service import VerificationService

        with caplog.at_level(logging.WARNING, logger="app.services.verification_service"):
            svc = VerificationService(canvas_base_path="/tmp")

        assert "IN-MEMORY TTLCache" in caplog.text
        assert "LOST on service restart" in caplog.text
        assert "maxsize=500" in caplog.text
        assert "ttl=3600" in caplog.text

    @pytest.mark.asyncio
    async def test_expired_session_warning_get_progress(self, caplog):
        """AC-31.A.7.2: get_progress 访问不存在会话时 WARNING 日志"""
        from app.services.verification_service import VerificationService

        svc = VerificationService(canvas_base_path="/tmp")

        with caplog.at_level(logging.WARNING, logger="app.services.verification_service"):
            with pytest.raises(ValueError, match="Session not found"):
                await svc.get_progress("nonexistent-session-id")

        assert "may have expired" in caplog.text or "TTL" in caplog.text

    @pytest.mark.asyncio
    async def test_expired_session_warning_process_answer(self, caplog):
        """AC-31.A.7.2: process_answer 访问不存在会话时 WARNING 日志"""
        from app.services.verification_service import VerificationService

        svc = VerificationService(canvas_base_path="/tmp")

        with caplog.at_level(logging.WARNING, logger="app.services.verification_service"):
            with pytest.raises(ValueError, match="Session not found"):
                await svc.process_answer("nonexistent-session-id", "test answer")

        assert "may have expired" in caplog.text or "TTL" in caplog.text

    @pytest.mark.asyncio
    async def test_expired_session_warning_pause_session(self, caplog):
        """AC-31.A.7.2: pause_session 访问不存在会话时 WARNING 日志"""
        from app.services.verification_service import VerificationService

        svc = VerificationService(canvas_base_path="/tmp")

        with caplog.at_level(logging.WARNING, logger="app.services.verification_service"):
            with pytest.raises(ValueError, match="Session not found"):
                await svc.pause_session("nonexistent-session-id")

        assert "may have expired" in caplog.text or "TTL" in caplog.text

    @pytest.mark.asyncio
    async def test_expired_session_warning_resume_session(self, caplog):
        """AC-31.A.7.2: resume_session 访问不存在会话时 WARNING 日志"""
        from app.services.verification_service import VerificationService

        svc = VerificationService(canvas_base_path="/tmp")

        with caplog.at_level(logging.WARNING, logger="app.services.verification_service"):
            with pytest.raises(ValueError, match="Session not found"):
                await svc.resume_session("nonexistent-session-id")

        assert "may have expired" in caplog.text or "TTL" in caplog.text

    @pytest.mark.asyncio
    async def test_expired_session_warning_end_session(self, caplog):
        """AC-31.A.7.2: end_session 访问不存在会话时 WARNING 日志"""
        from app.services.verification_service import VerificationService

        svc = VerificationService(canvas_base_path="/tmp")

        with caplog.at_level(logging.WARNING, logger="app.services.verification_service"):
            with pytest.raises(ValueError, match="Session not found"):
                await svc.end_session("nonexistent-session-id")

        assert "may have expired" in caplog.text or "TTL" in caplog.text

    @pytest.mark.asyncio
    async def test_expired_session_warning_skip_concept(self, caplog):
        """AC-31.A.7.2: skip_concept 访问不存在会话时 WARNING 日志"""
        from app.services.verification_service import VerificationService

        svc = VerificationService(canvas_base_path="/tmp")

        with caplog.at_level(logging.WARNING, logger="app.services.verification_service"):
            with pytest.raises(ValueError, match="Session not found"):
                await svc.skip_concept("nonexistent-session-id")

        assert "may have expired" in caplog.text or "TTL" in caplog.text

    def test_architecture_limitation_comment_exists(self):
        """AC-31.A.7.3: 代码中有架构限制注释"""
        import inspect
        from app.services.verification_service import VerificationService

        source = inspect.getsource(VerificationService.__init__)
        assert "ARCHITECTURE LIMITATION" in source
        assert "Service restart" in source or "service restart" in source
        assert "auto-expire" in source or "3600s" in source
        assert "500 concurrent" in source or "maxsize" in source

    @pytest.mark.asyncio
    async def test_get_progress_includes_storage_info(self, caplog):
        """AC-31.A.7.4: get_progress 返回包含 storage_info"""
        from app.services.verification_service import (
            VerificationService,
            VerificationProgress,
            VerificationStatus,
        )
        from datetime import datetime

        svc = VerificationService(canvas_base_path="/tmp")

        # Manually create a session for testing
        session_id = "test-session-123"
        progress = VerificationProgress(
            session_id=session_id,
            canvas_name="test",
            total_concepts=3,
            completed_concepts=0,
            current_concept="test concept",
            current_concept_idx=0,
        )
        svc._progress[session_id] = progress

        result = await svc.get_progress(session_id)

        assert "storage_info" in result
        assert result["storage_info"]["type"] == "in_memory_ttl_cache"
        assert result["storage_info"]["ttl_seconds"] == 3600
        assert "warning" in result["storage_info"]

    @pytest.mark.asyncio
    async def test_existing_session_no_false_warning(self, caplog):
        """确保访问存在的会话不会触发过期警告"""
        from app.services.verification_service import (
            VerificationService,
            VerificationProgress,
        )

        svc = VerificationService(canvas_base_path="/tmp")

        session_id = "existing-session"
        progress = VerificationProgress(
            session_id=session_id,
            canvas_name="test",
            total_concepts=3,
            completed_concepts=0,
            current_concept="test concept",
            current_concept_idx=0,
        )
        svc._progress[session_id] = progress

        with caplog.at_level(logging.WARNING, logger="app.services.verification_service"):
            result = await svc.get_progress(session_id)

        # Should NOT contain expiry warning for existing sessions
        assert "may have expired" not in caplog.text

    @pytest.mark.asyncio
    async def test_valueerror_backward_compatible(self):
        """AC-31.A.7.2: ValueError 行为保持向后兼容"""
        from app.services.verification_service import VerificationService

        svc = VerificationService(canvas_base_path="/tmp")

        with pytest.raises(ValueError, match="Session not found"):
            await svc.get_progress("nonexistent")
