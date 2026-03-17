"""
RAGAS Faithfulness Check Node (Story 7.1)

Implements two-stage claim-level NLI faithfulness verification
following the RAGAS framework (EACL 2024).

Algorithm:
1. Claim Extraction: LLM extracts atomic claims from the generated answer.
2. NLI Verification: For each claim, LLM judges whether it is supported
   by the retrieved context (entailment check).
3. Score Calculation: Faithfulness = |supported claims| / |total claims|

Uses LiteLLM unified API for model-agnostic LLM calls.
Supports safe degradation when faithfulness falls below threshold.

References:
- RAGAS (EACL 2024): Faithfulness claim-level NLI evaluation framework
  https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/faithfulness/
- arXiv 2505.04847: Benchmarking LLM Faithfulness in RAG

[Source: _bmad-output/implementation-artifacts/7-1-llm-faithfulness-prompt-injection.md]
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import structlog

logger = logging.getLogger(__name__)
struct_logger = structlog.get_logger("faithfulness_check")

# ═══════════════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════════════

# Faithfulness threshold (AC #1: >= 0.85)
FAITHFULNESS_THRESHOLD_HIGH = float(
    os.getenv("FAITHFULNESS_THRESHOLD", "0.85")
)
# Below this triggers full degradation (AC #4)
FAITHFULNESS_THRESHOLD_LOW = float(
    os.getenv("FAITHFULNESS_THRESHOLD_LOW", "0.5")
)
# Model for faithfulness checks (defaults to project AI model)
FAITHFULNESS_MODEL = os.getenv(
    "FAITHFULNESS_MODEL",
    os.getenv("AI_MODEL_NAME", "gemini-2.0-flash-exp"),
)
# Provider prefix for LiteLLM (e.g., "gemini/", "openai/")
FAITHFULNESS_LITELLM_PREFIX = os.getenv("FAITHFULNESS_LITELLM_PREFIX", "")
# Enable/disable faithfulness checking
FAITHFULNESS_ENABLED = os.getenv("FAITHFULNESS_ENABLED", "true").lower() == "true"

# LiteLLM availability check
LITELLM_AVAILABLE = False
try:
    import litellm
    litellm.set_verbose = False  # Suppress litellm debug output
    LITELLM_AVAILABLE = True
except ImportError:
    logger.warning(
        "litellm not installed. Faithfulness check will be disabled. "
        "Install with: pip install litellm>=1.40.0"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Prompt Templates
# ═══════════════════════════════════════════════════════════════════════════════

CLAIM_EXTRACTION_SYSTEM = """You are a precise claim extraction system.
Your task is to extract all atomic claims (independent, verifiable factual statements)
from the given answer text.

Rules:
- Each claim must be a single, self-contained factual statement.
- Break compound sentences into individual claims.
- Opinions, hedging language, and meta-statements are NOT claims.
- Preserve the original meaning without adding information.
- Output ONLY valid JSON, no markdown fences."""

CLAIM_EXTRACTION_USER = """Extract all atomic claims from this answer.

Answer:
{answer}

Return a JSON object with this exact format:
{{"claims": ["claim 1", "claim 2", ...]}}

If there are no verifiable claims, return: {{"claims": []}}"""

NLI_VERIFICATION_SYSTEM = """You are a natural language inference (NLI) verification system.
For each claim, determine whether it is SUPPORTED or NOT_SUPPORTED by the given context.

Rules:
- A claim is SUPPORTED only if the context contains sufficient evidence to confirm it.
- A claim is NOT_SUPPORTED if the context contradicts it OR has no relevant information.
- Be strict: partial evidence is NOT_SUPPORTED.
- Output ONLY valid JSON, no markdown fences."""

NLI_VERIFICATION_USER = """Verify each claim against the provided context.

Context:
{context}

Claims to verify:
{claims_json}

