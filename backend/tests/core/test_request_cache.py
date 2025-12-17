# Canvas Learning System - Request Cache Unit Tests
# Story 12.H.5: Backend Dedup - Unit Tests for RequestCache
# [Source: docs/stories/story-12.H.5-backend-dedup.md]
"""
Unit tests for request deduplication cache.

Tests the RequestCache class for thread-safety, TTL behavior,
key generation, and cleanup mechanisms.

[Source: docs/stories/story-12.H.5-backend-dedup.md#Task-4]
"""

import hashlib
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from app.core.request_cache import RequestCache, request_cache


class TestRequestCacheKeyGeneration:
    """Tests for cache key generation (AC3)."""

    def test_get_key_generates_md5_hash(self):
        """AC3: Cache key uses MD5 hash."""
        cache = RequestCache()
        key = cache.get_key("test.canvas", "node123", "oral")

        # Verify it's a valid MD5 hash (32 hex characters)
        assert len(key) == 32
        assert all(c in "0123456789abcdef" for c in key)

    def test_get_key_format_canvas_node_agent(self):
        """AC3: Key format is {canvas_name}:{node_id}:{agent_type}."""
        cache = RequestCache()

        # Manually compute expected hash
        raw = "test.canvas:node123:oral"
        expected = hashlib.md5(raw.encode()).hexdigest()

        key = cache.get_key("test.canvas", "node123", "oral")
        assert key == expected

    def test_get_key_same_inputs_same_key(self):
        """Same inputs should produce same key."""
        cache = RequestCache()
        key1 = cache.get_key("math.canvas", "abc123", "four-level")
        key2 = cache.get_key("math.canvas", "abc123", "four-level")
        assert key1 == key2

    def test_get_key_different_inputs_different_keys(self):
        """Different inputs should produce different keys."""
        cache = RequestCache()
        key1 = cache.get_key("math.canvas", "abc123", "oral")
        key2 = cache.get_key("math.canvas", "abc123", "four-level")
        key3 = cache.get_key("math.canvas", "def456", "oral")
        key4 = cache.get_key("physics.canvas", "abc123", "oral")

        # All keys should be unique
        keys = {key1, key2, key3, key4}
        assert len(keys) == 4

    def test_get_key_handles_special_characters(self):
        """Key generation handles special characters in inputs."""
        cache = RequestCache()
        # Chinese characters, spaces, special chars
        key = cache.get_key("数学笔记.canvas", "node with spaces", "explain_四层")

        # Should still produce valid MD5
        assert len(key) == 32
        assert all(c in "0123456789abcdef" for c in key)


class TestRequestCacheDuplicateDetection:
    """Tests for duplicate request detection (AC1, AC2)."""

    def test_is_duplicate_returns_false_for_new_request(self):
        """New request should not be detected as duplicate."""
        cache = RequestCache(ttl=60)
        cache.clear()

        key = cache.get_key("test.canvas", "node1", "oral")
        assert cache.is_duplicate(key) is False

    def test_is_duplicate_returns_true_for_in_progress_request(self):
        """In-progress request should be detected as duplicate (AC1)."""
        cache = RequestCache(ttl=60)
        cache.clear()

        key = cache.get_key("test.canvas", "node1", "oral")
        cache.mark_in_progress(key)

        assert cache.is_duplicate(key) is True

    def test_is_duplicate_returns_true_for_recently_completed_request(self):
        """Recently completed request should be detected as duplicate."""
        cache = RequestCache(ttl=60)
        cache.clear()

        key = cache.get_key("test.canvas", "node1", "oral")
        cache.mark_in_progress(key)
        cache.mark_completed(key)

        assert cache.is_duplicate(key) is True

    def test_is_duplicate_returns_false_after_ttl_expires(self):
        """Request should not be duplicate after TTL expires (AC5)."""
        cache = RequestCache(ttl=1)  # 1 second TTL
        cache.clear()

        key = cache.get_key("test.canvas", "node1", "oral")
        cache.mark_in_progress(key)
        cache.mark_completed(key)

        # Wait for TTL to expire
        time.sleep(1.5)

        assert cache.is_duplicate(key) is False


