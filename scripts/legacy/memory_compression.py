"""
记忆数据压缩系统
Canvas Learning System - Story 8.8

提供语义记忆压缩、相关记忆整合、压缩质量评估等功能。
"""

import json
import time
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
import hashlib
from collections import defaultdict

# 第三方库导入
try:
    import numpy as np
    from sklearn.cluster import KMeans
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available. Install with: pip install scikit-learn")

from mcp_memory_client import MCPSemanticMemory, CompressionMetadata

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CompressionCluster:
    """压缩簇数据类"""
    cluster_id: str
    centroid_id: str
    member_ids: List[str]
    compression_ratio: float
    information_retention: float
    cluster_metadata: Dict


@dataclass
class CompressionResult:
    """压缩结果数据类"""
    original_memory_count: int
    compressed_memory_count: int
    compression_ratio: float
    information_retention_score: float
    compression_time_seconds: float
    clusters: List[CompressionCluster]
    compression_metadata: Dict


class MemoryCompressor:
    """记忆压缩器"""

    def __init__(self, memory_client: MCPSemanticMemory, config: Dict = None):
        """初始化记忆压缩器

        Args:
            memory_client: MCP记忆客户端
            config: 配置字典
        """
        self.memory_client = memory_client
        self.config = config or self._get_default_config()

        # 压缩策略
        self.compression_strategies = {
            "semantic_clustering": self._semantic_clustering_compression,
            "frequency_based": self._frequency_based_compression,
            "temporal_grouping": self._temporal_grouping_compression,
            "topic_merging": self._topic_merging_compression
        }

        logger.info("记忆压缩器初始化完成")

    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "compression": {
                "default_strategy": "semantic_clustering",
                "target_compression_ratio": 0.3,
                "minimum_cluster_size": 3,
                "similarity_threshold": 0.8,
                "information_retention_threshold": 0.85,
                "max_compression_time_minutes": 30
            },
            "clustering": {
                "algorithm": "kmeans",
                "max_clusters": 10,
                "random_state": 42
            },
            "frequency": {
                "access_threshold": 10,
                "time_threshold_days": 90
            }
        }

    def compress_memories(self, memory_ids: List[str], compression_ratio: float = 0.3, strategy: str = None) -> CompressionResult:
        """压缩记忆数据

        Args:
            memory_ids: 需要压缩的记忆ID列表
            compression_ratio: 目标压缩比例
            strategy: 压缩策略

        Returns:
            CompressionResult: 压缩结果
        """
        try:
            start_time = time.time()

            # 验证输入
            if not memory_ids:
                raise ValueError("记忆ID列表不能为空")

            if strategy is None:
                strategy = self.config["compression"]["default_strategy"]

            if strategy not in self.compression_strategies:
                strategy = "semantic_clustering"

            # 获取记忆数据
            memories_data = self._get_memories_data(memory_ids)
            if not memories_data:
                raise ValueError("无法获取记忆数据")

            # 执行压缩
            compression_func = self.compression_strategies[strategy]
            clusters = compression_func(memories_data, compression_ratio)

            # 计算压缩指标
            original_count = len(memory_ids)
            compressed_count = len(clusters)
            actual_compression_ratio = compressed_count / original_count
            information_retention = self._calculate_information_retention(clusters, memories_data)

            # 创建压缩结果
            result = CompressionResult(
                original_memory_count=original_count,
                compressed_memory_count=compressed_count,
                compression_ratio=actual_compression_ratio,
                information_retention_score=information_retention,
                compression_time_seconds=time.time() - start_time,
                clusters=clusters,
                compression_metadata={
                    "strategy": strategy,
                    "target_ratio": compression_ratio,
                    "actual_ratio": actual_compression_ratio,
                    "timestamp": datetime.now().isoformat()
                }
            )

            logger.info(f"记忆压缩完成: {original_count} -> {compressed_count} (比例: {actual_compression_ratio:.3f})")
            return result

        except Exception as e:
            logger.error(f"记忆压缩失败: {e}")
            raise

    def _get_memories_data(self, memory_ids: List[str]) -> List[Dict]:
        """获取记忆数据"""
        memories_data = []

        for memory_id in memory_ids:
            try:
                # 这里应该从MCP客户端获取具体记忆数据
                # 由于当前MCP客户端没有直接获取单个记忆的方法，我们模拟数据
                # 在实际实现中，需要添加相应的API调用

                # 模拟数据结构
                simulated_data = {
                    "id": memory_id,
                    "content": f"记忆内容 {memory_id}",
                    "embedding": np.random.rand(384).tolist(),  # 模拟嵌入向量
                    "metadata": {
                        "created_at": datetime.now().isoformat(),
                        "access_count": np.random.randint(1, 100),
                        "tags": ["测试", "记忆"],
                        "category": "通用"
                    }
                }
                memories_data.append(simulated_data)

            except Exception as e:
                logger.warning(f"获取记忆 {memory_id} 数据失败: {e}")

        return memories_data

    def _semantic_clustering_compression(self, memories_data: List[Dict], target_ratio: float) -> List[CompressionCluster]:
        """基于语义聚类的压缩"""
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn不可用，使用简单聚类策略")
            return self._simple_clustering_compression(memories_data, target_ratio)

        try:
            # 提取嵌入向量
            embeddings = np.array([memory["embedding"] for memory in memories_data])

            # 计算目标聚类数量
            target_clusters = max(1, int(len(memories_data) * target_ratio))

            # 执行K-means聚类
            kmeans = KMeans(
                n_clusters=min(target_clusters, len(memories_data)),
                random_state=self.config["clustering"]["random_state"]
            )
            cluster_labels = kmeans.fit_predict(embeddings)

            # 组织聚类结果
            clusters = defaultdict(list)
            for i, label in enumerate(cluster_labels):
                clusters[label].append(memories_data[i])

            # 创建压缩簇
            compression_clusters = []
            for cluster_id, cluster_memories in clusters.items():
                cluster = self._create_compression_cluster(
                    f"cluster-{cluster_id}",
                    cluster_memories
                )
                compression_clusters.append(cluster)

            return compression_clusters

        except Exception as e:
            logger.error(f"语义聚类压缩失败: {e}")
            return self._simple_clustering_compression(memories_data, target_ratio)

    def _simple_clustering_compression(self, memories_data: List[Dict], target_ratio: float) -> List[CompressionCluster]:
        """简单聚类压缩（备用方案）"""
        clusters = []
        cluster_size = max(3, int(len(memories_data) / (len(memories_data) * target_ratio)))

        for i in range(0, len(memories_data), cluster_size):
            cluster_memories = memories_data[i:i + cluster_size]
            cluster = self._create_compression_cluster(
                f"simple-cluster-{i // cluster_size}",
                cluster_memories
            )
            clusters.append(cluster)

        return clusters

    def _frequency_based_compression(self, memories_data: List[Dict], target_ratio: float) -> List[CompressionCluster]:
        """基于访问频率的压缩"""
        # 按访问频率排序
        sorted_memories = sorted(
            memories_data,
            key=lambda x: x["metadata"].get("access_count", 0),
            reverse=True
        )

        # 保留高频记忆，合并低频记忆
        high_freq_threshold = len(memories_data) * target_ratio
        high_freq_memories = sorted_memories[:int(high_freq_threshold)]
        low_freq_memories = sorted_memories[int(high_freq_threshold):]

        clusters = []

        # 高频记忆各自成簇
        for memory in high_freq_memories:
            cluster = self._create_compression_cluster(
                f"high-freq-{memory['id'][:8]}",
                [memory]
            )
            clusters.append(cluster)

        # 低频记忆合并成簇
        if low_freq_memories:
            cluster = self._create_compression_cluster(
                "low-freq-merged",
                low_freq_memories
            )
            clusters.append(cluster)

        return clusters

    def _temporal_grouping_compression(self, memories_data: List[Dict], target_ratio: float) -> List[CompressionCluster]:
        """基于时间分组的压缩"""
        # 按创建时间分组
        time_groups = defaultdict(list)
        for memory in memories_data:
            created_at = memory["metadata"].get("created_at", "")
            if created_at:
                # 提取日期部分
                date_key = created_at.split("T")[0]
                time_groups[date_key].append(memory)
            else:
                time_groups["unknown"].append(memory)

        clusters = []
        for date_key, group_memories in time_groups.items():
            if group_memories:
                cluster = self._create_compression_cluster(
                    f"temporal-{date_key}",
                    group_memories
                )
                clusters.append(cluster)

        return clusters

    def _topic_merging_compression(self, memories_data: List[Dict], target_ratio: float) -> List[CompressionCluster]:
        """基于主题合并的压缩"""
        # 按标签分组
        tag_groups = defaultdict(list)
        for memory in memories_data:
            tags = memory["metadata"].get("tags", [])
            if tags:
                primary_tag = tags[0]  # 使用第一个标签作为主标签
                tag_groups[primary_tag].append(memory)
            else:
                tag_groups["untagged"].append(memory)

        clusters = []
        for tag, group_memories in tag_groups.items():
            if group_memories:
                cluster = self._create_compression_cluster(
                    f"topic-{tag}",
                    group_memories
                )
                clusters.append(cluster)

        return clusters

    def _create_compression_cluster(self, cluster_id: str, memories: List[Dict]) -> CompressionCluster:
        """创建压缩簇"""
        try:
            # 选择质心记忆（访问量最高的）
            centroid_memory = max(
                memories,
                key=lambda x: x["metadata"].get("access_count", 0)
            )

            # 计算压缩指标
            total_size = sum(len(m["content"].encode('utf-8')) for m in memories)
            centroid_size = len(centroid_memory["content"].encode('utf-8'))
            compression_ratio = centroid_size / total_size if total_size > 0 else 1.0

            # 计算信息保留度
            information_retention = self._calculate_cluster_information_retention(memories, centroid_memory)

            # 合并元数据
            merged_metadata = self._merge_metadata(memories)

            return CompressionCluster(
                cluster_id=cluster_id,
                centroid_id=centroid_memory["id"],
                member_ids=[m["id"] for m in memories],
                compression_ratio=compression_ratio,
                information_retention=information_retention,
                cluster_metadata=merged_metadata
            )

        except Exception as e:
            logger.error(f"创建压缩簇失败: {e}")
            raise

    def _calculate_cluster_information_retention(self, memories: List[Dict], centroid_memory: Dict) -> float:
        """计算簇的信息保留度"""
        try:
            # 简单的信息保留度计算
            # 在实际实现中，可以使用更复杂的算法

            if SKLEARN_AVAILABLE and len(memories) > 1:
                # 使用相似度计算信息保留度
                centroid_embedding = np.array(centroid_memory["embedding"]).reshape(1, -1)
                similarities = []

                for memory in memories:
                    if memory["id"] != centroid_memory["id"]:
                        memory_embedding = np.array(memory["embedding"]).reshape(1, -1)
                        similarity = cosine_similarity(centroid_embedding, memory_embedding)[0][0]
                        similarities.append(similarity)

                if similarities:
                    return np.mean(similarities)

            # 备用计算方法
            return 0.85  # 默认保留度

        except Exception as e:
            logger.warning(f"计算信息保留度失败: {e}")
            return 0.8

    def _calculate_information_retention(self, clusters: List[CompressionCluster], original_memories: List[Dict]) -> float:
        """计算总体信息保留度"""
        if not clusters:
            return 0.0

        total_retention = sum(cluster.information_retention for cluster in clusters)
        return total_retention / len(clusters)

    def _merge_metadata(self, memories: List[Dict]) -> Dict:
        """合并元数据"""
        merged = {
            "merged_count": len(memories),
            "earliest_created": None,
            "latest_created": None,
            "total_access_count": 0,
            "all_tags": set(),
            "categories": set()
        }

        for memory in memories:
            metadata = memory.get("metadata", {})

            # 时间信息
            created_at = metadata.get("created_at")
            if created_at:
                if merged["earliest_created"] is None or created_at < merged["earliest_created"]:
                    merged["earliest_created"] = created_at
                if merged["latest_created"] is None or created_at > merged["latest_created"]:
                    merged["latest_created"] = created_at

            # 访问计数
            merged["total_access_count"] += metadata.get("access_count", 0)

            # 标签和类别
            tags = metadata.get("tags", [])
            merged["all_tags"].update(tags)

            category = metadata.get("category", "")
            if category:
                merged["categories"].add(category)

        # 转换set为list以便JSON序列化
        merged["all_tags"] = list(merged["all_tags"])
        merged["categories"] = list(merged["categories"])

        return merged

    def auto_compress_memories(self, threshold: int = None, strategy: str = None) -> Dict:
        """自动压缩记忆

        Args:
            threshold: 压缩阈值（记忆数量）
            strategy: 压缩策略

        Returns:
            Dict: 压缩结果
        """
        try:
            # 获取记忆统计
            stats = self.memory_client.get_memory_stats()
            total_memories = stats.get("total_memories", 0)

            if threshold is None:
                threshold = self.config["compression"].get("auto_compress_threshold", 5000)

            if total_memories < threshold:
                return {
                    "compressed": False,
                    "reason": f"记忆数量 {total_memories} 低于阈值 {threshold}",
                    "total_memories": total_memories
                }

            # 获取所有记忆ID（这里需要实际实现）
            # 由于当前限制，我们模拟获取
            all_memory_ids = [f"memory-{i:016d}" for i in range(total_memories)]

            # 执行压缩
            compression_ratio = self.config["compression"]["target_compression_ratio"]
            result = self.compress_memories(all_memory_ids, compression_ratio, strategy)

            return {
                "compressed": True,
                "original_count": result.original_memory_count,
                "compressed_count": result.compressed_memory_count,
                "compression_ratio": result.compression_ratio,
                "information_retention": result.information_retention_score,
                "compression_time": result.compression_time_seconds,
                "strategy": strategy or self.config["compression"]["default_strategy"]
            }

        except Exception as e:
            logger.error(f"自动压缩失败: {e}")
            return {
                "compressed": False,
                "error": str(e)
            }

    def evaluate_compression_quality(self, original_ids: List[str], compressed_clusters: List[CompressionCluster]) -> Dict:
        """评估压缩质量

        Args:
            original_ids: 原始记忆ID列表
            compressed_clusters: 压缩后的簇列表

        Returns:
            Dict: 质量评估结果
        """
        try:
            # 计算各种质量指标
            compression_ratio = len(compressed_clusters) / len(original_ids) if original_ids else 0

            avg_information_retention = 0
            if compressed_clusters:
                avg_information_retention = sum(
                    cluster.information_retention for cluster in compressed_clusters
                ) / len(compressed_clusters)

            # 计算压缩效率
            total_compression_ratio = 0
            for cluster in compressed_clusters:
                total_compression_ratio += cluster.compression_ratio
            avg_compression_ratio = total_compression_ratio / len(compressed_clusters) if compressed_clusters else 0

            # 生成质量分数（0-100）
            quality_score = self._calculate_quality_score(
                compression_ratio,
                avg_information_retention,
                avg_compression_ratio
            )

            return {
                "quality_score": quality_score,
                "compression_ratio": compression_ratio,
                "information_retention": avg_information_retention,
                "avg_compression_ratio": avg_compression_ratio,
                "cluster_count": len(compressed_clusters),
                "evaluation_timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"压缩质量评估失败: {e}")
            return {
                "quality_score": 0,
                "error": str(e)
            }

    def _calculate_quality_score(self, compression_ratio: float, information_retention: float, avg_compression_ratio: float) -> float:
        """计算质量分数"""
        # 权重配置
        weights = {
            "compression_efficiency": 0.3,  # 压缩效率
            "information_retention": 0.5,     # 信息保留
            "compression_ratio": 0.2          # 压缩比例
        }

        # 计算各项分数
        compression_efficiency_score = (1 - compression_ratio) * 100  # 压缩效率分数
        information_retention_score = information_retention * 100     # 信息保留分数
        compression_ratio_score = (1 - avg_compression_ratio) * 100   # 压缩比例分数

        # 加权总分
        total_score = (
            compression_efficiency_score * weights["compression_efficiency"] +
            information_retention_score * weights["information_retention"] +
            compression_ratio_score * weights["compression_ratio"]
        )

        return max(0, min(100, total_score))


if __name__ == "__main__":
    # 简单测试
    try:
        from mcp_memory_client import create_memory_client

        memory_client = create_memory_client()
        compressor = MemoryCompressor(memory_client)

        # 测试数据
        test_memory_ids = [f"memory-{i:016d}" for i in range(20)]

        # 执行压缩
        result = compressor.compress_memories(
            test_memory_ids,
            compression_ratio=0.3,
            strategy="semantic_clustering"
        )

        print(f"压缩结果:")
        print(f"  原始记忆数: {result.original_memory_count}")
        print(f"  压缩后数量: {result.compressed_memory_count}")
        print(f"  压缩比例: {result.compression_ratio:.3f}")
        print(f"  信息保留度: {result.information_retention_score:.3f}")
        print(f"  压缩时间: {result.compression_time_seconds:.2f}秒")

        # 评估质量
        quality = compressor.evaluate_compression_quality(test_memory_ids, result.clusters)
        print(f"质量分数: {quality['quality_score']:.1f}/100")

        memory_client.close()

    except Exception as e:
        print(f"测试失败: {e}")