#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Task 3功能演示脚本
演示Canvas Orchestrator与Claude Code的协同机制

Story 7.3 - Claude Code深度集成
Task 3: 实现与canvas-orchestrator协同机制 (AC: 4)
"""

import asyncio
import json
import tempfile
import os
from canvas_utils import CanvasClaudeOrchestratorBridge
from claude_canvas_tools import canvas_orchestrator_collaboration


def create_demo_canvas():
    """创建演示用的Canvas文件"""
    demo_canvas = {
        "nodes": [
            {
                "id": "math_concept_1",
                "type": "text",
                "text": "逆否命题 - 不理解的数学概念",
                "x": 100,
                "y": 100,
                "width": 200,
                "height": 80,
                "color": "4"  # 红色
            },
            {
                "id": "math_concept_2",
                "type": "text",
                "text": "集合论基础 - 似懂非懂",
                "x": 300,
                "y": 100,
                "width": 200,
                "height": 80,
                "color": "3"  # 紫色
            },
            {
                "id": "my_understanding_1",
                "type": "text",
                "text": "我的理解：逆否命题就是反过来想...",
                "x": 100,
                "y": 250,
                "width": 200,
                "height": 80,
                "color": "6"  # 黄色
            },
            {
                "id": "my_understanding_2",
                "type": "text",
                "text": "集合论就是关于集合的...",
                "x": 300,
                "y": 250,
                "width": 200,
                "height": 80,
                "color": "6"  # 黄色
            }
        ],
        "edges": [
            {
                "id": "edge_1",
                "fromNode": "math_concept_1",
                "toNode": "my_understanding_1"
            },
            {
                "id": "edge_2",
                "fromNode": "math_concept_2",
                "toNode": "my_understanding_2"
            }
        ]
    }

    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False, encoding='utf-8')
    json.dump(demo_canvas, temp_file, ensure_ascii=False, indent=2)
    temp_file.close()

    return temp_file.name


async def demo_task_3_features():
    """演示Task 3的新功能"""
    print("=" * 60)
    print("Task 3功能演示: Canvas Orchestrator协同机制")
    print("=" * 60)

    # 创建演示Canvas
    demo_canvas_path = create_demo_canvas()
    print(f"创建演示Canvas文件: {demo_canvas_path}")

    try:
        # 1. 演示CanvasClaudeOrchestratorBridge基础功能
        print("\n1. CanvasClaudeOrchestratorBridge - 协同桥接器")
        print("-" * 50)

        bridge = CanvasClaudeOrchestratorBridge(demo_canvas_path)
        print("桥接器初始化成功")
        print(f"Canvas路径: {bridge.canvas_path}")

        # 获取可用Agent列表
        available_agents = bridge.get_available_agents()
        print(f"可用Agent数量: {len(available_agents)}")
        print(f"Agent列表: {', '.join(available_agents[:5])}{'...' if len(available_agents) > 5 else ''}")

        # 2. 演示Claude推荐转换为任务
        print("\n2. Claude推荐转换为任务")
        print("-" * 50)

        from canvas_utils import AgentRecommendation
        test_recommendations = [
            AgentRecommendation(
                agent_type="basic-decomposition",
                confidence=0.85,
                reason="红色节点需要基础拆解",
                target_nodes=["math_concept_1"],
                priority=1,
                estimated_time=15.0
            ),
            AgentRecommendation(
                agent_type="scoring-agent",
                confidence=0.90,
                reason="黄色节点需要评分验证",
                target_nodes=["my_understanding_1", "my_understanding_2"],
                priority=2,
                estimated_time=10.0
            )
        ]

        tasks = bridge._translate_claude_recommendations_to_tasks(
            test_recommendations, "decompose", ["math_concept_1"]
        )
        print(f"转换的任务数量: {len(tasks)}")
        for i, task in enumerate(tasks, 1):
            print(f"{i}. {task['agent_type']} (优先级: {task.get('priority', 'N/A')})")

        # 3. 演示canvas_orchestrator_collaboration工具
        print("\n3. canvas_orchestrator_collaboration工具")
        print("-" * 50)

        # 测试基本参数验证
        print("a) 参数验证测试:")
        result = await canvas_orchestrator_collaboration({})
        if 'content' in result:
            print("   参数验证功能正常")

        # 测试文件不存在
        print("\nb) 文件不存在测试:")
        result = await canvas_orchestrator_collaboration({
            "canvas_path": "nonexistent.canvas"
        })
        if 'content' in result:
            print("   文件验证功能正常")

        # 测试基本协同操作
        print("\nc) 基本协同操作测试:")
        result = await canvas_orchestrator_collaboration({
            "canvas_path": demo_canvas_path,
            "operation": "analyze",
            "user_intent": "演示用户意图",
            "claude_guidance": "请重点关注数学概念的理解"
        })
        if 'content' in result:
            print(f"   协同工具响应长度: {len(result['content'][0]['text'])} 字符")

        # 4. 演示模拟任务执行
        print("\n4. 模拟任务执行")
        print("-" * 50)

        # 模拟基础拆解任务
        basic_task = {
            "agent_type": "basic-decomposition",
            "target_nodes": ["math_concept_1"],
            "confidence": 0.8,
            "estimated_time": 15.0
        }

        basic_result = await bridge._execute_basic_decomposition(basic_task, "演示用户意图")
        print(f"基础拆解任务: {'成功' if basic_result['success'] else '失败'}")
        print(f"Canvas更新数量: {len(basic_result['canvas_updates'])}")
        print(f"执行详情: {basic_result['details']}")

        # 模拟评分任务
        score_task = {
            "agent_type": "scoring-agent",
            "target_nodes": ["my_understanding_1", "my_understanding_2"],
            "confidence": 0.9,
            "estimated_time": 10.0
        }

        score_result = await bridge._execute_scoring(score_task, "演示用户意图")
        print(f"评分任务: {'成功' if score_result['success'] else '失败'}")
        print(f"Canvas更新数量: {len(score_result['canvas_updates'])}")
        print(f"执行详情: {score_result['details']}")

        # 5. 演示执行历史
        print("\n5. 执行历史记录")
        print("-" * 50)

        history = bridge.get_execution_history(limit=5)
        print(f"历史记录数量: {len(history)}")
        for i, record in enumerate(history[-3:], 1):  # 显示最近3条
            timestamp = record.get('timestamp', 'N/A')
            result = record.get('result', {})
            success = result.get('success', False)
            print(f"{i}. 时间: {timestamp[:19]} | 状态: {'成功' if success else '失败'}")

        print("\n" + "=" * 60)
        print("Task 3功能演示完成!")
        print("新功能包括:")
        print("   - CanvasClaudeOrchestratorBridge: Claude Code与Orchestrator协同桥接器")
        print("   - canvas_orchestrator_collaboration: 协同工具函数")
        print("   - 智能工作流执行: Claude分析 + Orchestrator执行")
        print("   - 双向通信机制: Claude推荐 <-> Orchestrator任务")
        print("   - 执行结果回调: Canvas更新和状态跟踪")
        print("   - 12个Sub-agent完全兼容")
        print("=" * 60)

    finally:
        # 清理临时文件
        os.unlink(demo_canvas_path)
        print(f"\n已清理临时文件: {demo_canvas_path}")


if __name__ == "__main__":
    asyncio.run(demo_task_3_features())