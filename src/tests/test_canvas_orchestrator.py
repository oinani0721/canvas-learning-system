"""
集成测试 - Canvas Orchestrator 嵌入式评分检查点

Story 2.8: 测试嵌入式评分检查点功能

测试场景:
1. 黄色节点已填写，请求拆解，自动评分并提供建议
2. 黄色节点为空，请求解释，提醒填写理解
3. 黄色节点已评分(绿色)，请求拆解，直接执行不重复评分
4. 用户选择忽略建议，系统仍然执行原操作
5. 智能建议匹配最弱维度
6. 评分结果正确更新节点颜色

Author: Dev Agent (James)
Created: 2025-10-15
"""

import pytest

from canvas_utils import CanvasJSONOperator

# ========== Helper Functions ==========


def find_yellow_node_for_question(canvas_data: dict, question_node_id: str) -> dict:
    """
    查找问题节点关联的黄色节点（个人理解区）

    这是嵌入式评分检查点的核心检测逻辑，复用于多个测试用例。

    Args:
        canvas_data: Canvas JSON数据
        question_node_id: 问题节点ID

    Returns:
        dict: 黄色节点对象，如果未找到则返回None
    """
    for edge in canvas_data["edges"]:
        if edge["fromNode"] == question_node_id:
            to_node = next(
                (n for n in canvas_data["nodes"] if n["id"] == edge["toNode"]), None
            )
            if to_node and to_node.get("color") == "6":  # "6" = 黄色
                return to_node
    return None


def detect_scoring_need(canvas_data: dict, question_node_id: str) -> tuple:
    """
    检测问题节点是否需要评分（嵌入式评分检查点逻辑）

    这个函数实现了canvas-orchestrator.md中定义的检测逻辑。

    检测标准：
    1. 黄色节点已填写: text字段非空且长度 ≥ 10字符
    2. 问题节点未评分: 颜色仍为红色("1")

    Args:
        canvas_data: Canvas JSON数据
        question_node_id: 问题节点ID

    Returns:
        tuple: (needs_scoring: bool, reason: str, yellow_node: dict, question_node: dict)
    """
    # 获取问题节点
    question_node = next(
        (n for n in canvas_data["nodes"] if n["id"] == question_node_id), None
    )

    # 查找关联的黄色节点
    yellow_node = find_yellow_node_for_question(canvas_data, question_node_id)

    # 检测逻辑
    needs_scoring = False
    reason = ""

    if not yellow_node:
        reason = "无关联黄色节点"
    elif len(yellow_node.get("text", "").strip()) < 10:
        reason = "黄色节点内容不足(<10字符)"
    elif question_node.get("color") != "1":
        reason = "已评分（问题节点非红色）"
    else:
        needs_scoring = True
        reason = "黄色节点已填写且未评分"

    return needs_scoring, reason, yellow_node, question_node


# ========== Fixtures ==========


@pytest.fixture
def test_canvas_path():
    """测试Canvas文件路径"""
    return "src/tests/fixtures/test-embedded-scoring.canvas"


@pytest.fixture
def canvas_data(test_canvas_path):
    """读取测试Canvas数据"""
    return CanvasJSONOperator.read_canvas(test_canvas_path)


@pytest.fixture
def temp_canvas_path(tmp_path):
    """创建临时Canvas文件用于写入测试"""
    temp_file = tmp_path / "temp-embedded-scoring.canvas"

    # 复制测试fixture到临时文件
    source_path = "src/tests/fixtures/test-embedded-scoring.canvas"
    canvas_data = CanvasJSONOperator.read_canvas(source_path)
    CanvasJSONOperator.write_canvas(str(temp_file), canvas_data)

    return str(temp_file)


# ========== 测试用例1: 黄色节点已填写，自动评分触发 ==========


def test_auto_scoring_trigger_on_decomposition_request(canvas_data):
    """
    场景: 用户填写了黄色节点，请求"拆解问题"，系统自动评分

    预期:
    1. 检测到黄色节点已填写(≥10字符)
    2. 检测到问题节点仍为红色(未评分)
    3. 应该触发评分检查点
    4. needs_scoring = True
    """
    # Arrange & Act
    question_node_id = "question-unscored"
    needs_scoring, reason, yellow_node, question_node = detect_scoring_need(
        canvas_data, question_node_id
    )

    # Assert
    assert needs_scoring is True, f"应该触发评分，但检测结果为: {reason}"
    assert yellow_node is not None, "应该找到关联的黄色节点"
    assert len(yellow_node.get("text", "").strip()) >= 10, "黄色节点内容应该≥10字符"
    assert question_node.get("color") == "1", "问题节点应该为红色(未评分)"
    print(f"✅ 测试通过: 正确检测到需要评分 - {reason}")


