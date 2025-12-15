#!/usr/bin/env python3
"""
系统性诊断canvas_utils.py语法问题
"""

import ast
import sys
import os

def analyze_syntax_errors(filepath):
    """分析语法错误"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        print("解析AST中...")
        try:
            tree = ast.parse(content, filename=filepath)
            print("AST解析成功，检查潜在问题...")
            check_ast_issues(tree, content)
            return []
    except SyntaxError as e:
        print(f"语法错误: {e}")
        return [str(e)]

def check_ast_issues(tree, content):
    """检查AST中的潜在问题"""
    issues = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # 检查函数的缩进
            if hasattr(node, 'col_offset'):
                lines = content.split('\n')
                if node.lineno <= len(lines):
                    line_content = lines[node.lineno - 1]
                    leading_spaces = len(line_content) - len(line_content.lstrip())
                    print(f"函数 {node.name} at line {node.lineno}: {leading_spaces} leading spaces")

        elif isinstance(node, ast.ClassDef):
            # 检查类的缩进
            lines = content.split('\n')
            if node.lineno <= len(lines):
                line_content = lines[node.lineno - 1]
                leading_spaces = len(line_content) - len(line_content.lstrip())
                print(f"类 {node.name} at line {node.lineno}: {leading_spaces} leading spaces")

    return issues

def find_indentation_problems(filepath):
    """查找缩进问题"""
    print("检查缩进问题...")

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    issues = []
    for i, line in enumerate(lines, 1):
        stripped = line.lstrip()
        if stripped.startswith('def ') or stripped.startswith('async def ') or stripped.startswith('class '):
            # 这是一个定义行，检查缩进
            leading_spaces = len(line) - len(stripped)

            # 查找上一个非空行
            prev_line = ""
            for j in range(i - 2, -1, -1):
                if lines[j].strip():
                    prev_line = lines[j]
                    break

            # 计算期望的缩进
            if 'class ' in stripped:
                expected_spaces = 0  # 类应该在顶层
            elif 'def ' in stripped or 'async def ' in stripped:
                if prev_line.strip() == 'except:' or prev_line.strip() == 'finally:':
                    expected_spaces = 8  # except/finally块中的函数应该缩进8个空格
                else:
                    expected_spaces = 4  # 正常缩进4个空格

            if leading_spaces != expected_spaces:
                issues.append((i, leading_spaces, expected_spaces, line.strip()[:50]))

    return issues

def fix_indentation_problems(filepath, issues):
    """修复缩进问题"""
    print(f"发现 {len(issues)} 个缩进问题，开始修复...")

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 修复缩进
    for line_num, actual_spaces, expected_spaces, content in issues:
        if line_num <= len(lines):
            # 计算需要调整的空格数
            spaces_diff = expected_spaces - actual_spaces
            if spaces_diff != 0:
                # 修复这一行
                lines[line_num - 1] = ' ' * expected_spaces + lines[line_num - 1].lstrip()
                print(f"修复第{line_num}行: 从{actual_spaces}个空格调整到{expected_spaces}个空格")

    # 写回文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print("缩进问题修复完成")

def main():
    """主函数"""
    filepath = "canvas_utils.py"

    if not os.path.exists(filepath):
        print(f"文件不存在: {filepath}")
        return False

    print(f"开始分析 {filepath} 的语法问题...")

    # 检查语法错误
    syntax_errors = analyze_syntax_errors(filepath)

    if syntax_errors:
        print(f"发现 {len(syntax_errors)} 个语法错误:")
        for error in syntax_errors:
            print(f"  - {error}")
        return False

    # 检查缩进问题
    indent_issues = find_indentation_problems(filepath)

    if indent_issues:
        print(f"发现 {len(indent_issues)} 个缩进问题:")
        for line_num, actual, expected, content in indent_issues[:10]:  # 显示前10个
            print(f"  第{line_num}行: 实际缩进{actual}个空格，期望{expected}个空格")

        try:
            fix_indentation_problems(filepath, indent_issues)
            print("缩进问题已修复")
        except Exception as e:
            print(f"修复缩进问题时出错: {e}")
            return False

    print("语法和缩进检查完成")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)