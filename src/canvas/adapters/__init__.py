"""
Canvas Adapters - 集成层适配器

将外部系统（Agentic RAG, Graphiti等）适配为Canvas系统可用的接口。

Adapters:
- AgenticRAGAdapter: 封装Agentic RAG StateGraph为检验白板生成接口
- (Future) GraphitiAdapter: Graphiti知识图谱适配器

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
Story: 12.10 - Canvas检验白板生成集成
"""

from canvas.adapters.agentic_rag_adapter import AgenticRAGAdapter

__all__ = ["AgenticRAGAdapter"]
