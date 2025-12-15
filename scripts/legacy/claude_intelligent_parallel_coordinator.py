#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude智能并行协调器
=====================================================
这个脚本负责协调Python和Claude之间的交互
让/intelligent-parallel命令能真正调用Claude agents

工作流程：
1. Python扫描Canvas，提取黄色节点
2. 生成Claude调用指令
3. Claude执行Task tool调用真正的agents
4. Python接收结果并更新Canvas

Author: Canvas Learning System
Version: 1.0 - Real Implementation
Date: 2025-11-05
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Canvas颜色常量
COLOR_YELLOW = "6"  # 黄色：个人理解
COLOR_BLUE = "5"    # 蓝色：AI解释

class ClaudeCoordinator:
    """Claude智能并行协调器"""

    def __init__(self, canvas_path: str):
        self.canvas_path = Path(canvas_path)
        self.canvas_data = None
        self.yellow_nodes = []

    def load_and_scan(self) -> Dict[str, Any]:
        """加载Canvas并扫描黄色节点"""
        # 加载Canvas
        with open(self.canvas_path, 'r', encoding='utf-8') as f:
            self.canvas_data = json.load(f)

        # 扫描黄色节点
        for node in self.canvas_data.get('nodes', []):
            if node.get('color') == COLOR_YELLOW:
                content = ""
                if node.get('type') == 'text':
                    content = node.get('text', '')
                elif node.get('type') == 'file':
                    # 可以读取文件内容
                    pass

                if content:
                    self.yellow_nodes.append({
                        'id': node.get('id'),
                        'content': content,
                        'x': node.get('x', 0),
                        'y': node.get('y', 0),
                        'width': node.get('width', 300),
                        'height': node.get('height', 150)
                    })

        return {
            'canvas_path': str(self.canvas_path),
            'yellow_nodes': self.yellow_nodes,
            'total_nodes': len(self.yellow_nodes)
        }

    def generate_claude_instructions(self) -> str:
        """生成给Claude的执行指令"""
        if not self.yellow_nodes:
            return "没有发现黄色节点需要处理"

        instructions = f"""
# 🚀 智能并行处理任务

Canvas文件: {self.canvas_path.name}
黄色节点数: {len(self.yellow_nodes)}

## 需要执行的任务：

请使用Task tool并行调用以下agents处理黄色节点：

"""

        for i, node in enumerate(self.yellow_nodes, 1):
            content_preview = node['content'][:200] + "..." if len(node['content']) > 200 else node['content']

            # 智能选择agents
            agents = self.select_agents_for_node(node['content'])

            instructions += f"""
### 节点 {i}: {node['id']}

内容预览：
{content_preview}

**UltraThink深度分析模式** - 请并行调用以下agents：
"""

            for agent in agents:
                instructions += f"""
- **{agent['name']}** ({agent['emoji']}): {agent['purpose']}
  Task参数:
  - subagent_type: {agent['type']}
  - description: Process node {node['id']} with {agent['type']}
  - prompt: 分析以下内容并生成{agent['chinese_name']}：
    {node['content'][:500]}
"""

        instructions += """

## 执行要求：

1. **并行执行**：使用多个Task tool调用同时运行
2. **高质量输出**：每个agent生成1000+字的专业内容
3. **保存文档**：将生成的内容保存为.md文件
4. **更新Canvas**：添加蓝色AI节点并连接到黄色节点

## 预期输出格式：

每个agent完成后，创建文档：
- 文件名：{node_id}-{agent_type}-{timestamp}.md
- 内容：高质量的教育材料
- Canvas更新：添加蓝色节点和连接边

请立即开始执行UltraThink批处理！
"""

        return instructions

    def select_agents_for_node(self, content: str) -> List[Dict[str, str]]:
        """智能选择适合节点内容的agents"""
        content_lower = content.lower()
        agents = []

        # 基础agents - 总是包含
        agents.append({
            'name': 'memory-anchor',
            'type': 'memory-anchor',
            'emoji': '⚓',
            'chinese_name': '记忆锚点',
            'purpose': '生成生动类比和记忆法'
        })

        agents.append({
            'name': 'clarification-path',
            'type': 'clarification-path',
            'emoji': '🔍',
            'chinese_name': '澄清路径',
            'purpose': '系统化4步深度澄清'
        })

        # 条件agents
        if any(word in content_lower for word in ['对比', 'vs', '区别', '不同']):
            agents.append({
                'name': 'comparison-table',
                'type': 'comparison-table',
                'emoji': '📊',
                'chinese_name': '对比表格',
                'purpose': '结构化对比相似概念'
            })

        # 口语解释总是有用的
        agents.append({
            'name': 'oral-explanation',
            'type': 'oral-explanation',
            'emoji': '🗣️',
            'chinese_name': '口语解释',
            'purpose': '教授式亲切讲解'
        })

        # 如果内容包含例子或应用
        if any(word in content_lower for word in ['例如', '比如', '应用', 'example']):
            agents.append({
                'name': 'example-teaching',
                'type': 'example-teaching',
                'emoji': '📝',
                'chinese_name': '例题教学',
                'purpose': '完整的例题解析'
            })

        # 如果内容较复杂，添加四层次解释
        if len(content) > 500:
            agents.append({
                'name': 'four-level-explanation',
                'type': 'four-level-explanation',
                'emoji': '🎯',
                'chinese_name': '四层次解释',
                'purpose': '从新手到专家的渐进式解释'
            })

        return agents

    def create_execution_plan(self) -> Dict[str, Any]:
        """创建完整的执行计划"""
        node_data = self.load_and_scan()

        if not self.yellow_nodes:
            return {
                'status': 'no_nodes',
                'message': '没有发现黄色节点需要处理'
            }

        plan = {
            'status': 'ready',
            'canvas_file': str(self.canvas_path),
            'timestamp': datetime.now().isoformat(),
            'nodes': [],
            'total_agents': 0,
            'estimated_time': '5-10分钟'
        }

        for node in self.yellow_nodes:
            agents = self.select_agents_for_node(node['content'])
            plan['nodes'].append({
                'id': node['id'],
                'content_preview': node['content'][:100] + '...',
                'agents': [a['name'] for a in agents],
                'agent_count': len(agents)
            })
            plan['total_agents'] += len(agents)

        plan['instructions'] = self.generate_claude_instructions()

        return plan


