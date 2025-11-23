"""
Canvas Learning System v2.0 - 记忆数据模型测试

测试统一记忆系统的数据模型和序列化功能。

Author: Canvas Learning System Team
Version: 2.0
Created: 2025-10-23
"""

import pytest
import json
from datetime import datetime, timedelta
from typing import Dict, Any
import sys

# 添加项目根目录到路径
sys.path.append('..')
sys.path.append('../memory_system')

from memory_system.memory_models import (
    UnifiedMemoryEntry,
    MemoryLink,
    TemporalMemoryData,
    SemanticMemoryData,
    LearningSession,
    MemoryConsistencyReport,
    MemoryType,
    LearningState,
    InteractionType,
    MemoryLinkType,
    create_temporal_memory,
    create_semantic_memory,
    create_memory_link
)


class TestUnifiedMemoryEntry:
    """统一记忆条目测试类"""

    def test_create_unified_memory_entry_default(self):
        """测试创建默认统一记忆条目"""
        entry = UnifiedMemoryEntry()

        assert entry.memory_id is not None
        assert entry.temporal_id is None
        assert entry.semantic_id is None
        assert entry.canvas_id == ""
        assert entry.node_id == ""
        assert entry.content == ""
        assert entry.memory_type == MemoryType.UNIFIED
        assert entry.metadata == {}
        assert entry.created_at is not None
        assert entry.updated_at is not None
        assert entry.cross_references == []

    def test_create_unified_memory_entry_with_params(self):
        """测试带参数创建统一记忆条目"""
        test_time = datetime.now()
        entry = UnifiedMemoryEntry(
            memory_id="test_memory_123",
            temporal_id="temporal_123",
            semantic_id="semantic_123",
            canvas_id="test_canvas",
            node_id="test_node",
            content="测试内容",
            memory_type=MemoryType.TEMPORAL,
            metadata={"key": "value"},
            created_at=test_time,
            updated_at=test_time,
            cross_references=["ref1", "ref2"]
        )

        assert entry.memory_id == "test_memory_123"
        assert entry.temporal_id == "temporal_123"
        assert entry.semantic_id == "semantic_123"
        assert entry.canvas_id == "test_canvas"
        assert entry.node_id == "test_node"
        assert entry.content == "测试内容"
        assert entry.memory_type == MemoryType.TEMPORAL
        assert entry.metadata == {"key": "value"}
        assert entry.created_at == test_time
        assert entry.updated_at == test_time
        assert entry.cross_references == ["ref1", "ref2"]

    def test_unified_memory_entry_to_dict(self):
        """测试统一记忆条目转换为字典"""
        test_time = datetime.now()
        entry = UnifiedMemoryEntry(
            memory_id="test_memory",
            canvas_id="test_canvas",
            content="测试内容",
            memory_type=MemoryType.SEMANTIC,
            created_at=test_time
        )

        result = entry.to_dict()

        assert isinstance(result, dict)
        assert result["memory_id"] == "test_memory"
        assert result["canvas_id"] == "test_canvas"
        assert result["content"] == "测试内容"
        assert result["memory_type"] == "semantic"
        assert result["created_at"] == test_time.isoformat()
        assert result["updated_at"] == test_time.isoformat()

    def test_unified_memory_entry_from_dict(self):
        """测试从字典创建统一记忆条目"""
        test_time = datetime.now()
        data = {
            "memory_id": "test_memory",
            "temporal_id": "temporal_123",
            "semantic_id": "semantic_123",
            "canvas_id": "test_canvas",
            "node_id": "test_node",
            "content": "测试内容",
            "memory_type": "unified",
            "metadata": {"test": True},
            "created_at": test_time.isoformat(),
            "updated_at": test_time.isoformat(),
            "cross_references": ["ref1"]
        }

        entry = UnifiedMemoryEntry.from_dict(data)

        assert entry.memory_id == "test_memory"
        assert entry.temporal_id == "temporal_123"
        assert entry.semantic_id == "semantic_123"
        assert entry.canvas_id == "test_canvas"
        assert entry.node_id == "test_node"
        assert entry.content == "测试内容"
        assert entry.memory_type == MemoryType.UNIFIED
        assert entry.metadata == {"test": True}
        assert entry.created_at == test_time
        assert entry.updated_at == test_time
        assert entry.cross_references == ["ref1"]

    def test_unified_memory_entry_serialization_roundtrip(self):
        """测试统一记忆条目序列化往返"""
        original_entry = UnifiedMemoryEntry(
            canvas_id="test_canvas",
            node_id="test_node",
            content="测试序列化内容",
            memory_type=MemoryType.UNIFIED,
            metadata={"serialization": "test"}
        )

        # 转换为字典
        dict_data = original_entry.to_dict()

        # 转换为JSON字符串
        json_str = json.dumps(dict_data)

        # 从JSON字符串解析
        parsed_dict = json.loads(json_str)

        # 从字典创建新对象
        restored_entry = UnifiedMemoryEntry.from_dict(parsed_dict)

        # 验证往返一致性
        assert restored_entry.memory_id == original_entry.memory_id
        assert restored_entry.canvas_id == original_entry.canvas_id
        assert restored_entry.node_id == original_entry.node_id
        assert restored_entry.content == original_entry.content
        assert restored_entry.memory_type == original_entry.memory_type
        assert restored_entry.metadata == original_entry.metadata


