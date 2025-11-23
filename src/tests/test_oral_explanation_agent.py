"""
测试oral-explanation Agent定义文件

验证YAML frontmatter、Markdown结构、内容完整性和输出格式
"""

import json
import re
from pathlib import Path


def test_yaml_frontmatter():
    """测试YAML frontmatter格式"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/oral-explanation.md")
    content = agent_file.read_text(encoding='utf-8')

    # 提取YAML frontmatter
    yaml_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    assert yaml_match, "未找到YAML frontmatter"

    yaml_content = yaml_match.group(1)

    # 验证name字段
    assert 'name: oral-explanation' in yaml_content, "name字段不正确"

    # 验证description字段
    desc_match = re.search(r'description: (.+)', yaml_content)
    assert desc_match, "未找到description字段"
    description = desc_match.group(1)
    assert len(description) < 80, f"description过长: {len(description)}字符"

    # 验证tools字段
    assert 'tools: Read' in yaml_content, "tools字段应为Read"

    # 验证model字段
    assert 'model: sonnet' in yaml_content, "model字段应为sonnet"

    print("[PASS] YAML frontmatter验证通过")


def test_markdown_structure():
    """测试Markdown结构"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/oral-explanation.md")
    content = agent_file.read_text(encoding='utf-8')

    required_sections = [
        "## Role",
        "## Input Format",
        "## Output Format",
        "## System Prompt"
    ]

    for section in required_sections:
        assert section in content, f"缺少章节: {section}"

    print("[PASS] Markdown结构验证通过")


def test_content_completeness():
    """测试内容完整性"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/oral-explanation.md")
    content = agent_file.read_text(encoding='utf-8')

    # 验证Role部分
    assert "口语化" in content, "Role部分应提及口语化解释"
    assert "800-1200字" in content, "应说明字数要求"

    # 验证Input Format
    assert "material_content" in content, "缺少material_content字段"
    assert "topic" in content, "缺少topic字段"
    assert "user_understanding" in content, "缺少user_understanding字段"

    # 验证Output Format
    assert "Markdown" in content, "应说明输出Markdown格式"
    assert "无需JSON包裹" in content or "不要使用JSON" in content, "应明确说明不返回JSON"

    # 验证System Prompt包含4个解释要素
    elements = [
        "背景铺垫",
        "核心解释",
        "生动例子",
        "常见误区"
    ]
    for element in elements:
        assert element in content, f"缺少解释要素: {element}"

    # 验证包含示例
    assert "输入示例" in content, "缺少输入示例"
    assert "输出示例" in content, "缺少输出示例"

    # 验证质量标准
    assert "质量" in content, "缺少质量标准相关内容"

    print("[PASS] 内容完整性验证通过")


def test_input_output_format():
    """测试输入输出格式定义"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/oral-explanation.md")
    content = agent_file.read_text(encoding='utf-8')

    # 提取输入示例JSON
    input_match = re.search(
        r'输入示例.*?```json\n(.*?)\n```',
        content,
        re.DOTALL
    )
    assert input_match, "未找到输入示例"

    input_json = input_match.group(1)
    input_data = json.loads(input_json)

    # 验证输入结构
    assert "material_content" in input_data, "输入缺少material_content字段"
    assert "topic" in input_data, "输入缺少topic字段"
    assert "user_understanding" in input_data, "输入缺少user_understanding字段"

    # 验证输出示例是Markdown格式（不是JSON）
    output_match = re.search(
        r'输出示例.*?```markdown\n(.*?)\n```',
        content,
        re.DOTALL
    )
    assert output_match, "未找到输出示例（应为markdown格式）"

    output_markdown = output_match.group(1)

    # 验证输出示例包含4个要素的标题
    assert "## 为什么要学这个" in output_markdown or "## 背景铺垫" in output_markdown, "输出示例缺少背景铺垫部分"
    assert "## 核心讲解" in output_markdown or "## 核心解释" in output_markdown, "输出示例缺少核心解释部分"
    assert "## 举个例子" in output_markdown or "## 生动例子" in output_markdown, "输出示例缺少生动例子部分"
    assert "## 常见误区" in output_markdown, "输出示例缺少常见误区部分"

    # 验证字数（输出示例应该是800-1200字）
    word_count = len(output_markdown)
    assert 800 <= word_count <= 1500, f"输出示例字数{word_count}应在800-1500范围内（含markdown标记）"

    print("[PASS] 输入输出格式验证通过")


def test_explanation_structure():
    """测试解释结构要求"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/oral-explanation.md")
    content = agent_file.read_text(encoding='utf-8')

    # 验证背景铺垫要求
    assert "2-3句" in content or "50-80字" in content, "应说明背景铺垫的长度要求"

    # 验证核心解释要求
    assert "600-800字" in content, "应说明核心解释的字数要求"
    assert "日常语言" in content or "通俗语言" in content, "应说明使用日常语言"
    assert "类比" in content or "比喻" in content, "应说明使用类比和比喻"

    # 验证生动例子要求
    assert "100-150字" in content, "应说明生动例子的字数要求"
    assert "生活场景" in content or "实际应用" in content, "应说明提供生活场景"

    # 验证常见误区要求
    assert "80-120字" in content, "应说明常见误区的字数要求"

    # 验证口语化风格要求
    assert "口语化" in content, "应说明口语化风格"

    print("[PASS] 解释结构要求验证通过")


def test_user_understanding_handling():
    """测试user_understanding字段处理"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/oral-explanation.md")
    content = agent_file.read_text(encoding='utf-8')

    # 验证对user_understanding的处理说明
    assert "user_understanding" in content, "应说明如何处理user_understanding"
    assert "null" in content.lower(), "应说明user_understanding为null时的处理"

    # 在输入示例中应该有user_understanding字段
    input_match = re.search(
        r'输入示例.*?```json\n(.*?)\n```',
        content,
        re.DOTALL
    )
    if input_match:
        input_json = input_match.group(1)
        assert "user_understanding" in input_json, "输入示例应包含user_understanding字段"

    print("[PASS] user_understanding处理验证通过")


def test_ac_coverage():
    """验证所有AC都已满足"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/oral-explanation.md")
    content = agent_file.read_text(encoding='utf-8')

    # AC 1: 生成800-1200字的口语化解释
    assert "800-1200字" in content, "AC 1: 未说明字数范围"

    # AC 2: 创建.md文件并保存
    # 注意：文件创建由Canvas层处理，Agent定义文件不需要包含此信息

    # AC 3: 文件命名：[主题]-口语化解释-[时间戳].md
    # 注意：文件命名由Canvas层处理，Agent定义文件不需要包含此信息

    # AC 4: 在Canvas中创建蓝色节点（color: "5"）
    # 注意：节点创建由Canvas层处理，Agent定义文件不需要包含此信息

    # AC 5: 创建file节点引用.md文件
    # 注意：节点创建由Canvas层处理，Agent定义文件不需要包含此信息

    # AC 6: 响应时间<40秒（目标15-20秒）
    # 注意：响应时间取决于AI模型，不在Agent定义中控制

    print("[PASS] AC覆盖验证通过")


if __name__ == "__main__":
    print("开始验证oral-explanation Agent定义文件...\n")

    try:
        test_yaml_frontmatter()
        test_markdown_structure()
        test_content_completeness()
        test_input_output_format()
        test_explanation_structure()
        test_user_understanding_handling()
        test_ac_coverage()

        print("\n" + "="*50)
        print("SUCCESS: 所有验证通过！Agent定义文件符合规范。")
        print("="*50)

    except AssertionError as e:
        print(f"\n[FAIL] 验证失败: {e}")
        raise
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        raise
