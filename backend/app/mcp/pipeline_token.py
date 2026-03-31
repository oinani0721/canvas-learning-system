# Canvas Learning System - MCP Pipeline Token Manager
# Story 3.2: MCP Tool Exposure (AC-3)
#
# Cryptographic pipeline token system using HMAC-SHA256.
# Ensures tool call ordering: generate_question -> score_answer -> update_fsrs/update_bkt
#
# [Source: _bmad-output/implementation-artifacts/3-2-mcp-tool-exposure-backend-api.md#Task 3]
# [Source: _decisions/ADR-001-dialogue-engine.md#6-layer-defense]

import hashlib
import hmac
import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# Token validity window in seconds (default 5 minutes)
TOKEN_EXPIRY_SECONDS = 300

# Pipeline step ordering — defines valid transitions
PIPELINE_STEPS = {
    "generate_question": ["score_answer"],
    "score_answer": ["update_fsrs", "update_bkt"],
}


@dataclass
class PipelineTokenPayload:
    """Decoded payload from a pipeline token."""

    step_name: str
    session_id: str
    node_id: str
    timestamp: float
    expires_at: float
    question_id: Optional[str] = None


class PipelineTokenManager:
    """
    Generates and validates HMAC-SHA256 signed pipeline tokens.

    Tokens enforce the tool call ordering:
      generate_question -> score_answer -> update_fsrs/update_bkt

    Story 3.2 AC-3:
    - generate_question returns token_A
    - score_answer consumes token_A, returns token_B
    - update_fsrs/update_bkt consumes token_B
    - Skipping steps returns PIPELINE_TOKEN_INVALID
    """

    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize PipelineTokenManager.

        Args:
            secret_key: HMAC secret key. If not provided, reads from
                        MCP_PIPELINE_SECRET env var or generates a random one.
        """
        if secret_key:
            self._secret = secret_key.encode("utf-8")
        else:
            env_secret = os.environ.get("MCP_PIPELINE_SECRET", "")
            if env_secret:
                self._secret = env_secret.encode("utf-8")
            else:
                self._secret = os.urandom(32)
                logger.info(
                    "[Story 3.2] PipelineTokenManager: generated random secret "
                    "(set MCP_PIPELINE_SECRET env var for persistence)"
                )

    def generate_token(
        self,
        step_name: str,
        session_id: str,
        node_id: str,
        question_id: Optional[str] = None,
    ) -> str:
        """
        Generate a signed pipeline token after a step completes.

        Args:
            step_name: The pipeline step that just completed (e.g. "generate_question").
            session_id: The dialogue session identifier.
            node_id: The canvas node identifier.
            question_id: Optional question ID for traceability.

        Returns:
            Base64-encoded HMAC-signed token string.
        """
        now = time.time()
        payload = {
            "step": step_name,
            "sid": session_id,
            "nid": node_id,
            "ts": now,
            "exp": now + TOKEN_EXPIRY_SECONDS,
        }
        if question_id:
            payload["qid"] = question_id

        payload_bytes = json.dumps(
            payload, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
        signature = hmac.new(self._secret, payload_bytes, hashlib.sha256).hexdigest()

        # Token format: base64(payload).signature
        import base64

        encoded_payload = base64.urlsafe_b64encode(payload_bytes).decode("ascii")
        token = f"{encoded_payload}.{signature}"

        logger.debug(
            f"[Story 3.2] Pipeline token generated: step={step_name} session={session_id} node={node_id}"
        )
        return token

    def validate_token(
        self,
        token: str,
        expected_previous_step: str,
    ) -> PipelineTokenPayload:
        """
        Validate a pipeline token and check step ordering.

        Args:
            token: The token string to validate.
            expected_previous_step: The step that should have produced this token.

        Returns:
            PipelineTokenPayload with decoded data.

        Raises:
            PipelineTokenError: If token is invalid, expired, or wrong step.
        """
        import base64

        # Parse token format
        parts = token.split(".")
        if len(parts) != 2:
            raise PipelineTokenError(
                "PIPELINE_TOKEN_INVALID",
                "Malformed token: expected format payload.signature",
            )

        encoded_payload, provided_signature = parts

        # Decode payload
        try:
            payload_bytes = base64.urlsafe_b64decode(encoded_payload)
            payload = json.loads(payload_bytes)
        except Exception as exc:
            raise PipelineTokenError(
                "PIPELINE_TOKEN_INVALID",
                "Cannot decode token payload",
            ) from exc

        # Verify HMAC signature
        expected_signature = hmac.new(
            self._secret, payload_bytes, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(provided_signature, expected_signature):
            raise PipelineTokenError(
                "PIPELINE_TOKEN_INVALID",
                "Signature verification failed",
            )

        # Check expiry
        now = time.time()
        if now > payload.get("exp", 0):
            raise PipelineTokenError(
                "PIPELINE_TOKEN_EXPIRED",
                f"Token expired at {payload.get('exp', 0)}, current time {now}",
            )

        # Check step ordering
        step = payload.get("step", "")
        if step != expected_previous_step:
            raise PipelineTokenError(
                "PIPELINE_TOKEN_INVALID",
                f"Token from step '{step}' cannot be used here. Expected token from '{expected_previous_step}'.",
            )

        return PipelineTokenPayload(
            step_name=step,
            session_id=payload.get("sid", ""),
            node_id=payload.get("nid", ""),
            timestamp=payload.get("ts", 0.0),
            expires_at=payload.get("exp", 0.0),
            question_id=payload.get("qid"),
        )


class PipelineTokenError(Exception):
    """Error raised when pipeline token validation fails."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


# Singleton instance
_token_manager: Optional[PipelineTokenManager] = None


def get_pipeline_token_manager() -> PipelineTokenManager:
    """Get or create the singleton PipelineTokenManager."""
    global _token_manager
    if _token_manager is None:
        _token_manager = PipelineTokenManager()
    return _token_manager