class TestMemoryLink:
    """记忆链接测试类"""

    def test_create_memory_link_default(self):
        """测试创建默认记忆链接"""
        link = MemoryLink()

        assert link.link_id is not None
        assert link.source_memory_id == ""
        assert link.target_memory_id == ""
        assert link.link_type == MemoryLinkType.CONCEPT_RELATION
        assert link.strength == 1.0
        assert link.created_at is not None
        assert link.metadata == {}

    def test_create_memory_link_with_params(self):
        """测试带参数创建记忆链接"""
        test_time = datetime.now()
        link = MemoryLink(
            link_id="test_link_123",
            source_memory_id="source_memory",
            target_memory_id="target_memory",
            link_type=MemoryLinkType.TEMPORAL_SEMANTIC,
            strength=0.8,
            created_at=test_time,
            metadata={"relation": "test"}
        )

        assert link.link_id == "test_link_123"
        assert link.source_memory_id == "source_memory"
        assert link.target_memory_id == "target_memory"
        assert link.link_type == MemoryLinkType.TEMPORAL_SEMANTIC
        assert link.strength == 0.8
        assert link.created_at == test_time
        assert link.metadata == {"relation": "test"}

    def test_memory_link_to_dict(self):
        """测试记忆链接转换为字典"""
        test_time = datetime.now()
        link = MemoryLink(
            source_memory_id="source",
            target_memory_id="target",
            link_type=MemoryLinkType.CROSS_DOMAIN,
            strength=0.7,
            created_at=test_time
        )

        result = link.to_dict()

        assert isinstance(result, dict)
        assert result["source_memory_id"] == "source"
        assert result["target_memory_id"] == "target"
        assert result["link_type"] == "cross_domain"
        assert result["strength"] == 0.7
        assert result["created_at"] == test_time.isoformat()

    def test_memory_link_from_dict(self):
        """测试从字典创建记忆链接"""
        test_time = datetime.now()
        data = {
            "link_id": "test_link",
            "source_memory_id": "source_memory",
            "target_memory_id": "target_memory",
            "link_type": "concept_relation",
            "strength": 0.9,
            "created_at": test_time.isoformat(),
            "metadata": {"test": True}
        }

        link = MemoryLink.from_dict(data)

        assert link.link_id == "test_link"
        assert link.source_memory_id == "source_memory"
        assert link.target_memory_id == "target_memory"
        assert link.link_type == MemoryLinkType.CONCEPT_RELATION
        assert link.strength == 0.9
        assert link.created_at == test_time
        assert link.metadata == {"test": True}


