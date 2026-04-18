"""Story 1.1 Task 2: Templater template validation tests.

Verifies concept.md and exam-board.md templates contain
all required frontmatter fields per AC #4, #5, #6.
"""

from pathlib import Path

import pytest

TEMPLATES_DIR = (
    Path(__file__).resolve().parents[3] / "canvas-vault" / ".obsidian" / "templates"
)


class TestConceptTemplate:
    """Task 2: concept.md template fields (AC #4, #6)."""

    def test_template_exists(self):
        assert (TEMPLATES_DIR / "concept.md").exists(), "concept.md template must exist"

    def test_has_mastery_score(self):
        content = (TEMPLATES_DIR / "concept.md").read_text()
        assert "mastery_score:" in content

    def test_has_bkt_params(self):
        content = (TEMPLATES_DIR / "concept.md").read_text()
        assert "bkt_p_mastery:" in content

    def test_has_fsrs_params(self):
        content = (TEMPLATES_DIR / "concept.md").read_text()
        assert "fsrs_stability:" in content
        assert "fsrs_difficulty:" in content

    def test_has_errors_and_tips(self):
        content = (TEMPLATES_DIR / "concept.md").read_text()
        assert "errors:" in content
        assert "tips:" in content

    def test_has_relationships_field(self):
        content = (TEMPLATES_DIR / "concept.md").read_text()
        assert "relationships:" in content

    def test_has_review_fields(self):
        content = (TEMPLATES_DIR / "concept.md").read_text()
        assert "lastReview:" in content
        assert "nextReview:" in content
        assert "reviewLevel:" in content

    def test_has_timestamps(self):
        content = (TEMPLATES_DIR / "concept.md").read_text()
        assert "created_at:" in content
        assert "updated_at:" in content

    def test_mastery_score_initial_value(self):
        content = (TEMPLATES_DIR / "concept.md").read_text()
        assert "mastery_score: 0" in content


class TestExamBoardTemplate:
    """Task 2: exam-board.md template fields (AC #5)."""

    def test_template_exists(self):
        assert (TEMPLATES_DIR / "exam-board.md").exists(), (
            "exam-board.md template must exist"
        )

    def test_has_type_field(self):
        content = (TEMPLATES_DIR / "exam-board.md").read_text()
        assert "type: exam_board" in content

    def test_has_source_canvas(self):
        content = (TEMPLATES_DIR / "exam-board.md").read_text()
        assert "source_canvas:" in content

    def test_has_selected_nodes(self):
        content = (TEMPLATES_DIR / "exam-board.md").read_text()
        assert "selected_nodes:" in content

    def test_has_questions(self):
        content = (TEMPLATES_DIR / "exam-board.md").read_text()
        assert "questions:" in content

    def test_has_score_summary(self):
        content = (TEMPLATES_DIR / "exam-board.md").read_text()
        assert "score_summary:" in content
