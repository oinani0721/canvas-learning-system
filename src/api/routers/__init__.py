"""
API Routers Package for Canvas Learning System API

Exports all routers for registration in main application.
"""

from .health import router as health_router
from .canvas import router as canvas_router
from .agents import router as agents_router
from .review import router as review_router

__all__ = [
    "health_router",
    "canvas_router",
    "agents_router",
    "review_router",
]
