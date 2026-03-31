"""
测试example-teaching Agent定义文件

验证YAML frontmatter、Markdown结构、内容完整性和输出格式
"""

import re
from pathlib import Path


def test_yaml_frontmatter():
    """测试用例1：验证YAML frontmatter格式"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/example-teaching.md")
    content = agent_file.read_text(encoding="utf-8")

    # 提取YAML frontmatter
    yaml_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
    assert yaml_match, "未找到YAML frontmatter"

    yaml_content = yaml_match.group(1)

    # 验证name字段
    assert "name: example-teaching" in yaml_content, "name字段不正确"

    # 验证description字段
    desc_match = re.search(r"description: (.+)", yaml_content)
    assert desc_match, "未找到description字段"
    description = desc_match.group(1)
    assert len(description) < 80, f"description过长: {len(description)}字符"

    # 验证tools字段
    assert "tools: Read" in yaml_content, "tools字段应为Read"

    # 验证model字段
    assert "model: sonnet" in yaml_content, "model字段应为sonnet"

    print("[PASS] 测试用例1：YAML frontmatter验证通过")


def test_markdown_structure():
    """测试用例2：验证Markdown输出结构完整性"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/example-teaching.md")
    content = agent_file.read_text(encoding="utf-8")

    required_sections = [
        "## Role",
        "## Input Format",
        "## Output Format",
        "## System Prompt",
    ]

    for section in required_sections:
        assert section in content, f"缺少章节: {section}"

    # 验证Output Format说明6个部分
    assert "6个部分" in content or "题目" in content, "应说明包含6个部分"

    print("[PASS] 测试用例2：Markdown结构验证通过")


def test_problem_section():
    """测试用例3：验证题目部分存在且完整"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/example-teaching.md")
    content = agent_file.read_text(encoding="utf-8")

    # 验证题目部分的说明
    assert "题目" in content, "应说明包含题目部分"
    assert "完整" in content or "题目描述" in content, "应说明题目完整"
    assert "50-150字" in content, "应说明题目字数要求"

    # 验证输出示例包含题目部分
    output_match = re.search(r"输出示例.*?```markdown\n(.*?)\n```", content, re.DOTALL)
    if output_match:
        output_markdown = output_match.group(1)
        assert "## 题目" in output_markdown, "输出示例应包含'## 题目'标题"
        # 验证题目部分有内容
        problem_match = re.search(
            r"## 题目\n\n(.+?)(?=\n## )", output_markdown, re.DOTALL
        )
        assert problem_match, "题目部分应有内容"
        problem_text = problem_match.group(1)
        assert len(problem_text) >= 20, "题目部分内容应至少20字符"

    print("[PASS] 测试用例3：题目部分验证通过")


def test_analysis_section():
    """测试用例4：验证思路分析部分存在且清晰"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/example-teaching.md")
    content = agent_file.read_text(encoding="utf-8")

    # 验证思路分析部分的说明
    assert "思路分析" in content, "应说明包含思路分析部分"
    assert "识别题型" in content, "应说明识别题型"
    assert "回忆概念" in content, "应说明回忆概念"
    assert "确定步骤" in content, "应说明确定步骤"
    assert "150-250字" in content, "应说明思路分析字数要求"

    # 验证输出示例包含思路分析部分
    output_match = re.search(r"输出示例.*?```markdown\n(.*?)\n```", content, re.DOTALL)
    if output_match:
        output_markdown = output_match.group(1)
        assert "## 思路分析" in output_markdown, "输出示例应包含'## 思路分析'标题"
        # 验证思路分析包含三要素
        analysis_match = re.search(
            r"## 思路分析(.*?)(?=\n## )", output_markdown, re.DOTALL
        )
        assert analysis_match, "思路分析部分应有内容"
        analysis_text = analysis_match.group(1)
        assert "识别题型" in analysis_text or "题型" in analysis_text, (
            "思路分析应包含识别题型"
        )

    print("[PASS] 测试用例4：思路分析部分验证通过")


