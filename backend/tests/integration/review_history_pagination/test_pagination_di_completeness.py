# Story 34.11: DI completeness source code inspection tests
"""
Tests verifying dependency injection completeness for ReviewService.

Split from test_review_history_pagination.py (1234 lines → ≤300 lines).

Covers:
- Story 34.8 AC2: graphiti_client injection in canonical singleton
- Story 38.9: dependencies.py delegation to canonical singleton
"""

import inspect


class TestReviewServiceDICompleteness:
    """Story 34.8 AC2: Verify canonical singleton handles graphiti_client."""

    def test_canonical_singleton_injects_graphiti_client(self):
        """AC2: get_review_service() must explicitly inject graphiti_client."""
        from app.services.review_service import get_review_service

        source = inspect.getsource(get_review_service)
        assert "graphiti_client" in source, (
            "Canonical get_review_service() does not mention graphiti_client"
        )
        assert "graphiti_client=graphiti_client" in source, (
            "Canonical get_review_service() does not pass graphiti_client= to ReviewService()"
        )

    def test_dependencies_delegates_to_canonical_singleton(self):
        """AC2: dependencies.py get_review_service() must delegate to canonical singleton."""
        from app.dependencies import get_review_service

        source = inspect.getsource(get_review_service)
        assert "_get_rs_singleton" in source, (
            "dependencies.py get_review_service() does not delegate to canonical "
            "singleton via _get_rs_singleton — may construct ReviewService inline"
        )
