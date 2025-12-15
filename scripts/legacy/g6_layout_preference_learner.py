"""
Canvas学习系统 - G6布局偏好学习系统

记录用户的手动调整，学习个人布局偏好，支持迭代优化
实现用户调整→学习→优化的完整循环

Author: Canvas Learning System Team
Version: 2.0 (G6集成版)
Created: 2025-10-18
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, Counter


@dataclass
class UserAdjustment:
    """用户调整记录"""
    timestamp: str
    node_id: str
    node_type: str
    original_position: Tuple[float, float]
    new_position: Tuple[float, float]
    adjustment_vector: Tuple[float, float]
    context: Dict[str, Any]


@dataclass
class LayoutSession:
    """布局会话记录"""
    session_id: str
    start_time: str
    end_time: Optional[str]
    canvas_file: str
    layout_type: str
    adjustments: List[UserAdjustment]
    final_preferences: Optional[Dict[str, Any]]


class G6LayoutPreferenceLearner:
    """布局偏好学习系统"""

    def __init__(self, data_dir: str = "C:/Users/ROG/托福/布局学习数据/"):
        self.data_dir = data_dir
        self.adjustment_history: List[UserAdjustment] = []
        self.sessions: List[LayoutSession] = []
        self.preference_patterns: Dict[str, Any] = {}

        # 确保数据目录存在
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(os.path.join(data_dir, "sessions"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "preferences"), exist_ok=True)

        # 加载历史数据
        self._load_historical_data()

        # 初始化偏好模型
        self._initialize_preference_model()

    def _load_historical_data(self) -> None:
        """加载历史数据"""

        try:
            # 加载偏好模式
            preferences_file = os.path.join(self.data_dir, "preferences", "learned_preferences.json")
            if os.path.exists(preferences_file):
                with open(preferences_file, 'r', encoding='utf-8') as f:
                    self.preference_patterns = json.load(f)

            # 加载会话历史
            sessions_dir = os.path.join(self.data_dir, "sessions")
            if os.path.exists(sessions_dir):
                for filename in os.listdir(sessions_dir):
                    if filename.endswith('.json'):
                        session_file = os.path.join(sessions_dir, filename)
                        with open(session_file, 'r', encoding='utf-8') as f:
                            session_data = json.load(f)
                            session = self._deserialize_session(session_data)
                            if session:
                                self.sessions.append(session)
                                self.adjustment_history.extend(session.adjustments)

            print(f"✅ 加载历史数据: {len(self.sessions)} 个会话, {len(self.adjustment_history)} 次调整")

        except Exception as e:
            print(f"⚠️ 加载历史数据失败: {e}")

    def _initialize_preference_model(self) -> None:
        """初始化偏好模型"""

        default_preferences = {
            'yellow_node_alignment': {
                'preferred_offset_x': 0.0,  # 相对于父节点的X偏移
                'preferred_offset_y': 30.0,  # 相对于父节点的Y偏移
                'alignment_strictness': 0.8,  # 对齐严格程度 0-1
                'adjustment_frequency': defaultdict(int)
            },
            'spacing_preferences': {
                'vertical_gap': {
                    'question_to_understanding': 30.0,
                    'understanding_to_subquestion': 60.0,
                    'subquestion_to_subquestion': 40.0
                },
                'horizontal_gap': {
                    'main_branch': 120.0,
                    'sub_branch': 80.0
                }
            },
            'layout_direction_preference': {
                'compactbox': {'TB': 0.7, 'LR': 0.3},
                'mindmap': {'H': 0.8, 'LR': 0.2},
                'dendrogram': {'TB': 0.9, 'LR': 0.1}
            },
            'aesthetic_preferences': {
                'symmetry_preference': 0.6,  # 对称偏好 0-1
                'balance_preference': 0.7,   # 平衡偏好 0-1
                'density_preference': 0.5    # 密度偏好 0-1
            },
            'node_size_adjustments': {
                'yellow_nodes': {'width_scale': 1.0, 'height_scale': 1.0},
                'question_nodes': {'width_scale': 1.0, 'height_scale': 1.0},
                'explanation_nodes': {'width_scale': 1.0, 'height_scale': 1.0}
            }
        }

        # 合并已学习的偏好
        for key, value in default_preferences.items():
            if key not in self.preference_patterns:
                self.preference_patterns[key] = value

    def start_new_session(self, canvas_file: str, layout_type: str) -> str:
        """开始新的布局会话"""

        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.sessions)}"

        session = LayoutSession(
            session_id=session_id,
            start_time=datetime.now().isoformat(),
            end_time=None,
            canvas_file=canvas_file,
            layout_type=layout_type,
            adjustments=[],
            final_preferences=None
        )

        self.sessions.append(session)
        self._save_session(session)

        print(f"🎯 开始新会话: {session_id}")
        print(f"📁 Canvas文件: {canvas_file}")
        print(f"🎨 布局类型: {layout_type}")

        return session_id

    def record_user_adjustment(self,
                             session_id: str,
                             canvas_data_before: Dict[str, Any],
                             canvas_data_after: Dict[str, Any],
                             adjusted_node_ids: List[str]) -> Dict[str, Any]:
        """记录用户的手动调整"""

        # 查找会话
        session = self._find_session_by_id(session_id)
        if not session:
            raise ValueError(f"会话不存在: {session_id}")

        # 计算变化
        changes = self._calculate_changes(canvas_data_before, canvas_data_after, adjusted_node_ids)

        # 创建调整记录
        new_adjustments = []
        for change in changes:
            adjustment = UserAdjustment(
                timestamp=datetime.now().isoformat(),
                node_id=change['node_id'],
                node_type=change['node_type'],
                original_position=change['original_position'],
                new_position=change['new_position'],
                adjustment_vector=change['adjustment_vector'],
                context=change['context']
            )
            new_adjustments.append(adjustment)

        # 添加到会话
        session.adjustments.extend(new_adjustments)
        self.adjustment_history.extend(new_adjustments)

        # 更新偏好模式
        self._update_preference_patterns(new_adjustments, session)

        # 保存会话
        self._save_session(session)

        print(f"📝 记录调整: {len(new_adjustments)} 个节点")
        for adj in new_adjustments:
            print(f"   节点 {adj.node_id}: ({adj.adjustment_vector[0]:.1f}, {adj.adjustment_vector[1]:.1f})")

        return {
            'session_id': session_id,
            'adjustments_recorded': len(new_adjustments),
            'total_adjustments_in_session': len(session.adjustments),
            'updated_preferences': self.get_current_preferences()
        }

    def _calculate_changes(self,
                          before: Dict[str, Any],
                          after: Dict[str, Any],
                          adjusted_node_ids: List[str]) -> List[Dict[str, Any]]:
        """计算节点位置变化"""

        changes = []

        before_nodes = {node['id']: node for node in before.get('nodes', [])}
        after_nodes = {node['id']: node for node in after.get('nodes', [])}

        # 构建关系图
        relationship_graph = self._build_relationship_graph(after)

        for node_id in adjusted_node_ids:
            if node_id in before_nodes and node_id in after_nodes:
                before_node = before_nodes[node_id]
                after_node = after_nodes[node_id]

                dx = after_node['x'] - before_node['x']
                dy = after_node['y'] - before_node['y']

                if abs(dx) > 2 or abs(dy) > 2:  # 只记录显著调整
                    change = {
                        'node_id': node_id,
                        'node_type': self._determine_node_type(after_node),
                        'node_color': after_node.get('color'),
                        'original_position': (before_node['x'], before_node['y']),
                        'new_position': (after_node['x'], after_node['y']),
                        'adjustment_vector': (dx, dy),
                        'context': {
                            'parent_info': self._get_parent_info(node_id, relationship_graph, after_nodes),
                            'siblings_info': self._get_siblings_info(node_id, relationship_graph, after_nodes),
                            'node_size': (after_node.get('width', 400), after_node.get('height', 300))
                        }
                    }
                    changes.append(change)

        return changes

    def _build_relationship_graph(self, canvas_data: Dict[str, Any]) -> Dict[str, Dict[str, List[str]]]:
        """构建关系图"""

        graph = defaultdict(lambda: {'parents': [], 'children': []})

        for edge in canvas_data.get('edges', []):
            from_node = edge['fromNode']
            to_node = edge['toNode']
            label = edge.get('label', '')

            graph[to_node]['parents'].append({'id': from_node, 'label': label})
            graph[from_node]['children'].append({'id': to_node, 'label': label})

        return dict(graph)

    def _get_parent_info(self, node_id: str, relationship_graph: Dict, nodes: Dict) -> Optional[Dict]:
        """获取父节点信息"""
        if node_id in relationship_graph:
            parents = relationship_graph[node_id]['parents']
            if parents:
                parent_id = parents[0]['id']
                if parent_id in nodes:
                    parent_node = nodes[parent_id]
                    return {
                        'id': parent_id,
                        'type': self._determine_node_type(parent_node),
                        'position': (parent_node['x'], parent_node['y']),
                        'size': (parent_node.get('width', 400), parent_node.get('height', 300)),
                        'edge_label': parents[0]['label']
                    }
        return None

    def _get_siblings_info(self, node_id: str, relationship_graph: Dict, nodes: Dict) -> List[Dict]:
        """获取兄弟节点信息"""
        siblings = []

        if node_id in relationship_graph:
            parents = relationship_graph[node_id]['parents']
            if parents:
                parent_id = parents[0]['id']
                children = relationship_graph.get(parent_id, {}).get('children', [])

                for child in children:
                    child_id = child['id']
                    if child_id != node_id and child_id in nodes:
                        child_node = nodes[child_id]
                        siblings.append({
                            'id': child_id,
                            'type': self._determine_node_type(child_node),
                            'position': (child_node['x'], child_node['y']),
                            'size': (child_node.get('width', 400), child_node.get('height', 300))
                        })

        return siblings

    def _determine_node_type(self, node: Dict[str, Any]) -> str:
        """确定节点类型"""
        color = node.get('color', '')

        if color == '' or color is None:
            return 'material'
        elif color == '6':
            return 'understanding'
        elif color == '5':
            return 'explanation'
        elif color in ['4', '3']:
            return 'question'
        else:
            return 'unknown'

    def _update_preference_patterns(self, adjustments: List[UserAdjustment], session: LayoutSession) -> None:
        """更新偏好模式"""

        # 1. 更新黄色节点对齐偏好
        self._update_yellow_alignment_preferences(adjustments)

        # 2. 更新间距偏好
        self._update_spacing_preferences(adjustments)

        # 3. 更新布局方向偏好
        self._update_layout_direction_preferences(session)

        # 4. 更新美学偏好
        self._update_aesthetic_preferences(adjustments, session)

        # 5. 更新节点尺寸偏好
        self._update_node_size_preferences(adjustments)

        # 保存偏好
        self._save_preferences()

    def _update_yellow_alignment_preferences(self, adjustments: List[UserAdjustment]) -> None:
        """更新黄色节点对齐偏好"""

        yellow_adjustments = [adj for adj in adjustments if adj.node_type == 'understanding']

        if not yellow_adjustments:
            return

        # 计算平均偏移
        offset_x_sum = 0
        offset_y_sum = 0
        count = 0

        for adj in yellow_adjustments:
            parent_info = adj.context.get('parent_info')
            if parent_info:
                # 计算相对于父节点的偏移
                parent_x, parent_y = parent_info['position']
                parent_width, parent_height = parent_info['size']

                # 理想居中位置
                ideal_center_x = parent_x + parent_width / 2
                actual_center_x = adj.new_position[0] + adj.context['node_size'][0] / 2

                offset_x = actual_center_x - ideal_center_x
                offset_y = adj.new_position[1] - (parent_y + parent_height)

                offset_x_sum += offset_x
                offset_y_sum += offset_y
                count += 1

        if count > 0:
            avg_offset_x = offset_x_sum / count
            avg_offset_y = offset_y_sum / count

            # 更新偏好（使用加权平均）
            current_prefs = self.preference_patterns['yellow_node_alignment']
            weight = min(0.3, count / 10)  # 最多30%的权重

            current_prefs['preferred_offset_x'] = (1 - weight) * current_prefs['preferred_offset_x'] + weight * avg_offset_x
            current_prefs['preferred_offset_y'] = (1 - weight) * current_prefs['preferred_offset_y'] + weight * avg_offset_y

            # 更新对齐严格程度
            x_variance = sum((adj.adjustment_vector[0] - avg_offset_x) ** 2 for adj in yellow_adjustments) / count
            strictness = max(0.1, 1 - (x_variance / 1000))  # 方差越小越严格
            current_prefs['alignment_strictness'] = (1 - weight) * current_prefs['alignment_strictness'] + weight * strictness

    def _update_spacing_preferences(self, adjustments: List[UserAdjustment]) -> None:
        """更新间距偏好"""

        for adj in adjustments:
            parent_info = adj.context.get('parent_info')
            siblings_info = adj.context.get('siblings_info', [])

            if parent_info:
                # 分析垂直间距
                parent_y = parent_info['position'][1]
                parent_height = parent_info['size'][1]
                actual_gap = adj.new_position[1] - (parent_y + parent_height)

                # 根据边类型更新间距偏好
                edge_label = parent_info.get('edge_label', '')

                if edge_label == '个人理解':
                    key = 'question_to_understanding'
                elif edge_label == '拆解自':
                    if adj.node_type == 'question':
                        key = 'understanding_to_subquestion'
                    else:
                        key = 'subquestion_to_subquestion'
                else:
                    continue

                current_gap = self.preference_patterns['spacing_preferences']['vertical_gap'][key]
                weight = 0.2
                new_gap = (1 - weight) * current_gap + weight * actual_gap
                self.preference_patterns['spacing_preferences']['vertical_gap'][key] = new_gap

            # 分析水平间距（基于兄弟节点）
            if siblings_info:
                for sibling in siblings_info:
                    sibling_x = sibling['position'][0]
                    current_x = adj.new_position[0]

                    # 计算水平间距
                    if current_x > sibling_x:
                        gap = current_x - (sibling_x + sibling['size'][0])
                    else:
                        gap = sibling_x - (current_x + adj.context['node_size'][0])

                    if gap > 0:
                        current_gap = self.preference_patterns['spacing_preferences']['horizontal_gap']['sub_branch']
                        weight = 0.15
                        new_gap = (1 - weight) * current_gap + weight * gap
                        self.preference_patterns['spacing_preferences']['horizontal_gap']['sub_branch'] = new_gap

    def _update_layout_direction_preferences(self, session: LayoutSession) -> None:
        """更新布局方向偏好"""

        layout_type = session.layout_type
        adjustment_count = len(session.adjustments)

        if adjustment_count == 0:
            return

        # 调整次数越少，说明对该布局越满意
        satisfaction_score = max(0.1, 1 - (adjustment_count / 20))

        # 更新偏好
        if layout_type in self.preference_patterns['layout_direction_preference']:
            prefs = self.preference_patterns['layout_direction_preference'][layout_type]

            # 假设当前使用的方向是主要的（可以从session中获取具体方向）
            current_direction = 'TB' if layout_type in ['compactbox', 'dendrogram'] else 'H'

            if current_direction in prefs:
                weight = 0.1
                prefs[current_direction] = (1 - weight) * prefs[current_direction] + weight * satisfaction_score

                # 归一化
                total = sum(prefs.values())
                for key in prefs:
                    prefs[key] = prefs[key] / total

    def _update_aesthetic_preferences(self, adjustments: List[UserAdjustment], session: LayoutSession) -> None:
        """更新美学偏好"""

        # 分析对称性偏好
        if len(adjustments) > 2:
            # 计算调整的对称性
            left_adjustments = [adj for adj in adjustments if adj.adjustment_vector[0] < -10]
            right_adjustments = [adj for adj in adjustments if adj.adjustment_vector[0] > 10]

            if len(left_adjustments) > 0 and len(right_adjustments) > 0:
                # 用户同时在调整左右两侧，说明重视对称性
                symmetry_boost = min(0.1, min(len(left_adjustments), len(right_adjustments)) / 20)
                current = self.preference_patterns['aesthetic_preferences']['symmetry_preference']
                self.preference_patterns['aesthetic_preferences']['symmetry_preference'] = min(1.0, current + symmetry_boost)

        # 分析平衡偏好
        total_adjustment = sum(abs(adj.adjustment_vector[0]) + abs(adj.adjustment_vector[1]) for adj in adjustments)
        avg_adjustment = total_adjustment / len(adjustments) if adjustments else 0

        # 调整幅度适中说明追求平衡
        if 10 <= avg_adjustment <= 50:
            current = self.preference_patterns['aesthetic_preferences']['balance_preference']
            weight = 0.05
            self.preference_patterns['aesthetic_preferences']['balance_preference'] = (1 - weight) * current + weight * 0.8

    def _update_node_size_preferences(self, adjustments: List[UserAdjustment]) -> None:
        """更新节点尺寸偏好"""

        # 简化实现：基于调整频率推断节点大小偏好
        adjustment_counts = Counter(adj.node_type for adj in adjustments)

        for node_type, count in adjustment_counts.items():
            if node_type in ['understanding', 'question', 'explanation']:
                # 调整频繁可能说明尺寸不合适
                if count > 3:
                    scale_adjustment = 1.0 + (count - 3) * 0.05

                    if node_type == 'understanding':
                        key = 'yellow_nodes'
                    elif node_type == 'question':
                        key = 'question_nodes'
                    else:
                        key = 'explanation_nodes'

                    current_width_scale = self.preference_patterns['node_size_adjustments'][key]['width_scale']
                    current_height_scale = self.preference_patterns['node_size_adjustments'][key]['height_scale']

                    weight = 0.1
                    self.preference_patterns['node_size_adjustments'][key]['width_scale'] = (
                        (1 - weight) * current_width_scale + weight * scale_adjustment
                    )
                    self.preference_patterns['node_size_adjustments'][key]['height_scale'] = (
                        (1 - weight) * current_height_scale + weight * scale_adjustment
                    )

    def end_session(self, session_id: str) -> Dict[str, Any]:
        """结束会话"""

        session = self._find_session_by_id(session_id)
        if not session:
            raise ValueError(f"会话不存在: {session_id}")

        session.end_time = datetime.now().isoformat()
        session.final_preferences = self.get_current_preferences()

        self._save_session(session)

        # 生成会话总结
        summary = self._generate_session_summary(session)

        print(f"🏁 会话结束: {session_id}")
        print(f"⏱️ 会话时长: {summary['duration_minutes']:.1f} 分钟")
        print(f"📊 总调整次数: {summary['total_adjustments']}")
        print(f"🎯 主要调整类型: {summary['most_adjusted_type']}")

        return summary

    def _generate_session_summary(self, session: LayoutSession) -> Dict[str, Any]:
        """生成会话总结"""

        start_time = datetime.fromisoformat(session.start_time)
        end_time = datetime.fromisoformat(session.end_time) if session.end_time else datetime.now()
        duration_minutes = (end_time - start_time).total_seconds() / 60

        # 统计调整类型
        adjustment_types = Counter(adj.node_type for adj in session.adjustments)
        most_adjusted_type = adjustment_types.most_common(1)[0][0] if adjustment_types else '无'

        # 计算平均调整幅度
        if session.adjustments:
            avg_adjustment_x = sum(abs(adj.adjustment_vector[0]) for adj in session.adjustments) / len(session.adjustments)
            avg_adjustment_y = sum(abs(adj.adjustment_vector[1]) for adj in session.adjustments) / len(session.adjustments)
        else:
            avg_adjustment_x = avg_adjustment_y = 0

        return {
            'session_id': session.session_id,
            'duration_minutes': duration_minutes,
            'total_adjustments': len(session.adjustments),
            'most_adjusted_type': most_adjusted_type,
            'adjustment_breakdown': dict(adjustment_types),
            'avg_adjustment_magnitude': (avg_adjustment_x, avg_adjustment_y),
            'layout_type': session.layout_type,
            'canvas_file': session.canvas_file
        }

    def learn_layout_preferences(self) -> Dict[str, Any]:
        """学习布局偏好模式"""

        # 基于所有历史数据学习偏好
        preferences = {
            'yellow_node_alignment': self._learn_yellow_alignment_preference(),
            'spacing_preferences': self._learn_spacing_preferences(),
            'layout_direction_preference': self._learn_direction_preference(),
            'aesthetic_preferences': self._learn_aesthetic_preferences(),
            'node_size_preferences': self._learn_node_size_preferences(),
            'confidence_scores': self._calculate_confidence_scores()
        }

        return preferences

    def _learn_yellow_alignment_preference(self) -> Dict[str, Any]:
        """学习黄色节点对齐偏好"""

        yellow_adjustments = [adj for adj in self.adjustment_history if adj.node_type == 'understanding']

        if not yellow_adjustments:
            return self.preference_patterns['yellow_node_alignment']

        # 分析对齐模式
        left_moves = sum(1 for adj in yellow_adjustments if adj.adjustment_vector[0] < -10)
        right_moves = sum(1 for adj in yellow_adjustments if adj.adjustment_vector[0] > 10)
        center_moves = sum(1 for adj in yellow_adjustments if abs(adj.adjustment_vector[0]) <= 10)

        total_moves = left_moves + right_moves + center_moves

        if total_moves == 0:
            alignment_preference = 'strict_center'
        elif left_moves > right_moves * 1.5:
            alignment_preference = 'left_aligned'
        elif right_moves > left_moves * 1.5:
            alignment_preference = 'right_aligned'
        else:
            alignment_preference = 'strict_center'

        # 计算偏移量
        offsets_x = []
        offsets_y = []

        for adj in yellow_adjustments:
            parent_info = adj.context.get('parent_info')
            if parent_info:
                parent_x, parent_y = parent_info['position']
                parent_width, parent_height = parent_info['size']

                ideal_center_x = parent_x + parent_width / 2
                actual_center_x = adj.new_position[0] + adj.context['node_size'][0] / 2

                offset_x = actual_center_x - ideal_center_x
                offset_y = adj.new_position[1] - (parent_y + parent_height)

                offsets_x.append(offset_x)
                offsets_y.append(offset_y)

        avg_offset_x = sum(offsets_x) / len(offsets_x) if offsets_x else 0
        avg_offset_y = sum(offsets_y) / len(offsets_y) if offsets_y else 30

        return {
            'preferred_alignment': alignment_preference,
            'preferred_offset_x': avg_offset_x,
            'preferred_offset_y': avg_offset_y,
            'alignment_strictness': max(0.1, 1 - (len(set(left_moves for adj in yellow_adjustments if adj.adjustment_vector[0] < -10)) / max(1, len(yellow_adjustments)))),
            'sample_size': len(yellow_adjustments)
        }

    def _learn_spacing_preferences(self) -> Dict[str, Any]:
        """学习间距偏好"""
        return self.preference_patterns['spacing_preferences']

    def _learn_direction_preference(self) -> Dict[str, Any]:
        """学习布局方向偏好"""
        return self.preference_patterns['layout_direction_preference']

    def _learn_aesthetic_preferences(self) -> Dict[str, Any]:
        """学习美学偏好"""
        return self.preference_patterns['aesthetic_preferences']

    def _learn_node_size_preferences(self) -> Dict[str, Any]:
        """学习节点尺寸偏好"""
        return self.preference_patterns['node_size_adjustments']

    def _calculate_confidence_scores(self) -> Dict[str, float]:
        """计算偏好置信度"""

        total_adjustments = len(self.adjustment_history)
        if total_adjustments == 0:
            return {'overall': 0.0}

        # 基于样本量计算置信度
        base_confidence = min(1.0, total_adjustments / 50)

        # 各类偏好的置信度
        yellow_adjustments = sum(1 for adj in self.adjustment_history if adj.node_type == 'understanding')
        yellow_confidence = min(1.0, yellow_adjustments / 20) if yellow_adjustments > 0 else 0.0

        session_count = len(self.sessions)
        session_confidence = min(1.0, session_count / 10)

        return {
            'overall': base_confidence,
            'yellow_alignment': yellow_confidence,
            'layout_direction': session_confidence,
            'sample_size': total_adjustments
        }

    def get_current_preferences(self) -> Dict[str, Any]:
        """获取当前偏好设置"""
        return {
            'preferences': self.preference_patterns,
            'confidence_scores': self._calculate_confidence_scores(),
            'statistics': {
                'total_adjustments': len(self.adjustment_history),
                'total_sessions': len(self.sessions),
                'last_updated': datetime.now().isoformat()
            }
        }

    def apply_preferences_to_optimizer(self, optimizer) -> None:
        """将学习到的偏好应用到布局优化器"""

        if hasattr(optimizer, 'update_preferences'):
            optimizer.update_preferences(self.preference_patterns)

    def _find_session_by_id(self, session_id: str) -> Optional[LayoutSession]:
        """根据ID查找会话"""
        for session in self.sessions:
            if session.session_id == session_id:
                return session
        return None

    def _save_session(self, session: LayoutSession) -> None:
        """保存会话数据"""
        session_file = os.path.join(self.data_dir, "sessions", f"{session.session_id}.json")
        session_data = self._serialize_session(session)

        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

    def _save_preferences(self) -> None:
        """保存偏好数据"""
        preferences_file = os.path.join(self.data_dir, "preferences", "learned_preferences.json")

        with open(preferences_file, 'w', encoding='utf-8') as f:
            json.dump(self.preference_patterns, f, ensure_ascii=False, indent=2)

    def _serialize_session(self, session: LayoutSession) -> Dict[str, Any]:
        """序列化会话"""
        return {
            'session_id': session.session_id,
            'start_time': session.start_time,
            'end_time': session.end_time,
            'canvas_file': session.canvas_file,
            'layout_type': session.layout_type,
            'adjustments': [
                {
                    'timestamp': adj.timestamp,
                    'node_id': adj.node_id,
                    'node_type': adj.node_type,
                    'original_position': adj.original_position,
                    'new_position': adj.new_position,
                    'adjustment_vector': adj.adjustment_vector,
                    'context': adj.context
                }
                for adj in session.adjustments
            ],
            'final_preferences': session.final_preferences
        }

    def _deserialize_session(self, session_data: Dict[str, Any]) -> Optional[LayoutSession]:
        """反序列化会话"""
        try:
            adjustments = []
            for adj_data in session_data.get('adjustments', []):
                adjustment = UserAdjustment(
                    timestamp=adj_data['timestamp'],
                    node_id=adj_data['node_id'],
                    node_type=adj_data['node_type'],
                    original_position=tuple(adj_data['original_position']),
                    new_position=tuple(adj_data['new_position']),
                    adjustment_vector=tuple(adj_data['adjustment_vector']),
                    context=adj_data['context']
                )
                adjustments.append(adjustment)

            return LayoutSession(
                session_id=session_data['session_id'],
                start_time=session_data['start_time'],
                end_time=session_data.get('end_time'),
                canvas_file=session_data['canvas_file'],
                layout_type=session_data['layout_type'],
                adjustments=adjustments,
                final_preferences=session_data.get('final_preferences')
            )
        except Exception as e:
            print(f"⚠️ 反序列化会话失败: {e}")
            return None

    def export_learning_data(self, output_file: str = None) -> str:
        """导出学习数据"""

        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.data_dir, f"layout_learning_export_{timestamp}.json")

        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_sessions': len(self.sessions),
            'total_adjustments': len(self.adjustment_history),
            'learned_preferences': self.preference_patterns,
            'confidence_scores': self._calculate_confidence_scores(),
            'sessions_summary': [
                {
                    'session_id': session.session_id,
                    'layout_type': session.layout_type,
                    'adjustment_count': len(session.adjustments),
                    'duration_minutes': (
                        (datetime.fromisoformat(session.end_time or datetime.now().isoformat()) -
                         datetime.fromisoformat(session.start_time)).total_seconds() / 60
                        if session.end_time else 0
                    )
                }
                for session in self.sessions[-10:]  # 最近10个会话
            ]
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        print(f"📤 学习数据已导出: {output_file}")
        return output_file


# 测试和演示代码
def main():
    """主函数 - 演示偏好学习系统"""

    print("🧠 Canvas学习系统 - G6布局偏好学习系统")
    print("=" * 50)

    # 创建学习器
    learner = G6LayoutPreferenceLearner()

    # 显示当前偏好
    current_prefs = learner.get_current_preferences()
    print(f"📊 当前学习状态:")
    print(f"   总调整次数: {current_prefs['statistics']['total_adjustments']}")
    print(f"   总会话数: {current_prefs['statistics']['total_sessions']}")
    print(f"   置信度: {current_prefs['confidence_scores']['overall']:.2f}")

    # 演示新会话
    print("\n🎯 演示新会话...")
    session_id = learner.start_new_session(
        "C:/Users/ROG/托福/笔记库/测试/test-canvas-g6-layout-20251018.canvas",
        "compactbox"
    )

    # 模拟用户调整（这里只是演示，实际应该从真实的Canvas文件对比中获取）
    print("\n📝 模拟用户调整...")

    # 模拟一些调整数据
    mock_adjustments = [
        {
            'node_id': 'understanding-1',
            'node_type': 'understanding',
            'original_position': (600, 230),
            'new_position': (590, 235),  # 稍微左移
            'context': {
                'parent_info': {
                    'id': 'question-1-basic',
                    'position': (600, 80),
                    'size': (350, 120)
                },
                'node_size': (300, 150)
            }
        }
    ]

    # 这里应该传入真实的Canvas数据对比
    # learner.record_user_adjustment(session_id, canvas_before, canvas_after, adjusted_node_ids)

    # 结束会话
    summary = learner.end_session(session_id)
    print(f"\n📈 会话总结:")
    print(f"   会话ID: {summary['session_id']}")
    print(f"   调整次数: {summary['total_adjustments']}")
    print(f"   主要调整类型: {summary['most_adjusted_type']}")

    # 导出学习数据
    export_file = learner.export_learning_data()

    print(f"\n✅ 偏好学习系统演示完成!")
    print(f"📤 数据导出: {export_file}")


if __name__ == "__main__":
    main()