"""
智能缓存管理器 - Canvas学习系统

本模块实现智能缓存机制，包括：
- 内容相似度检测
- LRU + LFU混合缓存策略
- 压缩存储
- 缓存命中率优化

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-27
Story: 10.6 - Task 3
"""

import asyncio
import hashlib
import json
import gzip
import time
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import threading
from collections import OrderedDict
import statistics

# 文本相似度计算
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: sklearn not available, using simple similarity detection")


class CacheEntryType(Enum):
    """缓存条目类型"""
    AGENT_RESPONSE = "agent_response"
    PROCESSED_NODE = "processed_node"
    ANALYSIS_RESULT = "analysis_result"
    SIMILAR_CONTENT = "similar_content"
    RAW_DATA = "raw_data"


class CacheEvictionPolicy(Enum):
    """缓存驱逐策略"""
    LRU = "lru"      # 最近最少使用
    LFU = "lfu"      # 最少使用频率
    LRU_LFU = "lru_lfu"  # 混合策略
    TTL = "ttl"       # 基于时间


@dataclass
class CacheEntry:
    """缓存条目"""
    cache_key: str
    content_hash: str
    cached_result: Any
    content_type: CacheEntryType
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    size_bytes: int = 0
    ttl_seconds: int = 3600  # 1小时
    compression_enabled: bool = True
    similarity_threshold: float = 0.8

    @property
    def is_expired(self) -> bool:
        """检查是否过期"""
        return (datetime.now() - self.created_at).total_seconds() > self.ttl_seconds

    @property
    def access_frequency(self) -> float:
        """访问频率 (次/小时)"""
        age_hours = max((datetime.now() - self.created_at).total_seconds() / 3600, 0.1)
        return self.access_count / age_hours

    @property
    def age_seconds(self) -> float:
        """缓存年龄（秒）"""
        return (datetime.now() - self.created_at).total_seconds()

    def update_access(self) -> None:
        """更新访问信息"""
        self.last_accessed = datetime.now()
        self.access_count += 1

    def calculate_similarity_score(self, content: str) -> float:
        """计算内容相似度分数（简化版）"""
        if not isinstance(self.cached_result, str):
            return 0.0

        # 简单的相似度计算（基于共同字符）
        set1 = set(self.cached_result.lower())
        set2 = set(content.lower())

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0


@dataclass
class CacheStatistics:
    """缓存统计信息"""
    total_entries: int = 0
    total_size_mb: float = 0.0
    hit_rate: float = 0.0  # 命中率 0-1
    miss_rate: float = 0.0  # 未命中率 0-1
    eviction_count: int = 0  # 驱逐次数
    compression_ratio: float = 1.0  # 压缩比
    average_access_time_ms: float = 0.0
    cache_efficiency: float = 0.0  # 缓存效率分数 0-100
    last_updated: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """计算派生统计"""
        self.miss_rate = 1.0 - self.hit_rate
        self.cache_efficiency = self.hit_rate * 100 * (1 - self.eviction_count / max(self.total_entries, 1))


