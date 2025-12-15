"""
关键节点提取器 - 动态检验白板系统 (Story 8.16)

从源Canvas中智能提取关键节点，支持基于颜色、评分和知识图谱上下文的综合分析。

Author: Canvas Learning System Team
Version: 1.0 (Story 8.16)
Created: 2025-01-22
"""

import json
import os
import uuid
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# 尝试导入现有模块
try:
    from canvas_utils import (
        COLOR_CODE_RED, COLOR_CODE_GREEN, COLOR_CODE_PURPLE,
        COLOR_CODE_BLUE, COLOR_CODE_YELLOW,
        COLOR_SEMANTICS, COLOR_DESCRIPTIONS
    )
    from canvas_utils import CanvasJSONOperator
except ImportError:
    # 如果无法导入，定义本地常量
    COLOR_CODE_RED = "4"
    COLOR_CODE_GREEN = "2"
    COLOR_CODE_PURPLE = "3"
    COLOR_CODE_BLUE = "5"
    COLOR_CODE_YELLOW = "6"

    COLOR_SEMANTICS = {
        "4": "red",
        "2": "green",
        "3": "purple",
        "5": "blue",
        "6": "yellow"
    }

    COLOR_DESCRIPTIONS = {
        "4": "不理解/未通过评分 (红色)",
        "2": "完全理解/已通过评分 (≥80分)",
        "3": "似懂非懂/待检验 (60-79分)",
        "5": "AI生成的补充解释",
        "6": "用户个人理解输出区"
    }

    class CanvasJSONOperator:
        @staticmethod
        def read_canvas(canvas_path: str) -> Dict:
            with open(canvas_path, 'r', encoding='utf-8') as f:
                return json.load(f)

# 尝试导入loguru
try:
    from loguru import logger
    LOGURU_ENABLED = True
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    LOGURU_ENABLED = False


