# Canvas Learning System - Core Module
# Story 12.H.5: Backend Dedup - Request Cache Infrastructure
"""
Core infrastructure modules for Canvas Learning System.

This package contains shared infrastructure components:
- request_cache: Request deduplication cache (Story 12.H.5)
"""

from app.core.request_cache import RequestCache, request_cache

__all__ = ["RequestCache", "request_cache"]
