"""
Verification Graph Module - Canvas Learning System

Epic 24: Verification Canvas Redesign (智能引导模式)
Story 24.1: Smart Guidance Architecture Design
Story 24.2: Socratic Q&A Flow

This module implements the LangGraph StateGraph for Socratic-style
verification canvas with intelligent guidance.

Components:
- state.py: VerificationState TypedDict
- graph.py: StateGraph with Socratic loop
- nodes.py: Node functions for Q&A flow

Author: Canvas Learning System Team
Version: 1.1.0
Created: 2025-12-13
Updated: 2025-12-13 (Story 24.2)
"""

from verification_graph.graph import (
    build_verification_graph,
    verification_graph,
)
from verification_graph.nodes import (
    HINT_TEMPLATES,
    QUESTION_TEMPLATES,
    advance_to_next_concept,
    complete_verification,
    evaluate_answer,
    finalize_concept,
    generate_question,
    provide_hint,
    wait_for_answer,
)
from verification_graph.state import (
    AttemptRecord,
    ConceptResult,
    VerificationState,
    create_initial_state,
)

__all__ = [
    # State
    "VerificationState",
    "AttemptRecord",
    "ConceptResult",
    "create_initial_state",
    # Graph
    "verification_graph",
    "build_verification_graph",
    # Nodes
    "generate_question",
    "wait_for_answer",
    "evaluate_answer",
    "provide_hint",
    "finalize_concept",
    "advance_to_next_concept",
    "complete_verification",
    # Templates
    "QUESTION_TEMPLATES",
    "HINT_TEMPLATES",
]