class TestTemporalMemoryData:
    """时序记忆数据测试类"""

    def test_create_temporal_memory_data_default(self):
        """测试创建默认时序记忆数据"""
        data = TemporalMemoryData()

        assert data.session_id == ""
        assert data.canvas_id == ""
        assert data.node_id == ""
        assert data.learning_state == LearningState.RED
        assert data.timestamp is not None
        assert data.duration_seconds == 0
        assert data.interaction_type == InteractionType.VIEW
        assert data.confidence_score == 0.0
        assert data.review_interval_days == 1
        assert data.next_review_date is not None
        assert data.metadata == {}

    def test_create_temporal_memory_data_with_params(self):
        """测试带参数创建时序记忆数据"""
        test_time = datetime.now()
        next_review = test_time + timedelta(days=7)
        data = TemporalMemoryData(
            session_id="session_123",
            canvas_id="test_canvas",
            node_id="test_node",
            learning_state=LearningState.GREEN,
            timestamp=test_time,
            duration_seconds=300,
            interaction_type=InteractionType.SCORE,
            confidence_score=0.9,
            review_interval_days=7,
            next_review_date=next_review,
            metadata={"test": True}
        )

        assert data.session_id == "session_123"
        assert data.canvas_id == "test_canvas"
        assert data.node_id == "test_node"
        assert data.learning_state == LearningState.GREEN
        assert data.timestamp == test_time
        assert data.duration_seconds == 300
        assert data.interaction_type == InteractionType.SCORE
        assert data.confidence_score == 0.9
        assert data.review_interval_days == 7
        assert data.next_review_date == next_review
        assert data.metadata == {"test": True}

    def test_temporal_memory_data_to_dict(self):
        """测试时序记忆数据转换为字典"""
        test_time = datetime.now()
        data = TemporalMemoryData(
            session_id="test_session",
            canvas_id="test_canvas",
            learning_state=LearningState.YELLOW,
            timestamp=test_time,
            confidence_score=0.6
        )

        result = data.to_dict()

        assert isinstance(result, dict)
        assert result["session_id"] == "test_session"
        assert result["canvas_id"] == "test_canvas"
        assert result["learning_state"] == "yellow"
        assert result["timestamp"] == test_time.isoformat()
        assert result["confidence_score"] == 0.6

    def test_temporal_memory_data_from_dict(self):
        """测试从字典创建时序记忆数据"""
        test_time = datetime.now()
        data = {
            "session_id": "test_session",
            "canvas_id": "test_canvas",
            "node_id": "test_node",
            "learning_state": "purple",
            "timestamp": test_time.isoformat(),
            "duration_seconds": 180,
            "interaction_type": "edit",
            "confidence_score": 0.7,
            "review_interval_days": 3,
            "next_review_date": test_time.isoformat(),
            "metadata": {"test": True}
        }

        temporal_data = TemporalMemoryData.from_dict(data)

        assert temporal_data.session_id == "test_session"
        assert temporal_data.canvas_id == "test_canvas"
        assert temporal_data.node_id == "test_node"
        assert temporal_data.learning_state == LearningState.PURPLE
        assert temporal_data.timestamp == test_time
        assert temporal_data.duration_seconds == 180
        assert temporal_data.interaction_type == InteractionType.EDIT
        assert temporal_data.confidence_score == 0.7


