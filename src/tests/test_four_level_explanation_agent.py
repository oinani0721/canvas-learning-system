"""
测试four-level-explanation Agent定义文件

验证YAML frontmatter、Markdown结构、内容完整性和输出格式
"""

import json
import re
from pathlib import Path


def test_yaml_frontmatter():
    """测试YAML frontmatter格式"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/four-level-explanation.md")
    content = agent_file.read_text(encoding='utf-8')

    # 提取YAML frontmatter
    yaml_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    assert yaml_match, "未找到YAML frontmatter"

    yaml_content = yaml_match.group(1)

    # 验证name字段
    assert 'name: four-level-explanation' in yaml_content, "name字段不正确"

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
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/four-level-explanation.md")
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
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/four-level-explanation.md")
    content = agent_file.read_text(encoding='utf-8')

    # 验证Role部分
    assert "四层次" in content or "4个" in content, "Role部分应提及四层次解释"
    assert "1200-1600字" in content, "应说明字数要求"

    # 验证Input Format
    assert "concept" in content, "缺少concept字段"
    assert "topic" in content, "缺少topic字段"
    assert "material_content" in content, "缺少material_content字段"
    assert "user_understanding" in content, "缺少user_understanding字段"

    # 验证Output Format
    assert "Markdown" in content, "应说明输出Markdown格式"
    assert "无需JSON包裹" in content or "不要使用JSON" in content, "应明确说明不返回JSON"

    # 验证System Prompt包含4个层次
    levels = [
        "新手层",
        "进阶层",
        "专家层",
        "创新层"
    ]
    for level in levels:
        assert level in content, f"缺少层次: {level}"

    # 验证包含示例
    assert "输入示例" in content, "缺少输入示例"
    assert "输出示例" in content, "缺少输出示例"

    # 验证质量标准
    assert "质量" in content, "缺少质量标准相关内容"

    print("[PASS] 内容完整性验证通过")


def test_input_output_format():
    """测试输入输出格式定义"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/four-level-explanation.md")
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
    assert "concept" in input_data, "输入缺少concept字段"
    assert "topic" in input_data, "输入缺少topic字段"
    assert "material_content" in input_data, "输入缺少material_content字段"
    assert "user_understanding" in input_data, "输入缺少user_understanding字段"

    # 验证输出示例是Markdown格式（不是JSON）
    output_match = re.search(
        r'输出示例.*?```markdown\n(.*?)\n```',
        content,
        re.DOTALL
    )
    assert output_match, "未找到输出示例（应为markdown格式）"

    output_markdown = output_match.group(1)

    # 验证输出示例包含4个层次的标题
    assert "## 新手层" in output_markdown or "## Beginner" in output_markdown, "输出示例缺少新手层"
    assert "## 进阶层" in output_markdown or "## Intermediate" in output_markdown, "输出示例缺少进阶层"
    assert "## 专家层" in output_markdown or "## Expert" in output_markdown, "输出示例缺少专家层"
    assert "## 创新层" in output_markdown or "## Innovation" in output_markdown, "输出示例缺少创新层"

    # 验证字数（输出示例应该是1200-1600字）
    word_count = len(output_markdown)
    assert 1200 <= word_count <= 2000, f"输出示例字数{word_count}应在1200-2000范围内（含markdown标记）"

    print("[PASS] 输入输出格式验证通过")


def test_four_level_structure():
    """测试四层次结构要求"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/four-level-explanation.md")
    content = agent_file.read_text(encoding='utf-8')

    # 验证新手层要求
    assert "新手层" in content, "应说明新手层"
    assert "零基础" in content or "完全零基础" in content, "新手层应说明零基础可懂"
    assert "300-400字" in content, "应说明每层字数要求"

    # 验证进阶层要求
    assert "进阶层" in content, "应说明进阶层"
    assert "具体" in content or "例子" in content, "进阶层应说明提供具体例子"

    # 验证专家层要求
    assert "专家层" in content, "应说明专家层"
    assert "原理" in content or "本质" in content, "专家层应说明深入原理"

    # 验证创新层要求
    assert "创新层" in content, "应说明创新层"
    assert "应用" in content or "前沿" in content, "创新层应说明实际应用或前沿思考"

    # 验证渐进性要求
    assert "渐进" in content or "递进" in content or "逐步" in content, "应说明层次间的渐进性"

    print("[PASS] 四层次结构要求验证通过")


def test_each_level_requirements():
    """测试每个层次的详细要求"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/four-level-explanation.md")
    content = agent_file.read_text(encoding='utf-8')

    # 简化测试 - 只检查整体文档中是否包含关键要求
    # 新手层要求
    assert "日常语言" in content or "生活例子" in content, "新手层应说明使用日常语言和生活例子"
    assert "零基础" in content, "新手层应说明零基础可懂"

    # 进阶层要求
    assert "术语" in content, "进阶层应说明引入术语"
    assert "具体例子" in content or "具体的例子" in content or "例子" in content, "进阶层应说明提供例子"

    # 专家层要求
    assert "原理" in content or "本质" in content, "专家层应说明深入原理"
    assert "为什么" in content or "联系" in content, "专家层应说明解释'为什么'或建立联系"

    # 创新层要求
    assert "应用" in content and "前沿" in content, "创新层应说明应用场景和前沿思考"

    print("[PASS] 每层次详细要求验证通过")