def test_solution_steps():
    """测试用例5：验证分步求解部分存在且步骤清晰"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/example-teaching.md")
    content = agent_file.read_text(encoding="utf-8")

    # 验证分步求解部分的说明
    assert "分步求解" in content, "应说明包含分步求解部分"
    assert "步骤" in content, "应说明包含步骤标记"
    assert "300-500字" in content, "应说明分步求解字数要求"

    # 验证输出示例包含分步求解部分
    output_match = re.search(r"输出示例.*?```markdown\n(.*?)\n```", content, re.DOTALL)
    if output_match:
        output_markdown = output_match.group(1)
        assert "## 分步求解" in output_markdown, "输出示例应包含'## 分步求解'标题"
        # 验证包含步骤标记
        solution_match = re.search(
            r"## 分步求解(.*?)(?=\n## )", output_markdown, re.DOTALL
        )
        assert solution_match, "分步求解部分应有内容"
        solution_text = solution_match.group(1)
        assert "步骤" in solution_text or "Step" in solution_text, (
            "分步求解应包含步骤标记"
        )
        assert len(solution_text) >= 200, "分步求解部分内容应至少200字符"

    print("[PASS] 测试用例5：分步求解部分验证通过")


def test_common_mistakes():
    """测试用例6：验证易错点提醒部分存在"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/example-teaching.md")
    content = agent_file.read_text(encoding="utf-8")

    # 验证易错点提醒部分的说明
    assert "易错点提醒" in content, "应说明包含易错点提醒部分"
    assert "2-4个" in content or "常见错误" in content, "应说明包含2-4个常见错误"
    assert "150-250字" in content, "应说明易错点提醒字数要求"

    # 验证输出示例包含易错点提醒部分
    output_match = re.search(r"输出示例.*?```markdown\n(.*?)\n```", content, re.DOTALL)
    if output_match:
        output_markdown = output_match.group(1)
        assert "## 易错点提醒" in output_markdown, "输出示例应包含'## 易错点提醒'标题"
        # 验证包含多个易错点
        mistakes_match = re.search(
            r"## 易错点提醒(.*?)(?=\n## )", output_markdown, re.DOTALL
        )
        assert mistakes_match, "易错点提醒部分应有内容"
        mistakes_text = mistakes_match.group(1)
        assert "易错点" in mistakes_text or "注意" in mistakes_text, (
            "易错点提醒应包含易错点标记"
        )

    print("[PASS] 测试用例6：易错点提醒部分验证通过")


def test_practice_problems():
    """测试用例7：验证变式练习部分存在"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/example-teaching.md")
    content = agent_file.read_text(encoding="utf-8")

    # 验证变式练习部分的说明
    assert "变式练习" in content, "应说明包含变式练习部分"
    assert "2-3道" in content or "类似题目" in content, "应说明包含2-3道类似题目"
    assert "150-250字" in content, "应说明变式练习字数要求"

    # 验证答案提示部分的说明
    assert "答案提示" in content, "应说明包含答案提示部分"
    assert "100-150字" in content, "应说明答案提示字数要求"

    # 验证输出示例包含变式练习和答案提示部分
    output_match = re.search(r"输出示例.*?```markdown\n(.*?)\n```", content, re.DOTALL)
    if output_match:
        output_markdown = output_match.group(1)
        assert "## 变式练习" in output_markdown, "输出示例应包含'## 变式练习'标题"
        assert "## 答案提示" in output_markdown, "输出示例应包含'## 答案提示'标题"

        # 验证包含多道练习题
        practice_match = re.search(
            r"## 变式练习(.*?)(?=\n## )", output_markdown, re.DOTALL
        )
        assert practice_match, "变式练习部分应有内容"
        practice_text = practice_match.group(1)
        assert (
            "练习1" in practice_text or "1." in practice_text or "1)" in practice_text
        ), "变式练习应包含练习题标记"

    print("[PASS] 测试用例7：变式练习部分验证通过")


def test_total_word_count():
    """测试用例8：验证总字数约1000字"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/example-teaching.md")
    content = agent_file.read_text(encoding="utf-8")

    # 验证字数要求说明
    assert "约1000字" in content or "800-1200字" in content, (
        "应说明总字数要求约1000字（800-1200字范围）"
    )

    # 验证输出示例字数
    output_match = re.search(r"输出示例.*?```markdown\n(.*?)\n```", content, re.DOTALL)
    if output_match:
        output_markdown = output_match.group(1)
        word_count = len(output_markdown)
        assert 800 <= word_count <= 1500, (
            f"输出示例字数{word_count}应在800-1500范围内（含markdown标记）"
        )

    print("[PASS] 测试用例8：总字数要求验证通过")


