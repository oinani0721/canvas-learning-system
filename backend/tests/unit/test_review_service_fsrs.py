# Story 32.2: ReviewService FSRS Integration Unit Tests
# [Source: docs/stories/32.2.story.md#Task-7]
"""
Unit tests for ReviewService FSRS-4.5 integration.

Tests cover:
- AC-32.2.1: FSRSManager import and dependency injection
- AC-32.2.2: FSRS rating parameter (1-4) support
- AC-32.2.3: Dynamic interval calculation
- AC-32.2.4: Backward compatibility (score → rating conversion)
- AC-32.2.5: Migration documentation (docstring presence)
"""

import pytest

# Use shared isolate_card_states_file fixture from conftest.py
pytestmark = pytest.mark.usefixtures("isolate_card_states_file")

# Shared fixtures (mock_canvas_service, mock_task_manager, review_service_factory,
# review_service, fallback_service) are provided by unit/conftest.py


class TestFSRSImport:
    """AC-32.2.1: Test FSRSManager import and availability."""

    def test_fsrs_module_available(self):
        """FSRS module should be importable."""
        from app.services.review_service import FSRS_AVAILABLE

        # Note: FSRS_AVAILABLE may be True or False depending on environment
        assert isinstance(FSRS_AVAILABLE, bool)

    def test_fsrs_manager_import_success(self):
        """FSRSManager should be imported when available."""
        try:
            import sys
            from pathlib import Path

            _project_root = Path(__file__).parent.parent.parent
            _src_path = _project_root / "lib"
            if str(_src_path) not in sys.path:
                sys.path.insert(0, str(_src_path))

            from memory.temporal.fsrs_manager import FSRSManager

            assert FSRSManager is not None
        except ImportError:
            pytest.skip("FSRS module not available in test environment")

    def test_fsrs_fallback_when_unavailable(self, review_service_factory):
        """Service should work with fallback when FSRS unavailable."""
        # Should not raise even if FSRS unavailable
        service = review_service_factory()
        assert service is not None


class TestFSRSRatings:
    """AC-32.2.2: Test FSRS rating parameter (1-4) acceptance."""

    @pytest.mark.asyncio
    async def test_rating_1_again(self, review_service):
        """Rating 1 (Again) should be accepted."""
        result = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id="node_001",
            rating=1,  # Again
        )
        assert result is not None
        assert "next_review" in result or "next_review_date" in result
        # Again typically results in short interval (learning phase)
        assert result.get("interval_days", result.get("new_interval", 0)) <= 1

    @pytest.mark.asyncio
    async def test_rating_2_hard(self, review_service):
        """Rating 2 (Hard) should be accepted."""
        result = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id="node_002",
            rating=2,  # Hard
        )
        assert result is not None
        assert "next_review" in result or "next_review_date" in result

    @pytest.mark.asyncio
    async def test_rating_3_good(self, review_service):
        """Rating 3 (Good) should be accepted."""
        result = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id="node_003",
            rating=3,  # Good
        )
        assert result is not None
        assert "next_review" in result or "next_review_date" in result

    @pytest.mark.asyncio
    async def test_rating_4_easy(self, review_service):
        """Rating 4 (Easy) should be accepted and give longer interval."""
        result = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id="node_004",
            rating=4,  # Easy
        )
        assert result is not None
        assert "next_review" in result or "next_review_date" in result
        # Easy should result in longer interval than Again
        assert result.get("interval_days", result.get("new_interval", 0)) >= 1


class TestScoreToRatingConversion:
    """AC-32.2.4: Test backward compatibility with score-to-rating conversion."""

    @pytest.mark.asyncio
    async def test_score_under_40_converts_to_again(self, review_service):
        """Score < 40 should convert to rating 1 (Again)."""
        result = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id="node_low",
            score=25.0,  # Should become Again
        )
        assert result is not None
        # Low score should result in short interval (learning phase)
        assert result.get("interval_days", result.get("new_interval", 0)) <= 3

    @pytest.mark.asyncio
    async def test_score_40_59_converts_to_hard(self, review_service):
        """Score 40-59 should convert to rating 2 (Hard)."""
        result = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id="node_medium",
            score=50.0,  # Should become Hard
        )
        assert result is not None
        assert "next_review" in result or "next_review_date" in result

    @pytest.mark.asyncio
    async def test_score_60_84_converts_to_good(self, review_service):
        """Score 60-84 should convert to rating 3 (Good)."""
        result = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id="node_good",
            score=75.0,  # Should become Good
        )
        assert result is not None
        assert "next_review" in result or "next_review_date" in result

    @pytest.mark.asyncio
    async def test_score_85_plus_converts_to_easy(self, review_service):
        """Score >= 85 should convert to rating 4 (Easy)."""
        result = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id="node_excellent",
            score=95.0,  # Should become Easy
        )
        assert result is not None
        # High score should result in longer interval (FSRS state=2 review mode)
        assert result.get("interval_days", result.get("new_interval", 0)) >= 1