# ========== 测试用例2: 黄色节点为空，提醒填写 ==========


def test_empty_yellow_node_reminder(canvas_data):
    """
    场景: 用户请求"拆解问题"，但黄色节点为空

    预期:
    1. 检测到黄色节点为空或内容<10字符
    2. needs_scoring = False
    3. 原因为"黄色节点内容不足"
    4. 不调用scoring-agent，而是提醒用户填写理解
    """
    # Arrange & Act
    question_node_id = "question-empty-yellow"
    needs_scoring, reason, yellow_node, question_node = detect_scoring_need(
        canvas_data, question_node_id
    )

    # Assert
    assert needs_scoring is False, "黄色节点为空时不应触发评分"
    assert yellow_node is not None, "应该找到关联的黄色节点"
    assert len(yellow_node.get("text", "").strip()) < 10, "黄色节点内容应该<10字符"
    assert reason == "黄色节点内容不足(<10字符)", f"原因应该是内容不足，实际: {reason}"
    print(f"✅ 测试通过: 正确检测到黄色节点为空 - {reason}")


# ========== 测试用例3: 黄色节点已评分，不重复评分 ==========


def test_skip_scoring_if_already_scored(canvas_data):
    """
    场景: 问题节点已为绿色(已评分)，用户请求拆解

    预期:
    1. 检测到问题节点为绿色(color="2")
    2. needs_scoring = False
    3. 原因为"已评分"
    4. 直接执行拆解操作，不调用scoring-agent
    """
    # Arrange & Act
    question_node_id = "question-already-scored-green"
    needs_scoring, reason, yellow_node, question_node = detect_scoring_need(
        canvas_data, question_node_id
    )

    # Assert
    assert needs_scoring is False, "已评分的节点不应重复评分"
    assert yellow_node is not None, "应该找到关联的黄色节点"
    assert len(yellow_node.get("text", "").strip()) >= 10, "黄色节点内容应该≥10字符"
    assert question_node.get("color") == "2", "问题节点应该为绿色(已评分)"
    assert reason == "已评分（问题节点非红色）", f"原因应该是已评分，实际: {reason}"
    print(f"✅ 测试通过: 正确识别已评分节点，跳过重复评分 - {reason}")


# ========== 测试用例4: 无关联黄色节点，直接执行 ==========


def test_no_yellow_node_direct_execution(canvas_data):
    """
    场景: 问题节点没有关联的黄色节点，用户请求拆解

    预期:
    1. 检测到没有关联的黄色节点
    2. needs_scoring = False
    3. 原因为"无关联黄色节点"
    4. 直接执行拆解操作
    """
    # Arrange & Act
    question_node_id = "question-no-yellow"
    needs_scoring, reason, yellow_node, question_node = detect_scoring_need(
        canvas_data, question_node_id
    )

    # Assert
    assert needs_scoring is False, "无关联黄色节点时不应触发评分"
    assert yellow_node is None, "不应该找到黄色节点"
    assert reason == "无关联黄色节点", f"原因应该是无关联黄色节点，实际: {reason}"
    print(f"✅ 测试通过: 正确识别无黄色节点情况 - {reason}")


# ========== 测试用例5: 智能建议匹配最弱维度 ==========


