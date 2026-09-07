"""CARD-PYRIGHT-DEBT-rest [BATCH-2026-09-07-第十三批] 真 bug ① 回归门。

背景: `AutoScoreResult` 的四个 rubric 维度原先写成
`Field(default_factory=RubricDimension)`, 而 `RubricDimension.score` 无默认值
⇒ 该 default 一旦被真的用到就抛 `ValidationError`, 且消息报的是**内层**字段
(`RubricDimension.score`), 把「外层漏传了哪个维度」这条信息吃掉。

处置(卡文 §一(b)③): 四维改必填 `Field(...)`。⛔ **不**给 `score` 加默认 0
—— 「评分缺失静默为 0」是语义变化, 用户未裁。

先红后绿: 改 `:144-147` 之前, 本文件 `test_missing_dimensions_names_all_four`
必红(原实现抛的是 `score` 缺失, 消息里没有四个维度名)。
"""

import pytest
from pydantic import ValidationError

from app.models.exam_models import AutoScoreResult, RubricDimension

DIMENSIONS = (
    "concept_accuracy",
    "reasoning_quality",
    "knowledge_coverage",
    "knowledge_integration",
)


def _dim(score: int = 2) -> RubricDimension:
    return RubricDimension(score=score, justification="j", low_confidence=False)


class TestRubricDimensionScoreStaysRequired:
    """`score` 必填这件事本卡不改 —— 钉住它, 防后人顺手加默认 0。"""

    def test_bare_construction_raises(self):
        with pytest.raises(ValidationError) as exc:
            RubricDimension()
        assert "score" in str(exc.value)

    def test_explicit_score_ok(self):
        assert RubricDimension(score=0).score == 0
        assert RubricDimension(score=3).score == 3


class TestAutoScoreResultDimensionsRequired:
    def test_full_construction_ok(self):
        """两个真实调用方(services/autoscore.py:141 / :197)的形态: 四维全传。"""
        r = AutoScoreResult(
            node_id="n1",
            exam_id="e1",
            question_id="q1",
            evidence_points=["p"],
            concept_accuracy=_dim(3),
            reasoning_quality=_dim(2),
            knowledge_coverage=_dim(1),
            knowledge_integration=_dim(0),
            overall_score=6,
            grade=3,
        )
        assert [getattr(r, d).score for d in DIMENSIONS] == [3, 2, 1, 0]

    def test_missing_dimensions_names_all_four(self):
        """缺四维 -> ValidationError, 且消息逐个点名四个维度字段。

        ⛔ 这是「先红后绿」那条: 修复前抛的是 `RubricDimension.score` 缺失,
        消息里一个维度名都没有。
        """
        with pytest.raises(ValidationError) as exc:
            AutoScoreResult(node_id="n1", exam_id="e1", overall_score=6, grade=3)
        msg = str(exc.value)
        missing = [d for d in DIMENSIONS if d not in msg]
        assert not missing, f"消息未点名维度: {missing}\n---\n{msg}"

    @pytest.mark.parametrize("omitted", DIMENSIONS)
    def test_each_dimension_individually_required(self, omitted):
        kwargs = {
            "node_id": "n1",
            "exam_id": "e1",
            "overall_score": 6,
            "grade": 3,
            **{d: _dim() for d in DIMENSIONS},
        }
        kwargs.pop(omitted)
        with pytest.raises(ValidationError) as exc:
            AutoScoreResult(**kwargs)
        assert omitted in str(exc.value)
