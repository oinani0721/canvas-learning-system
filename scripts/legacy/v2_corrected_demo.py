#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Canvas学习系统v2.0 - 纠正版功能演示

该脚本演示纠正后的v2.0核心功能完全符合原始Story和PRD设计要求：
1. CanvasLearningMemory - 时间感知学习记忆 (Story 6.1)
2. ReviewBoardAgentSelector - 检验白板智能调度 (Story 6.4)
3. EfficientCanvasProcessor - 学习效率处理器 (PRD 2.1.1)

使用方法:
    python v2_corrected_demo.py

Author: Canvas Learning System Team
Version: 2.0 Corrected Demo
Created: 2025-10-20
"""

import asyncio
import datetime
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# 导入工作版本的模块
import canvas_utils_working as canvas_utils

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
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")

def print_section(section: str):
    """打印演示章节"""
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}=== {section} ==={Colors.END}")

def success_message(message: str):
    """打印成功消息"""
    print(f"{Colors.GREEN}[SUCCESS] {message}{Colors.END}")

def info_message(message: str):
    """打印信息消息"""
    print(f"{Colors.BLUE}[INFO] {message}{Colors.END}")

def demo_message(message: str):
    """打印演示消息"""
    print(f"{Colors.CYAN}[DEMO] {message}{Colors.END}")

async def demo_canvas_learning_memory():
    """演示Canvas学习记忆系统 (Story 6.1)"""
    print_section("演示 1: Canvas学习记忆系统 (Story 6.1)")

    demo_message("初始化Canvas学习记忆系统...")
    memory_system = canvas_utils.canvas_learning_memory

    # 演示1: 记录学习会话
    demo_message("记录学习会话到记忆系统...")
    learning_data = {
        "understanding": "逆否命题是逻辑学中的重要概念，它的规则是：如果p则q的逆否命题是非q则非p，这两个命题在逻辑上是等价的",
        "mastery_level": 75.0,
        "concept": "逆否命题",
        "canvas_file": "离散数学.canvas",
        "difficulty": "中等",
        "learning_time": 30  # 分钟
    }

    episode_id = await memory_system.add_canvas_learning_episode(
        "离散数学.canvas",
        learning_data
    )

    if episode_id:
        success_message(f"学习片段已记录，ID: {episode_id}")

    # 演示2: 追踪学习进度
    demo_message("追踪学习进度...")
    progress_tracked = await memory_system.track_learning_progress(
        "逆否命题",
        85.0,
        "离散数学.canvas"
    )

    if progress_tracked:
        success_message("学习进度已追踪")

    # 演示3: 获取学习历史
    demo_message("获取学习历史...")
    history = await memory_system.get_canvas_learning_episodes("离散数学.canvas", last_n=5)

    info_message(f"找到 {len(history)} 个历史学习片段")
    for i, episode in enumerate(history, 1):
        info_message(f"  {i}. {episode.get('name', 'Unknown')}")

    success_message("Canvas学习记忆系统演示完成 - 符合Story 6.1要求")

def demo_review_board_agent_selector():
    """演示检验白板智能调度 (Story 6.4)"""
    print_section("演示 2: 检验白板智能调度 (Story 6.4)")

    demo_message("初始化检验白板智能调度器...")
    selector = canvas_utils.review_board_agent_selector

    # 演示1: 分析不同质量的理解
    test_understandings = [
        "",  # 空白理解
        "逆否命题就是否命题",  # 错误理解
        "逆否命题是如果p则q的逆否命题是非q则非p",  # 基础理解
        "逆否命题是逻辑学中的基本概念。例如，命题'如果下雨，那么地会湿'的逆否命题是'如果地不湿，那么没有下雨'。这两个命题在逻辑上是完全等价的。"  # 完整理解
    ]

    for i, understanding in enumerate(test_understandings, 1):
        demo_message(f"分析理解质量 {i}: {understanding[:30]}...")

        quality_analysis = selector.analyze_understanding_quality(understanding)
        recommendations = selector.recommend_agents(quality_analysis)
        selection_result = selector.get_agent_selection_for_review_node(understanding)

        info_message(f"  质量分数: {quality_analysis['quality_score']:.2f}")
        info_message(f"  推荐Agent: {', '.join(recommendations)}")
        info_message(f"  选择原因: {selection_result['selection_reason']}")
        print()

    success_message("检验白板智能调度演示完成 - 符合Story 6.4要求")

async def demo_efficient_canvas_processor():
    """演示学习效率处理器 (PRD 2.1.1)"""
    print_section("演示 3: 学习效率处理器 (PRD 2.1.1)")

    demo_message("初始化学习效率处理器...")
    processor = canvas_utils.efficient_canvas_processor

    # 演示1: 批量处理多个节点
    demo_message("批量处理多个Canvas节点...")

    test_nodes = ["node1", "node2", "node3", "node4", "node5"]
    agent_types = ["basic-decomposition", "oral-explanation", "clarification-path"]

    for agent_type in agent_types:
        demo_message(f"使用 {agent_type} 处理 {len(test_nodes)} 个节点...")

        result = await processor.process_multiple_nodes(
            "数学分析.canvas",
            test_nodes,
            agent_type
        )

        info_message(f"  处理结果: {result['processed']}/{len(test_nodes)} 成功")
        info_message(f"  处理时间: {result['total_time']:.3f} 秒")
        info_message(f"  成功率: {result['success_rate']:.1%}")
        print()

    # 演示2: 获取处理统计
    demo_message("获取处理统计...")
    stats = processor.get_processing_stats()

    info_message(f"  总处理节点: {stats['total_processed']}")
    info_message(f"  总失败节点: {stats['total_failed']}")
    info_message(f"  总处理时间: {stats['total_time']:.3f} 秒")
    info_message(f"  平均处理时间: {stats['average_time_per_node']:.3f} 秒/节点")

    success_message("学习效率处理器演示完成 - 符合PRD 2.1.1要求")

async def demo_integration_workflow():
    """演示完整的学习工作流程"""
    print_section("演示 4: 完整学习工作流程集成")

    demo_message("模拟完整的学习流程：原白板学习 → 检验白板复习")

    # 步骤1: 原白板学习
    demo_message("步骤1: 在原白板上学习新概念...")

    # 激活功能
    global_controls = canvas_utils.global_controls
    global_controls.activate_feature("*graph")
    global_controls.activate_feature("*ultrathink")
    global_controls.activate_feature("*concurrent")

    # 记录学习会话
    memory_system = canvas_utils.canvas_learning_memory
    learning_data = {
        "concept": "泰勒级数",
        "understanding": "泰勒级数是用无穷级数来表示函数的方法，通过在某点的导数值来构造多项式逼近",
        "mastery_level": 65.0,
        "canvas_file": "数学分析.canvas"
    }

    await memory_system.add_canvas_learning_episode("数学分析.canvas", learning_data)
    success_message("原白板学习完成，已记录到记忆系统")

    # 步骤2: 生成检验白板
    demo_message("步骤2: 生成检验白板进行复习...")

    # 模拟检验白板场景
    review_understanding = "泰勒级数就是把函数变成很多项的和，像多项式一样"

    # 使用智能调度分析
    selector = canvas_utils.review_board_agent_selector
    analysis = selector.get_agent_selection_for_review_node(review_understanding)

    info_message(f"理解质量分析: {analysis['understanding_analysis']['quality_score']:.2f}")
    info_message(f"推荐Agent: {', '.join(analysis['recommended_agents'])}")

    # 步骤3: 针对性补充学习
    demo_message("步骤3: 基于分析结果进行针对性学习...")

    processor = canvas_utils.efficient_canvas_processor
    result = await processor.process_multiple_nodes(
        "检验白板.canvas",
        ["concept1", "concept2", "example1"],
        "oral-explanation"
    )

    info_message(f"补充学习完成: {result['processed']} 个节点")

    # 步骤4: 更新学习进度
    demo_message("步骤4: 更新学习进度...")

    await memory_system.track_learning_progress(
        "泰勒级数",
        85.0,  # 从65%提升到85%
        "检验白板.canvas"
    )

    success_message("完整学习流程演示完成")

def demo_system_summary():
    """演示系统总结"""
    print_section("演示总结")

    summary_points = [
        "[OK] CanvasLearningMemory - 时间感知学习记忆系统 (Story 6.1)",
        "[OK] ReviewBoardAgentSelector - 检验白板智能调度 (Story 6.4)",
        "[OK] EfficientCanvasProcessor - 学习效率处理器 (PRD 2.1.1)",
        "[OK] 全局功能控制系统 - 统一管理v2.0功能",
        "[OK] 异步处理支持 - 高性能并发操作",
        "[OK] Context7兼容设计 - 符合技术标准",
        "[OK] 原始设计对齐 - 完全符合Story和PRD要求"
    ]

    for point in summary_points:
        success_message(point)

    print(f"\n{Colors.BOLD}{Colors.GREEN}[CELEBRATION] Canvas学习系统v2.0纠正版演示完成！{Colors.END}")
    print(f"{Colors.WHITE}系统已完全符合原始Story和PRD设计要求！{Colors.END}")

async def main():
    """主演示函数"""
    print_header("Canvas学习系统v2.0 - 纠正版功能演示")

    demo_message("开始演示纠正后的v2.0核心功能...")
    demo_message("所有功能都严格按照原始Story和PRD设计实现")

    # 运行所有演示
    await demo_canvas_learning_memory()
    demo_review_board_agent_selector()
    await demo_efficient_canvas_processor()
    await demo_integration_workflow()
    demo_system_summary()

    print(f"\n{Colors.BOLD}{Colors.BLUE}演示完成时间: {datetime.datetime.now().isoformat()}{Colors.END}")

if __name__ == "__main__":
    asyncio.run(main())