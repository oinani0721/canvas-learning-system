#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Canvas学习系统v2.0 - 核心功能模块 (工作版本)

该模块包含v2.0纠正版的核心功能，专注于原始Story和PRD设计要求：
1. CanvasLearningMemory - 基于Graphiti的时间感知学习记忆系统
2. ReviewBoardAgentSelector - 检验白板智能调度
3. EfficientCanvasProcessor - 学习效率处理器

Author: Canvas Learning System Team
Version: 2.0 Corrected Working
Created: 2025-10-20
"""

import asyncio
import datetime
import json
import re
import sys
import math
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

# 尝试导入MCP Graphiti记忆系统
try:
    from mcp_graphiti_memory import add_memory, search_memories, get_memory
    GRAPHITI_AVAILABLE = True
except ImportError:
    print("[WARN] Graphiti MCP not available, using fallback memory system")
    GRAPHITI_AVAILABLE = False

# 尝试导入loguru日志系统
try:
    from loguru import logger
    LOGURU_ENABLED = True
except ImportError:
    print("[INFO] loguru not available, using print statements")
    LOGURU_ENABLED = False

# ============================================================================
# Layer 1: Canvas JSON操作层
# ============================================================================

class CanvasJSONOperator:
    """Canvas文件JSON操作器"""

    def __init__(self):
        """初始化Canvas JSON操作器"""
        if LOGURU_ENABLED:
            logger.debug("CanvasJSONOperator initialized")

    def read_canvas(self, canvas_file: str) -> Optional[Dict[str, Any]]:
        """读取Canvas文件"""
        try:
            canvas_path = Path(canvas_file)
            if not canvas_path.exists():
                if LOGURU_ENABLED:
                    logger.error(f"Canvas文件不存在: {canvas_file}")
                return None

            with open(canvas_path, 'r', encoding='utf-8') as f:
                canvas_data = json.load(f)

            if LOGURU_ENABLED:
                logger.info(f"成功读取Canvas文件: {canvas_file}")

            return canvas_data

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"读取Canvas文件失败: {e}")
            return None

    def write_canvas(self, canvas_file: str, canvas_data: Dict[str, Any]) -> bool:
        """写入Canvas文件"""
        try:
            canvas_path = Path(canvas_file)
            canvas_path.parent.mkdir(parents=True, exist_ok=True)

            with open(canvas_path, 'w', encoding='utf-8') as f:
                json.dump(canvas_data, f, indent=2, ensure_ascii=False)

            if LOGURU_ENABLED:
                logger.info(f"成功写入Canvas文件: {canvas_file}")

            return True

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"写入Canvas文件失败: {e}")
            return False

    def add_node(self, canvas_data: Dict[str, Any], node: Dict[str, Any]) -> bool:
        """添加节点到Canvas"""
        try:
            if "nodes" not in canvas_data:
                canvas_data["nodes"] = []

            canvas_data["nodes"].append(node)
            return True

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"添加节点失败: {e}")
            return False

    def find_nodes_by_color(self, canvas_data: Dict[str, Any], color: str) -> List[Dict[str, Any]]:
        """根据颜色查找节点"""
        try:
            nodes = canvas_data.get("nodes", [])
            return [node for node in nodes if node.get("color") == color]
        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"查找节点失败: {e}")
            return []

# ============================================================================
# v2.0 纠正版核心功能
# ============================================================================

class CanvasLearningMemory:
    """Canvas学习记忆系统 - 基于Graphiti的时间感知学习记忆 (Story 6.1)"""

    def __init__(self):
        """初始化Canvas学习记忆系统"""
        self.graphiti_available = GRAPHITI_AVAILABLE
        self.memory_store = []  # 备用内存存储
        if LOGURU_ENABLED:
            logger.info(f"CanvasLearningMemory initialized, Graphiti available: {self.graphiti_available}")

    async def add_canvas_learning_episode(self, canvas_file: str, learning_data: Dict[str, Any]) -> str:
        """记录Canvas学习会话到记忆系统（Context7验证的核心功能）"""
        try:
            timestamp = datetime.datetime.now().isoformat()
            episode_name = f"Canvas学习: {Path(canvas_file).stem} - {timestamp}"

            # 构建学习内容
            episode_content = self._format_learning_episode_content(canvas_file, learning_data)

            if self.graphiti_available:
                # 使用Graphiti MCP (Context7验证标准)
                result = await add_memory(
                    key=f"canvas_episode_{timestamp}",
                    content=episode_content,
                    metadata={
                        "canvas_file": canvas_file,
                        "learning_type": "canvas_episode",
                        "timestamp": timestamp,
                        "importance": learning_data.get("importance", 7)
                    }
                )
                if LOGURU_ENABLED:
                    logger.info(f"学习片段已记录到Graphiti: {episode_name}")
                return str(result)
            else:
                # 备用存储
                episode = {
                    "name": episode_name,
                    "content": episode_content,
                    "canvas_file": canvas_file,
                    "timestamp": timestamp,
                    "learning_data": learning_data
                }
                self.memory_store.append(episode)
                if LOGURU_ENABLED:
                    logger.info(f"学习片段已记录到本地存储: {episode_name}")
                return f"local_{len(self.memory_store)}"

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"记录学习片段失败: {e}")
            return None

    async def get_canvas_learning_episodes(self, canvas_file: str, last_n: int = 10) -> List[Dict[str, Any]]:
        """获取Canvas学习历史片段"""
        try:
            if self.graphiti_available:
                # 使用Graphiti MCP搜索
                results = await search_memories(f"canvas_file:{canvas_file}")
                return results[:last_n] if results else []
            else:
                # 从本地存储获取
                filtered_episodes = [
                    ep for ep in self.memory_store
                    if ep.get("canvas_file") == canvas_file
                ]
                return filtered_episodes[-last_n:] if filtered_episodes else []

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"获取学习历史失败: {e}")
            return []

    async def track_learning_progress(self, concept: str, mastery_level: float, canvas_file: str) -> bool:
        """追踪学习进度（时间感知功能）"""
        try:
            progress_data = {
                "concept": concept,
                "mastery_level": mastery_level,
                "canvas_file": canvas_file,
                "timestamp": datetime.datetime.now().isoformat()
            }

            if self.graphiti_available:
                await add_memory(
                    key=f"progress_{concept}_{datetime.datetime.now().timestamp()}",
                    content=f"学习进度更新: {concept} - 掌握度{mastery_level:.1f}%",
                    metadata=progress_data
                )
            else:
                self.memory_store.append({
                    "type": "progress",
                    "data": progress_data
                })

            if LOGURU_ENABLED:
                logger.info(f"学习进度已追踪: {concept} - {mastery_level:.1f}%")
            return True

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"学习进度追踪失败: {e}")
            return False

    def _format_learning_episode_content(self, canvas_file: str, learning_data: Dict[str, Any]) -> str:
        """格式化学习片段内容"""
        content = f"""Canvas学习会话
