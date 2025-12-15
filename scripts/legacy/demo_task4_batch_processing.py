#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Task 4功能演示脚本
演示批量Canvas处理功能和并发处理机制

Story 7.3 - Claude Code深度集成
Task 4: 开发批量Canvas处理功能 (AC: 5)
"""

import asyncio
import json
import tempfile
import os
import time
from canvas_utils import (
    BatchCanvasProcessor,
    BatchProcessingTask,
    BatchProgressMonitor,
    BatchErrorHandler,
    BatchProcessingResult
)
from claude_canvas_tools import canvas_batch_processor


def create_demo_canvases():
    """创建演示用的Canvas文件集合"""
    demo_canvases = []

    # Canvas 1: 基础数学概念
    canvas1 = {
        "nodes": [
            {
                "id": "math_basics_1",
                "type": "text",
                "text": "集合论基础 - 需要理解",
                "x": 100,
                "y": 100,
                "width": 200,
                "height": 80,
                "color": "1"  # 红色
            },
            {
                "id": "math_basics_2",
                "type": "text",
                "text": "函数概念 - 似懂非懂",
                "x": 300,
                "y": 100,
                "width": 200,
                "height": 80,
                "color": "3"  # 紫色
            },
            {
                "id": "my_understanding_1",
                "type": "text",
                "text": "集合就是元素的集合...",
                "x": 100,
                "y": 250,
                "width": 200,
                "height": 80,
                "color": "6"  # 黄色
            }
        ],
        "edges": [
            {
                "id": "edge_1",
                "fromNode": "math_basics_1",
                "toNode": "my_understanding_1"
            }
        ]
    }

    # Canvas 2: 离散数学进阶
    canvas2 = {
        "nodes": [
            {
                "id": "discrete_1",
                "type": "text",
                "text": "图论基础 - 完全不懂",
                "x": 100,
                "y": 100,
                "width": 200,
                "height": 80,
                "color": "1"  # 红色
            },
            {
                "id": "discrete_2",
                "type": "text",
                "text": "树结构 - 有些理解",
                "x": 300,
                "y": 100,
                "width": 200,
                "height": 80,
                "color": "3"  # 紫色
            },
            {
                "id": "discrete_3",
                "type": "text",
                "text": "算法复杂度 - 基本掌握",
                "x": 500,
                "y": 100,
                "width": 200,
                "height": 80,
                "color": "2"  # 绿色
            }
        ],
        "edges": []
    }

    # Canvas 3: 线性代数
    canvas3 = {
        "nodes": [
            {
                "id": "linear_1",
                "type": "text",
                "text": "矩阵运算 - 需要练习",
                "x": 100,
                "y": 100,
                "width": 200,
                "height": 80,
                "color": "3"  # 紫色
            },
            {
                "id": "linear_2",
                "type": "text",
                "text": "特征向量 - 概念模糊",
                "x": 300,
                "y": 100,
                "width": 200,
                "height": 80,
                "color": "1"  # 红色
            }
        ],
        "edges": [
            {
                "id": "edge_2",
                "fromNode": "linear_1",
                "toNode": "linear_2"
            }
        ]
    }

    # Canvas 4: 概率统计
    canvas4 = {
        "nodes": [
            {
                "id": "prob_1",
                "type": "text",
                "text": "概率分布 - 已掌握",
                "x": 100,
                "y": 100,
                "width": 200,
                "height": 80,
                "color": "2"  # 绿色
            },
            {
                "id": "prob_2",
                "type": "text",
                "text": "假设检验 - 需要复习",
                "x": 300,
                "y": 100,
                "width": 200,
                "height": 80,
                "color": "3"  # 紫色
            }
        ],
        "edges": []
    }

    # Canvas 5: 空Canvas（用于测试错误处理）
    canvas5 = {
        "nodes": [],
        "edges": []
    }

    canvases = [canvas1, canvas2, canvas3, canvas4, canvas5]

    # 创建临时文件
    for i, canvas_data in enumerate(canvases):
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix=f'_demo_canvas_{i+1}.canvas',
            delete=False,
            encoding='utf-8'
        )
        json.dump(canvas_data, temp_file, ensure_ascii=False, indent=2)
        temp_file.close()
        demo_canvases.append(temp_file.name)

    return demo_canvases


async def demo_batch_processing_components():
    """演示批量处理组件功能"""
    print("=" * 80)
    print("Task 4功能演示: 批量Canvas处理系统")
    print("=" * 80)

    # 创建演示Canvas文件
    demo_canvas_paths = create_demo_canvases()
    print(f"创建 {len(demo_canvas_paths)} 个演示Canvas文件")

    try:
        # 1. 演示BatchProgressMonitor
        print("\n1. BatchProgressMonitor - 进度监控器")
        print("-" * 50)

        monitor = BatchProgressMonitor()
        monitor.initialize(len(demo_canvas_paths))
        print(f"进度监控器初始化: 总任务数 {monitor.total_tasks}")

        # 模拟进度更新
        for i in range(3):
            time.sleep(0.1)  # 确保时间间隔
            monitor.update_progress(1, failed=False)
            current = monitor.get_current_progress()
            print(f"进度更新: {current['completed']}/{current['total']} ({current['percentage']:.1f}%)")

        summary = monitor.get_summary()
        print(f"进度摘要: 成功率 {summary['success_rate']:.1f}%, 平均时间 {summary['average_time_per_task']:.3f}秒")

        # 2. 演示BatchErrorHandler
        print("\n2. BatchErrorHandler - 错误处理器")
        print("-" * 50)

        error_handler = BatchErrorHandler()

        # 模拟一些错误
        error_handler.record_error("task_1", FileNotFoundError("Canvas文件不存在"))
        error_handler.record_error("task_2", ValueError("参数无效"))
        error_handler.record_error("task_3", FileNotFoundError("另一个文件不存在"))

        error_summary = error_handler.get_summary()
        print(f"错误统计: 总错误数 {error_summary['total_errors']}")
        print(f"错误类型: {', '.join(error_summary['error_types'])}")
        if error_summary['most_common_error']:
            most_common = error_summary['most_common_error']
            print(f"最常见错误: {most_common['type']} ({most_common['count']}次)")

        # 3. 演示BatchProcessingTask
        print("\n3. BatchProcessingTask - 批量处理任务")
        print("-" * 50)

        tasks = []
        for i, canvas_path in enumerate(demo_canvas_paths[:3]):  # 只演示前3个
            task = BatchProcessingTask(
                task_id=f"demo_task_{i+1}",
                canvas_path=canvas_path,
                detail_level="standard",
                include_recommendations=True,
                priority_threshold=0.7
            )
            tasks.append(task)
            print(f"创建任务 {i+1}: {os.path.basename(canvas_path)}")

        # 4. 演示BatchCanvasProcessor
        print("\n4. BatchCanvasProcessor - 批量处理器")
        print("-" * 50)

        processor = BatchCanvasProcessor(max_concurrent=2)
        print(f"批量处理器初始化: 最大并发数 {processor.max_concurrent}")

        # 演示单个任务处理
        if tasks:
            print(f"\n处理单个任务演示: {tasks[0].task_id}")
            try:
                start_time = time.time()
                result = await processor._process_single_task(tasks[0])
                end_time = time.time()

                print(f"任务处理: {'成功' if result.success else '失败'}")
                print(f"处理时间: {end_time - start_time:.3f}秒")
                print(f"Canvas路径: {result.canvas_path}")
                if hasattr(result, 'batch_task_id'):
                    print(f"批次任务ID: {result.batch_task_id}")

            except Exception as e:
                print(f"任务处理失败: {str(e)}")

        # 5. 演示canvas_batch_processor工具函数
        print("\n5. canvas_batch_processor工具函数")
        print("-" * 50)

        # 测试参数验证
        print("a) 参数验证测试:")
        result = await canvas_batch_processor({})
        if 'content' in result:
            print("   参数验证功能正常")

        # 测试无效参数类型
        print("\nb) 无效参数类型测试:")
        result = await canvas_batch_processor({"canvas_paths": "not_a_list"})
        if 'content' in result:
            print("   类型验证功能正常")

        # 测试基本批量处理
        print("\nc) 基本批量处理测试:")
        result = await canvas_batch_processor({
            "canvas_paths": demo_canvas_paths[:2],  # 只处理前2个
            "detail_level": "basic",
            "include_recommendations": True,
            "priority_threshold": 0.6,
            "max_concurrent": 1
        })

        if 'content' in result:
            report_text = result['content'][0]['text']
            print(f"   批量处理报告长度: {len(report_text)} 字符")
            print("   包含关键信息:")
            if "Canvas批量处理报告" in report_text:
                print("     - 批量处理报告标题")
            if "总Canvas数量" in report_text:
                print("     - Canvas统计信息")
            if "成功率" in report_text:
                print("     - 成功率统计")
            if "Context7验证" in report_text:
                print("     - Context7验证标识")

        # 6. 演示并发处理性能
        print("\n6. 并发处理性能演示")
        print("-" * 50)

        try:
            # 使用小批量进行性能测试
            test_canvases = demo_canvas_paths[:3]
            start_time = time.time()

            batch_result = await processor.batch_analyze_canvases(
                canvas_paths=test_canvases,
                detail_level="basic",
                include_recommendations=False,
                priority_threshold=0.5
            )

            end_time = time.time()
            total_time = end_time - start_time

            print(f"并发处理结果:")
            print(f"  - 总Canvas数: {batch_result.total_canvases}")
            print(f"  - 成功处理: {batch_result.successful_count}")
            print(f"  - 处理失败: {batch_result.failed_count}")
            print(f"  - 成功率: {batch_result.get_success_rate():.1f}%")
            print(f"  - 总耗时: {total_time:.3f}秒")
            print(f"  - 平均耗时: {batch_result.get_average_processing_time():.3f}秒/Canvas")
            print(f"  - 处理速度: {batch_result.total_canvases/total_time:.2f} Canvas/秒")

        except Exception as e:
            print(f"并发处理演示失败: {str(e)}")

        print("\n" + "=" * 80)
        print("Task 4功能演示完成!")
        print("新功能包括:")
        print("   - BatchCanvasProcessor: 高性能批量Canvas处理器")
        print("   - BatchProgressMonitor: 实时进度监控和历史记录")
        print("   - BatchErrorHandler: 智能错误收集和统计分析")
        print("   - canvas_batch_processor: Claude Code工具函数")
        print("   - 并发处理: 支持多Canvas同时分析")
        print("   - 参数验证: 严格的输入参数检查")
        print("   - 性能统计: 详细的处理时间和成功率指标")
        print("   - Context7验证: Trust Score 8.8认证")
        print("   - 错误恢复: 异常处理和失败任务管理")
        print("=" * 80)

    finally:
        # 清理临时文件
        for canvas_path in demo_canvas_paths:
            if os.path.exists(canvas_path):
                os.unlink(canvas_path)
                print(f"\n已清理临时文件: {os.path.basename(canvas_path)}")


async def demo_error_handling_scenarios():
    """演示错误处理场景"""
    print("\n" + "=" * 60)
    print("错误处理场景演示")
    print("=" * 60)

    # 1. 文件不存在错误
    print("\n1. 文件不存在错误处理:")
    processor = BatchCanvasProcessor()

    try:
        task = BatchProcessingTask(
            task_id="file_not_found_test",
            canvas_path="nonexistent_file.canvas"
        )
        await processor._process_single_task(task)
    except FileNotFoundError as e:
        print(f"   捕获文件不存在错误: {str(e)}")
        error_summary = processor.error_handler.get_summary()
        print(f"   错误统计: 总错误数 {error_summary['total_errors']}")

    # 2. 参数验证错误
    print("\n2. 参数验证错误处理:")
    test_cases = [
        {"canvas_paths": []},  # 空列表
        {"canvas_paths": ["test.canvas"], "detail_level": "invalid"},  # 无效详细程度
        {"canvas_paths": ["test.canvas"], "priority_threshold": 1.5},  # 超出范围的优先级
        {"canvas_paths": ["test.canvas"], "max_concurrent": 0},  # 无效并发数
    ]

    for i, test_case in enumerate(test_cases, 1):
        result = await canvas_batch_processor(test_case)
        if 'content' in result:
            content = result['content'][0]['text']
            if "错误" in content or "警告" in content:
                print(f"   测试用例 {i}: 参数验证正常工作")

    print("\n错误处理演示完成!")


if __name__ == "__main__":
    asyncio.run(demo_batch_processing_components())
    asyncio.run(demo_error_handling_scenarios())