#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Canvas学习系统v2.0 - 一键启用功能脚本 (纠正版)

该脚本会启用所有v2.0纠正后的功能，确保符合原始Story和PRD设计。

使用方法:
    python enable_v2_features_corrected.py          # 启用所有功能
    python enable_v2_features_corrected.py --check  # 仅检查状态

Author: Canvas Learning System Team
Version: 2.0 Corrected
Created: 2025-10-20
"""

import asyncio
import datetime
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

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
    """v2.0功能启用器 (纠正版)"""

    def __init__(self):
        self.enabled_features = []
        self.failed_features = []
        self.warnings = []
        self.start_time = datetime.datetime.now()
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
        """启用所有v2.0功能（纠正版）"""
        try:
            import canvas_utils
            global_controls = canvas_utils.global_controls

            # 纠正后的功能列表
            features = [
                ("ultrathink", "*ultrathink", "检验白板智能调度"),
                ("ebbinghaus_review", "*review", "艾宾浩斯复习系统"),
                ("concurrent_agents", "*concurrent", "学习效率处理器"),
                ("knowledge_graph", "*graph", "Canvas学习记忆系统"),
                ("smart_clipboard", "*clipboard", "智能剪贴板")
            ]

            # 添加纠正说明
            self.correction_notes.append("设计已纠正：专注于原始Story和PRD要求")

            print_step("1", "启用纠正后的v2.0核心功能")

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
                        if activation_result.get("success"):
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
        print_step("2", "验证纠正后的功能状态")

        try:
            import canvas_utils
            global_controls = canvas_utils.global_controls

            print(f"\n{Colors.BOLD}纠正后的功能状态:{Colors.END}")

            # 检查每个功能的初始状态
            features = {
                "ultrathink": "检验白板智能调度",
                "ebbinghaus_review": "艾宾浩斯复习",
                "concurrent_agents": "学习效率处理",
                "knowledge_graph": "Canvas学习记忆系统",
                "smart_clipboard": "智能剪贴板",
                "error_monitoring": "错误监控"
            }

            for feature, description in features:
                try:
                    if hasattr(global_controls, 'is_enabled'):
                        status = global_controls.is_enabled(feature)
                        if status:
                            success_message(f"{feature} - ✅ 已启用 (纠正版)")
                        else:
                            info_result(f"{feature} - ⚠️ 可用，使用*关键词激活")
                    else:
                        warning_result(f"{feature} - ❌ 状态检查失败")

                except Exception as e:
                    warning_result(f"{feature} - 状态检查异常: {str(e)}")

            print(f"\n{Colors.BOLD}设计纠正说明:{Colors.END}")
            for note in self.correction_notes:
                info_result(f"- {note}")

            # 测试核心功能
            print_step("3", "测试纠正后的核心功能")

            test_results = {}

            # 测试Graphiti记忆系统
            if hasattr(canvas_utils, 'canvas_learning_memory') and canvas_utils.canvas_learning_memory:
                success_message("Canvas学习记忆系统 - ✅ 可用")
                test_results["canvas_learning_memory"] = True
            else:
                error_message("Canvas学习记忆系统 - ❌ 不可用")
                test_results["canvas_learning_memory"] = False

            # 测试检验白板智能调度
            if hasattr(canvas_utils, 'ultrathink_canvas_integration') and canvas_utils.ultrathink_canvas_integration:
                success_message("检验白板智能调度 - ✅ 可用")
                test_results["review_board_agent_selector"] = True
            else:
                error_message("检验白板智能调度 - ❌ 不可用")
                test_results["review_board_agent_selector"] = False

            # 测试学习效率处理器
            if hasattr(canvas_utils, 'concurrent_agent_processor') and canvas_utils.concurrent_agent_processor:
                success_message("学习效率处理器 - ✅ 可用")
                test_results["efficient_canvas_processor"] = True
            else:
                error_message("学习效率处理器 - ❌ 不可用")
                test_results["efficient_canvas_processor"] = False

            return {
                "feature_status": results,
                "test_results": test_results,
                "correction_notes": self.correction_notes
            }

        except Exception as e:
            error_message(f"验证功能状态时发生错误: {e}")
            return {}

    def generate_usage_examples(self) -> List[str]:
        """生成使用示例"""
        print_step("4", "生成纠正后的使用示例")

        examples = [
            "# Canvas学习记忆系统使用",
            "",
            "## 基础使用",
            "# 启用记忆系统",
            "*graph",
            "",
            "# 记录学习会话",
            "canvas_learning_memory.add_canvas_learning_episode('数学分析.canvas', user_understandings)",
            "",
            "# 获取学习历史",
            "canvas_learning_memory.get_canvas_learning_episodes('数学分析.canvas', last_n=5)",
            "",
            "# 追踪学习进度",
            "canvas_learning_memory.track_learning_progress('极限概念', 85.0, '数学分析.canvas')",
            "",
            "",
            "# 检验白板智能调度使用",
            "",
            "## 基础使用",
            "# 启用智能调度",
            "*ultrathink",
            "",
            "# 分析理解质量",
            "agent_selector = ReviewBoardAgentSelector()",
            "quality = agent_selector.analyze_understanding_quality('用户的理解文本')",
            "",
            "# 获取Agent推荐",
            "recommendations = agent_selector.recommend_agents(quality)",
            "",
            "# 学习效率处理器使用",
            "",
            "## 基础使用",
            "# 启用效率处理",
            "*concurrent",
            "",
            "# 处理多个节点",
            "processor = EfficientCanvasProcessor()",
            "result = await processor.process_multiple_nodes('数学分析.canvas', ['node1', 'node2'], 'oral-explanation')",
            "",
            "# 查看处理结果",
            "print(f'成功处理: {result[\"processed\"]} 个节点')",
            "print(f'处理时间: {result[\"total_time\"]} 秒')",
            "",
            "",
            "# 综合使用流程",
            "",
            "## 完整学习流程",
            "# 1. 启用所有功能",
            "*graph *ultrathink *concurrent",
            "",
            "# 2. 学习新概念",
            "@数学分析.canvas 对'极限'进行基础拆解",
            "",
            "# 3. 记录学习",
            "canvas_learning_memory.add_canvas_learning_episode('数学分析.canvas', {...})",
            "",
            "# 4. 效率处理",
            "await concurrent_agent_processor.process_multiple_nodes('数学分析.canvas', node_ids, 'oral-explanation')",
            "",
            "# 5. 检验学习",
            "@数学分析.canvas 生成检验白板",
            "# 在检验白板上使用智能调度推荐Agent"
        ]

        # 保存使用示例
        examples_file = Path.cwd() / "v2_usage_examples_corrected.txt"
        with open(examples_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(examples))

        success_message(f"纠正版使用示例已保存至: {examples_file}")
        return examples

    def generate_summary_report(self) -> str:
        """生成纠正总结报告"""
        print_step("5", "生成纠正总结报告")

        end_time = datetime.datetime.now()
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
            "total_features": total_features,
            "correction_notes": self.correction_notes,
            "type": "corrected_v2"  # 标识这是纠正版本
        }

        # 保存报告
        report_file = Path.cwd() / f"v2_enablement_report_corrected_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # 显示总结
        print(f"\n{Colors.BOLD}[Summary] 纠正总结:{Colors.END}")
        print(f"  启用成功: {len(self.enabled_features)} 个功能")
        print(f"  启用失败: {len(self.failed_features)} 个功能")
        print(f"  成功率: {success_rate:.1f}%")
        print(f"  耗时: {duration.total_seconds():.2f} 秒")
        print(f"  报告文件: {report_file}")

        print(f"\n{Colors.BOLD}🔧 重要纠正:{Colors.END}")
        for note in self.correction_notes:
            info_result(f"  ✅ {note}")

        if success_rate >= 80:
            print(f"\n{Colors.GREEN}[SUCCESS] v2.0纠正完成！系统现在符合原始设计！{Colors.END}")
        else:
            print(f"\n{Colors.YELLOW}[PARTIAL] 部分功能启用失败，请检查错误信息。{Colors.END}")

        return str(report_file)

    def show_next_steps(self):
        """显示下一步建议"""
        print_step("6", "下一步建议 (纠正版)")

        next_steps = [
            "1. 📖 阅读纠正版使用指南: CANVAS_V2_纠正版使用指南.md",
            "2. 🧪 验证纠正后功能: python system_status_check.py",
            "3. 🎯 体验原始设计流程: 按照Story要求使用系统",
            "4. ⚡ 确认Context7技术栈: Graphiti记忆系统",
            "5. 📊 对比使用体验: 与v1.x对比学习效果"
        ]

        print(f"\n{Colors.BOLD}推荐操作流程:{Colors.END}")
        for step in next_steps:
            print(f"  {Colors.WHITE}{step}{Colors.END}")

        print(f"\n{Colors.BOLD}{Colors.GREEN}[READY] Canvas学习系统v2.0已纠正！{Colors.END}")
        print(f"{Colors.WHITE}专注于核心价值: 检验白板、学习记忆、效率提升{Colors.END}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Canvas学习系统v2.0 - 一键启用功能脚本 (纠正版)')
    parser.add_argument('--check', action='store_true', help='仅检查功能状态，不启用新功能')
    parser.add_argument('--verbose', action='store_true', help='显示详细信息')

    args = parser.parse_args()

    print_header("Canvas学习系统v2.0 - 一键启用功能脚本 (纠正版)")

    enabler = V2FeatureEnabler()

    if args.check:
        # 仅检查状态
        verification_results = enabler.verify_feature_status()
        info_message("功能状态检查完成")
        return 0

    # 启用所有功能
    enable_results = enabler.enable_all_features()
    verification_results = enabler.verify_feature_status()
    enabler.generate_usage_examples()
    report_file = enabler.generate_summary_report()
    enabler.show_next_steps()

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())