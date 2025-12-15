#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Canvas布局学习系统

该系统记录用户的布局调整，学习最优布局模式，并自动生成改进的布局。
结合Context7验证的MCP记忆服务技术。

使用方法:
    python canvas_layout_learner.py --record canvas_file before.json after.json
    python canvas_layout_learner.py --learn canvas_file
    python canvas_layout_learner.py --generate canvas_file content.json

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-10-20
"""

import json
import argparse
import asyncio
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import hashlib

# 尝试导入MCP记忆服务
try:
    from mcp_graphiti_memory import add_memory, search_memories
    MEMORY_SERVICE_AVAILABLE = True
except ImportError:
    print("[INFO] MCP记忆服务不可用，使用本地存储")
    MEMORY_SERVICE_AVAILABLE = False

@dataclass
class LayoutAdjustment:
    """布局调整记录"""
    canvas_file: str
    timestamp: datetime.datetime
    before_layout: Dict[str, Any]
    after_layout: Dict[str, Any]
    adjustment_reason: str
    user_feedback_score: Optional[float] = None  # 1-10分

@dataclass
class LayoutPattern:
    """布局模式"""
    pattern_type: str  # "hierarchical", "radial", "grid", "flow"
    node_spacing: Dict[str, float]  # 不同类型节点的间距
    alignment_rules: Dict[str, str]  # 对齐规则
    connection_style: str  # "straight", "curved", "orthogonal"
    color_grouping: bool  # 是否按颜色分组
    learned_from_examples: int  # 学习样本数量

class CanvasLayoutLearner:
    """Canvas布局学习器"""

    def __init__(self):
        """初始化布局学习器"""
        self.adjustments_history: List[LayoutAdjustment] = []
        self.learned_patterns: Dict[str, LayoutPattern] = {}
        self.memory_available = MEMORY_SERVICE_AVAILABLE

        # 初始化基础布局模式
        self._initialize_base_patterns()

    def _initialize_base_patterns(self):
        """初始化基础布局模式"""
        self.learned_patterns = {
            "hierarchical": LayoutPattern(
                pattern_type="hierarchical",
                node_spacing={
                    "parent_child": {"x": 0, "y": 120},
                    "sibling": {"x": 220, "y": 0},
                    "cross_level": {"x": 300, "y": 80}
                },
                alignment_rules={
                    "parent": "center",
                    "children": "horizontal_center",
                    "same_level": "top_align"
                },
                connection_style="orthogonal",
                color_grouping=True,
                learned_from_examples=0
            ),
            "radial": LayoutPattern(
                pattern_type="radial",
                node_spacing={
                    "center_radius": 0,
                    "first_ring": 150,
                    "second_ring": 300,
                    "angle_step": 45
                },
                alignment_rules={
                    "center": "center",
                    "ring_nodes": "radial_align"
                },
                connection_style="straight",
                color_grouping=True,
                learned_from_examples=0
            ),
            "flow": LayoutPattern(
                pattern_type="flow",
                node_spacing={
                    "main_flow": {"x": 200, "y": 0},
                    "branch": {"x": 100, "y": 100},
                    "merge": {"x": 150, "y": -50}
                },
                alignment_rules={
                    "flow_direction": "left_to_right",
                    "branches": "vertical_center"
                },
                connection_style="curved",
                color_grouping=False,
                learned_from_examples=0
            )
        }

    async def record_layout_adjustment(
        self,
        canvas_file: str,
        before_layout: Dict[str, Any],
        after_layout: Dict[str, Any],
        adjustment_reason: str = "用户手动调整"
    ) -> bool:
        """记录布局调整"""
        try:
            adjustment = LayoutAdjustment(
                canvas_file=canvas_file,
                timestamp=datetime.datetime.now(),
                before_layout=before_layout,
                after_layout=after_layout,
                adjustment_reason=adjustment_reason
            )

            self.adjustments_history.append(adjustment)

            # 分析调整模式
            pattern_changes = self._analyze_adjustment_pattern(before_layout, after_layout)

            # 存储到记忆系统
            if self.memory_available:
                memory_content = f"""