class TestSemanticMemoryData:
    """语义记忆数据测试类"""

    def test_create_semantic_memory_data_default(self):
        """测试创建默认语义记忆数据"""
        data = SemanticMemoryData()

        assert data.content_vector == []
        assert data.semantic_tags == []
        assert data.concept_entities == []
        assert data.domain_classification == ""
        assert data.related_concepts == []
        assert data.understanding_level == 0.0
        assert data.creativity_score == 0.0
        assert data.metadata == {}
        assert data.created_at is not None
        assert data.updated_at is not None

    def test_create_semantic_memory_data_with_params(self):
        """测试带参数创建语义记忆数据"""
        test_time = datetime.now()
        data = SemanticMemoryData(
            content_vector=[0.1, 0.2, 0.3],
            semantic_tags=["math", "function"],
            concept_entities=["函数", "映射"],
            domain_classification="mathematics",
            related_concepts=["导数", "积分"],
            understanding_level=0.8,
            creativity_score=0.7,
            metadata={"test": True},
            created_at=test_time,
            updated_at=test_time
        )

        assert data.content_vector == [0.1, 0.2, 0.3]
        assert data.semantic_tags == ["math", "function"]
        assert data.concept_entities == ["函数", "映射"]
        assert data.domain_classification == "mathematics"
        assert data.related_concepts == ["导数", "积分"]
        assert data.understanding_level == 0.8
        assert data.creativity_score == 0.7
        assert data.metadata == {"test": True}
        assert data.created_at == test_time
        assert data.updated_at == test_time

    def test_semantic_memory_data_to_dict(self):
        """测试语义记忆数据转换为字典"""
        test_time = datetime.now()
        data = SemanticMemoryData(
            content_vector=[0.1, 0.2, 0.3],
            semantic_tags=["test_tag"],
            domain_classification="test_domain",
            understanding_level=0.6,
            created_at=test_time
        )

        result = data.to_dict()

        assert isinstance(result, dict)
        assert result["content_vector"] == [0.1, 0.2, 0.3]
        assert result["semantic_tags"] == ["test_tag"]
        assert result["domain_classification"] == "test_domain"
        assert result["understanding_level"] == 0.6
        assert result["created_at"] == test_time.isoformat()

    def test_semantic_memory_data_from_dict(self):
        """测试从字典创建语义记忆数据"""
        test_time = datetime.now()
        data = {
            "content_vector": [0.4, 0.5, 0.6],
            "semantic_tags": ["physics", "motion"],
            "concept_entities": ["运动", "速度"],
            "domain_classification": "physics",
            "related_concepts": ["加速度", "力"],
            "understanding_level": 0.9,
            "creativity_score": 0.8,
            "metadata": {"test": True},
            "created_at": test_time.isoformat(),
            "updated_at": test_time.isoformat()
        }

        semantic_data = SemanticMemoryData.from_dict(data)

        assert semantic_data.content_vector == [0.4, 0.5, 0.6]
        assert semantic_data.semantic_tags == ["physics", "motion"]
        assert semantic_data.concept_entities == ["运动", "速度"]
        assert semantic_data.domain_classification == "physics"
        assert semantic_data.related_concepts == ["加速度", "力"]
        assert semantic_data.understanding_level == 0.9
        assert semantic_data.creativity_score == 0.8


