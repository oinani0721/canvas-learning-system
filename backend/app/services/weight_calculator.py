# ✅ Verified from Story 24.3 Dev Notes
"""
Weight Calculator for Intelligent Review Mode.

Calculates weakness scores for concepts based on review history
and applies weighted selection for targeted review mode.

PRD Reference: v1.1.8 - calculate_targeted_review_weights tool
Story: 24.3 - Intelligent Weight Algorithm for Targeted Review
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ConceptWeightData:
    """
    Weight calculation data for a concept.

    Attributes:
        concept_id: Unique concept identifier
        concept_name: Human-readable concept name
        weakness_score: Calculated weakness score (0.0-1.0)
        failure_count: Number of failed reviews (rating <= 2)
        avg_rating: Average review rating (1-4 scale)
        review_count: Total number of reviews
        days_since_review: Days since last review
        category: Classification ("weak", "borderline", "mastered")
    """
    concept_id: str
    concept_name: str
    weakness_score: float  # 0.0-1.0
    failure_count: int
    avg_rating: float
    review_count: int
    days_since_review: int
    category: str  # "weak", "borderline", "mastered"


class WeightCalculator:
    """
    Calculates weakness scores and applies weighted selection.

    This class implements the intelligent weight algorithm for targeted review mode.
    It analyzes historical review data to identify weak concepts and applies
    configurable weights to prioritize them in verification canvas generation.

    PRD Reference: v1.1.8 - calculate_targeted_review_weights tool
    Story Reference: docs/stories/24.3.story.md
    """

    # Configurable thresholds
    WEAK_THRESHOLD = 0.6
    MASTERED_THRESHOLD = 0.4
    DEFAULT_NEW_SCORE = 0.5

    # Score component weights (must sum to 1.0)
    RATING_WEIGHT = 0.4      # Avg rating impact
    FAILURE_WEIGHT = 0.3     # Failure count impact
    RECENCY_WEIGHT = 0.2     # Days since review impact
    TREND_WEIGHT = 0.1       # Improvement trend impact

    async def calculate_weakness_scores(
        self,
        concepts: List[Dict],
        review_history: List[Dict]
    ) -> List[ConceptWeightData]:
        """
        Calculate weakness scores for all concepts.

        AC1: Weakness Score Calculation
        - Factors in: average_rating, failure_count, days_since_last_review, trend_direction
        - Higher weakness_score = weaker concept = higher priority

        Args:
            concepts: List of concept dicts with id, name
            review_history: Review history from Graphiti/learning memories

        Returns:
            List of ConceptWeightData with calculated scores
        """
        results = []
        history_map = self._build_history_map(review_history)

        for concept in concepts:
            concept_id = concept.get("id", "")
            history = history_map.get(concept_id, [])

            if not history:
                # AC4: New concept - neutral score
                score = self.DEFAULT_NEW_SCORE
                weight_data = ConceptWeightData(
                    concept_id=concept_id,
                    concept_name=concept.get("name", ""),
                    weakness_score=score,
                    failure_count=0,
                    avg_rating=0.0,
                    review_count=0,
                    days_since_review=0,
                    category="borderline"
                )
            else:
                # Calculate score from history
                weight_data = self._calculate_from_history(concept, history)

            results.append(weight_data)

        logger.info(
            f"Calculated weakness scores for {len(results)} concepts: "
            f"{sum(1 for r in results if r.category == 'weak')} weak, "
            f"{sum(1 for r in results if r.category == 'mastered')} mastered, "
            f"{sum(1 for r in results if r.category == 'borderline')} borderline"
        )

        return results

    def _build_history_map(self, review_history: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Build a map of concept_id -> review history.

        Args:
            review_history: Flat list of review records

        Returns:
            Dict mapping concept_id to list of review dicts
        """
        history_map: Dict[str, List[Dict]] = {}

        for record in review_history:
            concept_id = record.get("concept_id") or record.get("node_id")
            if concept_id:
                if concept_id not in history_map:
                    history_map[concept_id] = []
                history_map[concept_id].append(record)

        return history_map

    def _calculate_from_history(
        self,
        concept: Dict,
        history: List[Dict]
    ) -> ConceptWeightData:
        """
        Calculate weakness score from review history.

        AC1: Score factors in rating, failure count, recency, and trend.

        Args:
            concept: Concept dict with id, name
            history: List of review records for this concept

        Returns:
            ConceptWeightData with calculated scores
        """
        # Calculate metrics
        ratings = [h.get("rating") or h.get("score", 0) for h in history if h.get("rating") or h.get("score")]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        failure_count = sum(1 for h in history if (h.get("rating") or h.get("score", 0)) <= 2)
        review_count = len(history)

        # Days since last review
        last_review = max(
            (self._parse_timestamp(h.get("timestamp")) for h in history if h.get("timestamp")),
            default=None
        )
        days_since = 0
        if last_review:
            days_since = (datetime.utcnow() - last_review).days

        # Calculate component scores (all normalized to 0-1, inverted where needed)
        # Rating 1-4 scale: 1 (worst) -> 1.0 weakness, 4 (best) -> 0.0 weakness
        rating_score = 1.0 - (avg_rating - 1) / 3.0 if avg_rating > 0 else 0.5
        rating_score = max(0.0, min(1.0, rating_score))

        # Failure score: Cap at 5 failures
        failure_score = min(failure_count / 5.0, 1.0)

        # Recency score: Cap at 30 days
        recency_score = min(days_since / 30.0, 1.0)

        # Trend score (simplified: comparing recent vs older ratings)
        trend_score = self._calculate_trend_score(history)

        # Weighted combination
        weakness_score = (
            self.RATING_WEIGHT * rating_score +
            self.FAILURE_WEIGHT * failure_score +
            self.RECENCY_WEIGHT * recency_score +
            self.TREND_WEIGHT * trend_score
        )

        # Clamp to 0-1
        weakness_score = max(0.0, min(1.0, weakness_score))

        # AC3: Categorize based on thresholds
        if weakness_score >= self.WEAK_THRESHOLD:
            category = "weak"
        elif weakness_score < self.MASTERED_THRESHOLD:
            category = "mastered"
        else:
            category = "borderline"

        return ConceptWeightData(
            concept_id=concept.get("id", ""),
            concept_name=concept.get("name", ""),
            weakness_score=weakness_score,
            failure_count=failure_count,
            avg_rating=avg_rating,
            review_count=review_count,
            days_since_review=days_since,
            category=category
        )

    def _calculate_trend_score(self, history: List[Dict]) -> float:
        """
        Calculate trend score based on rating improvement.

        AC1: Trend direction affects weakness score.

        Args:
            history: List of review records

        Returns:
            Trend score (0.0-1.0) where higher = getting worse
        """
        if len(history) < 2:
            return 0.5  # Neutral for insufficient data

        # Sort by timestamp
        sorted_history = sorted(
            history,
            key=lambda h: self._parse_timestamp(h.get("timestamp"))
        )

        # Compare recent half vs older half
        mid = len(sorted_history) // 2
        older_ratings = [
            h.get("rating") or h.get("score", 0)
            for h in sorted_history[:mid]
            if h.get("rating") or h.get("score")
        ]
        recent_ratings = [
            h.get("rating") or h.get("score", 0)
            for h in sorted_history[mid:]
            if h.get("rating") or h.get("score")
        ]

        if not older_ratings or not recent_ratings:
            return 0.5

        older_avg = sum(older_ratings) / len(older_ratings)
        recent_avg = sum(recent_ratings) / len(recent_ratings)

        # Improving = lower weakness score
        # Rating improved: recent > older -> negative trend score
        trend_diff = older_avg - recent_avg  # Positive if getting worse

        # Normalize to 0-1
        return max(0.0, min(1.0, 0.5 + trend_diff / 2.0))

    def _parse_timestamp(self, timestamp: Optional[str]) -> datetime:
        """
        Parse timestamp string to datetime.

        Args:
            timestamp: ISO format timestamp string or None

        Returns:
            datetime object, or datetime.min if parsing fails
        """
        if not timestamp:
            return datetime.min

        try:
            # Try ISO format
            if 'T' in timestamp:
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                # Try date only
                return datetime.fromisoformat(timestamp)
        except (ValueError, AttributeError):
            logger.warning(f"Failed to parse timestamp: {timestamp}")
            return datetime.min