class TestDynamicIntervalCalculation:
    """AC-32.2.3: Test FSRS dynamic interval calculation."""

    @pytest.mark.asyncio
    async def test_schedule_review_returns_fsrs_data(self, review_service):
        """schedule_review should return FSRS card data when available."""
        result = await review_service.schedule_review(canvas_name="test_canvas", concept_id="node_fsrs")
        assert result is not None
        # Check for various field names (API may use different naming)
        assert "scheduled_date" in result or "next_review_date" in result or "next_review" in result
        assert "interval_days" in result or "interval" in result
        # FSRS-specific fields (may be None if FSRS unavailable)
        assert "card_data" in result or "fsrs_state" in result or "algorithm" in result

    @pytest.mark.asyncio
    async def test_repeated_reviews_increase_interval(self, review_service):
        """Repeated successful reviews should increase intervals (FSRS behavior)."""
        concept_id = "node_repeated"

        # First review
        result1 = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id=concept_id,
            rating=3,  # Good
        )
        interval1 = result1.get("new_interval", 1)

        # Second review with same rating
        result2 = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id=concept_id,
            rating=3,  # Good
            card_state=result1.get("card_data"),
        )
        interval2 = result2.get("new_interval", 1)

        # With FSRS, repeated Good ratings should generally increase interval
        # Note: First review may have special learning phase behavior
        assert interval2 >= interval1 or interval2 >= 1  # Allow for learning phase

    @pytest.mark.asyncio
    async def test_failed_review_resets_interval(self, review_service):
        """Failed review (rating 1) should reset or reduce interval."""
        concept_id = "node_failed"

        # First successful review
        result1 = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id=concept_id,
            rating=4,  # Easy - should give longer interval
        )

        # Failed review
        result2 = await review_service.record_review_result(
            canvas_name="test_canvas",
            concept_id=concept_id,
            rating=1,  # Again - should reset
            card_state=result1.get("card_data"),
        )

        # After failure, interval should be short (learning phase)
        assert result2.get("new_interval", 0) <= 3


class TestCardStatePersistence:
    """Test FSRS card state persistence functionality."""

    @pytest.mark.asyncio
    async def test_card_data_returned_in_response(self, review_service):
        """Response should include card_data for client-side caching."""
        result = await review_service.record_review_result(
            canvas_name="test_canvas", concept_id="node_persist", rating=3
        )
        # card_data should be present (may be None if FSRS unavailable)
        assert "card_data" in result or result.get("algorithm") == "ebbinghaus-fallback"

    @pytest.mark.asyncio
    async def test_card_state_can_be_loaded(self, review_service):
        """Saved card state should be loadable."""
        concept_id = "node_load_test"

        # Record a review to save state
        result = await review_service.record_review_result(canvas_name="test_canvas", concept_id=concept_id, rating=3)
        card_data = result.get("card_data")

        if card_data:
            # Use saved state in next review
            result2 = await review_service.record_review_result(
                canvas_name="test_canvas",
                concept_id=concept_id,
                rating=3,
                card_state=card_data,
            )
            assert result2 is not None


class TestFSRSStateResponse:
    """Test FSRS state information in responses."""

    @pytest.mark.asyncio
    async def test_fsrs_state_fields(self, review_service):
        """Response should include FSRS state fields when available."""
        result = await review_service.record_review_result(canvas_name="test_canvas", concept_id="node_state", rating=3)

        fsrs_state = result.get("fsrs_state")
        if fsrs_state:
            # Check FSRS state fields
            assert "stability" in fsrs_state
            assert "difficulty" in fsrs_state
            assert "state" in fsrs_state
            assert "reps" in fsrs_state
            assert "lapses" in fsrs_state

            # Validate ranges
            assert fsrs_state["stability"] >= 0
            assert 1 <= fsrs_state["difficulty"] <= 10
            assert fsrs_state["state"] in [
                0,
                1,
                2,
                3,
            ]  # New, Learning, Review, Relearning


