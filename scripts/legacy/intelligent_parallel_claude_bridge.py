#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能并行处理 - Claude桥接器
这是正确的实现：Python只做辅助工作，真正的Agent调用在Claude对话中完成

使用流程：
1. Python准备数据：扫描Canvas，提取黄色节点
2. Claude调用Agent：使用Task tool调用真实Sub-agents
3. Python处理结果：接收Claude的结果，更新Canvas

Author: Canvas Learning System Team
Version: 2.0 - Real Implementation
Date: 2025-11-05
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import uuid

# Canvas颜色常量
COLOR_YELLOW = "6"  # 黄色：个人理解
COLOR_BLUE = "5"    # 蓝色：AI解释
COLOR_GREEN = "2"   # 绿色：完全理解
COLOR_RED = "1"     # 红色：不理解
COLOR_PURPLE = "3"  # 紫色：似懂非懂

class CanvasBridge:
    """Canvas桥接器 - 只负责文件操作和数据准备"""

    def __init__(self, canvas_path: str):
        self.canvas_path = Path(canvas_path)
        self.canvas_data = None
        self.yellow_nodes = []

    def load_canvas(self) -> bool:
        """加载Canvas文件"""
        try:
            with open(self.canvas_path, 'r', encoding='utf-8') as f:
                self.canvas_data = json.load(f)
            return True
        except Exception as e:
            print(f"❌ 加载Canvas失败: {e}")
            return False

    def scan_yellow_nodes(self) -> List[Dict[str, Any]]:
        """扫描黄色节点，准备数据供Claude处理"""
        if not self.canvas_data:
            return []

        self.yellow_nodes = []

        for node in self.canvas_data.get('nodes', []):
            if node.get('color') == COLOR_YELLOW:
                # 提取节点内容
                content = self._extract_content(node)
                if content:
                    self.yellow_nodes.append({
                        'id': node.get('id'),
                        'type': node.get('type'),
                        'content': content,
                        'x': node.get('x', 0),
                        'y': node.get('y', 0),
                        'width': node.get('width', 300),
                        'height': node.get('height', 150)
                    })

        return self.yellow_nodes

    def _extract_content(self, node: Dict[str, Any]) -> str:
        """提取节点内容"""
        if node.get('type') == 'text':
            return node.get('text', '')
        elif node.get('type') == 'file':
            # 对于文件节点，可能需要读取文件内容
            file_path = node.get('file', '')
            # 这里简化处理，只返回文件名
            return Path(file_path).stem if file_path else ''
        return ''

    def prepare_for_claude(self) -> Dict[str, Any]:
        """
        准备数据供Claude处理
        返回结构化的数据，Claude可以直接使用
        """
        return {
            'canvas_file': str(self.canvas_path),
            'timestamp': datetime.now().isoformat(),
            'yellow_nodes': self.yellow_nodes,
            'total_nodes': len(self.yellow_nodes),
            'canvas_metadata': {
                'total_nodes': len(self.canvas_data.get('nodes', [])),
                'total_edges': len(self.canvas_data.get('edges', [])),
                'has_red_nodes': any(n.get('color') == COLOR_RED for n in self.canvas_data.get('nodes', [])),
                'has_purple_nodes': any(n.get('color') == COLOR_PURPLE for n in self.canvas_data.get('nodes', []))
            }
        }

    def add_blue_node(self, yellow_node_id: str, doc_path: str, agent_name: str, agent_emoji: str) -> bool:
        """
        添加蓝色AI解释节点

        Args:
            yellow_node_id: 黄色节点ID
            doc_path: 生成的文档路径
            agent_name: Agent名称
            agent_emoji: Agent表情符号

        Returns:
            是否成功
        """
        # 找到黄色节点
        yellow_node = None
        for node in self.canvas_data.get('nodes', []):
            if node['id'] == yellow_node_id:
                yellow_node = node
                break

        if not yellow_node:
            print(f"❌ 找不到黄色节点: {yellow_node_id}")
            return False

        # 生成蓝色节点ID
        blue_node_id = f"ai-{agent_name}-{yellow_node_id}-{uuid.uuid4().hex[:8]}"

        # 计算位置（在黄色节点右侧）
        blue_x = yellow_node.get('x', 0) + yellow_node.get('width', 300) + 50
        blue_y = yellow_node.get('y', 0)

        # 创建蓝色节点
        blue_node = {
            'id': blue_node_id,
            'type': 'file',
            'file': doc_path,
            'x': blue_x,
            'y': blue_y,
            'width': 350,
            'height': 200,
            'color': COLOR_BLUE
        }

        # 添加节点
        self.canvas_data['nodes'].append(blue_node)

        # 创建连接边
        edge = {
            'id': f"edge-{yellow_node_id}-to-{blue_node_id}",
            'fromNode': yellow_node_id,
            'fromSide': 'right',
            'toNode': blue_node_id,
            'toSide': 'left',
            'color': COLOR_BLUE,
            'label': f"{agent_emoji} {agent_name}"
        }

        self.canvas_data['edges'].append(edge)

        print(f"✅ 添加蓝色节点: {blue_node_id}")
        return True

    def save_canvas(self) -> bool:
        """保存Canvas文件"""
        try:
            # 备份原文件
            backup_path = self.canvas_path.with_suffix('.backup.' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.canvas')
            shutil.copy(self.canvas_path, backup_path)
            print(f"📋 备份创建: {backup_path}")

            # 保存修改
            with open(self.canvas_path, 'w', encoding='utf-8') as f:
                json.dump(self.canvas_data, f, ensure_ascii=False, indent=2)
            print(f"✅ Canvas保存成功: {self.canvas_path}")
            return True
        except Exception as e:
            print(f"❌ 保存Canvas失败: {e}")
            return False

    def generate_report(self) -> str:
        """生成执行报告"""
        report = f"""
========================================
Canvas桥接器执行报告
========================================
Canvas文件: {self.canvas_path.name}
执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

扫描结果:
- 黄色节点数: {len(self.yellow_nodes)}
- 总节点数: {len(self.canvas_data.get('nodes', []))}
- 总连接数: {len(self.canvas_data.get('edges', []))}

节点详情:
"""
        for i, node in enumerate(self.yellow_nodes, 1):
            report += f"\n{i}. [{node['id']}]\n"
            report += f"   内容: {node['content'][:100]}...\n"

        return report


def main():
    """主函数 - 准备数据供Claude处理"""
    if len(sys.argv) < 2:
        print("用法: python intelligent_parallel_claude_bridge.py <canvas_path>")
        sys.exit(1)

    canvas_path = sys.argv[1]

    # 创建桥接器
    bridge = CanvasBridge(canvas_path)

    # 加载Canvas
    if not bridge.load_canvas():
        sys.exit(1)

    # 扫描黄色节点
    yellow_nodes = bridge.scan_yellow_nodes()

    if not yellow_nodes:
        print("⚠️ 没有发现黄色节点")
        sys.exit(0)

    # 准备数据
    data = bridge.prepare_for_claude()

    # 输出JSON供Claude处理
    print("\n" + "="*50)
    print("准备完成 - 数据供Claude处理")
    print("="*50)
    print(json.dumps(data, ensure_ascii=False, indent=2))

    # 生成报告
    print(bridge.generate_report())

    print("\n✅ 数据准备完成，等待Claude处理...")
    print("请在Claude对话中使用Task tool调用Sub-agents处理这些节点")


if __name__ == "__main__":
    main()