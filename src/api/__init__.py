# -*- coding: utf-8 -*-
"""
Canvas Learning System FastAPI Backend Package

Provides the FastAPI application for Canvas operations, Agent invocation,
and Ebbinghaus review system.

Story 15.6: API Documentation and Testing Framework
"""

from .main import app, create_app
from .config import settings, get_settings

__all__ = ["app", "create_app", "settings", "get_settings"]
