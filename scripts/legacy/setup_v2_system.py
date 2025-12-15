#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Canvas学习系统v2.0 - 一键配置脚本

自动配置所有v2.0功能，验证系统状态，提供使用指导

Author: Canvas Learning System Team
Version: 2.0 Setup Script
Created: 2025-10-20
"""

import asyncio
import datetime
import json
import math
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from canvas_utils_working import (
        global_controls,
        canvas_learning_memory,
        review_board_agent_selector,
        efficient_canvas_processor,
        forgetting_curve_manager,
        ebbinghaus_review_scheduler,
        ultrathink_canvas_integration,
        canvas_knowledge_graph,
        concurrent_agent_processor,
        ebbinghaus_system
    )
    IMPORT_SUCCESS = True
except ImportError as e:
    print(f"[ERROR] 导入失败: {e}")
    IMPORT_SUCCESS = False

class V2SystemSetup:
    """v2.0系统配置管理器"""

    def __init__(self):
        """初始化配置管理器"""
        self.setup_results = []
        if IMPORT_SUCCESS:
            print("[OK] Canvas学习系统v2.0模块导入成功")
        else:
            print("[ERROR] 模块导入失败，请检查依赖")

    def log_result(self, test_name: str, success: bool, message: str = ""):
        """记录配置结果"""
        status = "PASS" if success else "FAIL"
        self.setup_results.append({
            "name": test_name,
            "status": status,
            "message": message
        })

        symbol = "[OK]" if success else "[FAIL]"
        print(f"{symbol} {test_name}")
        if message:
            print(f"   {message}")

    def test_system_imports(self) -> bool:
        """测试系统导入"""
        print("\n[步骤1] 测试系统模块导入...")

        try:
            # 测试核心模块
            modules_to_test = [
                ("Canvas学习记忆", canvas_learning_memory),
                ("检验白板调度", review_board_agent_selector),
                ("并行处理器", efficient_canvas_processor),
                ("艾宾浩斯系统", forgetting_curve_manager),
                ("全局控制器", global_controls)
            ]

            all_success = True
            for name, module in modules_to_test:
                if module is not None:
                    self.log_result(name, True, "模块导入成功")
                else:
                    self.log_result(name, False, "模块为None")
                    all_success = False

            return all_success

        except Exception as e:
            self.log_result("系统导入测试", False, f"异常: {e}")
            return False

    def test_global_controls(self) -> bool:
        """测试全局控制功能"""
        print("\n[步骤2] 测试全局控制功能...")

        try:
            # 测试功能激活
            test_commands = [
                ("学习记忆系统", "*graph"),
                ("艾宾浩斯复习", "*review"),
                ("智能调度", "*ultrathink"),
                ("并行处理", "*concurrent"),
                ("智能剪贴板", "*clipboard")
            ]

            all_success = True
            for name, command in test_commands:
                result = global_controls.activate_feature(command)
                if result.get("success", False):
                    self.log_result(f"激活{name}", True, f"使用命令: {command}")
                else:
                    self.log_result(f"激活{name}", False, result.get("message", "未知错误"))
                    all_success = False

            return all_success

        except Exception as e:
            self.log_result("全局控制测试", False, f"异常: {e}")
            return False

    def test_ebbinghaus_system(self) -> bool:
        """测试艾宾浩斯复习系统"""
        print("\n[步骤3] 测试艾宾浩斯复习系统...")

        try:
            # 创建测试节点
            test_node = forgetting_curve_manager.create_review_node(
                node_id="setup_test_node",
                concept="配置测试概念",
                complexity_score=5.0,
                canvas_file="setup_test.canvas"
            )

            # 测试记忆强度计算
            strength = forgetting_curve_manager.calculate_memory_strength(5.0)
            if 0.5 <= strength <= 1.5:
                self.log_result("记忆强度计算", True, f"强度值: {strength:.2f}")
            else:
                self.log_result("记忆强度计算", False, f"强度值异常: {strength}")
                return False

            # 测试遗忘曲线公式
            retention = forgetting_curve_manager.calculate_retention_rate(1.0, 1.0)
            expected_retention = math.exp(-1.0)  # e^(-1)
            if abs(retention - expected_retention) < 0.01:
                self.log_result("遗忘曲线公式", True, f"R(1) = {retention:.3f}")
            else:
                self.log_result("遗忘曲线公式", False, f"计算错误: {retention}")
                return False

            # 测试复习时间计算
            optimal_times = forgetting_curve_manager.calculate_optimal_review_times(
                datetime.datetime.now(), 5.0
            )
            if len(optimal_times) == 5:
                self.log_result("复习时间计算", True, f"生成{len(optimal_times)}个时间点")
            else:
                self.log_result("复习时间计算", False, f"时间点数量错误: {len(optimal_times)}")
                return False

            return True

        except Exception as e:
            self.log_result("艾宾浩斯系统测试", False, f"异常: {e}")
            return False

    def test_error_system(self) -> bool:
        """测试错误日志系统"""
        print("\n[步骤4] 测试错误日志系统...")

        try:
            from canvas_error_system import CanvasErrorSystem, ErrorCategory, ErrorSeverity

            # 创建错误系统实例
            error_system = CanvasErrorSystem()

            # 测试错误记录
            error_id = asyncio.run(error_system.log_error(
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.INFO,
                error_type="配置测试错误",
                error_message="这是一条测试错误消息",
                context={"setup_phase": "system_test"}
            ))

            if error_id:
                self.log_result("错误记录功能", True, f"错误ID: {error_id}")
            else:
                self.log_result("错误记录功能", False, "未返回错误ID")
                return False

            # 测试错误查询
            errors = asyncio.run(error_system.query_errors("配置"))
            if errors:
                self.log_result("错误查询功能", True, f"找到{len(errors)}条相关错误")
            else:
                self.log_result("错误查询功能", False, "未找到相关错误")
                return False

            return True

        except Exception as e:
            self.log_result("错误系统测试", False, f"异常: {e}")
            return False

    async def test_review_scheduler(self) -> bool:
        """测试复习调度器"""
        print("\n[步骤5] 测试复习调度器...")

        try:
            # 创建测试数据
            test_node = forgetting_curve_manager.create_review_node(
                node_id="scheduler_test",
                concept="调度测试概念",
                complexity_score=6.0,
                canvas_file="scheduler_test.canvas"
            )

            # 测试复习会话
            session_result = await ebbinghaus_review_scheduler.execute_review_session(
                "scheduler_test.canvas"
            )

            if session_result.get("success", False):
                self.log_result("复习会话执行", True, session_result.get("message", ""))
            else:
                self.log_result("复习会话执行", False, session_result.get("message", "未知错误"))
                return False

            # 模拟需要复习的场景
            test_node.last_review_time = datetime.datetime.now() - datetime.timedelta(days=20)

            due_nodes = forgetting_curve_manager.get_due_nodes("scheduler_test.canvas")
            if due_nodes:
                self.log_result("到期节点检测", True, f"找到{len(due_nodes)}个到期节点")

                # 测试Agent调度
                schedule = await ebbinghaus_review_scheduler.schedule_review_agents(due_nodes)
                if schedule:
                    self.log_result("Agent智能调度", True, f"生成{len(schedule)}个调度项")
                else:
                    self.log_result("Agent智能调度", False, "未生成调度项")
                    return False
            else:
                self.log_result("到期节点检测", False, "未找到到期节点")
                return False

            return True

        except Exception as e:
            self.log_result("复习调度器测试", False, f"异常: {e}")
            return False

    def generate_setup_report(self) -> dict:
        """生成配置报告"""
        total_tests = len(self.setup_results)
        passed_tests = len([r for r in self.setup_results if r["status"] == "PASS"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

        report = {
            "setup_time": datetime.datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "system_status": "READY" if failed_tests == 0 else "NEEDS_ATTENTION",
            "test_results": self.setup_results
        }

        return report

    def save_setup_report(self, report: dict):
        """保存配置报告"""
        try:
            report_file = "v2_setup_report.json"
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            print(f"\n[REPORT] 配置报告已保存到: {report_file}")
        except Exception as e:
            print(f"\n[ERROR] 保存配置报告失败: {e}")

    def print_usage_guide(self):
        """打印使用指南"""
        print("\n" + "="*70)
        print("[SUCCESS] Canvas学习系统v2.0 配置完成！")
        print("="*70)

        print("\n[RECOMMENDED WORKFLOW] 推荐的学习流程:")
        print("1. 启用学习记忆系统: *graph")
        print("2. 启用艾宾浩斯复习: *review")
        print("3. 开始原白板学习: @你的Canvas.canvas 对'概念'进行基础拆解")
        print("4. 生成检验白板: @你的Canvas.canvas 生成检验白板")
        print("5. 启用智能调度: *ultrathink")
        print("6. 填写检验理解并复习")

        print("\n[ADVANCED FEATURES] 高级功能:")
        print("- 多Agent并行: *concurrent")
        print("- 布局学习: python canvas_layout_learner.py --help")
        print("- 错误预防: python canvas_error_system.py --report")
        print("- 艾宾浩斯演示: python ebbinghaus_demo.py")

        print("\n[DOCUMENTATION] 详细文档:")
        print("- 完整用户指南: V2_COMPLETE_USER_GUIDE.md")
        print("- 实现状态报告: PRD_STORY_IMPLEMENTATION_STATUS.md")
        print("- 系统状态指南: CURRENT_SYSTEM_STATUS_GUIDE.md")

    async def run_complete_setup(self) -> dict:
        """运行完整配置流程"""
        print("="*70)
        print("Canvas学习系统v2.0 - 一键配置脚本")
        print("="*70)

        if not IMPORT_SUCCESS:
            print("\n[ERROR] 系统模块导入失败，无法继续配置")
            return {"success": False, "message": "Import failed"}

        # 运行所有测试
        tests = [
            ("系统导入测试", self.test_system_imports),
            ("全局控制测试", self.test_global_controls),
            ("艾宾浩斯系统测试", self.test_ebbinghaus_system),
            ("错误系统测试", self.test_error_system),
            ("复习调度器测试", self.test_review_scheduler)
        ]

        all_success = True
        for test_name, test_func in tests:
            try:
                if asyncio.iscoroutinefunction(test_func):
                    result = await test_func()
                else:
                    result = test_func()
                if not result:
                    all_success = False
            except Exception as e:
                self.log_result(test_name, False, f"测试异常: {e}")
                all_success = False

        # 生成和保存报告
        report = self.generate_setup_report()
        report["overall_success"] = all_success
        self.save_setup_report(report)

        # 打印使用指南
        if all_success:
            self.print_usage_guide()
        else:
            print("\n[WARNING] 配置过程中发现问题，请查看报告了解详情")

        return report

async def main():
    """主配置函数"""
    setup_manager = V2SystemSetup()
    results = await setup_manager.run_complete_setup()

    if results.get("overall_success", False):
        print(f"\n[SUCCESS] 配置成功！系统状态: {results.get('system_status', 'UNKNOWN')}")
        print(f"成功率: {results.get('success_rate', 0):.1f}%")
    else:
        print(f"\n[PARTIAL SUCCESS] 配置部分成功，成功率: {results.get('success_rate', 0):.1f}%")
        print("建议查看配置报告了解具体问题")

    return results

if __name__ == "__main__":
    print("启动Canvas学习系统v2.0配置...")
    try:
        results = asyncio.run(main())

        # 显示简要结果
        print(f"\n[SUMMARY] 配置结果:")
        print(f"- 总测试数: {results.get('total_tests', 0)}")
        print(f"- 通过测试: {results.get('passed_tests', 0)}")
        print(f"- 失败测试: {results.get('failed_tests', 0)}")
        print(f"- 成功率: {results.get('success_rate', 0):.1f}%")
        print(f"- 系统状态: {results.get('system_status', 'UNKNOWN')}")

    except Exception as e:
        print(f"\n[ERROR] 配置过程失败: {e}")
        import traceback
        traceback.print_exc()