def main():
    """主函数 - 生成Claude执行指令"""
    if len(sys.argv) < 2:
        print("用法: python claude_intelligent_parallel_coordinator.py <canvas_path>")
        sys.exit(1)

    canvas_path = sys.argv[1]

    print("=" * 70)
    print("🤖 Claude智能并行协调器")
    print("=" * 70)
    print()

    coordinator = ClaudeCoordinator(canvas_path)
    plan = coordinator.create_execution_plan()

    if plan['status'] == 'no_nodes':
        print(plan['message'])
        return

    # 输出执行计划
    print(f"📋 执行计划")
    print(f"Canvas文件: {Path(canvas_path).name}")
    print(f"黄色节点数: {len(plan['nodes'])}")
    print(f"总Agent调用数: {plan['total_agents']}")
    print(f"预计时间: {plan['estimated_time']}")
    print()

    print("📝 节点分析：")
    for i, node in enumerate(plan['nodes'], 1):
        print(f"\n{i}. 节点 {node['id']}")
        print(f"   内容: {node['content_preview']}")
        print(f"   分配Agents: {', '.join(node['agents'])} ({node['agent_count']}个)")

    print("\n" + "=" * 70)
    print("🚀 Claude执行指令")
    print("=" * 70)
    print(plan['instructions'])

    # 保存执行计划供Claude使用
    plan_file = Path(f"ultrathink_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(plan_file, 'w', encoding='utf-8') as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print(f"✅ 执行计划已保存: {plan_file}")
    print("\n请在Claude中使用Task tool执行以上指令！")
    print("=" * 70)


if __name__ == "__main__":
    main()