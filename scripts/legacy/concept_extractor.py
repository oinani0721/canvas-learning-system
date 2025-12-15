#!/usr/bin/env python3
"""
概念关系自动提取器

从Canvas文件中自动提取概念和关系，使用NLP技术进行语义分析，
支持多种关系类型和置信度评估。

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-22
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set, Any

import jieba
import numpy as np
from loguru import logger
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN


class ConceptExtractor:
    """概念关系自动提取器

    负责从Canvas数据中自动提取概念和关系：
    - 概念识别和标准化
    - 语义关系识别
    - 关系强度计算
    - 置信度评估
    """

    def __init__(self):
        """初始化概念提取器"""
        # 关系类型定义
        self.relationship_types = {
            "is_prerequisite_for": "是...的前提",
            "is_similar_to": "类似于",
            "is_contradictory_of": "与...矛盾",
            "is_derived_from": "源于",
            "is_applied_in": "应用于",
            "is_example_of": "是...的例子",
            "includes": "包括",
            "leads_to": "导致"
        }

        # 关系关键词映射
        self.relationship_keywords = {
            "is_prerequisite_for": [
                "前提", "基础", "先决条件", "必须先掌握", "依赖于", "基于"
            ],
            "is_similar_to": [
                "类似", "相似", "像", "如同", "相近", "类似与"
            ],
            "is_contradictory_of": [
                "相反", "矛盾", "对立", "不同", "区别", "反面"
            ],
            "is_derived_from": [
                "推导", "导出", "派生", "得出", "源于", "来自"
            ],
            "is_applied_in": [
                "应用于", "用于", "使用在", "应用在", "实践中"
            ],
            "is_example_of": [
                "例子", "实例", "案例", "举例", "例如", "比如"
            ],
            "includes": [
                "包括", "包含", "涵盖", "由...组成", "含有"
            ],
            "leads_to": [
                "导致", "引起", "产生", "造成", "结果", "推论"
            ]
        }

        # 学科特定概念模式
        self.subject_patterns = {
            "数学": [
                r"(定理|公理|定义|公式|证明|推导|计算|求解)",
                r"(函数|方程|不等式|集合|映射|变换)",
                r"(微积分|导数|积分|极限|级数)"
            ],
            "物理": [
                r"(定律|原理|公式|实验|测量|观察)",
                r"(力|运动|能量|功|功率|动量)",
                r"(电场|磁场|波动|光学|热学)"
            ],
            "化学": [
                r"(元素|化合物|反应|方程式|实验)",
                r"(原子|分子|离子|化学键)",
                r"(酸碱|氧化还原|有机化学|无机化学)"
            ],
            "计算机": [
                r"(算法|数据结构|程序|代码|函数)",
                r"(类|对象|继承|多态|封装)",
                r"(网络|数据库|操作系统|编程语言)"
            ]
        }

        # 初始化TF-IDF向量化器
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            stop_words=None,  # 中文分词需要自定义停用词
            token_pattern=r'\b\w+\b'
        )

        logger.info("概念提取器初始化完成")

    def extract_concepts_from_canvas(self, canvas_path: str) -> Dict[str, Any]:
        """从Canvas文件中提取概念和关系

        Args:
            canvas_path: Canvas文件路径

        Returns:
            Dict: 包含概念、关系和元数据的字典

        Raises:
            FileNotFoundError: 如果Canvas文件不存在
            ValueError: 如果Canvas文件格式无效
        """
        canvas_file = Path(canvas_path)
        if not canvas_file.exists():
            raise FileNotFoundError(f"Canvas文件不存在: {canvas_path}")

        try:
            with open(canvas_file, 'r', encoding='utf-8') as f:
                canvas_data = json.load(f)

            # 提取概念
            concepts = self._extract_concepts_from_nodes(canvas_data.get("nodes", []))

            # 提取显式关系（基于边）
            explicit_relationships = self._extract_explicit_relationships(
                canvas_data.get("edges", []), concepts
            )

            # 提取隐式关系（基于语义分析）
            implicit_relationships = self._extract_implicit_relationships(concepts)

            # 合并关系
            all_relationships = explicit_relationships + implicit_relationships

            # 计算关系强度和置信度
            enhanced_relationships = self._enhance_relationships(
                all_relationships, concepts, canvas_path
            )

            result = {
                "canvas_file": canvas_path,
                "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
                "concepts": concepts,
                "relationships": enhanced_relationships,
                "statistics": {
                    "total_concepts": len(concepts),
                    "total_relationships": len(enhanced_relationships),
                    "explicit_relationships": len(explicit_relationships),
                    "implicit_relationships": len(implicit_relationships),
                    "relationship_types": self._count_relationship_types(enhanced_relationships)
                },
                "canvas_metadata": {
                    "node_count": len(canvas_data.get("nodes", [])),
                    "edge_count": len(canvas_data.get("edges", []))
                }
            }

            logger.info(f"从{canvas_path}提取了{len(concepts)}个概念和{len(enhanced_relationships)}个关系")
            return result

        except json.JSONDecodeError as e:
            raise ValueError(f"Canvas文件JSON格式错误: {e}")
        except Exception as e:
            logger.error(f"概念提取失败: {e}")
            raise

    def _extract_concepts_from_nodes(self, nodes: List[Dict]) -> Dict[str, Dict]:
        """从Canvas节点中提取概念"""
        concepts = {}

        for node in nodes:
            node_id = node.get("id")
            if not node_id:
                continue

            node_text = node.get("text", "").strip()
            if not node_text:
                continue

            # 分词和概念提取
            concept_names = self._extract_concept_names_from_text(node_text)

            for concept_name in concept_names:
                if concept_name not in concepts:
                    concepts[concept_name] = {
                        "name": concept_name,
                        "source_nodes": [],
                        "descriptions": [],
                        "node_types": set(),
                        "colors": set(),
                        "aliases": set(),
                        "subject_areas": set(),
                        "confidence": 0.0,
                        "text_content": ""
                    }

                # 更新概念信息
                concept = concepts[concept_name]
                concept["source_nodes"].append(node_id)
                concept["descriptions"].append(node_text)
                concept["node_types"].add(node.get("type", "unknown"))
                concept["colors"].add(node.get("color", ""))
                concept["text_content"] += " " + node_text

                # 识别学科领域
                subject_areas = self._identify_subject_areas(node_text)
                concept["subject_areas"].update(subject_areas)

                # 计算置信度
                concept["confidence"] = self._calculate_concept_confidence(concept)

        # 转换set为list以便JSON序列化
        for concept in concepts.values():
            concept["node_types"] = list(concept["node_types"])
            concept["colors"] = list(concept["colors"])
            concept["subject_areas"] = list(concept["subject_areas"])
            concept["aliases"] = list(concept["aliases"])

        return concepts

    def _extract_concept_names_from_text(self, text: str) -> List[str]:
        """从文本中提取概念名称"""
        concepts = []

        # 方法1: 基于标点符号分割
        sentences = re.split(r'[。！？；\n]+', text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 2 and len(sentence) < 50:
                concepts.append(sentence)

        # 方法2: 基于冒号和括号
        colon_patterns = [
            r'([^：:\n]+)[:：]',  # 冒号前的内容
            r'【([^】]+)】',        # 【】中的内容
            r'（([^）]+)）',        # （）中的内容
            r'\(([^)]+)\)',         # ()中的内容
        ]

        for pattern in colon_patterns:
            matches = re.findall(pattern, text)
            concepts.extend(matches)

        # 方法3: 基于中文分词
        words = jieba.lcut(text)
        n_grams = self._generate_ngrams(words, min_len=2, max_len=5)
        concepts.extend(n_grams)

        # 去重和过滤
        unique_concepts = list(set(concepts))
        filtered_concepts = [
            concept for concept in unique_concepts
            if self._is_valid_concept(concept)
        ]

        return filtered_concepts

    def _generate_ngrams(self, words: List[str], min_len: int = 2, max_len: int = 5) -> List[str]:
        """生成n-gram词组"""
        ngrams = []
        for n in range(min_len, max_len + 1):
            for i in range(len(words) - n + 1):
                ngram = "".join(words[i:i+n])
                if self._is_valid_concept(ngram):
                    ngrams.append(ngram)
        return ngrams

    def _is_valid_concept(self, text: str) -> bool:
        """验证概念是否有效"""
        if not text or len(text.strip()) < 2:
            return False

        text = text.strip()

        # 过滤条件
        invalid_patterns = [
            r'^[0-9]+$',  # 纯数字
            r'^[，。！？；：""''（）【】\\s]+$',  # 纯标点
            r'^(是|的|了|在|有|和|与|或|但|而|就|都|也|还|又|再)$',  # 常用虚词
        ]

        for pattern in invalid_patterns:
            if re.match(pattern, text):
                return False

        # 长度限制
        if len(text) > 50:
            return False

        return True

    def _identify_subject_areas(self, text: str) -> Set[str]:
        """识别学科领域"""
        subject_areas = set()

        for subject, patterns in self.subject_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    subject_areas.add(subject)
                    break

        return subject_areas

    def _calculate_concept_confidence(self, concept: Dict) -> float:
        """计算概念置信度"""
        confidence = 0.0

        # 基于出现频率
        confidence += min(len(concept["source_nodes"]) * 0.2, 0.6)

        # 基于描述长度
        total_text_length = sum(len(desc) for desc in concept["descriptions"])
        confidence += min(total_text_length / 1000, 0.3)

        # 基于学科领域
        if concept["subject_areas"]:
            confidence += 0.1

        return min(confidence, 1.0)

    def _extract_explicit_relationships(self, edges: List[Dict], concepts: Dict) -> List[Dict]:
        """提取显式关系（基于Canvas边）"""
        relationships = []

        for edge in edges:
            from_node_id = edge.get("fromNode")
            to_node_id = edge.get("toNode")
            edge_label = edge.get("label", "")

            # 查找对应的概念
            from_concepts = self._find_concepts_by_node_id(from_node_id, concepts)
            to_concepts = self._find_concepts_by_node_id(to_node_id, concepts)

            for from_concept in from_concepts:
                for to_concept in to_concepts:
                    if from_concept == to_concept:
                        continue

                    # 推断关系类型
                    relationship_type = self._infer_relationship_type_from_edge(
                        edge_label, from_concept, to_concept
                    )

                    relationship = {
                        "source_concept": from_concept,
                        "target_concept": to_concept,
                        "relationship_type": relationship_type,
                        "relationship_strength": 0.8,  # 显式关系强度较高
                        "confidence_score": 0.9,  # 显式关系置信度较高
                        "source": "canvas_edge",
                        "evidence": {
                            "edge_label": edge_label,
                            "from_node_id": from_node_id,
                            "to_node_id": to_node_id
                        }
                    }
                    relationships.append(relationship)

        return relationships

    def _find_concepts_by_node_id(self, node_id: str, concepts: Dict) -> List[str]:
        """根据节点ID查找概念"""
        concept_names = []
        for concept_name, concept_data in concepts.items():
            if node_id in concept_data["source_nodes"]:
                concept_names.append(concept_name)
        return concept_names

    def _infer_relationship_type_from_edge(self, edge_label: str, from_concept: str, to_concept: str) -> str:
        """从边标签推断关系类型"""
        edge_label = edge_label.lower()

        # 基于关键词匹配
        for rel_type, keywords in self.relationship_keywords.items():
            for keyword in keywords:
                if keyword in edge_label:
                    return rel_type

        # 基于边的方向和内容推断
        if "推导" in edge_label or "导出" in edge_label:
            return "is_derived_from"
        elif "相似" in edge_label or "类似" in edge_label:
            return "is_similar_to"
        elif "矛盾" in edge_label or "对立" in edge_label:
            return "is_contradictory_of"
        elif "应用" in edge_label or "使用" in edge_label:
            return "is_applied_in"
        elif "例子" in edge_label or "实例" in edge_label:
            return "is_example_of"
        elif "包括" in edge_label or "包含" in edge_label:
            return "includes"
        else:
            return "is_related_to"  # 默认关系类型

    def _extract_implicit_relationships(self, concepts: Dict) -> List[Dict]:
        """提取隐式关系（基于语义分析）"""
        relationships = []

        if len(concepts) < 2:
            return relationships

        # 构建概念文档
        concept_names = list(concepts.keys())
        concept_texts = [concepts[name]["text_content"] for name in concept_names]

        # 计算TF-IDF向量
        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(concept_texts)
            similarity_matrix = cosine_similarity(tfidf_matrix)

            # 基于相似度发现关系
            for i in range(len(concept_names)):
                for j in range(i + 1, len(concept_names)):
                    similarity = similarity_matrix[i][j]

                    if similarity > 0.3:  # 相似度阈值
                        relationship_type = self._infer_relationship_from_similarity(
                            concept_names[i], concept_names[j], concepts, similarity
                        )

                        relationship = {
                            "source_concept": concept_names[i],
                            "target_concept": concept_names[j],
                            "relationship_type": relationship_type,
                            "relationship_strength": float(similarity),
                            "confidence_score": max(0.5, float(similarity)),
                            "source": "semantic_similarity",
                            "evidence": {
                                "similarity_score": float(similarity),
                                "method": "tfidf_cosine_similarity"
                            }
                        }
                        relationships.append(relationship)

        except Exception as e:
            logger.warning(f"TF-IDF分析失败: {e}")

        # 基于学科领域发现关系
        subject_relationships = self._extract_subject_based_relationships(concepts)
        relationships.extend(subject_relationships)

        return relationships

    def _infer_relationship_from_similarity(self, concept1: str, concept2: str,
                                           concepts: Dict, similarity: float) -> str:
        """基于相似度推断关系类型"""
        # 高相似度 -> 相似关系
        if similarity > 0.7:
            return "is_similar_to"

        # 中等相似度 -> 应用或包含关系
        elif similarity > 0.5:
            # 检查是否为应用关系
            if self._is_application_relationship(concept1, concept2, concepts):
                return "is_applied_in"
            else:
                return "is_related_to"

        # 低相似度 -> 前提或推导关系
        else:
            if self._is_prerequisite_relationship(concept1, concept2, concepts):
                return "is_prerequisite_for"
            else:
                return "is_related_to"

    def _is_application_relationship(self, concept1: str, concept2: str, concepts: Dict) -> bool:
        """判断是否为应用关系"""
        app_keywords = ["应用", "实践", "使用", "案例", "项目", "工程"]
        theory_keywords = ["理论", "原理", "概念", "定义", "公式", "定理"]

        concept1_text = concepts[concept1]["text_content"].lower()
        concept2_text = concepts[concept2]["text_content"].lower()

        concept1_is_app = any(kw in concept1_text for kw in app_keywords)
        concept2_is_theory = any(kw in concept2_text for kw in theory_keywords)

        return concept1_is_app and concept2_is_theory

    def _is_prerequisite_relationship(self, concept1: str, concept2: str, concepts: Dict) -> bool:
        """判断是否为前提关系"""
        basic_keywords = ["基础", "入门", "基本", "简单", "初级"]
        advanced_keywords = ["高级", "复杂", "进阶", "深入", "专业"]

        concept1_text = concepts[concept1]["text_content"].lower()
        concept2_text = concepts[concept2]["text_content"].lower()

        concept1_is_basic = any(kw in concept1_text for kw in basic_keywords)
        concept2_is_advanced = any(kw in concept2_text for kw in advanced_keywords)

        return concept1_is_basic and concept2_is_advanced

    def _extract_subject_based_relationships(self, concepts: Dict) -> List[Dict]:
        """基于学科领域提取关系"""
        relationships = []

        # 按学科分组概念
        subject_groups = {}
        for concept_name, concept_data in concepts.items():
            for subject in concept_data["subject_areas"]:
                if subject not in subject_groups:
                    subject_groups[subject] = []
                subject_groups[subject].append(concept_name)

        # 同学科内的概念创建相似关系
        for subject, concept_list in subject_groups.items():
            if len(concept_list) > 1:
                for i in range(len(concept_list)):
                    for j in range(i + 1, len(concept_list)):
                        relationship = {
                            "source_concept": concept_list[i],
                            "target_concept": concept_list[j],
                            "relationship_type": "is_similar_to",
                            "relationship_strength": 0.6,
                            "confidence_score": 0.7,
                            "source": "subject_area",
                            "evidence": {
                                "subject_area": subject,
                                "method": "subject_grouping"
                            }
                        }
                        relationships.append(relationship)

        return relationships

    def _enhance_relationships(self, relationships: List[Dict], concepts: Dict, canvas_path: str) -> List[Dict]:
        """增强关系信息"""
        enhanced_relationships = []

        for rel in relationships:
            # 计算综合强度
            enhanced_rel = rel.copy()

            # 基于概念置信度调整关系强度
            source_confidence = concepts[rel["source_concept"]]["confidence"]
            target_confidence = concepts[rel["target_concept"]]["confidence"]
            avg_concept_confidence = (source_confidence + target_confidence) / 2

            enhanced_rel["relationship_strength"] = min(1.0, rel["relationship_strength"] * avg_concept_confidence)

            # 添加时间戳
            enhanced_rel["discovery_timestamp"] = datetime.now(timezone.utc).isoformat()

            # 添加Canvas文件路径
            enhanced_rel["canvas_file"] = canvas_path

            # 验证关系合理性
            if self._validate_relationship(enhanced_rel, concepts):
                enhanced_relationships.append(enhanced_rel)

        return enhanced_relationships

    def _validate_relationship(self, relationship: Dict, concepts: Dict) -> bool:
        """验证关系的合理性"""
        source = relationship["source_concept"]
        target = relationship["target_concept"]

        # 检查概念是否存在
        if source not in concepts or target not in concepts:
            return False

        # 检查自环
        if source == target:
            return False

        # 检查关系强度
        if relationship["relationship_strength"] < 0.1:
            return False

        # 检查置信度
        if relationship["confidence_score"] < 0.3:
            return False

        return True

    def _count_relationship_types(self, relationships: List[Dict]) -> Dict[str, int]:
        """统计关系类型数量"""
        type_counts = {}
        for rel in relationships:
            rel_type = rel["relationship_type"]
            type_counts[rel_type] = type_counts.get(rel_type, 0) + 1
        return type_counts

    def cluster_concepts(self, concepts: Dict, eps: float = 0.5, min_samples: int = 2) -> List[List[str]]:
        """对概念进行聚类

        Args:
            concepts: 概念字典
            eps: DBSCAN聚类参数
            min_samples: DBSCAN最小样本数

        Returns:
            List[List[str]]: 聚类结果，每个子列表包含一组相关的概念
        """
        if len(concepts) < 2:
            return [[name] for name in concepts.keys()]

        concept_names = list(concepts.keys())
        concept_texts = [concepts[name]["text_content"] for name in concept_names]

        try:
            # 计算TF-IDF向量
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(concept_texts)
            similarity_matrix = cosine_similarity(tfidf_matrix)

            # 转换为距离矩阵
            distance_matrix = 1 - similarity_matrix

            # DBSCAN聚类
            clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed')
            cluster_labels = clustering.fit_predict(distance_matrix)

            # 组织聚类结果
            clusters = {}
            for i, label in enumerate(cluster_labels):
                if label == -1:  # 噪声点
                    label = f"noise_{i}"
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(concept_names[i])

            return list(clusters.values())

        except Exception as e:
            logger.warning(f"概念聚类失败: {e}")
            return [[name] for name in concept_names]


# 便利函数
async def extract_concepts_from_canvas(canvas_path: str) -> Dict[str, Any]:
    """从Canvas文件提取概念和关系的便利函数

    Args:
        canvas_path: Canvas文件路径

    Returns:
        Dict: 提取结果
    """
    extractor = ConceptExtractor()
    return extractor.extract_concepts_from_canvas(canvas_path)


async def extract_and_analyze_canvas(canvas_path: str) -> Dict[str, Any]:
    """提取并分析Canvas的概念网络

    Args:
        canvas_path: Canvas文件路径

    Returns:
        Dict: 包含提取结果和分析的完整报告
    """
    extractor = ConceptExtractor()
    extraction_result = extractor.extract_concepts_from_canvas(canvas_path)

    # 概念聚类
    concept_clusters = extractor.cluster_concepts(extraction_result["concepts"])

    # 生成分析报告
    analysis = {
        "extraction_result": extraction_result,
        "concept_clusters": concept_clusters,
        "cluster_statistics": {
            "total_clusters": len(concept_clusters),
            "largest_cluster_size": max(len(cluster) for cluster in concept_clusters) if concept_clusters else 0,
            "average_cluster_size": sum(len(cluster) for cluster in concept_clusters) / len(concept_clusters) if concept_clusters else 0
        },
        "recommendations": _generate_extraction_recommendations(extraction_result, concept_clusters)
    }

    return analysis


def _generate_extraction_recommendations(extraction_result: Dict, concept_clusters: List[List[str]]) -> List[str]:
    """生成提取建议"""
    recommendations = []

    stats = extraction_result["statistics"]
    total_concepts = stats["total_concepts"]
    total_relationships = stats["total_relationships"]

    # 概念数量建议
    if total_concepts < 5:
        recommendations.append("概念数量较少，建议检查Canvas内容的完整性")
    elif total_concepts > 50:
        recommendations.append("概念数量较多，建议考虑分批处理或细化主题")

    # 关系数量建议
    if total_relationships < total_concepts:
        recommendations.append("关系数量较少，建议添加更多概念间的连接")
    elif total_relationships > total_concepts * 3:
        recommendations.append("关系数量较多，建议检查是否存在冗余关系")

    # 聚类质量建议
    if concept_clusters:
        large_clusters = [cluster for cluster in concept_clusters if len(cluster) > 10]
        if large_clusters:
            recommendations.append(f"发现{len(large_clusters)}个大聚类，建议进一步细分主题")

    # 学科覆盖建议
    subject_areas = set()
    for concept in extraction_result["concepts"].values():
        subject_areas.update(concept["subject_areas"])

    if len(subject_areas) > 3:
        recommendations.append("涉及多个学科领域，建议按学科组织概念")

    return recommendations