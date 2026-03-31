"""
Story 10.2.5 (AC2): Epic 10.2 性能基准测试

Performance Benchmarking Tests for Epic 10.2: Async Parallel Execution Engine

测试目标:
- 验证10节点处理时间 ≤ 15秒
- 验证20节点处理时间 ≤ 30秒
- 验证50节点处理时间 ≤ 60秒
- 记录详细性能数据用于分析

Author: Dev Agent (James)
Date: 2025-11-04
Version: v1.0
"""

import asyncio
import time
from pathlib import Path
from typing import Dict

import pytest

# ============================================================================
# Performance Benchmarks
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.benchmark
async def test_performance_benchmarks():
    """
    AC2: 性能基准测试

    测试10/20/50节点的处理性能，记录详细的性能指标

    性能目标:
    - 10节点 ≤ 15秒
    - 20节点 ≤ 30秒
    - 50节点 ≤ 60秒
    """
    print("\n" + "=" * 70)
    print("AC2: 性能基准测试")
    print("=" * 70)

    # 导入依赖
    try:
        from command_handlers.intelligent_parallel_handler import (
            IntelligentParallelCommandHandler,
        )
    except ImportError as e:
        pytest.skip(f"Required modules not available: {e}")

    # 测试数据路径
    test_cases = [
        ("test_data/canvas_10_nodes.canvas", 10, 15),
        ("test_data/canvas_20_nodes.canvas", 20, 30),
        ("test_data/canvas_50_nodes.canvas", 50, 60),
    ]

    results = {}

    for canvas_path, node_count, time_limit in test_cases:
        # 验证文件存在
        if not Path(canvas_path).exists():
            print(f"⚠️  跳过: {canvas_path} 不存在")
            continue

        print(f"\n{'=' * 70}")
        print(f"测试: {node_count}节点")
        print(f"文件: {canvas_path}")
        print(f"性能目标: ≤{time_limit}秒")
        print(f"{'=' * 70}")

        # 创建Handler
        handler = IntelligentParallelCommandHandler()

        # 执行测试
        start_time = time.time()

        result = await handler.execute_async(
            canvas_path,
            options={
                "auto": True,
                "max": 12,
                "grouping": "intelligent",
                "verbose": False,
            },
        )

        elapsed_time = time.time() - start_time

        # 记录结果
        results[f"{node_count}_nodes"] = {
            "elapsed_time": elapsed_time,
            "time_limit": time_limit,
            "passed": elapsed_time <= time_limit,
            "result": result,
        }

        # 输出结果
        status = "✅ PASS" if elapsed_time <= time_limit else "❌ FAIL"
        print(f"\n{status} {node_count}节点测试")
        print(f"⏱️  执行时间: {elapsed_time:.2f}s")
        print(f"🎯 性能目标: {time_limit}s")
        print(f"📊 性能比率: {elapsed_time / time_limit * 100:.1f}%")

        # 验证性能目标
        assert elapsed_time <= time_limit, (
            f"{node_count}节点超时: {elapsed_time:.2f}s > {time_limit}s"
        )

    # 生成性能报告
    print("\n" + "=" * 70)
    print("📊 性能基准测试总结")
    print("=" * 70)

    for key, data in results.items():
        node_count = key.replace("_nodes", "")
        print(f"\n{node_count}节点:")
        print(f"  ⏱️  执行时间: {data['elapsed_time']:.2f}s")
        print(f"  🎯 性能目标: {data['time_limit']}s")
        print(f"  ✅ 测试结果: {'通过' if data['passed'] else '失败'}")

    print("\n" + "=" * 70)
    print("🎉 所有性能基准测试通过！")
    print("=" * 70)

    return results


# ============================================================================
# Canvas Read/Write Performance Tests
# ============================================================================


@pytest.mark.benchmark
def test_canvas_read_performance():
    """
    测试Canvas文件读取性能

    目标: 单次读取 < 0.1秒
    """
    print("\n" + "=" * 70)
    print("Canvas文件读取性能测试")
    print("=" * 70)

    try:
        from canvas_utils import CanvasJSONOperator
    except ImportError as e:
        pytest.skip(f"canvas_utils not available: {e}")

    canvas_path = "test_data/canvas_20_nodes.canvas"

    if not Path(canvas_path).exists():
        pytest.skip(f"Test file not found: {canvas_path}")

    # 执行100次读取
    iterations = 100
    start_time = time.time()

    for i in range(iterations):
        canvas_data = CanvasJSONOperator.read_canvas(canvas_path)

    elapsed_time = time.time() - start_time
    avg_time = elapsed_time / iterations

    print(f"📊 执行次数: {iterations}")
    print(f"⏱️  总时间: {elapsed_time:.3f}s")
    print(f"⏱️  平均时间: {avg_time * 1000:.2f}ms")
    print("🎯 性能目标: <100ms")

    assert avg_time < 0.1, f"读取性能不达标: {avg_time * 1000:.2f}ms > 100ms"

    print("✅ Canvas读取性能测试通过")


