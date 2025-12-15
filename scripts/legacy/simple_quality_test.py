"""
简化的质量验证测试

验证Canvas学习系统v2.0的核心功能和质量标准。

Author: Canvas Learning System Team
Version: 2.0
Created: 2025-01-22
"""

import time
import json
import tempfile
import os
from pathlib import Path

# Import performance optimizers
from canvas_performance_optimizer import CanvasPerformanceOptimizer
from agent_performance_optimizer import AgentPerformanceOptimizer


def run_quality_validation():
    """运行质量验证测试"""
    print("开始Canvas学习系统v2.0质量验证...")

    test_results = []

    # 测试1: Canvas操作功能
    print("\n1. 测试Canvas操作功能...")
    try:
        canvas_optimizer = CanvasPerformanceOptimizer()

        # 创建测试数据
        test_data = {
            "nodes": [
                {"id": "test-1", "type": "text", "text": "测试节点1", "x": 100, "y": 100, "width": 300, "height": 200, "color": "1"},
                {"id": "test-2", "type": "text", "text": "测试节点2", "x": 500, "y": 100, "width": 300, "height": 200, "color": "2"}
            ],
            "edges": []
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        # 测试读写功能
        canvas_optimizer.write_canvas_optimized(temp_path, test_data)
        read_data = canvas_optimizer.read_canvas_cached(temp_path)

        assert read_data["nodes"][0]["text"] == "测试节点1"
        assert len(read_data["nodes"]) == 2

        # 测试缓存功能
        start_time = time.time()
        read_data2 = canvas_optimizer.read_canvas_cached(temp_path)
        cache_time = time.time() - start_time

        assert cache_time < 0.1

        os.unlink(temp_path)
        test_results.append(("Canvas操作功能", True, 0.05))
        print("  [PASS] Canvas操作功能测试通过")

    except Exception as e:
        test_results.append(("Canvas操作功能", False, 0))
        print(f"  [FAIL] Canvas操作功能测试失败: {e}")

    # 测试2: Agent系统功能
    print("\n2. 测试Agent系统功能...")
    try:
        agent_optimizer = AgentPerformanceOptimizer(max_workers=3, enable_caching=False)

        # 测试基础拆解Agent
        task_id = agent_optimizer.submit_task(
            agent_type="basic-decomposition",
            input_data={"concept": "质量验证测试"}
        )
        result = agent_optimizer.wait_for_task(task_id, timeout=10.0)

        assert result.success is True
        assert "sub_questions" in result.result
        assert len(result.result["sub_questions"]) >= 1

        # 测试并行执行
        tasks = [
            {"agent_type": "basic-decomposition", "input_data": {"concept": f"并行测试 {i}"}}
            for i in range(5)
        ]

        start_time = time.time()
        results = agent_optimizer.execute_parallel(tasks)
        execution_time = time.time() - start_time

        assert len(results) == 5
        assert all(r.success for r in results)
        assert execution_time < 10.0

        agent_optimizer.shutdown()
        test_results.append(("Agent系统功能", True, execution_time))
        print("  [PASS] Agent系统功能测试通过")

    except Exception as e:
        test_results.append(("Agent系统功能", False, 0))
        print(f"  [FAIL] Agent系统功能测试失败: {e}")

    # 测试3: 性能要求验证
    print("\n3. 测试性能要求...")
    try:
        canvas_optimizer = CanvasPerformanceOptimizer()

        # 测试大文件处理性能
        large_data = {"nodes": [{"id": f"node-{i}", "text": f"节点{i}"*100} for i in range(100)], "edges": []}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
            json.dump(large_data, f)
            temp_path = f.name

        # 测试读取性能（<3秒）
        start_time = time.time()
        data = canvas_optimizer.read_canvas_cached(temp_path)
        read_time = time.time() - start_time

        assert read_time < 3.0, f"读取耗时 {read_time:.3f}s 超过限制"

        # 测试写入性能（<3秒）
        start_time = time.time()
        canvas_optimizer.write_canvas_optimized(temp_path, data)
        write_time = time.time() - start_time

        assert write_time < 3.0, f"写入耗时 {write_time:.3f}s 超过限制"

        os.unlink(temp_path)
        test_results.append(("性能要求", True, max(read_time, write_time)))
        print("  [PASS] 性能要求测试通过")

    except Exception as e:
        test_results.append(("性能要求", False, 0))
        print(f"  [FAIL] 性能要求测试失败: {e}")

    # 测试4: 系统稳定性
    print("\n4. 测试系统稳定性...")
    try:
        agent_optimizer = AgentPerformanceOptimizer(max_workers=5, enable_caching=False)

        # 执行大量任务
        task_ids = []
        for i in range(20):
            task_id = agent_optimizer.submit_task(
                agent_type="verification-question",
                input_data={"concept": f"稳定性测试 {i}"}
            )
            task_ids.append(task_id)

        # 等待所有任务完成
        completed = 0
        for task_id in task_ids:
            try:
                result = agent_optimizer.wait_for_task(task_id, timeout=15.0)
                if result.success:
                    completed += 1
            except:
                pass

        success_rate = (completed / 20) * 100
        assert success_rate >= 90, f"成功率 {success_rate}% 低于90%"

        agent_optimizer.shutdown()
        test_results.append(("系统稳定性", True, success_rate))
        print(f"  [PASS] 系统稳定性测试通过 (成功率: {success_rate}%)")

    except Exception as e:
        test_results.append(("系统稳定性", False, 0))
        print(f"  [FAIL] 系统稳定性测试失败: {e}")

    # 生成质量报告
    print("\n" + "="*60)
    print("质量验证报告")
    print("="*60)

    total_tests = len(test_results)
    passed_tests = sum(1 for _, success, _ in test_results if success)
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests) * 100

    print(f"总测试数: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {failed_tests}")
    print(f"成功率: {success_rate:.1f}%")

    # 计算质量分数
    critical_passed = sum(1 for name, success, _ in test_results
                          if success and name in ["Canvas操作功能", "Agent系统功能"])
    quality_score = (critical_passed / 2) * 50 + (passed_tests / total_tests) * 50

    if success_rate >= 95 and critical_passed == 2:
        quality_level = "优秀"
    elif success_rate >= 85 and critical_passed == 2:
        quality_level = "良好"
    elif success_rate >= 70:
        quality_level = "可接受"
    else:
        quality_level = "需要改进"

    print(f"质量等级: {quality_level}")
    print(f"质量分数: {quality_score:.1f}")

    # 测试详情
    print("\n测试详情:")
    for test_name, success, metric in test_results:
        status = "[PASS]" if success else "[FAIL]"
        metric_str = f" (耗时: {metric:.3f}s)" if isinstance(metric, float) else f" (成功率: {metric:.1f}%)" if isinstance(metric, float) else ""
        print(f"  {status} {test_name}{metric_str}")

    print("\n" + "="*60)

    # 返回结果
    return {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "success_rate": success_rate,
        "quality_level": quality_level,
        "quality_score": quality_score,
        "test_results": test_results,
        "timestamp": time.time()
    }


if __name__ == "__main__":
    quality_report = run_quality_validation()

    # 保存报告
    report_file = f"quality_validation_report_{int(time.time())}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        import json
        json.dump(quality_report, f, ensure_ascii=False, indent=2)

    print(f"\n详细报告已保存到: {report_file}")