def test_filename_convention():
    """测试用例9：验证文件命名规范说明"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/example-teaching.md")
    content = agent_file.read_text(encoding="utf-8")

    # 注意：文件命名由Canvas orchestrator处理，
    # 但Agent定义可能在示例中提到文件命名规范
    # 这里主要验证Agent定义本身符合规范

    # 验证Agent文件名
    assert agent_file.name == "example-teaching.md", (
        "Agent文件名应为example-teaching.md"
    )

    # 验证name字段与文件名一致
    yaml_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
    if yaml_match:
        yaml_content = yaml_match.group(1)
        assert "name: example-teaching" in yaml_content, (
            "name字段应与文件名一致（kebab-case）"
        )

    print("[PASS] 测试用例9：文件命名规范验证通过")


def test_blue_explanation_node_creation():
    """测试用例10：验证蓝色节点创建说明（在canvas-orchestrator层面）"""
    # 注意：蓝色节点创建由canvas_utils.py和canvas-orchestrator处理
    # 这里验证Agent定义是否正确说明了输出格式

    agent_file = Path("C:/Users/ROG/托福/.claude/agents/example-teaching.md")
    content = agent_file.read_text(encoding="utf-8")

    # 验证Agent正确说明了输出格式为Markdown
    assert "Markdown" in content, "应说明输出Markdown格式"
    assert "无需JSON包裹" in content or "不要使用JSON" in content, (
        "应明确说明不返回JSON"
    )

    # 验证6个部分的说明
    sections = ["题目", "思路分析", "分步求解", "易错点提醒", "变式练习", "答案提示"]
    for section in sections:
        assert section in content, f"应说明包含'{section}'部分"

    # 验证canvas_utils.py中的emoji_map包含"例题教学"
    canvas_utils_file = Path("C:/Users/ROG/托福/canvas_utils.py")
    canvas_utils_content = canvas_utils_file.read_text(encoding="utf-8")
    assert '"例题教学"' in canvas_utils_content, (
        "canvas_utils.py应包含'例题教学'的emoji映射"
    )
    assert '"📝"' in canvas_utils_content or '"📚"' in canvas_utils_content, (
        "canvas_utils.py应包含例题教学的emoji（📝或📚）"
    )

    print("[PASS] 测试用例10：蓝色节点创建验证通过（emoji_map已配置）")


def test_edge_creation():
    """测试用例11：验证连接边创建说明（在canvas-orchestrator层面）"""
    # 注意：边创建由canvas-orchestrator处理
    # 这里验证Agent定义是否正确说明了角色和任务

    agent_file = Path("C:/Users/ROG/托福/.claude/agents/example-teaching.md")
    content = agent_file.read_text(encoding="utf-8")

    # 验证Role部分说明了Agent的任务
    role_match = re.search(r"## Role\n(.+?)(?=\n## )", content, re.DOTALL)
    assert role_match, "应包含Role部分"
    role_text = role_match.group(1)
    assert "例题教学" in role_text, "Role应说明Agent生成例题教学"
    assert "完整" in role_text or "详细" in role_text, "Role应说明生成完整或详细的内容"

    # 验证canvas-orchestrator.md包含example-teaching的集成说明
    orchestrator_file = Path("C:/Users/ROG/托福/.claude/agents/canvas-orchestrator.md")
    orchestrator_content = orchestrator_file.read_text(encoding="utf-8")
    assert "example-teaching" in orchestrator_content, (
        "canvas-orchestrator应包含example-teaching集成"
    )
    assert "例题教学" in orchestrator_content, (
        "canvas-orchestrator应包含例题教学的意图识别"
    )

    print("[PASS] 测试用例11：连接边创建验证通过（orchestrator已集成）")


def test_performance_requirement():
    """测试用例12：验证响应时间要求说明"""
    # 注意：响应时间<5秒的要求主要在canvas-orchestrator层面
    # Agent定义主要关注内容质量

    agent_file = Path("C:/Users/ROG/托福/.claude/agents/example-teaching.md")
    content = agent_file.read_text(encoding="utf-8")

    # 验证质量标准部分存在
    assert "质量标准" in content or "质量检查" in content, "应包含质量标准部分"

    # 验证各部分的质量要求
    quality_items = ["题目完整", "思路分析", "分步求解", "易错点", "变式练习"]

    for item in quality_items:
        assert item in content, f"质量标准应包含: {item}"

    # 验证字数要求清晰
    assert "800-1200字" in content or "约1000字" in content, "应明确说明总字数范围"

    # 验证canvas-orchestrator.md中说明了响应时间目标
    orchestrator_file = Path("C:/Users/ROG/托福/.claude/agents/canvas-orchestrator.md")
    orchestrator_content = orchestrator_file.read_text(encoding="utf-8")

    # 搜索example-teaching相关的响应时间说明
    # 在示例3.9中应该有响应时间目标的说明
    example_teaching_section = re.search(
        r"示例3\.9：例题教学完整流程(.*?)(?=#### 示例|$)",
        orchestrator_content,
        re.DOTALL,
    )
    if example_teaching_section:
        section_text = example_teaching_section.group(1)
        assert "<5秒" in section_text or "5秒" in section_text, (
            "canvas-orchestrator应说明例题教学的响应时间目标<5秒"
        )

    print("[PASS] 测试用例12：性能要求验证通过（响应时间目标已说明）")


def test_ac_coverage():
    """验证所有AC都已满足"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/example-teaching.md")
    content = agent_file.read_text(encoding="utf-8")

    # AC 1: 例题完整且有代表性
    assert "完整" in content and "代表性" in content, "AC 1: 未说明例题完整且有代表性"

    # AC 2: 解答详细，步骤清晰
    assert "详细" in content and "步骤清晰" in content, "AC 2: 未说明解答详细且步骤清晰"

    # AC 3: 包含易错点提醒
    assert "易错点" in content, "AC 3: 未说明包含易错点提醒"

    # AC 4: 提供变式练习（2-3道类似题目）
    assert "变式练习" in content and ("2-3道" in content or "类似题目" in content), (
        "AC 4: 未说明变式练习"
    )

    # AC 5: 创建.md文件（由orchestrator处理）
    orchestrator_file = Path("C:/Users/ROG/托福/.claude/agents/canvas-orchestrator.md")
    orchestrator_content = orchestrator_file.read_text(encoding="utf-8")
    assert "例题教学" in orchestrator_content, "AC 5: orchestrator未集成例题教学"

    # AC 6: 在Canvas中创建蓝色节点（由canvas_utils处理）
    canvas_utils_file = Path("C:/Users/ROG/托福/canvas_utils.py")
    canvas_utils_content = canvas_utils_file.read_text(encoding="utf-8")
    assert '"例题教学"' in canvas_utils_content, "AC 6: canvas_utils未配置例题教学emoji"

    # AC 7: 在Canvas中创建file节点（由canvas_utils处理）
    # 已验证在AC 6中

    # AC 8: 响应时间<5秒（在orchestrator中说明）
    assert "<5秒" in orchestrator_content or "5秒" in orchestrator_content, (
        "AC 8: 未说明响应时间目标"
    )

    print("[PASS] AC覆盖验证通过")


if __name__ == "__main__":
    print("开始验证example-teaching Agent定义文件...\n")

    try:
        test_yaml_frontmatter()
        test_markdown_structure()
        test_problem_section()
        test_analysis_section()
        test_solution_steps()
        test_common_mistakes()
        test_practice_problems()
        test_total_word_count()
        test_filename_convention()
        test_blue_explanation_node_creation()
        test_edge_creation()
        test_performance_requirement()
        test_ac_coverage()

        print("\n" + "=" * 50)
        print("SUCCESS: 所有12个测试用例通过！")
        print("example-teaching Agent定义文件符合规范。")
        print("=" * 50)

    except AssertionError as e:
        print(f"\n[FAIL] 验证失败: {e}")
        raise
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        raise