class TestLearningSession:
    """学习会话测试类"""

    def test_create_learning_session_default(self):
        """测试创建默认学习会话"""
        session = LearningSession()

        assert session.session_id is not None
        assert session.canvas_id == ""
        assert session.user_id == ""
        assert session.start_time is not None
        assert session.end_time is None
        assert session.duration_seconds == 0
        assert session.nodes_interacted == []
        assert session.memories_created == []
        assert session.learning_progress == {}
        assert session.metadata == {}

    def test_create_learning_session_with_params(self):
        """测试带参数创建学习会话"""
        test_time = datetime.now()
        end_time = test_time + timedelta(minutes=30)
        session = LearningSession(
            session_id="session_123",
            canvas_id="test_canvas",
            user_id="test_user",
            start_time=test_time,
            end_time=end_time,
            duration_seconds=1800,
            nodes_interacted=["node1", "node2"],
            memories_created=["mem1", "mem2"],
            learning_progress={"node1": 0.8, "node2": 0.6},
            metadata={"test": True}
        )

        assert session.session_id == "session_123"
        assert session.canvas_id == "test_canvas"
        assert session.user_id == "test_user"
        assert session.start_time == test_time
        assert session.end_time == end_time
        assert session.duration_seconds == 1800
        assert session.nodes_interacted == ["node1", "node2"]
        assert session.memories_created == ["mem1", "mem2"]
        assert session.learning_progress == {"node1": 0.8, "node2": 0.6}
        assert session.metadata == {"test": True}

    def test_learning_session_to_dict(self):
        """测试学习会话转换为字典"""
        test_time = datetime.now()
        session = LearningSession(
            canvas_id="test_canvas",
            user_id="test_user",
            start_time=test_time,
            duration_seconds=600,
            nodes_interacted=["node1"]
        )

        result = session.to_dict()

        assert isinstance(result, dict)
        assert result["canvas_id"] == "test_canvas"
        assert result["user_id"] == "test_user"
        assert result["start_time"] == test_time.isoformat()
        assert result["duration_seconds"] == 600
        assert result["end_time"] is None
        assert result["nodes_interacted"] == ["node1"]

    def test_learning_session_from_dict(self):
        """测试从字典创建学习会话"""
        test_time = datetime.now()
        data = {
            "session_id": "test_session",
            "canvas_id": "test_canvas",
            "user_id": "test_user",
            "start_time": test_time.isoformat(),
            "end_time": None,
            "duration_seconds": 1200,
            "nodes_interacted": ["node1", "node2"],
            "memories_created": ["mem1"],
            "learning_progress": {"node1": 0.7},
            "metadata": {"test": True}
        }

        session = LearningSession.from_dict(data)

        assert session.session_id == "test_session"
        assert session.canvas_id == "test_canvas"
        assert session.user_id == "test_user"
        assert session.start_time == test_time
        assert session.end_time is None
        assert session.duration_seconds == 1200
        assert session.nodes_interacted == ["node1", "node2"]
        assert session.memories_created == ["mem1"]
        assert session.learning_progress == {"node1": 0.7}


class TestMemoryConsistencyReport:
    """记忆一致性报告测试类"""

    def test_create_memory_consistency_report_default(self):
        """测试创建默认记忆一致性报告"""
        report = MemoryConsistencyReport()

        assert report.report_id is not None
        assert report.timestamp is not None
        assert report.temporal_memories_count == 0
        assert report.semantic_memories_count == 0
        assert report.unified_memories_count == 0
        assert report.consistency_score == 0.0
        assert report.inconsistencies_found == []
        assert report.recommendations == []
        assert report.auto_fixed is False

    def test_create_memory_consistency_report_with_params(self):
        """测试带参数创建记忆一致性报告"""
        test_time = datetime.now()
        report = MemoryConsistencyReport(
            report_id="report_123",
            timestamp=test_time,
            temporal_memories_count=10,
            semantic_memories_count=15,
            unified_memories_count=20,
            consistency_score=0.95,
            inconsistencies_found=[{"type": "orphaned_link", "severity": "medium"}],
            recommendations=["修复孤立链接"],
            auto_fixed=True
        )

        assert report.report_id == "report_123"
        assert report.timestamp == test_time
        assert report.temporal_memories_count == 10
        assert report.semantic_memories_count == 15
        assert report.unified_memories_count == 20
        assert report.consistency_score == 0.95
        assert len(report.inconsistencies_found) == 1
        assert report.inconsistencies_found[0]["type"] == "orphaned_link"
        assert report.recommendations == ["修复孤立链接"]
        assert report.auto_fixed is True

    def test_memory_consistency_report_to_dict(self):
        """测试记忆一致性报告转换为字典"""
        test_time = datetime.now()
        report = MemoryConsistencyReport(
            temporal_memories_count=5,
            semantic_memories_count=8,
            consistency_score=0.88,
            inconsistencies_found=[{"type": "test_issue"}],
            recommendations=["测试建议"]
        )

        result = report.to_dict()

        assert isinstance(result, dict)
        assert result["temporal_memories_count"] == 5
        assert result["semantic_memories_count"] == 8
        assert result["consistency_score"] == 0.88
        assert len(result["inconsistencies_found"]) == 1
        assert result["inconsistencies_found"][0]["type"] == "test_issue"
        assert result["recommendations"] == ["测试建议"]
        assert result["timestamp"] == test_time.isoformat()

    def test_memory_consistency_report_from_dict(self):
        """测试从字典创建记忆一致性报告"""
        test_time = datetime.now()
        data = {
            "report_id": "test_report",
            "timestamp": test_time.isoformat(),
            "temporal_memories_count": 12,
            "semantic_memories_count": 18,
            "unified_memories_count": 25,
            "consistency_score": 0.92,
            "inconsistencies_found": [
                {"type": "issue1", "severity": "low"},
                {"type": "issue2", "severity": "high"}
            ],
            "recommendations": ["建议1", "建议2"],
            "auto_fixed": False
        }

        report = MemoryConsistencyReport.from_dict(data)

        assert report.report_id == "test_report"
        assert report.timestamp == test_time
        assert report.temporal_memories_count == 12
        assert report.semantic_memories_count == 18
        assert report.unified_memories_count == 25
        assert report.consistency_score == 0.92
        assert len(report.inconsistencies_found) == 2
        assert report.inconsistencies_found[0]["type"] == "issue1"
        assert report.inconsistencies_found[1]["type"] == "issue2"
        assert report.recommendations == ["建议1", "建议2"]
        assert report.auto_fixed is False


