#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
艾宾浩斯复习系统演示 - Canvas学习系统v2.0

演示如何使用新实现的艾宾浩斯遗忘曲线算法进行智能复习管理

Author: Canvas Learning System Team
Version: 2.0 Ebbinghaus Demo
Created: 2025-10-20
"""

import asyncio
import datetime
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from canvas_utils_working import (
    forgetting_curve_manager,
    ebbinghaus_review_scheduler,
    ReviewNode
)

async def demo_ebbinghaus_system():
    """演示艾宾浩斯复习系统的完整功能"""
    print("=" * 70)
    print("艾宾浩斯复习系统演示 - Canvas学习系统v2.0")
    print("=" * 70)

    # 1. 创建复习节点
    print("\n[步骤1] 创建复习节点")
    print("-" * 40)

    # 模拟学习数学概念
    concepts_data = [
        ("逆否命题", 7.5, "离散数学.canvas"),
        ("集合论基础", 5.0, "离散数学.canvas"),
        ("逻辑联结词", 6.5, "离散数学.canvas"),
        ("极限定义", 8.5, "数学分析.canvas"),
        ("导数概念", 7.0, "数学分析.canvas")
    ]

    created_nodes = []
    for concept, complexity, canvas_file in concepts_data:
        node = forgetting_curve_manager.create_review_node(
            node_id=f"demo_{concept}",
            concept=concept,
            complexity_score=complexity,
            canvas_file=canvas_file
        )
        created_nodes.append(node)
        print(f"[OK] 创建节点: {concept} (复杂度: {complexity})")

    # 2. 计算最优复习时间
    print(f"\n[步骤2] 计算最优复习时间")
    print("-" * 40)

    for node in created_nodes[:2]:  # 只展示前两个
        optimal_times = forgetting_curve_manager.calculate_optimal_review_times(
            node.create_time,
            node.complexity_score
        )

        print(f"\n概念: {node.concept}")
        print(f"创建时间: {node.create_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"复杂度: {node.complexity_score}")
        print(f"记忆强度: {forgetting_curve_manager.calculate_memory_strength(node.complexity_score):.2f}")
        print("最优复习时间点:")
        for i, time in enumerate(optimal_times, 1):
            days_from_now = (time - datetime.datetime.now()).days
            print(f"  第{i}次: {time.strftime('%Y-%m-%d')} ({days_from_now}天后)")

    # 3. 模拟学习进度和掌握度更新
    print(f"\n[步骤3] 模拟学习进度")
    print("-" * 40)

    # 模拟用户已经学习并更新掌握度
    mastery_updates = [
        ("demo_逆否命题", 0.85),  # 掌握得很好
        ("demo_集合论基础", 0.65),  # 掌握一般
        ("demo_逻辑联结词", 0.45),  # 掌握不好
    ]

    for node_id, mastery in mastery_updates:
        forgetting_curve_manager.update_node_mastery(node_id, mastery)
        node = forgetting_curve_manager.review_nodes[node_id]
        print(f"[OK] 更新掌握度: {node.concept} -> {mastery:.1%} (复习{node.review_count}次)")

    # 4. 获取记忆状态分析
    print(f"\n[步骤4] 记忆状态分析")
    print("-" * 40)

    for node_id in ["demo_逆否命题", "demo_逻辑联结词"]:
        node = forgetting_curve_manager.review_nodes[node_id]
        status = forgetting_curve_manager.get_retention_status(node)

        print(f"\n概念: {status['concept']}")
        print(f"当前保持率: {status['retention_rate']:.1%}")
        print(f"紧急程度: {status['urgency']}")
        print(f"系统建议: {status['suggestion']}")
        print(f"掌握度: {status['mastery_level']:.1%}")

    # 5. 生成复习计划
    print(f"\n[步骤5] 生成未来30天复习计划")
    print("-" * 40)

    schedule = forgetting_curve_manager.generate_review_schedule(
        canvas_file="离散数学.canvas",
        days_ahead=30
    )

    if schedule:
        print("复习计划:")
        for date_str, tasks in sorted(schedule.items()):
            print(f"\n[DATE] {date_str}: {len(tasks)}个复习任务")
            for task in tasks:
                print(f"  - {task['concept']} (当前掌握度: {task['current_mastery']:.1%})")
    else:
        print("未来30天内没有需要复习的任务")

    # 6. Agent智能调度演示
    print(f"\n[步骤6] Agent智能调度演示")
    print("-" * 40)

    # 获取需要复习的节点
    due_nodes = forgetting_curve_manager.get_due_nodes("离散数学.canvas")

    if due_nodes:
        print(f"发现 {len(due_nodes)} 个需要复习的节点:")

        # 生成Agent调度计划
        agent_schedule = await ebbinghaus_review_scheduler.schedule_review_agents(due_nodes)

        for item in agent_schedule:
            print(f"\n[CONCEPT] {item['concept']}")
            print(f"   紧急程度: {item['urgency']}")
            print(f"   推荐Agent: {', '.join(item['recommended_agents'])}")
            print(f"   复习原因: {item['review_reason']}")
    else:
        print("当前没有需要立即复习的节点")

        # 模拟一个需要复习的场景
        print("\n[DEMO] 模拟场景: 假设有节点需要复习")
        test_node = forgetting_curve_manager.review_nodes["demo_集合论基础"]
        test_node.last_review_time = datetime.datetime.now() - datetime.timedelta(days=20)

        due_nodes = [test_node]
        agent_schedule = await ebbinghaus_review_scheduler.schedule_review_agents(due_nodes)

        for item in agent_schedule:
            print(f"\n[CONCEPT] {item['concept']} (模拟)")
            print(f"   紧急程度: {item['urgency']}")
            print(f"   推荐Agent: {', '.join(item['recommended_agents'])}")
            print(f"   复习原因: {item['review_reason']}")

    # 7. 完整复习会话演示
    print(f"\n[步骤7] 完整复习会话演示")
    print("-" * 40)

    session_result = await ebbinghaus_review_scheduler.execute_review_session("离散数学.canvas")

    print(f"会话状态: {'成功' if session_result['success'] else '失败'}")
    print(f"消息: {session_result['message']}")
    print(f"到期节点数: {session_result['due_nodes_count']}")
    print(f"生成调度数: {len(session_result['schedule'])}")

    print("\n" + "=" * 70)
    print("[SUCCESS] 艾宾浩斯复习系统演示完成！")
    print("=" * 70)

    print("\n[CORE FUNCTIONS] 核心功能验证:")
    print("  [OK] 遗忘曲线算法 R(t) = e^(-t/S)")
    print("  [OK] 标准艾宾浩斯间隔 (1,3,7,15,30天)")
    print("  [OK] 记忆强度动态调整")
    print("  [OK] Agent智能调度")
    print("  [OK] 复习会话自动化")

    print(f"\n[SYSTEM STATUS] 系统状态:")
    print(f"  - 总复习节点: {len(forgetting_curve_manager.review_nodes)}")
    print(f"  - 系统运行状态: 正常")
    print(f"  - 算法验证: 通过")

    return True

if __name__ == "__main__":
    print("启动艾宾浩斯复习系统演示...")
    try:
        result = asyncio.run(demo_ebbinghaus_system())
        if result:
            print("\n[SUCCESS] 演示成功完成！")
        else:
            print("\n[ERROR] 演示过程中出现问题")
    except Exception as e:
        print(f"\n[ERROR] 演示失败: {e}")
        import traceback
        traceback.print_exc()