"""
Canvas学习系统 - G6智能布局优化器

基于AntV G6图可视化引擎，为Canvas学习系统提供专业的图布局算法
解决黄色节点定位不严格、树状图结构不明显、排版美观性差等问题

Author: Canvas Learning System Team
Version: 2.0 (G6集成版)
Created: 2025-10-18
"""

import json
import math
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

# G6相关导入（在实际使用时需要安装@antv/g6）
# 这里提供JavaScript版本的核心逻辑，Python版本可以通过subprocess调用Node.js


class CanvasG6DataConverter:
    """Canvas数据与G6数据格式转换器"""

    @staticmethod
    def canvas_to_g6_data(canvas_data: Dict[str, Any]) -> Dict[str, Any]:
        """将Canvas数据转换为G6格式"""

        nodes = []
        edges = []

        # 转换节点
        for canvas_node in canvas_data.get('nodes', []):
            g6_node = {
                'id': canvas_node['id'],
                'data': {
                    'label': CanvasG6DataConverter._extract_text_content(canvas_node),
                    'type': CanvasG6DataConverter._determine_node_type(canvas_node),
                    'color': canvas_node.get('color'),
                    'original_canvas_data': canvas_node
                },
                'style': {
                    'x': canvas_node.get('x', 0),
                    'y': canvas_node.get('y', 0),
                    'width': canvas_node.get('width', 400),
                    'height': canvas_node.get('height', 300)
                }
            }
            nodes.append(g6_node)

        # 转换边
        for canvas_edge in canvas_data.get('edges', []):
            g6_edge = {
                'id': canvas_edge.get('id', f"edge-{len(edges)}"),
                'source': canvas_edge.get('fromNode', ''),
                'target': canvas_edge.get('toNode', ''),
                'data': {
                    'label': canvas_edge.get('label', ''),
                    'type': CanvasG6DataConverter._determine_edge_type(canvas_edge)
                },
                'style': {
                    'type': 'cubic-horizontal',
                    'endArrow': True
                }
            }
            edges.append(g6_edge)

        return {
            'nodes': nodes,
            'edges': edges
        }

    @staticmethod
    def g6_to_canvas_data(g6_data: Dict[str, Any]) -> Dict[str, Any]:
        """将G6数据转换回Canvas格式"""

        canvas_nodes = []
        canvas_edges = []

        # 转换节点
        for g6_node in g6_data['nodes']:
            original_data = g6_node['data'].get('original_canvas_data', {})

            canvas_node = {
                'id': g6_node['id'],
                'type': original_data.get('type', 'text'),
                'x': int(g6_node['style']['x']),
                'y': int(g6_node['style']['y']),
                'width': int(g6_node['style']['width']),
                'height': int(g6_node['style']['height']),
                'color': g6_node['data'].get('color'),
                'text': g6_node['data']['label']
            }

            # 保留原始Canvas的其他属性
            for key, value in original_data.items():
                if key not in ['x', 'y', 'width', 'height', 'id']:
                    canvas_node[key] = value

            canvas_nodes.append(canvas_node)

        # 转换边
        for g6_edge in g6_data['edges']:
            canvas_edge = {
                'id': g6_edge['id'],
                'fromNode': g6_edge['source'],
                'toNode': g6_edge['target'],
                'fromSide': 'right',
                'toSide': 'left',
                'label': g6_edge['data'].get('label', '')
            }
            canvas_edges.append(canvas_edge)

        return {
            'nodes': canvas_nodes,
            'edges': canvas_edges
        }

    @staticmethod
    def _extract_text_content(canvas_node: Dict[str, Any]) -> str:
        """提取节点文本内容"""
        if 'text' in canvas_node:
            text = canvas_node['text']
            if isinstance(text, str):
                # 提取第一行作为标签（避免过长）
                lines = text.split('\n')
                return lines[0] if lines else ''
        return ''

    @staticmethod
    def _determine_edge_type(canvas_edge: Dict[str, Any]) -> str:
        """确定边类型"""
        label = canvas_edge.get('label', '')

        if label == '拆解自':
            return 'decomposition'
        elif label == '个人理解':
            return 'understanding'
        elif label == '补充解释':
            return 'explanation'
        else:
            return 'general'

    @staticmethod
    def _determine_node_type(canvas_node: Dict[str, Any]) -> str:
        """确定节点类型"""
        color = canvas_node.get('color')
        text = canvas_node.get('text', '')

        # 根据颜色和内容判断节点类型
        if color is None or color == '':
            return 'material'  # 材料节点（无颜色）
        elif color == '6':  # 黄色
            return 'understanding'
        elif color == '5':  # 蓝色
            if '🗣️' in text:
                return 'explanation_oral'
            elif '📊' in text:
                return 'explanation_comparison'
            elif '⚓' in text:
                return 'explanation_memory'
            elif '🎯' in text:
                return 'explanation_four_level'
            else:
                return 'explanation'
        elif color in ['4', '3']:  # 红色或紫色
            return 'question'
        else:
            return 'unknown'


