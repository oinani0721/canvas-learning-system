#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UltraThink执行计划处理器
========================
读取生成的执行计划，为Claude生成可执行的Task调用指令

这个脚本在Claude端执行，读取计划文件并生成Task调用
"""

import json
from pathlib import Path
from datetime import datetime

def read_latest_plan():
    """读取最新的执行计划"""
    # 查找所有计划文件
    plan_files = list(Path(".").glob("ultrathink_plan_*.json"))

    if not plan_files:
        print("❌ 没有找到执行计划文件")
        return None

    # 获取最新的计划文件
    latest_plan = max(plan_files, key=lambda p: p.stat().st_mtime)

    with open(latest_plan, 'r', encoding='utf-8') as f:
        plan = json.load(f)

    print(f"✅ 读取执行计划: {latest_plan}")
    return plan


def generate_task_calls(plan):
    """生成Claude Task调用代码"""
    if not plan or plan['status'] != 'ready':
        return None

    print("\n" + "=" * 70)
    print("📋 执行计划摘要")
    print("=" * 70)
    print(f"Canvas文件: {Path(plan['canvas_file']).name}")
    print(f"节点数: {len(plan['nodes'])}")
    print(f"总Agent调用: {plan['total_agents']}")
    print()

    # 生成每个节点的Task调用
    task_calls = []

    for node_info in plan['nodes']:
        node_id = node_info['id']
        agents = node_info['agents']

        print(f"🔹 节点 {node_id}:")
        print(f"   Agents: {', '.join(agents)}")

        for agent in agents:
            task_call = {
                'node_id': node_id,
                'agent': agent,
                'ready': True
            }
            task_calls.append(task_call)

    return task_calls


def save_results(node_id, agent_name, content):
    """保存Agent生成的结果"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{node_id}-{agent_name}-{timestamp}.md"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ 已保存: {filename}")
    return filename


def main():
    """主函数"""
    print("=" * 70)
    print("🚀 UltraThink执行计划处理器")
    print("=" * 70)
    print()

    # 读取计划
    plan = read_latest_plan()
    if not plan:
        return

    # 生成Task调用
    task_calls = generate_task_calls(plan)

    if not task_calls:
        print("❌ 无法生成Task调用")
        return

    print("\n" + "=" * 70)
    print("✅ 准备就绪")
    print("=" * 70)
    print(f"即将执行 {len(task_calls)} 个Agent调用")
    print()
    print("请在Claude对话中：")
    print("1. 使用Task tool调用各个agents")
    print("2. 每个agent生成1000+字的内容")
    print("3. 保存结果并更新Canvas")
    print()

    # 输出第一个示例调用
    if task_calls:
        first = task_calls[0]
        print("示例Task调用:")
        print(f"""
Task(
    description="Process {first['node_id']} with {first['agent']}",
    subagent_type="{first['agent']}",
    prompt="分析节点内容并生成专业解释..."
)
""")


if __name__ == "__main__":
    main()