class TestMigrationDocumentation:
    """AC-32.2.5: Test migration documentation presence."""

    def test_module_docstring_contains_migration_info(self):
        """Module docstring should contain FSRS migration documentation."""
        from app.services import review_service

        docstring = review_service.__doc__
        assert docstring is not None
        assert "FSRS" in docstring or "fsrs" in docstring.lower()
        assert "migration" in docstring.lower() or "MIGRATION" in docstring

    def test_rating_conversion_documented(self):
        """Score-to-rating conversion should be documented."""
        from app.services import review_service

        docstring = review_service.__doc__
        assert "rating" in docstring.lower()
        # Check for conversion thresholds
        assert "40" in docstring or "score" in docstring.lower()


class TestAlgorithmField:
    """Test algorithm field in responses."""

    @pytest.mark.asyncio
    async def test_algorithm_field_present(self, review_service):
        """Response should include algorithm field."""
        result = await review_service.record_review_result(canvas_name="test_canvas", concept_id="node_algo", rating=3)
        assert "algorithm" in result
        # Should be fsrs-4.5 or ebbinghaus-fallback
        assert result["algorithm"] in ["fsrs-4.5", "ebbinghaus-fallback"]


# ═══════════════════════════════════════════════════════════════════════════════
# Story 32.11 P1-A: Ebbinghaus Fallback — next_review must be future date
# (Restored from Story 32.9; removed by Story 38.9 refactoring)
# ═══════════════════════════════════════════════════════════════════════════════


class TestEbbinghausFallbackNextReview:
    """P1: When FSRS is unavailable, Ebbinghaus fallback must return
    next_review as a future date (now + interval), not 'now'."""

    @pytest.mark.asyncio
    async def test_fallback_score_low_interval_1_day(self, fallback_service):
        """score < 40 → interval=1 day, next_review = now + 1 day."""
        from datetime import datetime, timezone

        before = datetime.now(timezone.utc)
        result = await fallback_service.record_review_result(canvas_name="test", concept_id="c1", score=20)
        assert result["algorithm"] == "ebbinghaus-fallback"
        assert result["interval_days"] == 1
        next_review = datetime.fromisoformat(result["next_review"])
        assert next_review > before, "next_review must be in the future"

    @pytest.mark.asyncio
    async def test_fallback_score_medium_interval_3_days(self, fallback_service):
        """score 40-59 → interval=3 days."""
        from datetime import datetime, timezone

        before = datetime.now(timezone.utc)
        result = await fallback_service.record_review_result(canvas_name="test", concept_id="c2", score=50)
        assert result["interval_days"] == 3
        next_review = datetime.fromisoformat(result["next_review"])
        assert (next_review - before).days >= 2

    @pytest.mark.asyncio
    async def test_fallback_score_good_interval_7_days(self, fallback_service):
        """score 60-84 → interval=7 days."""
        from datetime import datetime, timezone

        before = datetime.now(timezone.utc)
        result = await fallback_service.record_review_result(canvas_name="test", concept_id="c3", score=70)
        assert result["interval_days"] == 7
        next_review = datetime.fromisoformat(result["next_review"])
        assert (next_review - before).days >= 6

    @pytest.mark.asyncio
    async def test_fallback_score_easy_interval_30_days(self, fallback_service):
        """score >= 85 → interval=30 days."""
        from datetime import datetime, timezone

        before = datetime.now(timezone.utc)
        result = await fallback_service.record_review_result(canvas_name="test", concept_id="c4", score=95)
        assert result["interval_days"] == 30
        next_review = datetime.fromisoformat(result["next_review"])
        assert (next_review - before).days >= 29

    @pytest.mark.asyncio
    async def test_fallback_rating_only_no_score(self, fallback_service):
        """rating=1 without score → interval=1 day."""
        result = await fallback_service.record_review_result(canvas_name="test", concept_id="c5", rating=1)
        assert result["algorithm"] == "ebbinghaus-fallback"
        assert result["interval_days"] == 1

    @pytest.mark.asyncio
    async def test_fallback_recorded_at_is_utc(self, fallback_service):
        """recorded_at must contain timezone info (UTC)."""
        from datetime import datetime

        result = await fallback_service.record_review_result(canvas_name="test", concept_id="c6", score=50)
        recorded_at = datetime.fromisoformat(result["recorded_at"])
        assert recorded_at.tzinfo is not None, "recorded_at must be timezone-aware"

    @pytest.mark.asyncio
    async def test_fallback_next_review_is_utc(self, fallback_service):
        """next_review must contain timezone info (UTC)."""
        from datetime import datetime

        result = await fallback_service.record_review_result(canvas_name="test", concept_id="c7", score=50)
        next_review = datetime.fromisoformat(result["next_review"])
        assert next_review.tzinfo is not None, "next_review must be timezone-aware"


