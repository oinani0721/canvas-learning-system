# Canvas Learning System - Error Aggregator Unit Tests
# Story 7.4: 出题难度匹配与提取质量验证
# [Source: _bmad-output/implementation-artifacts/7-4-difficulty-matching-extraction-validation.md]
"""
Unit tests for ErrorAggregator:
  - Error classification accuracy (4 categories + uncategorized)
  - Time-window aggregation (24h / 7d / 30d)
  - Exception hierarchy traversal

[Source: Story 7.4 Task 8.3]
"""

import pytest
from app.services.error_aggregator import ErrorAggregator, classify_error

# ═══════════════════════════════════════════════════════════════════════════════
# Error Classification
# ═══════════════════════════════════════════════════════════════════════════════


class TestClassifyError:
    """Test error classification by exception type."""

    def test_value_error_is_algorithm(self):
        assert classify_error(ValueError("bad value")) == "algorithm_error"

    def test_key_error_is_algorithm(self):
        assert classify_error(KeyError("missing_key")) == "algorithm_error"

    def test_index_error_is_algorithm(self):
        assert classify_error(IndexError("out of range")) == "algorithm_error"

    def test_zero_division_is_algorithm(self):
        assert classify_error(ZeroDivisionError()) == "algorithm_error"

    def test_connection_error_is_network(self):
        assert classify_error(ConnectionError("refused")) == "network_error"

    def test_timeout_error_is_network(self):
        assert classify_error(TimeoutError("timed out")) == "network_error"

    def test_connection_refused_is_network(self):
        assert classify_error(ConnectionRefusedError()) == "network_error"

    def test_connection_reset_is_network(self):
        assert classify_error(ConnectionResetError()) == "network_error"

    def test_unknown_error_is_uncategorized(self):
        class CustomWeirdError(Exception):
            pass

        assert classify_error(CustomWeirdError("oops")) == "uncategorized"

    def test_parent_class_match(self):
        """Subclass of ValueError should match via MRO traversal."""

        class SpecialValueError(ValueError):
            pass

        assert classify_error(SpecialValueError("oops")) == "algorithm_error"

    def test_arithmetic_error_is_algorithm(self):
        assert classify_error(ArithmeticError("bad math")) == "algorithm_error"

    def test_broken_pipe_is_network(self):
        assert classify_error(BrokenPipeError()) == "network_error"


class TestClassifyErrorByModule:
    """Test classification fallback by module origin."""

    def test_module_hint_sqlite(self):
        """Exception from sqlite3 module classified as data_error."""

        class FakeSqliteError(Exception):
            pass

        FakeSqliteError.__module__ = "sqlite3.dbapi2"
        assert classify_error(FakeSqliteError("db error")) == "data_error"

    def test_module_hint_httpx(self):
        """Exception from httpx module classified as network_error."""

        class FakeHttpxError(Exception):
            pass

        FakeHttpxError.__module__ = "httpx._exceptions"
        assert classify_error(FakeHttpxError("conn error")) == "network_error"

    def test_module_hint_litellm(self):
        """Exception from litellm module classified as llm_error."""

        class FakeLiteLLMError(Exception):
            pass

        FakeLiteLLMError.__module__ = "litellm.exceptions"
        assert classify_error(FakeLiteLLMError("api error")) == "llm_error"


# ═══════════════════════════════════════════════════════════════════════════════
# Error Recording & Aggregation
# ═══════════════════════════════════════════════════════════════════════════════


class TestErrorAggregator:
    @pytest.mark.asyncio
    async def test_record_and_aggregate(self, tmp_path):
        db_path = str(tmp_path / "test_errors.db")
        agg = ErrorAggregator(db_path)

        # Record various errors
        cat1 = await agg.record_error(ValueError("bad"))
        assert cat1 == "algorithm_error"

        cat2 = await agg.record_error(ConnectionError("refused"))
        assert cat2 == "network_error"

        cat3 = await agg.record_error(TimeoutError("slow"))
        assert cat3 == "network_error"

        # Get aggregation
        result = await agg.get_aggregation()

        # All errors within 24h
        assert result.last_24h.algorithm_errors == 1
        assert result.last_24h.network_errors == 2
        assert result.last_24h.llm_errors == 0
        assert result.last_24h.data_errors == 0

        # Also within 7d and 30d
        assert result.last_7d.algorithm_errors == 1
        assert result.last_30d.network_errors == 2

    @pytest.mark.asyncio
    async def test_empty_aggregation(self, tmp_path):
        db_path = str(tmp_path / "test_empty.db")
        agg = ErrorAggregator(db_path)

        result = await agg.get_aggregation()
        assert result.last_24h.llm_errors == 0
        assert result.last_24h.network_errors == 0
        assert result.last_24h.algorithm_errors == 0
        assert result.last_24h.data_errors == 0
        assert result.last_24h.uncategorized == 0

    @pytest.mark.asyncio
    async def test_multiple_same_category(self, tmp_path):
        db_path = str(tmp_path / "test_multi.db")
        agg = ErrorAggregator(db_path)

        for _ in range(10):
            await agg.record_error(ValueError("bad"))

        result = await agg.get_aggregation()
        assert result.last_24h.algorithm_errors == 10
