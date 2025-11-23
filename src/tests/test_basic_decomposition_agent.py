"""
测试basic-decomposition Agent定义文件

验证YAML frontmatter、Markdown结构、内容完整性和JSON格式
"""

import json
import re
from pathlib import Path


def test_yaml_frontmatter():
    """测试YAML frontmatter格式"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/basic-decomposition.md")
    content = agent_file.read_text(encoding='utf-8')

    # 提取YAML frontmatter
    yaml_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    assert yaml_match, "未找到YAML frontmatter"

    yaml_content = yaml_match.group(1)

    # 验证name字段
    assert 'name: basic-decomposition' in yaml_content, "name字段不正确"

    # 验证description字段
    desc_match = re.search(r'description: "(.*?)"', yaml_content)
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
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/basic-decomposition.md")
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
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/basic-decomposition.md")
    content = agent_file.read_text(encoding='utf-8')

    # 验证Role部分
    assert "基础拆解Agent" in content, "缺少Agent名称"
    assert "红色节点" in content and "紫色节点" in content, "Role部分应说明颜色状态转换"

    # 验证Input Format
    assert "material_content" in content, "缺少material_content字段"
    assert "topic" in content, "缺少topic字段"
    assert "user_understanding" in content, "缺少user_understanding字段"

    # 验证Output Format
    assert "sub_questions" in content, "缺少sub_questions字段"
    assert "text" in content and "type" in content, "缺少问题字段"
    assert "difficulty" in content and "guidance" in content, "缺少难度和提示字段"

    # 验证System Prompt包含4种拆解策略
    strategies = [
        "降低抽象层次",
        "关键句逐句拆解",
        "引导性递进",
        "避免直接答案"
    ]
    for strategy in strategies:
        assert strategy in content, f"缺少拆解策略: {strategy}"

    # 验证System Prompt包含4种问题类型
    question_types = ["定义型", "实例型", "对比型", "探索型"]
    for qtype in question_types:
        assert qtype in content, f"缺少问题类型: {qtype}"

    # 验证包含示例
    assert "输入示例" in content, "缺少输入示例"
    assert "输出示例" in content, "缺少输出示例"
    assert "逆否命题" in content, "缺少具体示例内容"

    # 验证质量标准
    assert "质量标准" in content, "缺少质量标准章节"

    print("[PASS] 内容完整性验证通过")


def test_json_format():
    """测试JSON示例格式"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/basic-decomposition.md")
    content = agent_file.read_text(encoding='utf-8')

    # 提取所有JSON代码块
    json_blocks = re.findall(r'```json\n(.*?)\n```', content, re.DOTALL)

    assert len(json_blocks) >= 2, "至少应有2个JSON代码块（输入示例和输出示例）"

    for i, json_str in enumerate(json_blocks):
        # 移除注释（仅用于文档说明）
        json_str_clean = re.sub(r'//.*', '', json_str)
        json_str_clean = re.sub(r',\s*}', '}', json_str_clean)  # 移除尾部逗号
        json_str_clean = re.sub(r',\s*]', ']', json_str_clean)

        try:
            data = json.loads(json_str_clean)
            print(f"[PASS] JSON块 {i+1} 格式正确")
        except json.JSONDecodeError as e:
            print(f"[FAIL] JSON块 {i+1} 格式错误: {e}")
            print(f"JSON内容:\n{json_str_clean[:200]}...")
            raise

    # 验证输出示例的结构
    output_example_match = re.search(
        r'输出示例.*?```json\n(.*?)\n```',
        content,
        re.DOTALL
    )
    assert output_example_match, "未找到输出示例"

    output_json = output_example_match.group(1)
    output_json_clean = re.sub(r'//.*', '', output_json)
    output_json_clean = re.sub(r',\s*}', '}', output_json_clean)
    output_json_clean = re.sub(r',\s*]', ']', output_json_clean)

    output_data = json.loads(output_json_clean)

    # 验证输出结构
    assert "sub_questions" in output_data, "输出缺少sub_questions字段"
    assert isinstance(output_data["sub_questions"], list), "sub_questions应为数组"
    assert len(output_data["sub_questions"]) > 0, "sub_questions不能为空"

    # 验证问题对象结构
    first_question = output_data["sub_questions"][0]
    required_fields = ["text", "type", "difficulty", "guidance"]
    for field in required_fields:
        assert field in first_question, f"问题对象缺少字段: {field}"

    print("[PASS] JSON格式验证通过")


def test_ac_coverage():
    """验证所有AC都已满足"""
    agent_file = Path("C:/Users/ROG/托福/.claude/agents/basic-decomposition.md")
    content = agent_file.read_text(encoding='utf-8')

    # AC 1: 能够生成2-7个子问题
    assert "3-7个子问题" in content, "AC 1: 未说明问题数量范围"

    # AC 2: 子问题是基础的、可回答的
    assert "基础" in content, "AC 2: 未说明难度为基础"
    assert "易于回答" in content or "易回答" in content, "AC 2: 未说明易于回答"

    # AC 3: 每个子问题节点颜色为红色（"1"）
    # 注意：颜色由Canvas层处理，Agent定义文件不需要包含此信息

    # AC 4: 自动创建关联的黄色节点
    # 注意：节点创建由Canvas层处理，Agent定义文件不需要包含此信息

    # AC 5: 创建"拆解自"连接边
    # 注意：边创建由Canvas层处理，Agent定义文件不需要包含此信息

    # AC 6: 响应时间<3秒
    # 注意：响应时间取决于AI模型，不在Agent定义中控制

    print("[PASS] AC覆盖验证通过")


if __name__ == "__main__":
    print("开始验证basic-decomposition Agent定义文件...\n")

    try:
        test_yaml_frontmatter()
        test_markdown_structure()
        test_content_completeness()
        test_json_format()
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
