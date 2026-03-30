"""
Ping endpoint for the Canvas Learning System API.

Returns a simple {"status": "pong"} response for connectivity checks.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/ping")
def ping() -> dict:
    """Return a simple pong response for connectivity checks."""
    return {"status": "pong"}
