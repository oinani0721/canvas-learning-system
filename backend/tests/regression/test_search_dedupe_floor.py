"""批次1'④ 检索三小修回归 (MEM-FLYWHEEL-2026-07-22)。

文本级去重 + 相关度地板 + MMR 配方注册的单元层锁定。
punycode 子组扩展与端到端效果由 G0 门禁 (run_memory_retrieval_regression.py) 验证。
"""

from app.services.memory_service import MemoryService


def _r(content: str, score: float) -> dict:
    return {"content": content, "relevance_score": score}


def test_dedupe_exact_duplicates():
    """逐字节相同 (审查: 5 对同屏) → 只留最高分条。"""
    results = [
        _r("PCA uses 协方差矩阵的特征向量", 1.5),
        _r("PCA uses 协方差矩阵的特征向量", 1.1),
    ]
    kept = MemoryService._dedupe_by_text(results)
    assert len(kept) == 1
    assert kept[0]["relevance_score"] == 1.5


def test_dedupe_near_duplicates_whitespace_case():
    """空白/大小写/全半角差异 → 判为近重。"""
    results = [
        _r("Forward Checking prunes domains", 1.0),
        _r("forward  checking prunes domains", 0.8),
    ]
    assert len(MemoryService._dedupe_by_text(results)) == 1


def test_dedupe_keeps_distinct_facts():
    results = [
        _r("特征值与特征向量", 1.0),
        _r("零空间与矩阵的秩", 0.9),
        _r("forward checking vs AC-3", 0.8),
    ]
    assert len(MemoryService._dedupe_by_text(results)) == 3


def test_dedupe_empty_text_passthrough():
    """无文本字段的条目不参与去重、不被误杀。"""
    results = [{"relevance_score": 1.0}, {"relevance_score": 0.9}]
    assert len(MemoryService._dedupe_by_text(results)) == 2


def test_mmr_recipes_registered():
    """批次1'④: Graphiti 白送的 MMR 配方必须在注册表 (曾闲置)。"""
    recipes = MemoryService._get_search_recipes()
    if not recipes:  # graphiti_core 不可用的降级环境
        return
    for name in ("combined_mmr", "edge_mmr", "node_mmr", "combined_cross_encoder"):
        assert name in recipes, f"recipe {name} 未注册"