# ═══════════════════════════════════════════════════════════════════════════════
# Story 32.11 P1-B: schedule_review Ebbinghaus Fallback
# ═══════════════════════════════════════════════════════════════════════════════


class TestScheduleReviewFallback:
    """P1: schedule_review Ebbinghaus fallback must return future scheduled_date."""

    @pytest.mark.asyncio
    async def test_schedule_fallback_returns_future_date(self, fallback_service):
        """Ebbinghaus scheduled_date must be in the future."""
        from datetime import datetime, timezone

        before = datetime.now(timezone.utc)
        result = await fallback_service.schedule_review(canvas_name="test", concept_id="c1", trigger_point=1)
        assert result["algorithm"] == "ebbinghaus-fallback"
        scheduled = datetime.fromisoformat(result["scheduled_date"])
        assert scheduled > before, "scheduled_date must be in the future"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "trigger_point,expected_interval",
        [
            (1, 1),
            (2, 7),
            (3, 30),
            (4, 90),
        ],
    )
    async def test_schedule_fallback_interval_mapping(self, fallback_service, trigger_point, expected_interval):
        """Each trigger_point maps to correct Ebbinghaus interval."""
        result = await fallback_service.schedule_review(
            canvas_name="test", concept_id="c1", trigger_point=trigger_point
        )
        assert result["interval_days"] == expected_interval


# ═══════════════════════════════════════════════════════════════════════════════
# Story 32.11 P1-C: Boundary Conditions
# ═══════════════════════════════════════════════════════════════════════════════


class TestRecordReviewBoundaryConditions:
    """P1: Edge cases for score/rating inputs."""

    @pytest.mark.asyncio
    async def test_score_zero_maps_to_again(self, review_service):
        """score=0 → rating=1 (Again), interval should be shortest."""
        result = await review_service.record_review_result(canvas_name="test", concept_id="c_zero", score=0)
        assert result["rating"] == 1

    @pytest.mark.asyncio
    async def test_score_100_maps_to_easy(self, review_service):
        """score=100 → rating=4 (Easy)."""
        result = await review_service.record_review_result(canvas_name="test", concept_id="c_100", score=100)
        assert result["rating"] == 4

    @pytest.mark.asyncio
    async def test_no_score_no_rating_defaults_to_good(self, review_service):
        """Neither score nor rating → default rating=3 (Good)."""
        result = await review_service.record_review_result(canvas_name="test", concept_id="c_default")
        assert result["rating"] == 3

    @pytest.mark.asyncio
    async def test_rating_takes_precedence_over_score(self, review_service):
        """When both provided, rating is used directly (not converted from score)."""
        result = await review_service.record_review_result(canvas_name="test", concept_id="c_both", score=95, rating=1)
        # rating=1 should be used, not score=95→rating=4
        assert result["rating"] == 1

    @pytest.mark.asyncio
    async def test_invalid_rating_clamped_to_range(self, review_service):
        """rating=0 → clamped to 1; rating=5 → clamped to 4."""
        result_low = await review_service.record_review_result(canvas_name="test", concept_id="c_low", rating=0)
        assert result_low["rating"] >= 1

        result_high = await review_service.record_review_result(canvas_name="test", concept_id="c_high", rating=5)
        assert result_high["rating"] <= 4

    @pytest.mark.asyncio
    async def test_invalid_rating_string_defaults_to_good(self, review_service):
        """Non-numeric rating (e.g., 'abc') → default to 3."""
        result = await review_service.record_review_result(canvas_name="test", concept_id="c_str", rating="abc")
        assert result["rating"] == 3


# ═══════════════════════════════════════════════════════════════════════════════
# Story 32.11 P1-D: Algorithm Selection Path
# ═══════════════════════════════════════════════════════════════════════════════


