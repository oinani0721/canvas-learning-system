#!/usr/bin/env python3
"""
学习会话管理系统测试套件

测试新的 /learning 命令系统的所有功能，确保：
1. 所有命令正常执行
2. 与现有记忆系统正确集成
3. 跨Canvas会话管理正常
4. 错误处理机制完善

Author: Canvas Learning System Team
Version: 1.0
Date: 2025-10-25
"""

import asyncio
import json
import os
import sys
import time
import unittest
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from learning_session_wrapper import LearningSession, LearningSessionWrapper

    print("✅ 学习会话包装器导入成功")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)


class TestLearningSessionSystem(unittest.TestCase):
    """学习会话系统测试类"""

    def setUp(self):
        """测试前准备"""
        self.wrapper = LearningSessionWrapper()
        self.test_canvas_path = "tests/test_canvas.canvas"

        # 创建测试Canvas文件
        self._create_test_canvas()

    def tearDown(self):
        """测试后清理"""
        # 停止所有活跃会话
        asyncio.run(self._cleanup_sessions())

        # 清理测试文件
        self._cleanup_test_files()

    def _create_test_canvas(self):
        """创建测试Canvas文件"""
        test_canvas = {
            "nodes": [
                {
                    "id": "test-question-1",
                    "type": "text",
                    "x": 100,
                    "y": 100,
                    "width": 200,
                    "height": 100,
                    "color": "1",
                    "content": "什么是测试概念？",
                },
                {
                    "id": "test-yellow-1",
                    "type": "text",
                    "x": 350,
                    "y": 100,
                    "width": 200,
                    "height": 100,
                    "color": "6",
                    "content": "我的测试理解",
                },
            ],
            "edges": [
                {
                    "id": "test-edge-1",
                    "fromNode": "test-question-1",
                    "toNode": "test-yellow-1",
                    "label": "学习路径",
                }
            ],
        }

        # 确保测试目录存在
        test_dir = Path("tests")
        test_dir.mkdir(exist_ok=True)

        # 写入测试Canvas文件
        with open(self.test_canvas_path, "w", encoding="utf-8") as f:
            json.dump(test_canvas, f, ensure_ascii=False, indent=2)

    def _cleanup_test_files(self):
        """清理测试文件"""
        test_file = Path(self.test_canvas_path)
        if test_file.exists():
            test_file.unlink()

    async def _cleanup_sessions(self):
        """清理所有会话"""
        if self.wrapper.current_session:
            session_id = self.wrapper.current_session.session_id
            if session_id in self.wrapper.coordinator.active_sessions:
                await self.wrapper.stop_session(session_id)

    def test_01_start_session_basic(self):
        """测试基础会话启动"""
        print("🧪 测试1: 基础会话启动")

        async def run_test():
            result = await self.wrapper.start_session(
                canvas_path=self.test_canvas_path, session_name="测试学习会话"
            )

            self.assertTrue(result["success"])
            self.assertIsNotNone(result["session_id"])
            self.assertEqual(result["session_name"], "测试学习会话")
            self.assertEqual(result["canvas_path"], self.test_canvas_path)

            # 检查会话是否被正确创建
            session = self.wrapper.current_session
            self.assertIsNotNone(session)
            self.assertEqual(session.session_id, result["session_id"])

            print(f"✅ 会话启动成功: {result['session_id']}")

        asyncio.run(run_test())

    def test_02_start_session_with_options(self):
        """测试带选项的会话启动"""
        print("🧪 测试2: 带选项的会话启动")

        async def run_test():
            result = await self.wrapper.start_session(
                canvas_path=self.test_canvas_path,
                user_id="test_user",
                duration_minutes=120,
                enable_graphiti=True,
                enable_memory=False,
                enable_semantic=True,
            )

            self.assertTrue(result["success"])
            self.assertEqual(result["user_id"], "test_user")
            self.assertTrue(result["memory_systems"]["graphiti"])
            self.assertFalse(result["memory_systems"]["memory"])
            self.assertTrue(result["memory_systems"]["semantic"])

            print(
                f"✅ 带选项启动成功: Graphiti={result['memory_systems']['graphiti']}, Memory={result['memory_systems']['memory']}, Semantic={result['memory_systems']['semantic']}"
            )

        asyncio.run(run_test())

    def test_03_session_status(self):
        """测试会话状态查询"""
        print("🧪 测试3: 会话状态查询")

        async def run_test():
            # 先启动一个会话
            start_result = await self.wrapper.start_session(
                canvas_path=self.test_canvas_path, session_name="状态测试会话"
            )
            self.assertTrue(start_result["success"])

            # 查询状态
            status_result = await self.wrapper.get_session_status()
            self.assertTrue(status_result["success"])
            self.assertEqual(status_result["session_id"], start_result["session_id"])
            self.assertEqual(status_result["session_name"], "状态测试会话")
            self.assertEqual(status_result["canvas_path"], self.test_canvas_path)

            print(
                f"✅ 状态查询成功: 会话运行中，已用时 {status_result['duration_seconds']:.1f}秒"
            )

        asyncio.run(run_test())

    def test_04_stop_session(self):
        """测试会话停止"""
        print("🧪 测试4: 会话停止")

        async def run_test():
            # 先启动一个会话
            start_result = await self.wrapper.start_session(
                canvas_path=self.test_canvas_path, session_name="停止测试会话"
            )
            self.assertTrue(start_result["success"])

            # 等待一段时间，确保会话有运行时间
            await asyncio.sleep(1)

            # 停止会话
            stop_result = await self.wrapper.stop_session(save_report=True)
            self.assertTrue(stop_result["success"])
            self.assertIsNotNone(stop_result["end_time"])

            # 检查会话是否已从活跃列表中移除
            self.assertIsNone(self.wrapper.current_session)

            print(f"✅ 会话停止成功: 学习时长 {stop_result['duration_seconds']:.1f}秒")

        asyncio.run(run_test())

    def test_05_generate_report(self):
        """测试报告生成"""
        print("🧪 测试5: 报告生成")

        async def run_test():
            # 先启动一个会话
            start_result = await self.wrapper.start_session(
                canvas_path=self.test_canvas_path, session_name="报告测试会话"
            )
            self.assertTrue(start_result["success"])

            # 等待一段时间
            await asyncio.sleep(0.5)

            # 生成报告
            report_result = await self.wrapper.generate_report()
            self.assertTrue(report_result["success"])
            self.assertIsNotNone(report_result["report"])

            report = report_result["report"]
            self.assertEqual(report["session_id"], start_result["session_id"])
            self.assertEqual(report["session_name"], "报告测试会话")

            print(f"✅ 报告生成成功: {report['duration_seconds']:.1f}秒学习时长")

        asyncio.run(run_test())

    def test_06_multiple_canvases(self):
        """测试多Canvas管理"""
        print("🧪 测试6: 多Canvas管理")

        async def run_test():
            # 创建第二个测试Canvas
            test_canvas_2 = "tests/test_canvas_2.canvas"
            test_canvas_2_data = {
                "nodes": [
                    {
                        "id": "test2-question-1",
                        "type": "text",
                        "x": 100,
                        "y": 100,
                        "width": 200,
                        "height": 100,
                        "color": "1",
                        "content": "什么是第二个测试概念？",
                    }
                ],
                "edges": [],
            }

            with open(test_canvas_2, "w", encoding="utf-8") as f:
                json.dump(test_canvas_2_data, f, ensure_ascii=False, indent=2)

            # 启动第一个Canvas会话
            result1 = await self.wrapper.start_session(
                canvas_path=self.test_canvas_path, session_name="多Canvas测试1"
            )
            self.assertTrue(result1["success"])

            # 添加第二个Canvas到当前会话
            add_result = await self.wrapper._start_semantic(
                test_canvas_2, self.wrapper.current_session
            )
            self.assertTrue(add_result["success"])

            # 检查状态
            status = await self.wrapper.get_session_status()
            self.assertTrue(status["success"])
            self.assertIn(self.test_canvas_path, status["active_canvases"])
            self.assertIn(test_canvas_2, status["active_canvases"])

            print(f"✅ 多Canvas管理成功: {len(status['active_canvases'])}个Canvas")

            # 清理第二个测试文件
            Path(test_canvas_2).unlink()

        asyncio.run(run_test())

    def test_07_error_handling(self):
        """测试错误处理"""
        print("🧪 测试7: 错误处理")

        async def run_test():
            # 测试无效Canvas路径
            result1 = await self.wrapper.start_session(
                canvas_path="不存在的文件.canvas", session_name="错误测试会话"
            )
            # 这里应该能处理错误，但可能不会成功

            # 测试停止不存在的会话
            result2 = await self.wrapper.stop_session("不存在的会话ID")
            self.assertFalse(result2["success"])

            print(
                f"✅ 错误处理: 无效文件处理={result1.get('success', False)}, 无效会话处理={not result2['success']}"
            )

        asyncio.run(run_test())

    def test_08_performance(self):
        """测试性能指标"""
        print("🧪 测试8: 性能指标")

        async def run_test():
            # 测试启动性能
            start_time = time.time()

            result = await self.wrapper.start_session(
                canvas_path=self.test_canvas_path, session_name="性能测试会话"
            )

            startup_time = time.time() - start_time

            self.assertTrue(result["success"])
            self.assertLessThan(startup_time, 5.0, "启动时间应少于5秒")

            # 测试状态查询性能
            start_time = time.time()

            status = await self.wrapper.get_session_status()

            query_time = time.time() - start_time
            self.assertTrue(status["success"])
            self.assertLessThan(query_time, 1.0, "状态查询时间应少于1秒")

            print(
                f"✅ 性能测试通过: 启动时间={startup_time:.3f}s, 查询时间={query_time:.3f}s"
            )

        asyncio.run(run_test())


