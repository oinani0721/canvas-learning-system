"""
GraphitiClient - Graphiti知识图谱客户端封装 (graphiti_core SDK)

Story 12.1: Graphiti时序知识图谱集成
Story 2.2 Task 4: 替换MCP import为graphiti_core SDK直接调用

- AC 1.1: 初始化graphiti_core客户端 (方案C内嵌, Neo4j bolt://localhost:7689)
- AC 1.2: search_nodes接口封装
- AC 1.3: 错误处理和超时
- AC 1.4: 结果转换为SearchResult

Author: Canvas Learning System Team
Version: 2.0.0
Created: 2025-11-29
Updated: 2026-03-16 (Story 2.2 - 替换MCP为graphiti_core SDK)
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    from loguru import logger

    LOGURU_ENABLED = True
except ImportError:
    import logging

    logger = logging.getLogger(__name__)
    LOGURU_ENABLED = False


def _empty_result_list() -> List[Dict[str, Any]]:
    """Return a new empty list for fallback/degradation paths."""
    return list()


# ============================================================
# Story 12.1 AC 4: Canvas实体类型定义
# ✅ Verified from specs/data/graphiti-entity.schema.json
# ============================================================


class EntityType(str, Enum):
    """
    Canvas Learning System 实体类型枚举

    ✅ Story 12.1 AC 4: 实体类型定义
    """

    CANVAS = "canvas"  # Canvas白板实体
    CONCEPT = "concept"  # 概念实体
    NODE = "node"  # Canvas节点实体
    QUESTION = "question"  # 问题实体
    ANSWER = "answer"  # 答案实体
    REVIEW = "review"  # 复习记录实体
    LEARNING_SESSION = "learning_session"  # 学习会话实体


@dataclass
class CanvasEntity:
    """
    Canvas白板实体

    ✅ Story 12.1 AC 4: Canvas实体类型定义
    ✅ Verified from specs/data/graphiti-entity.schema.json

    Attributes:
        id: 实体唯一标识符
        name: Canvas文件名
        file_path: Canvas文件完整路径
        node_count: 节点数量
        created_at: 创建时间
        updated_at: 最后更新时间
        metadata: 额外元数据
    """

    id: str
    name: str
    file_path: str
    node_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "file_path": self.file_path,
            "node_count": self.node_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "entity_type": EntityType.CANVAS.value,
            "metadata": self.metadata,
        }


@dataclass
class ConceptEntity:
    """
    概念实体

    ✅ Story 12.1 AC 4: Concept实体类型定义
    ✅ Verified from specs/data/graphiti-entity.schema.json

    Attributes:
        id: 实体唯一标识符
        name: 概念名称
        description: 概念描述
        canvas_id: 关联的Canvas ID
        node_id: 关联的Canvas节点ID
        stability: FSRS稳定性分数 (0-1)
        difficulty: FSRS难度分数 (0-1)
        last_review: 最后复习时间
        next_review: 下次复习时间
        review_count: 复习次数
        metadata: 额外元数据
    """

    id: str
    name: str
    description: str = ""
    canvas_id: Optional[str] = None
    node_id: Optional[str] = None
    stability: float = 0.0
    difficulty: float = 0.5
    last_review: Optional[datetime] = None
    next_review: Optional[datetime] = None
    review_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "canvas_id": self.canvas_id,
            "node_id": self.node_id,
            "stability": self.stability,
            "difficulty": self.difficulty,
            "last_review": self.last_review.isoformat() if self.last_review else None,
            "next_review": self.next_review.isoformat() if self.next_review else None,
            "review_count": self.review_count,
            "entity_type": EntityType.CONCEPT.value,
            "metadata": self.metadata,
        }

    @property
    def is_weak(self) -> bool:
        """
        判断是否为薄弱概念

        ✅ Verified from Story 12.4: 弱点识别算法
        combined_score = 0.7 × (1 - stability) + 0.3 × error_rate
        """
        error_rate = self.metadata.get("error_rate", 0.0)
        combined_score = 0.7 * (1 - self.stability) + 0.3 * error_rate
        return combined_score > 0.5


@dataclass
class LearningSessionEntity:
    """
    学习会话实体

    ✅ Story 12.1 AC 4: 学习会话实体类型定义

    Attributes:
        id: 实体唯一标识符
        canvas_id: 关联的Canvas ID
        start_time: 会话开始时间
        end_time: 会话结束时间
        concepts_reviewed: 复习的概念ID列表
        score: 会话得分
        metadata: 额外元数据
    """

    id: str
    canvas_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    concepts_reviewed: List[str] = field(default_factory=list)
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "canvas_id": self.canvas_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "concepts_reviewed": self.concepts_reviewed,
            "score": self.score,
            "entity_type": EntityType.LEARNING_SESSION.value,
            "metadata": self.metadata,
        }


class GraphitiClient:
    """
    Graphiti 客户端封装 (graphiti_core SDK)

    Story 2.2 Task 4: 替换MCP import为graphiti_core SDK直接调用。
    使用方案C内嵌graphiti_core, Neo4j端点 bolt://localhost:7689。

    Usage:
        >>> client = GraphitiClient()
        >>> await client.initialize()
        >>> results = await client.search_nodes("逆否命题", canvas_file="离散数学.canvas")
        >>> print(results[0])
        {'doc_id': 'graphiti_node_123', 'content': '...', 'score': 0.85, 'metadata': {...}}
    """

    def __init__(
        self, timeout_ms: int = 200, batch_size: int = 10, enable_fallback: bool = True
    ):
        self.timeout_ms = timeout_ms
        self.batch_size = batch_size
        self.enable_fallback = enable_fallback
        self._initialized = False
        self._graphiti_available = False
        self._graphiti_instance = None

    async def initialize(self) -> bool:
        """
        初始化客户端，检测graphiti_core SDK可用性。

        Story 2.2 Task 4.7: 检测graphiti_core而非MCP模块。

        Returns:
            True if graphiti_core is available and Neo4j is reachable
        """
        import os

        try:
            from graphiti_core import Graphiti

            neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7691")
            neo4j_user = os.getenv("NEO4J_USER", "neo4j")
            neo4j_password = os.getenv("NEO4J_PASSWORD", "neo4j")

            self._graphiti_instance = Graphiti(
                neo4j_uri,
                neo4j_user,
                neo4j_password,
            )

            self._graphiti_available = True
            self._initialized = True

            if LOGURU_ENABLED:
                logger.info(
                    f"GraphitiClient initialized: graphiti_core SDK available, Neo4j={neo4j_uri}"
                )
            return True

        except ImportError as e:
            self._graphiti_available = False
            self._initialized = True

            if LOGURU_ENABLED:
                logger.warning(
                    f"GraphitiClient: graphiti_core not available ({e}), will use fallback mode (empty results)"
                )
            return False

        except Exception as e:
            self._graphiti_available = False
            self._initialized = True

            if LOGURU_ENABLED:
                logger.error(f"GraphitiClient initialization failed: {e}")
            return False

    async def search_nodes(
        self,
        query: str,
        canvas_file: Optional[str] = None,
        entity_types: Optional[List[str]] = None,
        num_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        搜索Graphiti知识图谱节点

        Story 2.2 Task 4: 使用graphiti_core SDK直接搜索。

        Args:
            query: 搜索查询
            canvas_file: Canvas文件路径(用于group_id过滤)
            entity_types: 实体类型过滤(可选)
            num_results: 返回结果数量

        Returns:
            List[SearchResult]: 标准化的搜索结果
        """
        start_time = time.perf_counter()

        if not self._initialized:
            await self.initialize()

        try:
            timeout_seconds = self.timeout_ms / 1000.0

            if self._graphiti_available and self._graphiti_instance is not None:
                results = await self._search_via_graphiti_core(
                    query=query,
                    canvas_file=canvas_file,
                    timeout=timeout_seconds,
                    num_results=num_results,
                )
            else:
                # graphiti_core not available: graceful degradation
                results = _empty_result_list()

            # 转换为SearchResult格式
            search_results = self._convert_to_search_results(
                results, canvas_file=canvas_file, num_results=num_results
            )

            latency_ms = (time.perf_counter() - start_time) * 1000

            if LOGURU_ENABLED:
                logger.debug(
                    f"GraphitiClient.search_nodes: "
                    f"query='{query[:50]}...', "
                    f"results={len(search_results)}, "
                    f"latency={latency_ms:.2f}ms"
                )

            return search_results

        except asyncio.TimeoutError:
            if LOGURU_ENABLED:
                logger.warning(
                    f"GraphitiClient.search_nodes timeout ({self.timeout_ms}ms): query='{query[:50]}...'"
                )
            if self.enable_fallback:
                return _empty_result_list()
            raise

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"GraphitiClient.search_nodes error: {e}")
            if self.enable_fallback:
                return _empty_result_list()
            raise

    async def _search_via_graphiti_core(
        self,
        query: str,
        canvas_file: Optional[str] = None,
        timeout: float = 0.2,
        num_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        通过graphiti_core SDK执行搜索

        Story 2.2 Task 4.1-4.3: 使用graphiti_core的search API。
        """
        all_results: List[Dict[str, Any]] = list()

        try:
            # Use group_ids based on canvas_file for scoped search
            group_ids = None
            if canvas_file:
                group_ids = [canvas_file]

            # Search via graphiti_core SDK with timeout
            search_coro = self._graphiti_instance.search(
                query=query,
                num_results=num_results,
                group_ids=group_ids,
            )
            raw_results = await asyncio.wait_for(search_coro, timeout=timeout)

            # Convert graphiti_core results to dicts
            if raw_results:
                for item in raw_results:
                    result_dict = {}
                    # graphiti_core returns objects with various attributes
                    if hasattr(item, "fact"):
                        result_dict["content"] = item.fact
                        result_dict["_graphiti_type"] = "fact"
                    elif hasattr(item, "name"):
                        result_dict["content"] = item.name
                        result_dict["_graphiti_type"] = "node"
                    elif hasattr(item, "content"):
                        result_dict["content"] = item.content
                        result_dict["_graphiti_type"] = "memory"
                    else:
                        result_dict["content"] = str(item)
                        result_dict["_graphiti_type"] = "unknown"

                    # Extract common fields
                    if hasattr(item, "uuid"):
                        result_dict["id"] = item.uuid
                    elif hasattr(item, "id"):
                        result_dict["id"] = item.id

                    if hasattr(item, "score"):
                        result_dict["score"] = item.score
                    if hasattr(item, "created_at"):
                        result_dict["created_at"] = str(item.created_at)

                    all_results.append(result_dict)

            if LOGURU_ENABLED:
                logger.debug(
                    f"graphiti_core search returned {len(all_results)} results for query='{query[:40]}...'"
                )

        except asyncio.TimeoutError:
            if LOGURU_ENABLED:
                logger.warning(f"graphiti_core search timed out ({timeout}s)")
            raise

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"graphiti_core search failed: {e}")

        return all_results

    def _tag_results(
        self, results: List[Dict[str, Any]], result_type: str
    ) -> List[Dict[str, Any]]:
        """为结果添加类型标签"""
        for r in results:
            r["_graphiti_type"] = result_type
        return results

    def _convert_to_search_results(
        self,
        raw_results: List[Dict[str, Any]],
        canvas_file: Optional[str] = None,
        num_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        转换Graphiti结果为标准SearchResult格式

        ✅ Story 12.1 AC 1.4: Graphiti Edge/Node → SearchResult

        SearchResult格式:
        {
            "doc_id": str,
            "content": str,
            "score": float,
            "metadata": {
                "source": "graphiti",
                "timestamp": str,
                "canvas_file": str|None,
                "graphiti_type": "node"|"memory"|"fact"
            }
        }
        """
        search_results = []

        for i, item in enumerate(raw_results[:num_results]):
            # 提取内容
            content = (
                item.get("content")
                or item.get("text")
                or item.get("name")
                or item.get("fact")
                or str(item)
            )

            # 生成文档ID
            doc_id = item.get("id") or item.get("uuid") or f"graphiti_{i}"
            if not doc_id.startswith("graphiti_"):
                doc_id = f"graphiti_{doc_id}"

            # 计算分数 (如果没有分数，使用排名倒推)
            score = item.get("score") or item.get("similarity") or (1.0 - i * 0.05)
            score = max(0.0, min(1.0, float(score)))  # 限制在[0,1]

            # 构建metadata
            graphiti_type = item.get("_graphiti_type", "unknown")
            metadata = {
                "source": "graphiti",
                "timestamp": datetime.now().isoformat(),
                "canvas_file": canvas_file,
                "graphiti_type": graphiti_type,
                "original_id": item.get("id") or item.get("uuid"),
            }

            # 添加额外的Graphiti元数据
            if "created_at" in item:
                metadata["created_at"] = item["created_at"]
            if "updated_at" in item:
                metadata["updated_at"] = item["updated_at"]
            if "entity_type" in item:
                metadata["entity_type"] = item["entity_type"]
            if "importance" in item:
                metadata["importance"] = item["importance"]

            search_results.append(
                {
                    "doc_id": doc_id,
                    "content": content,
                    "score": score,
                    "metadata": metadata,
                }
            )

        return search_results

    async def search_memories(
        self, query: str, num_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        搜索记忆 (便捷方法)

        Args:
            query: 搜索查询
            num_results: 返回结果数量

        Returns:
            List[SearchResult]
        """
        return await self.search_nodes(query=query, num_results=num_results)

    async def get_weak_concepts(
        self, canvas_file: str, threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        获取Canvas的薄弱概念 (用于检验白板生成)

        通过查询Graphiti中与Canvas关联的低稳定性概念

        Args:
            canvas_file: Canvas文件路径
            threshold: 薄弱概念阈值 (FSRS stability < threshold)

        Returns:
            List[Dict]: 薄弱概念列表
        """
        # 查询与Canvas关联的概念
        query = f"Canvas薄弱概念 {canvas_file}"
        results = await self.search_nodes(
            query=query, canvas_file=canvas_file, num_results=20
        )

        # 过滤低分概念
        weak_concepts = [r for r in results if r.get("score", 1.0) < threshold]

        return weak_concepts

    async def add_episode(
        self,
        content: str,
        canvas_file: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        添加学习历程到Graphiti知识图谱

        Story 2.2 Task 4: 使用graphiti_core SDK的add_episode接口。

        Args:
            content: 学习内容/对话内容
            canvas_file: 关联的Canvas文件路径
            metadata: 额外元数据 (importance, tags等)

        Returns:
            episode_id: 成功时返回episode ID, 失败返回None
        """
        if not self._initialized:
            await self.initialize()

        try:
            # ✅ AC 1.3: 设置超时
            timeout_seconds = self.timeout_ms / 1000.0

            if self._graphiti_available and self._graphiti_instance is not None:
                episode_id = await self._add_episode_via_graphiti_core(
                    content=content,
                    canvas_file=canvas_file,
                    metadata=metadata,
                    timeout=timeout_seconds,
                )
                return episode_id
            else:
                if LOGURU_ENABLED:
                    logger.warning(
                        "GraphitiClient.add_episode: graphiti_core not available"
                    )
                return None

        except asyncio.TimeoutError:
            if LOGURU_ENABLED:
                logger.warning(
                    f"GraphitiClient.add_episode timeout ({self.timeout_ms}ms)"
                )
            return None

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"GraphitiClient.add_episode error: {e}")
            return None

    async def _add_episode_via_graphiti_core(
        self,
        content: str,
        canvas_file: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timeout: float = 0.2,
    ) -> Optional[str]:
        """
        通过graphiti_core SDK添加episode

        Story 2.2 Task 4: 替换MCP为graphiti_core SDK调用。

        Args:
            content: 学习内容
            canvas_file: Canvas文件路径
            metadata: 额外元数据
            timeout: 超时时间(秒)

        Returns:
            episode_id or None
        """
        try:
            import uuid

            # Build group_id from canvas_file for scoped storage
            group_id = canvas_file if canvas_file else "default"

            # Build episode name from content prefix
            episode_name = content[:80] if content else "learning_episode"

            # Use graphiti_core add_episode API with timeout
            add_coro = self._graphiti_instance.add_episode(
                name=episode_name,
                episode_body=content,
                group_id=group_id,
                source_description=f"canvas_learning:{canvas_file or 'unknown'}",
            )
            result = await asyncio.wait_for(add_coro, timeout=timeout)

            # Extract episode_id from result
            if result and hasattr(result, "uuid"):
                episode_id = result.uuid
            else:
                episode_id = f"episode_{uuid.uuid4().hex[:12]}"

            if LOGURU_ENABLED:
                logger.info(
                    f"GraphitiClient.add_episode: content='{content[:50]}...', episode_id={episode_id}"
                )

            return episode_id

        except asyncio.TimeoutError:
            if LOGURU_ENABLED:
                logger.warning(f"graphiti_core add_episode timed out ({timeout}s)")
            raise

        except ImportError:
            if LOGURU_ENABLED:
                logger.warning("graphiti_core not available for add_episode")
            return None

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"graphiti_core add_episode failed: {e}")
            return None

    async def add_memory(
        self,
        key: str,
        content: str,
        importance: int = 5,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """
        添加记忆到Graphiti (通过 add_episode 实现)

        Story 2.2 Task 4: 使用graphiti_core SDK。
        graphiti_core没有独立的 add_memory API，
        通过 add_episode 将记忆作为 episode 存储。

        Args:
            key: 记忆的唯一标识符
            content: 记忆内容
            importance: 重要性等级(1-10)
            tags: 标签列表

        Returns:
            success: 是否成功
        """
        if not self._initialized:
            await self.initialize()

        try:
            if self._graphiti_available and self._graphiti_instance is not None:
                timeout_seconds = self.timeout_ms / 1000.0

                # Use add_episode as the underlying storage mechanism
                episode_body = f"[memory:{key}] {content}"
                add_coro = self._graphiti_instance.add_episode(
                    name=key,
                    episode_body=episode_body,
                    group_id="canvas-memories",
                    source_description=f"memory:importance={importance}",
                )
                await asyncio.wait_for(add_coro, timeout=timeout_seconds)

                if LOGURU_ENABLED:
                    logger.info(
                        f"GraphitiClient.add_memory: key={key}, importance={importance}"
                    )
                return True
            else:
                if LOGURU_ENABLED:
                    logger.warning("add_memory: graphiti_core not available")
                return False

        except asyncio.TimeoutError:
            if LOGURU_ENABLED:
                logger.warning(f"add_memory timed out ({self.timeout_ms}ms)")
            return False

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"add_memory failed: {e}")
            return False

    async def add_relationship(
        self, entity1: str, entity2: str, relationship_type: str
    ) -> bool:
        """
        添加实体关系到Graphiti (通过 add_episode 存储关系描述)

        Story 2.2 Task 4: 使用graphiti_core SDK。
        graphiti_core 自动从 episode 文本中提取实体和关系，
        因此通过 add_episode 存储关系描述来创建关系。

        Args:
            entity1: 第一个实体
            entity2: 第二个实体
            relationship_type: 关系类型

        Returns:
            success: 是否成功
        """
        if not self._initialized:
            await self.initialize()

        try:
            if self._graphiti_available and self._graphiti_instance is not None:
                timeout_seconds = self.timeout_ms / 1000.0

                # graphiti_core extracts entities and relationships from episode text
                relationship_text = f"{entity1} {relationship_type} {entity2}"
                add_coro = self._graphiti_instance.add_episode(
                    name=f"rel:{entity1}->{entity2}",
                    episode_body=relationship_text,
                    group_id="canvas-relationships",
                    source_description=f"relationship:{relationship_type}",
                )
                await asyncio.wait_for(add_coro, timeout=timeout_seconds)

                if LOGURU_ENABLED:
                    logger.info(
                        f"GraphitiClient.add_relationship: {entity1} --[{relationship_type}]--> {entity2}"
                    )
                return True
            else:
                if LOGURU_ENABLED:
                    logger.warning("add_relationship: graphiti_core not available")
                return False

        except asyncio.TimeoutError:
            if LOGURU_ENABLED:
                logger.warning(f"add_relationship timed out ({self.timeout_ms}ms)")
            return False

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"add_relationship failed: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════════════════════
    # P0 Task #5: Graphiti存储方法 - 检验白板历史关联
    # [Source: Plan - 问题8️⃣ 检验历史追踪缺失修复]
    # ═══════════════════════════════════════════════════════════════════════════════

    async def store_review_canvas_relationship(
        self,
        source_canvas_id: str,
        verification_canvas_id: str,
        review_date: str,
        node_count: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        存储检验白板与源Canvas的关联关系

        用于追踪检验白板历史，支持多次复习趋势分析。

        Args:
            source_canvas_id: 源Canvas文件路径/ID
            verification_canvas_id: 检验白板文件路径/ID
            review_date: 复习日期 (ISO格式: YYYY-MM-DD)
            node_count: 复习节点数量
            metadata: 可选的额外元数据 (scores, duration等)

        Returns:
            success: 是否成功存储

        Example:
            await client.store_review_canvas_relationship(
                source_canvas_id="离散数学.canvas",
                verification_canvas_id="离散数学-检验白板-20251207.canvas",
                review_date="2025-12-07",
                node_count=15,
                metadata={"average_score": 32.5, "green_ratio": 0.73}
            )
        """
        if not self._initialized:
            await self.initialize()

        try:
            if self._graphiti_available and self._graphiti_instance is not None:
                # 存储Canvas实体节点 (使用 add_memory 将信息作为 episode 存储)
                await self.add_memory(
                    key=f"canvas:{source_canvas_id}",
                    content=f"源Canvas: {source_canvas_id}",
                    importance=5,
                )

                extra_info = metadata or {}
                verification_content = (
                    f"检验白板: {verification_canvas_id}, 来源: {source_canvas_id}, "
                    f"日期: {review_date}, 节点数: {node_count}"
                )
                if extra_info:
                    verification_content += f", 额外信息: {extra_info}"

                await self.add_memory(
                    key=f"verification:{verification_canvas_id}",
                    content=verification_content,
                    importance=7,
                )

                # 存储关联关系
                await self.add_relationship(
                    entity1=source_canvas_id,
                    entity2=verification_canvas_id,
                    relationship_type="HAS_VERIFICATION",
                )

                if LOGURU_ENABLED:
                    logger.info(
                        f"store_review_canvas_relationship: "
                        f"{source_canvas_id} -> {verification_canvas_id} "
                        f"(date={review_date}, nodes={node_count})"
                    )
                return True
            else:
                if LOGURU_ENABLED:
                    logger.warning(
                        "store_review_canvas_relationship: graphiti_core not available"
                    )
                return False

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"store_review_canvas_relationship failed: {e}")
            return False

    async def query_review_history(
        self, canvas_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        查询Canvas的复习历史记录

        返回与指定Canvas关联的所有检验白板历史，按日期降序排列。

        Args:
            canvas_id: Canvas文件路径/ID
            limit: 返回结果数量限制 (默认10)

        Returns:
            review_history: 复习历史列表，每项包含:
                - verification_canvas_id: 检验白板ID
                - review_date: 复习日期
                - node_count: 节点数量
                - metadata: 额外元数据 (scores等)

        Example:
            history = await client.query_review_history("离散数学.canvas", limit=5)
            # Returns:
            # [
            #     {"verification_canvas_id": "...-20251207.canvas", "review_date": "2025-12-07", ...},
            #     {"verification_canvas_id": "...-20251201.canvas", "review_date": "2025-12-01", ...},
            # ]
        """
        if not self._initialized:
            await self.initialize()

        try:
            if self._graphiti_available:
                # 搜索与该Canvas关联的检验白板
                results = await self.search_memories(
                    query=f"检验白板 来源:{canvas_id}",
                )

                # 过滤并格式化结果
                history = []
                for result in results[:limit]:
                    if isinstance(result, dict):
                        metadata = result.get("metadata", {})
                        if metadata.get("type") == "verification_canvas":
                            history.append(
                                {
                                    "verification_canvas_id": metadata.get(
                                        "canvas_id", ""
                                    ),
                                    "review_date": metadata.get("review_date", ""),
                                    "node_count": metadata.get("node_count", 0),
                                    "source_canvas": metadata.get("source_canvas", ""),
                                    "metadata": {
                                        k: v
                                        for k, v in metadata.items()
                                        if k
                                        not in [
                                            "type",
                                            "canvas_id",
                                            "review_date",
                                            "node_count",
                                            "source_canvas",
                                        ]
                                    },
                                }
                            )

                # 按日期降序排序
                history.sort(key=lambda x: x.get("review_date", ""), reverse=True)

                if LOGURU_ENABLED:
                    logger.info(
                        f"query_review_history: canvas={canvas_id}, found={len(history)}"
                    )
                return history
            else:
                if LOGURU_ENABLED:
                    logger.warning("query_review_history: graphiti_core not available")
                return []

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"query_review_history failed: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """获取客户端统计信息"""
        return {
            "initialized": self._initialized,
            "graphiti_available": self._graphiti_available,
            "timeout_ms": self.timeout_ms,
            "batch_size": self.batch_size,
            "enable_fallback": self.enable_fallback,
        }


# =============================================================================
# Story 36.1 AC-36.1.5: Re-exports from unified backend location
#
# This module provides graphiti_core SDK-based GraphitiClient.
# For Neo4j-based operations, import from the unified backend location.
#
# Usage:
#   # graphiti_core SDK client (this file)
#   from src.agentic_rag.clients.graphiti_client import GraphitiClient
#
#   # Neo4j-based clients (unified backend)
#   from src.agentic_rag.clients.graphiti_client import (
#       GraphitiEdgeClient,
#       GraphitiClientBase,
#       EdgeRelationship,
#   )
# =============================================================================

try:
    # Re-export from unified backend location (Story 36.1)
    from backend.app.clients.graphiti_client import (
        GraphitiEdgeClient,
        GraphitiEdgeClientAdapter,
    )
    from backend.app.clients.graphiti_client_base import (
        EdgeRelationship,
        GraphitiClientBase,
    )

    # Flag for availability check
    UNIFIED_BACKEND_AVAILABLE = True

except ImportError:
    # Backend not available (e.g., running in isolated environment)
    UNIFIED_BACKEND_AVAILABLE = False
    GraphitiClientBase = None
    EdgeRelationship = None
    GraphitiEdgeClient = None
    GraphitiEdgeClientAdapter = None


# =============================================================================
# Exported symbols
# =============================================================================

__all__ = [
    # graphiti_core SDK client (this file)
    "GraphitiClient",
    # Entity types
    "EntityType",
    "CanvasEntity",
    "ConceptEntity",
    "LearningSessionEntity",
    # Re-exports from unified backend (Story 36.1)
    "GraphitiClientBase",
    "EdgeRelationship",
    "GraphitiEdgeClient",
    "GraphitiEdgeClientAdapter",
    # Availability flags
    "UNIFIED_BACKEND_AVAILABLE",
    "LOGURU_ENABLED",
]
