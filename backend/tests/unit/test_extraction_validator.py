# Canvas Learning System - Extraction Validator Unit Tests
# Story 7.4: 出题难度匹配与提取质量验证
# [Source: _bmad-output/implementation-artifacts/7-4-difficulty-matching-extraction-validation.md]
"""
Unit tests for ExtractionValidator:
  - Record storage
  - Annotation submission
  - Paginated query with type filter
  - Accuracy statistics with per-type breakdown

[Source: Story 7.4 Task 8.2]
"""

import pytest
from app.services.extraction_validator import ExtractionValidator


@pytest.fixture
async def validator(tmp_path):
    db_path = str(tmp_path / "test_extraction.db")
    v = ExtractionValidator(db_path)
    await v._ensure_init()
    return v


# ═══════════════════════════════════════════════════════════════════════════════
# Record Storage
# ═══════════════════════════════════════════════════════════════════════════════


class TestStoreRecord:
    @pytest.mark.asyncio
    async def test_store_basic_record(self, tmp_path):
        v = ExtractionValidator(str(tmp_path / "test.db"))
        record = await v.store_record(
            source_session_id="sess_1",
            source_node_id="node_1",
            original_text="User said X about topic Y",
            extracted_content="Error: misconception about Y",
            extraction_type="error",
            extraction_subtype="reasoning",
        )
        assert record.id
        assert record.source_session_id == "sess_1"
        assert record.extraction_type == "error"
        assert record.extraction_subtype == "reasoning"
        assert record.annotation is None

    @pytest.mark.asyncio
    async def test_store_tip_record(self, tmp_path):
        v = ExtractionValidator(str(tmp_path / "test.db"))
        record = await v.store_record(
            source_session_id="sess_2",
            source_node_id="node_2",
            original_text="Important tip about...",
            extracted_content="Key insight: ...",
            extraction_type="tip",
        )
        assert record.extraction_type == "tip"
        assert record.extraction_subtype is None


# ═══════════════════════════════════════════════════════════════════════════════
# Annotation
# ═══════════════════════════════════════════════════════════════════════════════


class TestAnnotation:
    @pytest.mark.asyncio
    async def test_annotate_correct(self, tmp_path):
        v = ExtractionValidator(str(tmp_path / "test.db"))
        record = await v.store_record(
            source_session_id="s1",
            source_node_id="n1",
            original_text="orig",
            extracted_content="extracted",
            extraction_type="error",
        )
        result = await v.annotate(record.id, "correct")
        assert result is True

        # Verify via query
        page = await v.get_records()
        annotated = [r for r in page.records if r.annotation == "correct"]
        assert len(annotated) == 1

    @pytest.mark.asyncio
    async def test_annotate_incorrect(self, tmp_path):
        v = ExtractionValidator(str(tmp_path / "test.db"))
        record = await v.store_record(
            source_session_id="s1",
            source_node_id="n1",
            original_text="orig",
            extracted_content="extracted",
            extraction_type="tip",
        )
        result = await v.annotate(record.id, "incorrect")
        assert result is True

    @pytest.mark.asyncio
    async def test_annotate_partial(self, tmp_path):
        v = ExtractionValidator(str(tmp_path / "test.db"))
        record = await v.store_record(
            source_session_id="s1",
            source_node_id="n1",
            original_text="orig",
            extracted_content="extracted",
            extraction_type="key_qa",
        )
        result = await v.annotate(record.id, "partial")
        assert result is True

    @pytest.mark.asyncio
    async def test_annotate_invalid_value(self, tmp_path):
        v = ExtractionValidator(str(tmp_path / "test.db"))
        record = await v.store_record(
            source_session_id="s1",
            source_node_id="n1",
            original_text="orig",
            extracted_content="extracted",
            extraction_type="error",
        )
        with pytest.raises(ValueError, match="Invalid annotation value"):
            await v.annotate(record.id, "invalid")

    @pytest.mark.asyncio
    async def test_annotate_nonexistent_record(self, tmp_path):
        v = ExtractionValidator(str(tmp_path / "test.db"))
        await v._ensure_init()
        result = await v.annotate("nonexistent_id", "correct")
        assert result is False


# ═══════════════════════════════════════════════════════════════════════════════
# Paginated Query
# ═══════════════════════════════════════════════════════════════════════════════


class TestGetRecords:
    @pytest.mark.asyncio
    async def test_empty_query(self, tmp_path):
        v = ExtractionValidator(str(tmp_path / "test.db"))
        page = await v.get_records()
        assert page.total == 0
        assert page.records == []
        assert page.page == 1

    @pytest.mark.asyncio
    async def test_pagination(self, tmp_path):
        v = ExtractionValidator(str(tmp_path / "test.db"))
        for i in range(25):
            await v.store_record(
                source_session_id=f"s{i}",
                source_node_id=f"n{i}",
                original_text=f"orig_{i}",
                extracted_content=f"extracted_{i}",
                extraction_type="error",
            )

        page1 = await v.get_records(page=1, page_size=10)
        assert len(page1.records) == 10
        assert page1.total == 25
        assert page1.page == 1

        page3 = await v.get_records(page=3, page_size=10)
        assert len(page3.records) == 5

    @pytest.mark.asyncio
    async def test_type_filter(self, tmp_path):
        v = ExtractionValidator(str(tmp_path / "test.db"))
        await v.store_record("s1", "n1", "o1", "e1", "error")
        await v.store_record("s2", "n2", "o2", "e2", "tip")
        await v.store_record("s3", "n3", "o3", "e3", "error")

        errors = await v.get_records(extraction_type="error")
        assert errors.total == 2

        tips = await v.get_records(extraction_type="tip")
        assert tips.total == 1


# ═══════════════════════════════════════════════════════════════════════════════
# Statistics
# ═══════════════════════════════════════════════════════════════════════════════


class TestExtractionStats:
    @pytest.mark.asyncio
    async def test_stats_empty(self, tmp_path):
        v = ExtractionValidator(str(tmp_path / "test.db"))
        stats = await v.get_stats()
        assert stats.total_records == 0
        assert stats.annotated_count == 0
        assert stats.accuracy == 0.0

    @pytest.mark.asyncio
    async def test_stats_with_annotations(self, tmp_path):
        v = ExtractionValidator(str(tmp_path / "test.db"))

        # Create 5 records
        records = []
        for i in range(5):
            r = await v.store_record(
                f"s{i}",
                f"n{i}",
                f"o{i}",
                f"e{i}",
                "error" if i < 3 else "tip",
            )
            records.append(r)

        # Annotate: 3 correct, 1 incorrect
        await v.annotate(records[0].id, "correct")
        await v.annotate(records[1].id, "correct")
        await v.annotate(records[2].id, "correct")
        await v.annotate(records[3].id, "incorrect")

        stats = await v.get_stats()
        assert stats.total_records == 5
        assert stats.annotated_count == 4
        assert stats.accuracy == pytest.approx(0.75, abs=0.01)

        # Per-type breakdown
        assert "error" in stats.by_type
        assert stats.by_type["error"].total == 3
        assert stats.by_type["error"].correct == 3
        assert stats.by_type["error"].accuracy == pytest.approx(1.0, abs=0.01)

        assert "tip" in stats.by_type
        assert stats.by_type["tip"].total == 1
        assert stats.by_type["tip"].correct == 0