Canvas布局调整记录:
文件: {canvas_file}
时间: {adjustment.timestamp.isoformat()}
调整原因: {adjustment_reason}
模式变化: {pattern_changes}

调整前布局:
节点数量: {len(before_layout.get('nodes', []))}
连接数量: {len(before_layout.get('edges', []))}

调整后布局:
节点数量: {len(after_layout.get('nodes', []))}
连接数量: {len(after_layout.get('edges', []))}
"""

                await add_memory(
                    key=f"layout_adjustment_{canvas_file}_{adjustment.timestamp.timestamp()}",
                    content=memory_content,
                    metadata={
                        "canvas_file": canvas_file,
                        "type": "layout_adjustment",
                        "pattern_changes": pattern_changes,
                        "timestamp": adjustment.timestamp.isoformat()
                    }
                )

            print(f"[SUCCESS] 布局调整已记录: {canvas_file}")
            return True

        except Exception as e:
            print(f"[ERROR] 记录布局调整失败: {e}")
            return False

    def _analyze_adjustment_pattern(self, before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
        """分析布局调整模式"""
        try:
            before_nodes = before.get('nodes', [])
            after_nodes = after.get('nodes', [])

            # 计算节点位置变化
            position_changes = []
            for after_node in after_nodes:
                node_id = after_node.get('id')
                before_node = next((n for n in before_nodes if n.get('id') == node_id), None)

                if before_node:
                    dx = after_node.get('x', 0) - before_node.get('x', 0)
                    dy = after_node.get('y', 0) - before_node.get('y', 0)

                    if abs(dx) > 5 or abs(dy) > 5:  # 忽略微小调整
                        position_changes.append({
                            'node_id': node_id,
                            'dx': dx,
                            'dy': dy,
                            'distance': (dx**2 + dy**2)**0.5
                        })

            # 分析布局模式
            pattern_analysis = {
                'total_adjustments': len(position_changes),
                'average_distance': sum(c['distance'] for c in position_changes) / len(position_changes) if position_changes else 0,
                'main_direction': self._calculate_main_direction(position_changes),
                'affected_colors': self._analyze_color_changes(before_nodes, after_nodes),
                'clustering_changes': self._analyze_clustering_changes(before_nodes, after_nodes)
            }

            return pattern_analysis

        except Exception as e:
            print(f"[ERROR] 分析布局模式失败: {e}")
            return {}

    def _calculate_main_direction(self, position_changes: List[Dict[str, Any]]) -> str:
        """计算主要调整方向"""
        if not position_changes:
            return "none"

        total_dx = sum(c['dx'] for c in position_changes)
        total_dy = sum(c['dy'] for c in position_changes)

        if abs(total_dx) > abs(total_dy):
            return "horizontal" if total_dx > 0 else "horizontal_left"
        else:
            return "vertical" if total_dy > 0 else "vertical_up"

    def _analyze_color_changes(self, before_nodes: List[Dict], after_nodes: List[Dict]) -> Dict[str, int]:
        """分析颜色节点调整"""
        color_changes = {}
        for after_node in after_nodes:
            node_id = after_node.get('id')
            before_node = next((n for n in before_nodes if n.get('id') == node_id), None)

            if before_node:
                color = after_node.get('color', 'unknown')
                color_changes[color] = color_changes.get(color, 0) + 1

        return color_changes

    def _analyze_clustering_changes(self, before_nodes: List[Dict], after_nodes: List[Dict]) -> Dict[str, Any]:
        """分析聚类变化"""
        # 计算节点的聚集程度
        def calculate_clustering(nodes):
            if len(nodes) < 2:
                return 0

            total_distance = 0
            count = 0
            for i, node1 in enumerate(nodes):
                for node2 in nodes[i+1:]:
                    dist = ((node1.get('x', 0) - node2.get('x', 0))**2 +
                           (node1.get('y', 0) - node2.get('y', 0))**2)**0.5
                    total_distance += dist
                    count += 1

            return total_distance / count if count > 0 else 0

        before_clustering = calculate_clustering(before_nodes)
        after_clustering = calculate_clustering(after_nodes)

        return {
            "before_avg_distance": before_clustering,
            "after_avg_distance": after_clustering,
            "clustering_change": after_clustering - before_clustering
        }

    async def learn_from_adjustments(self, canvas_file: str) -> Dict[str, Any]:
        """从历史调整中学习布局模式"""
        try:
            # 获取相关调整记录
            file_adjustments = [adj for adj in self.adjustments_history if adj.canvas_file == canvas_file]

            if not file_adjustments:
                print(f"[INFO] 没有找到 {canvas_file} 的调整记录")
                return {}

            # 分析共同模式
            common_patterns = self._extract_common_patterns(file_adjustments)

            # 更新布局模式
            updated_patterns = self._update_layout_patterns(common_patterns)

            # 存储学习结果
            if self.memory_available:
                learning_content = f"""
