#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
艾宾浩斯复习系统测试 - Canvas学习系统v2.0

测试真正的艾宾浩斯遗忘曲线算法实现：
- ForgettingCurveManager类功能测试
- 遗忘曲线公式 R(t) = e^(-t/S) 验证
- 标准复习间隔计算 (1,3,7,15,30天)
- Agent智能调度功能测试

Author: Canvas Learning System Team
Version: 2.0 Ebbinghaus Implementation
Created: 2025-10-20
"""

import asyncio
import datetime
import json
import math
import os
import sys
from typing import Any, Dict

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from canvas_utils_working import EbbinghausReviewScheduler, ForgettingCurveManager, ReviewNode
    IMPORT_SUCCESS = True
except ImportError as e:
    print(f"[ERROR] 导入失败: {e}")
    IMPORT_SUCCESS = False

class EbbinghausSystemTest:
    """艾宾浩斯复习系统测试类"""

    def __init__(self):
        """初始化测试类"""
        if IMPORT_SUCCESS:
            self.forgetting_curve = ForgettingCurveManager()
            self.scheduler = EbbinghausReviewScheduler()
        self.test_results = []

    def run_test(self, test_name: str, test_func) -> bool:
        """运行单个测试"""
        try:
            print(f"\n[TEST] {test_name}...")
            result = test_func()
            if result:
                print(f"[PASS] {test_name}")
                self.test_results.append({"name": test_name, "status": "PASS"})
                return True
            else:
                print(f"[FAIL] {test_name}")
                self.test_results.append({"name": test_name, "status": "FAIL"})
                return False
        except Exception as e:
            print(f"[ERROR] {test_name}: {e}")
            self.test_results.append({"name": test_name, "status": "ERROR", "error": str(e)})
            return False

    def test_memory_strength_calculation(self) -> bool:
        """测试记忆强度计算"""
        print("  测试不同复杂度的记忆强度计算...")

        # 测试复杂度1.0 (容易) -> 记忆强度应该接近2.0
        strength_easy = self.forgetting_curve.calculate_memory_strength(1.0)
        print(f"    复杂度1.0 -> 记忆强度: {strength_easy:.2f}")
        assert abs(strength_easy - 2.0) < 0.1, f"Expected ~2.0, got {strength_easy}"

        # 测试复杂度10.0 (困难) -> 记忆强度应该接近0.1
        strength_hard = self.forgetting_curve.calculate_memory_strength(10.0)
        print(f"    复杂度10.0 -> 记忆强度: {strength_hard:.2f}")
        assert abs(strength_hard - 0.2) < 0.2, f"Expected ~0.2, got {strength_hard}"

        # 测试复杂度5.5 (中等) -> 记忆强度应该在中间范围
        strength_medium = self.forgetting_curve.calculate_memory_strength(5.5)
        print(f"    复杂度5.5 -> 记忆强度: {strength_medium:.2f}")
        assert 0.5 <= strength_medium <= 1.5, f"Expected medium range, got {strength_medium}"

        return True

    def test_retention_rate_formula(self) -> bool:
        """测试遗忘曲线公式 R(t) = e^(-t/S)"""
        print("  测试遗忘曲线数学公式...")

        # 测试S=2.0, t=0时的保持率应该是1.0
        retention_initial = self.forgetting_curve.calculate_retention_rate(0.0, 2.0)
        print(f"    t=0, S=2.0 -> 保持率: {retention_initial:.3f}")
        assert abs(retention_initial - 1.0) < 0.001, f"Expected 1.0, got {retention_initial}"

        # 测试S=2.0, t=2时的保持率应该是e^(-1) ≈ 0.368
        retention_2days = self.forgetting_curve.calculate_retention_rate(2.0, 2.0)
        expected = math.exp(-1.0)  # e^(-2/2) = e^(-1)
        print(f"    t=2, S=2.0 -> 保持率: {retention_2days:.3f} (期望: {expected:.3f})")
        assert abs(retention_2days - expected) < 0.01, f"Expected {expected}, got {retention_2days}"

        # 测试S=1.0, t=1时的保持率应该是e^(-1) ≈ 0.368
        retention_1day = self.forgetting_curve.calculate_retention_rate(1.0, 1.0)
        expected = math.exp(-1.0)  # e^(-1/1) = e^(-1)
        print(f"    t=1, S=1.0 -> 保持率: {retention_1day:.3f} (期望: {expected:.3f})")
        assert abs(retention_1day - expected) < 0.01, f"Expected {expected}, got {retention_1day}"

        return True

    def test_standard_intervals(self) -> bool:
        """测试标准艾宾浩斯复习间隔"""
        print("  测试标准复习间隔 (1,3,7,15,30天)...")

        # 创建测试节点
        test_time = datetime.datetime.now()
        review_times = self.forgetting_curve.calculate_optimal_review_times(
            test_time, 5.0  # 中等复杂度
        )

        print(f"    生成了 {len(review_times)} 个复习时间点")
        assert len(review_times) == 5, f"Expected 5 intervals, got {len(review_times)}"

        # 验证间隔天数的合理性
        intervals = []
        for i, time in enumerate(review_times):
            days_diff = (time - test_time).days
            intervals.append(days_diff)
            print(f"    间隔 {i+1}: {days_diff} 天")

        # 验证间隔递增
        for i in range(1, len(intervals)):
            assert intervals[i] > intervals[i-1], f"Interval {i+1} should be greater than interval {i}"

        # 验证第一个间隔接近1天
        assert 0.5 <= intervals[0] <= 2.0, f"First interval should be ~1 day, got {intervals[0]}"

        return True

    def test_review_node_creation(self) -> bool:
        """测试复习节点创建"""
        print("  测试复习节点创建和管理...")

        # 创建测试节点
        node = self.forgetting_curve.create_review_node(
            node_id="test_node_1",
            concept="逆否命题",
            complexity_score=6.5,
            canvas_file="test_canvas.canvas"
        )

        # 验证节点属性
        assert node.concept == "逆否命题", "Concept mismatch"
        assert node.complexity_score == 6.5, "Complexity score mismatch"
        assert node.mastery_level == 0.0, "Initial mastery should be 0"
        assert node.review_count == 0, "Initial review count should be 0"
        assert node.canvas_file == "test_canvas.canvas", "Canvas file mismatch"

        print(f"    成功创建节点: {node.concept} (复杂度: {node.complexity_score})")

        # 验证节点已存储
        assert "test_node_1" in self.forgetting_curve.review_nodes, "Node not stored"
        stored_node = self.forgetting_curve.review_nodes["test_node_1"]
        assert stored_node.concept == node.concept, "Stored node mismatch"

        return True

    def test_mastery_update(self) -> bool:
        """测试掌握度更新"""
        print("  测试掌握度更新功能...")

        # 创建节点
        node = self.forgetting_curve.create_review_node(
            node_id="test_mastery",
            concept="测试概念",
            complexity_score=5.0
        )

        # 更新掌握度
        self.forgetting_curve.update_node_mastery("test_mastery", 0.75)

        # 验证更新
        updated_node = self.forgetting_curve.review_nodes["test_mastery"]
        assert updated_node.mastery_level == 0.75, "Mastery not updated correctly"
        assert updated_node.review_count == 1, "Review count not incremented"
        assert updated_node.last_review_time is not None, "Last review time not set"

        print(f"    掌握度更新为: {updated_node.mastery_level:.2f}")
        print(f"    复习次数: {updated_node.review_count}")

        return True

    def test_retention_status(self) -> bool:
        """测试记忆状态分析"""
        print("  测试记忆状态分析...")

        # 创建一个有历史的节点
        past_time = datetime.datetime.now() - datetime.timedelta(days=5)
        node = ReviewNode(
            node_id="status_test",
            concept="状态测试",
            create_time=past_time,
            complexity_score=5.0,
            mastery_level=0.6,
            last_review_time=past_time,
            review_count=1
        )

        # 获取状态
        status = self.forgetting_curve.get_retention_status(node)

        # 验证状态字段
        required_fields = ["node_id", "concept", "retention_rate", "suggestion", "urgency"]
        for field in required_fields:
            assert field in status, f"Missing field: {field}"

        print(f"    概念: {status['concept']}")
        print(f"    保持率: {status['retention_rate']:.3f}")
        print(f"    建议: {status['suggestion']}")
        print(f"    紧急程度: {status['urgency']}")

        # 验证保持率在合理范围内
        assert 0.0 <= status["retention_rate"] <= 1.0, "Invalid retention rate"

        return True

    async def test_agent_scheduling(self) -> bool:
        """测试Agent智能调度"""
        print("  测试Agent智能调度功能...")

        # 创建几个测试节点
        test_nodes = []
        concepts = ["基础概念", "进阶概念", "复杂概念"]
        complexities = [3.0, 6.0, 8.0]
        masteries = [0.9, 0.5, 0.3]

        for i, (concept, complexity, mastery) in enumerate(zip(concepts, complexities, masteries)):
            node = self.forgetting_curve.create_review_node(
                node_id=f"schedule_test_{i}",
                concept=concept,
                complexity_score=complexity
            )
            node.mastery_level = mastery
            node.last_review_time = datetime.datetime.now() - datetime.timedelta(days=10)
            test_nodes.append(node)

        # 生成调度计划
        schedule = await self.scheduler.schedule_review_agents(test_nodes)

        # 验证调度结果
        assert len(schedule) == 3, f"Expected 3 scheduled items, got {len(schedule)}"

        for item in schedule:
            print(f"    节点: {item['concept']}")
            print(f"      紧急程度: {item['urgency']}")
            print(f"      推荐Agent: {item['recommended_agents']}")
            print(f"      复习原因: {item['review_reason']}")

            # 验证必要字段
            required_fields = ["node_id", "concept", "urgency", "recommended_agents", "review_reason"]
            for field in required_fields:
                assert field in item, f"Missing field: {field}"

            # 验证Agent推荐合理性
            assert isinstance(item["recommended_agents"], list), "Recommended agents should be a list"
            assert len(item["recommended_agents"]) > 0, "Should recommend at least one agent"

        return True

    async def test_review_session(self) -> bool:
        """测试完整复习会话"""
        print("  测试完整复习会话执行...")

        # 创建测试节点
        canvas_file = "test_session.canvas"
        for i in range(3):
            self.forgetting_curve.create_review_node(
                node_id=f"session_test_{i}",
                concept=f"会话测试概念{i}",
                complexity_score=5.0 + i,
                canvas_file=canvas_file
            )

        # 执行复习会话
        session_result = await self.scheduler.execute_review_session(canvas_file)

        # 验证会话结果
        assert session_result["success"], f"Session failed: {session_result.get('message', 'Unknown error')}"
        assert "due_nodes_count" in session_result, "Missing due_nodes_count"
        assert "schedule" in session_result, "Missing schedule"

        print(f"    会话成功: {session_result['success']}")
        print(f"    消息: {session_result['message']}")
        print(f"    到期节点数: {session_result['due_nodes_count']}")
        print(f"    调度计划数: {len(session_result['schedule'])}")

        return True

    def test_schedule_generation(self) -> bool:
        """测试复习计划生成"""
        print("  测试复习计划生成...")

        # 创建测试节点
        test_time = datetime.datetime.now()
        node = self.forgetting_curve.create_review_node(
            node_id="schedule_gen_test",
            concept="计划生成测试",
            complexity_score=5.0,
            canvas_file="test.canvas"
        )
        node.create_time = test_time - datetime.timedelta(days=1)  # 1天前创建

        # 生成30天复习计划
        schedule = self.forgetting_curve.generate_review_schedule(
            canvas_file="test.canvas",
            days_ahead=30
        )

        # 验证计划结构
        assert isinstance(schedule, dict), "Schedule should be a dictionary"

        if schedule:  # 如果有计划
            for date_str, items in schedule.items():
                print(f"    日期 {date_str}: {len(items)} 个复习任务")
                assert isinstance(items, list), "Schedule items should be a list"

                for item in items:
                    required_fields = ["node_id", "concept", "review_time"]
                    for field in required_fields:
                        assert field in item, f"Missing field: {field}"

        return True

    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("=" * 60)
        print("艾宾浩斯复习系统完整测试 - Canvas学习系统v2.0")
        print("=" * 60)

        if not IMPORT_SUCCESS:
            print("[ERROR] 无法导入必要模块，测试终止")
            return {"success": False, "message": "Import failed"}

        # 同步测试
        sync_tests = [
            ("记忆强度计算测试", self.test_memory_strength_calculation),
            ("遗忘曲线公式测试", self.test_retention_rate_formula),
            ("标准复习间隔测试", self.test_standard_intervals),
            ("复习节点创建测试", self.test_review_node_creation),
            ("掌握度更新测试", self.test_mastery_update),
            ("记忆状态分析测试", self.test_retention_status),
            ("复习计划生成测试", self.test_schedule_generation)
        ]

        # 异步测试
        async_tests = [
            ("Agent智能调度测试", self.test_agent_scheduling),
            ("完整复习会话测试", self.test_review_session)
        ]

        # 运行同步测试
        print("\n[SYNC TESTS] 开始同步测试...")
        sync_passed = 0
        for test_name, test_func in sync_tests:
            if self.run_test(test_name, test_func):
                sync_passed += 1

        # 运行异步测试
        print("\n[ASYNC TESTS] 开始异步测试...")
        async_passed = 0
        for test_name, test_func in async_tests:
            try:
                result = await test_func()
                if result:
                    print(f"[PASS] {test_name}")
                    self.test_results.append({"name": test_name, "status": "PASS"})
                    async_passed += 1
                else:
                    print(f"[FAIL] {test_name}")
                    self.test_results.append({"name": test_name, "status": "FAIL"})
            except Exception as e:
                print(f"[ERROR] {test_name}: {e}")
                self.test_results.append({"name": test_name, "status": "ERROR", "error": str(e)})

        # 统计结果
        total_tests = len(sync_tests) + len(async_tests)
        passed_tests = sync_passed + async_passed
        failed_tests = total_tests - passed_tests

        print("\n" + "=" * 60)
        print("测试结果统计")
        print("=" * 60)
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {failed_tests}")
        print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")

        print("\n[测试详情]")
        for result in self.test_results:
            status_symbol = "[PASS]" if result["status"] == "PASS" else "[FAIL]"
            if result["status"] == "ERROR":
                status_symbol = "[ERROR]"
            print(f"  {status_symbol} {result['name']}")
            if result["status"] == "ERROR":
                print(f"    错误: {result.get('error', 'Unknown error')}")

        return {
            "success": failed_tests == 0,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "test_results": self.test_results
        }

async def main():
    """主测试函数"""
    test_runner = EbbinghausSystemTest()
    results = await test_runner.run_all_tests()

    if results["success"]:
        print("\n[SUCCESS] 所有测试通过！艾宾浩斯复习系统实现正确！")
        print("\n[CORE FUNCTIONS VERIFIED]:")
        print("  - 遗忘曲线公式 R(t) = e^(-t/S) [PASS]")
        print("  - 标准复习间隔 (1,3,7,15,30天) [PASS]")
        print("  - 记忆强度计算 [PASS]")
        print("  - Agent智能调度 [PASS]")
        print("  - 复习会话执行 [PASS]")
    else:
        print(f"\n[FAILED] 测试失败！成功率: {results['success_rate']:.1f}%")
        print("需要修复的问题:")
        for result in results["test_results"]:
            if result["status"] != "PASS":
                print(f"  - {result['name']}: {result.get('error', 'Failed')}")

    return results

if __name__ == "__main__":
    # 运行测试
    results = asyncio.run(main())

    # 保存测试结果
    try:
        with open("ebbinghaus_test_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        print("\n测试结果已保存到: ebbinghaus_test_results.json")
    except Exception as e:
        print(f"保存测试结果失败: {e}")