class TestRequestCacheLifecycle:
    """Tests for request lifecycle management."""

    def test_mark_in_progress_adds_entry(self):
        """mark_in_progress should add entry to cache."""
        cache = RequestCache(ttl=60)
        cache.clear()

        key = cache.get_key("test.canvas", "node1", "oral")
        assert len(cache) == 0

        cache.mark_in_progress(key)
        assert len(cache) == 1

    def test_mark_completed_keeps_entry_with_refreshed_ttl(self):
        """mark_completed should keep entry with refreshed TTL."""
        cache = RequestCache(ttl=60)
        cache.clear()

        key = cache.get_key("test.canvas", "node1", "oral")
        cache.mark_in_progress(key)

        # Get initial timestamp
        with cache._lock:
            initial_ts, _ = cache._cache[key]

        time.sleep(0.1)  # Small delay
        cache.mark_completed(key)

        # Entry should still exist with updated timestamp
        assert len(cache) == 1
        with cache._lock:
            new_ts, _ = cache._cache[key]
        assert new_ts >= initial_ts

    def test_remove_deletes_entry(self):
        """remove should delete entry from cache."""
        cache = RequestCache(ttl=60)
        cache.clear()

        key = cache.get_key("test.canvas", "node1", "oral")
        cache.mark_in_progress(key)
        assert len(cache) == 1

        cache.remove(key)
        assert len(cache) == 0

    def test_remove_allows_immediate_retry(self):
        """After remove, same request should not be duplicate."""
        cache = RequestCache(ttl=60)
        cache.clear()

        key = cache.get_key("test.canvas", "node1", "oral")
        cache.mark_in_progress(key)
        assert cache.is_duplicate(key) is True

        cache.remove(key)
        assert cache.is_duplicate(key) is False


class TestRequestCacheCleanup:
    """Tests for automatic cleanup of expired entries (AC5)."""

    def test_cleanup_removes_expired_entries(self):
        """Expired entries should be cleaned up."""
        cache = RequestCache(ttl=1, cleanup_interval=0.5)  # Short TTL and interval
        cache.clear()

        # Add multiple entries
        for i in range(5):
            key = cache.get_key("test.canvas", f"node{i}", "oral")
            cache.mark_in_progress(key)

        assert len(cache) == 5

        # Wait for TTL to expire
        time.sleep(1.5)

        # Trigger cleanup via is_duplicate
        cache.is_duplicate(cache.get_key("trigger", "cleanup", "now"))

        # All entries should be cleaned up
        # (The trigger key is not added because is_duplicate returned False)
        assert len(cache) == 0

    def test_cleanup_preserves_non_expired_entries(self):
        """Non-expired entries should be preserved during cleanup."""
        cache = RequestCache(ttl=60, cleanup_interval=0.1)
        cache.clear()

        # Add entry
        key = cache.get_key("test.canvas", "node1", "oral")
        cache.mark_in_progress(key)

        # Trigger cleanup
        time.sleep(0.2)
        cache.is_duplicate(cache.get_key("trigger", "cleanup", "now"))

        # Entry should still exist
        assert len(cache) == 1

    def test_clear_removes_all_entries(self):
        """clear should remove all entries."""
        cache = RequestCache(ttl=60)

        # Add multiple entries
        for i in range(10):
            key = cache.get_key("test.canvas", f"node{i}", "oral")
            cache.mark_in_progress(key)

        assert len(cache) == 10

        cache.clear()
        assert len(cache) == 0


