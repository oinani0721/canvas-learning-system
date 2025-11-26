#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gherkin Feature File Validation Script
验证Gherkin .feature文件的语法和结构

功能:
1. 验证Gherkin语法正确性
2. 检查必需的关键字 (Feature, Scenario, Given/When/Then)
3. 验证场景结构完整性
4. 检查步骤定义是否有对应测试文件

用法:
  python scripts/validate-gherkin.py [feature_files...]

参数:
  feature_files - 要验证的.feature文件列表，如果不提供则验证所有

返回码:
  0 - 验证通过
  1 - 验证失败

Context7 Reference:
  - Cucumber/Gherkin: /cucumber/docs (260 snippets, Benchmark 75.6)
  - pytest-bdd: /pytest-dev/pytest-bdd (79 snippets, Benchmark 82.3)
"""

import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field


# =============================================================================
# Gherkin Keywords (支持中英文)
# =============================================================================

GHERKIN_KEYWORDS = {
    'feature': ['Feature', '功能', 'Functionality'],
    'background': ['Background', '背景'],
    'scenario': ['Scenario', '场景', 'Example'],
    'scenario_outline': ['Scenario Outline', '场景大纲', 'Scenario Template'],
    'given': ['Given', '假如', '假设', '假定'],
    'when': ['When', '当', '如果'],
    'then': ['Then', '那么', '则'],
    'and': ['And', '并且', '而且', '同时'],
    'but': ['But', '但是', '但'],
    'examples': ['Examples', '例子', 'Scenarios'],
    'rule': ['Rule', '规则'],
}


@dataclass
class ValidationResult:
    """验证结果"""
    file_path: Path
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    scenarios_count: int = 0
    steps_count: int = 0


@dataclass
class GherkinScenario:
    """Gherkin场景"""
    name: str
    line_number: int
    steps: List[Tuple[str, str, int]] = field(default_factory=list)  # (keyword, text, line)
    has_given: bool = False
    has_when: bool = False
    has_then: bool = False


# =============================================================================
# Helper Functions
# =============================================================================

def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent


def is_keyword(line: str, keyword_type: str) -> bool:
    """检查行是否以指定类型的关键字开头"""
    stripped = line.strip()
    for kw in GHERKIN_KEYWORDS.get(keyword_type, []):
        if stripped.startswith(kw + ':') or stripped.startswith(kw + ' '):
            return True
    return False


def get_keyword_type(line: str) -> Optional[str]:
    """获取行的关键字类型"""
    stripped = line.strip()
    for kw_type, keywords in GHERKIN_KEYWORDS.items():
        for kw in keywords:
            if stripped.startswith(kw + ':') or stripped.startswith(kw + ' '):
                return kw_type
    return None


def extract_step_text(line: str) -> Tuple[Optional[str], str]:
    """提取步骤的关键字和文本"""
    stripped = line.strip()
    for kw_type in ['given', 'when', 'then', 'and', 'but']:
        for kw in GHERKIN_KEYWORDS.get(kw_type, []):
            if stripped.startswith(kw + ' '):
                return kw_type, stripped[len(kw) + 1:].strip()
    return None, stripped


# =============================================================================
# Validation Functions
# =============================================================================

def validate_encoding(file_path: Path) -> Tuple[bool, str]:
    """验证文件编码为UTF-8"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read()
        return True, ""
    except UnicodeDecodeError as e:
        return False, f"File encoding error: {e}. Feature files must be UTF-8 encoded."


def validate_feature_declaration(lines: List[str], file_path: Path) -> List[str]:
    """验证Feature声明"""
    errors = []
    feature_found = False
    feature_line = 0

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # 跳过空行和注释
        if not stripped or stripped.startswith('#') or stripped.startswith('@'):
            continue

        if is_keyword(line, 'feature'):
            feature_found = True
            feature_line = i

            # 检查Feature名称
            for kw in GHERKIN_KEYWORDS['feature']:
                if stripped.startswith(kw + ':'):
                    feature_name = stripped[len(kw) + 1:].strip()
                    if not feature_name:
                        errors.append(f"Line {i}: Feature has no name")
                    break
            break
        else:
            # 非注释/标签/空行的第一行应该是Feature
            errors.append(f"Line {i}: Expected 'Feature:' declaration, found: {stripped[:50]}")
            break

    if not feature_found:
        errors.append(f"{file_path}: No Feature declaration found")

    return errors


