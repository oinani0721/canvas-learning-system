"""批次4' 检索束 — 术语双语别名表 (MEM-FLYWHEEL-2026-07-22, 对账采纳)。

中英混合检索的稳态修法: 与其换 embedding 模型, 不如把 query 扩成「检索束」
(原文 + 命中术语的另一语言 + 别名) — 对「代理/agent」「极小极大/minimax」
这类短词多义与跨语场景, 束比单条 query 稳 (ChatGPT 对账裁决: 优先于任何
换模型动作)。

实现: 最小拼接式 — 命中表内术语时把对侧语言术语拼进 query, 单次查询
(BM25 多词 OR 天然支持, dense embedding 对拼接 query 稳健), 不做多路
多次检索 (延迟 ×N 不值)。

表按 vault 主题维护 (CS188 + 线代), 新学科加条目即可。
"""

from __future__ import annotations

#: 中文 → 英文术语束 (含常用别名, 空格分隔)
ZH_TO_EN: dict[str, str] = {
    "特征值": "eigenvalue",
    "特征向量": "eigenvector",
    "协方差": "covariance",
    "零空间": "null space kernel",
    "主成分": "principal component PCA",
    "矩阵": "matrix",
    "行列式": "determinant",
    "线性变换": "linear transformation",
    "极小极大": "minimax",
    "剪枝": "pruning alpha-beta",
    "值迭代": "value iteration",
    "策略迭代": "policy iteration",
    "启发函数": "heuristic",
    "启发式": "heuristic",
    "可采纳": "admissible admissibility",
    "一致性": "consistency consistent",
    "弧一致": "arc consistency AC-3",
    "约束满足": "constraint satisfaction CSP",
    "回溯": "backtracking",
    "深度优先": "depth-first DFS",
    "广度优先": "breadth-first BFS",
    "理性代理": "rational agent",
    "代理": "agent",
    "零和": "zero-sum",
    "误解": "misconception",
    "递归": "recursion",
}

#: 英文 → 中文术语束 (跨语反向: 英文 query 召回中文三元组)
EN_TO_ZH: dict[str, str] = {
    "eigenvalue": "特征值",
    "eigenvector": "特征向量",
    "covariance": "协方差",
    "null space": "零空间",
    "minimax": "极小极大",
    "pruning": "剪枝",
    "value iteration": "值迭代",
    "heuristic": "启发函数",
    "admissible": "可采纳",
    "admissibility": "可采纳",
    "consistency": "一致性",
    "arc consistency": "弧一致",
    "backtracking": "回溯",
    "agent": "代理",
    "zero-sum": "零和",
    "misconception": "误解",
    "recursion": "递归",
}


def expand_query(query: str) -> str:
    """query 命中术语表 → 拼接对侧语言术语束; 无命中原样返回。

    长词优先匹配 (「理性代理」先于「代理」), 已在 query 中的术语不重复拼。
    """
    if not query:
        return query
    additions: list[str] = []
    q_lower = query.lower()
    matched_spans: list[str] = []

    for zh, en in sorted(ZH_TO_EN.items(), key=lambda kv: -len(kv[0])):
        if zh in query and not any(zh in s for s in matched_spans):
            matched_spans.append(zh)
            for term in en.split():
                if term.lower() not in q_lower and term not in additions:
                    additions.append(term)

    for en, zh in sorted(EN_TO_ZH.items(), key=lambda kv: -len(kv[0])):
        if en in q_lower and zh not in query and zh not in additions:
            additions.append(zh)

    if not additions:
        return query
    return query + " " + " ".join(additions)
