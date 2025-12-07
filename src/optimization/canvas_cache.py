# Canvas Learning System - Canvas File Cache
# ✅ Verified from Architecture Doc (performance-monitoring-architecture.md:346-360)
# ✅ Verified from ADR-007 (ADR-007-CACHING-STRATEGY-TIERED.md:103-129)
# [Source: docs/stories/17.4.story.md - Task 1]
"""
Canvas file read optimization using orjson and lru_cache.

Features:
- orjson for fast JSON parsing (30% CPU reduction)
- lru_cache for in-memory caching (80%+ hit rate target)
- Automatic cache invalidation on file modification
- Cache statistics for monitoring

[Source: docs/architecture/performance-monitoring-architecture.md:346-360]
[Source: docs/architecture/decisions/ADR-007-CACHING-STRATEGY-TIERED.md:103-129]
"""

import json
import os
import threading
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Dict, Optional

import structlog

# ✅ Try orjson for performance, fallback to json
try:
    import orjson
    HAS_ORJSON = True
except ImportError:
    HAS_ORJSON = False

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Cache Configuration
# [Source: docs/architecture/decisions/ADR-007-CACHING-STRATEGY-TIERED.md:103-129]
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CacheConfig:
    """Canvas cache configuration.

    [Source: docs/architecture/decisions/ADR-007-CACHING-STRATEGY-TIERED.md:103-129]
    """

    # Canvas file cache
    canvas_maxsize: int = 100
    canvas_ttl: int = 3600  # 1 hour

    # Enable/disable optimization (feature flag)
    enabled: bool = True

    # Use orjson if available
    use_orjson: bool = True


# Global configuration
_config = CacheConfig()

# Cache statistics
@dataclass
class CacheStats:
    """Cache hit/miss statistics."""

    hits: int = 0
    misses: int = 0
    invalidations: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total

    def record_hit(self):
        """Record a cache hit."""
        with self._lock:
            self.hits += 1

    def record_miss(self):
        """Record a cache miss."""
        with self._lock:
            self.misses += 1

    def record_invalidation(self):
        """Record a cache invalidation."""
        with self._lock:
            self.invalidations += 1

    def reset(self):
        """Reset statistics."""
        with self._lock:
            self.hits = 0
            self.misses = 0
            self.invalidations = 0


_stats = CacheStats()