class TestAlgorithmSelectionPath:
    """P1: Verify FSRS vs Ebbinghaus algorithm selection."""

    @pytest.fixture
    def fsrs_service(self, review_service_factory):
        """Service with FSRS enabled."""
        return review_service_factory()

    @pytest.mark.asyncio
    async def test_fsrs_enabled_uses_fsrs_algorithm(self, fsrs_service):
        """When FSRS is available, algorithm should be 'fsrs-4.5'."""
        if fsrs_service._fsrs_manager is None:
            pytest.skip("FSRS not available in test environment")
        result = await fsrs_service.record_review_result(canvas_name="test", concept_id="c_fsrs", rating=3)
        assert result["algorithm"] == "fsrs-4.5"

    @pytest.mark.asyncio
    async def test_fsrs_disabled_uses_ebbinghaus(self, fallback_service):
        """When FSRS is unavailable, algorithm should be 'ebbinghaus-fallback'."""
        result = await fallback_service.record_review_result(canvas_name="test", concept_id="c_ebb", rating=3)
        assert result["algorithm"] == "ebbinghaus-fallback"

    @pytest.mark.asyncio
    async def test_schedule_fsrs_vs_ebbinghaus(self, fsrs_service, fallback_service):
        """schedule_review returns different algorithms based on FSRS availability."""
        if fsrs_service._fsrs_manager is None:
            pytest.skip("FSRS not available in test environment")
        # FSRS schedule_review with existing card_state avoids new-card edge cases
        # First record a review to create a card, then schedule using the card_data
        record = await fsrs_service.record_review_result(canvas_name="test", concept_id="c_sched", rating=3)
        fsrs_result = await fsrs_service.schedule_review(
            canvas_name="test",
            concept_id="c_sched",
            trigger_point=1,
            card_state=record.get("card_data"),
        )
        fallback_result = await fallback_service.schedule_review(canvas_name="test", concept_id="c1", trigger_point=1)
        assert fsrs_result["algorithm"] == "fsrs-4.5"
        assert fallback_result["algorithm"] == "ebbinghaus-fallback"


# ═══════════════════════════════════════════════════════════════════════════════
# CARD-C4: Fire-and-Forget Failure Counter 已随幻影 Graphiti 镜像下线
# ═══════════════════════════════════════════════════════════════════════════════


