# Canvas Learning System - Story 12.J.4 Tests
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing)
"""
Story 12.J.4 - UnicodeEncodeError Exception Handling Tests

Tests for explicit UnicodeEncodeError handling in Agent endpoints:
- AC1: UnicodeEncodeError returns structured ENCODING_ERROR type response
- AC2: Error logs use ASCII-safe format (no secondary encoding errors)
- AC3: All 11 Agent endpoints have explicit UnicodeEncodeError handlers
- AC4: Encoding error includes safe diagnostic info (hex position, char code)

[Source: docs/stories/story-12.J.4-unicode-exception-handling.md#Testing]
[Source: specs/api/agent-api.openapi.yml#AgentErrorType]
"""

from unittest.mock import patch

import pytest
from app.api.v1.endpoints.agents import _create_encoding_error_response

# ═══════════════════════════════════════════════════════════════════════════════
# AC1: Structured ENCODING_ERROR Response Tests
# ═══════════════════════════════════════════════════════════════════════════════


def test_encoding_error_returns_encoding_error_type():
    """
    AC1: UnicodeEncodeError returns structured ENCODING_ERROR type.

    [Source: docs/stories/story-12.J.4-unicode-exception-handling.md#AC-1]
    [Source: specs/api/agent-api.openapi.yml#AgentErrorType]
    """
    # Create a UnicodeEncodeError similar to Windows GBK encoding issues
    error = UnicodeEncodeError(
        'gbk',           # encoding name
        'test\U0001F525emoji',  # object (with fire emoji)
        4,               # start position
        5,               # end position
        'illegal multibyte sequence'  # reason
    )

    with patch('app.api.v1.endpoints.agents.cancel_request'):
        with patch('app.api.v1.endpoints.agents.logger'):
            http_exception = _create_encoding_error_response(
                e=error,
                endpoint_name="test_endpoint",
                cache_key="test_key"
            )

    # Verify HTTPException is returned with correct structure
    assert http_exception.status_code == 500
    assert http_exception.detail["error_type"] == "ENCODING_ERROR"
    assert http_exception.detail["message"] == "Text encoding error - please ensure content uses UTF-8"
    assert http_exception.detail["is_retryable"] is True