class TestRequestCacheThreadSafety:
    """Tests for thread-safe operations."""

    def test_concurrent_is_duplicate_checks(self):
        """Concurrent is_duplicate calls should be thread-safe."""
        cache = RequestCache(ttl=60)
        cache.clear()

        key = cache.get_key("test.canvas", "node1", "oral")
        results = []

        def check_duplicate():
            result = cache.is_duplicate(key)
            results.append(result)

        # Run concurrent checks
        threads = [threading.Thread(target=check_duplicate) for _ in range(100)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All should return False (no entry exists)
        assert all(r is False for r in results)

    def test_concurrent_mark_in_progress(self):
        """Concurrent mark_in_progress calls should be thread-safe."""
        cache = RequestCache(ttl=60)
        cache.clear()

        def mark_progress(i):
            key = cache.get_key("test.canvas", f"node{i}", "oral")
            cache.mark_in_progress(key)

        # Run concurrent marks
        with ThreadPoolExecutor(max_workers=20) as executor:
            executor.map(mark_progress, range(100))

        # All entries should be added
        assert len(cache) == 100

    def test_concurrent_complete_and_remove(self):
        """Concurrent complete and remove operations should be thread-safe."""
        cache = RequestCache(ttl=60)
        cache.clear()

        # Pre-populate cache
        keys = []
        for i in range(50):
            key = cache.get_key("test.canvas", f"node{i}", "oral")
            cache.mark_in_progress(key)
            keys.append(key)

        def complete_or_remove(i):
            key = keys[i]
            if i % 2 == 0:
                cache.mark_completed(key)
            else:
                cache.remove(key)

        # Run concurrent operations
        with ThreadPoolExecutor(max_workers=20) as executor:
            executor.map(complete_or_remove, range(50))

        # Half should be completed (still in cache), half removed
        assert len(cache) == 25


class TestRequestCacheWithMetadata:
    """Tests for storing metadata with cache entries."""

    def test_mark_in_progress_with_data(self):
        """mark_in_progress can store additional metadata."""
        cache = RequestCache(ttl=60)
        cache.clear()

        key = cache.get_key("test.canvas", "node1", "oral")
        metadata = {"start_time": time.time(), "user": "test"}
        cache.mark_in_progress(key, data=metadata)

        with cache._lock:
            _, stored_data = cache._cache[key]
        assert stored_data == metadata


class TestRequestCacheGlobalInstance:
    """Tests for the global request_cache singleton."""

    def test_global_instance_exists(self):
        """Global request_cache instance should exist."""
        assert request_cache is not None
        assert isinstance(request_cache, RequestCache)

    def test_global_instance_default_ttl(self):
        """Global instance should have default TTL of 60 seconds."""
        assert request_cache.ttl == 60

    def test_global_instance_operations(self):
        """Global instance should support all operations."""
        request_cache.clear()

        key = request_cache.get_key("global.canvas", "node1", "test")
        assert request_cache.is_duplicate(key) is False

        request_cache.mark_in_progress(key)
        assert request_cache.is_duplicate(key) is True

        request_cache.remove(key)
        assert request_cache.is_duplicate(key) is False


class TestRequestCacheEdgeCases:
    """Tests for edge cases and error handling."""

    def test_remove_nonexistent_key(self):
        """Removing nonexistent key should not raise error."""
        cache = RequestCache(ttl=60)
        cache.clear()

        key = cache.get_key("test.canvas", "nonexistent", "oral")
        # Should not raise
        cache.remove(key)
        assert len(cache) == 0

    def test_mark_completed_nonexistent_key(self):
        """Completing nonexistent key should not raise error."""
        cache = RequestCache(ttl=60)
        cache.clear()

        key = cache.get_key("test.canvas", "nonexistent", "oral")
        # Should not raise (key doesn't exist, so nothing happens)
        cache.mark_completed(key)
        assert len(cache) == 0

    def test_empty_string_inputs(self):
        """Empty string inputs should be handled."""
        cache = RequestCache(ttl=60)
        key = cache.get_key("", "", "")

        # Should produce valid hash
        assert len(key) == 32

    def test_very_long_inputs(self):
        """Very long inputs should be handled via MD5 hash."""
        cache = RequestCache(ttl=60)
        long_name = "a" * 10000
        key = cache.get_key(long_name, long_name, long_name)

        # Should produce fixed-length hash
        assert len(key) == 32


class TestRequestCacheLogging:
    """Tests for logging behavior (AC4)."""

    def test_duplicate_detection_logs_warning(self):
        """Duplicate detection should log a warning (AC4)."""
        cache = RequestCache(ttl=60)
        cache.clear()

        key = cache.get_key("test.canvas", "node1", "oral")
        cache.mark_in_progress(key)

        with patch("app.core.request_cache.logger") as mock_logger:
            cache.is_duplicate(key)
            mock_logger.warning.assert_called_once()
            assert "Duplicate request detected" in str(mock_logger.warning.call_args)