class TestEnums:
    """枚举类型测试类"""

    def test_memory_type_enum(self):
        """测试记忆类型枚举"""
        assert MemoryType.TEMPORAL.value == "temporal"
        assert MemoryType.SEMANTIC.value == "semantic"
        assert MemoryType.UNIFIED.value == "unified"

    def test_learning_state_enum(self):
        """测试学习状态枚举"""
        assert LearningState.RED.value == "red"
        assert LearningState.YELLOW.value == "yellow"
        assert LearningState.PURPLE.value == "purple"
        assert LearningState.GREEN.value == "green"

    def test_interaction_type_enum(self):
        """测试交互类型枚举"""
        assert InteractionType.VIEW.value == "view"
        assert InteractionType.EDIT.value == "edit"
        assert InteractionType.SCORE.value == "score"
        assert InteractionType.DECOMPOSE.value == "decompose"
        assert InteractionType.EXPLAIN.value == "explain"
        assert InteractionType.VERIFY.value == "verify"

    def test_memory_link_type_enum(self):
        """测试记忆链接类型枚举"""
        assert MemoryLinkType.TEMPORAL_SEMANTIC.value == "temporal_semantic"
        assert MemoryLinkType.SEMANTIC_TEMPORAL.value == "semantic_temporal"
        assert MemoryLinkType.CROSS_DOMAIN.value == "cross_domain"
        assert MemoryLinkType.LEARNING_PROGRESS.value == "learning_progress"
        assert MemoryLinkType.CONCEPT_RELATION.value == "concept_relation"