class IntelligentCacheManager:
    """智能缓存管理器

    提供内容感知的智能缓存功能，支持相似度检测、
    压缩存储和自适应驱逐策略。
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化智能缓存管理器

        Args:
            config: 缓存配置
        """
        self.config = config

        # 缓存配置
        self.max_size_mb = config.get("max_cache_size_mb", 500)
        self.max_entries = config.get("max_entries", 10000)
        self.default_ttl = config.get("default_ttl_seconds", 3600)
        self.compression_threshold = config.get("compression_threshold_bytes", 1024)
        self.similarity_threshold = config.get("similarity_threshold", 0.8)
        self.enable_compression = config.get("enable_compression", True)
        self.eviction_policy = CacheEvictionPolicy(
            config.get("eviction_policy", "lru_lfu")
        )

        # 缓存存储
        self.cache_storage: OrderedDict[str, CacheEntry] = OrderedDict()
        self.similarity_index: Dict[str, List[str]] = {}  # 内容hash到cache_keys的映射

        # 统计信息
        self.stats = CacheStatistics()
        self.hit_count = 0
        self.miss_count = 0
        self.total_access_time = 0.0
        self.access_count = 0

        # 文本相似度检测器
        self.vectorizer = None
        self.tfidf_cache: Dict[str, Any] = {}
        if SKLEARN_AVAILABLE:
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )

        # 后台任务
        self.cleanup_task: Optional[asyncio.Task] = None
        self.cleanup_interval = config.get("cleanup_interval_seconds", 300)  # 5分钟
        self.monitoring_active = False

        # 线程锁
        self._lock = threading.RLock()

        print(f"IntelligentCacheManager initialized (max_size: {self.max_size_mb}MB)")

    async def start_monitoring(self) -> None:
        """启动缓存监控"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop_monitoring(self) -> None:
        """停止缓存监控"""
        self.monitoring_active = False
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

    async def _cleanup_loop(self) -> None:
        """清理主循环"""
        while self.monitoring_active:
            try:
                # 清理过期条目
                await self._cleanup_expired_entries()

                # 清理空间不足
                await self._cleanup_for_space()

                # 更新统计信息
                await self._update_statistics()

                await asyncio.sleep(self.cleanup_interval)

            except Exception as e:
                print(f"Cache cleanup error: {e}")
                await asyncio.sleep(60)

    def _generate_cache_key(self, content: str, agent_type: str = "") -> str:
        """生成缓存键

        Args:
            content: 内容
            agent_type: Agent类型

        Returns:
            str: 缓存键
        """
        # 生成内容哈希
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

        # 组合缓存键
        cache_key = f"{agent_type}:{content_hash}"

        return cache_key

    def _calculate_content_hash(self, content: Any) -> str:
        """计算内容哈希

        Args:
            content: 内容对象

        Returns:
            str: 内容哈希
        """
        # 序列化内容
        if isinstance(content, str):
            serialized = content
        elif isinstance(content, dict):
            serialized = json.dumps(content, sort_keys=True)
        else:
            serialized = pickle.dumps(content)

        # 计算哈希
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

    def _compress_data(self, data: Any) -> Tuple[bytes, bool]:
        """压缩数据

        Args:
            data: 要压缩的数据

        Returns:
            Tuple[bytes, bool]: (压缩后的数据, 是否压缩)
        """
        if not self.enable_compression:
            if isinstance(data, str):
                return data.encode('utf-8'), False
            else:
                return pickle.dumps(data), False

        # 序列化数据
        if isinstance(data, str):
            serialized = data.encode('utf-8')
        else:
            serialized = pickle.dumps(data)

        # 检查是否需要压缩
        if len(serialized) < self.compression_threshold:
            return serialized, False

        # 压缩数据
        compressed = gzip.compress(serialized, level=6)

        # 只有压缩有效才使用压缩
        if len(compressed) < len(serialized) * 0.9:
            return compressed, True
        else:
            return serialized, False

    def _decompress_data(self, compressed_data: bytes, is_compressed: bool) -> Any:
        """解压数据

        Args:
            compressed_data: 压缩的数据
            is_compressed: 是否已压缩

        Returns:
            Any: 解压后的数据
        """
        # 解压
        if is_compressed:
            decompressed = gzip.decompress(compressed_data)
        else:
            decompressed = compressed_data

        # 尝试多种反序列化方式
        try:
            # 尝试作为JSON解析
            decoded = decompressed.decode('utf-8')
            return json.loads(decoded)
        except:
            try:
                # 尝试作为pickle解析
                return pickle.loads(decompressed)
            except:
                # 最后作为字符串返回
                return decompressed.decode('utf-8')

    async def get_cached_result(self, cache_key: str) -> Optional[Any]:
        """获取缓存结果

        Args:
            cache_key: 缓存键

        Returns:
            Optional[Any]: 缓存的结果，如果不存在返回None
        """
        start_time = time.time()

        with self._lock:
            if cache_key not in self.cache_storage:
                self.miss_count += 1
                return None

            entry = self.cache_storage[cache_key]

            # 检查是否过期
            if entry.is_expired:
                await self._remove_entry(cache_key)
                self.miss_count += 1
                return None

            # 更新访问信息
            entry.update_access()

            # 移到最后（LRU）
            self.cache_storage.move_to_end(cache_key)

            # 解压数据
            result = self._decompress_data(entry.cached_result, entry.compression_enabled)

            self.hit_count += 1

        # 记录访问时间
        self.access_count += 1
        self.total_access_time += (time.time() - start_time) * 1000

        return result

    async def cache_result(self,
                          cache_key: str,
                          result: Any,
                          content_type: CacheEntryType,
                          ttl_seconds: Optional[int] = None) -> bool:
        """缓存结果

        Args:
            cache_key: 缓存键
            result: 要缓存的结果
            content_type: 内容类型
            ttl_seconds: 生存时间（秒）

        Returns:
            bool: 缓存是否成功
        """
        try:
            with self._lock:
                # 检查空间限制
                if len(self.cache_storage) >= self.max_entries:
                    await self._evict_entries(1)

                # 压缩数据
                compressed_data, is_compressed = self._compress_data(result)

                # 计算内容哈希
                content_hash = self._calculate_content_hash(result)

                # 创建缓存条目
                entry = CacheEntry(
                    cache_key=cache_key,
                    content_hash=content_hash,
                    cached_result=compressed_data,
                    content_type=content_type,
                    ttl_seconds=ttl_seconds or self.default_ttl,
                    compression_enabled=is_compressed,
                    size_bytes=len(compressed_data)
                )

                # 存储到缓存
                self.cache_storage[cache_key] = entry

                # 更新相似度索引
                if content_hash not in self.similarity_index:
                    self.similarity_index[content_hash] = []
                self.similarity_index[content_hash].append(cache_key)

                # 检查总大小限制
                await self._check_size_limit()

                return True

        except Exception as e:
            print(f"Failed to cache result: {e}")
            return False

    async def invalidate_cache(self, pattern: Optional[str] = None) -> int:
        """使缓存失效

        Args:
            pattern: 可选的模式匹配，如果为None则清空所有缓存

        Returns:
            int: 清除的条目数
        """
        with self._lock:
            if pattern is None:
                # 清空所有缓存
                count = len(self.cache_storage)
                self.cache_storage.clear()
                self.similarity_index.clear()
                return count
            else:
                # 模式匹配清除
                keys_to_remove = [
                    key for key in self.cache_storage.keys()
                    if pattern in key
                ]

                for key in keys_to_remove:
                    await self._remove_entry(key)

                return len(keys_to_remove)

    async def calculate_content_similarity(self, content1: str, content2: str) -> float:
        """计算内容相似度

        Args:
            content1: 内容1
            content2: 内容2

        Returns:
            float: 相似度分数 0-1
        """
        if not SKLEARN_AVAILABLE:
            # 简单相似度计算
            set1 = set(content1.lower().split())
            set2 = set(content2.lower().split())

            intersection = len(set1 & set2)
            union = len(set1 | set2)

            return intersection / union if union > 0 else 0.0

        # 使用TF-IDF计算相似度
        try:
            documents = [content1, content2]

            # 如果缓存中有向量器，复用
            cache_key = f"tfidf_{hash(content1 + content2)}"
            if cache_key in self.tfidf_cache:
                vectors = self.tfidf_cache[cache_key]
            else:
                vectors = self.vectorizer.fit_transform(documents).toarray()
                # 缓存向量（限制缓存大小）
                if len(self.tfidf_cache) < 100:
                    self.tfidf_cache[cache_key] = vectors

            # 计算余弦相似度
            similarity = cosine_similarity([vectors[0]], [vectors[1]])[0][0]

            return float(similarity)

        except Exception as e:
            print(f"Similarity calculation error: {e}")
            # 回退到简单计算
            return await self._calculate_simple_similarity(content1, content2)

    async def _calculate_simple_similarity(self, content1: str, content2: str) -> float:
        """简单相似度计算（回退方案）"""
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    async def find_similar_cached_results(self, content: str, threshold: float = None) -> List[CacheEntry]:
        """查找相似的缓存结果

        Args:
            content: 查询内容
            threshold: 相似度阈值

        Returns:
            List[CacheEntry]: 相似的缓存条目列表
        """
        if threshold is None:
            threshold = self.similarity_threshold

        similar_entries = []

        with self._lock:
            for entry in self.cache_storage.values():
                # 只对文本内容进行相似度比较
                if isinstance(entry.cached_result, bytes):
                    # 解压检查内容类型
                    try:
                        decompressed = self._decompress_data(
                            entry.cached_result,
                            entry.compression_enabled
                        )
                        if isinstance(decompressed, str):
                            similarity = await self.calculate_content_similarity(
                                content, decompressed
                            )
                            if similarity >= threshold:
                                similar_entries.append(entry)
                    except:
                        pass

        # 按相似度排序
        similar_entries.sort(
            key=lambda e: e.calculate_similarity_score(content),
            reverse=True
        )

        return similar_entries

    async def get_cache_statistics(self) -> CacheStatistics:
        """获取缓存统计信息

        Returns:
            CacheStatistics: 缓存统计
        """
        await self._update_statistics()
        return self.stats

    async def _update_statistics(self) -> None:
        """更新统计信息"""
        with self._lock:
            self.stats.total_entries = len(self.cache_storage)

            # 计算总大小
            total_size = sum(entry.size_bytes for entry in self.cache_storage.values())
            self.stats.total_size_mb = total_size / 1024 / 1024

            # 计算命中率
            total_requests = self.hit_count + self.miss_count
            if total_requests > 0:
                self.stats.hit_rate = self.hit_count / total_requests
                self.stats.miss_rate = self.miss_count / total_requests

            # 计算平均访问时间
            if self.access_count > 0:
                self.stats.average_access_time_ms = self.total_access_time / self.access_count

            # 计算压缩比
            if self.cache_storage:
                original_sizes = []
                compressed_sizes = []

                for entry in self.cache_storage.values():
                    if entry.compression_enabled:
                        # 估算原始大小（这需要额外的存储来保存原始大小）
                        # 这里使用简化的估算
                        compressed_sizes.append(entry.size_bytes)
                        original_sizes.append(entry.size_bytes * 1.5)  # 假设1.5倍压缩比

                if compressed_sizes:
                    self.stats.compression_ratio = sum(compressed_sizes) / sum(original_sizes)

            # 更新时间戳
            self.stats.last_updated = datetime.now()

    async def optimize_cache(self) -> Dict[str, Any]:
        """优化缓存

        Returns:
            Dict[str, Any]: 优化结果
        """
        optimization_results = {
            "entries_removed": 0,
            "space_freed_mb": 0.0,
            "hit_rate_before": self.stats.hit_rate,
            "hit_rate_after": 0.0,
            "optimizations_applied": []
        }

        # 1. 清理过期条目
        expired_count = await self._cleanup_expired_entries()
        optimization_results["entries_removed"] += expired_count
        optimization_results["optimizations_applied"].append("expired_entries_cleanup")

        # 2. 清理低频访问条目
        low_freq_count = await self._cleanup_low_frequency_entries()
        optimization_results["entries_removed"] += low_freq_count
        optimization_results["optimizations_applied"].append("low_frequency_cleanup")

        # 3. 重新压缩大条目
        recompressed_count = await self._recompress_entries()
        optimization_results["optimizations_applied"].append("recompression")

        # 4. 更新统计
        await self._update_statistics()
        optimization_results["hit_rate_after"] = self.stats.hit_rate

        return optimization_results

    async def _cleanup_expired_entries(self) -> int:
        """清理过期条目"""
        expired_keys = [
            key for key, entry in self.cache_storage.items()
            if entry.is_expired
        ]

        for key in expired_keys:
            await self._remove_entry(key)

        return len(expired_keys)

    async def _cleanup_low_frequency_entries(self, threshold: float = 0.01) -> int:
        """清理低频访问条目"""
        low_freq_keys = [
            key for key, entry in self.cache_storage.items()
            if entry.access_frequency < threshold
        ]

        # 只清理一部分，避免误删
        for key in low_freq_keys[:len(low_freq_keys)//2]:
            await self._remove_entry(key)

        return len(low_freq_keys[:len(low_freq_keys)//2])

    async def _recompress_entries(self) -> int:
        """重新压缩条目"""
        recompressed_count = 0

        for key, entry in list(self.cache_storage.items()):
            if not entry.compression_enabled and entry.size_bytes > self.compression_threshold:
                # 尝试压缩未压缩的大条目
                data = self._decompress_data(entry.cached_result, False)
                compressed_data, is_compressed = self._compress_data(data)

                if is_compressed and len(compressed_data) < entry.size_bytes:
                    # 更新条目
                    entry.cached_result = compressed_data
                    entry.compression_enabled = True
                    entry.size_bytes = len(compressed_data)
                    recompressed_count += 1

        return recompressed_count

    async def _check_size_limit(self) -> None:
        """检查并处理大小限制"""
        total_size = sum(entry.size_bytes for entry in self.cache_storage.values())
        max_size_bytes = self.max_size_mb * 1024 * 1024

        if total_size > max_size_bytes:
            # 计算需要释放的空间
            space_to_free = total_size - max_size_bytes * 0.8  # 清理到80%
            await self._evict_for_space(space_to_free)

    async def _evict_for_space(self, bytes_to_free: int) -> int:
        """为释放空间而驱逐条目"""
        freed_bytes = 0
        evicted_count = 0

        # 根据策略排序
        entries = list(self.cache_storage.items())

        if self.eviction_policy == CacheEvictionPolicy.LRU:
            # 最近最少使用
            entries.sort(key=lambda x: x[1].last_accessed)
        elif self.eviction_policy == CacheEvictionPolicy.LFU:
            # 最少使用频率
            entries.sort(key=lambda x: x[1].access_frequency)
        elif self.eviction_policy == CacheEvictionPolicy.LRU_LFU:
            # 混合策略
            entries.sort(key=lambda x: (
                x[1].access_frequency * 0.6 +
                (time.time() - x[1].last_accessed.timestamp()) / 3600 * 0.4
            ))
        else:  # TTL
            # 已经过期的应该先被清理
            entries.sort(key=lambda x: x[1].created_at)

        # 驱逐条目直到释放足够空间
        for key, entry in entries:
            if freed_bytes >= bytes_to_free:
                break

            await self._remove_entry(key)
            freed_bytes += entry.size_bytes
            evicted_count += 1

        return evicted_count

    async def _evict_entries(self, count: int) -> None:
        """驱逐指定数量的条目"""
        evicted = 0

        for key in list(self.cache_storage.keys()):
            if evicted >= count:
                break

            await self._remove_entry(key)
            evicted += 1

        self.stats.eviction_count += evicted

    async def _remove_entry(self, cache_key: str) -> None:
        """移除缓存条目"""
        if cache_key in self.cache_storage:
            entry = self.cache_storage.pop(cache_key)

            # 从相似度索引中移除
            if entry.content_hash in self.similarity_index:
                if cache_key in self.similarity_index[entry.content_hash]:
                    self.similarity_index[entry.content_hash].remove(cache_key)

                # 如果没有其他引用，删除索引条目
                if not self.similarity_index[entry.content_hash]:
                    del self.similarity_index[entry.content_hash]

    async def export_cache_data(self, file_path: str) -> bool:
        """导出缓存数据

        Args:
            file_path: 导出文件路径

        Returns:
            bool: 是否成功
        """
        try:
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "cache_config": self.config,
                "statistics": {
                    "total_entries": len(self.cache_storage),
                    "hit_rate": self.stats.hit_rate,
                    "total_size_mb": self.stats.total_size_mb
                },
                "cache_entries": [
                    {
                        "cache_key": key,
                        "content_hash": entry.content_hash,
                        "content_type": entry.content_type.value,
                        "created_at": entry.created_at.isoformat(),
                        "last_accessed": entry.last_accessed.isoformat(),
                        "access_count": entry.access_count,
                        "size_bytes": entry.size_bytes,
                        "ttl_seconds": entry.ttl_seconds
                    }
                    for key, entry in self.cache_storage.items()
                ]
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            print(f"Failed to export cache data: {e}")
            return False