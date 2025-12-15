"""
MCP语义记忆服务客户端
Canvas Learning System - Story 8.8

提供语义记忆压缩、智能标签生成、关联发现和创意联想功能。
"""

import json
import uuid
import os
import time
import hashlib
from typing import Dict, List, Tuple, Optional, Union, Any
from datetime import datetime, timedelta
from pathlib import Path
import logging
import yaml
from dataclasses import dataclass, asdict

# 导入统一异常处理
from mcp_exceptions import (
    MCPException, MCPDependencyError, MCPConfigurationError,
    MCPModelLoadError, MCPDatabaseError, MCPMemoryError, MCPSearchError,
    MCPSemanticError, MCPCreativeError, MCPCanvasError, MCPHardwareError,
    handle_exception, create_dependency_error, create_config_error,
    create_model_error, create_database_error
)

# 第三方库导入
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logging.warning("ChromaDB not available. Install with: pip install chromadb")

try:
    import sentence_transformers
    import torch
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("Sentence Transformers not available. Install with: pip install sentence-transformers torch")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logging.warning("NumPy not available. Install with: pip install numpy")

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ConceptInfo:
    """概念信息数据类"""
    concept: str
    confidence: float
    category: str
    related_fields: List[str]


@dataclass
class SemanticRelationship:
    """语义关系数据类"""
    related_memory_id: str
    relationship_type: str
    similarity_score: float
    relationship_context: str


@dataclass
class CompressionMetadata:
    """压缩元数据数据类"""
    original_size_bytes: int
    compressed_size_bytes: int
    compression_ratio: float
    compression_method: str
    information_retention_score: float


@dataclass
class AccessMetadata:
    """访问元数据数据类"""
    created_at: str
    last_accessed: str
    access_count: int
    retrieval_context: List[str]


class HardwareDetector:
    """硬件检测器"""

    @staticmethod
    def detect_gpu() -> Dict[str, Any]:
        """检测GPU硬件"""
        gpu_info = {
            "has_gpu": False,
            "gpu_count": 0,
            "gpu_memory_mb": 0,
            "cuda_available": False,
            "recommended_device": "cpu"
        }

        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            return gpu_info

        try:
            import torch
            gpu_info["cuda_available"] = torch.cuda.is_available()

            if torch.cuda.is_available():
                gpu_info["has_gpu"] = True
                gpu_info["gpu_count"] = torch.cuda.device_count()

                # 获取GPU内存信息
                if gpu_info["gpu_count"] > 0:
                    gpu_info["gpu_memory_mb"] = torch.cuda.get_device_properties(0).total_memory // (1024*1024)
                    gpu_info["recommended_device"] = "cuda"

        except Exception as e:
            logger.warning(f"GPU检测失败: {e}")

        return gpu_info

    @staticmethod
    def get_system_memory() -> int:
        """获取系统内存（MB）"""
        try:
            import psutil
            return psutil.virtual_memory().total // (1024*1024)
        except ImportError:
            # 如果没有psutil，返回保守估计
            return 4096  # 4GB