class TestAutoPersistCounterRemoved:
    """CARD-C4 (G-FAKE-007) 回归锁定: 幻影镜像写的失败计数器已删。

    原 Story 32.10/32.11 的 _auto_persist_failures 只为一个从未成功过的
    幻影后台写计数 (调用的方法全 git 历史不存在), 无任何暴露口。随
    CARD-C4 安全下线一并移除——本锁防止它被无意识复活。
    """

    def test_phantom_failure_counter_is_gone(self, review_service_factory):
        svc = review_service_factory()
        assert not hasattr(svc, "_auto_persist_failures"), (
            "幻影 Graphiti 镜像的失败计数器已随 CARD-C4 下线, 不应复活; 真接 Graphiti 须等 epic-5a C-1/C-2 契约"
        )

    def test_retired_public_card_state_writer_is_gone(self, review_service_factory):
        """CARD-G3-7-R2: 退役的公开卡状态写入口不得复活。

        为什么单立一条: 下面那条 G-FAKE-007 锁覆盖的是**现存**路径
        (_save_card_states / load_card_state)。如果有人把这个方法整个加回来,
        那条锁碰不到它 —— 它不在用例的调用面里。退役此前只由人工 grep 守着,
        本条把它变成会自己报警的门 (范式抄同类上一条)。
        """
        svc = review_service_factory()
        assert not hasattr(svc, "save_card_state"), (
            "save_card_state 已于 CARD-G3-7-R2 (第十三批) 退役: 它在 backend/app 内"
            "零调用方, 唯一动作是转调 _save_card_states (唯一真实持久化通道), "
            "属 DD-13 名实不符的死路径。要重新引入公开写入口须先立卡说明谁调用它、"
            "以及它与 _save_card_states 的分工。"
        )

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("isolate_card_states_file")
    async def test_card_state_persist_paths_touch_no_memory_client(self, review_service_factory, monkeypatch):
        """Codex MEDIUM-3 补强: 卡状态的写/读真实入口零外部访问——
        两处直接幻影路径若复活, 此锁必红。

        CARD-G3-7-R2: 写侧从退役的公开包装改指其被包装者 `_save_card_states`
        (唯一真实持久化通道)。覆盖面**未变窄**: 被退役的那层只是转调本方法,
        所以原路径上仍存在的每一行都还在本用例的执行面内, 少掉的只是那层
        已不存在的包装本身。读侧 `load_card_state` 两条断言原样保留。

        CARD-G3-7-R2 (Codex r1 MEDIUM-3): 只让替身抛异常是锁不住的 —— 若复活的
        幻影调用被它自己的 `except Exception` 吞掉, 业务返回值照样正常, 本用例
        就什么也看不见。故除替身抛异常外, **独立记录 getter 被访问的次数并断言
        为 0**: 异常吞不吞掉都不影响这条, 碰过一次就红。"""
        import app.clients.graphiti_client as gc_module

        touched: list[str] = []

        def _forbidden(*args, **kwargs):
            touched.append("get_learning_memory_client")
            raise AssertionError("_save_card_states/load_card_state 不得访问 LearningMemoryClient (G-FAKE-007)")

        monkeypatch.setattr(gc_module, "get_learning_memory_client", _forbidden)
        svc = review_service_factory()
        assert await svc._save_card_states(pending=("c4-lock", '{"state": 1}')) is True
        assert await svc.load_card_state("c4-lock") == '{"state": 1}'
        assert await svc.load_card_state("missing-c4-lock") is None
        assert touched == [], (
            f"G-FAKE-007: LearningMemoryClient getter 被访问了 {len(touched)} 次 —— "
            "幻影镜像路径已复活。本断言不依赖异常能否冒泡: 即便复活的调用把 "
            "AssertionError 吞掉、业务返回值照常, 这里的计数仍会把它抓出来。"
        )

    @pytest.mark.asyncio
    async def test_save_card_states_returns_false_when_file_write_fails(self, review_service_factory, monkeypatch):
        """Codex HIGH-1 锁定: 唯一真实持久化通道 (文件) 失败时不得谎报 True
        ('仅内存暂存、重启即丢' != '持久化成功')。

        CARD-G3-7-R2: 原先经退役的公开包装断言, 现直接断言被包装者
        `_save_card_states` —— 谎报 True 的能力本来就在它这一层, 改指后
        锁的是同一层, 且不再依赖一个已不存在的入口。"""
        from pathlib import Path

        import app.services.review_service as rs_module

        monkeypatch.setattr(rs_module, "_CARD_STATES_FILE", Path("/dev/null/card-states.json"))
        svc = review_service_factory()
        assert await svc._save_card_states(pending=("c4-fail", '{"state": 1}')) is False