def test_encoding_error_is_retryable():
    """
    AC1.2: ENCODING_ERROR has is_retryable=True per ADR-009.

    [Source: docs/stories/story-12.J.4-unicode-exception-handling.md#AC-1]
    [Source: ADR-009 - 错误分类体系: ENCODING_ERROR is RETRYABLE]
    """
    error = UnicodeEncodeError('gbk', 'test\u4e2d\u6587', 4, 5, 'illegal')

    with patch('app.api.v1.endpoints.agents.cancel_request'):
        with patch('app.api.v1.endpoints.agents.logger'):
            http_exception = _create_encoding_error_response(
                e=error,
                endpoint_name="decompose_basic",
                cache_key=""
            )

    assert http_exception.detail["is_retryable"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# AC4: Safe Diagnostic Information Tests
# ═══════════════════════════════════════════════════════════════════════════════


def test_encoding_error_diagnostic_contains_position():
    """
    AC4.1: Diagnostic info contains error position.

    [Source: docs/stories/story-12.J.4-unicode-exception-handling.md#AC-4]
    """
    error = UnicodeEncodeError('gbk', 'abc\U0001F525xyz', 3, 4, 'illegal')

    with patch('app.api.v1.endpoints.agents.cancel_request'):
        with patch('app.api.v1.endpoints.agents.logger'):
            http_exception = _create_encoding_error_response(
                e=error,
                endpoint_name="decompose_basic",
                cache_key=""
            )

    diagnostic = http_exception.detail["diagnostic"]
    assert "position 3" in diagnostic


def test_encoding_error_diagnostic_contains_hex_char_code():
    """
    AC4.2: Diagnostic info contains hex char code (U+XXXX format).

    [Source: docs/stories/story-12.J.4-unicode-exception-handling.md#AC-4]
    """
    # Fire emoji: U+1F525
    error = UnicodeEncodeError('gbk', 'abc\U0001F525', 3, 4, 'illegal')

    with patch('app.api.v1.endpoints.agents.cancel_request'):
        with patch('app.api.v1.endpoints.agents.logger'):
            http_exception = _create_encoding_error_response(
                e=error,
                endpoint_name="decompose_basic",
                cache_key=""
            )

    diagnostic = http_exception.detail["diagnostic"]
    assert "U+1F525" in diagnostic  # Fire emoji code point


def test_encoding_error_diagnostic_chinese_character():
    """
    AC4.3: Diagnostic handles Chinese characters correctly.

    [Source: docs/stories/story-12.J.4-unicode-exception-handling.md#AC-4]
    """
    # Chinese character 中 = U+4E2D
    error = UnicodeEncodeError('ascii', 'test\u4e2d', 4, 5, 'ordinal not in range')

    with patch('app.api.v1.endpoints.agents.cancel_request'):
        with patch('app.api.v1.endpoints.agents.logger'):
            http_exception = _create_encoding_error_response(
                e=error,
                endpoint_name="explain_oral",
                cache_key=""
            )

    diagnostic = http_exception.detail["diagnostic"]
    assert "position 4" in diagnostic
    assert "U+4E2D" in diagnostic


# ═══════════════════════════════════════════════════════════════════════════════
# AC2: ASCII-Safe Logging Tests
# ═══════════════════════════════════════════════════════════════════════════════


def test_encoding_error_logs_ascii_safe():
    """
    AC2: Error log uses ASCII-safe format (no emoji/Unicode).

    [Source: docs/stories/story-12.J.4-unicode-exception-handling.md#AC-2]
    """
    error = UnicodeEncodeError('gbk', 'test\U0001F525', 4, 5, 'illegal')

    with patch('app.api.v1.endpoints.agents.cancel_request'):
        with patch('app.api.v1.endpoints.agents.logger') as mock_logger:
            _create_encoding_error_response(
                e=error,
                endpoint_name="test_endpoint",
                cache_key=""
            )

            # Verify logger.error was called
            mock_logger.error.assert_called_once()

            # Get the logged message
            log_call = mock_logger.error.call_args
            log_message = log_call[0][0]

            # Verify message is ASCII-safe
            assert "[Story 12.J.4]" in log_message
            assert "test_endpoint" in log_message
            assert "position" in log_message
            assert "U+" in log_message

            # Verify no raw Unicode/emoji in log message
            try:
                log_message.encode('ascii')
                is_ascii_safe = True
            except UnicodeEncodeError:
                is_ascii_safe = False
            assert is_ascii_safe, f"Log message contains non-ASCII characters: {log_message}"


# ═══════════════════════════════════════════════════════════════════════════════
# Request Cache Cleanup Tests
# ═══════════════════════════════════════════════════════════════════════════════


def test_encoding_error_cancels_request_cache():
    """
    Encoding error handling cleans up request cache for retry.

    [Source: docs/stories/story-12.H.5-backend-dedup.md#Task-3.7]
    """
    error = UnicodeEncodeError('gbk', 'test\U0001F525', 4, 5, 'illegal')

    with patch('app.api.v1.endpoints.agents.cancel_request') as mock_cancel:
        with patch('app.api.v1.endpoints.agents.logger'):
            _create_encoding_error_response(
                e=error,
                endpoint_name="decompose_basic",
                cache_key="test_cache_key_123"
            )

            # Verify cancel_request was called with the cache key
            mock_cancel.assert_called_once_with("test_cache_key_123")


def test_encoding_error_no_cancel_when_no_cache_key():
    """
    No cancel_request call when cache_key is empty.

    [Source: docs/stories/story-12.H.5-backend-dedup.md#Task-3.7]
    """
    error = UnicodeEncodeError('gbk', 'test\U0001F525', 4, 5, 'illegal')

    with patch('app.api.v1.endpoints.agents.cancel_request') as mock_cancel:
        with patch('app.api.v1.endpoints.agents.logger'):
            _create_encoding_error_response(
                e=error,
                endpoint_name="decompose_basic",
                cache_key=""
            )

            # Verify cancel_request was NOT called
            mock_cancel.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════════
# Edge Case Tests
# ═══════════════════════════════════════════════════════════════════════════════


def test_encoding_error_empty_object():
    """
    Handle edge case where error.object is empty.
    """
    error = UnicodeEncodeError('gbk', '', 0, 0, 'empty')

    with patch('app.api.v1.endpoints.agents.cancel_request'):
        with patch('app.api.v1.endpoints.agents.logger'):
            http_exception = _create_encoding_error_response(
                e=error,
                endpoint_name="test",
                cache_key=""
            )

    # Should not crash, just have position info
    assert "position 0" in http_exception.detail["diagnostic"]


def test_encoding_error_position_out_of_bounds():
    """
    Handle edge case where start position exceeds object length.
    """
    error = UnicodeEncodeError('gbk', 'short', 100, 101, 'out of bounds')

    with patch('app.api.v1.endpoints.agents.cancel_request'):
        with patch('app.api.v1.endpoints.agents.logger'):
            http_exception = _create_encoding_error_response(
                e=error,
                endpoint_name="test",
                cache_key=""
            )

    # Should not crash, just have position without char code
    assert "position 100" in http_exception.detail["diagnostic"]
    # U+ should NOT be in diagnostic since position is out of bounds
    assert "U+" not in http_exception.detail["diagnostic"]


# ═══════════════════════════════════════════════════════════════════════════════
# AC3: Endpoint Coverage Verification Tests
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_decompose_basic_has_encoding_error_handler():
    """
    AC3.1: decompose_basic endpoint has UnicodeEncodeError handler.

    [Source: docs/stories/story-12.J.4-unicode-exception-handling.md#Task-2.1]
    """
    # Verify function source contains UnicodeEncodeError handling
    import inspect

    from app.api.v1.endpoints.agents import decompose_basic
    source = inspect.getsource(decompose_basic)
    assert "except UnicodeEncodeError" in source


@pytest.mark.asyncio
async def test_decompose_deep_has_encoding_error_handler():
    """
    AC3.2: decompose_deep endpoint has UnicodeEncodeError handler.

    [Source: docs/stories/story-12.J.4-unicode-exception-handling.md#Task-2.2]
    """
    import inspect

    from app.api.v1.endpoints.agents import decompose_deep
    source = inspect.getsource(decompose_deep)
    assert "except UnicodeEncodeError" in source


@pytest.mark.asyncio
async def test_decompose_question_has_encoding_error_handler():
    """
    AC3.3: decompose_question endpoint has UnicodeEncodeError handler.

    [Source: docs/stories/story-12.J.4-unicode-exception-handling.md#Task-2.3]
    """
    import inspect

    from app.api.v1.endpoints.agents import decompose_question
    source = inspect.getsource(decompose_question)
    assert "except UnicodeEncodeError" in source


@pytest.mark.asyncio
async def test_call_explanation_has_encoding_error_handler():
    """
    AC3.4: _call_explanation helper has UnicodeEncodeError handler.

    This covers all 6 explain endpoints: oral, clarification, comparison,
    memory, four-level, example.

    [Source: docs/stories/story-12.J.4-unicode-exception-handling.md#Task-3]
    """
    import inspect

    from app.api.v1.endpoints.agents import _call_explanation
    source = inspect.getsource(_call_explanation)
    assert "except UnicodeEncodeError" in source


@pytest.mark.asyncio
async def test_score_understanding_has_encoding_error_handler():
    """
    AC3.5: score_understanding endpoint has UnicodeEncodeError handler.

    [Source: docs/stories/story-12.J.4-unicode-exception-handling.md#Task-4.1]
    """
    import inspect

    from app.api.v1.endpoints.agents import score_understanding
    source = inspect.getsource(score_understanding)
    assert "except UnicodeEncodeError" in source


@pytest.mark.asyncio
async def test_generate_verification_questions_has_encoding_error_handler():
    """
    AC3.6: generate_verification_questions endpoint has UnicodeEncodeError handler.

    [Source: docs/stories/story-12.J.4-unicode-exception-handling.md#Task-4.2]
    """
    import inspect

    from app.api.v1.endpoints.agents import generate_verification_questions
    source = inspect.getsource(generate_verification_questions)
    assert "except UnicodeEncodeError" in source
