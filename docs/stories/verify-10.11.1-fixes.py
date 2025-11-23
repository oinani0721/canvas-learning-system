#!/usr/bin/env python3
"""
Story 10.11.1 修复验证脚本

用途：验证所有10个修复是否正确应用到Story文件
使用方法：python verify-10.11.1-fixes.py <story_file_path>

示例：
  python verify-10.11.1-fixes.py docs/stories/10.11.1.story.md
  python verify-10.11.1-fixes.py docs/stories/10.11.1.story-FIXED.md
"""

import sys
import os
from typing import List, Tuple, Dict


class Fix:
    """修复项定义"""
    def __init__(self, fix_id: str, name: str, check_func, severity: str):
        self.fix_id = fix_id
        self.name = name
        self.check_func = check_func
        self.severity = severity  # 'CRITICAL', 'SHOULD_FIX', 'NICE_TO_HAVE'


def check_fix_1(content: str) -> Tuple[bool, str]:
    """检查修复1: 添加Task 3.5 - .gitignore更新任务"""
    if "### Task 3.5: 更新.gitignore文件" in content:
        if "防止包含敏感密码的.env文件被提交到Git" in content:
            return True, "✅ Task 3.5已添加，包含.gitignore更新"
        else:
            return False, "⚠️  Task 3.5存在但内容不完整"
    return False, "❌ 缺少Task 3.5 (.gitignore更新)"


def check_fix_2(content: str) -> Tuple[bool, str]:
    """检查修复2: Task 4添加deployment/目录创建"""
    if "创建`deployment/`目录（如果不存在）" in content:
        if "if not exist \"deployment\" mkdir deployment" in content:
            return True, "✅ Task 4已添加deployment/目录创建步骤"
        else:
            return False, "⚠️  Task 4提到目录创建但缺少具体命令"
    return False, "❌ Task 4缺少deployment/目录创建步骤"


def check_fix_3(content: str) -> Tuple[bool, str]:
    """检查修复3: 更正Neo4j驱动版本号 (6.0.2 → 5.28.2)"""
    # 检查是否还有错误的6.0.2版本
    if "6.0.2" in content:
        count = content.count("6.0.2")
        return False, f"❌ 仍然包含错误版本6.0.2 ({count}处)"

    # 检查是否有3处正确的5.28.2版本
    count_5_28_2 = content.count("5.28.2")
    if count_5_28_2 >= 3:
        return True, f"✅ Neo4j驱动版本已更正为5.28.2 ({count_5_28_2}处)"
    elif count_5_28_2 > 0:
        return False, f"⚠️  只找到{count_5_28_2}处5.28.2，应该至少有3处"
    else:
        return False, "❌ 未找到正确的版本号5.28.2"


def check_fix_4(content: str) -> Tuple[bool, str]:
    """检查修复4: 更正行号引用为逻辑描述"""
    # 检查是否还有"第60行"这样的硬编码引用
    if "第60行" in content or "第 60 行" in content:
        return False, "❌ 仍然包含硬编码行号引用（第60行）"

    # 检查是否有正确的逻辑描述
    correct_references = [
        "在__init__方法开头（Neo4j连接建立之前）",
        "在__init__方法开头导入",
        "在__init__方法开头添加验证"
    ]

    found_count = sum(1 for ref in correct_references if ref in content)

    if found_count >= 3:
        return True, f"✅ 行号引用已更正为逻辑描述 ({found_count}处)"
    elif found_count > 0:
        return False, f"⚠️  只找到{found_count}处逻辑描述，应该至少有3处"
    else:
        return False, "❌ 未找到正确的逻辑描述"


def check_fix_5(content: str) -> Tuple[bool, str]:
    """检查修复5: Task 1添加Neo4j API代码示例"""
    has_socket_example = "import socket" in content and "sock.connect_ex" in content
    has_neo4j_example = "from neo4j import GraphDatabase" in content and "driver = GraphDatabase.driver" in content

    if has_socket_example and has_neo4j_example:
        return True, "✅ Task 1已添加socket和Neo4j API代码示例"
    elif has_socket_example:
        return False, "⚠️  只有socket示例，缺少Neo4j driver示例"
    elif has_neo4j_example:
        return False, "⚠️  只有Neo4j driver示例，缺少socket示例"
    else:
        return False, "❌ Task 1缺少API代码示例"