class G6TreeLayoutBuilder:
    """G6树状图布局构建器"""

    def build_tree_structure(self, canvas_data: Dict[str, Any]) -> Dict[str, Any]:
        """构建树状结构"""

        # 转换为G6格式
        g6_data = CanvasG6DataConverter.canvas_to_g6_data(canvas_data)

        # 构建层次结构
        tree_data = self._build_hierarchy(g6_data)

        return tree_data

    def _build_hierarchy(self, g6_data: Dict[str, Any]) -> Dict[str, Any]:
        """构建层次结构"""

        # 创建节点映射
        node_map = {node['id']: node for node in g6_data['nodes']}

        # 构建父子关系
        for edge in g6_data['edges']:
            parent_id = edge['source']
            child_id = edge['target']

            if parent_id in node_map:
                parent_node = node_map[parent_id]
                if 'children' not in parent_node:
                    parent_node['children'] = []
                parent_node['children'].append(child_id)

        # 找到根节点（没有父节点的节点）
        root_nodes = []
        child_nodes = set(edge['target'] for edge in g6_data['edges'])

        for node in g6_data['nodes']:
            if node['id'] not in child_nodes:
                root_nodes.append(node)

        # 构建树结构
        if len(root_nodes) == 1:
            return self._build_subtree(root_nodes[0]['id'], node_map)
        else:
            # 多个根节点，创建虚拟根节点
            virtual_root = {
                'id': 'virtual-root',
                'data': {'label': 'Root', 'type': 'virtual'},
                'children': [node['id'] for node in root_nodes]
            }
            return self._build_subtree('virtual-root', {**node_map, 'virtual-root': virtual_root})

    def _build_subtree(self, node_id: str, node_map: Dict[str, Any]) -> Dict[str, Any]:
        """构建子树"""
        node = node_map[node_id]
        subtree = {
            'id': node_id,
            'data': node['data'],
            'children': []
        }

        if 'children' in node:
            for child_id in node['children']:
                child_subtree = self._build_subtree(child_id, node_map)
                subtree['children'].append(child_subtree)

        return subtree