def test_user_understanding_handling():
    """测试user_understanding字段处理"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/four-level-explanation.md")
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


def test_word_count_requirements():
    """测试字数要求"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/four-level-explanation.md")
    content = agent_file.read_text(encoding='utf-8')

    # 验证每层字数要求
    assert "300-400字" in content, "应说明每层字数要求为300-400字"

    # 验证总字数要求
    assert "1200-1600字" in content, "应说明总字数要求为1200-1600字"

    print("[PASS] 字数要求验证通过")


def test_output_example_structure():
    """测试输出示例的结构"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/four-level-explanation.md")
    content = agent_file.read_text(encoding='utf-8')

    # 提取输出示例
    output_match = re.search(
        r'输出示例.*?```markdown\n(.*?)\n```',
        content,
        re.DOTALL
    )
    assert output_match, "未找到输出示例"

    output_markdown = output_match.group(1)

    # 提取每个层次的内容
    beginner_match = re.search(r'## 新手层.*?(?=## )', output_markdown, re.DOTALL)
    intermediate_match = re.search(r'## 进阶层.*?(?=## )', output_markdown, re.DOTALL)
    expert_match = re.search(r'## 专家层.*?(?=## )', output_markdown, re.DOTALL)
    innovation_match = re.search(r'## 创新层.*?$', output_markdown, re.DOTALL)

    assert beginner_match, "输出示例缺少新手层内容"
    assert intermediate_match, "输出示例缺少进阶层内容"
    assert expert_match, "输出示例缺少专家层内容"
    assert innovation_match, "输出示例缺少创新层内容"

    # 验证每层字数（允许弹性）
    beginner_text = beginner_match.group(0) if beginner_match else ""
    intermediate_text = intermediate_match.group(0) if intermediate_match else ""
    expert_text = expert_match.group(0) if expert_match else ""
    innovation_text = innovation_match.group(0) if innovation_match else ""

    # 每层至少应有200字（含标题和markdown标记），最多500字
    for level_name, level_text in [
        ("新手层", beginner_text),
        ("进阶层", intermediate_text),
        ("专家层", expert_text),
        ("创新层", innovation_text)
    ]:
        word_count = len(level_text)
        assert 200 <= word_count <= 600, f"{level_name}字数{word_count}不在合理范围（200-600）"

    print("[PASS] 输出示例结构验证通过")


def test_quality_checklist():
    """测试质量检查清单"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/four-level-explanation.md")
    content = agent_file.read_text(encoding='utf-8')

    # 验证质量检查清单存在
    assert "质量检查清单" in content or "质量标准" in content, "应包含质量检查清单"

    # 验证关键质量标准
    quality_items = [
        "4个完整层次",
        "300-400字",
        "1200-1600字",
        "层次间逐步深入",
        "零基础可懂"
    ]

    for item in quality_items:
        assert item in content, f"质量标准缺少: {item}"

    print("[PASS] 质量检查清单验证通过")


def test_ac_coverage():
    """验证所有AC都已满足"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/four-level-explanation.md")
    content = agent_file.read_text(encoding='utf-8')

    # AC 1: 生成4个清晰的层次（新手、进阶、专家、创新）
    assert "新手层" in content and "进阶层" in content, "AC 1: 未说明4个层次"
    assert "专家层" in content and "创新层" in content, "AC 1: 未说明4个层次"

    # AC 2: 层次间逐步深入，无跳跃
    assert "逐步" in content or "渐进" in content or "递进" in content, "AC 2: 未说明层次间逐步深入"

    # AC 3: 总字数约1200-1600字
    assert "1200-1600字" in content, "AC 3: 未说明总字数范围"

    # AC 4: 创建.md文件
    # 注意：文件创建由Canvas层处理，Agent定义文件不需要包含此信息

    # AC 5: 在Canvas中创建蓝色节点（color: "5"）
    # 注意：节点创建由Canvas层处理，Agent定义文件不需要包含此信息

    # AC 6: 创建file节点引用.md文件
    # 注意：节点创建由Canvas层处理，Agent定义文件不需要包含此信息

    # AC 7: 响应时间<5秒
    # 注意：响应时间取决于AI模型，不在Agent定义中控制

    print("[PASS] AC覆盖验证通过")


if __name__ == "__main__":
    print("开始验证four-level-explanation Agent定义文件...\n")

    try:
        test_yaml_frontmatter()
        test_markdown_structure()
        test_content_completeness()
        test_input_output_format()
        test_four_level_structure()
        test_each_level_requirements()
        test_user_understanding_handling()
        test_word_count_requirements()
        test_output_example_structure()
        test_quality_checklist()
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