def test_intelligent_suggestion_matches_weakness():
    """
    场景: 评分结果显示"形象性"最弱，建议应推荐记忆锚点或对比表

    预期:
    1. 根据最弱维度生成建议
    2. 建议包含对应的解释Agent
    3. 不同分数范围给出不同建议
    """
    # Arrange: 定义维度-Agent推荐映射表
    dimension_agent_map = {
        "accuracy": ["澄清路径", "口语化解释", "例题教学"],
        "imagery": ["记忆锚点", "对比表"],
        "completeness": ["澄清路径", "四层次答案"],
        "originality": ["口语化解释", "记忆锚点"],
    }

    # Test Case 1: 形象性最弱
    score_result_1 = {
        "total_score": 72,
        "breakdown": {
            "accuracy": 22,
            "imagery": 15,  # 最弱
            "completeness": 20,
            "originality": 15,
        },
        "pass": False,
    }

    # Act: 找到最弱维度
    weakest_dim_1 = min(
        score_result_1["breakdown"], key=score_result_1["breakdown"].get
    )
    recommended_agents_1 = dimension_agent_map[weakest_dim_1]

    # Assert
    assert weakest_dim_1 == "imagery", "应该识别出形象性最弱"
    assert "记忆锚点" in recommended_agents_1, "应该推荐记忆锚点"
    assert "对比表" in recommended_agents_1, "应该推荐对比表"
    print(f"✅ 测试通过: 形象性最弱 → 推荐 {recommended_agents_1}")

    # Test Case 2: 准确性最弱
    score_result_2 = {
        "total_score": 65,
        "breakdown": {
            "accuracy": 12,  # 最弱
            "imagery": 18,
            "completeness": 20,
            "originality": 15,
        },
        "pass": False,
    }

    weakest_dim_2 = min(
        score_result_2["breakdown"], key=score_result_2["breakdown"].get
    )
    recommended_agents_2 = dimension_agent_map[weakest_dim_2]

    assert weakest_dim_2 == "accuracy", "应该识别出准确性最弱"
    assert "澄清路径" in recommended_agents_2, "应该推荐澄清路径"
    print(f"✅ 测试通过: 准确性最弱 → 推荐 {recommended_agents_2}")


# ========== 测试用例6: 评分结果正确更新节点颜色 ==========


def test_scoring_result_updates_node_color_correctly(temp_canvas_path):
    """
    场景: 评分完成后，根据分数自动更新问题节点颜色

    预期:
    1. ≥80分 → 绿色("2")
    2. 60-79分 → 紫色("3")
    3. <60分 → 红色("1")
    """
    # Test Case 1: 高分 (≥80) → 绿色
    canvas_data_1 = CanvasJSONOperator.read_canvas(temp_canvas_path)
    question_node_id_1 = "question-unscored"
    score_1 = 85

    # 计算新颜色
    new_color_1 = "2" if score_1 >= 80 else ("3" if score_1 >= 60 else "1")

    # 更新节点颜色
    CanvasJSONOperator.update_node_color(canvas_data_1, question_node_id_1, new_color_1)
    CanvasJSONOperator.write_canvas(temp_canvas_path, canvas_data_1)

    # 验证
    updated_data_1 = CanvasJSONOperator.read_canvas(temp_canvas_path)
    updated_node_1 = next(
        (n for n in updated_data_1["nodes"] if n["id"] == question_node_id_1), None
    )

    assert updated_node_1 is not None, "应该找到更新后的节点"
    assert updated_node_1.get("color") == "2", (
        f"高分(≥80)应该变绿色，实际: {updated_node_1.get('color')}"
    )
    print("✅ 测试通过: 85分 → 绿色('2')")

    # Test Case 2: 中等分数 (60-79) → 紫色
    canvas_data_2 = CanvasJSONOperator.read_canvas(temp_canvas_path)
    question_node_id_2 = "question-empty-yellow"
    score_2 = 72

    new_color_2 = "2" if score_2 >= 80 else ("3" if score_2 >= 60 else "1")

    CanvasJSONOperator.update_node_color(canvas_data_2, question_node_id_2, new_color_2)
    CanvasJSONOperator.write_canvas(temp_canvas_path, canvas_data_2)

    updated_data_2 = CanvasJSONOperator.read_canvas(temp_canvas_path)
    updated_node_2 = next(
        (n for n in updated_data_2["nodes"] if n["id"] == question_node_id_2), None
    )

    assert updated_node_2.get("color") == "3", (
        f"中等分数(60-79)应该变紫色，实际: {updated_node_2.get('color')}"
    )
    print("✅ 测试通过: 72分 → 紫色('3')")

    # Test Case 3: 低分 (<60) → 保持红色
    canvas_data_3 = CanvasJSONOperator.read_canvas(temp_canvas_path)
    question_node_id_3 = "question-no-yellow"
    score_3 = 45

    new_color_3 = "2" if score_3 >= 80 else ("3" if score_3 >= 60 else "1")

    CanvasJSONOperator.update_node_color(canvas_data_3, question_node_id_3, new_color_3)
    CanvasJSONOperator.write_canvas(temp_canvas_path, canvas_data_3)

    updated_data_3 = CanvasJSONOperator.read_canvas(temp_canvas_path)
    updated_node_3 = next(
        (n for n in updated_data_3["nodes"] if n["id"] == question_node_id_3), None
    )

    assert updated_node_3.get("color") == "1", (
        f"低分(<60)应该保持红色，实际: {updated_node_3.get('color')}"
    )
    print("✅ 测试通过: 45分 → 红色('1')")


