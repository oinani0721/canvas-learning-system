# Canvas Learning System - FastAPI Backend
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: application structure)
"""
Canvas Learning System FastAPI Backend Application Package.

This package provides the REST API backend for the Canvas Learning System,
an AI-assisted learning platform using the Feynman method with 14 specialized agents.
"""

# Load .env FIRST — before any submodule imports that use os.getenv()
# (e.g., agent_service.py reads ENABLE_REACT_AGENT at module level)
from pathlib import Path as _Path
from dotenv import load_dotenv as _load_dotenv
_load_dotenv(_Path(__file__).parent.parent / ".env")

__version__ = "1.0.0"