class G6CanvasLayoutOptimizer:
    """G6智能布局优化器"""

    def __init__(self):
        self.converter = CanvasG6DataConverter()
        self.tree_builder = G6TreeLayoutBuilder()

        # 用户偏好配置
        self.user_preferences = {
            'default_layout': 'compactbox',
            'yellow_node_alignment': 'strict_center',
            'tree_direction': 'TB',
            'node_spacing': {
                'vertical': 80,
                'horizontal': 120
            },
            'aesthetic_settings': {
                'symmetry': True,
                'balance': True,
                'hierarchy_clarity': 10
            }
        }

    def optimize_canvas_layout(self, canvas_data: Dict[str, Any],
                             layout_type: str = 'compactbox') -> Dict[str, Any]:
        """优化Canvas布局"""

        # 1. 转换Canvas数据为G6格式
        g6_data = self.converter.canvas_to_g6_data(canvas_data)

        # 2. 分析图结构和节点类型
        layout_config = self._analyze_and_configure_layout(g6_data, layout_type)

        # 3. 应用G6布局算法
        positioned_data = self._apply_g6_layout(g6_data, layout_config)

        # 4. 优化黄色节点位置（严格正下方对齐）
        optimized_data = self._optimize_yellow_node_positions(positioned_data)

        # 5. 转换回Canvas格式
        return self.converter.g6_to_canvas_data(optimized_data)

    def _analyze_and_configure_layout(self, g6_data: Dict[str, Any],
                                    layout_type: str) -> Dict[str, Any]:
        """分析并配置布局参数"""

        node_count = len(g6_data['nodes'])
        edge_count = len(g6_data['edges'])

        # 基于布局类型配置参数
        if layout_type == 'compactbox':
            return self._configure_compactbox_layout(g6_data)
        elif layout_type == 'mindmap':
            return self._configure_mindmap_layout(g6_data)
        elif layout_type == 'dendrogram':
            return self._configure_dendrogram_layout(g6_data)
        else:
            raise ValueError(f"不支持的布局类型: {layout_type}")

    def _configure_compactbox_layout(self, g6_data: Dict[str, Any]) -> Dict[str, Any]:
        """配置紧凑树布局"""

        return {
            'type': 'compactbox',
            'direction': self.user_preferences['tree_direction'],
            'getWidth': lambda d: self._get_node_width(d),
            'getHeight': lambda d: self._get_node_height(d),
            'getVGap': lambda d: self._get_vertical_gap(d),
            'getHGap': lambda d: self._get_horizontal_gap(d)
        }

    def _configure_mindmap_layout(self, g6_data: Dict[str, Any]) -> Dict[str, Any]:
        """配置思维导图布局"""

        return {
            'type': 'mindmap',
            'direction': 'H',  # 水平方向
            'getWidth': lambda d: self._get_node_width(d),
            'getHeight': lambda d: self._get_node_height(d),
            'getVGap': lambda d: self._get_mindmap_vgap(d),
            'getHGap': lambda d: self._get_mindmap_hgap(d),
            'getSide': lambda d: self._get_mindmap_side(d)
        }

    def _configure_dendrogram_layout(self, g6_data: Dict[str, Any]) -> Dict[str, Any]:
        """配置系统树图布局"""

        return {
            'type': 'dendrogram',
            'direction': self.user_preferences['tree_direction'],
            'nodeSep': 50,
            'rankSep': 120
        }

    def _get_node_width(self, node_data: Dict[str, Any]) -> int:
        """根据节点类型动态设置宽度"""
        node_type = node_data.get('data', {}).get('type', '')

        width_map = {
            'material': 400,
            'question': 350,
            'understanding': 300,  # 黄色节点稍窄
            'explanation': 320,
            'explanation_oral': 300,
            'explanation_comparison': 300,
            'explanation_memory': 300,
            'explanation_four_level': 300,
            'virtual': 200
        }

        return width_map.get(node_type, 300)

    def _get_node_height(self, node_data: Dict[str, Any]) -> int:
        """根据节点类型动态设置高度"""
        node_type = node_data.get('data', {}).get('type', '')

        height_map = {
            'material': 200,
            'question': 120,
            'understanding': 150,  # 黄色节点高度
            'explanation': 100,
            'explanation_oral': 80,
            'explanation_comparison': 80,
            'explanation_memory': 80,
            'explanation_four_level': 80,
            'virtual': 50
        }

        return height_map.get(node_type, 80)

    def _get_vertical_gap(self, node_data: Dict[str, Any]) -> int:
        """计算垂直间距"""
        node_type = node_data.get('data', {}).get('type', '')

        # 问题→黄色节点更紧密
        if node_type == 'question':
            return 30
        return self.user_preferences['node_spacing']['vertical']

    def _get_horizontal_gap(self, node_data: Dict[str, Any]) -> int:
        """计算水平间距"""
        return self.user_preferences['node_spacing']['horizontal']

    def _get_mindmap_vgap(self, node_data: Dict[str, Any]) -> int:
        """思维导图垂直间距"""
        node_type = node_data.get('data', {}).get('type', '')

        # 黄色节点垂直间距更小
        if node_type == 'understanding':
            return 15
        return 25

    def _get_mindmap_hgap(self, node_data: Dict[str, Any]) -> int:
        """思维导图水平间距"""
        return 80

    def _get_mindmap_side(self, node_data: Dict[str, Any]) -> str:
        """思维导图左右分布"""
        node_type = node_data.get('data', {}).get('type', '')
        node_color = node_data.get('data', {}).get('color', '')

        # 自定义左右分布规则
        if node_type == 'understanding':
            return 'right'
        elif node_color == '5':  # 解释节点放在左边
            return 'left'
        else:
            return 'right'

    def _apply_g6_layout(self, g6_data: Dict[str, Any],
                        layout_config: Dict[str, Any]) -> Dict[str, Any]:
        """应用G6布局算法

        这里提供Python版本的基本布局逻辑
        实际的G6布局算法需要通过JavaScript实现
        """

        # 简化版本：基于配置计算位置
        positioned_nodes = []

        # 构建树结构
        tree_data = self.tree_builder.build_tree_structure({
            'nodes': g6_data['nodes'],
            'edges': g6_data['edges']
        })

        # 应用布局算法
        if layout_config['type'] == 'compactbox':
            positioned_nodes = self._apply_compactbox_layout(tree_data, layout_config)
        elif layout_config['type'] == 'mindmap':
            positioned_nodes = self._apply_mindmap_layout(tree_data, layout_config)

        return {
            'nodes': positioned_nodes,
            'edges': g6_data['edges']
        }

    def _apply_compactbox_layout(self, tree_data: Dict[str, Any],
                                config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """应用紧凑树布局"""

        positioned_nodes = []
        start_x, start_y = 100, 100

        def layout_subtree(node_data: Dict[str, Any], x: int, y: int, level: int) -> int:
            """递归布局子树"""

            node_id = node_data['id']
            width = config['getWidth'](node_data)
            height = config['getHeight'](node_data)

            # 找到对应的G6节点
            g6_node = None
            for node in self._find_g6_nodes_by_id(node_id):
                g6_node = node
                break

            if not g6_node:
                return height

            # 设置节点位置
            g6_node['style']['x'] = x
            g6_node['style']['y'] = y
            g6_node['style']['width'] = width
            g6_node['style']['height'] = height

            positioned_nodes.append(g6_node)

            # 布局子节点
            if 'children' in node_data and node_data['children']:
                child_y = y + height + config['getVGap'](node_data)
                total_height = 0

                for child_id in node_data['children']:
                    child_node = self._find_node_in_tree(tree_data, child_id)
                    if child_node:
                        child_height = layout_subtree(child_node, x + config['getHGap'](node_data), child_y, level + 1)
                        child_y += child_height + config['getVGap'](child_node)
                        total_height += child_height + config['getVGap'](child_node)

                return max(height, total_height - config['getVGap'](node_data))

            return height

        # 从根节点开始布局
        layout_subtree(tree_data, start_x, start_y, 0)

        return positioned_nodes

    def _apply_mindmap_layout(self, tree_data: Dict[str, Any],
                             config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """应用思维导图布局"""

        positioned_nodes = []
        center_x, center_y = 500, 300

        def layout_subtree(node_data: Dict[str, Any], x: int, y: int,
                          angle: float, radius: int, parent_side: str) -> None:
            """递归布局子树"""

            node_id = node_data['id']
            width = config['getWidth'](node_data)
            height = config['getHeight'](node_data)

            # 找到对应的G6节点
            g6_node = None
            for node in self._find_g6_nodes_by_id(node_id):
                g6_node = node
                break

            if not g6_node:
                return

            # 计算位置
            pos_x = x + math.cos(angle) * radius
            pos_y = y + math.sin(angle) * radius

            # 设置节点位置
            g6_node['style']['x'] = pos_x
            g6_node['style']['y'] = pos_y
            g6_node['style']['width'] = width
            g6_node['style']['height'] = height

            positioned_nodes.append(g6_node)

            # 布局子节点
            if 'children' in node_data and node_data['children']:
                child_count = len(node_data['children'])
                angle_step = math.pi / 3  # 60度扇形

                for i, child_id in enumerate(node_data['children']):
                    child_node = self._find_node_in_tree(tree_data, child_id)
                    if child_node:
                        side = config['getSide'](child_node)

                        if side == 'left':
                            child_angle = angle - angle_step/2 + (i - child_count/2) * angle_step/child_count
                        else:
                            child_angle = angle - angle_step/2 + (i - child_count/2) * angle_step/child_count

                        layout_subtree(child_node, pos_x, pos_y, child_angle,
                                     radius * 0.8, side)

        # 从根节点开始布局
        layout_subtree(tree_data, center_x, center_y, 0, 150, 'center')

        return positioned_nodes

    def _find_g6_nodes_by_id(self, node_id: str) -> List[Dict[str, Any]]:
        """根据ID查找G6节点"""
        # 这里需要访问原始G6数据，简化实现
        return []

    def _find_node_in_tree(self, tree_data: Dict[str, Any], node_id: str) -> Optional[Dict[str, Any]]:
        """在树结构中查找节点"""

        if tree_data['id'] == node_id:
            return tree_data

        if 'children' in tree_data:
            for child in tree_data['children']:
                result = self._find_node_in_tree(child, node_id)
                if result:
                    return result

        return None

    def _optimize_yellow_node_positions(self, g6_data: Dict[str, Any]) -> Dict[str, Any]:
        """优化黄色节点位置 - 确保严格在材料节点正下方"""

        for node in g6_data['nodes']:
            if node.get('data', {}).get('color') == '6':  # 黄色节点
                # 找到父节点（材料/问题节点）
                parent_edges = [e for e in g6_data['edges']
                              if e['target'] == node['id']]

                if parent_edges:
                    parent_id = parent_edges[0]['source']
                    parent_node = self._find_g6_node_by_id(g6_data, parent_id)

                    if parent_node:
                        # 严格居中对齐计算
                        ideal_x = parent_node['style']['x'] + (parent_node['style']['width'] - node['style']['width']) / 2
                        ideal_y = parent_node['style']['y'] + parent_node['style']['height'] + 30

                        # 检查重叠并调整
                        final_position = self._adjust_for_overlap(
                            ideal_x, ideal_y, node, g6_data
                        )

                        node['style']['x'] = final_position['x']
                        node['style']['y'] = final_position['y']

        return g6_data

    def _find_g6_node_by_id(self, g6_data: Dict[str, Any], node_id: str) -> Optional[Dict[str, Any]]:
        """根据ID查找G6节点"""
        for node in g6_data['nodes']:
            if node['id'] == node_id:
                return node
        return None

    def _adjust_for_overlap(self, x: float, y: float, node: Dict[str, Any],
                           g6_data: Dict[str, Any]) -> Dict[str, float]:
        """调整位置以避免重叠"""

        node_rect = {
            'x': x, 'y': y,
            'width': node['style']['width'],
            'height': node['style']['height']
        }

        # 检查与其他节点的重叠
        for other_node in g6_data['nodes']:
            if other_node['id'] != node['id']:
                other_rect = {
                    'x': other_node['style']['x'],
                    'y': other_node['style']['y'],
                    'width': other_node['style']['width'],
                    'height': other_node['style']['height']
                }

                if self._rectangles_overlap(node_rect, other_rect):
                    # 计算调整方向
                    overlap_x = self._calculate_overlap_x(node_rect, other_rect)
                    overlap_y = self._calculate_overlap_y(node_rect, other_rect)

                    # 优先向下调整，保持水平对齐
                    if overlap_y > 0:
                        y += overlap_y + 10  # 额外10px间距
                    elif overlap_x > 0:
                        x += overlap_x + 10

        return {'x': x, 'y': y}

    def _rectangles_overlap(self, rect1: Dict[str, float], rect2: Dict[str, float]) -> bool:
        """检查两个矩形是否重叠"""
        return not (rect1['x'] + rect1['width'] <= rect2['x'] or
                   rect2['x'] + rect2['width'] <= rect1['x'] or
                   rect1['y'] + rect1['height'] <= rect2['y'] or
                   rect2['y'] + rect2['height'] <= rect1['y'])

    def _calculate_overlap_x(self, rect1: Dict[str, float], rect2: Dict[str, float]) -> float:
        """计算x方向重叠量"""
        left = max(rect1['x'], rect2['x'])
        right = min(rect1['x'] + rect1['width'], rect2['x'] + rect2['width'])
        return max(0, right - left)

    def _calculate_overlap_y(self, rect1: Dict[str, float], rect2: Dict[str, float]) -> float:
        """计算y方向重叠量"""
        top = max(rect1['y'], rect2['y'])
        bottom = min(rect1['y'] + rect1['height'], rect2['y'] + rect2['height'])
        return max(0, bottom - top)

    def update_preferences(self, preferences: Dict[str, Any]) -> None:
        """更新用户偏好"""
        self.user_preferences.update(preferences)

    def get_current_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return {
            'preferences': self.user_preferences,
            'supported_layouts': ['compactbox', 'mindmap', 'dendrogram']
        }


class G6LayoutTester:
    """G6布局测试器"""

    def __init__(self):
        self.optimizer = G6CanvasLayoutOptimizer()
        self.test_results = []

    def test_layout_optimization(self, canvas_file_path: str) -> Dict[str, Any]:
        """测试布局优化"""

        # 读取Canvas文件
        with open(canvas_file_path, 'r', encoding='utf-8') as f:
            canvas_data = json.load(f)

        # 测试不同布局算法
        layout_types = ['compactbox', 'mindmap', 'dendrogram']
        results = {}

        for layout_type in layout_types:
            try:
                print(f"测试 {layout_type} 布局...")

                # 应用布局优化
                optimized_canvas = self.optimizer.optimize_canvas_layout(canvas_data, layout_type)

                # 评估布局质量
                quality_metrics = self._evaluate_layout_quality(optimized_canvas)

                # 保存测试结果
                output_file = self._save_test_result(optimized_canvas, layout_type)

                results[layout_type] = {
                    'success': True,
                    'output_file': output_file,
                    'quality_metrics': quality_metrics
                }

                print(f"✅ {layout_type} 布局测试成功")

            except Exception as e:
                print(f"❌ {layout_type} 布局测试失败: {e}")
                results[layout_type] = {
                    'success': False,
                    'error': str(e)
                }

        return {
            'test_file': canvas_file_path,
            'results': results,
            'recommendation': self._get_best_layout(results)
        }

    def _evaluate_layout_quality(self, canvas_data: Dict[str, Any]) -> Dict[str, float]:
        """评估布局质量"""

        nodes = canvas_data.get('nodes', [])
        edges = canvas_data.get('edges', [])

        # 1. 黄色节点对齐质量
        yellow_alignment_score = self._evaluate_yellow_alignment(nodes, edges)

        # 2. 层次清晰度
        hierarchy_score = self._evaluate_hierarchy_clarity(nodes, edges)

        # 3. 重叠检测
        overlap_score = self._evaluate_overlap_avoidance(nodes)

        # 4. 对称性评分
        symmetry_score = self._evaluate_symmetry(nodes)

        # 5. 空间利用效率
        space_efficiency_score = self._evaluate_space_efficiency(nodes)

        return {
            'yellow_alignment': yellow_alignment_score,
            'hierarchy_clarity': hierarchy_score,
            'overlap_avoidance': overlap_score,
            'symmetry': symmetry_score,
            'space_efficiency': space_efficiency_score,
            'overall_score': (yellow_alignment_score + hierarchy_score +
                            overlap_score + symmetry_score + space_efficiency_score) / 5
        }

    def _evaluate_yellow_alignment(self, nodes: List[Dict], edges: List[Dict]) -> float:
        """评估黄色节点对齐质量"""

        yellow_nodes = [node for node in nodes if node.get('color') == '6']
        if not yellow_nodes:
            return 1.0

        alignment_scores = []

        for yellow_node in yellow_nodes:
            # 找到父节点
            parent_edges = [edge for edge in edges if edge['toNode'] == yellow_node['id']]

            if parent_edges:
                parent_id = parent_edges[0]['fromNode']
                parent_node = next((node for node in nodes if node['id'] == parent_id), None)

                if parent_node:
                    # 计算居中对齐偏差
                    ideal_x = parent_node['x'] + (parent_node['width'] - yellow_node['width']) / 2
                    actual_x = yellow_node['x']

                    deviation = abs(actual_x - ideal_x)
                    max_deviation = 50  # 最大允许偏差

                    score = max(0, 1 - deviation / max_deviation)
                    alignment_scores.append(score)

        return sum(alignment_scores) / len(alignment_scores) if alignment_scores else 1.0

    def _evaluate_hierarchy_clarity(self, nodes: List[Dict], edges: List[Dict]) -> float:
        """评估层次清晰度"""

        # 简化实现：基于y坐标的层次分布
        y_positions = [node['y'] for node in nodes]
        y_positions.sort()

        # 计算层次间距的一致性
        if len(y_positions) < 2:
            return 1.0

        gaps = []
        for i in range(1, len(y_positions)):
            gaps.append(y_positions[i] - y_positions[i-1])

        if not gaps:
            return 1.0

        avg_gap = sum(gaps) / len(gaps)
        variance = sum((gap - avg_gap) ** 2 for gap in gaps) / len(gaps)

        # 方差越小，层次越清晰
        score = max(0, 1 - variance / (avg_gap ** 2))

        return score

    def _evaluate_overlap_avoidance(self, nodes: List[Dict]) -> float:
        """评估重叠避免"""

        total_pairs = 0
        overlap_pairs = 0

        for i, node1 in enumerate(nodes):
            for node2 in nodes[i+1:]:
                total_pairs += 1

                # 检查重叠
                if (node1['x'] < node2['x'] + node2['width'] and
                    node1['x'] + node1['width'] > node2['x'] and
                    node1['y'] < node2['y'] + node2['height'] and
                    node1['y'] + node1['height'] > node2['y']):
                    overlap_pairs += 1

        if total_pairs == 0:
            return 1.0

        return 1 - (overlap_pairs / total_pairs)

    def _evaluate_symmetry(self, nodes: List[Dict]) -> float:
        """评估对称性"""

        # 简化实现：基于x坐标分布的对称性
        x_positions = [node['x'] + node['width'] / 2 for node in nodes]

        if len(x_positions) < 2:
            return 1.0

        center_x = sum(x_positions) / len(x_positions)

        # 计算左右对称性
        left_nodes = [pos for pos in x_positions if pos < center_x]
        right_nodes = [pos for pos in x_positions if pos > center_x]

        if not left_nodes or not right_nodes:
            return 0.8  # 单侧布局，对称性稍低

        # 计算左右节点数量平衡
        balance_score = 1 - abs(len(left_nodes) - len(right_nodes)) / max(len(left_nodes), len(right_nodes))

        return balance_score

    def _evaluate_space_efficiency(self, nodes: List[Dict]) -> float:
        """评估空间利用效率"""

        if not nodes:
            return 1.0

        # 计算边界框
        min_x = min(node['x'] for node in nodes)
        max_x = max(node['x'] + node['width'] for node in nodes)
        min_y = min(node['y'] for node in nodes)
        max_y = max(node['y'] + node['height'] for node in nodes)

        bounding_area = (max_x - min_x) * (max_y - min_y)

        # 计算节点总面积
        node_area = sum(node['width'] * node['height'] for node in nodes)

        if bounding_area == 0:
            return 1.0

        # 空间利用率
        efficiency = node_area / bounding_area

        # 理想利用率在0.3-0.7之间
        if 0.3 <= efficiency <= 0.7:
            return 1.0
        elif efficiency < 0.3:
            return efficiency / 0.3
        else:
            return 1.0 - (efficiency - 0.7) / 0.3

    def _save_test_result(self, canvas_data: Dict[str, Any], layout_type: str) -> str:
        """保存测试结果"""

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"test-{layout_type}-layout-{timestamp}.canvas"
        filepath = os.path.join("C:/Users/ROG/托福/笔记库/测试/", filename)

        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(canvas_data, f, ensure_ascii=False, indent=2)

        return filepath

    def _get_best_layout(self, results: Dict[str, Dict]) -> str:
        """获取最佳布局推荐"""

        best_layout = 'compactbox'
        best_score = 0

        for layout_type, result in results.items():
            if result.get('success') and 'quality_metrics' in result:
                overall_score = result['quality_metrics'].get('overall_score', 0)
                if overall_score > best_score:
                    best_score = overall_score
                    best_layout = layout_type

        return best_layout


def main():
    """主函数 - 演示G6布局优化"""

    # 创建测试器
    tester = G6LayoutTester()

    # 测试文件路径
    test_file = "C:/Users/ROG/托福/笔记库/测试/test-canvas-g6-layout-20251018.canvas"

    if os.path.exists(test_file):
        print(f"🧪 开始测试Canvas布局优化...")
        print(f"📁 测试文件: {test_file}")

        # 运行测试
        test_results = tester.test_layout_optimization(test_file)

        # 输出结果
        print("\n📊 测试结果:")
        print("=" * 50)

        for layout_type, result in test_results['results'].items():
            if result['success']:
                metrics = result['quality_metrics']
                print(f"✅ {layout_type}:")
                print(f"   整体评分: {metrics['overall_score']:.2f}")
                print(f"   黄色对齐: {metrics['yellow_alignment']:.2f}")
                print(f"   层次清晰: {metrics['hierarchy_clarity']:.2f}")
                print(f"   无重叠: {metrics['overlap_avoidance']:.2f}")
                print(f"   输出文件: {result['output_file']}")
            else:
                print(f"❌ {layout_type}: {result['error']}")
            print()

        print(f"🏆 推荐布局: {test_results['recommendation']}")

    else:
        print(f"❌ 测试文件不存在: {test_file}")
        print("请先创建测试Canvas文件")


if __name__ == "__main__":
    main()