class TestConvenienceFunctions:
    """便捷函数测试类"""

    def test_create_temporal_memory(self):
        """测试创建时序记忆数据便捷函数"""
        test_time = datetime.now()
        memory = create_temporal_memory(
            session_id="test_session",
            canvas_id="test_canvas",
            node_id="test_node",
            learning_state=LearningState.YELLOW,
            interaction_type=InteractionType.EDIT,
            confidence_score=0.7,
            duration_seconds=300
        )

        assert memory.session_id == "test_session"
        assert memory.canvas_id == "test_canvas"
        assert memory.node_id == "test_node"
        assert memory.learning_state == LearningState.YELLOW
        assert memory.interaction_type == InteractionType.EDIT
        assert memory.confidence_score == 0.7
        assert memory.duration_seconds == 300
        assert memory.timestamp is not None
        assert memory.next_review_date is not None

    def test_create_semantic_memory(self):
        """测试创建语义记忆数据便捷函数"""
        memory = create_semantic_memory(
            content_vector=[0.1, 0.2, 0.3, 0.4, 0.5],
            semantic_tags=["math", "function"],
            concept_entities=["函数", "映射"],
            domain_classification="mathematics",
            understanding_level=0.8
        )

        assert memory.content_vector == [0.1, 0.2, 0.3, 0.4, 0.5]
        assert memory.semantic_tags == ["math", "function"]
        assert memory.concept_entities == ["函数", "映射"]
        assert memory.domain_classification == "mathematics"
        assert memory.understanding_level == 0.8
        assert memory.creativity_score == 0.0  # 默认值
        assert memory.created_at is not None
        assert memory.updated_at is not None

    def test_create_memory_link(self):
        """测试创建记忆链接便捷函数"""
        test_time = datetime.now()
        link = create_memory_link(
            source_id="source_memory",
            target_id="target_memory",
            link_type=MemoryLinkType.CONCEPT_RELATION,
            strength=0.85
        )

        assert link.source_memory_id == "source_memory"
        assert link.target_memory_id == "target_memory"
        assert link.link_type == MemoryLinkType.CONCEPT_RELATION
        assert link.strength == 0.85
        assert link.link_id is not None
        assert link.created_at is not None
        assert link.metadata == {}

    def test_create_memory_link_with_custom_strength(self):
        """测试创建带自定义强度的记忆链接"""
        link = create_memory_link(
            source_id="source",
            target_id="target",
            link_type=MemoryLinkType.CROSS_DOMAIN,
            strength=0.3
        )

        assert link.strength == 0.3
        assert link.link_type == MemoryLinkType.CROSS_DOMAIN


class TestDataModelValidation:
    """数据模型验证测试类"""

    def test_unified_memory_entry_validation(self):
        """测试统一记忆条目验证"""
        # 测试有效数据
        valid_entry = UnifiedMemoryEntry(
            canvas_id="test_canvas",
            node_id="test_node",
            content="测试内容"
        )
        assert valid_entry.memory_id is not None

        # 测试边界值
        long_content = "a" * 10000  # 测试长内容
        entry_long = UnifiedMemoryEntry(
            canvas_id="test",
            node_id="test",
            content=long_content
        )
        assert len(entry_long.content) == 10000

    def test_memory_link_validation(self):
        """测试记忆链接验证"""
        # 测试强度边界值
        link_min = create_memory_link("source", "target", MemoryLinkType.CONCEPT_RELATION, 0.0)
        assert link_min.strength == 0.0

        link_max = create_memory_link("source", "target", MemoryLinkType.CONCEPT_RELATION, 2.0)
        assert link_max.strength == 2.0

        # 测试负强度（应该允许）
        link_negative = create_memory_link("source", "target", MemoryLinkType.CONCEPT_RELATION, -0.5)
        assert link_negative.strength == -0.5

    def test_temporal_memory_data_validation(self):
        """测试时序记忆数据验证"""
        # 测试时间间隔边界值
        memory = create_temporal_memory(
            session_id="test",
            canvas_id="test",
            node_id="test",
            learning_state=LearningState.GREEN,
            duration_seconds=86400,  # 24小时
            interaction_type=InteractionType.VIEW
        )
        assert memory.duration_seconds == 86400

        # 测试置信度边界值
        memory.confidence_score = 1.0
        assert memory.confidence_score == 1.0

        memory.confidence_score = 0.0
        assert memory.confidence_score == 0.0

    def test_semantic_memory_data_validation(self):
        """测试语义记忆数据验证"""
        # 测试向量维度
        large_vector = list(range(1000))  # 1000维向量
        memory = create_semantic_memory(
            content_vector=large_vector,
            semantic_tags=["test"],
            concept_entities=["测试"],
            domain_classification="test"
        )
        assert len(memory.content_vector) == 1000

        # 测试理解程度边界值
        memory.understanding_level = 1.0
        assert memory.understanding_level == 1.0

        memory.understanding_level = 0.0
        assert memory.understanding_level == 0.0


