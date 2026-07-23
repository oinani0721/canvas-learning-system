"""批次4' 检索束单元锁定 (MEM-FLYWHEEL-2026-07-22)。"""

from app.core.term_aliases import expand_query


def test_zh_query_gains_en_terms():
    out = expand_query("极小极大搜索的剪枝方法")
    assert "minimax" in out
    assert "alpha-beta" in out
    assert out.startswith("极小极大搜索的剪枝方法")


def test_en_query_gains_zh_terms():
    out = expand_query("covariance matrix and its eigenvectors")
    assert "协方差" in out
    assert "特征向量" in out


def test_longest_match_wins():
    """「理性代理」整体命中, 不因子串「代理」重复扩展。"""
    out = expand_query("什么是理性代理")
    assert "rational" in out and "agent" in out
    assert out.count("agent") == 1


def test_no_hit_returns_unchanged():
    q = "今天天气怎么样"
    assert expand_query(q) == q


def test_already_present_terms_not_duplicated():
    q = "eigenvalue 特征值的意义"
    out = expand_query(q)
    assert out.lower().count("eigenvalue") == 1


def test_empty_query_safe():
    assert expand_query("") == ""
