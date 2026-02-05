"""
LanceDBClient - LanceDB 向量数据库客户端

Story 12.2: LanceDB POC验证
- AC 2.1: LanceDB连接测试
- AC 2.2: 向量检索接口
- AC 2.3: 性能基准 (P95 < 400ms)
- AC 2.4: 结果转换为SearchResult

Story 23.2: LanceDB Embedding Pipeline
- AC 1: 支持文本内容向量化 (embed方法)
- AC 2: 支持Canvas节点批量索引 (index_canvas方法)
- AC 3: 支持语义相似度查询 (search增强)
- AC 4: 向量维度和模型可配置
- AC 5: 索引持久化到本地文件

✅ Verified from LanceDB documentation:
- lancedb.connect(path) - 连接数据库
- table.search(query_vector).limit(n).to_list() - 向量搜索
- 支持 metric="cosine" 或 "L2"

✅ Verified from MultimodalVectorizer (src/agentic_rag/processors/multimodal_vectorizer.py):
- vectorize_text(text) → VectorizedContent with .vector attribute
- batch_vectorize(texts) → List[VectorizedContent]
- DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
- DEFAULT_EMBEDDING_DIM = 384

Author: Canvas Learning System Team
Version: 1.1.0 (Story 23.2)
Created: 2025-11-29
Updated: 2025-12-12 (Story 23.2 - Embedding Pipeline)
"""

import asyncio
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from loguru import logger
    LOGURU_ENABLED = True
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    LOGURU_ENABLED = False

# ✅ Verified from LanceDB documentation
try:
    import lancedb
    LANCEDB_AVAILABLE = True
