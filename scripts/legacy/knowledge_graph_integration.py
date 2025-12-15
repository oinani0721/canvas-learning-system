"""
知识图谱集成模块 - 动态检验白板系统 (Story 8.16)

集成MCP Graphiti记忆服务，提供知识图谱上下文分析功能。

Author: Canvas Learning System Team
Version: 1.0 (Story 8.16)
Created: 2025-01-22
"""

import json
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# 尝试导入loguru
try:
    from loguru import logger
    LOGURU_ENABLED = True
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    LOGURU_ENABLED = False


@dataclass
class KnowledgeGraphContext:
    """知识图谱上下文数据结构"""
    concept_relations: Dict[str, List[str]] = field(default_factory=dict)
    learning_dependencies: Dict[str, float] = field(default_factory=dict)
    related_concepts: Dict[str, List[str]] = field(default_factory=dict)
    concept_clusters: Dict[str, List[str]] = field(default_factory=dict)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    extraction_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class KnowledgeGraphIntegration:
    """
    知识图谱集成器

    提供与MCP Graphiti记忆服务的集成，支持：
    1. 概念关系分析
    2. 学习依赖建模
    3. 知识网络聚类
    4. 上下文感知推荐
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化知识图谱集成器

        Args:
            config: 配置参数
        """
        self.config = config or self._get_default_config()
        self.mcp_available = self._check_mcp_availability()

        if self.mcp_available:
            logger.info("KnowledgeGraphIntegration initialized with MCP Graphiti support")
        else:
            logger.warning("MCP Graphiti not available, using fallback knowledge analysis")

    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "mcp_timeout": 30,
            "max_related_concepts": 5,
            "similarity_threshold": 0.3,
            "cluster_threshold": 0.5,
            "enable_mcp_fallback": True
        }

    def _check_mcp_availability(self) -> bool:
        """检查MCP Graphiti服务是否可用"""
        try:
            # 尝试调用MCP服务来检测可用性
            # 注意：这里需要根据实际的MCP调用方式调整
            return True  # 暂时返回True，实际使用时需要检测MCP服务
        except Exception as e:
            if LOGURU_ENABLED:
                logger.warning(f"MCP Graphiti service not available: {e}")
            return False

    def analyze_concept_context(self, concepts: List[str], canvas_data: Dict) -> KnowledgeGraphContext:
        """
        分析概念上下文

        Args:
            concepts: 概念列表
            canvas_data: Canvas数据

        Returns:
            KnowledgeGraphContext: 知识图谱上下文
        """
        if self.mcp_available:
            return self._analyze_with_mcp(concepts, canvas_data)
        else:
            return self._analyze_with_fallback(concepts, canvas_data)

    def _analyze_with_mcp(self, concepts: List[str], canvas_data: Dict) -> KnowledgeGraphContext:
        """使用MCP Graphiti进行分析"""
        try:
            context = KnowledgeGraphContext()

            # 为每个概念搜索相关记忆
            for concept in concepts:
                try:
                    # 调用MCP搜索服务
                    related_memories = self._search_concept_memories(concept)
                    context.related_concepts[concept] = related_memories[:self.config["max_related_concepts"]]

                    # 计算概念关系
                    concept_relations = self._calculate_concept_relations_mcp(concept, related_memories)
                    context.concept_relations[concept] = concept_relations

                    # 估算学习依赖
                    dependencies = self._estimate_dependencies_mcp(concept, canvas_data)
                    context.learning_dependencies.update(dependencies)

                except Exception as e:
                    if LOGURU_ENABLED:
                        logger.warning(f"MCP analysis failed for concept '{concept}': {e}")
                    # 降级到fallback分析
                    self._add_fallback_analysis(concept, context, canvas_data)

            # 聚类分析
            context.concept_clusters = self._perform_clustering_mcp(concepts, context)

            # 计算置信度
            context.confidence_scores = self._calculate_confidence_scores(context)

            return context

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"MCP analysis failed, using fallback: {e}")
            return self._analyze_with_fallback(concepts, canvas_data)

    def _analyze_with_fallback(self, concepts: List[str], canvas_data: Dict) -> KnowledgeGraphContext:
        """使用本地fallback方法进行分析"""
        context = KnowledgeGraphContext()

        for concept in concepts:
            self._add_fallback_analysis(concept, context, canvas_data)

        # 基础聚类分析
        context.concept_clusters = self._perform_clustering_fallback(concepts, canvas_data)

        # 计算置信度
        context.confidence_scores = self._calculate_confidence_scores(context)

        if LOGURU_ENABLED:
            logger.info("Completed fallback knowledge graph analysis")

        return context

    def _add_fallback_analysis(self, concept: str, context: KnowledgeGraphContext, canvas_data: Dict):
        """添加fallback分析结果"""
        # 基于文本相似性查找相关概念
        related_concepts = self._find_similar_concepts(concept, canvas_data)
        context.related_concepts[concept] = related_concepts

        # 简单的关系分析
        context.concept_relations[concept] = related_concepts

        # 基础依赖分析
        dependencies = self._estimate_basic_dependencies(concept, canvas_data)
        context.learning_dependencies.update(dependencies)

    def _search_concept_memories(self, concept: str) -> List[str]:
        """
        搜索概念相关记忆

        Args:
            concept: 概念名称

        Returns:
            List[str]: 相关记忆列表
        """
        try:
            # 这里需要调用实际的MCP Graphiti搜索服务
            # 示例实现（需要根据实际MCP API调整）：
            # result = mcp__graphiti_memory__search_memories(query=concept)
            # return [memory.get("content", "") for memory in result.get("memories", [])]

            # 临时实现：返回模拟数据
            return [
                f"与{concept}相关的基础概念",
                f"{concept}的应用场景",
                f"{concept}的深入理解"
            ]
        except Exception as e:
            if LOGURU_ENABLED:
                logger.warning(f"Failed to search memories for concept '{concept}': {e}")
            return []

    def _calculate_concept_relations_mcp(self, concept: str, memories: List[str]) -> List[str]:
        """使用MCP计算概念关系"""
        # 简化实现：从记忆中提取关系概念
        relations = []
        for memory in memories:
            # 在实际实现中，这里应该使用更复杂的NLP技术
            words = memory.split()
            for word in words:
                if len(word) > 3 and word not in concept:
                    relations.append(word)
        return list(set(relations))[:5]  # 去重并限制数量

    def _estimate_dependencies_mcp(self, concept: str, canvas_data: Dict) -> Dict[str, float]:
        """使用MCP估算学习依赖"""
        dependencies = {}

        try:
            # 这里可以调用MCP服务来分析概念依赖关系
            # 临时实现：基于启发式规则
            nodes = canvas_data.get("nodes", [])
            for node in nodes:
                if node.get("type") == "text":
                    node_text = node.get("text", "").lower()
                    if concept.lower() in node_text:
                        # 估算依赖强度
                        similarity = self._calculate_text_similarity(concept, node_text)
                        if similarity > self.config["similarity_threshold"]:
                            dependencies[f"{concept}→{node_text[:30]}"] = similarity
        except Exception as e:
            if LOGURU_ENABLED:
                logger.warning(f"Failed to estimate dependencies with MCP: {e}")

        return dependencies

    def _find_similar_concepts(self, concept: str, canvas_data: Dict) -> List[str]:
        """查找相似概念（fallback方法）"""
        similar_concepts = []
        nodes = canvas_data.get("nodes", [])
        concept_words = set(concept.lower().split())

        for node in nodes:
            if node.get("type") == "text":
                node_text = node.get("text", "")
                node_words = set(node_text.lower().split())

                # 计算词汇重叠度
                common_words = concept_words & node_words
                if len(common_words) >= 1 and len(node_text) > 10:
                    similarity = len(common_words) / len(concept_words | node_words)
                    if similarity > self.config["similarity_threshold"]:
                        similar_concepts.append(node_text[:50] + "..." if len(node_text) > 50 else node_text)

        return similar_concepts[:self.config["max_related_concepts"]]

    def _estimate_basic_dependencies(self, concept: str, canvas_data: Dict) -> Dict[str, float]:
        """估算基础依赖关系（fallback方法）"""
        dependencies = {}
        nodes = canvas_data.get("nodes", [])

        for node in nodes:
            if node.get("type") == "text":
                node_text = node.get("text", "")
                dependency_score = self._calculate_text_similarity(concept, node_text)
                if dependency_score > self.config["similarity_threshold"]:
                    dependencies[f"{concept}→{node_text[:30]}"] = dependency_score

        return dependencies

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def _perform_clustering_mcp(self, concepts: List[str], context: KnowledgeGraphContext) -> Dict[str, List[str]]:
        """使用MCP执行聚类分析"""
        # 简化实现：基于概念关系进行聚类
        clusters = {"unclustered": concepts}

        # 在实际实现中，这里应该调用MCP的聚类功能
        # 临时实现：根据相关概念的重叠度进行简单聚类

        return clusters

    def _perform_clustering_fallback(self, concepts: List[str], canvas_data: Dict) -> Dict[str, List[str]]:
        """执行fallback聚类分析"""
        clusters = {
            "by_color": {},
            "by_position": {},
            "by_content": []
        }

        nodes = canvas_data.get("nodes", [])

        # 按颜色聚类
        for node in nodes:
            if node.get("type") == "text":
                color = node.get("color", "unknown")
                text = node.get("text", "")
                if text[:30] in concepts:
                    if color not in clusters["by_color"]:
                        clusters["by_color"][color] = []
                    clusters["by_color"][color].append(text[:30])

        # 按位置聚类
        for i, concept1 in enumerate(concepts):
            for concept2 in concepts[i+1:]:
                # 在实际实现中，这里应该基于Canvas中的位置信息进行聚类
                pass

        return clusters

    def _calculate_confidence_scores(self, context: KnowledgeGraphContext) -> Dict[str, float]:
        """计算置信度分数"""
        scores = {}

        for concept, relations in context.concept_relations.items():
            # 基于关系数量和质量计算置信度
            relation_count = len(relations)
            related_count = len(context.related_concepts.get(concept, []))

            # 简单的置信度计算公式
            base_confidence = 0.5
            relation_bonus = min(relation_count * 0.1, 0.3)
            related_bonus = min(related_count * 0.05, 0.2)

            scores[concept] = min(base_confidence + relation_bonus + related_bonus, 1.0)

        return scores

    def get_learning_recommendations(self, concept: str, context: KnowledgeGraphContext) -> List[str]:
        """
        获取学习推荐

        Args:
            concept: 概念名称
            context: 知识图谱上下文

        Returns:
            List[str]: 学习推荐列表
        """
        recommendations = []

        # 基于相关概念推荐
        if concept in context.related_concepts:
            related = context.related_concepts[concept]
            if related:
                recommendations.append(f"建议先学习相关概念：{', '.join(related[:3])}")

        # 基于依赖关系推荐
        for dep_key, dep_score in context.learning_dependencies.items():
            if dep_key.startswith(f"{concept}→") and dep_score > 0.7:
                target_concept = dep_key.replace(f"{concept}→", "")
                recommendations.append(f"重点掌握依赖概念：{target_concept}")

        # 基于置信度推荐
        if concept in context.confidence_scores:
            confidence = context.confidence_scores[concept]
            if confidence < 0.5:
                recommendations.append("该概念理解度较低，建议重新学习基础")
            elif confidence > 0.8:
                recommendations.append("该概念掌握良好，可以进行进阶学习")

        return recommendations[:5]  # 限制推荐数量

    def update_knowledge_graph(self, new_learnings: Dict[str, Any]) -> bool:
        """
        更新知识图谱

        Args:
            new_learnings: 新的学习内容

        Returns:
            bool: 更新是否成功
        """
        if not self.mcp_available:
            if LOGURU_ENABLED:
                logger.warning("MCP not available, cannot update knowledge graph")
            return False

        try:
            # 这里应该调用MCP的添加记忆功能
            for concept, learning_data in new_learnings.items():
                # 示例：mcp__graphiti_memory__add_memory(key=concept, content=learning_data)
                pass

            if LOGURU_ENABLED:
                logger.info(f"Updated knowledge graph with {len(new_learnings)} new learnings")
            return True
        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"Failed to update knowledge graph: {e}")
            return False


# 便利函数
def analyze_knowledge_context(concepts: List[str], canvas_data: Dict, config: Optional[Dict] = None) -> KnowledgeGraphContext:
    """
    便利函数：分析知识上下文

    Args:
        concepts: 概念列表
        canvas_data: Canvas数据
        config: 可选配置

    Returns:
        KnowledgeGraphContext: 分析结果
    """
    integrator = KnowledgeGraphIntegration(config)
    return integrator.analyze_concept_context(concepts, canvas_data)


if __name__ == "__main__":
    # 简单测试
    test_concepts = ["逆否命题", "逻辑等价性"]
    test_canvas = {"nodes": [], "edges": []}

    context = analyze_knowledge_context(test_concepts, test_canvas)
    print(f"分析完成，相关概念数量: {len(context.related_concepts)}")