def validate_scenarios(lines: List[str], file_path: Path) -> Tuple[List[str], List[str], int]:
    """验证所有场景"""
    errors = []
    warnings = []
    scenarios: List[GherkinScenario] = []
    current_scenario: Optional[GherkinScenario] = None
    in_background = False
    in_examples = False
    last_step_type = None

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # 跳过空行、注释
        if not stripped or stripped.startswith('#'):
            continue

        kw_type = get_keyword_type(line)

        # Background
        if kw_type == 'background':
            in_background = True
            in_examples = False
            current_scenario = None
            last_step_type = None
            continue

        # Scenario / Scenario Outline
        if kw_type in ['scenario', 'scenario_outline']:
            in_background = False
            in_examples = False

            # 保存之前的场景
            if current_scenario:
                scenarios.append(current_scenario)

            # 提取场景名称
            for kw in GHERKIN_KEYWORDS[kw_type]:
                if stripped.startswith(kw + ':'):
                    name = stripped[len(kw) + 1:].strip()
                    break
                elif stripped.startswith(kw + ' '):
                    # 有时候Scenario后面没有冒号
                    name = stripped[len(kw) + 1:].strip()
                    break
            else:
                name = "Unnamed"

            current_scenario = GherkinScenario(name=name, line_number=i)
            last_step_type = None
            continue

        # Examples
        if kw_type == 'examples':
            in_examples = True
            continue

        # Rule
        if kw_type == 'rule':
            continue

        # Steps (Given/When/Then/And/But)
        if kw_type in ['given', 'when', 'then', 'and', 'but']:
            step_kw, step_text = extract_step_text(stripped)

            if in_background:
                # Background中的步骤
                last_step_type = step_kw if step_kw not in ['and', 'but'] else last_step_type
            elif current_scenario:
                # 记录步骤
                current_scenario.steps.append((step_kw, step_text, i))

                # 跟踪Given/When/Then状态
                if step_kw == 'given':
                    current_scenario.has_given = True
                    last_step_type = 'given'
                elif step_kw == 'when':
                    current_scenario.has_when = True
                    last_step_type = 'when'
                elif step_kw == 'then':
                    current_scenario.has_then = True
                    last_step_type = 'then'
                elif step_kw in ['and', 'but']:
                    # And/But继承前一个步骤的类型
                    if last_step_type == 'given':
                        current_scenario.has_given = True
                    elif last_step_type == 'when':
                        current_scenario.has_when = True
                    elif last_step_type == 'then':
                        current_scenario.has_then = True

    # 保存最后一个场景
    if current_scenario:
        scenarios.append(current_scenario)

    # 验证每个场景
    for scenario in scenarios:
        # 检查是否有步骤
        if not scenario.steps:
            errors.append(f"Line {scenario.line_number}: Scenario '{scenario.name}' has no steps")
            continue

        # 检查Given-When-Then结构
        if not scenario.has_given and not scenario.has_when and not scenario.has_then:
            errors.append(
                f"Line {scenario.line_number}: Scenario '{scenario.name}' "
                "has no Given/When/Then steps"
            )
        elif not scenario.has_then:
            warnings.append(
                f"Line {scenario.line_number}: Scenario '{scenario.name}' "
                "has no Then step (no assertion)"
            )

    # 检查是否有场景
    if not scenarios:
        errors.append(f"{file_path}: No Scenario found in feature file")

    return errors, warnings, len(scenarios)


def check_corresponding_test_file(file_path: Path) -> Tuple[bool, str]:
    """检查是否有对应的pytest-bdd测试文件"""
    project_root = get_project_root()
    feature_name = file_path.stem  # e.g., 'scoring-agent'

    # 期望的测试文件位置
    test_patterns = [
        project_root / 'tests' / 'bdd' / f'test_{feature_name.replace("-", "_")}.py',
        project_root / 'tests' / 'bdd' / f'test_{feature_name}.py',
    ]

    for test_path in test_patterns:
        if test_path.exists():
            return True, str(test_path)

    return False, ""


