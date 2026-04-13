"""
统一结果数据模型

定义UnifiedResult作为所有融合算法的统一输出格式。

✅ Verified from docs/architecture/FUSION-ALGORITHM-DESIGN.md

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class SearchSource(Enum):
    """检索来源"""
    GRAPHITI = "graphiti"
    LANCEDB = "lancedb"
    MULTIMODAL = "multimodal"  # Story 6.8: 多模态检索来源
    FUSED = "fused"  # 融合后的结果


class ResultType(Enum):
    """结果类型"""
    NODE = "node"           # Graphiti节点
    EDGE = "edge"           # Graphiti边
    EPISODE = "episode"     # Graphiti情节
    DOCUMENT = "document"   # LanceDB文档
    CHUNK = "chunk"         # LanceDB文档块
    # Story 6.8: 多模态类型
    IMAGE = "image"         # 图片
    PDF = "pdf"             # PDF文档
    AUDIO = "audio"         # 音频
    VIDEO = "video"         # 视频


@dataclass
class UnifiedResult:
    """
    统一结果数据模型

    所有融合算法的输出都使用此格式，便于后续处理和评估。

    ✅ Verified from docs/architecture/FUSION-ALGORITHM-DESIGN.md Section 1.2

    Attributes:
        id: 唯一标识符
        content: 结果内容文本
        source: 检索来源 (graphiti/lancedb)
        result_type: 结果类型 (node/edge/episode/document)
        original_score: 原始检索分数
        fused_score: 融合后的分数
        rank: 融合后的排名
        metadata: 附加元数据

    Example:
        >>> result = UnifiedResult(
        ...     id="node_123",
        ...     content="逆否命题的定义...",
        ...     source=SearchSource.GRAPHITI,
        ...     result_type=ResultType.NODE,
        ...     original_score=0.85,
        ...     fused_score=0.0156
        ... )
    """
    id: str
    content: str
    source: SearchSource
    result_type: ResultType
    original_score: float
    fused_score: float = 0.0
    rank: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """验证字段"""
        if not self.id:
            raise ValueError("id cannot be empty")
        if self.original_score < 0:
            raise ValueError("original_score cannot be negative")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "source": self.source.value,
            "result_type": self.result_type.value,
            "original_score": self.original_score,
            "fused_score": self.fused_score,
            "rank": self.rank,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UnifiedResult":
        """从字典创建"""
        return cls(
            id=data["id"],
            content=data["content"],
            source=SearchSource(data["source"]),
            result_type=ResultType(data["result_type"]),
            original_score=data["original_score"],
            fused_score=data.get("fused_score", 0.0),
            rank=data.get("rank", 0),
            metadata=data.get("metadata", {})
        )

    @classmethod
    def from_graphiti_node(
        cls,
        node_id: str,
        content: str,
        score: float,
        metadata: Optional[Dict] = None
    ) -> "UnifiedResult":
        """从Graphiti节点创建"""
        return cls(
            id=f"graphiti_node_{node_id}",
            content=content,
            source=SearchSource.GRAPHITI,
            result_type=ResultType.NODE,
            original_score=score,
            metadata=metadata or {}
        )

    @classmethod
    def from_graphiti_edge(
        cls,
        edge_id: str,
        content: str,
        score: float,
        metadata: Optional[Dict] = None
    ) -> "UnifiedResult":
        """从Graphiti边创建"""
        return cls(
            id=f"graphiti_edge_{edge_id}",
            content=content,
            source=SearchSource.GRAPHITI,
            result_type=ResultType.EDGE,
            original_score=score,
            metadata=metadata or {}
        )

    @classmethod
    def from_graphiti_episode(
        cls,
        episode_id: str,
        content: str,
        score: float,
        metadata: Optional[Dict] = None
    ) -> "UnifiedResult":
        """从Graphiti情节创建"""
        return cls(
            id=f"graphiti_episode_{episode_id}",
            content=content,
            source=SearchSource.GRAPHITI,
            result_type=ResultType.EPISODE,
            original_score=score,
            metadata=metadata or {}
        )

    @classmethod
    def from_lancedb_result(
        cls,
        doc_id: str,
        content: str,
        distance: float,
        metadata: Optional[Dict] = None
    ) -> "UnifiedResult":
        """
        从LanceDB结果创建

        Note: LanceDB使用distance（越小越好），需要转换为score（越大越好）
        """
        # 将distance转换为score: score = 1 / (1 + distance)
        score = 1.0 / (1.0 + distance) if distance >= 0 else 0.0

        return cls(
            id=f"lancedb_{doc_id}",
            content=content,
            source=SearchSource.LANCEDB,
            result_type=ResultType.DOCUMENT,
            original_score=score,
            metadata=metadata or {"original_distance": distance}
        )