def check_fix_6(content: str) -> Tuple[bool, str]:
    """检查修复6: Task 6指定unittest.mock库"""
    if "from unittest.mock import Mock, patch, MagicMock" in content:
        return True, "✅ Task 6已指定使用unittest.mock库"
    elif "unittest.mock" in content:
        return False, "⚠️  提到unittest.mock但格式不完整"
    else:
        return False, "❌ Task 6未指定mock库"


def check_fix_7(content: str) -> Tuple[bool, str]:
    """检查修复7: Task 6添加性能测试"""
    if "性能测试" in content and "validate_neo4j_connection" in content and "2秒内完成" in content:
        return True, "✅ Task 6已添加性能测试（验证≤2秒）"
    elif "性能测试" in content:
        return False, "⚠️  提到性能测试但内容不完整"
    else:
        return False, "❌ Task 6缺少性能测试"


def check_fix_8(content: str) -> Tuple[bool, str]:
    """检查修复8: Task 4添加批处理失败输出格式"""
    if "失败输出格式示例" in content or "失败输出格式" in content:
        if "❌ Neo4j连接验证失败" in content and "快速修复命令" in content:
            return True, "✅ Task 4已添加批处理失败输出格式示例"
        else:
            return False, "⚠️  提到失败输出但示例不完整"
    return False, "❌ Task 4缺少批处理失败输出格式"


def check_fix_9(content: str) -> Tuple[bool, str]:
    """检查修复9: Task 2添加密码清理说明"""
    if "安全要求" in content and "清理敏感信息" in content and "密码必须被替换为" in content:
        return True, "✅ Task 2已添加密码清理安全要求"
    elif "密码" in content and "清理" in content:
        return False, "⚠️  提到密码清理但描述不完整"
    else:
        return False, "❌ Task 2缺少密码清理说明"


def check_fix_10(content: str) -> Tuple[bool, str]:
    """检查修复10: 添加Change Log章节"""
    if "## Change Log" in content:
        if "v1.1 - 2025-10-31" in content and "PO Validation Fixes" in content:
            return True, "✅ 已添加Change Log章节，包含v1.1修复记录"
        else:
            return False, "⚠️  Change Log存在但内容不完整"
    return False, "❌ 缺少Change Log章节"


def verify_story_fixes(file_path: str) -> Dict:
    """验证Story文件的所有修复"""

    # 读取文件
    if not os.path.exists(file_path):
        return {
            'success': False,
            'error': f"文件不存在: {file_path}",
            'results': []
        }

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {
            'success': False,
            'error': f"读取文件失败: {str(e)}",
            'results': []
        }

    # 定义所有修复项
    fixes = [
        Fix("1", "添加Task 3.5 - .gitignore更新", check_fix_1, "CRITICAL"),
        Fix("2", "Task 4添加deployment/目录创建", check_fix_2, "CRITICAL"),
        Fix("3", "更正Neo4j驱动版本号", check_fix_3, "CRITICAL"),
        Fix("4", "更正行号引用为逻辑描述", check_fix_4, "CRITICAL"),
        Fix("5", "Task 1添加Neo4j API代码示例", check_fix_5, "SHOULD_FIX"),
        Fix("6", "Task 6指定unittest.mock库", check_fix_6, "SHOULD_FIX"),
        Fix("7", "Task 6添加性能测试", check_fix_7, "SHOULD_FIX"),
        Fix("8", "Task 4添加批处理失败输出格式", check_fix_8, "SHOULD_FIX"),
        Fix("9", "Task 2添加密码清理说明", check_fix_9, "SHOULD_FIX"),
        Fix("10", "添加Change Log章节", check_fix_10, "NICE_TO_HAVE"),
    ]

    # 执行所有检查
    results = []
    critical_passed = 0
    critical_total = 0
    should_fix_passed = 0
    should_fix_total = 0
    nice_to_have_passed = 0
    nice_to_have_total = 0

    for fix in fixes:
        passed, message = fix.check_func(content)
        results.append({
            'fix_id': fix.fix_id,
            'name': fix.name,
            'severity': fix.severity,
            'passed': passed,
            'message': message
        })

        if fix.severity == "CRITICAL":
            critical_total += 1
            if passed:
                critical_passed += 1
        elif fix.severity == "SHOULD_FIX":
            should_fix_total += 1
            if passed:
                should_fix_passed += 1
        elif fix.severity == "NICE_TO_HAVE":
            nice_to_have_total += 1
            if passed:
                nice_to_have_passed += 1

    # 计算总分
    total_passed = critical_passed + should_fix_passed + nice_to_have_passed
    total_fixes = len(fixes)

    # 判断GO/NO-GO
    go_decision = (
        critical_passed == critical_total and  # 所有关键修复必须通过
        should_fix_passed >= (should_fix_total * 0.8)  # 至少80%的建议修复通过
    )

    return {
        'success': True,
        'file_path': file_path,
        'results': results,
        'summary': {
            'total_passed': total_passed,
            'total_fixes': total_fixes,
            'critical_passed': critical_passed,
            'critical_total': critical_total,
            'should_fix_passed': should_fix_passed,
            'should_fix_total': should_fix_total,
            'nice_to_have_passed': nice_to_have_passed,
            'nice_to_have_total': nice_to_have_total,
            'percentage': round((total_passed / total_fixes) * 100, 1),
            'go_decision': go_decision
        }
    }


