"""
单元测试 - Story 2.9: 增强智能建议引擎

Story 2.9: 评分结果影响Agent调用策略

测试场景:
1. 维度分析识别最弱维度
2. 准确性低推荐oral-explanation/clarification-path
3. 高分(≥80)推荐进入下一阶段
4. 低分(<60)推荐clarification-path
5. 黄色节点为空提示填写
6. 建议包含清晰的推荐理由
7. 边界情况:4个维度得分相同

Author: Dev Agent (James)
Created: 2025-10-15
Reviewed & Refactored: Quinn (QA Agent)
"""

from typing import Any, Dict

import pytest

# ========== Constants ==========

# Dimension to Agent mapping (extracted to avoid duplication)
DIMENSION_TO_AGENTS = {
    "accuracy": {
        "agents": ["clarification-path", "oral-explanation"],
        "reason": "通过详细解释纠正理解偏差",
    },
    "imagery": {
        "agents": ["memory-anchor", "comparison-table"],
        "reason": "通过生动类比加深记忆",
    },
    "completeness": {
        "agents": ["clarification-path", "four-level-answer"],
        "reason": "填补知识盲区,覆盖完整知识点",
    },
    "originality": {
        "agents": ["oral-explanation", "memory-anchor"],
        "reason": "引导用自己的语言表达",
    },
}

# Dimension names in Chinese
DIMENSION_NAMES = {
    "accuracy": "准确性",
    "imagery": "形象性",
    "completeness": "完整性",
    "originality": "原创性",
}


# ========== 增强版智能建议引擎实现 ==========