For each claim, return a JSON object with this exact format:
{{"verdicts": [{{"claim": "the claim text", "verdict": "SUPPORTED or NOT_SUPPORTED", "reason": "brief reason"}}]}}"""


# ═══════════════════════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ClaimVerdict:
    """Verification result for a single claim."""
    claim: str
    verdict: str  # "SUPPORTED" or "NOT_SUPPORTED"
    reason: str = ""


@dataclass
class FaithfulnessResult:
    """Complete faithfulness check result."""
    score: float
    total_claims: int
    supported_claims: int
    claims: List[ClaimVerdict] = field(default_factory=list)
    degraded: bool = False
    degradation_reason: str = ""
    latency_ms: float = 0.0
    error: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Core Algorithm Implementation
# ═══════════════════════════════════════════════════════════════════════════════

_EMPTY_CLAIMS: List[str] = list()


def _get_litellm_model() -> str:
    """Build the LiteLLM model string with optional provider prefix."""
    model = FAITHFULNESS_MODEL
    prefix = FAITHFULNESS_LITELLM_PREFIX
    if prefix and not model.startswith(prefix):
        return f"{prefix}{model}"
    return model


def _parse_json_response(text: str) -> dict:
    """Parse JSON from LLM response, handling markdown code fences."""
    cleaned = text.strip()
    # Remove markdown code fences if present
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first line (```json or ```) and last line (```)
        lines = [line for line in lines if not line.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()
    return json.loads(cleaned)


def _make_unsupported_verdicts(
    claims: List[str], reason: str
) -> List[ClaimVerdict]:
    """Create NOT_SUPPORTED verdicts for all claims with a shared reason."""
    return [
        ClaimVerdict(claim=c, verdict="NOT_SUPPORTED", reason=reason)
        for c in claims
    ]


async def extract_claims(answer: str) -> List[str]:
    """
    Stage 1: Extract atomic claims from the LLM answer.

    Uses LiteLLM to call the configured model for claim decomposition.

    Args:
        answer: The LLM-generated answer text.

    Returns:
        List of atomic claim strings.

    Reference: RAGAS EACL 2024, Section 3.1 - Claim Decomposition
    """
    if not LITELLM_AVAILABLE:
        logger.warning("LiteLLM not available, skipping claim extraction")
        return list(_EMPTY_CLAIMS)

    if not answer or not answer.strip():
        return list(_EMPTY_CLAIMS)

    model = _get_litellm_model()
    user_prompt = CLAIM_EXTRACTION_USER.format(answer=answer)

    try:
        response = await litellm.acompletion(
            model=model,
            messages=[
                {"role": "system", "content": CLAIM_EXTRACTION_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
            max_tokens=2000,
            api_key=os.getenv("AI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
            api_base=os.getenv("AI_BASE_URL") or None,
        )

        content = response.choices[0].message.content
        parsed = _parse_json_response(content)
        claims = parsed.get("claims", list(_EMPTY_CLAIMS))

        logger.debug(
            f"[faithfulness] Extracted {len(claims)} claims from answer "
            f"({len(answer)} chars)"
        )
        return claims

    except json.JSONDecodeError as e:
        logger.error(f"[faithfulness] Failed to parse claim extraction JSON: {e}")
        return list(_EMPTY_CLAIMS)
    except Exception as e:
        logger.error(f"[faithfulness] Claim extraction LLM call failed: {e}")
        return list(_EMPTY_CLAIMS)


async def verify_claims_nli(
    claims: List[str], context: str
) -> List[ClaimVerdict]:
    """
    Stage 2: NLI verification of each claim against context.

    For each atomic claim, uses LLM to determine if the claim is
    entailed (SUPPORTED) or not entailed (NOT_SUPPORTED) by the context.

    Args:
        claims: List of atomic claim strings to verify.
        context: The retrieved context (concatenated document contents).

    Returns:
        List of ClaimVerdict objects with verdict for each claim.

    Reference: RAGAS EACL 2024, Section 3.2 - NLI Verification
    """
    if not LITELLM_AVAILABLE:
        logger.warning("LiteLLM not available, skipping NLI verification")
        return _make_unsupported_verdicts(claims, "LiteLLM unavailable")

    if not claims:
        return list()

    if not context or not context.strip():
        return _make_unsupported_verdicts(claims, "No context available")

    model = _get_litellm_model()
    claims_json = json.dumps(claims, ensure_ascii=False)
    user_prompt = NLI_VERIFICATION_USER.format(
        context=context, claims_json=claims_json
    )

    try:
        response = await litellm.acompletion(
            model=model,
            messages=[
                {"role": "system", "content": NLI_VERIFICATION_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
            max_tokens=4000,
            api_key=os.getenv("AI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
            api_base=os.getenv("AI_BASE_URL") or None,
        )

        content = response.choices[0].message.content
        parsed = _parse_json_response(content)
        verdicts_raw = parsed.get("verdicts", list())

        verdicts = []
        for v in verdicts_raw:
            verdicts.append(
                ClaimVerdict(
                    claim=v.get("claim", ""),
                    verdict=v.get("verdict", "NOT_SUPPORTED").upper(),
                    reason=v.get("reason", ""),
                )
            )

        # Ensure we have a verdict for every claim (handle partial responses)
        verified_claims = {v.claim for v in verdicts}
        for claim in claims:
            if claim not in verified_claims:
                verdicts.append(
                    ClaimVerdict(
                        claim=claim,
                        verdict="NOT_SUPPORTED",
                        reason="No verdict returned by NLI model",
                    )
                )

        logger.debug(
            f"[faithfulness] NLI verified {len(verdicts)} claims, "
            f"{sum(1 for v in verdicts if v.verdict == 'SUPPORTED')} supported"
        )
        return verdicts

    except json.JSONDecodeError as e:
        logger.error(f"[faithfulness] Failed to parse NLI verification JSON: {e}")
        return _make_unsupported_verdicts(claims, f"JSON parse error: {e}")
    except Exception as e:
        logger.error(f"[faithfulness] NLI verification LLM call failed: {e}")
        return _make_unsupported_verdicts(claims, f"LLM error: {e}")


def calculate_faithfulness(verdicts: List[ClaimVerdict]) -> float:
    """
    Calculate faithfulness score.

    Faithfulness = |supported claims| / |total claims|

    Args:
        verdicts: List of claim verdicts from NLI verification.

    Returns:
        Faithfulness score between 0.0 and 1.0.
        Returns 1.0 if there are no claims (vacuous truth).

    Reference: RAGAS EACL 2024, Equation 1
    """
    if not verdicts:
        return 1.0  # No claims = nothing to be unfaithful about

    total = len(verdicts)
    supported = sum(1 for v in verdicts if v.verdict == "SUPPORTED")
    return supported / total


def apply_degradation(
    score: float,
    result: FaithfulnessResult,
) -> FaithfulnessResult:
    """
    Apply safe degradation based on faithfulness score thresholds.

    Degradation strategy (aligned with FR-RET-11):
    - score >= 0.85: PASS, no degradation
    - 0.5 <= score < 0.85: LOW_CONFIDENCE warning
    - score < 0.5: FULL_DEGRADATION, replace answer

    Args:
        score: Faithfulness score.
        result: FaithfulnessResult to update.

    Returns:
        Updated FaithfulnessResult with degradation info.
    """
    if score >= FAITHFULNESS_THRESHOLD_HIGH:
        result.degraded = False
        result.degradation_reason = ""
    elif score >= FAITHFULNESS_THRESHOLD_LOW:
        result.degraded = True
        result.degradation_reason = (
            "The retrieved information may not fully support this answer. "
            "Some claims could not be verified against the source material."
        )
    else:
        result.degraded = True
        result.degradation_reason = (
            "The retrieved information is insufficient to reliably answer this question. "
            "Please refer to your original study materials for accurate information."
        )
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# LangGraph Node Function
# ═══════════════════════════════════════════════════════════════════════════════

async def faithfulness_check(state: dict) -> dict:
    """
    LangGraph node: RAGAS Faithfulness Check.

    Performs two-stage claim-level NLI faithfulness verification on the
    LLM-generated answer against retrieved context.

    Position in RAG pipeline:
        retriever -> reranker -> check_quality -> faithfulness_check -> END

    Args:
        state: CanvasRAGState dict containing:
            - messages: Conversation messages (last message = LLM answer)
            - reranked_results: Retrieved and reranked context documents

    Returns:
        State updates:
            - faithfulness_score: float (0.0-1.0)
            - faithfulness_details: dict with claim-level evidence
            - faithfulness_degraded: bool

    AC #1: Faithfulness >= 0.85
    AC #4: Safe degradation when score < 0.85
    """
    start_time = time.perf_counter()

    logger.debug("[faithfulness_check] START")

    # ── Check if faithfulness checking is enabled ──
    if not FAITHFULNESS_ENABLED:
        logger.info("[faithfulness_check] Disabled via FAITHFULNESS_ENABLED=false")
        return {
            "faithfulness_score": None,
            "faithfulness_details": {"status": "disabled"},
            "faithfulness_degraded": False,
        }

    if not LITELLM_AVAILABLE:
        logger.warning(
            "[faithfulness_check] LiteLLM not available, skipping check"
        )
        return {
            "faithfulness_score": None,
            "faithfulness_details": {"status": "litellm_unavailable"},
            "faithfulness_degraded": False,
        }

    # ── Extract answer from messages ──
    messages = state.get("messages", list())
    answer = ""
    if messages:
        last_msg = messages[-1]
        if isinstance(last_msg, dict):
            answer = last_msg.get("content", "")
        else:
            answer = getattr(last_msg, "content", "")

    if not answer or not answer.strip():
        logger.debug("[faithfulness_check] No answer to check, skipping")
        return {
            "faithfulness_score": 1.0,
            "faithfulness_details": {"status": "no_answer"},
            "faithfulness_degraded": False,
        }

    # ── Build context from reranked results ──
    reranked = state.get("reranked_results", list())
    context_parts = []
    for doc in reranked:
        content = doc.get("content", "") if isinstance(doc, dict) else ""
        if content.strip():
            context_parts.append(content)

    context = "\n\n---\n\n".join(context_parts)

    if not context.strip():
        logger.debug("[faithfulness_check] No context available, marking as degraded")
        latency = (time.perf_counter() - start_time) * 1000
        result = FaithfulnessResult(
            score=0.0,
            total_claims=0,
            supported_claims=0,
            degraded=True,
            degradation_reason=(
                "No source material was retrieved to verify the answer. "
                "The response may not be reliable."
            ),
            latency_ms=latency,
        )
        _log_faithfulness_result(result, answer)
        return {
            "faithfulness_score": result.score,
            "faithfulness_details": _result_to_details(result),
            "faithfulness_degraded": result.degraded,
        }

    # ── Stage 1: Claim Extraction ──
    logger.debug(
        f"[faithfulness_check] Stage 1: Extracting claims from answer "
        f"({len(answer)} chars)"
    )
    claims = await extract_claims(answer)

    if not claims:
        logger.debug("[faithfulness_check] No claims extracted, score = 1.0")
        latency = (time.perf_counter() - start_time) * 1000
        result = FaithfulnessResult(
            score=1.0,
            total_claims=0,
            supported_claims=0,
            latency_ms=latency,
        )
        _log_faithfulness_result(result, answer)
        return {
            "faithfulness_score": 1.0,
            "faithfulness_details": _result_to_details(result),
            "faithfulness_degraded": False,
        }

    # ── Stage 2: NLI Verification ──
    logger.debug(
        f"[faithfulness_check] Stage 2: NLI verifying {len(claims)} claims "
        f"against {len(context_parts)} context docs"
    )
    verdicts = await verify_claims_nli(claims, context)

    # ── Stage 3: Score Calculation ──
    score = calculate_faithfulness(verdicts)
    supported = sum(1 for v in verdicts if v.verdict == "SUPPORTED")

    latency = (time.perf_counter() - start_time) * 1000

    result = FaithfulnessResult(
        score=score,
        total_claims=len(verdicts),
        supported_claims=supported,
        claims=verdicts,
        latency_ms=latency,
    )

    # ── Apply Degradation ──
    result = apply_degradation(score, result)

    logger.info(
        f"[faithfulness_check] END - score={score:.3f}, "
        f"claims={len(verdicts)}, supported={supported}, "
        f"degraded={result.degraded}, latency={latency:.1f}ms"
    )

    _log_faithfulness_result(result, answer)

    return {
        "faithfulness_score": result.score,
        "faithfulness_details": _result_to_details(result),
        "faithfulness_degraded": result.degraded,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Logging Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _result_to_details(result: FaithfulnessResult) -> Dict[str, Any]:
    """Convert FaithfulnessResult to a serializable dict for state storage."""
    return {
        "score": result.score,
        "total_claims": result.total_claims,
        "supported_claims": result.supported_claims,
        "claims": [
            {
                "claim": v.claim,
                "verdict": v.verdict,
                "reason": v.reason,
            }
            for v in result.claims
        ],
        "degraded": result.degraded,
        "degradation_reason": result.degradation_reason,
        "latency_ms": round(result.latency_ms, 2),
        "error": result.error,
    }


def _log_faithfulness_result(result: FaithfulnessResult, answer: str) -> None:
    """Emit structured log for faithfulness check (AC #6)."""
    try:
        struct_logger.info(
            "faithfulness_check_completed",
            check_type="faithfulness",
            score=result.score,
            total_claims=result.total_claims,
            supported_claims=result.supported_claims,
            degraded=result.degraded,
            degradation_reason=result.degradation_reason,
            latency_ms=round(result.latency_ms, 2),
            answer_length=len(answer),
            error=result.error,
        )
    except Exception as e:
        logger.error(f"[faithfulness_check] Failed to emit structured log: {e}")
