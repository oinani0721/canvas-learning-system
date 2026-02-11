# Canvas Learning System - Agent Routing Engine
# Story 33.5: Agent Routing Engine
# [Source: docs/stories/33.5.story.md]
"""
Content-based Agent Routing Engine for batch processing.

This module implements intelligent agent routing based on content pattern analysis.
It analyzes node text to recommend the most suitable agent with confidence scoring.

Key Features:
- Content pattern matching for 6 agent types
- Confidence scoring with threshold (>= 0.7)
- Manual override support
- Integration with 14-agent mapping from agent_memory_mapping.py

Routing Matrix (from Story 33.5 AC1):
| Pattern (Chinese)    | Pattern (English)      | Recommended Agent     |
|----------------------|------------------------|-----------------------|
| "什么是X", "X是什么"  | "What is X"           | oral-explanation      |
| "A和B区别", "A vs B"  | "Difference A and B"  | comparison-table      |
| "如何理解X"          | "How to understand X"  | clarification-path    |
| "举例说明X"          | "Give example of X"    | example-teaching      |
| "记忆X", "记住X"     | "Memorize X"           | memory-anchor         |
| "深度剖析X"          | "Deep analysis of X"   | deep-decomposition    |

[Source: specs/api/parallel-api.openapi.yml#L301-L313]
[Source: specs/data/agent-type.schema.json#L14-L29]
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from app.core.agent_memory_mapping import AGENT_MEMORY_MAPPING, ALL_AGENT_NAMES
from app.models.agent_routing_models import (
    BatchRoutingRequest,
    BatchRoutingResponse,
    RoutingRequest,
    RoutingResult,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Routing Pattern Configuration (Task 5)
# ═══════════════════════════════════════════════════════════════════════════════

# Pattern version for A/B testing
PATTERN_VERSION = "1.0.0"

# Weight for catch-all agent (oral-explanation) — slightly lower to prefer specific matches
ORAL_EXPLANATION_WEIGHT = 0.9

# Content pattern map: agent_name -> pattern configuration
# Patterns are ordered by specificity (more specific first)
CONTENT_PATTERN_MAP: Dict[str, Dict[str, Any]] = {
    "comparison-table": {
        "patterns": [
            # Chinese patterns (more specific first)
            r".*和.*的?区别.*",       # "A和B的区别"
            r".*区别.*",              # "...区别..."
            r".*对比.*",              # "...对比..."
            r".*异同.*",              # "...异同..."
            r".*比较.*和.*",          # "比较A和B"
            # English patterns
            r".*\bvs\.?\s+.*",        # "A vs B"
            r".*difference\s+between.*",  # "difference between A and B"
            r".*compare.*and.*",      # "compare A and B"
        ],
        "weight": 1.0,
        "priority": 1,  # Higher priority for specific patterns
        "description": "Comparison table - for comparing similar/confusing concepts"
    },
    "deep-decomposition": {
        "patterns": [
            # Chinese patterns
            r"深度剖析.*",            # "深度剖析X"
            r".*深度剖析.*",          # "...深度剖析..."
            r"深入分析.*",            # "深入分析X"
            r".*深入分析.*",          # "...深入分析..."
            r"详细分析.*",            # "详细分析X"
            # English patterns
            r".*deep\s+analysis.*",   # "deep analysis of X"
            r".*in-depth.*analysis.*",  # "in-depth analysis"
        ],
        "weight": 1.0,
        "priority": 2,
        "description": "Deep decomposition - for complex analytical breakdown"
    },
    "memory-anchor": {
        "patterns": [
            # Chinese patterns
            r"记忆.*",                # "记忆X"
            r".*记忆.*",              # "...记忆..."
            r"记住.*",                # "记住X"
            r".*记住.*",              # "...记住..."
            r"背诵.*",                # "背诵X"
            r".*背诵.*",              # "...背诵..."
            r"怎么记.*",              # "怎么记X"
            # English patterns
            r".*memorize.*",          # "memorize X"
            r".*remember.*",          # "remember X"
        ],
        "weight": 1.0,
        "priority": 3,
        "description": "Memory anchor - for creating mnemonics and analogies"
    },
    "example-teaching": {
        "patterns": [
            # Chinese patterns
            r"举例说明.*",            # "举例说明X"
            r".*举例.*",              # "...举例..."
            r"例子.*",                # "例子..."
            r".*例子.*",              # "...例子..."
            r"举个例子.*",            # "举个例子..."
            r".*实例.*",              # "...实例..."
            # English patterns
            r".*give.*example.*",     # "give example of X"
            r".*example.*of.*",       # "example of X"
            r".*for\s+example.*",     # "for example"
        ],
        "weight": 1.0,
        "priority": 4,
        "description": "Example teaching - for concrete examples and problem-solving"
    },
    "clarification-path": {
        "patterns": [
            # Chinese patterns
            r"如何理解.*",            # "如何理解X"
            r"怎么理解.*",            # "怎么理解X"
            r".*怎么理解.*",          # "...怎么理解..."
            r".*如何理解.*",          # "...如何理解..."
            r"理解.*",                # "理解X"
            r"解释.*怎么.*",          # "解释...怎么..."
            # English patterns
            r".*how\s+to\s+understand.*",  # "how to understand X"
            r".*explain.*how.*",      # "explain how"
        ],
        "weight": 1.0,
        "priority": 5,
        "description": "Clarification path - systematic 1500+ word explanation"
    },
    "oral-explanation": {
        "patterns": [
            # Chinese patterns (general definition questions)
            r"什么是.*",              # "什么是X"
            r".*是什么.*",            # "X是什么"
            r"定义.*",                # "定义X"
            r".*定义.*",              # "...定义..."
            r"解释.*",                # "解释X"
            r".*解释.*什么.*",        # "...解释...什么..."
            r".*是.*吗.*",            # "X是...吗"
            # English patterns
            r".*what\s+is.*",         # "what is X"
            r".*define.*",            # "define X"
            r".*explain.*what.*",     # "explain what"
        ],
        "weight": ORAL_EXPLANATION_WEIGHT,
        "priority": 6,  # Lower priority - used as default fallback
        "description": "Oral explanation - professor-style verbal explanation"
    },
}

# Default fallback agent when no patterns match or confidence is low
DEFAULT_FALLBACK_AGENT = "oral-explanation"

# ═══════════════════════════════════════════════════════════════════════════════
# Confidence Thresholds & Scoring Constants
# [Source: docs/stories/33.12.story.md — extracted from inline magic numbers]
# ═══════════════════════════════════════════════════════════════════════════════

# --- Routing decision thresholds (AC2) ---
# NOTE: MEDIUM and LOW are intentionally equal — there is no "low but keep match" band.
# >= 0.85 = high confidence, 0.70-0.85 = medium confidence, < 0.70 = fallback to default.
CONFIDENCE_HIGH_THRESHOLD = 0.85    # Strong match, single dominant agent
CONFIDENCE_MEDIUM_THRESHOLD = 0.70  # Medium confidence lower bound (for batch counting)
CONFIDENCE_LOW_THRESHOLD = 0.70     # Below this, use fallback agent

# --- _calculate_confidence() scoring parameters ---
CONFIDENCE_NO_MATCH = 0.50          # Confidence when no patterns match at all
CONFIDENCE_BASE = 0.60              # Base confidence for multi-match scoring
CONFIDENCE_SCORE_WEIGHT = 0.30      # Weight applied to top match score
CONFIDENCE_SINGLE_MATCH_BASE = 0.85 # Base confidence for single-match case
CONFIDENCE_SINGLE_MATCH_SCALE = 0.50  # Scale factor for single-match quality bonus
CONFIDENCE_SINGLE_MATCH_OFFSET = 0.75  # Score offset for single-match calculation
CONFIDENCE_MAX = 0.98               # Absolute ceiling for confidence
CONFIDENCE_MIN = 0.40               # Absolute floor for confidence

# Dominance detection: how far top match must exceed second match
DOMINANCE_RATIO_HIGH = 0.30         # Score gap ratio for clear dominance
DOMINANCE_RATIO_MODERATE = 0.15     # Score gap ratio for moderate dominance
CONFIDENCE_CLEAR_DOMINANCE_BONUS = 0.15   # Bonus when top match clearly dominates
CONFIDENCE_MODERATE_DOMINANCE_BONUS = 0.08  # Bonus when top match moderately dominates

# Competing pattern penalty
COMPETING_SCORE_RATIO = 0.70        # Fraction of top score to count as "competing"
COMPETING_THRESHOLD = 2             # Number of competing matches before penalty applies
CONFIDENCE_COMPETING_PENALTY = 0.05 # Penalty per extra competing pattern

# --- _calculate_match_quality() parameters ---
MATCH_QUALITY_BASE = 0.75           # Default quality for any pattern match
MATCH_QUALITY_NO_LEADING_WILDCARD_BONUS = 0.10   # Bonus for anchored start
MATCH_QUALITY_NO_TRAILING_WILDCARD_BONUS = 0.05  # Bonus for anchored end
MATCH_QUALITY_LONG_PATTERN_BONUS = 0.05   # Bonus for specific (long) patterns
MATCH_QUALITY_LONG_PATTERN_MIN_LEN = 6    # Minimum cleaned pattern length for bonus

# --- analyze_content() pattern bonus ---
PATTERN_COUNT_BONUS_PER_EXTRA = 0.05      # Score bonus per additional matched pattern
PATTERN_COUNT_BONUS_MAX = 1.15            # Maximum pattern count multiplier

# --- route_batch() accuracy weights ---
BATCH_ACCURACY_HIGH_WEIGHT = 0.95   # Weight for high-confidence matches
BATCH_ACCURACY_MEDIUM_WEIGHT = 0.80 # Weight for medium-confidence matches
BATCH_ACCURACY_LOW_WEIGHT = 0.60    # Weight for low-confidence matches


class AgentRoutingEngine:
    """
    Content-based Agent Routing Engine.

    Analyzes node content to recommend the most suitable agent for processing.
    Implements pattern matching with confidence scoring.

    Usage:
        engine = AgentRoutingEngine()
        request = RoutingRequest(node_id="n1", node_text="什么是逆否命题")
        result = engine.route_single_node(request)
        print(f"Recommended: {result.recommended_agent}, Confidence: {result.confidence}")

    [Source: docs/architecture/decisions/0002-langgraph-agents.md]
    """

    def __init__(self, pattern_config: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Initialize the routing engine.

        Args:
            pattern_config: Optional custom pattern configuration.
                           If None, uses default CONTENT_PATTERN_MAP.
        """
        self.pattern_config = pattern_config or CONTENT_PATTERN_MAP
        self.pattern_version = PATTERN_VERSION
        logger.info(f"AgentRoutingEngine initialized with pattern version {self.pattern_version}")

    def analyze_content(self, node_text: str) -> List[Tuple[str, float]]:
        """
        Analyze content and return matching agents with scores.

        Args:
            node_text: The text content to analyze

        Returns:
            List of (agent_name, match_score) tuples sorted by score descending
        """
        if not node_text or not node_text.strip():
            logger.warning("Empty node text provided for analysis")
            return []

        # Normalize text: lowercase for English, keep original for Chinese
        normalized_text = node_text.strip()
        normalized_lower = normalized_text.lower()

        matches: List[Tuple[str, float, int, List[str]]] = []  # (agent, score, priority, patterns)

        for agent_name, config in self.pattern_config.items():
            patterns = config.get("patterns", [])
            weight = config.get("weight", 1.0)
            priority = config.get("priority", 10)

            matched_patterns = []
            max_match_quality = 0.0

            for pattern in patterns:
                try:
                    # Try matching against both original and lowercase text
                    if re.search(pattern, normalized_text, re.IGNORECASE):
                        matched_patterns.append(pattern)
                        # Calculate match quality based on pattern specificity
                        match_quality = self._calculate_match_quality(pattern, normalized_text)
                        max_match_quality = max(max_match_quality, match_quality)
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern}': {e}")
                    continue

            if matched_patterns:
                # Score = weight * match_quality * pattern count bonus
                pattern_bonus = min(
                    1.0 + PATTERN_COUNT_BONUS_PER_EXTRA * (len(matched_patterns) - 1),
                    PATTERN_COUNT_BONUS_MAX,
                )
                score = weight * max_match_quality * pattern_bonus
                matches.append((agent_name, score, priority, matched_patterns))

        # Sort by score (descending), then by priority (ascending for ties)
        matches.sort(key=lambda x: (-x[1], x[2]))

        return [(agent, score) for agent, score, _, _ in matches]

    def _calculate_match_quality(self, pattern: str, text: str) -> float:
        """
        Calculate match quality based on pattern specificity.

        More specific patterns (longer, more constrained) get higher quality scores.

        Args:
            pattern: The regex pattern that matched
            text: The original text

        Returns:
            Match quality score (0.0 - 1.0)
        """
        quality = MATCH_QUALITY_BASE

        # Boost for patterns without leading/trailing wildcards
        if not pattern.startswith(".*"):
            quality += MATCH_QUALITY_NO_LEADING_WILDCARD_BONUS
        if not pattern.endswith(".*"):
            quality += MATCH_QUALITY_NO_TRAILING_WILDCARD_BONUS

        # Boost for longer specific patterns (more characters excluding wildcards)
        clean_pattern = re.sub(r'\.\*|\.\+|\\s\+|\\s\*', '', pattern)
        if len(clean_pattern) > MATCH_QUALITY_LONG_PATTERN_MIN_LEN:
            quality += MATCH_QUALITY_LONG_PATTERN_BONUS

        return min(quality, 1.0)

    def _calculate_confidence(
        self,
        matches: List[Tuple[str, float]],
        has_override: bool = False
    ) -> float:
        """
        Calculate confidence score based on match analysis.

        Confidence scoring (AC2):
        - High confidence (>= 0.85): Strong pattern match, single dominant agent
        - Medium confidence (0.7-0.85): Multiple patterns, clear winner
        - Low confidence (< 0.7): Ambiguous content, use fallback

        Args:
            matches: List of (agent, score) tuples
            has_override: Whether manual override was used

        Returns:
            Confidence score (0.0 - 1.0)
        """
        if has_override:
            return 1.0

        if not matches:
            return CONFIDENCE_NO_MATCH

        if len(matches) == 1:
            # Single match - base confidence on match score
            score = matches[0][1]
            return min(
                CONFIDENCE_SINGLE_MATCH_BASE
                + (score - CONFIDENCE_SINGLE_MATCH_OFFSET) * CONFIDENCE_SINGLE_MATCH_SCALE,
                CONFIDENCE_MAX,
            )

        # Multiple matches - check dominance
        top_score = matches[0][1]
        second_score = matches[1][1] if len(matches) > 1 else 0

        # Calculate confidence based on score gap
        if top_score > 0:
            score_gap = (top_score - second_score) / top_score
        else:
            score_gap = 0

        # Base confidence from top score
        base_confidence = CONFIDENCE_BASE + (top_score * CONFIDENCE_SCORE_WEIGHT)

        # Bonus for clear winner
        if score_gap >= DOMINANCE_RATIO_HIGH:
            base_confidence += CONFIDENCE_CLEAR_DOMINANCE_BONUS
        elif score_gap >= DOMINANCE_RATIO_MODERATE:
            base_confidence += CONFIDENCE_MODERATE_DOMINANCE_BONUS

        # Penalty for multiple competing patterns
        competing_count = sum(
            1 for _, score in matches if score >= top_score * COMPETING_SCORE_RATIO
        )
        if competing_count > COMPETING_THRESHOLD:
            base_confidence -= CONFIDENCE_COMPETING_PENALTY * (competing_count - COMPETING_THRESHOLD)

        return max(min(base_confidence, CONFIDENCE_MAX), CONFIDENCE_MIN)

    def route_single_node(self, request: RoutingRequest) -> RoutingResult:
        """
        Route a single node to the best matching agent.

        Args:
            request: RoutingRequest with node_id, node_text, and optional agent_override

        Returns:
            RoutingResult with recommended agent and confidence
        """
        logger.debug(f"Routing node {request.node_id}: '{request.node_text[:50]}...'")

        # Task 4: Handle manual override (AC3)
        if request.agent_override:
            if request.agent_override in ALL_AGENT_NAMES:
                logger.info(f"Manual override to {request.agent_override} for node {request.node_id}")
                return RoutingResult(
                    node_id=request.node_id,
                    recommended_agent=request.agent_override,
                    confidence=1.0,
                    patterns_matched=[],
                    fallback_agent=DEFAULT_FALLBACK_AGENT,
                    reason="manual_override"
                )
            else:
                logger.warning(
                    f"Invalid override agent '{request.agent_override}', "
                    f"falling back to automatic routing"
                )

        # Analyze content
        matches = self.analyze_content(request.node_text)

        if not matches:
            # No matches - use fallback
            logger.debug(f"No pattern matches for node {request.node_id}, using fallback")
            return RoutingResult(
                node_id=request.node_id,
                recommended_agent=DEFAULT_FALLBACK_AGENT,
                confidence=CONFIDENCE_NO_MATCH,
                patterns_matched=[],
                fallback_agent=None,
                reason="no_pattern_match"
            )

        # Get top match
        top_agent, top_score = matches[0]
        confidence = self._calculate_confidence(matches)

        # Get matched patterns for top agent
        patterns_matched = []
        if top_agent in self.pattern_config:
            for pattern in self.pattern_config[top_agent].get("patterns", []):
                try:
                    if re.search(pattern, request.node_text, re.IGNORECASE):
                        patterns_matched.append(pattern)
                except re.error:
                    continue

        # Determine fallback (second best if available)
        fallback_agent = matches[1][0] if len(matches) > 1 else DEFAULT_FALLBACK_AGENT

        # Check confidence threshold
        if confidence < CONFIDENCE_LOW_THRESHOLD:
            logger.debug(
                f"Low confidence ({confidence:.2f}) for node {request.node_id}, "
                f"using fallback {DEFAULT_FALLBACK_AGENT}"
            )
            return RoutingResult(
                node_id=request.node_id,
                recommended_agent=DEFAULT_FALLBACK_AGENT,
                confidence=confidence,
                patterns_matched=patterns_matched,
                fallback_agent=top_agent,  # Original top match as fallback
                reason=f"low_confidence_fallback (original: {top_agent})"
            )

        # Determine reason based on confidence level
        if confidence >= CONFIDENCE_HIGH_THRESHOLD:
            reason = "high_confidence_match"
        else:
            reason = "medium_confidence_match"

        return RoutingResult(
            node_id=request.node_id,
            recommended_agent=top_agent,
            confidence=confidence,
            patterns_matched=patterns_matched,
            fallback_agent=fallback_agent,
            reason=reason
        )

    def route_batch(self, request: BatchRoutingRequest) -> BatchRoutingResponse:
        """
        Route a batch of nodes to their best matching agents.

        Args:
            request: BatchRoutingRequest with list of nodes

        Returns:
            BatchRoutingResponse with results and accuracy estimate
        """
        logger.info(f"Batch routing {len(request.nodes)} nodes")

        results = []
        high_confidence_count = 0
        medium_confidence_count = 0
        low_confidence_count = 0

        for node_request in request.nodes:
            result = self.route_single_node(node_request)
            results.append(result)

            # Count confidence levels
            if result.confidence >= CONFIDENCE_HIGH_THRESHOLD:
                high_confidence_count += 1
            elif result.confidence >= CONFIDENCE_MEDIUM_THRESHOLD:
                medium_confidence_count += 1
            else:
                low_confidence_count += 1

        # Calculate routing accuracy estimate
        # Based on weighted confidence average
        total_nodes = len(results)
        if total_nodes > 0:
            # Weight high confidence matches more heavily
            weighted_sum = (
                high_confidence_count * BATCH_ACCURACY_HIGH_WEIGHT +
                medium_confidence_count * BATCH_ACCURACY_MEDIUM_WEIGHT +
                low_confidence_count * BATCH_ACCURACY_LOW_WEIGHT
            )
            accuracy_estimate = weighted_sum / total_nodes
        else:
            accuracy_estimate = 0.0

        logger.info(
            f"Batch routing complete: {high_confidence_count} high, "
            f"{medium_confidence_count} medium, {low_confidence_count} low confidence"
        )

        return BatchRoutingResponse(
            results=results,
            routing_accuracy_estimate=accuracy_estimate,
            total_nodes=total_nodes,
            high_confidence_count=high_confidence_count,
            medium_confidence_count=medium_confidence_count,
            low_confidence_count=low_confidence_count,
        )