布局学习结果:
文件: {canvas_file}
学习样本数: {len(file_adjustments)}
发现模式: {common_patterns}
更新模式: {updated_patterns}
"""

                await add_memory(
                    key=f"layout_learning_{canvas_file}_{datetime.datetime.now().timestamp()}",
                    content=learning_content,
                    metadata={
                        "canvas_file": canvas_file,
                        "type": "layout_learning",
                        "sample_count": len(file_adjustments),
                        "patterns": common_patterns
                    }
                )

            print(f"[SUCCESS] 布局学习完成: {canvas_file}")
            return {
                "learned_patterns": common_patterns,
                "updated_patterns": updated_patterns,
                "sample_count": len(file_adjustments)
            }

        except Exception as e:
            print(f"[ERROR] 布局学习失败: {e}")
            return {}

    def _extract_common_patterns(self, adjustments: List[LayoutAdjustment]) -> Dict[str, Any]:
        """提取共同布局模式"""
        try:
            all_patterns = []
            for adj in adjustments:
                pattern = self._analyze_adjustment_pattern(adj.before_layout, adj.after_layout)
                all_patterns.append(pattern)

            if not all_patterns:
                return {}

            # 计算平均模式
            common_patterns = {
                "average_adjustments": sum(p.get('total_adjustments', 0) for p in all_patterns) / len(all_patterns),
                "average_distance": sum(p.get('average_distance', 0) for p in all_patterns) / len(all_patterns),
                "most_common_direction": self._most_common_direction([p.get('main_direction') for p in all_patterns]),
                "color_preferences": self._aggregate_color_preferences([p.get('affected_colors', {}) for p in all_patterns]),
                "clustering_tendency": self._calculate_clustering_tendency([p.get('clustering_changes', {}) for p in all_patterns])
            }

            return common_patterns

        except Exception as e:
            print(f"[ERROR] 提取共同模式失败: {e}")
            return {}

    def _most_common_direction(self, directions: List[str]) -> str:
        """获取最常见方向"""
        if not directions:
            return "none"

        direction_counts = {}
        for direction in directions:
            if direction:
                direction_counts[direction] = direction_counts.get(direction, 0) + 1

        return max(direction_counts.items(), key=lambda x: x[1])[0] if direction_counts else "none"

    def _aggregate_color_preferences(self, color_dicts: List[Dict[str, int]]) -> Dict[str, int]:
        """聚合颜色偏好"""
        aggregated = {}
        for color_dict in color_dicts:
            for color, count in color_dict.items():
                aggregated[color] = aggregated.get(color, 0) + count

        return aggregated

    def _calculate_clustering_tendency(self, clustering_changes: List[Dict[str, Any]]) -> str:
        """计算聚类倾向"""
        if not clustering_changes:
            return "neutral"

        avg_changes = sum(c.get('clustering_change', 0) for c in clustering_changes) / len(clustering_changes)

        if avg_changes > 10:
            return "spreading"
        elif avg_changes < -10:
            return "clustering"
        else:
            return "neutral"

    def _update_layout_patterns(self, common_patterns: Dict[str, Any]) -> Dict[str, LayoutPattern]:
        """基于学习结果更新布局模式"""
        try:
            # 根据学习结果调整现有模式
            updated_patterns = self.learned_patterns.copy()

            # 示例：如果用户倾向于让节点更聚集，调整间距
            clustering_tendency = common_patterns.get('clustering_tendency', 'neutral')
            if clustering_tendency == 'clustering':
                for pattern in updated_patterns.values():
                    for spacing_type in pattern.node_spacing:
                        if isinstance(pattern.node_spacing[spacing_type], dict):
                            for axis in pattern.node_spacing[spacing_type]:
                                if isinstance(pattern.node_spacing[spacing_type][axis], (int, float)):
                                    pattern.node_spacing[spacing_type][axis] *= 0.8  # 减少20%间距

            elif clustering_tendency == 'spreading':
                for pattern in updated_patterns.values():
                    for spacing_type in pattern.node_spacing:
                        if isinstance(pattern.node_spacing[spacing_type], dict):
                            for axis in pattern.node_spacing[spacing_type]:
                                if isinstance(pattern.node_spacing[spacing_type][axis], (int, float)):
                                    pattern.node_spacing[spacing_type][axis] *= 1.2  # 增加20%间距

            # 增加学习样本计数
            for pattern in updated_patterns.values():
                pattern.learned_from_examples += 1

            return updated_patterns

        except Exception as e:
            print(f"[ERROR] 更新布局模式失败: {e}")
            return self.learned_patterns

    async def generate_optimal_layout(
        self,
        canvas_content: Dict[str, Any],
        pattern_type: str = "hierarchical"
    ) -> Dict[str, Any]:
        """生成最优布局"""
        try:
            if pattern_type not in self.learned_patterns:
                pattern_type = "hierarchical"  # 默认模式

            pattern = self.learned_patterns[pattern_type]
            nodes = canvas_content.get('nodes', [])
            edges = canvas_content.get('edges', [])

            # 分析节点类型和关系
            node_analysis = self._analyze_nodes(nodes, edges)

            # 应用布局模式
            layout_result = self._apply_layout_pattern(nodes, edges, pattern, node_analysis)

            print(f"[SUCCESS] 生成最优布局: {pattern_type}")
            return layout_result

        except Exception as e:
            print(f"[ERROR] 生成布局失败: {e}")
            return canvas_content  # 返回原始内容

    def _analyze_nodes(self, nodes: List[Dict], edges: List[Dict]) -> Dict[str, Any]:
        """分析节点关系"""
        try:
            node_types = {}
            node_connections = {}

            # 分析节点类型（基于颜色和ID）
            for node in nodes:
                node_id = node.get('id')
                color = node.get('color', 'unknown')

                # 分类节点
                if 'problem' in node_id.lower() or color == '1':
                    node_type = 'problem'
                elif 'understanding' in node_id.lower() or color == '6':
                    node_type = 'understanding'
                elif 'example' in node_id.lower() or color == '5':
                    node_type = 'example'
                elif 'connection' in node_id.lower():
                    node_type = 'connection'
                else:
                    node_type = 'general'

                node_types[node_id] = node_type
                node_connections[node_id] = []

            # 分析连接关系
            for edge in edges:
                from_node = edge.get('fromNode')
                to_node = edge.get('toNode')

                if from_node in node_connections:
                    node_connections[from_node].append(to_node)
                if to_node in node_connections:
                    node_connections[to_node].append(from_node)

            return {
                'node_types': node_types,
                'node_connections': node_connections,
                'root_nodes': [node_id for node_id, connections in node_connections.items() if len(connections) > 0],
                'leaf_nodes': [node_id for node_id, connections in node_connections.items() if len(connections) <= 1]
            }

        except Exception as e:
            print(f"[ERROR] 节点分析失败: {e}")
            return {}

    def _apply_layout_pattern(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        pattern: LayoutPattern,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """应用布局模式"""
        try:
            layout_nodes = nodes.copy()
            node_types = analysis.get('node_types', {})
            node_connections = analysis.get('node_connections', {})

            if pattern.pattern_type == "hierarchical":
                layout_nodes = self._apply_hierarchical_layout(layout_nodes, node_types, node_connections, pattern)
            elif pattern.pattern_type == "radial":
                layout_nodes = self._apply_radial_layout(layout_nodes, node_types, node_connections, pattern)
            elif pattern.pattern_type == "flow":
                layout_nodes = self._apply_flow_layout(layout_nodes, node_types, node_connections, pattern)

            return {
                "nodes": layout_nodes,
                "edges": edges,
                "pattern_used": pattern.pattern_type,
                "pattern_confidence": min(pattern.learned_from_examples / 10, 1.0)
            }

        except Exception as e:
            print(f"[ERROR] 应用布局模式失败: {e}")
            return {"nodes": nodes, "edges": edges}

    def _apply_hierarchical_layout(
        self,
        nodes: List[Dict],
        node_types: Dict[str, str],
        node_connections: Dict[str, List[str]],
        pattern: LayoutPattern
    ) -> List[Dict]:
        """应用层次布局"""
        try:
            # 找到根节点
            root_nodes = [node_id for node_id, node_type in node_types.items() if node_type == 'problem']

            if not root_nodes:
                root_nodes = list(node_types.keys())[:1]  # 如果没有明确的根节点，使用第一个

            positioned_nodes = {}
            current_y = 100
            level_width = 800

            # 按层次布局
            for level in range(5):  # 最多5层
                level_nodes = []

                if level == 0:
                    level_nodes = root_nodes
                else:
                    # 找到上一层的子节点
                    for parent in positioned_nodes:
                        if positioned_nodes[parent].get('level') == level - 1:
                            children = node_connections.get(parent, [])
                            level_nodes.extend(children)

                # 布局当前层
                if level_nodes:
                    spacing = pattern.node_spacing["sibling"]["x"]
                    total_width = len(level_nodes) * spacing
                    start_x = (level_width - total_width) / 2

                    for i, node_id in enumerate(level_nodes):
                        node = next((n for n in nodes if n.get('id') == node_id), None)
                        if node:
                            node_copy = node.copy()
                            node_copy['x'] = start_x + i * spacing
                            node_copy['y'] = current_y
                            node_copy['level'] = level
                            positioned_nodes[node_id] = node_copy

                current_y += pattern.node_spacing["parent_child"]["y"]

            # 返回重新排序的节点
            return [positioned_nodes[node_id] for node_id in positioned_nodes if node_id in [n.get('id') for n in nodes]]

        except Exception as e:
            print(f"[ERROR] 层次布局失败: {e}")
            return nodes

    def _apply_radial_layout(
        self,
        nodes: List[Dict],
        node_types: Dict[str, str],
        node_connections: Dict[str, List[str]],
        pattern: LayoutPattern
    ) -> List[Dict]:
        """应用径向布局"""
        try:
            center_x, center_y = 400, 300
            positioned_nodes = {}

            # 找到中心节点
            center_nodes = [node_id for node_id, node_type in node_types.items() if node_type == 'problem']
            center_node = center_nodes[0] if center_nodes else list(node_types.keys())[0]

            # 布局中心节点
            center_node_obj = next((n for n in nodes if n.get('id') == center_node), None)
            if center_node_obj:
                center_copy = center_node_obj.copy()
                center_copy['x'] = center_x
                center_copy['y'] = center_y
                positioned_nodes[center_node] = center_copy

            # 布局其他节点
            other_nodes = [node_id for node_id in node_types.keys() if node_id != center_node]
            angle_step = 360 / len(other_nodes) if other_nodes else 90

            for i, node_id in enumerate(other_nodes):
                node = next((n for n in nodes if n.get('id') == node_id), None)
                if node:
                    node_copy = node.copy()
                    angle = i * angle_step
                    radius = pattern.node_spacing["first_ring"]

                    node_copy['x'] = center_x + radius * (angle * 3.14159 / 180)
                    node_copy['y'] = center_y + radius * (angle * 3.14159 / 180)
                    positioned_nodes[node_id] = node_copy

            return [positioned_nodes[node_id] for node_id in positioned_nodes if node_id in [n.get('id') for n in nodes]]

        except Exception as e:
            print(f"[ERROR] 径向布局失败: {e}")
            return nodes

    def _apply_flow_layout(
        self,
        nodes: List[Dict],
        node_types: Dict[str, str],
        node_connections: Dict[str, List[str]],
        pattern: LayoutPattern
    ) -> List[Dict]:
        """应用流程布局"""
        try:
            positioned_nodes = {}
            current_x, current_y = 100, 300

            # 按照连接关系布局
            visited = set()

            def layout_node_and_children(node_id, x, y):
                if node_id in visited:
                    return

                visited.add(node_id)
                node = next((n for n in nodes if n.get('id') == node_id), None)
                if node:
                    node_copy = node.copy()
                    node_copy['x'] = x
                    node_copy['y'] = y
                    positioned_nodes[node_id] = node_copy

                    # 布局子节点
                    children = node_connections.get(node_id, [])
                    child_y = y - 100 if len(children) > 1 else y

                    for i, child_id in enumerate(children):
                        child_x = x + pattern.node_spacing["main_flow"]["x"]
                        child_y = child_y + (i * 100) if len(children) > 1 else child_y
                        layout_node_and_children(child_id, child_x, child_y)

            # 从根节点开始布局
            root_nodes = [node_id for node_id, node_type in node_types.items() if node_type == 'problem']
            start_node = root_nodes[0] if root_nodes else list(node_types.keys())[0]

            layout_node_and_children(start_node, current_x, current_y)

            return [positioned_nodes[node_id] for node_id in positioned_nodes if node_id in [n.get('id') for n in nodes]]

        except Exception as e:
            print(f"[ERROR] 流程布局失败: {e}")
            return nodes

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Canvas布局学习系统')
    parser.add_argument('--record', nargs=3, metavar=('canvas_file', 'before.json', 'after.json'),
                       help='记录布局调整')
    parser.add_argument('--learn', metavar='canvas_file', help='从历史调整中学习')
    parser.add_argument('--generate', nargs=2, metavar=('canvas_file', 'content.json'),
                       help='生成最优布局')
    parser.add_argument('--pattern', default='hierarchical',
                       choices=['hierarchical', 'radial', 'flow'],
                       help='布局模式类型')

    args = parser.parse_args()

    learner = CanvasLayoutLearner()

    try:
        if args.record:
            canvas_file, before_file, after_file = args.record

            # 读取布局文件
            with open(before_file, 'r', encoding='utf-8') as f:
                before_layout = json.load(f)

            with open(after_file, 'r', encoding='utf-8') as f:
                after_layout = json.load(f)

            # 记录调整
            success = await learner.record_layout_adjustment(canvas_file, before_layout, after_layout)
            if success:
                print("布局调整记录成功")

        elif args.learn:
            canvas_file = args.learn

            # 学习布局模式
            result = await learner.learn_from_adjustments(canvas_file)
            if result:
                print(f"学习完成: {result}")

        elif args.generate:
            canvas_file, content_file = args.generate

            # 读取内容
            with open(content_file, 'r', encoding='utf-8') as f:
                content = json.load(f)

            # 生成布局
            result = await learner.generate_optimal_layout(content, args.pattern)

            # 保存结果
            output_file = f"{canvas_file}_optimized_{args.pattern}.canvas"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            print(f"最优布局已生成: {output_file}")

        else:
            print("请指定操作模式: --record, --learn, 或 --generate")
            print("使用 --help 查看详细帮助")

    except Exception as e:
        print(f"[ERROR] 执行失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())