class TestDataModelSerialization:
    """数据模型序列化测试类"""

    def test_complex_serialization_roundtrip(self):
        """测试复杂对象序列化往返"""
        # 创建复杂的统一记忆条目
        original_entry = UnifiedMemoryEntry(
            temporal_id="temporal_123",
            semantic_id="semantic_123",
            canvas_id="complex_canvas",
            node_id="complex_node",
            content="复杂的测试内容，包含中文和English混合",
            memory_type=MemoryType.UNIFIED,
            metadata={
                "complex_data": {
                    "nested": {
                        "value": 42,
                        "array": [1, 2, 3]
                    },
                    "unicode": "测试中文字符🎯"
                },
                "tags": ["test", "complex", "测试"]
            },
            cross_references=["ref1", "ref2", "ref3"]
        )

        # 序列化往返
        dict_data = original_entry.to_dict()
        json_str = json.dumps(dict_data, ensure_ascii=False)
        parsed_dict = json.loads(json_str)
        restored_entry = UnifiedMemoryEntry.from_dict(parsed_dict)

        # 验证复杂数据的完整性
        assert restored_entry.canvas_id == original_entry.canvas_id
        assert restored_entry.content == original_entry.content
        assert restored_entry.memory_type == original_entry.memory_type
        assert restored_entry.metadata["complex_data"]["nested"]["value"] == 42
        assert restored_entry.metadata["complex_data"]["nested"]["array"] == [1, 2, 3]
        assert restored_entry.metadata["complex_data"]["unicode"] == "测试中文字符🎯"
        assert restored_entry.cross_references == original_entry.cross_references

    def test_datetime_serialization_consistency(self):
        """测试日期时间序列化一致性"""
        test_time = datetime(2025, 1, 15, 14, 30, 45, 123456)

        # 创建包含精确时间的对象
        original_data = TemporalMemoryData(
            session_id="test_session",
            canvas_id="test_canvas",
            timestamp=test_time,
            next_review_date=test_time + timedelta(days=7)
        )

        # 序列化往返
        dict_data = original_data.to_dict()
        restored_data = TemporalMemoryData.from_dict(dict_data)

        # 验证时间一致性（可能存在微秒精度差异）
        assert restored_data.session_id == original_data.session_id
        assert restored_data.canvas_id == original_data.canvas_id
        # 允许1秒的误差
        time_diff = abs((restored_data.timestamp - original_data.timestamp).total_seconds())
        assert time_diff < 1.0

    def test_enum_serialization_stability(self):
        """测试枚举序列化稳定性"""
        # 测试所有枚举类型的序列化
        original_entry = UnifiedMemoryEntry(
            memory_type=MemoryType.TEMPORAL
        )

        original_link = MemoryLink(
            link_type=MemoryLinkType.SEMANTIC_TEMPORAL
        )

        original_temporal = create_temporal_memory(
            session_id="test",
            canvas_id="test",
            node_id="test",
            learning_state=LearningState.PURPLE,
            interaction_type=InteractionType.DECOMPOSE
        )

        # 序列化往返
        restored_entry = UnifiedMemoryEntry.from_dict(original_entry.to_dict())
        restored_link = MemoryLink.from_dict(original_link.to_dict())
        restored_temporal = TemporalMemoryData.from_dict(original_temporal.to_dict())

        # 验证枚举值
        assert restored_entry.memory_type == MemoryType.TEMPORAL
        assert restored_link.link_type == MemoryLinkType.SEMANTIC_TEMPORAL
        assert restored_temporal.learning_state == LearningState.PURPLE
        assert restored_temporal.interaction_type == InteractionType.DECOMPOSE


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])