class TestLearningSessionIntegration(unittest.TestCase):
    """学习会话集成测试类"""

    def setUp(self):
        """测试前准备"""
        self.wrapper = LearningSessionWrapper()
        self.test_canvas_path = "tests/integration_test.canvas"
        self._create_integration_test_canvas()

    def tearDown(self):
        """测试后清理"""
        asyncio.run(self._cleanup_integration_test())

    def _create_integration_test_canvas(self):
        """创建集成测试Canvas"""
        integration_canvas = {
            "nodes": [
                {
                    "id": "integration-question-1",
                    "type": "text",
                    "x": 100,
                    "y": 100,
                    "width": 300,
                    "height": 100,
                    "color": "1",
                    "content": "这是一个集成测试问题，用于验证学习会话系统的完整性。",
                },
                {
                    "id": "integration-yellow-1",
                    "type": "text",
                    "x": 450,
                    "y": 100,
                    "width": 300,
                    "height": 100,
                    "color": "6",
                    "content": "这是我对集成测试问题的理解和回答，用于测试黄色节点的记忆功能。",
                },
                {
                    "id": "integration-green-1",
                    "type": "text",
                    "x": 800,
                    "y": 100,
                    "width": 300,
                    "height": 100,
                    "color": "2",
                    "content": "这是完全理解的集成测试概念，已经达到了学习目标。",
                },
            ],
            "edges": [
                {
                    "id": "integration-edge-1",
                    "fromNode": "integration-question-1",
                    "toNode": "integration-yellow-1",
                    "label": "理解过程",
                },
                {
                    "id": "integration-edge-2",
                    "fromNode": "integration-yellow-1",
                    "toNode": "integration-green-1",
                    "label": "理解提升",
                },
            ],
        }

        test_dir = Path("tests")
        test_dir.mkdir(exist_ok=True)

        with open(self.test_canvas_path, "w", encoding="utf-8") as f:
            json.dump(integration_canvas, f, ensure_ascii=False, indent=2)

    def _cleanup_integration_test(self):
        """清理集成测试"""
        # 停止会话
        if self.wrapper.current_session:
            asyncio.run(self.wrapper.stop_session())

        # 清理测试文件
        test_file = Path(self.test_canvas_path)
        if test_file.exists():
            test_file.unlink()

    def test_01_full_workflow(self):
        """测试完整工作流程"""
        print("🧪 集成测试1: 完整工作流程")

        async def run_workflow_test():
            # 1. 启动会话
            start_result = await self.wrapper.start_session(
                canvas_path=self.test_canvas_path, session_name="集成测试会话"
            )
            self.assertTrue(start_result["success"])

            # 2. 模拟学习活动
            await asyncio.sleep(1)  # 模拟学习时间

            # 3. 检查状态
            status = await self.wrapper.get_session_status()
            self.assertTrue(status["success"])

            # 4. 生成报告
            report = await self.wrapper.generate_report()
            self.assertTrue(report["success"])

            # 5. 停止会话
            stop_result = await self.wrapper.stop_session()
            self.assertTrue(stop_result["success"])

            # 6. 验证完整性
            self.assertEqual(start_result["session_id"], report["report"]["session_id"])
            self.assertIsNotNone(stop_result["end_time"])
            self.assertIsNone(self.wrapper.current_session)

            print("✅ 完整工作流程测试通过")

        asyncio.run(run_workflow_test())


