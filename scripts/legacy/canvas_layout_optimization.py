"""
Canvas节点智能布局优化算法核心功能

Story 8.3 的最小实现，包含所有验收标准的核心功能。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import json
import tempfile
import os
import time
import math

# ========== 布局优化常量 ==========

# 对齐方式
LAYOUT_OPTIMIZATION_ALIGNMENT_LEFT = "left"
LAYOUT_OPTIMIZATION_ALIGNMENT_CENTER = "center"
LAYOUT_OPTIMIZATION_ALIGNMENT_RIGHT = "right"
LAYOUT_OPTIMIZATION_DEFAULT_ALIGNMENT = "center"

# 性能参数
LAYOUT_OPTIMIZATION_TARGET_TIME_MS = 2000
LAYOUT_OPTIMIZATION_OVERLAP_THRESHOLD = 5
LAYOUT_OPTIMIZATION_MIN_SPACING = 20

# 质量评估参数
LAYOUT_QUALITY_WEIGHT_ALIGNMENT = 0.3
LAYOUT_QUALITY_WEIGHT_SPACING = 0.25
LAYOUT_QUALITY_WEIGHT_OVERLAP = 0.25
LAYOUT_QUALITY_WEIGHT_CLUSTERING = 0.2
LAYOUT_QUALITY_TARGET_SCORE = 8.0

# 节点尺寸常量
DEFAULT_NODE_WIDTH = 400
DEFAULT_NODE_HEIGHT = 300
QUESTION_NODE_HEIGHT = 120
YELLOW_NODE_WIDTH = 350
YELLOW_NODE_HEIGHT = 150
YELLOW_OFFSET_Y = 30

# 颜色常量
COLOR_RED = "1"
COLOR_GREEN = "2"
COLOR_PURPLE = "3"
COLOR_BLUE = "5"
COLOR_YELLOW = "6"


@dataclass
class LayoutPreferences:
    """用户布局偏好配置类"""
    alignment_mode: str = LAYOUT_OPTIMIZATION_DEFAULT_ALIGNMENT
    spacing_settings: Dict[str, int] = field(default_factory=lambda: {
        "horizontal_spacing": 450,
        "vertical_spacing": 380,
        "yellow_offset_y": YELLOW_OFFSET_Y,
        "auto_adjust_spacing": True
    })
    clustering_settings: Dict[str, Any] = field(default_factory=lambda: {
        "enable_clustering": True,
        "cluster_spacing": 100,
        "same_topic_grouping": True
    })
    visual_preferences: Dict[str, bool] = field(default_factory=lambda: {
        "prevent_overlap": True,
        "optimize_aesthetics": True,
        "maintain_logic_flow": True
    })

    def validate_preferences(self) -> bool:
        """验证偏好设置的有效性"""
        valid_alignments = [
            LAYOUT_OPTIMIZATION_ALIGNMENT_LEFT,
            LAYOUT_OPTIMIZATION_ALIGNMENT_CENTER,
            LAYOUT_OPTIMIZATION_ALIGNMENT_RIGHT
        ]

        if self.alignment_mode not in valid_alignments:
            return False

        for key, value in self.spacing_settings.items():
            if isinstance(value, int) and value < 0:
                return False

        return True

    def get_alignment_offset(self, question_width: int, yellow_width: int) -> int:
        """根据对齐模式计算黄色节点的水平偏移"""
        if self.alignment_mode == LAYOUT_OPTIMIZATION_ALIGNMENT_LEFT:
            return 0
        elif self.alignment_mode == LAYOUT_OPTIMIZATION_ALIGNMENT_CENTER:
            return (question_width - yellow_width) // 2
        elif self.alignment_mode == LAYOUT_OPTIMIZATION_ALIGNMENT_RIGHT:
            return question_width - yellow_width
        else:
            return 0


@dataclass
class LayoutSnapshot:
    """布局快照类"""
    snapshot_id: str
    timestamp: str
    canvas_data: Dict[str, Any]
    layout_description: str
    user_action: str
    optimization_stats: Optional[Dict[str, Any]] = None


@dataclass
class LayoutOptimizationResult:
    """布局优化结果类"""
    optimization_id: str
    canvas_path: str
    original_stats: Dict[str, Any]
    optimized_stats: Dict[str, Any]
    changes_made: List[str]
    optimization_time_ms: int
    quality_score: float
    success: bool = True
    error_message: Optional[str] = None


class LayoutOptimizer:
    """Canvas布局优化器"""

    def __init__(self, canvas_data: Dict[str, Any], preferences: Optional[LayoutPreferences] = None):
        """初始化布局优化器"""
        self.canvas_data = canvas_data
        self.preferences = preferences or LayoutPreferences()
        self.nodes = canvas_data.get("nodes", [])
        self.edges = canvas_data.get("edges", [])
        self.node_map = {node["id"]: node for node in self.nodes}

    def calculate_yellow_position(self, question_node: Dict[str, Any], alignment: Optional[str] = None) -> Dict[str, int]:
        """计算黄色节点的精确位置（支持多种对齐方式）"""
        actual_alignment = alignment or self.preferences.alignment_mode

        question_x = question_node.get("x", 0)
        question_y = question_node.get("y", 0)
        question_width = question_node.get("width", DEFAULT_NODE_WIDTH)

        # 计算黄色节点X坐标（根据对齐方式）
        if actual_alignment == LAYOUT_OPTIMIZATION_ALIGNMENT_LEFT:
            yellow_x = question_x
        elif actual_alignment == LAYOUT_OPTIMIZATION_ALIGNMENT_CENTER:
            yellow_x = question_x + (question_width - YELLOW_NODE_WIDTH) // 2
        elif actual_alignment == LAYOUT_OPTIMIZATION_ALIGNMENT_RIGHT:
            yellow_x = question_x + question_width - YELLOW_NODE_WIDTH
        else:
            # 默认使用水平对齐
            yellow_x = question_x + 50

        # 计算黄色节点Y坐标（严格位于问题节点正下方30px处）
        yellow_y = question_y + QUESTION_NODE_HEIGHT + self.preferences.spacing_settings["yellow_offset_y"]

        return {"x": yellow_x, "y": yellow_y}

    def detect_node_overlaps(self) -> List[Dict[str, Any]]:
        """检测节点重叠情况"""
        overlaps = []

        for i, node1 in enumerate(self.nodes):
            for node2 in self.nodes[i+1:]:
                if self._check_nodes_overlap(node1, node2):
                    overlaps.append({
                        "node1_id": node1["id"],
                        "node2_id": node2["id"],
                        "overlap_area": self._calculate_overlap_area(node1, node2),
                        "node1_rect": self._get_node_rect(node1),
                        "node2_rect": self._get_node_rect(node2)
                    })

        return overlaps

    def adjust_node_spacing(self, prevent_overlap: bool = True) -> List[str]:
        """调整节点间距，避免重叠"""
        changes_made = []

        if prevent_overlap:
            overlaps = self.detect_node_overlaps()

            for overlap in overlaps:
                node1_id = overlap["node1_id"]
                node2_id = overlap["node2_id"]

                if self._fix_node_overlap(node1_id, node2_id):
                    changes_made.append(f"修复了节点 {node1_id} 和 {node2_id} 的重叠")

        return changes_made

    def cluster_similar_nodes(self, enable_clustering: bool = True) -> List[str]:
        """聚类相似节点，分组排列"""
        if not enable_clustering:
            return []

        changes_made = []

        # 简单的基于颜色的聚类
        color_clusters = self._group_nodes_by_color()

        for color, nodes in color_clusters.items():
            if len(nodes) > 1:
                # 对聚类内的节点进行位置优化
                cluster_changes = self._optimize_cluster_layout(nodes)
                changes_made.extend(cluster_changes)

        return changes_made

    def calculate_layout_score(self) -> float:
        """计算布局质量评分（1-10分）"""
        return self._calculate_layout_quality_score()

    def optimize_canvas_layout(self, optimize_mode: str = "auto") -> LayoutOptimizationResult:
        """优化Canvas布局"""
        start_time = time.time()
        optimization_id = f"opt-{int(time.time())}"

        try:
            # 1. 记录原始统计
            original_stats = self._calculate_layout_stats()

            # 2. 执行优化步骤
            changes_made = []

            if optimize_mode in ["auto", "alignment"]:
                alignment_changes = self._optimize_node_alignment()
                changes_made.extend(alignment_changes)

            if optimize_mode in ["auto", "spacing"]:
                spacing_changes = self.adjust_node_spacing(True)
                changes_made.extend(spacing_changes)

            if optimize_mode in ["auto", "clustering"] and self.preferences.clustering_settings["enable_clustering"]:
                clustering_changes = self.cluster_similar_nodes(True)
                changes_made.extend(clustering_changes)

            # 3. 计算优化后统计
            optimized_stats = self._calculate_layout_stats()
            optimization_time_ms = int((time.time() - start_time) * 1000)
            quality_score = self._calculate_layout_quality_score()

            # 4. 构建结果
            result = LayoutOptimizationResult(
                optimization_id=optimization_id,
                canvas_path="",  # 将在调用处设置
                original_stats=original_stats,
                optimized_stats=optimized_stats,
                changes_made=changes_made,
                optimization_time_ms=optimization_time_ms,
                quality_score=quality_score,
                success=True
            )

            return result

        except Exception as e:
            optimization_time_ms = int((time.time() - start_time) * 1000)

            return LayoutOptimizationResult(
                optimization_id=optimization_id,
                canvas_path="",
                original_stats={},
                optimized_stats={},
                changes_made=[],
                optimization_time_ms=optimization_time_ms,
                quality_score=0.0,
                success=False,
                error_message=str(e)
            )

    # ========== 私有辅助方法 ==========

    def _calculate_layout_stats(self) -> Dict[str, Any]:
        """计算布局统计信息"""
        return {
            "total_nodes": len(self.nodes),
            "overlap_count": len(self.detect_node_overlaps()),
            "aesthetics_score": self._calculate_aesthetics_score(),
            "alignment_score": self._calculate_alignment_score(),
            "spacing_score": self._calculate_spacing_score()
        }

    def _calculate_layout_quality_score(self) -> float:
        """计算综合布局质量分数"""
        alignment_score = self._calculate_alignment_score()
        spacing_score = self._calculate_spacing_score()
        overlap_score = self._calculate_overlap_score()
        clustering_score = self._calculate_clustering_score()

        # 加权计算总分
        total_score = (
            alignment_score * LAYOUT_QUALITY_WEIGHT_ALIGNMENT +
            spacing_score * LAYOUT_QUALITY_WEIGHT_SPACING +
            overlap_score * LAYOUT_QUALITY_WEIGHT_OVERLAP +
            clustering_score * LAYOUT_QUALITY_WEIGHT_CLUSTERING
        )

        return min(10.0, max(0.0, total_score))

    def _calculate_alignment_score(self) -> float:
        """计算对齐质量分数"""
        question_yellow_pairs = self._find_question_yellow_pairs()

        if not question_yellow_pairs:
            return 10.0

        aligned_count = 0
        for question_node, yellow_node in question_yellow_pairs:
            expected_pos = self.calculate_yellow_position(question_node)
            actual_x = yellow_node.get("x", 0)
            expected_x = expected_pos["x"]

            # 允许1px的误差
            if abs(actual_x - expected_x) <= 1:
                aligned_count += 1

        return (aligned_count / len(question_yellow_pairs)) * 10.0

    def _calculate_spacing_score(self) -> float:
        """计算间距质量分数"""
        total_spacing_score = 0
        spacing_count = 0

        for i, node1 in enumerate(self.nodes):
            for node2 in self.nodes[i+1:]:
                distance = self._calculate_node_distance(node1, node2)
                if distance > 0:
                    ideal_spacing = self._calculate_ideal_spacing(node1, node2)
                    spacing_ratio = min(distance / ideal_spacing, 2.0)
                    spacing_score = 1.0 - abs(1.0 - spacing_ratio)
                    total_spacing_score += spacing_score
                    spacing_count += 1

        return (total_spacing_score / spacing_count * 10.0) if spacing_count > 0 else 10.0

    def _calculate_overlap_score(self) -> float:
        """计算重叠避免分数"""
        overlaps = self.detect_node_overlaps()
        max_possible_overlaps = len(self.nodes) * (len(self.nodes) - 1) // 2

        if max_possible_overlaps == 0:
            return 10.0

        overlap_penalty = len(overlaps) / max_possible_overlaps
        return (1.0 - overlap_penalty) * 10.0

    def _calculate_clustering_score(self) -> float:
        """计算聚类质量分数"""
        if not self.preferences.clustering_settings["enable_clustering"]:
            return 8.0

        # 基于颜色聚类的简单评分
        color_clusters = self._group_nodes_by_color()
        cluster_score = 0

        for color, nodes in color_clusters.items():
            if len(nodes) > 1:
                cluster_tightness = self._calculate_cluster_tightness(nodes)
                cluster_score += cluster_tightness

        average_cluster_score = cluster_score / len(color_clusters) if color_clusters else 8.0
        return min(10.0, average_cluster_score * 10.0)

    def _calculate_aesthetics_score(self) -> float:
        """计算美观度分数"""
        alignment = self._calculate_alignment_score()
        spacing = self._calculate_spacing_score()
        return (alignment + spacing) / 2

    def _check_nodes_overlap(self, node1: Dict, node2: Dict) -> bool:
        """检查两个节点是否重叠"""
        rect1 = self._get_node_rect(node1)
        rect2 = self._get_node_rect(node2)

        return not (
            rect1["right"] <= rect2["left"] + LAYOUT_OPTIMIZATION_OVERLAP_THRESHOLD or
            rect2["right"] <= rect1["left"] + LAYOUT_OPTIMIZATION_OVERLAP_THRESHOLD or
            rect1["bottom"] <= rect2["top"] + LAYOUT_OPTIMIZATION_OVERLAP_THRESHOLD or
            rect2["bottom"] <= rect1["top"] + LAYOUT_OPTIMIZATION_OVERLAP_THRESHOLD
        )

    def _get_node_rect(self, node: Dict) -> Dict[str, int]:
        """获取节点的矩形边界"""
        return {
            "left": node.get("x", 0),
            "top": node.get("y", 0),
            "right": node.get("x", 0) + node.get("width", DEFAULT_NODE_WIDTH),
            "bottom": node.get("y", 0) + node.get("height", DEFAULT_NODE_HEIGHT)
        }

    def _calculate_overlap_area(self, node1: Dict, node2: Dict) -> int:
        """计算两个节点重叠的面积"""
        rect1 = self._get_node_rect(node1)
        rect2 = self._get_node_rect(node2)

        overlap_width = min(rect1["right"], rect2["right"]) - max(rect1["left"], rect2["left"])
        overlap_height = min(rect1["bottom"], rect2["bottom"]) - max(rect1["top"], rect2["top"])

        if overlap_width > 0 and overlap_height > 0:
            return overlap_width * overlap_height
        return 0

    def _calculate_node_distance(self, node1: Dict, node2: Dict) -> float:
        """计算两个节点之间的欧几里得距离"""
        x1, y1 = node1.get("x", 0), node1.get("y", 0)
        x2, y2 = node2.get("x", 0), node2.get("y", 0)

        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def _calculate_ideal_spacing(self, node1: Dict, node2: Dict) -> float:
        """计算两个节点之间的理想间距"""
        avg_width = (node1.get("width", DEFAULT_NODE_WIDTH) + node2.get("width", DEFAULT_NODE_WIDTH)) / 2
        avg_height = (node1.get("height", DEFAULT_NODE_HEIGHT) + node2.get("height", DEFAULT_NODE_HEIGHT)) / 2

        return max(avg_width, avg_height) * 0.5

    def _find_question_yellow_pairs(self) -> List[Tuple[Dict, Dict]]:
        """查找问题-黄色节点对"""
        pairs = []

        for edge in self.edges:
            from_node_id = edge.get("fromNode")
            to_node_id = edge.get("toNode")

            if from_node_id in self.node_map and to_node_id in self.node_map:
                from_node = self.node_map[from_node_id]
                to_node = self.node_map[to_node_id]

                # 检查是否为问题到黄色的连接
                if (from_node.get("color") in [COLOR_RED, COLOR_GREEN, COLOR_PURPLE] and
                    to_node.get("color") == COLOR_YELLOW):
                    pairs.append((from_node, to_node))

        return pairs

    def _group_nodes_by_color(self) -> Dict[str, List[Dict]]:
        """按颜色分组节点"""
        color_groups = {}

        for node in self.nodes:
            color = node.get("color", "")
            if color not in color_groups:
                color_groups[color] = []
            color_groups[color].append(node)

        return color_groups

    def _calculate_cluster_tightness(self, nodes: List[Dict]) -> float:
        """计算聚类内节点的紧密程度"""
        if len(nodes) <= 1:
            return 1.0

        total_distance = 0
        pair_count = 0

        for i, node1 in enumerate(nodes):
            for node2 in nodes[i+1:]:
                distance = self._calculate_node_distance(node1, node2)
                total_distance += distance
                pair_count += 1

        avg_distance = total_distance / pair_count

        # 理想聚类距离是基于节点大小的函数
        avg_node_size = sum(
            (node.get("width", DEFAULT_NODE_WIDTH) + node.get("height", DEFAULT_NODE_HEIGHT)) / 2
            for node in nodes
        ) / len(nodes)

        ideal_distance = avg_node_size * 2

        # 紧密度 = 1 - |实际距离/理想距离 - 1|
        tightness = 1.0 - abs(avg_distance / ideal_distance - 1.0)
        return max(0.0, min(1.0, tightness))

    def _fix_node_overlap(self, node1_id: str, node2_id: str) -> bool:
        """修复两个节点的重叠"""
        if node1_id not in self.node_map or node2_id not in self.node_map:
            return False

        node1 = self.node_map[node1_id]
        node2 = self.node_map[node2_id]

        # 简单的重叠修复：移动node2
        rect1 = self._get_node_rect(node1)
        rect2 = self._get_node_rect(node2)

        # 计算移动方向和距离
        move_x = max(0, rect1["right"] - rect2["left"] + LAYOUT_OPTIMIZATION_MIN_SPACING)
        move_y = max(0, rect1["bottom"] - rect2["top"] + LAYOUT_OPTIMIZATION_MIN_SPACING)

        # 选择较小的移动距离
        if move_x > 0 and move_y > 0:
            if move_x < move_y:
                node2["x"] += move_x
            else:
                node2["y"] += move_y
        elif move_x > 0:
            node2["x"] += move_x
        elif move_y > 0:
            node2["y"] += move_y

        return True

    def _optimize_cluster_layout(self, nodes: List[Dict]) -> List[str]:
        """优化聚类内节点的布局"""
        # 这里可以实现聚类布局优化算法
        # 目前返回空列表，表示没有执行聚类优化
        return []

    def _optimize_node_alignment(self) -> List[str]:
        """优化节点对齐"""
        changes = []

        # 修复黄色节点的对齐
        question_yellow_pairs = self._find_question_yellow_pairs()

        for question_node, yellow_node in question_yellow_pairs:
            expected_pos = self.calculate_yellow_position(question_node)
            actual_x = yellow_node.get("x", 0)
            expected_x = expected_pos["x"]

            if abs(actual_x - expected_x) > 1:
                yellow_node["x"] = expected_x
                changes.append(f"调整黄色节点 {yellow_node['id']} 的水平位置到 {expected_x}")

        return changes


class CanvasJSONOperator:
    """简化的Canvas JSON操作器"""

    @staticmethod
    def read_canvas(canvas_path: str) -> Dict[str, Any]:
        """读取Canvas文件"""
        try:
            with open(canvas_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise FileNotFoundError(f"无法读取Canvas文件 {canvas_path}: {e}")

    @staticmethod
    def write_canvas(canvas_path: str, canvas_data: Dict[str, Any]) -> bool:
        """写入Canvas文件"""
        try:
            with open(canvas_path, 'w', encoding='utf-8') as f:
                json.dump(canvas_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"写入Canvas文件失败: {e}")
            return False

    @staticmethod
    def find_node_by_id(canvas_data: Dict[str, Any], node_id: str) -> Optional[Dict[str, Any]]:
        """根据ID查找节点"""
        for node in canvas_data.get("nodes", []):
            if node.get("id") == node_id:
                return node
        return None


class CanvasBusinessLogic:
    """Canvas业务逻辑层"""

    def __init__(self, canvas_path: str):
        """初始化Canvas业务逻辑"""
        self.canvas_path = canvas_path
        self.canvas_data = CanvasJSONOperator.read_canvas(canvas_path)

    def calculate_yellow_position(
        self,
        question_node: Dict[str, Any],
        alignment: str = LAYOUT_OPTIMIZATION_DEFAULT_ALIGNMENT
    ) -> Dict[str, int]:
        """计算黄色节点的精确位置（支持多种对齐方式）"""
        # 验证对齐方式
        valid_alignments = [
            LAYOUT_OPTIMIZATION_ALIGNMENT_LEFT,
            LAYOUT_OPTIMIZATION_ALIGNMENT_CENTER,
            LAYOUT_OPTIMIZATION_ALIGNMENT_RIGHT
        ]

        if alignment not in valid_alignments:
            raise ValueError(f"无效的对齐方式: {alignment}")

        # 获取问题节点参数
        question_x = question_node.get("x", 0)
        question_y = question_node.get("y", 0)
        question_width = question_node.get("width", DEFAULT_NODE_WIDTH)

        # 计算黄色节点X坐标（根据对齐方式）
        if alignment == LAYOUT_OPTIMIZATION_ALIGNMENT_LEFT:
            yellow_x = question_x
        elif alignment == LAYOUT_OPTIMIZATION_ALIGNMENT_CENTER:
            yellow_x = question_x + (question_width - YELLOW_NODE_WIDTH) // 2
        elif alignment == LAYOUT_OPTIMIZATION_ALIGNMENT_RIGHT:
            yellow_x = question_x + question_width - YELLOW_NODE_WIDTH
        else:
            yellow_x = question_x + 50

        # 计算黄色节点Y坐标（严格位于问题节点正下方30px处）
        yellow_y = question_y + QUESTION_NODE_HEIGHT + YELLOW_OFFSET_Y

        return {"x": yellow_x, "y": yellow_y}

    def optimize_canvas_layout(
        self,
        preferences: Optional[LayoutPreferences] = None,
        optimize_mode: str = "auto"
    ) -> LayoutOptimizationResult:
        """优化Canvas布局的高级接口"""
        # 验证优化模式
        valid_modes = ["auto", "alignment", "spacing", "clustering"]
        if optimize_mode not in valid_modes:
            raise ValueError(f"无效的优化模式: {optimize_mode}")

        # 使用默认偏好或提供的偏好
        actual_preferences = preferences or LayoutPreferences()

        # 创建布局优化器
        optimizer = LayoutOptimizer(self.canvas_data, actual_preferences)

        # 执行布局优化
        result = optimizer.optimize_canvas_layout(optimize_mode)
        result.canvas_path = self.canvas_path

        # 如果优化成功，保存Canvas
        if result.success:
            CanvasJSONOperator.write_canvas(self.canvas_path, self.canvas_data)

        return result

    def get_layout_optimization_suggestions(self) -> List[str]:
        """获取布局优化建议"""
        suggestions = []

        # 创建优化器进行布局分析
        optimizer = LayoutOptimizer(self.canvas_data)

        # 检查重叠
        overlaps = optimizer.detect_node_overlaps()
        if overlaps:
            suggestions.append(f"发现 {len(overlaps)} 个节点重叠，建议运行间距优化")

        # 检查对齐
        alignment_score = optimizer._calculate_alignment_score()
        if alignment_score < 8.0:
            suggestions.append("部分黄色节点对齐不精确，建议运行对齐优化")

        # 检查间距
        spacing_score = optimizer._calculate_spacing_score()
        if spacing_score < 7.0:
            suggestions.append("节点间距不够均匀，建议运行间距优化")

        # 检查整体质量
        overall_score = optimizer.calculate_layout_score()
        if overall_score < LAYOUT_QUALITY_TARGET_SCORE:
            suggestions.append(
                f"布局质量分数 {overall_score:.1f}/10，建议运行综合优化以提升到 {LAYOUT_QUALITY_TARGET_SCORE}/10"
            )

        if not suggestions:
            suggestions.append("当前布局质量良好，无需优化")

        return suggestions

    def create_layout_snapshot(self, description: str = "") -> str:
        """创建当前布局的快照"""
        snapshot_id = f"snap-{int(time.time())}"
        timestamp = f"{int(time.time())}"

        # 创建快照对象
        snapshot = LayoutSnapshot(
            snapshot_id=snapshot_id,
            timestamp=timestamp,
            canvas_data=self.canvas_data.copy(),
            layout_description=description or f"布局快照 - {timestamp}",
            user_action="手动创建快照"
        )

        # TODO: 实现快照持久化存储
        # 目前只返回ID
        return snapshot_id

    def restore_layout_snapshot(self, snapshot_id: str) -> bool:
        """恢复到指定的布局快照"""
        # TODO: 实现快照加载和恢复逻辑
        # 目前返回False，表示功能尚未完全实现
        return False


class CanvasOrchestrator:
    """Canvas操作的高级接口"""

    def __init__(self, canvas_path: str):
        """初始化Canvas编排器"""
        self.canvas_path = canvas_path
        self.logic = CanvasBusinessLogic(canvas_path)

    def optimize_canvas_layout(
        self,
        preferences: Optional[LayoutPreferences] = None,
        optimize_mode: str = "auto",
        create_backup: bool = True
    ) -> LayoutOptimizationResult:
        """优化Canvas布局的高级接口"""
        # 创建备份（如果需要）
        backup_id = None
        if create_backup:
            backup_id = self.logic.create_layout_snapshot("布局优化前自动备份")

        try:
            # 调用业务逻辑层的优化方法
            result = self.logic.optimize_canvas_layout(preferences, optimize_mode)

            # 添加备份信息到结果
            if hasattr(result, 'optimization_stats') and result.optimization_stats is None:
                result.optimization_stats = {}

            if backup_id:
                result.optimization_stats['backup_id'] = backup_id

            return result

        except Exception as e:
            # 返回失败结果
            return LayoutOptimizationResult(
                optimization_id=f"failed-{int(time.time())}",
                canvas_path=self.canvas_path,
                original_stats={},
                optimized_stats={},
                changes_made=[],
                optimization_time_ms=0,
                quality_score=0.0,
                success=False,
                error_message=str(e)
            )

    def get_layout_optimization_suggestions(self) -> List[str]:
        """获取布局优化建议"""
        return self.logic.get_layout_optimization_suggestions()

    def create_layout_snapshot(self, description: str = "") -> str:
        """创建布局快照"""
        return self.logic.create_layout_snapshot(description)

    def restore_layout_snapshot(self, snapshot_id: str) -> bool:
        """恢复布局快照"""
        return self.logic.restore_layout_snapshot(snapshot_id)