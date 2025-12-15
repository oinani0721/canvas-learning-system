#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Canvas学习系统v2.0 - 一键启用功能脚本

该脚本会自动启用所有v2.0功能，检查依赖，并提供个性化配置建议。
运行此脚本可以快速启动v2.0的所有AI增强功能。

使用方法:
    python enable_v2_features.py          # 启用所有功能
    python enable_v2_features.py --check  # 仅检查状态
    python enable_v2_features.py --help   # 查看帮助

Author: Canvas Learning System Team
Version: 2.0
Created: 2025-10-20
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

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
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")

def print_step(step: str, description: str):
    """打印步骤"""
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}[STEP] 步骤 {step}: {description}{Colors.END}")
    print(f"{Colors.MAGENTA}{'-'*50}{Colors.END}")

def success_message(message: str):
    """打印成功消息"""
    print(f"{Colors.GREEN}[OK] {message}{Colors.END}")

def error_message(message: str):
    """打印错误消息"""
    print(f"{Colors.RED}[FAIL] {message}{Colors.END}")

def warning_message(message: str):
    """打印警告消息"""
    print(f"{Colors.YELLOW}[WARN] {message}{Colors.END}")

def info_message(message: str):
    """打印信息消息"""
    print(f"{Colors.BLUE}[INFO] {message}{Colors.END}")