文件: {canvas_file}
时间: {datetime.datetime.now().isoformat()}

学习数据:
{json.dumps(learning_data, ensure_ascii=False, indent=2)}
"""
        return content


class ReviewBoardAgentSelector:
    """检验白板智能Agent选择器 (Story 6.4)"""

    def __init__(self):
        """初始化Agent选择器"""
        if LOGURU_ENABLED:
            logger.info("ReviewBoardAgentSelector initialized")

    def analyze_understanding_quality(self, yellow_node_text: str) -> Dict[str, Any]:
        """分析黄色理解质量（为检验白板决策提供依据）"""
        try:
            word_count = len(yellow_node_text.split()) if yellow_node_text else 0
            char_count = len(yellow_node_text) if yellow_node_text else 0

            # 基础完整性检查
            has_content = word_count > 0
            has_examples = any(keyword in yellow_node_text for keyword in ["例如", "比如", "例子", "例题"])
            has_structure = any(keyword in yellow_node_text for keyword in ["因为", "所以", "首先", "其次", "最后"])

            # 计算质量分数 (0-1)
            quality_score = 0.0
            if has_content:
                quality_score += 0.2  # 有内容
                if word_count >= 10:
                    quality_score += 0.2  # 足够的字数
                if has_examples:
                    quality_score += 0.3  # 有例子
                if has_structure:
                    quality_score += 0.3  # 有结构

            completeness = self._check_basic_completeness(yellow_node_text)

            return {
                "has_content": has_content,
                "word_count": word_count,
                "char_count": char_count,
                "has_examples": has_examples,
                "has_structure": has_structure,
                "completeness": completeness,
                "quality_score": min(1.0, quality_score)
            }

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"理解质量分析失败: {e}")
            return {
                "has_content": False,
                "word_count": 0,
                "quality_score": 0.0,
                "completeness": 0.0,
                "error": str(e)
            }

    def recommend_agents(self, understanding_analysis: Dict[str, Any]) -> List[str]:
        """基于理解质量推荐Agent（检验白板专用）"""
        recommendations = []

        # 检查是否完全空白
        if not understanding_analysis["has_content"]:
            recommendations.append("basic-decomposition")
            return recommendations

        # 检查理解质量
        quality_score = understanding_analysis["quality_score"]
        completeness = understanding_analysis["completeness"]
        word_count = understanding_analysis["word_count"]

        # 基于质量分数推荐 (符合原始Story设计)
        if quality_score < 0.3:
            recommendations.extend(["basic-decomposition", "oral-explanation"])
        elif quality_score < 0.6:
            if completeness < 0.5:
                recommendations.append("four-level-explanation")
            if word_count < 10:
                recommendations.append("oral-explanation")
            recommendations.append("clarification-path")
        elif quality_score < 0.8:
            # 理解不够深入，推荐记忆锚点或例题
            recommendations.extend(["memory-anchor", "example-teaching"])

        return recommendations

    def get_agent_selection_for_review_node(self, yellow_node_text: str) -> Dict[str, Any]:
        """为检验白板节点获取Agent选择建议"""
        analysis = self.analyze_understanding_quality(yellow_node_text)
        recommended_agents = self.recommend_agents(analysis)

        return {
            "understanding_analysis": analysis,
            "recommended_agents": recommended_agents,
            "selection_reason": self._get_selection_reason(analysis, recommended_agents)
        }

    def _check_basic_completeness(self, text: str) -> float:
        """检查基础完整性"""
        if not text:
            return 0.0

        score = 0.0

        # 长度分数 (30%)
        word_count = len(text.split())
        if word_count >= 20:
            score += 0.3
        elif word_count >= 10:
            score += 0.15

        # 例子分数 (40%)
        if any(phrase in text for phrase in ["例如", "比如", "例子", "例题"]):
            score += 0.4

        # 结构化表达分数 (30%)
        if any(phrase in text for phrase in ["因为", "所以", "首先", "其次", "最后"]):
            score += 0.3
        elif any(phrase in text for phrase in ["是", "指", "包括", "分为"]):
            score += 0.15

        return min(1.0, score)

    def _get_selection_reason(self, analysis: Dict[str, Any], agents: List[str]) -> str:
        """获取选择原因"""
        if not analysis["has_content"]:
            return "空白理解，需要基础拆解"

        if analysis["quality_score"] < 0.3:
            return "理解质量低，需要基础解释和结构化指导"
        elif analysis["quality_score"] < 0.6:
            return "理解不够完整，需要深化解释"
        else:
            return "理解基本到位，需要记忆强化和练习"


class EfficientCanvasProcessor:
    """Canvas学习效率处理器 - 简单高效的多节点处理工具 (PRD 2.1.1)"""

    def __init__(self):
        """初始化效率处理器"""
        self.processing_stats = {
            "total_processed": 0,
            "total_failed": 0,
            "total_time": 0.0
        }
        if LOGURU_ENABLED:
            logger.info("EfficientCanvasProcessor initialized")

    async def process_multiple_nodes(self, canvas_file: str, node_ids: List[str], agent_type: str) -> Dict[str, Any]:
        """高效处理多个Canvas节点（简单asyncio并发，符合PRD设计）"""
        try:
            import time
            start_time = time.time()

            if LOGURU_ENABLED:
                logger.info(f"开始处理 {len(node_ids)} 个节点，类型: {agent_type}")

            # 创建任务列表 (简单的asyncio.gather，不是复杂引擎)
            tasks = []
            for node_id in node_ids:
                task = self._process_single_node(canvas_file, node_id, agent_type)
                tasks.append(task)

            # 并发执行 (符合PRD 2.1.1的简单效率工具设计)
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 统计结果
            processed_count = 0
            failed_count = 0
            successful_results = []

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    failed_count += 1
                    if LOGURU_ENABLED:
                        logger.error(f"节点 {node_ids[i]} 处理失败: {result}")
                else:
                    processed_count += 1
                    successful_results.append(result)

            execution_time = time.time() - start_time

            # 更新统计
            self.processing_stats["total_processed"] += processed_count
            self.processing_stats["total_failed"] += failed_count
            self.processing_stats["total_time"] += execution_time

            result = {
                "processed": processed_count,
                "failed": failed_count,
                "total_time": execution_time,
                "node_ids": node_ids,
                "agent_type": agent_type,
                "results": successful_results,
                "success_rate": processed_count / len(node_ids) if node_ids else 0.0
            }

            if LOGURU_ENABLED:
                logger.info(f"处理完成: {processed_count}/{len(node_ids)} 成功，耗时 {execution_time:.2f}s")

            return result

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"批量处理失败: {e}")
            return {
                "processed": 0,
                "failed": len(node_ids),
                "error": str(e),
                "total_time": 0.0
            }

    async def _process_single_node(self, canvas_file: str, node_id: str, agent_type: str) -> Dict[str, Any]:
        """处理单个节点（简化实现）"""
        try:
            # 这里可以调用具体的Agent
            # 为了演示，返回简单的处理结果
            await asyncio.sleep(0.1)  # 模拟处理时间

            return {
                "node_id": node_id,
                "agent_type": agent_type,
                "status": "success",
                "processing_time": 0.1,
                "result": f"Node {node_id} processed by {agent_type}"
            }

        except Exception as e:
            return {
                "node_id": node_id,
                "agent_type": agent_type,
                "status": "error",
                "error": str(e)
            }

    def get_processing_stats(self) -> Dict[str, Any]:
        """获取处理统计"""
        stats = self.processing_stats.copy()
        if stats["total_processed"] > 0:
            stats["average_time_per_node"] = stats["total_time"] / stats["total_processed"]
        else:
            stats["average_time_per_node"] = 0.0

        return stats


# ============================================================================
# 全局控制和管理
# ============================================================================

class GlobalFeatureControls:
    """全局功能控制"""

    def __init__(self):
        """初始化全局控制"""
        self.feature_status = {
            "ultrathink": False,
            "ebbinghaus_review": False,
            "concurrent_agents": False,
            "knowledge_graph": False,
            "smart_clipboard": False,
            "error_monitoring": True
        }
        if LOGURU_ENABLED:
            logger.info("GlobalFeatureControls initialized")

    def is_enabled(self, feature_name: str) -> bool:
        """检查功能是否启用"""
        return self.feature_status.get(feature_name, False)

    def activate_feature(self, keyword: str) -> Dict[str, Any]:
        """激活功能"""
        try:
            feature_map = {
                "*ultrathink": "ultrathink",
                "*review": "ebbinghaus_review",
                "*concurrent": "concurrent_agents",
                "*graph": "knowledge_graph",
                "*clipboard": "smart_clipboard"
            }

            feature = feature_map.get(keyword)
            if feature:
                self.feature_status[feature] = True
                if LOGURU_ENABLED:
                    logger.info(f"功能已激活: {feature}")
                return {"success": True, "feature": feature}
            else:
                return {"success": False, "message": f"未知关键词: {keyword}"}

        except Exception as e:
            return {"success": False, "message": str(e)}


# ============================================================================
# 艾宾浩斯遗忘曲线管理系统 - PRD 2.1.1核心实现
# ============================================================================

@dataclass
class ReviewNode:
    """复习节点数据结构"""
    node_id: str
    concept: str
    create_time: datetime.datetime
    complexity_score: float  # 1.0-10.0
    mastery_level: float    # 0.0-1.0
    last_review_time: Optional[datetime.datetime] = None
    review_count: int = 0
    canvas_file: str = ""

class ForgettingCurveManager:
    """
    艾宾浩斯遗忘曲线管理器

    基于PRD 2.1.1要求实现真正的艾宾浩斯复习算法：
    - 遗忘曲线公式: R(t) = e^(-t/S) 其中S为记忆强度衰减常数
    - 标准复习间隔: 1天、3天、7天、15天、30天
    - 智能Agent调度系统
    """

    def __init__(self):
        """初始化艾宾浩斯遗忘曲线管理器"""
        self.memory_decay_constant = 0.5  # S值，记忆强度衰减常数
        self.standard_intervals = [1, 3, 7, 15, 30]  # 标准艾宾浩斯间隔（天）
        self.review_nodes: Dict[str, ReviewNode] = {}

        if LOGURU_ENABLED:
            logger.info("ForgettingCurveManager initialized with Ebbinghaus algorithm")

    def calculate_memory_strength(self, complexity_score: float) -> float:
        """
        基于复杂度计算记忆强度

        Args:
            complexity_score: 复杂度评分 (1.0-10.0)

        Returns:
            float: 记忆强度系数 (0.1-2.0)
        """
        # 复杂度越高，记忆强度越低（需要更频繁复习）
        # 复杂度1.0 -> 记忆强度2.0（容易记住）
        # 复杂度10.0 -> 记忆强度0.1（难记住）
        strength = max(0.1, 2.0 - (complexity_score - 1.0) * 0.2)
        return strength

    def calculate_retention_rate(self, time_elapsed_days: float, memory_strength: float) -> float:
        """
        计算记忆保持率 R(t) = e^(-t/S)

        Args:
            time_elapsed_days: 经过的时间（天）
            memory_strength: 记忆强度 S 值

        Returns:
            float: 记忆保持率 (0.0-1.0)
        """
        # R(t) = e^(-t/S) 其中 t 是时间，S 是记忆强度
        retention_rate = math.exp(-time_elapsed_days / memory_strength)
        return max(0.0, min(1.0, retention_rate))

    def calculate_optimal_review_times(self, node_create_time: datetime.datetime,
                                     complexity_score: float) -> List[datetime.datetime]:
        """
        基于遗忘曲线计算最优复习时间点

        Args:
            node_create_time: 节点创建时间
            complexity_score: 复杂度评分

        Returns:
            List[datetime.datetime]: 最优复习时间点列表
        """
        memory_strength = self.calculate_memory_strength(complexity_score)
        review_times = []

        for interval in self.standard_intervals:
            # 调整间隔 = 标准间隔 × 记忆强度
            adjusted_interval = interval * memory_strength
            review_time = node_create_time + datetime.timedelta(days=adjusted_interval)
            review_times.append(review_time)

        return review_times

    def should_review_now(self, node: ReviewNode) -> bool:
        """
        判断节点是否需要立即复习

        Args:
            node: 复习节点

        Returns:
            bool: 是否需要复习
        """
        now = datetime.datetime.now()

        # 如果从未复习过，检查第一个复习点
        if node.last_review_time is None:
            optimal_times = self.calculate_optimal_review_times(
                node.create_time,
                node.complexity_score
            )
            if optimal_times and now >= optimal_times[0]:
                return True
            return False

        # 计算距离上次复习的时间
        days_since_review = (now - node.last_review_time).days

        # 基于掌握度确定复习间隔
        if node.mastery_level >= 0.8:  # 掌握得很好
            next_interval = 30  # 30天后复习
        elif node.mastery_level >= 0.6:  # 掌握一般
            next_interval = 15  # 15天后复习
        else:  # 掌握不好
            next_interval = 7   # 7天后复习

        return days_since_review >= next_interval

    def get_retention_status(self, node: ReviewNode) -> Dict[str, Any]:
        """
        获取节点记忆状态

        Args:
            node: 复习节点

        Returns:
            Dict: 包含保持率、建议等信息的字典
        """
        now = datetime.datetime.now()

        if node.last_review_time is None:
            time_elapsed = (now - node.create_time).days
        else:
            time_elapsed = (now - node.last_review_time).days

        memory_strength = self.calculate_memory_strength(node.complexity_score)
        retention_rate = self.calculate_retention_rate(time_elapsed, memory_strength)

        # 基于保持率给出建议
        if retention_rate >= 0.8:
            suggestion = "记忆良好，可以暂缓复习"
            urgency = "low"
        elif retention_rate >= 0.5:
            suggestion = "记忆有所下降，建议近期复习"
            urgency = "medium"
        else:
            suggestion = "记忆严重衰退，需要立即复习"
            urgency = "high"

        return {
            "node_id": node.node_id,
            "concept": node.concept,
            "retention_rate": round(retention_rate, 3),
            "time_elapsed_days": time_elapsed,
            "memory_strength": round(memory_strength, 3),
            "suggestion": suggestion,
            "urgency": urgency,
            "mastery_level": round(node.mastery_level, 3),
            "review_count": node.review_count
        }

    def create_review_node(self, node_id: str, concept: str, complexity_score: float,
                          canvas_file: str = "") -> ReviewNode:
        """
        创建新的复习节点

        Args:
            node_id: 节点ID
            concept: 概念名称
            complexity_score: 复杂度评分
            canvas_file: Canvas文件名

        Returns:
            ReviewNode: 创建的复习节点
        """
        node = ReviewNode(
            node_id=node_id,
            concept=concept,
            create_time=datetime.datetime.now(),
            complexity_score=complexity_score,
            mastery_level=0.0,  # 初始掌握度为0
            canvas_file=canvas_file
        )

        self.review_nodes[node_id] = node

        if LOGURU_ENABLED:
            logger.info(f"Created review node: {concept} (complexity: {complexity_score})")

        return node

    def update_node_mastery(self, node_id: str, new_mastery_level: float,
                           review_time: Optional[datetime.datetime] = None):
        """
        更新节点掌握度

        Args:
            node_id: 节点ID
            new_mastery_level: 新的掌握度 (0.0-1.0)
            review_time: 复习时间（默认为当前时间）
        """
        if node_id not in self.review_nodes:
            raise ValueError(f"Node {node_id} not found")

        node = self.review_nodes[node_id]
        node.mastery_level = max(0.0, min(1.0, new_mastery_level))
        node.last_review_time = review_time or datetime.datetime.now()
        node.review_count += 1

        if LOGURU_ENABLED:
            logger.info(f"Updated mastery for {node.concept}: {node.mastery_level:.3f}")

    def get_due_nodes(self, canvas_file: Optional[str] = None) -> List[ReviewNode]:
        """
        获取需要复习的节点列表

        Args:
            canvas_file: 可选的Canvas文件过滤

        Returns:
            List[ReviewNode]: 需要复习的节点列表
        """
        due_nodes = []

        for node in self.review_nodes.values():
            if canvas_file and node.canvas_file != canvas_file:
                continue

            if self.should_review_now(node):
                due_nodes.append(node)

        # 按紧急程度排序（保持率低的优先）
        due_nodes.sort(key=lambda n: self.get_retention_status(n)["retention_rate"])

        return due_nodes

    def generate_review_schedule(self, canvas_file: Optional[str] = None,
                               days_ahead: int = 30) -> Dict[str, List[Dict[str, Any]]]:
        """
        生成复习计划

        Args:
            canvas_file: 可选的Canvas文件过滤
            days_ahead: 预览天数

        Returns:
            Dict: 按日期分组的复习计划
        """
        schedule = {}
        now = datetime.datetime.now()

        for node in self.review_nodes.values():
            if canvas_file and node.canvas_file != canvas_file:
                continue

            # 获取所有最优复习时间点
            optimal_times = self.calculate_optimal_review_times(
                node.create_time,
                node.complexity_score
            )

            for review_time in optimal_times:
                if 0 <= (review_time - now).days <= days_ahead:
                    date_str = review_time.strftime("%Y-%m-%d")

                    if date_str not in schedule:
                        schedule[date_str] = []

                    schedule[date_str].append({
                        "node_id": node.node_id,
                        "concept": node.concept,
                        "complexity_score": node.complexity_score,
                        "current_mastery": node.mastery_level,
                        "review_time": review_time.isoformat(),
                        "canvas_file": node.canvas_file
                    })

        return schedule


class EbbinghausReviewScheduler:
    """
    艾宾浩斯复习Agent调度器

    集成遗忘曲线算法和Agent智能调度系统
    """

    def __init__(self):
        """初始化调度器"""
        self.forgetting_curve = ForgettingCurveManager()

        if LOGURU_ENABLED:
            logger.info("EbbinghausReviewScheduler initialized")

    async def schedule_review_agents(self, due_nodes: List[ReviewNode]) -> List[Dict[str, Any]]:
        """
        为到期复习节点智能调度Agent

        Args:
            due_nodes: 需要复习的节点列表

        Returns:
            List[Dict]: 调度计划列表
        """
        schedule = []

        for node in due_nodes:
            # 获取记忆状态
            memory_status = self.forgetting_curve.get_retention_status(node)

            # 基于记忆状态和掌握度推荐Agent
            recommended_agents = self._recommend_agents_for_review(node, memory_status)

            schedule.append({
                "node_id": node.node_id,
                "concept": node.concept,
                "canvas_file": node.canvas_file,
                "retention_rate": memory_status["retention_rate"],
                "urgency": memory_status["urgency"],
                "recommended_agents": recommended_agents,
                "review_reason": memory_status["suggestion"],
                "scheduled_time": datetime.datetime.now().isoformat()
            })

        return schedule

    def _recommend_agents_for_review(self, node: ReviewNode,
                                   memory_status: Dict[str, Any]) -> List[str]:
        """
        基于节点状态推荐复习Agent

        Args:
            node: 复习节点
            memory_status: 记忆状态

        Returns:
            List[str]: 推荐的Agent列表
        """
        agents = []
        retention_rate = memory_status["retention_rate"]
        mastery_level = node.mastery_level

        # 记忆严重衰退，需要基础重建
        if retention_rate < 0.5:
            agents.append("basic-decomposition")
            agents.append("oral-explanation")

        # 掌握度不高，需要深度理解
        elif mastery_level < 0.6:
            agents.append("deep-decomposition")
            agents.append("clarification-path")

        # 需要对比澄清
        elif retention_rate < 0.8:
            agents.append("comparison-table")
            agents.append("memory-anchor")

        # 需要练习巩固
        else:
            agents.append("example-teaching")
            agents.append("four-level-explanation")

        return agents

    async def execute_review_session(self, canvas_file: str,
                                   node_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        执行复习会话

        Args:
            canvas_file: Canvas文件名
            node_ids: 可选的节点ID列表（为None则自动获取到期节点）

        Returns:
            Dict: 复习会话结果
        """
        try:
            # 获取需要复习的节点
            if node_ids:
                due_nodes = [self.forgetting_curve.review_nodes[nid]
                           for nid in node_ids if nid in self.forgetting_curve.review_nodes]
            else:
                due_nodes = self.forgetting_curve.get_due_nodes(canvas_file)

            if not due_nodes:
                return {
                    "success": True,
                    "message": "没有需要复习的节点",
                    "due_nodes_count": 0,
                    "schedule": []
                }

            # 生成Agent调度计划
            schedule = await self.schedule_review_agents(due_nodes)

            return {
                "success": True,
                "message": f"发现 {len(due_nodes)} 个需要复习的节点",
                "due_nodes_count": len(due_nodes),
                "schedule": schedule,
                "canvas_file": canvas_file
            }

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"Review session execution failed: {e}")
            return {
                "success": False,
                "message": f"复习会话执行失败: {str(e)}",
                "due_nodes_count": 0,
                "schedule": []
            }


# ============================================================================
# 全局实例
# ============================================================================

# 创建全局实例
global_controls = GlobalFeatureControls()
canvas_learning_memory = CanvasLearningMemory()
review_board_agent_selector = ReviewBoardAgentSelector()
efficient_canvas_processor = EfficientCanvasProcessor()

# 艾宾浩斯复习系统全局实例
forgetting_curve_manager = ForgettingCurveManager()
ebbinghaus_review_scheduler = EbbinghausReviewScheduler()

# 兼容性别名
ultrathink_canvas_integration = review_board_agent_selector  # 纠正后的别名
canvas_knowledge_graph = canvas_learning_memory  # 纠正后的别名
concurrent_agent_processor = efficient_canvas_processor  # 纠正后的别名
ebbinghaus_system = ebbinghaus_review_scheduler  # 新增别名

if LOGURU_ENABLED:
    logger.info("Canvas v2.0 Corrected Working - All systems including Ebbinghaus initialized")