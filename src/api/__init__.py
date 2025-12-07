# -*- coding: utf-8 -*-
"""
Canvas Learning System FastAPI Backend Package

Provides the FastAPI application for Canvas operations, Agent invocation,
and Ebbinghaus review system.

Story 15.6: API Documentation and Testing Framework
"""

from .config import get_settings, settings
from .main import app, create_app

__all__ = ["app", "create_app", "settings", "get_settings"]