@pytest.mark.benchmark
def test_canvas_write_performance():
    """
    测试Canvas文件写入性能

    目标: 单次写入 < 0.5秒
    """
    print("\n" + "=" * 70)
    print("Canvas文件写入性能测试")
    print("=" * 70)

    try:
        from canvas_utils import CanvasJSONOperator
    except ImportError as e:
        pytest.skip(f"canvas_utils not available: {e}")

    canvas_path = "test_data/canvas_20_nodes.canvas"

    if not Path(canvas_path).exists():
        pytest.skip(f"Test file not found: {canvas_path}")

    # 读取Canvas数据
    canvas_data = CanvasJSONOperator.read_canvas(canvas_path)

    # 执行10次写入
    iterations = 10
    start_time = time.time()

    for i in range(iterations):
        CanvasJSONOperator.write_canvas(canvas_path, canvas_data)

    elapsed_time = time.time() - start_time
    avg_time = elapsed_time / iterations

    print(f"📊 执行次数: {iterations}")
    print(f"⏱️  总时间: {elapsed_time:.3f}s")
    print(f"⏱️  平均时间: {avg_time * 1000:.2f}ms")
    print("🎯 性能目标: <500ms")

    assert avg_time < 0.5, f"写入性能不达标: {avg_time * 1000:.2f}ms > 500ms"

    print("✅ Canvas写入性能测试通过")


# ============================================================================
# Async Engine Performance Tests
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.benchmark
async def test_async_engine_overhead():
    """
    测试AsyncExecutionEngine的开销

    验证异步执行引擎本身的性能开销是否合理
    """
    print("\n" + "=" * 70)
    print("AsyncExecutionEngine开销测试")
    print("=" * 70)

    try:
        from command_handlers.async_execution_engine import (
            AsyncExecutionEngine,
            AsyncTask,
        )
    except ImportError as e:
        pytest.skip(f"AsyncExecutionEngine not available: {e}")

    # 创建executor函数 (处理任务)
    async def simple_executor(task: AsyncTask) -> Dict:
        """简单的测试executor"""
        await asyncio.sleep(0.01)  # 模拟10ms任务
        return {
            "task_id": task.task_id,
            "success": True,
            "data": f"Task {task.task_id} completed",
        }

    # 测试场景: 10个并发任务
    task_count = 10
    engine = AsyncExecutionEngine(max_concurrency=12)

    # 创建任务
    tasks = []
    for i in range(task_count):
        task = AsyncTask(
            task_id=f"task-{i}",
            agent_name="test-agent",
            node_data={"index": i, "content": f"Test task {i}"},
            priority=1,
        )
        tasks.append(task)

    # 执行任务
    print(f"🚀 执行{task_count}个并发任务...")
    start_time = time.time()

    result = await engine.execute_parallel(tasks, simple_executor)

    elapsed_time = time.time() - start_time

    # 理论最小时间 (如果完美并行) = 10ms
    # 实际时间应该接近10ms，开销应该很小
    theoretical_min = 0.01  # 10ms
    overhead = elapsed_time - theoretical_min

    print(f"📊 任务数量: {task_count}")
    print(f"⏱️  执行时间: {elapsed_time * 1000:.2f}ms")
    print(f"🎯 理论最小: {theoretical_min * 1000:.2f}ms")
    print(f"📉 引擎开销: {overhead * 1000:.2f}ms")
    print(f"✅ 成功任务: {result['success']}/{task_count}")

    # 验证开销合理 (应该小于50ms)
    assert overhead < 0.05, f"AsyncEngine开销过大: {overhead * 1000:.2f}ms > 50ms"

    print("✅ AsyncExecutionEngine开销测试通过")


# ============================================================================
# Test Execution Summary
# ============================================================================

if __name__ == "__main__":
    """本地测试执行入口"""
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                   Epic 10.2 Performance Benchmarks                       ║
║                   Story 10.2.5 (AC2): 性能基准测试                       ║
╚══════════════════════════════════════════════════════════════════════════╝

测试覆盖:
- ✅ AC2: 10/20/50节点性能基准测试
- ✅ Canvas读取性能测试
- ✅ Canvas写入性能测试
- ✅ AsyncEngine开销测试

运行方式:
  pytest tests/test_epic10_2_performance.py -v
  pytest tests/test_epic10_2_performance.py -v -m "benchmark"

""")
    pytest.main([__file__, "-v", "--tb=short"])
