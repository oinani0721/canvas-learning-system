"""S2-1 (V-10 fix) — 题面 registry 单元测试.

验证 generate_question 存的真实题面能被 score_answer 按 question_id 回读,
而不是漂移到节点正文。
"""

import pytest

from app.services.question_registry import (
    clear_registry,
    get_question,
    put_question,
)


@pytest.fixture(autouse=True)
def _clean_registry():
    clear_registry()
    yield
    clear_registry()


def test_put_then_get_returns_real_question_text():
    put_question("q-1", "你之前说 BST 平均 O(log n), 最坏呢?", node_id="bst")
    record = get_question("q-1")
    assert record is not None
    assert record["question_text"] == "你之前说 BST 平均 O(log n), 最坏呢?"
    assert record["node_id"] == "bst"


def test_get_missing_returns_none():
    assert get_question("does-not-exist") is None


def test_get_empty_id_returns_none():
    assert get_question("") is None


def test_put_empty_text_is_ignored():
    put_question("q-2", "")
    assert get_question("q-2") is None


def test_put_overwrites_same_id():
    put_question("q-3", "v1 题面", node_id="n")
    put_question("q-3", "v2 题面", node_id="n")
    assert get_question("q-3")["question_text"] == "v2 题面"


def test_get_returns_copy_not_live_ref():
    put_question("q-4", "原题面")
    record = get_question("q-4")
    record["question_text"] = "被外部改了"
    # registry 内部不应被污染
    assert get_question("q-4")["question_text"] == "原题面"


def test_ring_buffer_evicts_oldest():
    from app.services import question_registry

    # 填满到上限
    for i in range(question_registry._MAX_ENTRIES):
        put_question(f"q-{i}", f"题面 {i}")
    # 再加一个 → 最旧 (q-0) 应被淘汰
    put_question("q-new", "新题面")
    assert get_question("q-0") is None
    assert get_question("q-new") is not None


def test_v10_drift_scenario_real_vs_node_content():
    """V-10 核心场景: 出题用 tip 原话, 评分必须拿到这个题面, 不是节点正文."""
    tip_grounded_question = "你在 tip 里说 recursion 不用 base case, 请反驳自己"
    put_question("q-v10", tip_grounded_question, node_id="recursion")
    # 模拟 score_answer 回读
    record = get_question("q-v10")
    assert record["question_text"] == tip_grounded_question
    # 题面是 tip 引导的针对题, 而非泛泛的 "recursion" 节点正文
    assert "tip" in record["question_text"]