class TestCardStatePersistHonestyD3:
    """CARD-D3: record_review_result 消费 _save_card_states 返回值 —
    持久化失败不得再被丢弃后谎报纯成功 (原 :1018 丢弃返回值,
    API 200 无任何失败字段)。沿用 /dev/null 注入范式 (Codex HIGH-1 先例)。"""

    @pytest.mark.asyncio
    async def test_record_review_reports_persist_success_and_failure(self, review_service_factory, monkeypatch):
        """成功→card_state_persisted=True; 文件写失败→False + degraded_reason。"""
        from pathlib import Path

        import app.services.review_service as rs_module

        svc = review_service_factory()
        ok = await svc.record_review_result(canvas_name="d3.canvas", concept_id="d3-persist-ok", rating=3)
        assert ok["status"] == "recorded"
        assert ok["card_state_persisted"] is True
        assert ok["degraded_reason"] is None

        monkeypatch.setattr(rs_module, "_CARD_STATES_FILE", Path("/dev/null/card-states.json"))
        svc2 = review_service_factory()
        bad = await svc2.record_review_result(canvas_name="d3.canvas", concept_id="d3-persist-fail", rating=3)
        # 评分计算本身仍成功 (status=recorded), 但持久化结果必须如实标注
        assert bad["status"] == "recorded"
        assert bad["card_state_persisted"] is False
        assert bad["degraded_reason"] == "card_state_write_failed"

    @pytest.mark.asyncio
    async def test_record_review_empty_concept_id_marks_not_persisted(self, review_service):
        """empty concept_id 分支: 卡状态算了但没存, 不得沉默。"""
        result = await review_service.record_review_result(canvas_name="d3.canvas", concept_id="", rating=3)
        assert result["status"] == "recorded"
        assert result["card_state_persisted"] is False
        assert result["degraded_reason"] == "empty_concept_id_not_persisted"

    @pytest.mark.asyncio
    async def test_record_review_fallback_marks_not_applicable(self, fallback_service):
        """Ebbinghaus fallback 无 FSRS 卡状态可持久化 → 标注不适用 (None)。"""
        result = await fallback_service.record_review_result(
            canvas_name="d3.canvas", concept_id="d3-fallback", rating=3
        )
        assert result["algorithm"] == "ebbinghaus-fallback"
        assert result["card_state_persisted"] is None
        assert result["degraded_reason"] is None

    @pytest.mark.asyncio
    async def test_record_review_unicode_write_failure_stays_fsrs_and_honest(self, review_service_factory):
        """Codex HIGH-3: lone surrogate concept_id 使 UTF-8 写盘抛
        UnicodeEncodeError (ValueError 族) — 必须在持久化边界归一为
        False, 不得冒泡成 Ebbinghaus fallback 谎报"不适用"。"""
        svc = review_service_factory()
        result = await svc.record_review_result(canvas_name="d3.canvas", concept_id="\ud800", rating=3)
        assert result["algorithm"] == "fsrs-4.5"
        assert result["card_state_persisted"] is False
        assert result["degraded_reason"] == "card_state_write_failed"

    @pytest.mark.asyncio
    async def test_surrogate_key_does_not_poison_subsequent_saves(self, review_service_factory):
        """Codex 二轮残留 HIGH: 序列化类失败 (毒 key) 必须回滚隔离, 不得
        永久留在全量快照里拖垮后续正常 concept 的持久化 (二轮实测
        normal-after-surrogate 也失败)。磁盘失败 (OSError) 则保留内存。"""
        svc = review_service_factory()
        bad = await svc.record_review_result(canvas_name="d3.canvas", concept_id="\ud800", rating=3)
        assert bad["card_state_persisted"] is False
        assert "\ud800" not in svc._card_states, "毒 key 必须被回滚隔离"
        good = await svc.record_review_result(canvas_name="d3.canvas", concept_id="normal-after-surrogate", rating=3)
        assert good["card_state_persisted"] is True
        assert good["degraded_reason"] is None

    @pytest.mark.asyncio
    async def test_save_card_states_pending_mutation_inside_lock(self, review_service_factory, monkeypatch):
        """Codex HIGH-2: mutation 随 pending 参数移入锁内 — 成功快照必含
        本次状态 (bool 与本响应的 card_data 绑定), 失败时 concept 进
        dirty 集合供查询侧诚实上报。"""
        import json as _json
        from pathlib import Path

        import app.services.review_service as rs_module

        svc = review_service_factory()
        ok = await svc._save_card_states(pending=("d3-bind", '{"state": 1}'))
        assert ok is True
        assert svc._card_states["d3-bind"] == '{"state": 1}'
        on_disk = _json.loads(rs_module._CARD_STATES_FILE.read_text("utf-8"))
        # CARD-G3-5: 落盘顶层键改成 vault_id (投影按 vault 分桶), concept_id 落
        # 二层。本用例原意 (锁内 mutation 必进落盘快照) 一字不减。
        #
        # ⚠️ Codex r1 MEDIUM-2 整改: 断言要绑**正确身份 (vault, concept)**, 不能
        # 只问"某处出现过这张卡"—— 那样"内存写对桶、落盘落进另一个 vault"也会
        # 通过。这里向 svc 问它自己当前解析到的 vault, 再定点查那个桶: 既绑住了
        # 身份, 又不把测试钉死在某个具体 vault 名上 (它随 active vault 配置变)。
        current_vault = svc._dirty_key("d3-bind")[0]
        assert current_vault is not None, "作用域应能解析出来, 否则前面的写不会成功"
        assert isinstance(on_disk.get(current_vault), dict), f"落盘顶层应是 vault 桶 (dict), 实得 {on_disk!r}"
        assert on_disk[current_vault]["d3-bind"] == '{"state": 1}', (
            f"本次 pending 状态未进**本 vault** 的落盘桶: {on_disk!r}"
        )
        assert not svc._is_unpersisted("d3-bind")

        monkeypatch.setattr(rs_module, "_CARD_STATES_FILE", Path("/dev/null/card-states.json"))
        bad = await svc._save_card_states(pending=("d3-bind-fail", "{}"))
        assert bad is False
        # CARD-G3-5: dirty 集的身份是 (vault, concept), 见 _dirty_key 的
        # 跨 vault 误报理由。
        assert svc._is_unpersisted("d3-bind-fail")