# ═══════════════════════════════════════════════════════════════════════════════
# Canvas Read with Cache
# [Source: docs/architecture/performance-monitoring-architecture.md:346-360]
# ═══════════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=100)
def read_canvas_cached(canvas_path: str, mtime: float) -> Dict[str, Any]:
    """Read Canvas file with caching.

    Uses file modification time (mtime) as part of cache key for automatic
    invalidation when file changes.

    [Source: docs/architecture/performance-monitoring-architecture.md:346-360]

    Args:
        canvas_path: Path to Canvas file
        mtime: File modification timestamp (used for cache invalidation)

    Returns:
        dict: Canvas JSON data

    Raises:
        FileNotFoundError: If canvas file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    logger.debug(
        "canvas_cache.read",
        path=canvas_path,
        mtime=mtime,
        use_orjson=HAS_ORJSON and _config.use_orjson,
    )

    with open(canvas_path, 'rb') as f:
        content = f.read()

    # ✅ Use orjson if available and enabled
    if HAS_ORJSON and _config.use_orjson:
        return orjson.loads(content)
    else:
        return json.loads(content.decode('utf-8'))


def read_canvas(canvas_path: str) -> Dict[str, Any]:
    """Read Canvas file with automatic caching.

    This is the main entry point for reading Canvas files. It automatically:
    - Checks file modification time for cache invalidation
    - Uses orjson for fast parsing if available
    - Records cache statistics

    [Source: docs/architecture/performance-monitoring-architecture.md:346-360]

    Args:
        canvas_path: Path to Canvas file

    Returns:
        dict: Canvas JSON data

    Example:
        >>> canvas_data = read_canvas("/path/to/canvas.canvas")
        >>> nodes = canvas_data.get("nodes", [])
    """
    if not _config.enabled:
        # Optimization disabled, read directly
        return _read_canvas_direct(canvas_path)

    # Get file modification time for cache key
    mtime = os.path.getmtime(canvas_path)

    # Check if this is a cache hit or miss
    cache_info = read_canvas_cached.cache_info()
    hits_before = cache_info.hits

    # Read with caching
    result = read_canvas_cached(canvas_path, mtime)

    # Record statistics
    cache_info_after = read_canvas_cached.cache_info()
    if cache_info_after.hits > hits_before:
        _stats.record_hit()
        logger.debug("canvas_cache.hit", path=canvas_path)
    else:
        _stats.record_miss()
        logger.debug("canvas_cache.miss", path=canvas_path)

    return result


def _read_canvas_direct(canvas_path: str) -> Dict[str, Any]:
    """Read Canvas file directly without caching.

    Used when optimization is disabled or as fallback.

    Args:
        canvas_path: Path to Canvas file

    Returns:
        dict: Canvas JSON data
    """
    with open(canvas_path, 'rb') as f:
        content = f.read()

    if HAS_ORJSON and _config.use_orjson:
        return orjson.loads(content)
    else:
        return json.loads(content.decode('utf-8'))


# ═══════════════════════════════════════════════════════════════════════════════
# Cache Management
# ═══════════════════════════════════════════════════════════════════════════════

def clear_canvas_cache():
    """Clear the canvas file cache.

    Should be called when Canvas files are modified externally
    or when memory needs to be freed.
    """
    read_canvas_cached.cache_clear()
    _stats.record_invalidation()
    logger.info("canvas_cache.cleared")


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics.

    Returns:
        dict: Cache statistics including hits, misses, hit_rate
    """
    cache_info = read_canvas_cached.cache_info()
    return {
        "hits": _stats.hits,
        "misses": _stats.misses,
        "hit_rate": _stats.hit_rate,
        "invalidations": _stats.invalidations,
        "cache_size": cache_info.currsize,
        "cache_maxsize": cache_info.maxsize,
        "orjson_available": HAS_ORJSON,
        "orjson_enabled": _config.use_orjson,
        "optimization_enabled": _config.enabled,
    }


def configure_cache(
    maxsize: Optional[int] = None,
    enabled: Optional[bool] = None,
    use_orjson: Optional[bool] = None,
):
    """Configure cache settings.

    Note: Changes to maxsize require cache to be cleared.

    Args:
        maxsize: Maximum cache size (requires restart to take effect)
        enabled: Enable/disable caching
        use_orjson: Use orjson for JSON parsing
    """
    global _config

    if enabled is not None:
        _config.enabled = enabled
        logger.info("canvas_cache.config.enabled", enabled=enabled)

    if use_orjson is not None:
        _config.use_orjson = use_orjson
        logger.info("canvas_cache.config.use_orjson", use_orjson=use_orjson)

    if maxsize is not None:
        _config.canvas_maxsize = maxsize
        logger.warning(
            "canvas_cache.config.maxsize",
            maxsize=maxsize,
            note="Requires cache clear and restart to take effect",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# JSON Write Optimization
# [Source: docs/architecture/performance-monitoring-architecture.md:346-360]
# ═══════════════════════════════════════════════════════════════════════════════

def write_canvas_json(canvas_path: str, data: Dict[str, Any], pretty: bool = True):
    """Write Canvas data to file with optimization.

    Uses orjson for fast serialization if available.
    Clears cache entry for the file after write.

    Args:
        canvas_path: Path to write Canvas file
        data: Canvas data dictionary
        pretty: Format JSON with indentation (default True)
    """
    if HAS_ORJSON and _config.use_orjson:
        options = orjson.OPT_INDENT_2 if pretty else 0
        content = orjson.dumps(data, option=options)
    else:
        indent = 2 if pretty else None
        content = json.dumps(data, indent=indent, ensure_ascii=False).encode('utf-8')

    with open(canvas_path, 'wb') as f:
        f.write(content)

    # Invalidate cache for this file
    clear_canvas_cache()
    logger.debug("canvas_cache.write", path=canvas_path, size=len(content))