class TestLearningSessionPerformance(unittest.TestCase):
    """学习会话性能测试类"""

    def setUp(self):
        """性能测试准备"""
        self.wrapper = LearningSessionWrapper()
        self.test_canvases = []

        # 创建多个测试Canvas
        for i in range(5):
            canvas_path = f"tests/perf_test_{i}.canvas"
            test_canvas = {
                "nodes": [
                    {
                        "id": f"perf-node-{i}",
                        "type": "text",
                        "x": 100,
                        "y": 100,
                        "width": 200,
                        "height": 100,
                        "color": "1",
                        "content": f"性能测试节点{i}",
                    }
                ],
                "edges": [],
            }

            test_dir = Path("tests")
            test_dir.mkdir(exist_ok=True)

            with open(canvas_path, "w", encoding="utf-8") as f:
                json.dump(test_canvas, f, ensure_ascii=False, indent=2)

            self.test_canvases.append(canvas_path)

    def tearDown(self):
        """性能测试清理"""
        asyncio.run(self._cleanup_performance_test())

        # 清理测试文件
        for canvas_path in self.test_canvases:
            if Path(canvas_path).exists():
                Path(canvas_path).unlink()

    def _cleanup_performance_test(self):
        """清理性能测试"""

        async def cleanup():
            if self.wrapper.current_session:
                await self.wrapper.stop_session()

        asyncio.run(cleanup())

    def test_01_startup_performance(self):
        """测试启动性能"""
        print("🚀 性能测试1: 启动性能")

        async def run_performance_test():
            startup_times = []

            for canvas_path in self.test_canvases:
                start_time = time.time()

                result = await self.wrapper.start_session(
                    canvas_path=canvas_path,
                    session_name=f"性能测试_{Path(canvas_path).stem}",
                )

                startup_time = time.time() - start_time
                startup_times.append(startup_time)

                self.assertTrue(result["success"])
                await self.wrapper.stop_session(result["session_id"])

            avg_time = sum(startup_times) / len(startup_times)
            max_time = max(startup_times)
            min_time = min(startup_times)

            self.assertLessThan(
                avg_time, 3.0, f"平均启动时间应少于3秒，实际: {avg_time:.3f}s"
            )
            self.assertLessThan(
                max_time, 5.0, f"最大启动时间应少于5秒，实际: {max_time:.3f}s"
            )

            print(
                f"✅ 启动性能: 平均={avg_time:.3f}s, 最大={max_time:.3f}s, 最小={min_time:.3f}s"
            )

        asyncio.run(run_performance_test())

    def test_02_concurrent_sessions(self):
        """测试并发会话"""
        print("⚡ 性能测试2: 并发会话")

        async def start_concurrent_sessions():
            tasks = []

            for i, canvas_path in enumerate(self.test_canvases[:3]):  # 测试3个并发会话
                task = self.wrapper.start_session(
                    canvas_path=canvas_path, session_name=f"并发测试{i + 1}"
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks)

            # 验证所有会话都成功启动
            for i, result in enumerate(results):
                self.assertTrue(result["success"], f"会话{i + 1}启动失败")

            # 检查是否有会话冲突
            active_sessions = self.wrapper.coordinator.active_sessions
            self.assertEqual(
                len(active_sessions),
                3,
                f"应有3个活跃会话，实际: {len(active_sessions)}",
            )

            # 停止所有会话
            for session_id in list(active_sessions.keys()):
                stop_result = await self.wrapper.stop_session(session_id)
                self.assertTrue(stop_result["success"])

            print(f"✅ 并发测试通过: {len(results)}个会话并发启动")

            return len(results)

        result_count = asyncio.run(start_concurrent_sessions())
        self.assertEqual(result_count, 3, "应该成功启动3个并发会话")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("Canvas学习会话管理系统 - 测试套件")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 创建测试套件
    test_suite = unittest.TestSuite()

    # 添加测试类
    test_classes = [
        TestLearningSessionSystem,
        TestLearningSessionIntegration,
        TestLearningSessionPerformance,
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # 统计结果
    total_tests = result.testsRun
    failures = result.failures
    errors = result.errors
    skipped = result.skipped

    print()
    print("=" * 60)
    print("测试结果统计")
    print("=" * 60)
    print(f"总测试数: {total_tests}")
    print(f"成功: {total_tests - failures - errors}")
    print(f"失败: {failures}")
    print(f"错误: {errors}")
    print(f"跳过: {skipped}")
    print(f"成功率: {((total_tests - failures - errors) / total_tests * 100):.1f}%")

    if failures == 0 and errors == 0:
        print("\n🎉 所有测试通过！学习会话管理系统准备就绪。")
        return True
    else:
        print(f"\n❌ 发现 {failures + errors} 个问题，请检查并修复。")
        return False


if __name__ == "__main__":
    success = run_all_tests()

    if success:
        print("\n📋 下一步建议:")
        print("1. 集成到现有的斜杠命令系统")
        print("2. 进行用户测试")
        print("3. 根据用户反馈进行优化")
    else:
        print("\n🔧 下一步建议:")
        print("1. 修复失败的测试用例")
        print("2. 重新运行测试")
        print("3. 所有测试通过后再进行集成")