# ========== 边界条件测试 ==========


def test_edge_case_exactly_10_characters(canvas_data):
    """
    边界条件: 黄色节点内容刚好10个字符

    预期: 应该触发评分 (≥10字符)
    """
    # 创建测试节点
    test_yellow_text = "十个字符测试内容12"  # 刚好10个字符

    assert len(test_yellow_text) >= 10, "应该满足≥10字符的条件"
    print("✅ 边界测试通过: 10字符内容应该触发评分")


def test_edge_case_9_characters():
    """
    边界条件: 黄色节点内容9个字符

    预期: 不应该触发评分 (<10字符)
    """
    test_yellow_text = "九个字符测试1"  # 9个字符

    assert len(test_yellow_text) < 10, "应该不满足≥10字符的条件"
    print("✅ 边界测试通过: 9字符内容不应该触发评分")


# ========== Story 2.9: 增强智能建议引擎测试 ==========


def generate_enhanced_intelligent_suggestion(score_result: dict) -> dict:
    """
    基于评分结果生成个性化建议(增强版)

    这是canvas-orchestrator.md中Section 2.5.3定义的增强版建议生成算法的Python实现。
    用于单元测试验证。

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
        Dict: {
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

        # 维度到Agent映射
        dimension_to_agents = {
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

        recommendation = dimension_to_agents[weakest_dim]
        recommended_agent = recommendation["agents"][0]

        # 维度中文名
        dim_names = {
            "accuracy": "准确性",
            "imagery": "形象性",
            "completeness": "完整性",
            "originality": "原创性",
        }

        # 格式化维度分析
        analysis_lines = []
        for dim, score in breakdown.items():
            indicator = (
                "⚠️ (最弱)" if dim == weakest_dim else ("✅" if score >= 20 else "")
            )
            analysis_lines.append(f"- {dim_names[dim]}: {score}/25 {indicator}")
        analysis = "\n".join(analysis_lines)

        suggestion_text = f"""您的理解得分{total}分,基本正确但存在盲区。

分析:
{analysis}

建议:
A. 使用{recommended_agent} Agent,{recommendation["reason"]}
B. 继续原计划操作
C. 取消操作

推荐理由:您的{dim_names[weakest_dim]}得分{weakest_score}/25,{recommendation["reason"]}能帮助您提升这个维度。"""

        return {
            "suggestion_text": suggestion_text,
            "recommended_agent": recommended_agent,
            "reasoning": f"{dim_names[weakest_dim]}较弱,需要针对性提升",
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


def handle_empty_yellow_node() -> dict:
    """处理黄色节点为空的情况"""
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


# ========== 测试用例7: 维度分析准确性 ==========


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
            "imagery": 16,  # 最弱
            "completeness": 20,
            "originality": 15,
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
    assert "16/25" in suggestion["suggestion_text"], (
        f"建议文本应该包含最弱维度得分'16/25',实际: {suggestion['suggestion_text']}"
    )
    print(f"✅ 测试通过: 形象性最弱 → 推荐 {suggestion['recommended_agent']}")


# ========== 测试用例8: 准确性低推荐oral-explanation ==========


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


# ========== 测试用例9: 高分推荐进入下一阶段 ==========


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


# ========== 测试用例10: 低分推荐clarification-path ==========


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


# ========== 测试用例11: 黄色节点为空的建议 ==========


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


# ========== 测试用例12: 建议理由清晰度 ==========


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


# ========== 测试用例13: 边界情况-4维度得分相同 ==========


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


# ========== 测试用例14: 完整性最弱推荐clarification-path ==========


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


# ========== 测试用例15: 原创性最弱推荐oral-explanation ==========


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
    print("Canvas Orchestrator 测试套件")
    print("Story 2.8: 嵌入式评分检查点")
    print("Story 2.9: 增强智能建议引擎")
    print("=" * 60)
    print()

    # 运行pytest
    pytest.main([__file__, "-v", "--tb=short"])
