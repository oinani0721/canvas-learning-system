# Canvas Learning System - Unified Graphiti Episode Schema (C-1 写入契约 owner)
#
# Story 5-ge-1: CanvasGraphEpisodeV1 统一事件 schema.
#
# 所有学习事件 (callout / wikilink / calibration / error) 都序列化成这一份
# CanvasGraphEpisodeV1 进 add_episode 写入口 (C-1: 唯一写入契约, 不造第二条 writer 主干)。
#
# ⚠️ 偏离 spec 5-ge-1 AC#3 (记入 Change Log D4):
#   spec 原文要求把 CANVAS_ENTITY_TYPES / CANVAS_EDGE_TYPES 放进 entity_types.py,
#   但该文件已有同名常量 (LearningConcept... / PrerequisiteRelation) 且被已活
#   memory_service 管道 import。覆盖会打断已活管道, 故本文件改用新名
#   CANVAS_GRAPH_ENTITY_TYPES / CANVAS_GRAPH_EDGE_TYPES / CANVAS_EDGE_TYPE_MAP。
#
# [Source: _bmad-output/implementation-artifacts/epic-5a-graphiti-runtime/5-ge-1-canvas-graph-episode-v1.md]

from __future__ import annotations

import hashlib
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

# ═══════════════════════════════════════════════════════════════════════════════
# Event Type Enum (AC#1 — 7 类事件)
# ═══════════════════════════════════════════════════════════════════════════════


class EventType(str, Enum):
    """7 类 Canvas 学习事件 (统一进 CanvasGraphEpisodeV1)。"""

    WIKILINK_ADDED = "wikilink_added"  # 新增双链关系
    WIKILINK_REMOVED = "wikilink_removed"  # 删除双链关系 (演化型)
    CALLOUT_ADDED = "callout_added"  # 新增批注
    CALLOUT_UPDATED = "callout_updated"  # 修改批注 (演化型 — belief 版本链)
    CALLOUT_REMOVED = "callout_removed"  # 删除批注 (演化型)
    CALIBRATION_VOTE = "calibration_vote"  # 校准投票 (演化型)
    ERROR_MARKED = "error_marked"  # 标记错误 (演化型)


# "演化型" 事件 = 同一 belief_key 会随时间改写, 需走 belief 版本链 (5-ge-2)。
EVOLUTION_EVENT_TYPES: frozenset[EventType] = frozenset(
    {
        EventType.WIKILINK_REMOVED,
        EventType.CALLOUT_UPDATED,
        EventType.CALLOUT_REMOVED,
        EventType.CALIBRATION_VOTE,
        EventType.ERROR_MARKED,
    }
)


# ═══════════════════════════════════════════════════════════════════════════════
# Payload 子结构
# ═══════════════════════════════════════════════════════════════════════════════


class CalloutPayload(BaseModel):
    """批注内容载荷 (callout 类事件)。anchor 由 node_path + offset 派生 (belief_key 用)。"""

    callout_type: str = Field(
        ..., description="批注类型: question/tip/error/hint/note/warning/info"
    )
    text: str = Field(..., description="批注正文 (用户写下的内容)")
    offset: int = Field(
        default=0,
        description="批注在节点 md 内的字符偏移 (anchor = sha256(node_path+offset))",
    )