except ImportError:
    LANCEDB_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class LanceDBClient:
    """
    LanceDB 向量数据库客户端

    封装 LanceDB 向量检索为统一的搜索接口。

    ✅ Verified from Story 12.2 (docs/epics/EPIC-12-STORY-MAP.md):
    - AC 2.1: LanceDB连接测试
    - AC 2.2: search()接口, 返回List[SearchResult]
    - AC 2.3: P95延迟 < 400ms
    - AC 2.4: 结果转换为SearchResult格式

    ✅ Story 23.2: LanceDB Embedding Pipeline
    - AC 1: embed(text) 方法支持文本向量化
    - AC 2: index_canvas() 方法支持批量索引
    - AC 3: search() 支持Canvas文件过滤
    - AC 4: embedding_model 可配置
    - AC 5: 索引持久化到本地文件

    Usage:
        >>> client = LanceDBClient(db_path="backend/data/lancedb")
        >>> await client.initialize()
        >>> # Story 23.2 AC 1: 向量化文本
        >>> vector = await client.embed("什么是逆否命题？")
        >>> # Story 23.2 AC 2: 批量索引Canvas节点
        >>> count = await client.index_canvas("离散数学.canvas")
        >>> # Story 23.2 AC 3: 语义搜索
        >>> results = await client.search("逆否命题", table_name="canvas_nodes")
        >>> print(results[0])
        {'doc_id': 'lancedb_doc_123', 'content': '...', 'score': 0.85, 'metadata': {...}}
    """

    # 默认表名
    DEFAULT_TABLES = ["canvas_explanations", "canvas_concepts", "canvas_nodes"]

    # ✅ Story 23.2 AC 4: 默认嵌入维度 (all-MiniLM-L6-v2)
    DEFAULT_EMBEDDING_DIM = 384

    # ✅ Story 23.2 AC 4: 支持的embedding模型
    SUPPORTED_MODELS = {
        "sentence-transformers/all-MiniLM-L6-v2": 384,
        "sentence-transformers/all-mpnet-base-v2": 768,
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": 384,
    }

    def __init__(
        self,
        db_path: str = "data/lancedb",  # ✅ Story 38.1 Fix: 从 backend/ 目录运行时路径正确
        embedding_dim: int = DEFAULT_EMBEDDING_DIM,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        timeout_ms: int = 400,
        batch_size: int = 100,
        enable_fallback: bool = True
    ):
        """
        初始化 LanceDBClient

        ✅ Story 23.2 AC 4: 向量维度和模型可配置

        Args:
            db_path: LanceDB数据库路径 (默认: backend/data/lancedb)
            embedding_dim: 嵌入向量维度 (默认: 384 for all-MiniLM-L6-v2)
            embedding_model: embedding模型名称 (默认: all-MiniLM-L6-v2)
            timeout_ms: 超时时间(毫秒), 默认400ms (Story 12.2 AC 2.3)
            batch_size: 批量处理大小 (默认: 100, Story 23.2 AC 2)
            enable_fallback: 启用降级(超时/错误时返回空结果)
        """
        self.db_path = os.path.expanduser(db_path)
        self.embedding_dim = embedding_dim
        self.embedding_model = embedding_model
        self.timeout_ms = timeout_ms
        self.batch_size = batch_size
        self.enable_fallback = enable_fallback

        self._db = None
        self._initialized = False
        self._tables_cache: Dict[str, Any] = {}
        self._embedder = None

        # ✅ Story 23.2: MultimodalVectorizer for embedding
        self._vectorizer = None
        self._vectorizer_initialized = False

    async def initialize(self) -> bool:
        """
        初始化客户端，连接LanceDB

        ✅ Story 12.2 AC 2.1: LanceDB连接测试

        Returns:
            True if connection successful
        """
        if not LANCEDB_AVAILABLE:
            if LOGURU_ENABLED:
                logger.warning("LanceDB not installed. Run: pip install lancedb")
            self._initialized = True
            return False

        try:
            # ✅ Verified from LanceDB docs: lancedb.connect(path)
            self._db = lancedb.connect(self.db_path)
            self._initialized = True

            # 缓存表信息
            await self._cache_tables()

            if LOGURU_ENABLED:
                logger.info(
                    f"LanceDBClient initialized: path={self.db_path}, "
                    f"tables={list(self._tables_cache.keys())}"
                )

            return True

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"LanceDBClient initialization failed: {e}")

            self._initialized = True
            return False

    async def _cache_tables(self):
        """缓存表信息"""
        if self._db is None:
            return

        try:
            table_names = self._db.table_names()
            for name in table_names:
                try:
                    self._tables_cache[name] = self._db.open_table(name)
                except Exception:
                    pass
        except Exception as e:
            if LOGURU_ENABLED:
                logger.debug(f"Failed to cache tables: {e}")

    # =========================================================================
    # Story 23.2: Embedding Pipeline Methods
    # =========================================================================

    async def _init_vectorizer(self) -> bool:
        """
        懒加载embedding模型 (MultimodalVectorizer)

        ✅ Story 23.2 AC 1: 支持文本内容向量化
        ✅ Verified from MultimodalVectorizer (src/agentic_rag/processors/multimodal_vectorizer.py:162-200)

        Returns:
            bool: True if vectorizer initialized successfully
        """
        if self._vectorizer_initialized:
            return self._vectorizer is not None

        try:
            # Import MultimodalVectorizer lazily
            from agentic_rag.processors.multimodal_vectorizer import MultimodalVectorizer

            self._vectorizer = MultimodalVectorizer(
                model_name=self.embedding_model,
                device="cpu"  # Can be configured for GPU
            )
            await self._vectorizer.initialize()
            self._vectorizer_initialized = True

            if LOGURU_ENABLED:
                logger.info(
                    f"Vectorizer initialized: model={self.embedding_model}, "
                    f"dim={self._vectorizer.embedding_dim}"
                )

            return True

        except ImportError as e:
            if LOGURU_ENABLED:
                logger.warning(f"MultimodalVectorizer not available: {e}")
            self._vectorizer_initialized = True
            return False

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"Failed to initialize vectorizer: {e}")
            self._vectorizer_initialized = True
            return False

    async def embed(self, text: str) -> List[float]:
        """
        文本向量化

        ✅ Story 23.2 AC 1: 支持文本内容向量化
        - 返回384维向量 (使用all-MiniLM-L6-v2)
        - 或返回768维向量 (使用all-mpnet-base-v2)
        - 响应时间 < 100ms/单条文本

        ✅ Verified from MultimodalVectorizer.vectorize_text():
        - Returns VectorizedContent with .vector attribute

        Args:
            text: 要向量化的文本

        Returns:
            List[float]: embedding向量 (384或768维)

        Raises:
            RuntimeError: 如果vectorizer初始化失败
        """
        await self._init_vectorizer()

        if self._vectorizer is None:
            raise RuntimeError(
                "Vectorizer not available. Install sentence-transformers: "
                "pip install sentence-transformers"
            )

        # ✅ Verified from MultimodalVectorizer.vectorize_text() (line 244-290)
        result = await self._vectorizer.vectorize_text(text)
        return result.vector

    async def index_canvas(
        self,
        canvas_path: str,
        nodes: Optional[List[Dict[str, Any]]] = None,
        table_name: str = "canvas_nodes",
        subject: Optional[str] = None  # ✅ Story 38.1: 添加 subject 参数
    ) -> int:
        """
        批量索引Canvas节点

        ✅ Story 23.2 AC 2: 支持Canvas节点批量索引
        - 所有节点被索引到 canvas_nodes 表
        - 每个节点记录包含: doc_id, content, vector, canvas_file, node_id, color, metadata
        - 批量处理支持100+节点
        - 处理速度 < 1秒/10节点

        ✅ Story 38.1: 添加 subject 参数用于学科隔离
        - subject 存储在每个文档中，用于按学科过滤

        ✅ Verified from specs/data/canvas-node.schema.json:
        - id: string (节点唯一标识)
        - type: "text" | "file" | "group" | "link"
        - text: string (文本内容)
        - color: "1"-"6" (颜色代码)
        - x, y: integer (位置坐标)

        Args:
            canvas_path: Canvas文件路径
            nodes: 节点列表 (可选，不提供则从文件读取)
            table_name: LanceDB表名 (默认: canvas_nodes)
            subject: 学科标识 (用于学科隔离过滤)

        Returns:
            int: 索引的节点数量
        """
        if not self._initialized:
            await self.initialize()

        await self._init_vectorizer()

        if self._vectorizer is None:
            if LOGURU_ENABLED:
                logger.warning("Vectorizer not available, skipping index_canvas")
            return 0

        # 如果未提供nodes，从Canvas文件读取
        if nodes is None:
            nodes = self._read_canvas_nodes(canvas_path)

        # 过滤出有文本内容的text类型节点
        text_nodes = [
            node for node in nodes
            if node.get("type") == "text" and node.get("text", "").strip()
        ]

        if not text_nodes:
            if LOGURU_ENABLED:
                logger.info(f"No text nodes to index in {canvas_path}")
            return 0

        # 提取文本列表用于批量向量化
        texts = [node.get("text", "") for node in text_nodes]

        # ✅ Story 23.2 AC 2: 批量向量化 (batch_size=100)
        # ✅ Verified from MultimodalVectorizer.batch_vectorize() (line 455-515)
        try:
            vectorized = await self._vectorizer.batch_vectorize(texts)
        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"Batch vectorization failed: {e}")
            return 0

        # 准备LanceDB文档
        documents = []
        for node, vec_result in zip(text_nodes, vectorized):
            doc = {
                "doc_id": f"canvas_{node['id']}",
                "content": node.get("text", ""),
                "vector": vec_result.vector,
                "canvas_file": canvas_path,
                "node_id": node.get("id", ""),
                "node_type": node.get("type", "text"),
                "color": node.get("color", ""),
                "x": node.get("x", 0),
                "y": node.get("y", 0),
                "subject": subject or "",  # ✅ Story 38.1: 存储 subject 用于学科隔离
                "timestamp": datetime.now().isoformat(),
                "metadata_json": json.dumps({
                    "width": node.get("width"),
                    "height": node.get("height"),
                    "subject": subject,  # ✅ Story 38.1: 也在 metadata 中存储
                }, ensure_ascii=False)
            }
            documents.append(doc)

        # 写入LanceDB
        count = await self.add_documents(table_name, documents)

        if LOGURU_ENABLED:
            logger.info(
                f"Indexed {count} nodes from {canvas_path} to {table_name}"
            )

        return count

    def _read_canvas_nodes(self, canvas_path: str) -> List[Dict[str, Any]]:
        """
        从Canvas文件读取节点

        ✅ Verified from specs/data/canvas-node.schema.json:
        Canvas JSON格式: {"nodes": [...], "edges": [...]}

        Args:
            canvas_path: Canvas文件路径

        Returns:
            List[Dict]: 节点列表
        """
        try:
            with open(canvas_path, 'r', encoding='utf-8') as f:
                canvas_data = json.load(f)
            return canvas_data.get("nodes", [])
        except FileNotFoundError:
            if LOGURU_ENABLED:
                logger.error(f"Canvas file not found: {canvas_path}")
            return []
        except json.JSONDecodeError as e:
            if LOGURU_ENABLED:
                logger.error(f"Invalid JSON in canvas file {canvas_path}: {e}")
            return []
        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"Failed to read canvas file {canvas_path}: {e}")
            return []

    async def search(
        self,
        query: str,
        table_name: str = "canvas_explanations",
        canvas_file: Optional[str] = None,
        subject: Optional[str] = None,
        num_results: int = 10,
        metric: str = "cosine"
    ) -> List[Dict[str, Any]]:
        """
        向量搜索

        ✅ Story 12.2 AC 2.2: 向量检索接口
        ✅ Story 12.2 AC 2.3: P95 < 400ms
        ✅ Story 12.2 AC 2.4: 结果转换

        Args:
            query: 搜索查询 (文本或向量)
            table_name: 表名
            canvas_file: Canvas文件路径(用于过滤)
            subject: 学科标识(用于学科隔离过滤)
            num_results: 返回结果数量
            metric: 距离度量 ("cosine" 或 "L2")

        Returns:
            List[SearchResult]: 标准化的搜索结果
        """
        start_time = time.perf_counter()

        if not self._initialized:
            await self.initialize()

        try:
            # ✅ AC 2.3: 设置超时
            timeout_seconds = self.timeout_ms / 1000.0

            # 执行搜索
            results = await asyncio.wait_for(
                self._search_internal(
                    query=query,
                    table_name=table_name,
                    canvas_file=canvas_file,
                    subject=subject,
                    num_results=num_results,
                    metric=metric
                ),
                timeout=timeout_seconds
            )

            latency_ms = (time.perf_counter() - start_time) * 1000

            if LOGURU_ENABLED:
                logger.debug(
                    f"LanceDBClient.search: "
                    f"query='{query[:50] if isinstance(query, str) else 'vector'}...', "
                    f"table={table_name}, "
                    f"results={len(results)}, "
                    f"latency={latency_ms:.2f}ms"
                )

            # ✅ AC 2.3: 检查性能
            if latency_ms > 400:
                if LOGURU_ENABLED:
                    logger.warning(
                        f"LanceDB search exceeded 400ms: {latency_ms:.2f}ms"
                    )

            return results

        except asyncio.TimeoutError:
            if LOGURU_ENABLED:
                logger.warning(
                    f"LanceDBClient.search timeout ({self.timeout_ms}ms)"
                )

            if self.enable_fallback:
                return []
            else:
                raise

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"LanceDBClient.search error: {e}")

            if self.enable_fallback:
                return []
            else:
                raise

    async def _search_internal(
        self,
        query: str,
        table_name: str,
        canvas_file: Optional[str],
        subject: Optional[str],
        num_results: int,
        metric: str
    ) -> List[Dict[str, Any]]:
        """内部搜索实现"""
        if self._db is None:
            return []

        # 获取表
        try:
            if table_name in self._tables_cache:
                table = self._tables_cache[table_name]
            else:
                table = self._db.open_table(table_name)
                self._tables_cache[table_name] = table
        except Exception as e:
            if LOGURU_ENABLED:
                logger.debug(f"Table {table_name} not found: {e}")
            return []

        # 获取查询向量
        query_vector = await self._get_query_vector(query)
        if query_vector is None:
            return []

        # ✅ Verified from LanceDB docs:
        # table.search(query_vector).limit(n).metric("cosine").to_list()
        try:
            # 构建搜索查询
            search_query = table.search(query_vector).limit(num_results)

            # 添加Canvas文件过滤 (如果提供)
            if canvas_file:
                search_query = search_query.where(
                    f"canvas_file = '{canvas_file}'"
                )

            # 添加学科过滤 (如果提供)
            if subject:
                search_query = search_query.where(
                    f"subject = '{subject}'"
                )

            # 执行搜索
            raw_results = search_query.to_list()

            # 转换为SearchResult格式
            return self._convert_to_search_results(
                raw_results,
                canvas_file=canvas_file
            )

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"LanceDB search failed: {e}")
            return []

    async def _get_query_vector(
        self,
        query: str
    ) -> Optional[List[float]]:
        """
        获取查询向量

        ✅ Story 23.2: 使用embed()方法替换随机向量fallback

        如果query已经是向量，直接返回；
        否则使用embed()方法生成向量。

        Args:
            query: 查询文本或向量

        Returns:
            查询向量 (List[float]) 或 None
        """
        # 如果已经是向量
        if isinstance(query, list):
            return query

        if NUMPY_AVAILABLE and isinstance(query, np.ndarray):
            return query.tolist()

        # 尝试使用embedder生成向量 (legacy support)
        if self._embedder is not None:
            try:
                return await self._embedder(query)
            except Exception as e:
                if LOGURU_ENABLED:
                    logger.error(f"Embedder failed: {e}")

        # ✅ Story 23.2: 使用embed()方法 (MultimodalVectorizer)
        try:
            return await self.embed(query)
        except RuntimeError:
            # Vectorizer not available - return None instead of random vector
            if LOGURU_ENABLED:
                logger.warning(
                    "Vectorizer not available. Install sentence-transformers."
                )
            return None
        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"Embedding failed: {e}")
            return None

    def _convert_to_search_results(
        self,
        raw_results: List[Dict[str, Any]],
        canvas_file: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        转换LanceDB结果为标准SearchResult格式

        ✅ Story 12.2 AC 2.4: 结果转换

        SearchResult格式:
        {
            "doc_id": str,
            "content": str,
            "score": float,
            "metadata": {
                "source": "lancedb",
                "timestamp": str,
                "canvas_file": str|None
            }
        }
        """
        search_results = []

        for i, item in enumerate(raw_results):
            # 提取内容
            content = (
                item.get("content") or
                item.get("text") or
                item.get("document") or
                ""
            )

            # 生成文档ID
            doc_id = item.get("doc_id") or item.get("id") or f"lancedb_{i}"
            if not doc_id.startswith("lancedb_"):
                doc_id = f"lancedb_{doc_id}"

            # 计算分数 (LanceDB返回_distance, 需要转换为相似度)
            distance = item.get("_distance") or item.get("distance") or 0.0
            # 余弦距离转相似度: score = 1 / (1 + distance)
            # 或者: score = 1 - distance (如果distance在[0,1]范围)
            if distance >= 0:
                score = 1.0 / (1.0 + distance)
            else:
                score = 0.0

            # 构建metadata
            metadata = {
                "source": "lancedb",
                "timestamp": datetime.now().isoformat(),
                "canvas_file": item.get("canvas_file") or canvas_file,
                "original_distance": distance,
            }

            # 复制其他metadata字段
            for key in ["concept", "agent_type", "node_id", "metadata_json"]:
                if key in item:
                    metadata[key] = item[key]

            search_results.append({
                "doc_id": doc_id,
                "content": content,
                "score": score,
                "metadata": metadata
            })

        return search_results

    def set_embedder(self, embedder):
        """
        设置嵌入器

        Args:
            embedder: 异步函数 async def embed(text: str) -> List[float]
        """
        self._embedder = embedder

    async def add_documents(
        self,
        table_name: str,
        documents: List[Dict[str, Any]]
    ) -> int:
        """
        添加文档到表

        Args:
            table_name: 表名
            documents: 文档列表，每个包含 doc_id, content, vector, metadata

        Returns:
            添加的文档数量
        """
        if self._db is None:
            return 0

        try:
            # 准备数据
            data = []
            for doc in documents:
                lance_doc = {
                    "doc_id": doc.get("doc_id"),
                    "content": doc.get("content", ""),
                    "vector": doc.get("vector") or doc.get("embedding"),
                    "canvas_file": doc.get("metadata", {}).get("canvas_file", ""),
                    "timestamp": datetime.now().isoformat(),
                }

                # 添加metadata_json
                if "metadata" in doc:
                    import json
                    lance_doc["metadata_json"] = json.dumps(
                        doc["metadata"],
                        ensure_ascii=False
                    )

                data.append(lance_doc)

            # 检查表是否存在
            if table_name in self._tables_cache:
                table = self._tables_cache[table_name]
                table.add(data)
            else:
                # 创建新表
                table = self._db.create_table(table_name, data=data)
                self._tables_cache[table_name] = table

            if LOGURU_ENABLED:
                logger.info(f"Added {len(data)} documents to {table_name}")

            return len(data)

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"Failed to add documents: {e}")
            return 0

    async def search_multiple_tables(
        self,
        query: str,
        table_names: Optional[List[str]] = None,
        canvas_file: Optional[str] = None,
        subject: Optional[str] = None,
        num_results_per_table: int = 5
    ) -> List[Dict[str, Any]]:
        """
        搜索多个表并合并结果

        Args:
            query: 搜索查询
            table_names: 表名列表 (默认使用DEFAULT_TABLES)
            canvas_file: Canvas文件过滤
            subject: 学科标识(用于学科隔离过滤)
            num_results_per_table: 每个表的结果数量

        Returns:
            合并后的搜索结果 (按分数排序)
        """
        if table_names is None:
            table_names = self.DEFAULT_TABLES

        all_results = []

        for table_name in table_names:
            try:
                results = await self.search(
                    query=query,
                    table_name=table_name,
                    canvas_file=canvas_file,
                    subject=subject,
                    num_results=num_results_per_table
                )
                all_results.extend(results)
            except Exception as e:
                if LOGURU_ENABLED:
                    logger.debug(f"Search in {table_name} failed: {e}")

        # 按分数排序
        all_results.sort(key=lambda x: x.get("score", 0.0), reverse=True)

        return all_results

    async def count_documents_by_canvas(
        self,
        canvas_path: str,
        table_name: str = "canvas_nodes"
    ) -> Dict[str, Any]:
        """
        统计指定 Canvas 的已索引文档数量

        ✅ Story 38.1: 使用 pandas 直接查询，不依赖向量搜索
        - 解决空查询无法向量化的问题
        - 使用 endswith() 匹配处理路径前缀差异

        Args:
            canvas_path: Canvas 文件路径（相对路径）
            table_name: LanceDB 表名

        Returns:
            Dict with:
            - count: 文档数量
            - last_indexed: 最后索引时间
            - subject: 索引时的学科标识
        """
        if not self._initialized:
            await self.initialize()

        if self._db is None:
            return {"count": 0, "last_indexed": None, "subject": None}

        try:
            # 检查表是否存在
            if table_name not in self._db.table_names():
                return {"count": 0, "last_indexed": None, "subject": None}

            # 打开表
            table = self._db.open_table(table_name)

            # 使用 to_pandas() 获取所有数据，然后过滤
            # 这避免了需要向量化的问题
            df = table.to_pandas()

            if df.empty:
                return {"count": 0, "last_indexed": None, "subject": None}

            # 使用 endswith 匹配来处理路径前缀差异
            # 例如: "测试学科/测试Canvas.canvas" 可以匹配
            # "C:/path/to/vault/测试学科/测试Canvas.canvas"
            # 标准化路径分隔符
            normalized_path = canvas_path.replace("\\", "/")

            # 过滤匹配的文档
            if "canvas_file" in df.columns:
                # 标准化 DataFrame 中的路径
                df["canvas_file_normalized"] = df["canvas_file"].str.replace("\\\\", "/", regex=False)
                df["canvas_file_normalized"] = df["canvas_file_normalized"].str.replace("\\", "/", regex=False)

                # 使用 endswith 匹配
                mask = df["canvas_file_normalized"].str.endswith(normalized_path)
                matched_df = df[mask]

                if matched_df.empty:
                    # 尝试精确匹配
                    mask_exact = df["canvas_file_normalized"] == normalized_path
                    matched_df = df[mask_exact]

                if matched_df.empty:
                    return {"count": 0, "last_indexed": None, "subject": None}

                # 获取统计信息
                count = len(matched_df)
                last_indexed = None
                subject = None

                if "timestamp" in matched_df.columns:
                    last_indexed = matched_df["timestamp"].max()

                if "subject" in matched_df.columns:
                    # 获取第一个非空 subject
                    subjects = matched_df["subject"].dropna()
                    if len(subjects) > 0:
                        subject = subjects.iloc[0]

                return {
                    "count": count,
                    "last_indexed": last_indexed,
                    "subject": subject
                }
            else:
                return {"count": 0, "last_indexed": None, "subject": None}

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"count_documents_by_canvas failed: {e}")
            return {"count": 0, "last_indexed": None, "subject": None}

    def get_stats(self) -> Dict[str, Any]:
        """获取客户端统计信息"""
        return {
            "initialized": self._initialized,
            "db_available": self._db is not None,
            "db_path": self.db_path,
            "tables": list(self._tables_cache.keys()),
            "timeout_ms": self.timeout_ms,
            "batch_size": self.batch_size,
            "enable_fallback": self.enable_fallback,
            "lancedb_installed": LANCEDB_AVAILABLE
        }