def generate_enhanced_intelligent_suggestion(
    score_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    基于评分结果生成个性化建议(增强版)

    这是canvas-orchestrator.md中Section 2.5.3定义的增强版建议生成算法的Python实现。

    Args:
        score_result: {
            "total_score": int (0-100),
            "breakdown": {
                "accuracy": int (0-25),
                "imagery": int (0-25),
                "completeness": int (0-25),
                "originality": int (0-25)
            },
            "pass": bool,
            "feedback": str
        }

    Returns:
        Dict[str, Any]: {
            "suggestion_text": str (markdown formatted),
            "recommended_agent": str or None,
            "reasoning": str,
            "options": List[str] (A/B/C/D)
        }
    """
    total = score_result["total_score"]
    breakdown = score_result["breakdown"]

    # 档位1: ≥80分
    if total >= 80:
        return {
            "suggestion_text": "理解良好!(≥80分)\n\n建议:\nA. 继续拆解更深层次\nB. 进入无纸化检验阶段\nC. 继续原计划",
            "recommended_agent": None,
            "reasoning": "您的理解已达标,可以进入下一学习阶段。",
            "options": ["A", "B", "C"],
        }

    # 档位2: 60-79分 - 维度导向
    elif 60 <= total < 80:
        # 识别最弱的维度
        sorted_dimensions = sorted(breakdown.items(), key=lambda x: x[1])
        weakest_dim = sorted_dimensions[0][0]
        weakest_score = sorted_dimensions[0][1]

        # 使用模块级常量而非重复定义
        recommendation = DIMENSION_TO_AGENTS[weakest_dim]
        recommended_agent = recommendation["agents"][0]

        # 格式化维度分析
        analysis_lines = []
        for dim, score in breakdown.items():
            indicator = (
                "⚠️ (最弱)" if dim == weakest_dim else ("✅" if score >= 20 else "")
            )
            analysis_lines.append(f"- {DIMENSION_NAMES[dim]}: {score}/25 {indicator}")
        analysis = "\n".join(analysis_lines)

        suggestion_text = f"""您的理解得分{total}分,基本正确但存在盲区。

分析:
{analysis}

建议:
A. 使用{recommended_agent} Agent,{recommendation["reason"]}
B. 继续原计划操作
C. 取消操作

推荐理由:您的{DIMENSION_NAMES[weakest_dim]}得分{weakest_score}/25,{recommendation["reason"]}能帮助您提升这个维度。"""

        return {
            "suggestion_text": suggestion_text,
            "recommended_agent": recommended_agent,
            "reasoning": f"{DIMENSION_NAMES[weakest_dim]}较弱,需要针对性提升",
            "options": ["A", "B", "C"],
        }

    # 档位3: <60分
    else:
        return {
            "suggestion_text": """理解存在明显问题(<60分)

建议:
A. 使用clarification-path Agent(最详细解释)
B. 使用oral-explanation Agent(通俗解释)
C. 继续原计划
D. 取消操作

推荐理由:您的理解有基础性错误,需要详细的重新解释。建议从澄清路径开始,它会提供最完整的4步骤解释。""",
            "recommended_agent": "clarification-path",
            "reasoning": "理解有基础性错误,需要最详细的解释",
            "options": ["A", "B", "C", "D"],
        }


def handle_empty_yellow_node() -> Dict[str, Any]:
    """处理黄色节点为空的情况

    Returns:
        Dict[str, Any]: 包含建议文本、推荐Agent(None)、理由和选项列表
    """
    return {
        "suggestion_text": """请先填写个人理解,输出是学习的关键

选项:
A. 返回填写个人理解(推荐)
B. 继续原操作(不推荐,可能影响学习效果)

💡 提示:费曼学习法的核心是输出。只有尝试用自己的语言解释,才能发现理解盲区。""",
        "recommended_agent": None,
        "reasoning": "输出是最好的学习",
        "options": ["A", "B"],
    }


# ========== 测试用例 ==========


def test_dimension_analysis_identifies_weakest():
    """
    Story 2.9 - Test Case 1
    场景:评分breakdown中形象性最低

    预期:
    1. 正确识别形象性为最弱维度
    2. 推荐memory-anchor或comparison-table
    3. 建议理由提到"形象性"
    """
    score_result = {
        "total_score": 72,
        "breakdown": {
            "accuracy": 21,
            "imagery": 14,  # 最弱
            "completeness": 20,
            "originality": 17,
        },
        "pass": False,
        "feedback": "基本正确但形象性较弱",
    }

    suggestion = generate_enhanced_intelligent_suggestion(score_result)

    assert suggestion["recommended_agent"] in ["memory-anchor", "comparison-table"], (
        f"应该推荐memory-anchor或comparison-table,实际推荐: {suggestion['recommended_agent']}"
    )
    assert "形象性" in suggestion["reasoning"], (
        f"建议理由应该提到'形象性',实际: {suggestion['reasoning']}"
    )
    assert "14/25" in suggestion["suggestion_text"], (
        f"建议文本应该包含最弱维度得分'14/25',实际: {suggestion['suggestion_text']}"
    )
    print(f"✅ 测试通过: 形象性最弱 → 推荐 {suggestion['recommended_agent']}")


def test_low_accuracy_recommends_explanation():
    """
    Story 2.9 - Test Case 2
    场景:准确性得分最低(12/25)

    预期:推荐oral-explanation或clarification-path
    """
    score_result = {
        "total_score": 65,
        "breakdown": {
            "accuracy": 12,  # 最弱
            "imagery": 18,
            "completeness": 19,
            "originality": 16,
        },
        "pass": False,
        "feedback": "准确性较弱",
    }

    suggestion = generate_enhanced_intelligent_suggestion(score_result)

    assert suggestion["recommended_agent"] in [
        "oral-explanation",
        "clarification-path",
    ], (
        f"应该推荐oral-explanation或clarification-path,实际推荐: {suggestion['recommended_agent']}"
    )
    assert "准确性" in suggestion["reasoning"], (
        f"建议理由应该提到'准确性',实际: {suggestion['reasoning']}"
    )
    print(f"✅ 测试通过: 准确性最弱 → 推荐 {suggestion['recommended_agent']}")


def test_high_score_recommends_next_stage():
    """
    Story 2.9 - Test Case 3
    场景:总分85分(≥80)

    预期:
    1. 不推荐补充解释Agent
    2. 建议继续拆解或进入检验阶段
    """
    score_result = {
        "total_score": 85,
        "breakdown": {
            "accuracy": 22,
            "imagery": 21,
            "completeness": 23,
            "originality": 19,
        },
        "pass": True,
        "feedback": "理解良好",
    }

    suggestion = generate_enhanced_intelligent_suggestion(score_result)

    assert suggestion["recommended_agent"] is None, (
        f"高分(≥80)不应推荐补充解释Agent,实际推荐: {suggestion['recommended_agent']}"
    )
    assert (
        "继续拆解" in suggestion["suggestion_text"]
        or "检验阶段" in suggestion["suggestion_text"]
    ), f"应该建议继续拆解或检验阶段,实际: {suggestion['suggestion_text']}"
    print("✅ 测试通过: 85分(≥80) → 不推荐补充Agent,建议进入下一阶段")


def test_low_score_recommends_detailed_explanation():
    """
    Story 2.9 - Test Case 4
    场景:总分45分(<60)

    预期:推荐clarification-path(最详细解释)
    """
    score_result = {
        "total_score": 45,
        "breakdown": {
            "accuracy": 10,
            "imagery": 12,
            "completeness": 11,
            "originality": 12,
        },
        "pass": False,
        "feedback": "理解存在明显问题",
    }

    suggestion = generate_enhanced_intelligent_suggestion(score_result)

    assert suggestion["recommended_agent"] == "clarification-path", (
        f"低分(<60)应该推荐clarification-path,实际推荐: {suggestion['recommended_agent']}"
    )
    assert (
        "详细" in suggestion["reasoning"] or "基础性错误" in suggestion["reasoning"]
    ), f"建议理由应该提到'详细'或'基础性错误',实际: {suggestion['reasoning']}"
    print("✅ 测试通过: 45分(<60) → 推荐 clarification-path")


def test_empty_yellow_node_suggestion():
    """
    Story 2.9 - Test Case 5
    场景:黄色节点为空,用户请求继续操作

    预期:
    1. 提示填写个人理解
    2. 提供"返回填写"和"继续"两个选项
    3. 强调输出的重要性
    """
    suggestion = handle_empty_yellow_node()

    assert "填写个人理解" in suggestion["suggestion_text"], (
        f"应该提示填写个人理解,实际: {suggestion['suggestion_text']}"
    )
    assert "输出" in suggestion["reasoning"], (
        f"建议理由应该强调'输出',实际: {suggestion['reasoning']}"
    )
    assert len(suggestion["options"]) == 2, (
        f"应该提供2个选项(A和B),实际: {len(suggestion['options'])}个"
    )
    assert "费曼学习法" in suggestion["suggestion_text"], (
        f"应该提到费曼学习法,实际: {suggestion['suggestion_text']}"
    )
    print("✅ 测试通过: 黄色节点为空 → 提示填写理解,强调输出重要性")


def test_suggestion_includes_clear_reasoning():
    """
    Story 2.9 - Test Case 6
    场景:任何60-79分的评分

    预期:
    1. 建议文本包含"推荐理由"部分
    2. 理由明确说明为什么推荐该Agent
    3. 理由关联到具体的维度得分
    """
    score_result = {
        "total_score": 68,
        "breakdown": {
            "accuracy": 18,
            "imagery": 14,  # 最弱
            "completeness": 19,
            "originality": 17,
        },
        "pass": False,
        "feedback": "形象性较弱",
    }

    suggestion = generate_enhanced_intelligent_suggestion(score_result)

    assert "推荐理由" in suggestion["suggestion_text"], (
        f"建议文本应该包含'推荐理由'部分,实际: {suggestion['suggestion_text']}"
    )
    assert (
        "14/25" in suggestion["suggestion_text"] or "形象性" in suggestion["reasoning"]
    ), f"建议应该关联到具体的维度得分,实际: {suggestion['suggestion_text']}"
    print("✅ 测试通过: 建议包含清晰的推荐理由,关联到最弱维度得分")


def test_tied_dimensions():
    """
    Story 2.9 - Test Case 7
    场景:4个维度得分完全相同

    预期:
    1. 不崩溃
    2. 推荐任意合理的Agent
    3. 建议文本合理
    """
    score_result = {
        "total_score": 64,
        "breakdown": {
            "accuracy": 16,
            "imagery": 16,
            "completeness": 16,
            "originality": 16,
        },
        "pass": False,
        "feedback": "各维度均衡但得分不高",
    }

    suggestion = generate_enhanced_intelligent_suggestion(score_result)

    assert suggestion["recommended_agent"] is not None, (
        "即使维度得分相同,也应该推荐一个Agent"
    )
    assert len(suggestion["options"]) >= 2, (
        f"应该提供至少2个选项,实际: {len(suggestion['options'])}个"
    )
    assert "建议" in suggestion["suggestion_text"], (
        f"建议文本应该合理,实际: {suggestion['suggestion_text']}"
    )
    print(
        f"✅ 测试通过: 4维度得分相同(16/25) → 推荐 {suggestion['recommended_agent']},不崩溃"
    )


def test_completeness_weakness_recommends_clarification_path():
    """
    Story 2.9 - Additional Test
    场景:完整性得分最低

    预期:推荐clarification-path或four-level-answer
    """
    score_result = {
        "total_score": 66,
        "breakdown": {
            "accuracy": 19,
            "imagery": 18,
            "completeness": 13,  # 最弱
            "originality": 16,
        },
        "pass": False,
        "feedback": "完整性较弱",
    }

    suggestion = generate_enhanced_intelligent_suggestion(score_result)

    assert suggestion["recommended_agent"] in [
        "clarification-path",
        "four-level-answer",
    ], (
        f"完整性最弱应该推荐clarification-path或four-level-answer,实际推荐: {suggestion['recommended_agent']}"
    )
    assert "完整性" in suggestion["reasoning"], (
        f"建议理由应该提到'完整性',实际: {suggestion['reasoning']}"
    )
    print(f"✅ 测试通过: 完整性最弱 → 推荐 {suggestion['recommended_agent']}")


def test_originality_weakness_recommends_oral_explanation():
    """
    Story 2.9 - Additional Test
    场景:原创性得分最低

    预期:推荐oral-explanation或memory-anchor
    """
    score_result = {
        "total_score": 70,
        "breakdown": {
            "accuracy": 20,
            "imagery": 19,
            "completeness": 18,
            "originality": 13,  # 最弱
        },
        "pass": False,
        "feedback": "原创性较弱",
    }

    suggestion = generate_enhanced_intelligent_suggestion(score_result)

    assert suggestion["recommended_agent"] in ["oral-explanation", "memory-anchor"], (
        f"原创性最弱应该推荐oral-explanation或memory-anchor,实际推荐: {suggestion['recommended_agent']}"
    )
    assert "原创性" in suggestion["reasoning"], (
        f"建议理由应该提到'原创性',实际: {suggestion['reasoning']}"
    )
    print(f"✅ 测试通过: 原创性最弱 → 推荐 {suggestion['recommended_agent']}")


# ========== 运行所有测试 ==========

if __name__ == "__main__":
    print("=" * 60)
    print("Story 2.9: 增强智能建议引擎 - 单元测试")
    print("=" * 60)
    print()

    # 运行pytest
    pytest.main([__file__, "-v", "--tb=short"])