class ContextPayload(BaseModel):
    """事件发生时的探索上下文 (喂 narrative + 未来 search_facts 命中)。"""

    source_board: str = Field(default="", description="事件发生所在的原白板 (MOC) 名称")
    path_trace: list[str] = Field(
        default_factory=list,
        description="用户到达该节点的探索路径, 如 ['概览','递归定义','base case']",
    )
    in_links: list[str] = Field(
        default_factory=list, description="反向引用该节点的其他节点 (wikilink in-links)"
    )
    out_links: list[str] = Field(
        default_factory=list, description="该节点出链到的其他节点 (wikilink out-links)"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Canvas Entity / Edge 本体类型 (AC#3 — 新名, 不碰 entity_types.py 同名常量)
# ═══════════════════════════════════════════════════════════════════════════════


class CanvasNode(BaseModel):
    """Canvas 概念节点实体 (扁平节点池中的一个 md)。"""

    node_id: str = Field(..., description="节点稳定 ID (相对 vault 的路径或 slug)")
    title: str = Field(default="", description="节点标题")
    subject_area: str = Field(default="", description="学科领域 (vault 级)")


class _RelationEdge(BaseModel):
    """关系型边的公共基: 一句自然语言陈述 (Graphiti fact)。"""

    statement: str = Field(default="", description="该关系的自然语言陈述")


class Prerequisite(_RelationEdge):
    """A 是 B 的前置 (学 B 前必须先掌握 A)。"""

    strength: str = Field(default="strong", description="strong | weak")


class Elaborates(_RelationEdge):
    """A 详述 / 精化 B (refines/extends)。"""


class Contrasts(_RelationEdge):
    """A 与 B 对比 / 相异 (contradicts/contrasts)。"""


class ExampleOf(_RelationEdge):
    """A 是 B 的具体例子 (example_of)。"""


class Causes(_RelationEdge):
    """A 导致 / 引发 B (causal)。"""


class PartOf(_RelationEdge):
    """A 是 B 的组成部分 (part_of)。"""


class RelatedTo(_RelationEdge):
    """A 与 B 泛相关 (兜底关系)。"""


class SelfAnnotation(_RelationEdge):
    """节点对自身的批注 (callout 自环边: src == tgt)。"""

    callout_type: str = Field(default="", description="批注类型")


class SelfMisconception(_RelationEdge):
    """节点自身的错误标记 (error 自环边: src == tgt)。"""

    error_type: str = Field(default="", description="错误类型")


class CalibrationVote(_RelationEdge):
    """节点自身的校准投票 (calibration 自环边: src == tgt)。"""

    vote: str = Field(default="", description="校准结果")


CANVAS_GRAPH_ENTITY_TYPES: dict[str, type[BaseModel]] = {
    "CanvasNode": CanvasNode,
}

CANVAS_GRAPH_EDGE_TYPES: dict[str, type[BaseModel]] = {
    # 7 关系型
    "Prerequisite": Prerequisite,
    "Elaborates": Elaborates,
    "Contrasts": Contrasts,
    "ExampleOf": ExampleOf,
    "Causes": Causes,
    "PartOf": PartOf,
    "RelatedTo": RelatedTo,
    # 3 自环型 (callout / error / calibration 建模为 node→自身 的边)
    "SelfAnnotation": SelfAnnotation,
    "SelfMisconception": SelfMisconception,
    "CalibrationVote": CalibrationVote,
}

# Graphiti custom ontology: CanvasNode↔CanvasNode 允许的边类型 (edge_type_map 透传留待后续)。
CANVAS_EDGE_TYPE_MAP: dict[tuple[str, str], list[str]] = {
    ("CanvasNode", "CanvasNode"): list(CANVAS_GRAPH_EDGE_TYPES.keys()),
}

# relation_type 字符串 (payload AC#2 词表) → 边类名 (CANVAS_GRAPH_EDGE_TYPES 的 key)。
# 供 belief 服务从 payload.relation_type 选 EntityEdge.name。
RELATION_TYPE_TO_EDGE_NAME: dict[str, str] = {
    "prerequisite": "Prerequisite",
    "depends_on": "Prerequisite",
    "refines": "Elaborates",
    "extends": "Elaborates",
    "elaborates": "Elaborates",
    "contradicts": "Contrasts",
    "contrasts": "Contrasts",
    "example_of": "ExampleOf",
    "causes": "Causes",
    "part_of": "PartOf",
    "related_to": "RelatedTo",
}


def edge_name_for_relation(relation_type: str | None) -> str:
    """把 payload.relation_type 字符串映射到 CANVAS_GRAPH_EDGE_TYPES 的边类名 (兜底 RelatedTo)。"""
    if not relation_type:
        return "RelatedTo"
    return RELATION_TYPE_TO_EDGE_NAME.get(relation_type.lower(), "RelatedTo")


# ═══════════════════════════════════════════════════════════════════════════════
# 统一事件 schema (AC#2)
# ═══════════════════════════════════════════════════════════════════════════════


class CanvasGraphEpisodeV1(BaseModel):
    """所有 Canvas 学习事件的统一 episode 载荷 (C-1 写入契约)。

    序列化后作为 add_episode 的 episode_body (结构化 JSON 载体)。
    """

    schema_version: Literal["CanvasGraphEpisodeV1"] = "CanvasGraphEpisodeV1"
    event_id: str = Field(
        default="",
        description="确定性事件 ID (空则由 (vault_id+canvas_path+anchor+occurred_at) 自动派生)",
    )
    event_type: EventType
    occurred_at: datetime
    vault_id: str
    group_id: str = Field(
        ..., description="vault:<vault_id>[:<subject>] (Canvas D16 格式)"
    )
    canvas_path: str
    node_id: str
    source_node_id: str | None = None
    target_node_id: str | None = None
    relation_type: str | None = Field(
        default=None,
        description="prerequisite/depends_on/refines/extends/example_of/contradicts/related_to",
    )
    belief_key: str = Field(
        ..., description="belief 版本链 key (见 5-ge-2 BeliefKeyResolver)"
    )
    callout: CalloutPayload | None = None
    context: ContextPayload
    narrative: str = Field(
        ..., description="⛔ 必填自然语言句子 (Graphiti search_facts 命中关键)"
    )

    @field_validator("narrative")
    @classmethod
    def _narrative_must_be_nonempty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("narrative 必填且不能为空字符串 (AC#6: Graphiti 命中关键)")
        return v

    @model_validator(mode="after")
    def _autofill_event_id(self) -> CanvasGraphEpisodeV1:
        if not self.event_id:
            anchor = self.belief_key or self.node_id
            self.event_id = self.compute_event_id(
                self.vault_id, self.canvas_path, anchor, self.occurred_at
            )
        return self

    @staticmethod
    def compute_event_id(
        vault_id: str, canvas_path: str, anchor: str, timestamp: datetime
    ) -> str:
        """确定性事件 ID = SHA-256(vault_id + canvas_path + anchor + ISO 时间戳)。"""
        raw = f"{vault_id}|{canvas_path}|{anchor}|{timestamp.isoformat()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