def print_results(verification_result: Dict):
    """打印验证结果"""

    if not verification_result['success']:
        print(f"\n❌ 验证失败: {verification_result['error']}\n")
        return

    print("\n" + "="*80)
    print(f"Story 10.11.1 修复验证报告")
    print("="*80)
    print(f"\n文件路径: {verification_result['file_path']}\n")

    # 按严重性分组打印结果
    for severity, severity_name in [("CRITICAL", "关键修复"), ("SHOULD_FIX", "建议修复"), ("NICE_TO_HAVE", "可选修复")]:
        print(f"\n{severity_name} ({severity}):")
        print("-" * 80)

        for result in verification_result['results']:
            if result['severity'] == severity:
                print(f"  修复 #{result['fix_id']}: {result['name']}")
                print(f"    {result['message']}")

    # 打印统计信息
    summary = verification_result['summary']
    print("\n" + "="*80)
    print("统计摘要")
    print("="*80)
    print(f"  总修复数: {summary['total_fixes']}")
    print(f"  已通过: {summary['total_passed']} ({summary['percentage']}%)")
    print(f"  未通过: {summary['total_fixes'] - summary['total_passed']}")
    print()
    print(f"  关键修复 (CRITICAL): {summary['critical_passed']}/{summary['critical_total']} 通过")
    print(f"  建议修复 (SHOULD_FIX): {summary['should_fix_passed']}/{summary['should_fix_total']} 通过")
    print(f"  可选修复 (NICE_TO_HAVE): {summary['nice_to_have_passed']}/{summary['nice_to_have_total']} 通过")

    # 打印GO/NO-GO决策
    print("\n" + "="*80)
    if summary['go_decision']:
        print("✅ 决策: GO")
        print("   所有关键修复已通过，建议修复通过率≥80%")
        print("   Story 10.11.1可以进入开发阶段")
    else:
        print("❌ 决策: NO-GO")
        if summary['critical_passed'] < summary['critical_total']:
            print(f"   未通过的关键修复: {summary['critical_total'] - summary['critical_passed']}个")
        if summary['should_fix_passed'] < (summary['should_fix_total'] * 0.8):
            print(f"   建议修复通过率不足: {round((summary['should_fix_passed']/summary['should_fix_total'])*100, 1)}% < 80%")
        print("   请修复上述问题后重新验证")
    print("="*80 + "\n")


def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("用法: python verify-10.11.1-fixes.py <story_file_path>")
        print("\n示例:")
        print("  python verify-10.11.1-fixes.py docs/stories/10.11.1.story.md")
        print("  python verify-10.11.1-fixes.py docs/stories/10.11.1.story-FIXED.md")
        sys.exit(1)

    file_path = sys.argv[1]

    print("开始验证Story 10.11.1的修复...")
    result = verify_story_fixes(file_path)
    print_results(result)

    # 退出码：GO返回0，NO-GO返回1
    if result['success'] and result['summary']['go_decision']:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