class MCPSemanticMemory:
    """MCP语义记忆服务管理器"""

    def __init__(self, config_path: str = "config/mcp_config.yaml"):
        """初始化MCP记忆服务

        Args:
            config_path: MCP配置文件路径
        """
        self.config = self._load_config(config_path)
        self._validate_dependencies()

        # 硬件检测
        self.hardware_info = HardwareDetector.detect_gpu()
        self.device = self._determine_device()

        # 初始化组件
        self.embedding_model = None
        self.vector_db = None
        self._initialize_embedding_model()
        self._initialize_vector_database()

        logger.info(f"MCP语义记忆服务初始化完成，使用设备: {self.device}")

    @handle_exception
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except FileNotFoundError:
            logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
            return self._get_default_config()
        except yaml.YAMLError as e:
            logger.error(f"配置文件格式错误: {e}")
            raise create_config_error(config_path, "parse_error", f"YAML解析失败: {str(e)}")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            raise create_config_error(config_path, "unknown_error", f"未知错误: {str(e)}")

    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "mcp_service": {
                "vector_database": {
                    "type": "chromadb",
                    "persist_directory": "./data/memory_db",
                    "collection_name": "canvas_memories"
                },
                "embedding_model": {
                    "model_name": "sentence-transformers/all-MiniLM-L6-v2",
                    "device": "auto"
                },
                "hardware_detection": {
                    "auto_detect_gpu": True,
                    "fallback_to_cpu": True
                }
            }
        }

    @handle_exception
    def _validate_dependencies(self):
        """验证依赖库"""
        if not CHROMADB_AVAILABLE:
            logger.error("ChromaDB不可用，请运行: pip install chromadb")
            raise create_dependency_error("chromadb", "pip install chromadb")
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.error("Sentence Transformers不可用，请运行: pip install sentence-transformers torch")
            raise create_dependency_error("sentence-transformers", "pip install sentence-transformers torch")
        if not NUMPY_AVAILABLE:
            logger.error("NumPy不可用，请运行: pip install numpy")
            raise create_dependency_error("numpy", "pip install numpy")

    def _determine_device(self) -> str:
        """确定使用的设备"""
        device_config = self.config.get("mcp_service", {}).get("embedding_model", {}).get("device", "auto")

        if device_config == "auto":
            if self.hardware_info["has_gpu"] and self.hardware_info["gpu_memory_mb"] >= 4096:
                return "cuda"
            else:
                return "cpu"
        elif device_config == "cuda":
            if self.hardware_info["cuda_available"]:
                return "cuda"
            else:
                logger.warning("CUDA不可用，回退到CPU")
                return "cpu"

        return device_config

    def _initialize_embedding_model(self):
        """初始化嵌入模型"""
        try:
            model_name = self.config.get("mcp_service", {}).get("embedding_model", {}).get("model_name")

            logger.info(f"正在加载嵌入模型: {model_name}")
            self.embedding_model = sentence_transformers.SentenceTransformer(
                model_name,
                device=self.device
            )

            # 测试嵌入
            test_embedding = self.embedding_model.encode("测试文本")
            logger.info(f"嵌入模型加载成功，向量维度: {len(test_embedding)}")

        except Exception as e:
            logger.error(f"嵌入模型初始化失败: {e}")
            raise

    def _initialize_vector_database(self):
        """初始化向量数据库"""
        try:
            db_config = self.config.get("mcp_service", {}).get("vector_database", {})
            persist_directory = db_config.get("persist_directory", "./data/memory_db")
            collection_name = db_config.get("collection_name", "canvas_memories")

            # 确保数据目录存在
            os.makedirs(persist_directory, exist_ok=True)

            # 初始化ChromaDB
            self.vector_db = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False
                    # allow_rest参数在ChromaDB 1.2.1+中已移除
                )
            )

            # 获取或创建集合
            try:
                self.collection = self.vector_db.get_collection(name=collection_name)
                logger.info(f"使用现有集合: {collection_name}")
            except:
                self.collection = self.vector_db.create_collection(
                    name=collection_name,
                    metadata={"description": "Canvas语义记忆集合"}
                )
                logger.info(f"创建新集合: {collection_name}")

        except Exception as e:
            logger.error(f"向量数据库初始化失败: {e}")
            raise

    def store_semantic_memory(self, content: str, metadata: Dict) -> str:
        """存储语义记忆

        Args:
            content: 需要记忆的内容
            metadata: 内容元数据

        Returns:
            str: 记忆ID
        """
        try:
            # 生成记忆ID
            memory_id = f"memory-{uuid.uuid4().hex[:16]}"

            # 生成内容嵌入
            embedding = self.embedding_model.encode(content)
            # 转换为列表格式（兼容ChromaDB）
            if hasattr(embedding, 'tolist'):
                embedding = embedding.tolist()

            # 构建完整的元数据
            full_metadata = {
                "memory_id": memory_id,
                "content": content,
                "content_length": len(content),
                "model_name": self.embedding_model._modules['0'].auto_model.name_or_path,
                "embedding_timestamp": datetime.now().isoformat(),
                "device": self.device,
                **metadata
            }

            # 存储到向量数据库
            self.collection.add(
                ids=[memory_id],
                embeddings=[embedding],
                metadatas=[full_metadata],
                documents=[content]
            )

            logger.info(f"语义记忆存储成功: {memory_id}")
            return memory_id

        except Exception as e:
            logger.error(f"语义记忆存储失败: {e}")
            raise

    def search_semantic_memory(self, query: str, limit: int = 10) -> List[Dict]:
        """语义搜索记忆

        Args:
            query: 搜索查询
            limit: 返回结果数量限制

        Returns:
            List[Dict]: 相关记忆列表
        """
        try:
            # 生成查询嵌入
            query_embedding = self.embedding_model.encode(query)
            # 转换为列表格式（兼容ChromaDB）
            if hasattr(query_embedding, 'tolist'):
                query_embedding = query_embedding.tolist()

            # 执行搜索
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(limit, 100),  # ChromaDB限制
                include=["metadatas", "documents", "distances"]
            )

            # 格式化结果
            formatted_results = []
            if results["ids"] and results["ids"][0]:
                for i, memory_id in enumerate(results["ids"][0]):
                    formatted_results.append({
                        "memory_id": memory_id,
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "similarity_score": 1 - results["distances"][0][i],  # 转换为相似度
                        "distance": results["distances"][0][i]
                    })

            logger.info(f"语义搜索完成，返回 {len(formatted_results)} 个结果")
            return formatted_results

        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            return []

    def auto_generate_tags(self, content: str, max_tags: int = 10) -> List[str]:
        """自动生成内容标签

        Args:
            content: 内容文本
            max_tags: 最大标签数量

        Returns:
            List[str]: 生成的标签列表
        """
        # 简单的基于关键词的标签生成
        # 在实际应用中，这里可以使用更复杂的NLP技术

        # 中文常见停用词
        stop_words = {
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这", "那", "她", "他", "它", "这个", "那个", "什么", "怎么", "为什么", "因为", "所以", "但是", "然后", "还有", "可以", "应该", "需要", "想要", "正在", "已经", "还是", "或者", "而且", "比如", "例如"
        }

        # 简单分词（基于空格和标点）
        import re
        words = re.findall(r'[\w]+', content)

        # 过滤停用词和短词
        filtered_words = [word for word in words if len(word) > 1 and word not in stop_words]

        # 统计词频
        word_count = {}
        for word in filtered_words:
            word_count[word] = word_count.get(word, 0) + 1

        # 按频率排序
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)

        # 生成标签
        tags = [word for word, count in sorted_words[:max_tags]]

        logger.info(f"生成了 {len(tags)} 个标签")
        return tags

    def find_related_concepts(self, concept: str, similarity_threshold: float = 0.7) -> List[Dict]:
        """查找相关概念

        Args:
            concept: 查询概念
            similarity_threshold: 相似度阈值

        Returns:
            List[Dict]: 相关概念列表
        """
        try:
            # 使用语义搜索查找相关记忆
            search_results = self.search_semantic_memory(concept, limit=20)

            # 过滤相似度
            related_concepts = []
            for result in search_results:
                if result["similarity_score"] >= similarity_threshold:
                    related_concepts.append({
                        "concept": result["content"][:100],  # 取前100字符作为概念描述
                        "memory_id": result["memory_id"],
                        "similarity_score": result["similarity_score"],
                        "context": result["metadata"]
                    })

            logger.info(f"找到 {len(related_concepts)} 个相关概念")
            return related_concepts

        except Exception as e:
            logger.error(f"查找相关概念失败: {e}")
            return []

    def get_memory_stats(self) -> Dict:
        """获取记忆统计信息"""
        try:
            # 获取集合中的文档数量
            count_result = self.collection.count()

            return {
                "total_memories": count_result,
                "device": self.device,
                "model_name": self.embedding_model._modules['0'].auto_model.name_or_path if self.embedding_model else "unknown",
                "hardware_info": self.hardware_info,
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取记忆统计失败: {e}")
            return {}

    def delete_memory(self, memory_id: str) -> bool:
        """删除记忆

        Args:
            memory_id: 记忆ID

        Returns:
            bool: 删除是否成功
        """
        try:
            self.collection.delete(ids=[memory_id])
            logger.info(f"记忆删除成功: {memory_id}")
            return True
        except Exception as e:
            logger.error(f"记忆删除失败: {e}")
            return False

    def close(self):
        """关闭连接"""
        try:
            if self.vector_db:
                self.vector_db = None
            if self.embedding_model:
                del self.embedding_model
                self.embedding_model = None
            logger.info("MCP语义记忆服务已关闭")
        except Exception as e:
            logger.error(f"关闭服务时出错: {e}")


# 便捷函数
def create_memory_client(config_path: str = "config/mcp_config.yaml") -> MCPSemanticMemory:
    """创建记忆客户端的便捷函数

    Args:
        config_path: 配置文件路径

    Returns:
        MCPSemanticMemory: 记忆客户端实例
    """
    return MCPSemanticMemory(config_path)


if __name__ == "__main__":
    # 简单测试
    client = create_memory_client()

    # 测试存储
    test_content = "逆否命题是逻辑学中的重要概念，它与原命题具有相同的真假性。"
    metadata = {
        "source": "test",
        "category": "logic",
        "tags": ["逻辑", "命题", "数学"]
    }

    memory_id = client.store_semantic_memory(test_content, metadata)
    print(f"存储记忆ID: {memory_id}")

    # 测试搜索
    search_results = client.search_semantic_memory("逆否命题", limit=5)
    print(f"搜索结果数量: {len(search_results)}")

    # 显示统计
    stats = client.get_memory_stats()
    print(f"记忆统计: {stats}")

    client.close()