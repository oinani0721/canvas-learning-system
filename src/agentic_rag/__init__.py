"""
Agentic RAG - Canvas Learning System智能检索增强生成系统

基于LangGraph构建的多层记忆检索与质量控制编排系统。

Architecture:
- Layer 1: Graphiti时序知识图谱 (概念关系 + 学习历史)
- Layer 2: LanceDB向量数据库 (语义检索)
- Layer 3: Temporal Memory (FSRS遗忘曲线 + 学习行为)

Core Features:
- 并行检索 (Send模式)
- 3种融合算法 (RRF, Weighted, Cascade)
- 混合Reranking (Local + Cohere)
- 质量控制循环 (Query重写)

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
Story: 12.5 - LangGraph StateGraph构建
"""

from agentic_rag.state import CanvasRAGState
from agentic_rag.config import CanvasRAGConfig
from agentic_rag.state_graph import canvas_agentic_rag

__version__ = "1.0.0"

__all__ = [
    "CanvasRAGState",
    "CanvasRAGConfig",
    "canvas_agentic_rag",
]