# Singleton instance
_routing_engine: Optional[AgentRoutingEngine] = None


def get_routing_engine() -> AgentRoutingEngine:
    """Get singleton AgentRoutingEngine instance."""
    global _routing_engine
    if _routing_engine is None:
        _routing_engine = AgentRoutingEngine()
    return _routing_engine


__all__ = [
    "AgentRoutingEngine",
    "CONTENT_PATTERN_MAP",
    "PATTERN_VERSION",
    "DEFAULT_FALLBACK_AGENT",
    "ORAL_EXPLANATION_WEIGHT",
    # Routing decision thresholds
    "CONFIDENCE_HIGH_THRESHOLD",
    "CONFIDENCE_MEDIUM_THRESHOLD",
    "CONFIDENCE_LOW_THRESHOLD",
    # Confidence scoring parameters
    "CONFIDENCE_NO_MATCH",
    "CONFIDENCE_BASE",
    "CONFIDENCE_SCORE_WEIGHT",
    "CONFIDENCE_SINGLE_MATCH_BASE",
    "CONFIDENCE_SINGLE_MATCH_SCALE",
    "CONFIDENCE_SINGLE_MATCH_OFFSET",
    "CONFIDENCE_MAX",
    "CONFIDENCE_MIN",
    # Dominance detection
    "DOMINANCE_RATIO_HIGH",
    "DOMINANCE_RATIO_MODERATE",
    "CONFIDENCE_CLEAR_DOMINANCE_BONUS",
    "CONFIDENCE_MODERATE_DOMINANCE_BONUS",
    # Competing pattern penalty
    "COMPETING_SCORE_RATIO",
    "COMPETING_THRESHOLD",
    "CONFIDENCE_COMPETING_PENALTY",
    # Match quality scoring
    "MATCH_QUALITY_BASE",
    "MATCH_QUALITY_NO_LEADING_WILDCARD_BONUS",
    "MATCH_QUALITY_NO_TRAILING_WILDCARD_BONUS",
    "MATCH_QUALITY_LONG_PATTERN_BONUS",
    "MATCH_QUALITY_LONG_PATTERN_MIN_LEN",
    # Pattern count bonus
    "PATTERN_COUNT_BONUS_PER_EXTRA",
    "PATTERN_COUNT_BONUS_MAX",
    # Batch accuracy weights
    "BATCH_ACCURACY_HIGH_WEIGHT",
    "BATCH_ACCURACY_MEDIUM_WEIGHT",
    "BATCH_ACCURACY_LOW_WEIGHT",
    # Factory
    "get_routing_engine",
]