@dataclass
class CriticalNode:
    """关键节点数据结构"""
    node_id: str
    color: str
    concept_name: str
    confidence_score: float
    mastery_estimation: float
    reason_for_critical: str
    text_content: str = ""
    x_position: int = 0
    y_position: int = 0
    width: int = 400
    height: int = 300
    related_concepts: List[str] = field(default_factory=list)
    learning_dependencies: Dict[str, float] = field(default_factory=dict)
    extraction_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SourceAnalysis:
    """源分析数据结构"""
    canvas_id: str
    extraction_algorithm: str
    total_source_nodes: int
    critical_nodes_extracted: List[CriticalNode]
    knowledge_graph_context: Dict[str, Any]
    extraction_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class CriticalNodesExtractor:
    """
    关键节点提取器

    实现基于多种策略的智能节点提取算法：
    1. 基于颜色和评分的节点筛选
    2. 知识图谱上下文分析
    3. 掌握度估算算法
    4. 学习依赖关系分析
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化关键节点提取器

        Args:
            config: 配置参数，包含权重和阈值设置
        """
        self.config = config or self._get_default_config()

        # 提取算法权重
        self.extraction_weights = {
            "color_weight": self.config.get("color_weight", 0.4),
            "mastery_weight": self.config.get("mastery_weight", 0.3),
            "context_weight": self.config.get("context_weight", 0.2),
            "dependency_weight": self.config.get("dependency_weight", 0.1)
        }

        # 掌握度估算参数
        self.mastery_params = {
            "red_base_mastery": self.config.get("red_base_mastery", 0.2),
            "purple_base_mastery": self.config.get("purple_base_mastery", 0.6),
            "yellow_bonus": self.config.get("yellow_bonus", 0.1),
            "blue_bonus": self.config.get("blue_bonus", 0.15)
        }

        if LOGURU_ENABLED:
            logger.info("CriticalNodesExtractor initialized with config", extra={"config": self.config})

    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "color_weight": 0.4,
            "mastery_weight": 0.3,
            "context_weight": 0.2,
            "dependency_weight": 0.1,

            # 节点提取配置
            "critical_colors": [COLOR_CODE_RED, COLOR_CODE_PURPLE],
            "confidence_threshold": 0.7,
            "mastery_threshold": 0.7,

            # 掌握度估算参数
            "red_base_mastery": 0.2,
            "purple_base_mastery": 0.6,
            "yellow_bonus": 0.1,
            "blue_bonus": 0.15,

            # 知识图谱配置
            "enable_knowledge_graph": False,
            "kg_context_weight": 0.3,
            "related_concepts_limit": 5
        }

    def extract_critical_nodes(self, source_canvas_path: str) -> SourceAnalysis:
        """
        提取关键节点 - 主要入口函数

        Args:
            source_canvas_path: 源Canvas文件路径

        Returns:
            SourceAnalysis: 源分析结果

        Raises:
            FileNotFoundError: Canvas文件不存在
            ValueError: Canvas文件格式错误
        """
        if not os.path.exists(source_canvas_path):
            error_msg = f"Canvas文件不存在: {source_canvas_path}"
            if LOGURU_ENABLED:
                logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        try:
            # 读取Canvas文件
            canvas_data = CanvasJSONOperator.read_canvas(source_canvas_path)

            if LOGURU_ENABLED:
                logger.info(f"开始提取关键节点", extra={
                    "canvas_path": source_canvas_path,
                    "total_nodes": len(canvas_data.get("nodes", []))
                })

            # 提取候选节点
            candidate_nodes = self._extract_candidate_nodes(canvas_data)

            # 计算关键性评分
            scored_nodes = self._calculate_criticality_scores(candidate_nodes, canvas_data)

            # 筛选关键节点
            critical_nodes = self._filter_critical_nodes(scored_nodes)

            # 分析知识图谱上下文
            kg_context = self._analyze_knowledge_graph_context(critical_nodes, canvas_data)

            # 生成源分析结果
            analysis = SourceAnalysis(
                canvas_id=self._generate_canvas_id(source_canvas_path),
                extraction_algorithm="intelligent_node_identification",
                total_source_nodes=len(canvas_data.get("nodes", [])),
                critical_nodes_extracted=critical_nodes,
                knowledge_graph_context=kg_context
            )

            if LOGURU_ENABLED:
                logger.info(f"关键节点提取完成", extra={
                    "total_nodes": analysis.total_source_nodes,
                    "critical_nodes": len(critical_nodes),
                    "extraction_rate": len(critical_nodes) / analysis.total_source_nodes if analysis.total_source_nodes > 0 else 0
                })

            return analysis

        except Exception as e:
            error_msg = f"关键节点提取失败: {str(e)}"
            if LOGURU_ENABLED:
                logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg) from e

    def _extract_candidate_nodes(self, canvas_data: Dict) -> List[Dict]:
        """
        提取候选节点

        Args:
            canvas_data: Canvas数据

        Returns:
            List[Dict]: 候选节点列表
        """
        nodes = canvas_data.get("nodes", [])
        candidate_nodes = []
        critical_colors = self.config.get("critical_colors", [COLOR_CODE_RED, COLOR_CODE_PURPLE])

        for node in nodes:
            # 检查节点类型和颜色
            if node.get("type") != "text":
                continue

            color = node.get("color")
            if color not in critical_colors:
                continue

            # 检查文本内容长度
            text = node.get("text", "").strip()
            if len(text) < 10:  # 过滤太短的节点
                continue

            candidate_nodes.append(node)

        return candidate_nodes

    def _calculate_criticality_scores(self, candidate_nodes: List[Dict], canvas_data: Dict) -> List[Tuple[Dict, float]]:
        """
        计算节点关键性评分

        Args:
            candidate_nodes: 候选节点列表
            canvas_data: Canvas完整数据

        Returns:
            List[Tuple[Dict, float]]: 带评分的节点列表
        """
        scored_nodes = []

        for node in candidate_nodes:
            try:
                # 基础颜色评分
                color_score = self._calculate_color_score(node)

                # 掌握度评分
                mastery_score = self._calculate_mastery_score(node, canvas_data)

                # 上下文评分
                context_score = self._calculate_context_score(node, canvas_data)

                # 依赖关系评分
                dependency_score = self._calculate_dependency_score(node, canvas_data)

                # 综合评分
                total_score = (
                    color_score * self.extraction_weights["color_weight"] +
                    mastery_score * self.extraction_weights["mastery_weight"] +
                    context_score * self.extraction_weights["context_weight"] +
                    dependency_score * self.extraction_weights["dependency_weight"]
                )

                scored_nodes.append((node, total_score))

            except Exception as e:
                if LOGURU_ENABLED:
                    logger.warning(f"计算节点评分失败: {str(e)}", extra={"node_id": node.get("id")})
                continue

        # 按评分降序排序
        scored_nodes.sort(key=lambda x: x[1], reverse=True)
        return scored_nodes

    def _calculate_color_score(self, node: Dict) -> float:
        """
        计算颜色评分

        Args:
            node: 节点数据

        Returns:
            float: 颜色评分 (0-1)
        """
        color = node.get("color")

        # 红色节点最重要，紫色节点次之
        if color == COLOR_CODE_RED:
            return 1.0
        elif color == COLOR_CODE_PURPLE:
            return 0.8
        else:
            return 0.3

    def _calculate_mastery_score(self, node: Dict, canvas_data: Dict) -> float:
        """
        计算掌握度评分

        Args:
            node: 节点数据
            canvas_data: Canvas完整数据

        Returns:
            float: 掌握度评分 (0-1，越高表示掌握度越低，越需要关注)
        """
        mastery_estimation = self._estimate_mastery_level(node, canvas_data)

        # 掌握度越低，评分越高（越需要关注）
        return 1.0 - mastery_estimation

    def _calculate_context_score(self, node: Dict, canvas_data: Dict) -> float:
        """
        计算上下文评分

        Args:
            node: 节点数据
            canvas_data: Canvas完整数据

        Returns:
            float: 上下文评分 (0-1)
        """
        # 基于节点连接数计算上下文重要性
        node_id = node.get("id")
        edges = canvas_data.get("edges", [])

        connection_count = 0
        for edge in edges:
            if edge.get("fromNode") == node_id or edge.get("toNode") == node_id:
                connection_count += 1

        # 连接数越多，重要性越高
        return min(connection_count / 5.0, 1.0)  # 标准化到0-1

    def _calculate_dependency_score(self, node: Dict, canvas_data: Dict) -> float:
        """
        计算依赖关系评分

        Args:
            node: 节点数据
            canvas_data: Canvas完整数据

        Returns:
            float: 依赖关系评分 (0-1)
        """
        # 简化实现：基于节点位置估算依赖关系
        # 在实际实现中，这里可以集成更复杂的依赖分析算法

        x, y = node.get("x", 0), node.get("y", 0)
        nodes = canvas_data.get("nodes", [])

        # 计算周围节点密度
        nearby_nodes = 0
        for other_node in nodes:
            if other_node.get("id") == node.get("id"):
                continue

            other_x, other_y = other_node.get("x", 0), other_node.get("y", 0)
            distance = ((x - other_x) ** 2 + (y - other_y) ** 2) ** 0.5

            if distance < 500:  # 500像素范围内
                nearby_nodes += 1

        # 周围节点越多，依赖关系越复杂，评分越高
        return min(nearby_nodes / 8.0, 1.0)

    def _filter_critical_nodes(self, scored_nodes: List[Tuple[Dict, float]]) -> List[CriticalNode]:
        """
        筛选关键节点

        Args:
            scored_nodes: 带评分的节点列表

        Returns:
            List[CriticalNode]: 关键节点列表
        """
        confidence_threshold = self.config.get("confidence_threshold", 0.7)
        critical_nodes = []

        for node, score in scored_nodes:
            if score >= confidence_threshold:
                try:
                    # 创建CriticalNode对象
                    critical_node = self._create_critical_node(node, score)
                    critical_nodes.append(critical_node)
                except Exception as e:
                    if LOGURU_ENABLED:
                        logger.warning(f"创建关键节点失败: {str(e)}", extra={"node_id": node.get("id")})
                    continue

        return critical_nodes

    def _create_critical_node(self, node: Dict, criticality_score: float) -> CriticalNode:
        """
        创建关键节点对象

        Args:
            node: 原始节点数据
            criticality_score: 关键性评分

        Returns:
            CriticalNode: 关键节点对象
        """
        node_id = node.get("id", f"node-{uuid.uuid4().hex[:16]}")
        color = node.get("color", COLOR_CODE_RED)
        text = node.get("text", "").strip()

        # 提取概念名称（取文本的前50个字符作为概念名称）
        concept_name = text[:50] + "..." if len(text) > 50 else text

        # 估算掌握度
        mastery_estimation = self._estimate_mastery_level(node, {})

        # 确定关键原因
        reason_for_critical = self._determine_critical_reason(color, mastery_estimation)

        return CriticalNode(
            node_id=node_id,
            color=color,
            concept_name=concept_name,
            confidence_score=criticality_score,
            mastery_estimation=mastery_estimation,
            reason_for_critical=reason_for_critical,
            text_content=text,
            x_position=node.get("x", 0),
            y_position=node.get("y", 0),
            width=node.get("width", 400),
            height=node.get("height", 300)
        )

    def _estimate_mastery_level(self, node: Dict, canvas_data: Dict) -> float:
        """
        估算掌握度

        Args:
            node: 节点数据
            canvas_data: Canvas数据

        Returns:
            float: 掌握度估算 (0-1)
        """
        color = node.get("color")
        params = self.mastery_params

        # 基础掌握度
        if color == COLOR_CODE_RED:
            base_mastery = params["red_base_mastery"]
        elif color == COLOR_CODE_PURPLE:
            base_mastery = params["purple_base_mastery"]
        else:
            base_mastery = 0.8  # 其他颜色默认较高掌握度

        # 检查是否有相关黄色节点（用户理解输出）
        node_id = node.get("id")
        if self._has_related_yellow_node(node_id, canvas_data):
            base_mastery += params["yellow_bonus"]

        # 检查是否有蓝色节点（AI解释）
        if self._has_related_blue_node(node_id, canvas_data):
            base_mastery += params["blue_bonus"]

        return min(base_mastery, 1.0)

    def _has_related_yellow_node(self, node_id: str, canvas_data: Dict) -> bool:
        """检查是否有相关的黄色节点"""
        nodes = canvas_data.get("nodes", [])
        for node in nodes:
            if (node.get("color") == COLOR_CODE_YELLOW and
                node.get("type") == "text"):
                # 简化实现：检查黄色节点的文本是否包含相关关键词
                text = node.get("text", "").lower()
                # 在实际实现中，这里可以更精确地判断关联性
                return len(text) > 20  # 简单的启发式规则
        return False

    def _has_related_blue_node(self, node_id: str, canvas_data: Dict) -> bool:
        """检查是否有相关的蓝色节点"""
        nodes = canvas_data.get("nodes", [])
        for node in nodes:
            if node.get("color") == COLOR_CODE_BLUE and node.get("type") == "text":
                # 简化实现：检查蓝色节点数量
                return True
        return False

    def _determine_critical_reason(self, color: str, mastery_estimation: float) -> str:
        """
        确定关键原因

        Args:
            color: 节点颜色
            mastery_estimation: 掌握度估算

        Returns:
            str: 关键原因描述
        """
        if color == COLOR_CODE_RED:
            return "用户评分<60分，多次复习仍未掌握"
        elif color == COLOR_CODE_PURPLE:
            if mastery_estimation < 0.5:
                return "评分60-79分，理解深度不足"
            else:
                return "评分60-79分，需要进一步验证"
        else:
            return "其他原因需要关注"

    def _analyze_knowledge_graph_context(self, critical_nodes: List[CriticalNode], canvas_data: Dict) -> Dict[str, Any]:
        """
        分析知识图谱上下文

        Args:
            critical_nodes: 关键节点列表
            canvas_data: Canvas数据

        Returns:
            Dict[str, Any]: 知识图谱上下文信息
        """
        kg_context = {
            "related_concepts": {},
            "learning_dependencies": {},
            "concept_clusters": {}
        }

        # 分析相关概念
        for node in critical_nodes:
            concept_name = node.concept_name
            related = self._find_related_concepts(node, canvas_data)
            kg_context["related_concepts"][concept_name] = related[:5]  # 限制最多5个相关概念

        # 分析学习依赖
        kg_context["learning_dependencies"] = self._analyze_learning_dependencies(critical_nodes, canvas_data)

        # 概念聚类分析
        kg_context["concept_clusters"] = self._cluster_concepts(critical_nodes, canvas_data)

        return kg_context

    def _find_related_concepts(self, node: CriticalNode, canvas_data: Dict) -> List[str]:
        """查找相关概念"""
        related_concepts = []
        nodes = canvas_data.get("nodes", [])

        # 基于文本相似性查找相关概念（简化实现）
        node_text = node.text_content.lower()
        node_words = set(node_text.split())

        for other_node in nodes:
            if other_node.get("id") == node.node_id:
                continue

            other_text = other_node.get("text", "").lower()
            other_words = set(other_text.split())

            # 计算词汇重叠度
            common_words = node_words & other_words
            if len(common_words) >= 2:  # 至少有2个共同词汇
                related_concepts.append(other_text[:30] + "..." if len(other_text) > 30 else other_text)

        return related_concepts[:5]  # 返回最多5个相关概念

    def _analyze_learning_dependencies(self, critical_nodes: List[CriticalNode], canvas_data: Dict) -> Dict[str, float]:
        """分析学习依赖关系"""
        dependencies = {}

        # 简化实现：基于概念名称的相似性估算依赖关系
        for i, node1 in enumerate(critical_nodes):
            for node2 in critical_nodes[i+1:]:
                similarity = self._calculate_concept_similarity(node1.concept_name, node2.concept_name)
                if similarity > 0.3:  # 相似度阈值
                    dependencies[f"{node1.concept_name}→{node2.concept_name}"] = similarity

        return dependencies

    def _calculate_concept_similarity(self, concept1: str, concept2: str) -> float:
        """计算概念相似度"""
        words1 = set(concept1.lower().split())
        words2 = set(concept2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def _cluster_concepts(self, critical_nodes: List[CriticalNode], canvas_data: Dict) -> Dict[str, List[str]]:
        """概念聚类分析"""
        clusters = {}

        # 简化实现：基于颜色分组
        for node in critical_nodes:
            color_name = COLOR_SEMANTICS.get(node.color, "unknown")
            if color_name not in clusters:
                clusters[color_name] = []
            clusters[color_name].append(node.concept_name)

        return clusters

    def _generate_canvas_id(self, canvas_path: str) -> str:
        """生成Canvas ID"""
        path = Path(canvas_path)
        return f"canvas-{path.stem}-{uuid.uuid4().hex[:16]}"


# 便利函数
def extract_critical_nodes(canvas_path: str, config: Optional[Dict] = None) -> SourceAnalysis:
    """
    便利函数：提取关键节点

    Args:
        canvas_path: Canvas文件路径
        config: 可选配置

    Returns:
        SourceAnalysis: 提取结果
    """
    extractor = CriticalNodesExtractor(config)
    return extractor.extract_critical_nodes(canvas_path)


if __name__ == "__main__":
    # 简单测试
    test_canvas = "test_canvas.canvas"
    if os.path.exists(test_canvas):
        result = extract_critical_nodes(test_canvas)
        print(f"提取到 {len(result.critical_nodes_extracted)} 个关键节点")
    else:
        print(f"测试Canvas文件不存在: {test_canvas}")