def validate_step_consistency(lines: List[str]) -> List[str]:
    """检查步骤定义的一致性"""
    warnings = []
    steps_seen = {}

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        kw_type = get_keyword_type(line)

        if kw_type in ['given', 'when', 'then']:
            _, step_text = extract_step_text(stripped)

            # 提取步骤模式（忽略引号内的内容）
            pattern = re.sub(r'"[^"]*"', '"{}"', step_text)
            pattern = re.sub(r'\d+', '{n}', pattern)

            if pattern in steps_seen:
                if steps_seen[pattern] != step_text:
                    pass  # 不同参数的相同模式是正常的
            else:
                steps_seen[pattern] = step_text

    return warnings


def validate_feature_file(file_path: Path) -> ValidationResult:
    """
    验证单个Feature文件

    Returns:
        ValidationResult: 验证结果
    """
    result = ValidationResult(file_path=file_path)

    # 1. 验证文件编码
    valid, error_msg = validate_encoding(file_path)
    if not valid:
        result.errors.append(f"{file_path}: {error_msg}")
        return result

    # 2. 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')

    # 3. 验证Feature声明
    feature_errors = validate_feature_declaration(lines, file_path)
    result.errors.extend(feature_errors)

    if feature_errors:
        return result  # Feature声明错误，不继续检查

    # 4. 验证场景
    scenario_errors, scenario_warnings, scenarios_count = validate_scenarios(lines, file_path)
    result.errors.extend(scenario_errors)
    result.warnings.extend(scenario_warnings)
    result.scenarios_count = scenarios_count

    # 5. 检查步骤一致性
    consistency_warnings = validate_step_consistency(lines)
    result.warnings.extend(consistency_warnings)

    # 6. 检查对应的测试文件
    has_test, test_path = check_corresponding_test_file(file_path)
    if not has_test:
        result.warnings.append(
            f"{file_path.name}: No corresponding pytest-bdd test file found. "
            f"Expected at: tests/bdd/test_{file_path.stem.replace('-', '_')}.py"
        )
    else:
        # 统计步骤数
        result.steps_count = sum(
            1 for line in lines
            if get_keyword_type(line) in ['given', 'when', 'then', 'and', 'but']
        )

    return result


# =============================================================================
# Main Function
# =============================================================================

def main():
    """主函数"""
    print("=" * 60)
    print("Gherkin Feature File Validation")
    print("=" * 60)

    # 确定要验证的文件
    if len(sys.argv) > 1:
        # 验证指定的文件
        files_to_validate = [Path(f) for f in sys.argv[1:]]
    else:
        # 验证所有Feature文件
        behavior_dir = get_project_root() / 'specs' / 'behavior'
        if not behavior_dir.exists():
            print(f"Behavior directory not found: {behavior_dir}")
            return 0

        files_to_validate = list(behavior_dir.glob('*.feature'))

    if not files_to_validate:
        print("No feature files to validate")
        return 0

    print(f"Validating {len(files_to_validate)} feature file(s)...\n")

    # 验证每个文件
    all_results: List[ValidationResult] = []

    for file_path in files_to_validate:
        if not file_path.exists():
            print(f"File not found: {file_path}")
            all_results.append(ValidationResult(
                file_path=file_path,
                errors=[f"File not found: {file_path}"]
            ))
            continue

        print(f"Validating: {file_path.name}...", end=" ")
        result = validate_feature_file(file_path)
        all_results.append(result)

        if result.errors:
            print("FAILED")
        elif result.warnings:
            print(f"WARNINGS ({result.scenarios_count} scenarios)")
        else:
            print(f"OK ({result.scenarios_count} scenarios, {result.steps_count} steps)")

    # 打印汇总
    print("\n" + "=" * 60)

    total_errors = sum(len(r.errors) for r in all_results)
    total_warnings = sum(len(r.warnings) for r in all_results)
    total_scenarios = sum(r.scenarios_count for r in all_results)

    if total_errors:
        print("\nERRORS:")
        for result in all_results:
            for error in result.errors:
                print(f"  {error}")

    if total_warnings:
        print("\nWARNINGS:")
        for result in all_results:
            for warning in result.warnings:
                print(f"  {warning}")

    # 统计
    print(f"\nSummary:")
    print(f"  Files validated: {len(files_to_validate)}")
    print(f"  Total scenarios: {total_scenarios}")
    print(f"  Errors: {total_errors}")
    print(f"  Warnings: {total_warnings}")

    if not total_errors:
        print("\nAll feature files validated successfully!")

    print("=" * 60)

    # 返回码：只有errors才返回1
    return 1 if total_errors else 0


if __name__ == "__main__":
    sys.exit(main())
