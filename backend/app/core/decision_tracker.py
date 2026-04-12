"""Decision ID tracker for business logic traceability.

Generates DECN-{uuid8} IDs at key decision points and logs them
via structlog for correlation with request_id.

Usage in service functions:
    from app.core.decision_tracker import log_decision

    log_decision(
        function="determine_mastery_level",
        input_summary={"node_id": node_id, "score": score},
        output="Developing",
        reason="score 0.45 < proficient_threshold 0.6",
        request_id=request_id,  # optional
    )
"""

import json
import logging
import uuid
from typing import Any, Dict, Optional

import structlog

logger = logging.getLogger(__name__)


def generate_decision_id() -> str:
    """Generate a unique decision ID in DECN-{8-hex} format."""
    return f"DECN-{uuid.uuid4().hex[:8].upper()}"


def log_decision(
    function: str,
    input_summary: Dict[str, Any],
    output: Any,
    reason: str,
    request_id: Optional[str] = None,
    story_id: Optional[str] = None,
) -> str:
    """Log a business decision with a unique ID. Returns the decision_id.

    If request_id is not provided, auto-reads from structlog contextvars
    (set by MetricsMiddleware for every HTTP request).
    story_id is optional — set by contextvars when running within a BMAD Story scope.
    """
    if request_id is None:
        ctx = structlog.contextvars.get_contextvars()
        request_id = ctx.get("request_id", "unknown")

    if story_id is None:
        ctx = structlog.contextvars.get_contextvars()
        story_id = ctx.get("current_story_id")

    decision_id = generate_decision_id()
    extra = {
        "decision_id": decision_id,
        "function": function,
        "input": json.dumps(input_summary, default=str),
        "output": str(output),
        "reason": reason,
        "request_id": request_id,
    }
    if story_id:
        extra["story_id"] = story_id
    logger.info("decision_recorded", extra=extra)
    return decision_id
