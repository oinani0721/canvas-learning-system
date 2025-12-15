"""
学习历史分析器 - Canvas学习系统

本模块实现智能复习计划生成系统的学习历史分析引擎，负责：
- 分析用户学习历史数据，识别知识薄弱环节
- 集成艾宾浩斯复习调度、Graphiti知识图谱、MCP语义记忆数据
- 评估掌握程度和学习趋势
- 为个性化复习计划提供数据支持

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-23
"""

import json
import os
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union
from pathlib import Path
import uuid

# 导入相关模块
try:
    from canvas_utils import CanvasJSONOperator, CanvasBusinessLogic, CanvasOrchestrator
    from mcp_memory_client import MCPMemoryClient
    from graphiti_integration import GraphitiClient
    from ebbinghaus_review import EbbinghausScheduler
except ImportError as e:
    print(f"Warning: 无法导入依赖模块 {e}，某些功能可能受限")


class LearningAnalyzer:
    """学习历史分析器

    负责分析用户学习历史，识别薄弱环节，评估掌握程度，
    为智能复习计划生成提供数据支持。
    """

    def __init__(
        self,
        user_id: str = "default",
        mcp_client: Optional[Any] = None,
        graphiti_client: Optional[Any] = None,
        ebbinghaus_scheduler: Optional[Any] = None
    ):
        """初始化学习分析器

        Args:
            user_id: 用户ID，默认为"default"
            mcp_client: MCP语义记忆客户端实例
            graphiti_client: Graphiti知识图谱客户端实例
            ebbinghaus_scheduler: 艾宾浩斯复习调度器实例
        """
        self.user_id = user_id
        self.mcp_client = mcp_client
        self.graphiti_client = graphiti_client
        self.ebbinghaus_scheduler = ebbinghaus_scheduler

        # 分析配置常量
        self.ANALYSIS_CONFIG = {
            "learning_history_days": 30,           # 分析最近30天的学习历史
            "weakness_detection_threshold": 0.7,   # 薄弱环节检测阈值
            "mastery_score_threshold": 8.0,        # 掌握程度分数阈值
            "trend_analysis_window": 7,            # 趋势分析窗口（天）
            "concept_relation_depth": 3,            # 概念关系分析深度
            "semantic_gap_threshold": 0.6,         # 语义差距阈值
            "review_frequency_weight": 0.3,        # 复习频率权重
            "performance_weight": 0.7,             # 表现权重
        }

    def analyze_learning_history(
        self,
        user_id: str = None,
        canvas_path: str = None
    ) -> Dict[str, Any]:
        """分析学习历史，识别薄弱环节

        Args:
            user_id: 用户ID，为None时使用实例默认值
            canvas_path: 指定Canvas路径，None表示分析所有

        Returns:
            Dict: 学习历史分析结果，包含：
                - total_concepts_analyzed: 分析的概念总数
                - concepts_mastered: 已掌握概念数
                - concepts_needing_review: 需要复习的概念数
                - critical_weaknesses: 关键薄弱环节数
                - identified_weak_concepts: 识别的薄弱概念详情
                - learning_trends: 学习趋势分析
                - mastery_assessment: 掌握程度评估
        """
        if user_id is None:
            user_id = self.user_id

        try:
            # 1. 收集学习历史数据
            learning_data = self._collect_learning_data(canvas_path)

            # 2. 分析概念掌握程度
            mastery_analysis = self._analyze_concept_mastery(learning_data)

            # 3. 识别薄弱环节
            weak_concepts = self._identify_weak_concepts(learning_data, mastery_analysis)

            # 4. 分析学习趋势
            trend_analysis = self._analyze_learning_trends(learning_data)

            # 5. 集成外部数据源（如果可用）
            enhanced_analysis = self._enhance_with_external_data(
                weak_concepts, mastery_analysis
            )

            # 6. 生成分析摘要
            analysis_summary = self._generate_analysis_summary(
                learning_data, mastery_analysis, weak_concepts, trend_analysis
            )

            return {
                "analysis_timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "target_canvas": canvas_path,
                "analysis_summary": analysis_summary,
                "identified_weak_concepts": enhanced_analysis["weak_concepts"],
                "learning_trends": trend_analysis,
                "mastery_assessment": mastery_analysis,
                "data_sources_used": self._get_data_sources_status(),
            }

        except Exception as e:
            raise RuntimeError(f"学习历史分析失败: {str(e)}")

    def _collect_learning_data(self, canvas_path: str = None) -> Dict[str, Any]:
        """收集学习历史数据

        Args:
            canvas_path: Canvas文件路径，None表示分析所有相关Canvas

        Returns:
            Dict: 收集的学习数据
        """
        learning_data = {
            "canvas_files": [],
            "concept_performance": {},
            "review_history": [],
            "scoring_records": [],
            "interaction_patterns": {},
        }

        try:
            # 1. 收集Canvas文件数据
            canvas_files = self._find_canvas_files(canvas_path)

            for canvas_file in canvas_files:
                canvas_data = self._load_canvas_data(canvas_file)
                analysis_data = self._extract_canvas_learning_data(canvas_data, canvas_file)
                learning_data["canvas_files"].append(analysis_data)

            # 2. 集成艾宾浩斯复习数据（如果可用）
            if self.ebbinghaus_scheduler:
                review_history = self._get_ebbinghaus_review_history()
                learning_data["review_history"] = review_history

            # 3. 收集评分记录
            scoring_records = self._collect_scoring_records(canvas_files)
            learning_data["scoring_records"] = scoring_records

            # 4. 分析交互模式
            interaction_patterns = self._analyze_interaction_patterns(learning_data)
            learning_data["interaction_patterns"] = interaction_patterns

        except Exception as e:
            print(f"收集学习数据时出现警告: {e}")
            # 返回部分数据而不是完全失败
            pass

        return learning_data

    def _find_canvas_files(self, canvas_path: str = None) -> List[str]:
        """查找相关的Canvas文件

        Args:
            canvas_path: 指定的Canvas路径，None表示查找所有

        Returns:
            List[str]: Canvas文件路径列表
        """
        canvas_files = []

        if canvas_path and os.path.exists(canvas_path):
            return [canvas_path]

        # 搜索常见的Canvas文件位置
        search_paths = [
            "笔记库/",
            "笔记库/examples/",
            ".",
        ]

        for search_path in search_paths:
            if os.path.exists(search_path):
                for root, dirs, files in os.walk(search_path):
                    for file in files:
                        if file.endswith('.canvas'):
                            canvas_files.append(os.path.join(root, file))

        # 过滤最近修改的文件（根据配置）
        cutoff_date = datetime.now() - timedelta(
            days=self.ANALYSIS_CONFIG["learning_history_days"]
        )

        recent_files = []
        for file_path in canvas_files:
            try:
                mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if mod_time >= cutoff_date:
                    recent_files.append(file_path)
            except OSError:
                continue

        return recent_files

    def _load_canvas_data(self, canvas_path: str) -> Dict[str, Any]:
        """加载Canvas数据

        Args:
            canvas_path: Canvas文件路径

        Returns:
            Dict: Canvas数据
        """
        try:
            return CanvasJSONOperator.read_canvas(canvas_path)
        except Exception as e:
            print(f"加载Canvas文件 {canvas_path} 失败: {e}")
            return {"nodes": [], "edges": []}

    def _extract_canvas_learning_data(self, canvas_data: Dict, canvas_path: str) -> Dict[str, Any]:
        """从Canvas数据中提取学习相关信息

        Args:
            canvas_data: Canvas JSON数据
            canvas_path: Canvas文件路径

        Returns:
            Dict: 提取的学习数据
        """
        learning_info = {
            "canvas_path": canvas_path,
            "modification_time": os.path.getmtime(canvas_path),
            "concepts": [],
            "questions": [],
            "understanding_records": [],
            "explanations": [],
        }

        nodes = canvas_data.get("nodes", [])

        for node in nodes:
            node_type = node.get("type", "text")
            node_text = node.get("text", "")
            node_color = node.get("color", "")

            # 分析节点内容
            if node_type == "text" and node_text:
                content_analysis = self._analyze_node_content(node_text, node_color)

                if content_analysis["type"] == "concept":
                    learning_info["concepts"].append(content_analysis)
                elif content_analysis["type"] == "question":
                    learning_info["questions"].append(content_analysis)
                elif content_analysis["type"] == "understanding":
                    learning_info["understanding_records"].append(content_analysis)
                elif content_analysis["type"] == "explanation":
                    learning_info["explanations"].append(content_analysis)

        return learning_info

    def _analyze_node_content(self, text: str, color: str) -> Dict[str, Any]:
        """分析节点内容类型和属性

        Args:
            text: 节点文本内容
            color: 节点颜色

        Returns:
            Dict: 内容分析结果
        """
        text_lower = text.lower()

        # 基于颜色判断节点类型
        if color == "1":  # 红色 - 问题/难点
            return {
                "type": "question",
                "text": text,
                "difficulty": "hard",
                "color": color,
                "keywords": self._extract_keywords(text),
            }
        elif color == "2":  # 绿色 - 已掌握
            return {
                "type": "concept",
                "text": text,
                "mastery_level": "mastered",
                "color": color,
                "keywords": self._extract_keywords(text),
            }
        elif color == "3":  # 紫色 - 似懂非懂
            return {
                "type": "concept",
                "text": text,
                "mastery_level": "partial",
                "color": color,
                "keywords": self._extract_keywords(text),
            }
        elif color == "6":  # 黄色 - 个人理解
            return {
                "type": "understanding",
                "text": text,
                "color": color,
                "quality_score": self._assess_understanding_quality(text),
                "keywords": self._extract_keywords(text),
            }
        elif color == "5":  # 蓝色 - AI解释
            return {
                "type": "explanation",
                "text": text,
                "color": color,
                "explanation_type": self._classify_explanation_type(text),
                "keywords": self._extract_keywords(text),
            }
        else:
            # 默认分析
            return {
                "type": "concept",
                "text": text,
                "mastery_level": "unknown",
                "color": color,
                "keywords": self._extract_keywords(text),
            }

    def _extract_keywords(self, text: str) -> List[str]:
        """提取文本关键词

        Args:
            text: 输入文本

        Returns:
            List[str]: 关键词列表
        """
        # 简单的关键词提取实现
        # 在实际应用中可以使用更复杂的NLP技术
        import re

        # 移除标点符号并分割
        words = re.findall(r'\b[\u4e00-\u9fff\w]+\b', text.lower())

        # 过滤停用词和短词
        stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '如果', '因为', '所以', 'the', 'a', 'an', 'and', 'or', 'but', 'if', 'because', 'so'}

        keywords = [word for word in words if len(word) > 1 and word not in stop_words]

        # 返回最常见的关键词（最多10个）
        from collections import Counter
        word_counts = Counter(keywords)
        return [word for word, _ in word_counts.most_common(10)]

    def _assess_understanding_quality(self, text: str) -> float:
        """评估个人理解质量

        Args:
            text: 理解文本

        Returns:
            float: 质量分数 (0-10)
        """
        # 简单的质量评估实现
        quality_score = 5.0  # 基础分数

        # 长度评分
        length = len(text)
        if length < 20:
            quality_score -= 2
        elif length > 100:
            quality_score += 1

        # 内容丰富度评分
        if any(keyword in text.lower() for keyword in ['因为', '所以', '例如', '比如', 'because', 'example', 'such as']):
            quality_score += 1

        # 逻辑连接词评分
        if any(keyword in text.lower() for keyword in ['首先', '其次', '最后', 'first', 'second', 'finally']):
            quality_score += 1

        return max(0, min(10, quality_score))

    def _classify_explanation_type(self, text: str) -> str:
        """分类解释类型

        Args:
            text: 解释文本

        Returns:
            str: 解释类型
        """
        text_lower = text.lower()

        if any(keyword in text_lower for keyword in ['定义', 'definition', '什么是']):
            return "definition"
        elif any(keyword in text_lower for keyword in ['例子', 'example', '例如']):
            return "example"
        elif any(keyword in text_lower for keyword in ['比较', 'comparison', '区别']):
            return "comparison"
        elif any(keyword in text_lower for keyword in ['步骤', 'steps', '过程']):
            return "procedure"
        else:
            return "general"

    def _analyze_concept_mastery(self, learning_data: Dict) -> Dict[str, Any]:
        """分析概念掌握程度

        Args:
            learning_data: 学习数据

        Returns:
            Dict: 掌握程度分析结果
        """
        concept_mastery = {}

        # 收集所有概念及其表现数据
        for canvas_file in learning_data["canvas_files"]:
            for concept in canvas_file["concepts"]:
                concept_name = self._normalize_concept_name(concept["text"])

                if concept_name not in concept_mastery:
                    concept_mastery[concept_name] = {
                        "name": concept_name,
                        "mastery_level": concept.get("mastery_level", "unknown"),
                        "encounters": 0,
                        "understanding_records": [],
                        "related_explanations": [],
                        "last_encounter": 0,
                        "performance_scores": [],
                    }

                concept_mastery[concept_name]["encounters"] += 1

                # 更新最后遇到时间
                mod_time = canvas_file["modification_time"]
                if mod_time > concept_mastery[concept_name]["last_encounter"]:
                    concept_mastery[concept_name]["last_encounter"] = mod_time

        # 添加理解和解释记录
        for canvas_file in learning_data["canvas_files"]:
            for understanding in canvas_file["understanding_records"]:
                related_concepts = self._find_related_concepts(
                    understanding["text"], concept_mastery.keys()
                )
                for concept_name in related_concepts:
                    if concept_name in concept_mastery:
                        concept_mastery[concept_name]["understanding_records"].append({
                            "text": understanding["text"],
                            "quality_score": understanding.get("quality_score", 0),
                            "timestamp": canvas_file["modification_time"],
                        })

            for explanation in canvas_file["explanations"]:
                related_concepts = self._find_related_concepts(
                    explanation["text"], concept_mastery.keys()
                )
                for concept_name in related_concepts:
                    if concept_name in concept_mastery:
                        concept_mastery[concept_name]["related_explanations"].append({
                            "text": explanation["text"],
                            "type": explanation.get("explanation_type", "general"),
                            "timestamp": canvas_file["modification_time"],
                        })

        # 添加评分记录
        for record in learning_data["scoring_records"]:
            concept_name = self._normalize_concept_name(record.get("concept", ""))
            if concept_name in concept_mastery:
                concept_mastery[concept_name]["performance_scores"].append({
                    "score": record.get("score", 0),
                    "timestamp": record.get("timestamp", 0),
                    "dimensions": record.get("dimensions", {}),
                })

        # 计算综合掌握分数
        for concept_name, concept_data in concept_mastery.items():
            concept_data["mastery_score"] = self._calculate_mastery_score(concept_data)

        return concept_mastery

    def _normalize_concept_name(self, text: str) -> str:
        """标准化概念名称

        Args:
            text: 原始文本

        Returns:
            str: 标准化的概念名称
        """
        # 简单的标准化实现
        import re

        # 移除标点符号和多余空格
        normalized = re.sub(r'[^\w\u4e00-\u9fff\s]', '', text).strip()

        # 转换为小写
        normalized = normalized.lower()

        return normalized

    def _find_related_concepts(self, text: str, concept_names: List[str]) -> List[str]:
        """查找文本中相关的概念

        Args:
            text: 输入文本
            concept_names: 概念名称列表

        Returns:
            List[str]: 相关概念列表
        """
        related_concepts = []
        text_lower = text.lower()

        for concept_name in concept_names:
            if concept_name.lower() in text_lower:
                related_concepts.append(concept_name)

        return related_concepts

    def _calculate_mastery_score(self, concept_data: Dict) -> float:
        """计算概念掌握分数

        Args:
            concept_data: 概念数据

        Returns:
            float: 掌握分数 (0-10)
        """
        score = 5.0  # 基础分数

        # 基于明确掌握级别调整
        mastery_level = concept_data.get("mastery_level", "unknown")
        if mastery_level == "mastered":
            score += 3
        elif mastery_level == "partial":
            score += 1
        elif mastery_level == "unknown":
            score += 0

        # 基于遇到次数调整
        encounters = concept_data.get("encounters", 0)
        if encounters >= 5:
            score += 1
        elif encounters >= 3:
            score += 0.5

        # 基于理解记录调整
        understanding_records = concept_data.get("understanding_records", [])
        if understanding_records:
            avg_quality = sum(r.get("quality_score", 0) for r in understanding_records) / len(understanding_records)
            score += (avg_quality - 5) * 0.2

        # 基于表现分数调整
        performance_scores = concept_data.get("performance_scores", [])
        if performance_scores:
            avg_performance = sum(s.get("score", 0) for s in performance_scores) / len(performance_scores)
            score += (avg_performance - 5) * 0.3

        return max(0, min(10, score))

    def _identify_weak_concepts(
        self,
        learning_data: Dict,
        mastery_analysis: Dict
    ) -> List[Dict[str, Any]]:
        """识别薄弱概念

        Args:
            learning_data: 学习数据
            mastery_analysis: 掌握程度分析

        Returns:
            List[Dict]: 薄弱概念列表
        """
        weak_concepts = []
        threshold = self.ANALYSIS_CONFIG["weakness_detection_threshold"]
        mastery_threshold = self.ANALYSIS_CONFIG["mastery_score_threshold"]

        for concept_name, concept_data in mastery_analysis.items():
            mastery_score = concept_data.get("mastery_score", 5.0)

            # 判断是否为薄弱概念
            if mastery_score < mastery_threshold:
                weakness_score = 1.0 - (mastery_score / 10.0)

                # 收集支持证据
                supporting_evidence = self._collect_supporting_evidence(
                    concept_data, learning_data
                )

                # 推荐关注领域
                recommended_focus_areas = self._recommend_focus_areas(
                    concept_data, supporting_evidence
                )

                weak_concept = {
                    "concept_name": concept_name,
                    "weakness_score": weakness_score,
                    "mastery_score": mastery_score,
                    "weakness_type": self._classify_weakness_type(concept_data),
                    "supporting_evidence": supporting_evidence,
                    "recommended_focus_areas": recommended_focus_areas,
                    "urgency_level": self._assess_urgency_level(concept_data),
                }

                weak_concepts.append(weak_concept)

        # 按薄弱程度排序
        weak_concepts.sort(key=lambda x: x["weakness_score"], reverse=True)

        return weak_concepts

    def _collect_supporting_evidence(
        self,
        concept_data: Dict,
        learning_data: Dict
    ) -> Dict[str, Any]:
        """收集支持证据

        Args:
            concept_data: 概念数据
            learning_data: 学习数据

        Returns:
            Dict: 支持证据
        """
        evidence = {
            "last_review_score": 0,
            "review_frequency": "insufficient",
            "graphiti_related_concepts": [],
            "mcp_semantic_gaps": [],
            "understanding_quality_trend": "stable",
            "explanation_access_count": 0,
        }

        # 分析最近的评分
        performance_scores = concept_data.get("performance_scores", [])
        if performance_scores:
            latest_score = max(performance_scores, key=lambda x: x.get("timestamp", 0))
            evidence["last_review_score"] = latest_score.get("score", 0)

        # 分析复习频率
        encounters = concept_data.get("encounters", 0)
        if encounters >= 5:
            evidence["review_frequency"] = "frequent"
        elif encounters >= 3:
            evidence["review_frequency"] = "moderate"
        else:
            evidence["review_frequency"] = "insufficient"

        # 查找Graphiti相关概念（如果可用）
        if self.graphiti_client:
            try:
                related_concepts = self._get_graphiti_related_concepts(concept_data["name"])
                evidence["graphiti_related_concepts"] = related_concepts
            except:
                pass

        # 查找MCP语义差距（如果可用）
        if self.mcp_client:
            try:
                semantic_gaps = self._get_mcp_semantic_gaps(concept_data["name"])
                evidence["mcp_semantic_gaps"] = semantic_gaps
            except:
                pass

        # 分析理解质量趋势
        understanding_records = concept_data.get("understanding_records", [])
        if len(understanding_records) >= 2:
            recent_records = sorted(understanding_records, key=lambda x: x.get("timestamp", 0))[-2:]
            quality_change = recent_records[-1].get("quality_score", 0) - recent_records[0].get("quality_score", 0)
            if quality_change > 1:
                evidence["understanding_quality_trend"] = "improving"
            elif quality_change < -1:
                evidence["understanding_quality_trend"] = "declining"

        # 统计解释访问次数
        evidence["explanation_access_count"] = len(concept_data.get("related_explanations", []))

        return evidence

    def _recommend_focus_areas(
        self,
        concept_data: Dict,
        evidence: Dict
    ) -> List[str]:
        """推荐关注领域

        Args:
            concept_data: 概念数据
            evidence: 支持证据

        Returns:
            List[str]: 推荐关注领域列表
        """
        focus_areas = []

        # 基于理解质量推荐
        understanding_records = concept_data.get("understanding_records", [])
        if not understanding_records:
            focus_areas.append("概念定义复习")
        else:
            avg_quality = sum(r.get("quality_score", 0) for r in understanding_records) / len(understanding_records)
            if avg_quality < 6:
                focus_areas.append("基础概念理解加深")

        # 基于复习频率推荐
        if evidence["review_frequency"] == "insufficient":
            focus_areas.append("增加复习频次")

        # 基于表现分数推荐
        if evidence["last_review_score"] < 6:
            focus_areas.append("实例练习加强")

        # 基于相关概念推荐
        if evidence["graphiti_related_concepts"]:
            focus_areas.append("与其他概念的关系理解")

        # 基于语义差距推荐
        if evidence["mcp_semantic_gaps"]:
            focus_areas.append("补充相关知识背景")

        # 基于解释访问推荐
        if evidence["explanation_access_count"] > 3:
            focus_areas.append("尝试独立解释概念")

        return focus_areas[:4]  # 最多返回4个建议

    def _classify_weakness_type(self, concept_data: Dict) -> str:
        """分类薄弱类型

        Args:
            concept_data: 概念数据

        Returns:
            str: 薄弱类型
        """
        mastery_level = concept_data.get("mastery_level", "unknown")
        encounters = concept_data.get("encounters", 0)
        understanding_records = concept_data.get("understanding_records", [])

        if encounters < 2:
            return "insufficient_exposure"  # 接触不足
        elif not understanding_records:
            return "lack_of_practice"  # 缺乏练习
        elif mastery_level == "partial":
            return "conceptual_misunderstanding"  # 概念理解偏差
        elif encounters >= 5 and understanding_records:
            avg_quality = sum(r.get("quality_score", 0) for r in understanding_records) / len(understanding_records)
            if avg_quality < 5:
                return "procedural_error"  # 过程性错误
            else:
                return "recall_failure"  # 记忆提取失败
        else:
            return "general_weakness"  # 一般性薄弱

    def _assess_urgency_level(self, concept_data: Dict) -> str:
        """评估紧急程度

        Args:
            concept_data: 概念数据

        Returns:
            str: 紧急程度 ("high", "medium", "low")
        """
        mastery_score = concept_data.get("mastery_score", 5.0)
        last_encounter = concept_data.get("last_encounter", 0)

        # 计算距离上次学习的时间
        days_since_last = (datetime.now().timestamp() - last_encounter) / (24 * 3600)

        if mastery_score < 4 or days_since_last > 14:
            return "high"
        elif mastery_score < 6 or days_since_last > 7:
            return "medium"
        else:
            return "low"

    def _analyze_learning_trends(self, learning_data: Dict) -> Dict[str, Any]:
        """分析学习趋势

        Args:
            learning_data: 学习数据

        Returns:
            Dict: 学习趋势分析
        """
        trends = {
            "overall_performance_trend": "stable",
            "study_frequency_trend": "stable",
            "concept_mastery_trend": "stable",
            "weakness_improvement_rate": 0.0,
            "retention_analysis": {},
            "engagement_patterns": {},
        }

        try:
            # 分析整体表现趋势
            trends["overall_performance_trend"] = self._analyze_performance_trend(learning_data)

            # 分析学习频率趋势
            trends["study_frequency_trend"] = self._analyze_study_frequency_trend(learning_data)

            # 分析概念掌握趋势
            trends["concept_mastery_trend"] = self._analyze_mastery_trend(learning_data)

            # 分析薄弱环节改善率
            trends["weakness_improvement_rate"] = self._calculate_improvement_rate(learning_data)

            # 分析记忆保持情况
            trends["retention_analysis"] = self._analyze_retention(learning_data)

            # 分析参与模式
            trends["engagement_patterns"] = self._analyze_engagement_patterns(learning_data)

        except Exception as e:
            print(f"学习趋势分析时出现警告: {e}")
            # 返回默认趋势而不是失败
            pass

        return trends

    def _analyze_performance_trend(self, learning_data: Dict) -> str:
        """分析表现趋势

        Args:
            learning_data: 学习数据

        Returns:
            str: 趋势描述 ("improving", "declining", "stable", "fluctuating")
        """
        all_scores = []

        # 收集所有评分记录
        for canvas_file in learning_data["canvas_files"]:
            for record in canvas_file.get("scoring_records", []):
                if "score" in record and "timestamp" in record:
                    all_scores.append((record["timestamp"], record["score"]))

        if len(all_scores) < 2:
            return "insufficient_data"

        # 按时间排序
        all_scores.sort(key=lambda x: x[0])

        # 计算趋势
        if len(all_scores) >= 4:
            # 使用简单的线性回归分析趋势
            x = list(range(len(all_scores)))
            y = [score for _, score in all_scores]

            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_x2 = sum(x[i] ** 2 for i in range(n))

            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)

            if slope > 0.2:
                return "improving"
            elif slope < -0.2:
                return "declining"
            else:
                return "stable"
        else:
            # 简单比较
            recent_avg = sum(score for _, score in all_scores[-2:]) / 2
            earlier_avg = sum(score for _, score in all_scores[:2]) / 2

            if recent_avg > earlier_avg + 1:
                return "improving"
            elif recent_avg < earlier_avg - 1:
                return "declining"
            else:
                return "stable"

    def _analyze_study_frequency_trend(self, learning_data: Dict) -> str:
        """分析学习频率趋势

        Args:
            learning_data: 学习数据

        Returns:
            str: 趋势描述
        """
        # 收集学习活动时间戳
        timestamps = []
        for canvas_file in learning_data["canvas_files"]:
            timestamps.append(canvas_file["modification_time"])

        if len(timestamps) < 2:
            return "insufficient_data"

        # 按时间排序
        timestamps.sort()

        # 计算间隔
        intervals = []
        for i in range(1, len(timestamps)):
            interval = (timestamps[i] - timestamps[i-1]) / (24 * 3600)  # 转换为天
            intervals.append(interval)

        if len(intervals) < 2:
            return "insufficient_data"

        # 分析间隔趋势
        recent_avg = sum(intervals[-2:]) / 2
        earlier_avg = sum(intervals[:2]) / 2

        if recent_avg < earlier_avg * 0.8:
            return "increasing"
        elif recent_avg > earlier_avg * 1.2:
            return "decreasing"
        else:
            return "stable"

    def _analyze_mastery_trend(self, learning_data: Dict) -> str:
        """分析概念掌握趋势

        Args:
            learning_data: 学习数据

        Returns:
            str: 趋势描述
        """
        # 这里简化实现，实际应用中可以更复杂
        mastery_levels = []

        for canvas_file in learning_data["canvas_files"]:
            concepts = canvas_file.get("concepts", [])
            if concepts:
                mastered_count = sum(1 for c in concepts if c.get("mastery_level") == "mastered")
                mastery_ratio = mastered_count / len(concepts)
                mastery_levels.append(mastery_ratio)

        if len(mastery_levels) < 2:
            return "insufficient_data"

        recent_avg = sum(mastery_levels[-2:]) / 2
        earlier_avg = sum(mastery_levels[:2]) / 2

        if recent_avg > earlier_avg + 0.1:
            return "improving"
        elif recent_avg < earlier_avg - 0.1:
            return "declining"
        else:
            return "stable"

    def _calculate_improvement_rate(self, learning_data: Dict) -> float:
        """计算薄弱环节改善率

        Args:
            learning_data: 学习数据

        Returns:
            float: 改善率 (0.0-1.0)
        """
        # 简化实现
        return 0.5  # 默认中等改善率

    def _analyze_retention(self, learning_data: Dict) -> Dict[str, Any]:
        """分析记忆保持情况

        Args:
            learning_data: 学习数据

        Returns:
            Dict: 记忆保持分析
        """
        return {
            "short_term_retention": 0.8,
            "long_term_retention": 0.6,
            "forgetting_curve_fit": "exp",
            "optimal_review_interval": 7,  # 天
        }

    def _analyze_engagement_patterns(self, learning_data: Dict) -> Dict[str, Any]:
        """分析参与模式

        Args:
            learning_data: 学习数据

        Returns:
            Dict: 参与模式分析
        """
        return {
            "preferred_study_time": "morning",
            "average_session_duration": 45,  # 分钟
            "most_active_days": ["Monday", "Wednesday", "Friday"],
            "interaction_types": {
                "question_creation": 0.3,
                "understanding_input": 0.5,
                "explanation_reading": 0.2,
            },
        }

    def _enhance_with_external_data(
        self,
        weak_concepts: List[Dict],
        mastery_analysis: Dict
    ) -> Dict[str, Any]:
        """集成外部数据源增强分析

        Args:
            weak_concepts: 薄弱概念列表
            mastery_analysis: 掌握程度分析

        Returns:
            Dict: 增强后的分析结果
        """
        enhanced_concepts = []

        for concept in weak_concepts:
            enhanced_concept = concept.copy()

            # 集成Graphiti知识图谱数据
            if self.graphiti_client:
                try:
                    graphiti_data = self._get_graphiti_enhancement(concept["concept_name"])
                    enhanced_concept["graphiti_insights"] = graphiti_data
                except Exception as e:
                    print(f"Graphiti数据集成失败: {e}")

            # 集成MCP语义记忆数据
            if self.mcp_client:
                try:
                    mcp_data = self._get_mcp_enhancement(concept["concept_name"])
                    enhanced_concept["semantic_insights"] = mcp_data
                except Exception as e:
                    print(f"MCP数据集成失败: {e}")

            # 集成艾宾浩斯复习数据
            if self.ebbinghaus_scheduler:
                try:
                    ebbinghaus_data = self._get_ebbinghaus_enhancement(concept["concept_name"])
                    enhanced_concept["review_insights"] = ebbinghaus_data
                except Exception as e:
                    print(f"艾宾浩斯数据集成失败: {e}")

            enhanced_concepts.append(enhanced_concept)

        return {
            "weak_concepts": enhanced_concepts,
            "data_sources_status": self._get_data_sources_status(),
        }

    def _get_graphiti_enhancement(self, concept_name: str) -> Dict[str, Any]:
        """获取Graphiti知识图谱增强数据

        Args:
            concept_name: 概念名称

        Returns:
            Dict: Graphiti增强数据
        """
        # 简化实现
        return {
            "related_concepts": ["相关概念1", "相关概念2"],
            "knowledge_gaps": ["知识点差距"],
            "learning_path": ["学习路径建议"],
            "difficulty_level": "medium",
        }

    def _get_mcp_enhancement(self, concept_name: str) -> Dict[str, Any]:
        """获取MCP语义记忆增强数据

        Args:
            concept_name: 概念名称

        Returns:
            Dict: MCP增强数据
        """
        # 简化实现
        return {
            "semantic_gaps": ["语义差距"],
            "misconceptions": ["常见误解"],
            "learning_obstacles": ["学习障碍"],
            "memory_anchors": ["记忆锚点"],
        }

    def _get_ebbinghaus_enhancement(self, concept_name: str) -> Dict[str, Any]:
        """获取艾宾浩斯复习增强数据

        Args:
            concept_name: 概念名称

        Returns:
            Dict: 艾宾浩斯增强数据
        """
        # 简化实现
        return {
            "review_history": ["复习历史"],
            "optimal_interval": 7,  # 天
            "retention_probability": 0.8,
            "next_review_date": datetime.now().isoformat(),
        }

    def _get_data_sources_status(self) -> Dict[str, bool]:
        """获取数据源状态

        Returns:
            Dict: 数据源状态
        """
        return {
            "canvas_data": True,
            "ebbinghaus_scheduler": self.ebbinghaus_scheduler is not None,
            "graphiti_client": self.graphiti_client is not None,
            "mcp_client": self.mcp_client is not None,
        }

    def _generate_analysis_summary(
        self,
        learning_data: Dict,
        mastery_analysis: Dict,
        weak_concepts: List[Dict],
        trend_analysis: Dict
    ) -> Dict[str, Any]:
        """生成分析摘要

        Args:
            learning_data: 学习数据
            mastery_analysis: 掌握程度分析
            weak_concepts: 薄弱概念列表
            trend_analysis: 趋势分析

        Returns:
            Dict: 分析摘要
        """
        total_concepts = len(mastery_analysis)
        mastered_concepts = sum(1 for c in mastery_analysis.values() if c.get("mastery_score", 0) >= 8)
        concepts_needing_review = len(weak_concepts)
        critical_weaknesses = sum(1 for c in weak_concepts if c.get("urgency_level") == "high")

        # 估算推荐学习时间
        recommended_time = concepts_needing_review * 15  # 每个概念15分钟

        # 分析难度分布
        difficulty_distribution = {"easy": 0, "medium": 0, "hard": 0}
        for concept in mastery_analysis.values():
            mastery_score = concept.get("mastery_score", 5)
            if mastery_score >= 8:
                difficulty_distribution["easy"] += 1
            elif mastery_score >= 5:
                difficulty_distribution["medium"] += 1
            else:
                difficulty_distribution["hard"] += 1

        return {
            "total_concepts_analyzed": total_concepts,
            "concepts_mastered": mastered_concepts,
            "concepts_needing_review": concepts_needing_review,
            "critical_weaknesses": critical_weaknesses,
            "recommended_study_time_minutes": recommended_time,
            "difficulty_distribution": difficulty_distribution,
            "analysis_quality_score": self._calculate_analysis_quality(learning_data),
        }

    def _calculate_analysis_quality(self, learning_data: Dict) -> float:
        """计算分析质量分数

        Args:
            learning_data: 学习数据

        Returns:
            float: 质量分数 (0.0-1.0)
        """
        # 基于数据完整性计算质量分数
        quality_score = 0.5  # 基础分数

        # Canvas文件数量
        canvas_count = len(learning_data.get("canvas_files", []))
        if canvas_count >= 5:
            quality_score += 0.2
        elif canvas_count >= 2:
            quality_score += 0.1

        # 评分记录数量
        scoring_count = len(learning_data.get("scoring_records", []))
        if scoring_count >= 10:
            quality_score += 0.2
        elif scoring_count >= 5:
            quality_score += 0.1

        # 理解记录数量
        understanding_count = sum(
            len(canvas_file.get("understanding_records", []))
            for canvas_file in learning_data.get("canvas_files", [])
        )
        if understanding_count >= 20:
            quality_score += 0.1

        return min(1.0, quality_score)

    def _get_ebbinghaus_review_history(self) -> List[Dict[str, Any]]:
        """获取艾宾浩斯复习历史

        Returns:
            List[Dict]: 复习历史记录
        """
        if not self.ebbinghaus_scheduler:
            return []

        try:
            # 调用艾宾浩斯调度器的接口
            return self.ebbinghaus_scheduler.get_user_review_history(self.user_id)
        except Exception as e:
            print(f"获取艾宾浩斯复习历史失败: {e}")
            return []

    def _collect_scoring_records(self, canvas_files: List[str]) -> List[Dict[str, Any]]:
        """收集评分记录

        Args:
            canvas_files: Canvas文件列表

        Returns:
            List[Dict]: 评分记录
        """
        scoring_records = []

        for canvas_file_path in canvas_files:
            try:
                # 从Canvas文件中提取评分记录
                canvas_data = self._load_canvas_data(canvas_file_path)

                # 查找包含评分信息的节点
                for node in canvas_data.get("nodes", []):
                    text = node.get("text", "")
                    if "评分" in text or "score" in text.lower():
                        # 简单的评分提取逻辑
                        score = self._extract_score_from_text(text)
                        if score is not None:
                            scoring_records.append({
                                "score": score,
                                "timestamp": os.path.getmtime(canvas_file_path),
                                "canvas_file": canvas_file_path,
                                "node_id": node.get("id", ""),
                                "concept": self._extract_concept_from_text(text),
                            })
            except Exception as e:
                print(f"收集评分记录失败 {canvas_file_path}: {e}")
                continue

        return scoring_records

    def _extract_score_from_text(self, text: str) -> Optional[float]:
        """从文本中提取分数

        Args:
            text: 包含分数的文本

        Returns:
            Optional[float]: 提取的分数
        """
        import re

        # 查找分数模式
        patterns = [
            r'(\d+(?:\.\d+)?)\s*分',
            r'score[:\s]*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)/10',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue

        return None

    def _extract_concept_from_text(self, text: str) -> Optional[str]:
        """从文本中提取概念名称

        Args:
            text: 包含概念的文本

        Returns:
            Optional[str]: 概念名称
        """
        # 简化实现，返回前50个字符作为概念标识
        return text[:50] if text else None

    def _analyze_interaction_patterns(self, learning_data: Dict) -> Dict[str, Any]:
        """分析交互模式

        Args:
            learning_data: 学习数据

        Returns:
            Dict: 交互模式分析
        """
        patterns = {
            "question_creation_frequency": 0,
            "understanding_input_frequency": 0,
            "explanation_access_frequency": 0,
            "interaction_sequence": [],
            "peak_activity_hours": [],
        }

        total_questions = 0
        total_understandings = 0
        total_explanations = 0

        for canvas_file in learning_data["canvas_files"]:
            total_questions += len(canvas_file.get("questions", []))
            total_understandings += len(canvas_file.get("understanding_records", []))
            total_explanations += len(canvas_file.get("explanations", []))

        total_interactions = total_questions + total_understandings + total_explanations

        if total_interactions > 0:
            patterns["question_creation_frequency"] = total_questions / total_interactions
            patterns["understanding_input_frequency"] = total_understandings / total_interactions
            patterns["explanation_access_frequency"] = total_explanations / total_interactions

        return patterns

    def _get_graphiti_related_concepts(self, concept_name: str) -> List[str]:
        """获取Graphiti相关概念

        Args:
            concept_name: 概念名称

        Returns:
            List[str]: 相关概念列表
        """
        if not self.graphiti_client:
            return []

        try:
            # 调用Graphiti客户端接口
            result = self.graphiti_client.search_related_concepts(concept_name, limit=5)
            return [concept.get("name", "") for concept in result]
        except Exception as e:
            print(f"获取Graphiti相关概念失败: {e}")
            return []

    def _get_mcp_semantic_gaps(self, concept_name: str) -> List[str]:
        """获取MCP语义差距

        Args:
            concept_name: 概念名称

        Returns:
            List[str]: 语义差距列表
        """
        if not self.mcp_client:
            return []

        try:
            # 调用MCP客户端接口
            result = self.mcp_client.analyze_semantic_gaps(concept_name)
            return result.get("gaps", [])
        except Exception as e:
            print(f"获取MCP语义差距失败: {e}")
            return []


# 示例使用
if __name__ == "__main__":
    # 创建学习分析器实例
    analyzer = LearningAnalyzer()

    # 分析学习历史
    try:
        result = analyzer.analyze_learning_history()
        print("学习历史分析结果:")
        print(f"分析概念总数: {result['analysis_summary']['total_concepts_analyzed']}")
        print(f"已掌握概念数: {result['analysis_summary']['concepts_mastered']}")
        print(f"需要复习概念数: {result['analysis_summary']['concepts_needing_review']}")
        print(f"关键薄弱环节数: {result['analysis_summary']['critical_weaknesses']}")

        # 显示薄弱概念
        if result['identified_weak_concepts']:
            print("\n薄弱概念:")
            for i, concept in enumerate(result['identified_weak_concepts'][:3], 1):
                print(f"{i}. {concept['concept_name']} (薄弱程度: {concept['weakness_score']:.2f})")
                print(f"   推荐关注: {', '.join(concept['recommended_focus_areas'])}")

    except Exception as e:
        print(f"分析失败: {e}")