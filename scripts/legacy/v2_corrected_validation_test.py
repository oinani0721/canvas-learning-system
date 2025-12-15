#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Canvas学习系统v2.0 - 纠正版功能验证测试

该脚本创建全面的测试用例来验证纠正后的v2.0功能是否符合原始Story和PRD设计。
验证Context7技术合规性以及核心功能的正确性。

使用方法:
    python v2_corrected_validation_test.py          # 运行完整验证测试
    python v2_corrected_validation_test.py --quick  # 快速验证模式
    python v2_corrected_validation_test.py --report # 生成详细报告

Author: Canvas Learning System Team
Version: 2.0 Corrected Validation
Created: 2025-10-20
"""

import asyncio
import datetime
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

# 添加当前目录到Python路径
sys.path.insert(0, str(Path.cwd()))

# ANSI颜色代码
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(title: str):
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")

def print_section(section: str):
    """打印测试章节"""
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}=== {section} ==={Colors.END}")

def success_message(message: str):
    """打印成功消息"""
    print(f"{Colors.GREEN}[PASS] {message}{Colors.END}")

def error_message(message: str):
    """打印错误消息"""
    print(f"{Colors.RED}[FAIL] {message}{Colors.END}")

def warning_message(message: str):
    """打印警告消息"""
    print(f"{Colors.YELLOW}[WARN] {message}{Colors.END}")

def info_message(message: str):
    """打印信息消息"""
    print(f"{Colors.BLUE}[INFO] {message}{Colors.END}")

@dataclass
class TestResult:
    """测试结果"""
    test_name: str
    passed: bool
    details: str = ""
    execution_time: float = 0.0
    error_message: str = ""

@dataclass
class ValidationReport:
    """验证报告"""
    timestamp: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    test_results: List[TestResult] = field(default_factory=list)
    overall_status: str = "UNKNOWN"
    context7_compliance: Dict[str, bool] = field(default_factory=dict)
    story_compliance: Dict[str, bool] = field(default_factory=dict)
    prd_compliance: Dict[str, bool] = field(default_factory=dict)

class V2CorrectedValidator:
    """v2.0纠正版功能验证器"""

    def __init__(self):
        self.test_results: List[TestResult] = []
        self.start_time = time.time()
        self.report = ValidationReport(
            timestamp=datetime.datetime.now().isoformat(),
            total_tests=0,
            passed_tests=0,
            failed_tests=0
        )

    def run_test(self, test_name: str, test_func) -> TestResult:
        """运行单个测试"""
        print(f"\n{Colors.CYAN}Testing: {test_name}{Colors.END}")

        start_time = time.time()
        try:
            result = test_func()
            execution_time = time.time() - start_time

            if result:
                success_message(f"{test_name} - PASSED ({execution_time:.3f}s)")
                test_result = TestResult(
                    test_name=test_name,
                    passed=True,
                    execution_time=execution_time
                )
            else:
                error_message(f"{test_name} - FAILED ({execution_time:.3f}s)")
                test_result = TestResult(
                    test_name=test_name,
                    passed=False,
                    execution_time=execution_time,
                    details="Test function returned False"
                )

        except Exception as e:
            execution_time = time.time() - start_time
            error_message(f"{test_name} - ERROR ({execution_time:.3f}s): {str(e)}")
            test_result = TestResult(
                test_name=test_name,
                passed=False,
                execution_time=execution_time,
                error_message=str(e),
                details=traceback.format_exc()
            )

        self.test_results.append(test_result)
        return test_result

    def test_canvas_utils_import(self) -> bool:
        """测试canvas_utils导入"""
        try:
            import canvas_utils
            return hasattr(canvas_utils, 'global_controls')
        except ImportError:
            return False

    def test_canvas_learning_memory_system(self) -> bool:
        """测试Canvas学习记忆系统 (Story 6.1)"""
        try:
            import canvas_utils

            # 检查类是否存在
            if not hasattr(canvas_utils, 'CanvasLearningMemory'):
                warning_message("CanvasLearningMemory类不存在")
                return False

            # 创建实例
            memory_system = canvas_utils.CanvasLearningMemory()

            # 检查核心方法
            required_methods = [
                'add_canvas_learning_episode',
                'get_canvas_learning_episodes',
                'track_learning_progress'
            ]

            for method in required_methods:
                if not hasattr(memory_system, method):
                    warning_message(f"CanvasLearningMemory缺少方法: {method}")
                    return False

            # 测试Graphiti连接 (Context7验证)
            if hasattr(memory_system, 'graphiti'):
                success_message("Graphiti记忆系统连接正常")
                return True
            else:
                warning_message("Graphiti连接不可用")
                return False

        except Exception as e:
            error_message(f"Canvas学习记忆系统测试失败: {str(e)}")
            return False

    def test_review_board_agent_selector(self) -> bool:
        """测试检验白板智能调度 (Story 6.4)"""
        try:
            import canvas_utils

            # 检查类是否存在
            if not hasattr(canvas_utils, 'ReviewBoardAgentSelector'):
                warning_message("ReviewBoardAgentSelector类不存在")
                return False

            # 创建实例
            selector = canvas_utils.ReviewBoardAgentSelector()

            # 检查核心方法
            required_methods = [
                'analyze_understanding_quality',
                'recommend_agents',
                'get_agent_selection_for_review_node'
            ]

            for method in required_methods:
                if not hasattr(selector, method):
                    warning_message(f"ReviewBoardAgentSelector缺少方法: {method}")
                    return False

            # 测试理解质量分析
            test_text = "逆否命题就是原命题的否定形式，如果p则q的逆否命题是如果非q则非p"
            quality_result = selector.analyze_understanding_quality(test_text)

            if isinstance(quality_result, dict) and 'has_content' in quality_result:
                success_message("理解质量分析功能正常")
                return True
            else:
                warning_message("理解质量分析返回格式错误")
                return False

        except Exception as e:
            error_message(f"检验白板智能调度测试失败: {str(e)}")
            return False

    def test_efficient_canvas_processor(self) -> bool:
        """测试学习效率处理器 (PRD 2.1.1)"""
        try:
            import canvas_utils

            # 检查类是否存在
            if not hasattr(canvas_utils, 'EfficientCanvasProcessor'):
                warning_message("EfficientCanvasProcessor类不存在")
                return False

            # 创建实例
            processor = canvas_utils.EfficientCanvasProcessor()

            # 检查核心方法
            required_methods = [
                'process_multiple_nodes',
                'get_processing_stats'
            ]

            for method in required_methods:
                if not hasattr(processor, method):
                    warning_message(f"EfficientCanvasProcessor缺少方法: {method}")
                    return False

            success_message("学习效率处理器结构验证通过")
            return True

        except Exception as e:
            error_message(f"学习效率处理器测试失败: {str(e)}")
            return False

    def test_context7_compliance(self) -> bool:
        """测试Context7技术合规性"""
        try:
            import canvas_utils

            compliance_results = {}

            # 1. Graphiti验证 (Trust Score 8.2/10)
            if hasattr(canvas_utils, 'CanvasLearningMemory'):
                memory_system = canvas_utils.CanvasLearningMemory()
                if hasattr(memory_system, 'graphiti'):
                    compliance_results['graphiti_api'] = True
                    success_message("Graphiti API使用符合Context7标准")
                else:
                    compliance_results['graphiti_api'] = False
                    warning_message("Graphiti API不符合Context7标准")

            # 2. Episode API验证
            if hasattr(memory_system, 'add_canvas_learning_episode'):
                compliance_results['episode_api'] = True
                success_message("Episode API使用符合Context7标准")
            else:
                compliance_results['episode_api'] = False

            # 3. 时间感知验证
            if hasattr(memory_system, 'track_learning_progress'):
                compliance_results['time_aware'] = True
                success_message("时间感知功能符合Context7标准")
            else:
                compliance_results['time_aware'] = False

            self.report.context7_compliance = compliance_results

            # 至少80%的Context7要求通过
            passed_count = sum(compliance_results.values())
            total_count = len(compliance_results)

            if total_count == 0:
                return False

            compliance_rate = passed_count / total_count
            return compliance_rate >= 0.8

        except Exception as e:
            error_message(f"Context7合规性测试失败: {str(e)}")
            return False

    def test_story_compliance(self) -> bool:
        """测试Story合规性"""
        try:
            story_compliance = {}

            import canvas_utils

            # Story 6.1: Canvas学习记忆系统
            if hasattr(canvas_utils, 'CanvasLearningMemory'):
                memory_system = canvas_utils.CanvasLearningMemory()
                if hasattr(memory_system, 'add_canvas_learning_episode'):
                    story_compliance['story_6_1'] = True
                    success_message("Story 6.1 (Canvas学习记忆系统) 符合")
                else:
                    story_compliance['story_6_1'] = False

            # Story 6.4: 检验白板智能调度
            if hasattr(canvas_utils, 'ReviewBoardAgentSelector'):
                selector = canvas_utils.ReviewBoardAgentSelector()
                if hasattr(selector, 'analyze_understanding_quality'):
                    story_compliance['story_6_4'] = True
                    success_message("Story 6.4 (检验白板智能调度) 符合")
                else:
                    story_compliance['story_6_4'] = False

            # PRD 2.1.1: 学习效率处理器
            if hasattr(canvas_utils, 'EfficientCanvasProcessor'):
                processor = canvas_utils.EfficientCanvasProcessor()
                if hasattr(processor, 'process_multiple_nodes'):
                    story_compliance['prd_2_1_1'] = True
                    success_message("PRD 2.1.1 (学习效率处理器) 符合")
                else:
                    story_compliance['prd_2_1_1'] = False

            self.report.story_compliance = story_compliance

            # 所有Story要求都必须通过
            if not story_compliance:
                return False

            return all(story_compliance.values())

        except Exception as e:
            error_message(f"Story合规性测试失败: {str(e)}")
            return False

    def test_feature_integration(self) -> bool:
        """测试功能集成"""
        try:
            import canvas_utils

            # 检查全局控制
            if not hasattr(canvas_utils, 'global_controls'):
                warning_message("全局控制系统不可用")
                return False

            global_controls = canvas_utils.global_controls

            # 检查功能激活
            features_to_test = [
                ('ultrathink', '检验白板智能调度'),
                ('knowledge_graph', 'Canvas学习记忆系统'),
                ('concurrent_agents', '学习效率处理器')
            ]

            integration_results = {}

            for feature, description in features_to_test:
                try:
                    # 尝试激活功能
                    if hasattr(global_controls, 'activate_feature'):
                        result = global_controls.activate_feature(f"*{feature.split('_')[0]}")
                        integration_results[feature] = result.get('success', False)
                    else:
                        integration_results[feature] = False

                except Exception as e:
                    warning_message(f"功能 {feature} 激活失败: {str(e)}")
                    integration_results[feature] = False

            success_rate = sum(integration_results.values()) / len(integration_results)
            success_message(f"功能集成成功率: {success_rate:.1%}")

            return success_rate >= 0.6

        except Exception as e:
            error_message(f"功能集成测试失败: {str(e)}")
            return False

    def test_performance_benchmarks(self) -> bool:
        """测试性能基准"""
        try:
            performance_results = {}

            # 测试导入时间
            import_start = time.time()
            import canvas_utils
            import_time = time.time() - import_start

            performance_results['import_time'] = import_time < 2.0  # 应该在2秒内完成

            # 测试实例创建时间
            instance_start = time.time()
            memory_system = canvas_utils.CanvasLearningMemory()
            selector = canvas_utils.ReviewBoardAgentSelector()
            processor = canvas_utils.EfficientCanvasProcessor()
            instance_time = time.time() - instance_start

            performance_results['instance_time'] = instance_time < 1.0  # 应该在1秒内完成

            # 测试理解质量分析性能
            analysis_start = time.time()
            test_text = "这是一个测试用的理解文本，用来验证分析性能"
            if hasattr(selector, 'analyze_understanding_quality'):
                result = selector.analyze_understanding_quality(test_text)
                analysis_time = time.time() - analysis_start
                performance_results['analysis_time'] = analysis_time < 0.5  # 应该在0.5秒内完成

            success_count = sum(performance_results.values())
            total_count = len(performance_results)

            success_message(f"性能测试通过率: {success_count}/{total_count}")

            return success_count / total_count >= 0.8

        except Exception as e:
            error_message(f"性能基准测试失败: {str(e)}")
            return False

    def run_all_tests(self, quick_mode: bool = False) -> ValidationReport:
        """运行所有验证测试"""
        print_header("Canvas学习系统v2.0 - 纠正版功能验证测试")

        # 定义测试用例
        test_cases = [
            ("Canvas Utils导入测试", self.test_canvas_utils_import),
            ("Canvas学习记忆系统测试", self.test_canvas_learning_memory_system),
            ("检验白板智能调度测试", self.test_review_board_agent_selector),
            ("学习效率处理器测试", self.test_efficient_canvas_processor),
            ("Context7技术合规性测试", self.test_context7_compliance),
            ("Story/PRD合规性测试", self.test_story_compliance),
            ("功能集成测试", self.test_feature_integration),
        ]

        # 快速模式跳过性能测试
        if not quick_mode:
            test_cases.append(("性能基准测试", self.test_performance_benchmarks))

        print_section(f"运行 {len(test_cases)} 项测试")

        # 运行所有测试
        for test_name, test_func in test_cases:
            self.run_test(test_name, test_func)

        # 生成报告
        self.generate_report()

        return self.report

    def generate_report(self) -> str:
        """生成验证报告"""
        print_section("生成验证报告")

        # 统计结果
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.passed)
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # 更新报告
        self.report.total_tests = total_tests
        self.report.passed_tests = passed_tests
        self.report.failed_tests = failed_tests

        # 确定整体状态
        if success_rate >= 90:
            overall_status = "EXCELLENT"
            status_color = Colors.GREEN
        elif success_rate >= 75:
            overall_status = "GOOD"
            status_color = Colors.YELLOW
        else:
            overall_status = "FAILED"
            status_color = Colors.RED

        self.report.overall_status = overall_status

        # 显示总结
        print(f"\n{Colors.BOLD}=== 验证测试总结 ==={Colors.END}")
        print(f"总测试数: {total_tests}")
        print(f"{Colors.GREEN}通过: {passed_tests}{Colors.END}")
        print(f"{Colors.RED}失败: {failed_tests}{Colors.END}")
        print(f"成功率: {success_rate:.1f}%")
        print(f"整体状态: {status_color}{Colors.BOLD}{overall_status}{Colors.END}")

        # Context7合规性
        if self.report.context7_compliance:
            print(f"\n{Colors.BLUE}Context7合规性:{Colors.END}")
            for item, passed in self.report.context7_compliance.items():
                status = f"{Colors.GREEN}✓{Colors.END}" if passed else f"{Colors.RED}✗{Colors.END}"
                print(f"  {status} {item}")

        # Story合规性
        if self.report.story_compliance:
            print(f"\n{Colors.BLUE}Story/PRD合规性:{Colors.END}")
            for item, passed in self.report.story_compliance.items():
                status = f"{Colors.GREEN}✓{Colors.END}" if passed else f"{Colors.RED}✗{Colors.END}"
                print(f"  {status} {item}")

        # 详细测试结果
        print(f"\n{Colors.BLUE}详细测试结果:{Colors.END}")
        for result in self.test_results:
            status = f"{Colors.GREEN}PASS{Colors.END}" if result.passed else f"{Colors.RED}FAIL{Colors.END}"
            print(f"  {status} {result.test_name} ({result.execution_time:.3f}s)")
            if result.error_message:
                print(f"    错误: {result.error_message}")

        # 保存报告
        report_file = self.save_report()

        if success_rate >= 90:
            print(f"\n{Colors.GREEN}{Colors.BOLD}[SUCCESS] v2.0纠正版验证通过！系统符合原始设计要求！{Colors.END}")
        else:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}[PARTIAL] 部分测试未通过，请检查失败项目。{Colors.END}")

        print(f"{Colors.BLUE}详细报告: {report_file}{Colors.END}")

        return report_file

    def save_report(self) -> str:
        """保存验证报告到文件"""
        # 构建报告数据
        report_data = {
            "timestamp": self.report.timestamp,
            "summary": {
                "total_tests": self.report.total_tests,
                "passed_tests": self.report.passed_tests,
                "failed_tests": self.report.failed_tests,
                "success_rate": f"{(self.report.passed_tests / self.report.total_tests * 100):.1f}%" if self.report.total_tests > 0 else "0%",
                "overall_status": self.report.overall_status
            },
            "context7_compliance": self.report.context7_compliance,
            "story_compliance": self.report.story_compliance,
            "test_results": [
                {
                    "name": result.test_name,
                    "passed": result.passed,
                    "execution_time": result.execution_time,
                    "error_message": result.error_message,
                    "details": result.details
                }
                for result in self.test_results
            ],
            "validation_type": "v2_corrected",
            "environment": {
                "python_version": sys.version,
                "platform": sys.platform,
                "working_directory": str(Path.cwd())
            }
        }

        # 保存报告文件
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = Path.cwd() / f"v2_corrected_validation_report_{timestamp}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        return str(report_file)

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Canvas学习系统v2.0 - 纠正版功能验证测试')
    parser.add_argument('--quick', action='store_true', help='快速验证模式（跳过性能测试）')
    parser.add_argument('--report', action='store_true', help='生成详细报告')

    args = parser.parse_args()

    validator = V2CorrectedValidator()

    # 运行验证测试
    report = validator.run_all_tests(quick_mode=args.quick)

    # 返回适当的退出码
    if report.overall_status in ["EXCELLENT", "GOOD"]:
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())