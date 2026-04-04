"""
Agent Domain Gateway — AI 对话引擎统一入口

Strangler Fig Pattern: 所有外部调用（endpoint, dependencies.py）
应通过此 gateway 访问 agent 领域的功能，而非直接导入 services/ 下的文件。

包含: agent_service, react_agent, agent_routing_engine, agent_selector,
       tool_executor, tool_definitions, skill_registry, context_enrichment_service,
       conversation_archive, conversation_distiller, conversation_inheritance,
       archive_scheduler, extraction_validator, error_classifier
"""

from __future__ import annotations

from typing import TYPE_CHECKING

# ── 核心 Agent 服务 ──
from app.services.agent_service import AgentService, AgentType, AgentResult

# ── 上下文增强 ──
from app.services.context_enrichment_service import ContextEnrichmentService

# ── 技能注册 ──
from app.services.skill_registry import get_skill_registry

# ── 会话归档 ──
from app.services.conversation_archive import get_archive_manager
from app.services.archive_scheduler import get_archive_scheduler

# ── 会话提取与验证 ──
from app.services.conversation_distiller import ConversationDistiller
from app.services.extraction_validator import ExtractionValidator

# ── 学生错误分类（教学用，非系统错误） ──
from app.services.error_classifier import ErrorClassifier

# ── 会话继承 ──
from app.services.conversation_inheritance import get_inherited_context

# ── 图片提取（用于多模态 agent 输入） ──
from app.services.markdown_image_extractor import MarkdownImageExtractor

__all__ = [
    # 核心
    "AgentService",
    "AgentType",
    "AgentResult",
    # 上下文
    "ContextEnrichmentService",
    # 技能
    "get_skill_registry",
    # 归档
    "get_archive_manager",
    "get_archive_scheduler",
    # 提取
    "ConversationDistiller",
    "ExtractionValidator",
    "ErrorClassifier",
    # 继承
    "get_inherited_context",
    # 工具
    "MarkdownImageExtractor",
]