class V2FeatureEnabler:
    """v2.0功能启用器"""

    def __init__(self):
        self.enabled_features = []
        self.failed_features = []
        self.warnings = []
        self.start_time = datetime.now()
        self.correction_notes = []

    def check_canvas_import(self) -> bool:
        """检查canvas_utils导入"""
        try:
            import canvas_utils
            success_message("canvas_utils.py导入成功")
            return True
        except ImportError as e:
            error_message(f"无法导入canvas_utils.py: {e}")
            return False

    def enable_all_features(self) -> Dict[str, Any]:
        """启用所有v2.0功能"""
        try:
            import canvas_utils
            global_controls = canvas_utils.global_controls

            # 功能列表
            features = [
                ("ultrathink", "*ultrathink", "UltraThink智能分析"),
                ("ebbinghaus_review", "*review", "艾宾浩斯复习系统"),
                ("concurrent_agents", "*concurrent", "多Agent并发处理"),
                ("knowledge_graph", "*graph", "Graphiti知识图谱"),
                ("smart_clipboard", "*clipboard", "智能剪贴板"),
            ]

            print_step("1", "启用v2.0核心功能")

            results = {}
            for feature, keyword, description in features:
                try:
                    # 检查功能可用性
                    if hasattr(global_controls, 'is_enabled') and global_controls.is_enabled(feature):
                        success_message(f"{description} - 已经启用")
                        results[feature] = {"status": "already_enabled", "keyword": keyword}
                        self.enabled_features.append(feature)
                        continue

                    # 尝试激活功能
                    if hasattr(global_controls, 'activate_feature'):
                        activation_result = global_controls.activate_feature(keyword)
                        if activation_result.get("success", False):
                            success_message(f"{description} - 启用成功")
                            results[feature] = {"status": "enabled", "keyword": keyword}
                            self.enabled_features.append(feature)
                        else:
                            error_message(f"{description} - 启用失败: {activation_result.get('message', '未知错误')}")
                            results[feature] = {"status": "failed", "error": activation_result.get('message')}
                            self.failed_features.append(feature)
                    else:
                        # 备用方法：直接设置状态
                        if hasattr(global_controls, 'feature_status'):
                            global_controls.feature_status[feature] = True
                            success_message(f"{description} - 启用成功（备用方法）")
                            results[feature] = {"status": "enabled", "keyword": keyword}
                            self.enabled_features.append(feature)
                        else:
                            error_message(f"{description} - 功能控制器不可用")
                            results[feature] = {"status": "failed", "error": "功能控制器不可用"}
                            self.failed_features.append(feature)

                except Exception as e:
                    error_message(f"{description} - 启用异常: {str(e)}")
                    results[feature] = {"status": "error", "error": str(e)}
                    self.failed_features.append(feature)

            return results

        except Exception as e:
            error_message(f"启用功能时发生错误: {e}")
            return {}

    def verify_feature_status(self) -> Dict[str, Any]:
        """验证功能状态"""
        print_step("2", "验证功能状态")

        try:
            import canvas_utils
            global_controls = canvas_utils.global_controls

            verification_results = {}

            features_to_check = [
                "ultrathink",
                "ebbinghaus_review",
                "concurrent_agents",
                "knowledge_graph",
                "smart_clipboard",
                "error_monitoring"
            ]

            for feature in features_to_check:
                try:
                    if hasattr(global_controls, 'is_enabled'):
                        status = global_controls.is_enabled(feature)
                        verification_results[feature] = status

                        if status:
                            success_message(f"{feature} - 验证通过")
                        else:
                            warning_message(f"{feature} - 未启用")
                    else:
                        verification_results[feature] = "unknown"
                        warning_message(f"{feature} - 无法验证状态")

                except Exception as e:
                    verification_results[feature] = f"error: {str(e)}"
                    warning_message(f"{feature} - 验证失败: {str(e)}")

            return verification_results

        except Exception as e:
            error_message(f"验证功能状态时发生错误: {e}")
            return {}

    def test_core_functionality(self) -> Dict[str, Any]:
        """测试核心功能"""
        print_step("3", "测试核心功能")

        test_results = {}

        try:
            import canvas_utils

            # 测试1: 检查v2.0核心类
            v2_classes = [
                "UltraThinkCanvasIntegration",
                "CanvasKnowledgeGraph",
                "ConcurrentAgentProcessor",
                "LearningAnalyticsDashboard",
                "PerformanceOptimizer"
            ]

            for class_name in v2_classes:
                if hasattr(canvas_utils, class_name):
                    test_results[f"class_{class_name}"] = True
                    success_message(f"{class_name} - 可用")
                else:
                    test_results[f"class_{class_name}"] = False
                    warning_message(f"{class_name} - 不可用")

            # 测试2: 检查全局实例
            global_instances = [
                "global_controls",
                "ultrathink_canvas_integration",
                "canvas_knowledge_graph",
                "concurrent_agent_processor"
            ]

            for instance_name in global_instances:
                if hasattr(canvas_utils, instance_name):
                    test_results[f"instance_{instance_name}"] = True
                    success_message(f"{instance_name} - 可用")
                else:
                    test_results[f"instance_{instance_name}"] = False
                    warning_message(f"{instance_name} - 不可用")

        except Exception as e:
            error_message(f"测试核心功能时发生错误: {e}")
            test_results["error"] = str(e)

        return test_results

    def generate_usage_examples(self) -> List[str]:
        """生成使用示例"""
        print_step("4", "生成使用示例")

        examples = [
            "# 立即开始使用v2.0功能",
            "",
            "## 基础使用",
            "# 分析Canvas理解水平",
            "/ultrathink analyze @你的Canvas.canvas",
            "",
            "# 并发执行多个Agent",
            "/concurrent basic-decomposition,clarification-path @你的Canvas.canvas",
            "",
            "# 查看学习分析",
            "/v2 analytics",
            "",
            "## 知识管理",
            "# 构建知识图谱",
            "/knowledge-graph build @你的Canvas.canvas",
            "",
            "# 搜索知识图谱",
            "/knowledge-graph search '关键概念'",
            "",
            "## 复习系统",
            "# 检查复习内容",
            "/ebbinghaus due",
            "",
            "# 生成检验白板",
            "@你的Canvas.canvas 生成检验白板",
            "",
            "## 系统管理",
            "# 查看功能状态",
            "/v2 status",
            "",
            "# 查看系统健康",
            "/v2 health"
        ]

        # 保存使用示例
        examples_file = Path.cwd() / "v2_usage_examples.txt"
        with open(examples_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(examples))

        success_message(f"使用示例已保存至: {examples_file}")
        return examples

    def generate_summary_report(self) -> str:
        """生成总结报告"""
        print_step("5", "生成总结报告")

        end_time = datetime.now()
        duration = end_time - self.start_time

        # 统计结果
        total_features = len(self.enabled_features) + len(self.failed_features)
        success_rate = (len(self.enabled_features) / total_features * 100) if total_features > 0 else 0

        # 生成报告
        report = {
            "timestamp": end_time.isoformat(),
            "duration_seconds": duration.total_seconds(),
            "enabled_features": self.enabled_features,
            "failed_features": self.failed_features,
            "warnings": self.warnings,
            "success_rate": success_rate,
            "total_features": total_features
        }

        # 保存报告
        report_file = Path.cwd() / f"v2_enablement_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # 显示总结
        print(f"\n{Colors.BOLD}[Summary] 启用总结:{Colors.END}")
        print(f"  启用成功: {len(self.enabled_features)} 个功能")
        print(f"  启用失败: {len(self.failed_features)} 个功能")
        print(f"  成功率: {success_rate:.1f}%")
        print(f"  耗时: {duration.total_seconds():.2f} 秒")
        print(f"  报告文件: {report_file}")

        if success_rate >= 80:
            print(f"\n{Colors.GREEN}[SUCCESS] v2.0功能启用成功！{Colors.END}")
        else:
            print(f"\n{Colors.YELLOW}[PARTIAL] 部分功能启用失败，请检查错误信息。{Colors.END}")

        return str(report_file)

    def show_next_steps(self):
        """显示下一步建议"""
        print_step("6", "下一步建议")

        next_steps = [
            "1. 📖 阅读完整使用指南: CANVAS_V2_完整使用指南.md",
            "2. 🧪 测试基础功能: /ultrathink analyze @你的Canvas.canvas",
            "3. 📊 查看学习分析: /v2 analytics",
            "4. 🎯 尝试并发处理: /concurrent basic-decomposition,oral-explanation @你的Canvas.canvas",
            "5. 🧠 构建知识图谱: /knowledge-graph build @你的Canvas.canvas",
            "6. 📝 查看使用示例: v2_usage_examples.txt",
            "7. 🔧 系统状态检查: python system_status_check.py"
        ]

        print(f"\n{Colors.BOLD}推荐操作流程:{Colors.END}")
        for step in next_steps:
            print(f"  {Colors.WHITE}{step}{Colors.END}")

        print(f"\n{Colors.BOLD}{Colors.GREEN}[READY] Canvas学习系统v2.0已就绪！享受AI增强的学习体验！{Colors.END}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Canvas学习系统v2.0 - 一键启用功能脚本')
    parser.add_argument('--check', action='store_true', help='仅检查功能状态，不启用新功能')
    parser.add_argument('--verbose', action='store_true', help='显示详细信息')

    args = parser.parse_args()

    print_header("Canvas学习系统v2.0 - 一键启用功能")

    enabler = V2FeatureEnabler()

    # 检查canvas_utils导入
    if not enabler.check_canvas_import():
        error_message("请确保在正确的目录下运行此脚本，且canvas_utils.py存在")
        return 1

    if args.check:
        # 仅检查状态
        verification_results = enabler.verify_feature_status()
        test_results = enabler.test_core_functionality()
        info_message("功能状态检查完成")
        return 0

    # 启用所有功能
    enable_results = enabler.enable_all_features()
    verification_results = enabler.verify_feature_status()
    test_results = enabler.test_core_functionality()
    enabler.generate_usage_examples()
    report_file = enabler.generate_summary_report()
    enabler.show_next_steps()

    return 0

if __name__ == "__main__":
    sys.exit(main())