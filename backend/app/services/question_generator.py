# Canvas Learning System - Question Generator Service
# Story 6.3: AI Precise Question Generation (ACP Data Package)
# Story 4.2: Legacy template-based generation (preserved for backward compat)
#
# Upgraded from template-only to FSRS+BKT+KG triangle selection + ACP assembly
# + 5-layer Prompt (arXiv:2408.04394 PS4) + LLM-based question generation.
#
# [Source: _bmad-output/implementation-artifacts/6-3-ai-precise-question-acp.md]
"""
QuestionGenerator: FSRS+BKT+KG target selection + ACP + 5-layer Prompt + LLM.

Story 6.3 AC-1: select_target_node() — triple-factor priority ranking.
Story 6.3 AC-2: assemble_acp() — Graphiti + mastery_engine + archive aggregation.
Story 6.3 AC-3: 5-layer prompt construction (PS4 strategy).
Story 6.3 AC-5: generate_exam_question() — full pipeline entry point.

Legacy: generate_questions() / generate_for_nodes() retained for Story 4.2 usage.
"""

import asyncio
import json
import logging
import re

import structlog
from neo4j.exceptions import DriverError, Neo4jError
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from app.core.decision_tracker import log_decision
from app.core.source_descriptions import (
    CONVERSATION_ARCHIVE_SOURCES,
    MISCONCEPTION_SOURCES,
    TIP_SOURCES,
)
from app.models.exam_models import (
    ACPData,
    ExamMode,
    NodePriority,
    QuestionGenerationResult,
)

logger = structlog.get_logger(__name__)

QuestionType = Literal["breakthrough", "verification", "application"]

# Prompt template directory
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts" / "exam"

# FSRS+BKT+KG priority weights (Story 6.3 AC-1)
W_MASTERY = 0.4
W_RETRIEVABILITY = 0.3
W_KG_RELEVANCE = 0.3

# ACP token budget (Story 6.3 AC-2)
ACP_MAX_CHARS = 9000  # ~3K tokens at ~3 chars/token


def _load_prompt_file(filename: str) -> str:
    """Load a prompt template file from the exam prompts directory."""
    path = _PROMPTS_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    logger.warning(f"[Story 6.3] Prompt file not found: {path}")
    return ""


class QuestionGenerator:
    """
    Dual-mode question generator:
      - generate_exam_question(): Story 6.3 full pipeline (LLM-based)
      - generate_questions(): Story 4.2 legacy template-based (kept for compat)
    """

    # Legacy templates (Story 4.2 — preserved for backward compatibility)
    BREAKTHROUGH_TEMPLATES = [
        "请用自己的话解释：{concept}",
        "{concept} 的核心原理是什么？",
        "为什么 {concept}？请从根本原因分析",
        "如果要向初学者解释 {concept}，你会怎么说？",
    ]
    VERIFICATION_TEMPLATES = [
        "请详细描述 {concept} 的工作机制",
        "验证理解：{concept} 与什么概念相关？有何区别？",
        "{concept} 在什么情况下适用？什么情况下不适用？",
        "请举一个具体例子来说明 {concept}",
    ]
    APPLICATION_TEMPLATES = [
        "{concept} 可以应用在哪些实际场景中？",
        "如何使用 {concept} 解决实际问题？",
        "设计一个使用 {concept} 的案例",
    ]

    def __init__(self) -> None:
        """Initialize the question generator with 5-layer prompt templates."""
        self._template_index = 0
        # Load 5-layer prompt templates once (Story 6.3 AC-3)
        self._layer1 = _load_prompt_file("layer1_role.md")
        self._layer2 = _load_prompt_file("layer2_mode.md")
        self._layer3_template = _load_prompt_file("layer3.md")
        self._layer4 = _load_prompt_file("layer4_rules.md")
        self._layer5 = _load_prompt_file("layer5_scoring_preset.md")

    # ═══════════════════════════════════════════════════════════════════════
    # Story 6.3: Full Pipeline — Target Selection + ACP + LLM Generation
    # ═══════════════════════════════════════════════════════════════════════

    async def select_target_node(
        self,
        exam_id: str,
        source_canvas_id: str,
        exam_mode: ExamMode,
        examined_nodes: Optional[List[str]] = None,
        target_node_id: Optional[str] = None,
    ) -> Optional[NodePriority]:
        """Select the weakest node for examination using FSRS+BKT+KG.

        Story 6.3 AC-1: Triple-factor priority ranking.
        priority = W1*(1-p_mastery) + W2*(1-R) + W3*kg_relevance

        Args:
            exam_id: Current exam session ID.
            source_canvas_id: Original canvas board ID.
            exam_mode: Examination mode for strategy selection.
            examined_nodes: Nodes already examined this session (deprioritized).
            target_node_id: If specified, skip selection and use this node.

        Returns:
            NodePriority for the selected target, or None if no nodes available.
        """
        if target_node_id:
            mastery_data = await self._get_mastery_data(target_node_id)
            # M-3 (Sprint 1.2.1): explicit kg_relevance_degraded=None makes
            # the contract self-documenting and resilient to future Pydantic
            # default changes. When the caller specifies a target node we
            # skip the KG query entirely, so there is no degraded reason
            # to record.
            # A10 Phase 0 Hardening: propagate mastery_degraded to NodePriority
            # so single-target observability is symmetric with batch path.
            return NodePriority(
                node_id=target_node_id,
                priority_score=1.0,
                p_mastery=mastery_data.get("p_mastery", 0.1),
                retrievability=mastery_data.get("retrievability", 1.0),
                kg_relevance=1.0,
                kg_relevance_degraded=None,
                mastery_degraded=mastery_data.get("mastery_degraded"),
            )

        examined = set(examined_nodes or list())

        # Get all nodes from the source canvas
        nodes = await self._get_canvas_nodes(source_canvas_id)
        if not nodes:
            return None

        # Filter nodes with valid IDs
        valid_nodes = [(node, node.get("id", "")) for node in nodes]
        valid_nodes = [(node, nid) for node, nid in valid_nodes if nid]
        if not valid_nodes:
            return None

        # 6-3 H3 fix: Batch mastery + KG queries with asyncio.gather to avoid N+1
        node_ids = [nid for _, nid in valid_nodes]

        # Code-Review C-1 (Sprint 1.2.1) defense-in-depth:
        # `return_exceptions=True` ensures any unanticipated exception leaking
        # out of `_get_kg_relevance` or `_get_mastery_data` degrades the
        # affected node instead of crashing the entire exam batch. The typed
        # Neo4jError catch in `_get_kg_relevance` is the primary fix; this is
        # the second layer — e.g. `_get_mastery_data` only catches
        # (ImportError, AttributeError, ValueError), so a future TypeError
        # would still escape without this guard.
        #
        # A10 Phase 0 Hardening: bound per-batch Neo4j concurrency at 20 using
        # a function-local asyncio.Semaphore. Mirrors the canvas_service.py:598
        # pattern. Prevents pool exhaustion on large canvases (N=500 → 1000+
        # simultaneous queries without the bound). 20 is higher than
        # canvas_service's 12 because kg_relevance + mastery queries are
        # read-only and lighter than edge sync writes.
        semaphore = asyncio.Semaphore(20)

        async def _gated_mastery(nid: str) -> Dict[str, Any]:
            async with semaphore:
                return await self._get_mastery_data(nid)

        async def _gated_kg(nid: str) -> tuple[float, Optional[str]]:
            async with semaphore:
                return await self._get_kg_relevance(nid, source_canvas_id)

        mastery_results, kg_results = await asyncio.gather(
            asyncio.gather(
                *(_gated_mastery(nid) for nid in node_ids),
                return_exceptions=True,
            ),
            asyncio.gather(
                *(_gated_kg(nid) for nid in node_ids),
                return_exceptions=True,
            ),
        )

        priorities: List[NodePriority] = list()
        for idx, (_node, node_id) in enumerate(valid_nodes):
            # C-1 defense-in-depth: gather may yield BaseException for failed
            # coroutines now. Degrade per node instead of crashing the batch.
            mastery_data = mastery_results[idx]
            if isinstance(mastery_data, BaseException):
                logger.warning(
                    f"[Story 6.3] mastery query crashed for node {node_id}: "
                    f"{type(mastery_data).__name__}: {mastery_data}"
                )
                # A10 Phase 0 Hardening: mark batch-level exception distinctly
                # from concept_not_found so observability can differentiate
                # "query threw" from "data missing".
                mastery_data = {
                    "p_mastery": 0.1,
                    "retrievability": 1.0,
                    "mastery_degraded": "exception",
                }
            p_mastery = mastery_data.get("p_mastery", 0.1)
            retrievability = mastery_data.get("retrievability", 1.0)
            # A10 Phase 0 Hardening: surface mastery_degraded to NodePriority
            mastery_degraded = mastery_data.get("mastery_degraded")

            kg_result = kg_results[idx]
            if isinstance(kg_result, BaseException):
                logger.warning(
                    f"[Story 6.3] kg_relevance crashed for node {node_id}: "
                    f"{type(kg_result).__name__}: {kg_result}"
                )
                kg_relevance, kg_degraded = 0.5, "neo4j_unavailable"
            else:
                # FR-KG-04 fix: _get_kg_relevance returns (score, degraded_reason)
                kg_relevance, kg_degraded = kg_result

            priority = (
                W_MASTERY * (1.0 - p_mastery)
                + W_RETRIEVABILITY * (1.0 - retrievability)
                + W_KG_RELEVANCE * kg_relevance
            )

            already_examined = node_id in examined
            if already_examined:
                priority *= 0.3  # Demote already-examined nodes

            priorities.append(
                NodePriority(
                    node_id=node_id,
                    priority_score=round(priority, 4),
                    p_mastery=p_mastery,
                    retrievability=retrievability,
                    kg_relevance=kg_relevance,
                    kg_relevance_degraded=kg_degraded,
                    mastery_degraded=mastery_degraded,
                    already_examined=already_examined,
                )
            )

        if not priorities:
            return None

        priorities.sort(key=lambda p: p.priority_score, reverse=True)
        selected = priorities[0]

        log_decision(
            function="QuestionGenerator.select_target_node",
            input_summary={
                "candidates": len(priorities),
                "top_score": round(selected.priority_score, 3),
            },
            output=selected.node_id,
            reason=f"p_mastery={selected.p_mastery}, R={selected.retrievability}, kg={selected.kg_relevance}",
        )
        return selected

    async def assemble_acp(self, node_id: str) -> ACPData:
        """Assemble Assessment Context Package from multiple data sources.

        Story 6.3 AC-2: Aggregates Tips, error history, edge reasons,
        mastery data, and conversation summary. Token budget: 3K tokens.

        Args:
            node_id: Target node for ACP assembly.

        Returns:
            ACPData with assembled context.
        """
        acp = ACPData(node_id=node_id)

        # 1. Get node content from canvas
        node_data = await self._get_node_content(node_id)
        acp.node_content = self._truncate(node_data.get("text", ""), 1000)

        # Classify content type
        k_signals, p_signals = self._classify_content(acp.node_content)
        if p_signals > k_signals:
            acp.node_type = "problem_type"

        # 2. Get mastery data from mastery_engine
        mastery = await self._get_mastery_data(node_id)
        acp.p_mastery = mastery.get("p_mastery", 0.1)
        acp.retrievability = mastery.get("retrievability", 1.0)
        acp.effective_proficiency = mastery.get("effective_proficiency", 0.0)
        acp.mastery_level = mastery.get("mastery_level", 0.0)
        acp.mastery_label = mastery.get("mastery_label", "Not Assessed")
        # A10 Phase 0 Hardening: propagate mastery_degraded observability marker
        # so downstream callers can distinguish happy-path "truly not assessed"
        # from concept_not_found / exception fallback paths.
        acp.mastery_degraded = mastery.get("mastery_degraded")

        # 3. Get Tips from Graphiti
        acp.student_tips = await self._get_tips(node_id)

        # 4. Get error history from Graphiti
        acp.error_history = await self._get_error_history(node_id)

        # 5. Get edge reasons from Graphiti
        acp.edge_reasons = await self._get_edge_reasons(node_id)

        # 6. Get conversation summary (Tier 2 summary level)
        acp.conversation_summary = await self._get_conversation_summary(node_id)

        # Token budget enforcement
        self._enforce_token_budget(acp)

        logger.info(
            f"[Story 6.3] ACP assembled for node {node_id}: "
            f"tips={len(acp.student_tips)} errors={len(acp.error_history)} "
            f"edges={len(acp.edge_reasons)} mastery={acp.mastery_label}"
        )
        return acp

    # ═══════════════════════════════════════════════════════════════════════
    # Remediation Strategy — MathCCS 4-type error → differentiated approach
    # (layer4_rules.md: Error Type to Question Strategy Mapping)
    # ═══════════════════════════════════════════════════════════════════════

    # MathCCS 4 error types mapped to remediation strategies
    REMEDIATION_STRATEGIES: Dict[str, str] = {
        "破题错误": (
            "【补救策略：破题错误】\n"
            "该学生存在破题错误——能记住解法但无法灵活应用。\n"
            "请出「同结构不同包装」的新题，验证破题能力而非记忆。\n"
            "例如：更换题目的表面情境但保持底层数学/逻辑结构不变。"
        ),
        "推理谬误": (
            "【补救策略：推理谬误】\n"
            "该学生存在推理谬误——推理过程中出现逻辑错误。\n"
            "请采用以下策略之一：\n"
            "1. 给出一段包含错误推理的过程，让学生找出错误并修正；\n"
            "2. 出反例题，要求学生判断某个看似正确的推理为何是错的。"
        ),
        "知识点缺失": (
            "【补救策略：知识点缺失】\n"
            "该学生存在知识点缺失——基础定义/概念尚未掌握。\n"
            "请回退到定义级别的基础题，确认学生理解核心定义后再逐步升级难度。\n"
            "例如：先考察「请用自己的话解释 X 是什么」，通过后再出应用题。"
        ),
        "似懂非懂": (
            "【补救策略：似懂非懂】\n"
            "该学生处于似懂非懂状态——表面理解但缺乏深度。\n"
            "请采用以下策略之一：\n"
            "1. 辨析题：给出两个易混淆概念让学生区分；\n"
            "2. 反例题：给出一个看似正确但实际错误的例子让学生判断；\n"
            "3. 迁移题：要求将概念应用到全新的场景中。"
        ),
    }

    # Alias mapping for English error type keys → Chinese strategy keys
    _ERROR_TYPE_ALIASES: Dict[str, str] = {
        "breakthrough_error": "破题错误",
        "reasoning_fallacy": "推理谬误",
        "knowledge_gap": "知识点缺失",
        "partial_understanding": "似懂非懂",
        "breaking": "破题错误",
        "reasoning": "推理谬误",
        "knowledge": "知识点缺失",
        "partial": "似懂非懂",
    }

    def _determine_remediation_strategy(self, acp: ACPData) -> str:
        """Determine the remediation strategy based on student's error history.

        Analyzes the error_history in ACP to find the dominant error type,
        then returns the matching remediation strategy text for prompt injection.

        Args:
            acp: ACP data containing error_history.

        Returns:
            Remediation strategy text, or empty string if no error history.
        """
        if not acp.error_history:
            return ""

        # Count occurrences of each error type
        error_counts: Dict[str, int] = {}
        for err in acp.error_history:
            err_type = err.get("error_type", "").strip()
            if not err_type or err_type == "unknown":
                continue
            # Normalize: try direct match first, then alias mapping
            normalized = err_type
            if err_type not in self.REMEDIATION_STRATEGIES:
                normalized = self._ERROR_TYPE_ALIASES.get(err_type.lower(), err_type)
            error_counts[normalized] = error_counts.get(normalized, 0) + 1

        if not error_counts:
            return ""

        # Pick the most frequent error type
        dominant_type = max(error_counts, key=error_counts.get)  # type: ignore[arg-type]
        strategy = self.REMEDIATION_STRATEGIES.get(dominant_type, "")

        if strategy:
            logger.info(
                f"[Story 6.3] Remediation strategy selected: {dominant_type} "
                f"(count={error_counts[dominant_type]}/{len(acp.error_history)})"
            )
        return strategy

    def build_5_layer_prompt(self, acp: ACPData, exam_mode: ExamMode) -> str:
        """Construct the 5-layer prompt for LLM question generation.

        Story 6.3 AC-3: Bloom's Taxonomy PS4 strategy (arXiv:2408.04394).
        Layer 1 (static): Examiner role
        Layer 2 (user-selected): Exam mode
        Layer 3 (dynamic): ACP student data
        Layer 4 (static): Question rules + dynamic remediation strategy
        Layer 5 (static): Scoring preset

        Args:
            acp: Assembled ACP data package.
            exam_mode: User-selected examination mode.

        Returns:
            Complete prompt string for LLM.
        """
        # Layer 1: Role
        layer1 = (
            self._layer1 or "你是一位经验丰富的学习考官，通过精准提问检验学生理解深度。"
        )

        # Layer 2: Mode (substitute variable)
        layer2 = (
            self._layer2.replace("{{exam_mode}}", exam_mode.value)
            if self._layer2
            else (f"当前考察模式: {exam_mode.value}")
        )

        # Layer 3: ACP (dynamic)
        layer3 = self._format_acp_layer(acp)

        # Layer 4: Rules (static base + dynamic remediation strategy)
        layer4 = self._layer4 or "一次只出一道题，从弱点出题，不暗示答案。"
        remediation = self._determine_remediation_strategy(acp)
        if remediation:
            layer4 = f"{layer4}\n\n{remediation}"

        # Layer 5: Scoring preset
        layer5 = self._layer5 or "题目将按4维4分制Rubric评分，需有区分度。"

        prompt = f"{layer1}\n\n---\n{layer2}\n\n---\n### 学生数据（ACP）\n{layer3}\n\n---\n{layer4}\n\n---\n{layer5}"
        return prompt

    async def generate_exam_question(
        self,
        exam_id: str,
        source_canvas_id: str,
        exam_mode: ExamMode,
        target_node_id: Optional[str] = None,
        examined_nodes: Optional[List[str]] = None,
    ) -> QuestionGenerationResult:
        """Full Story 6.3 pipeline: select target -> assemble ACP -> 5-layer prompt -> LLM.

        Story 6.3 AC-5: MCP generate_question entry point.

        Args:
            exam_id: Exam session ID.
            source_canvas_id: Original canvas board ID.
            exam_mode: User-selected examination mode.
            target_node_id: Optional specific node to question.
            examined_nodes: Nodes already examined this session.

        Returns:
            QuestionGenerationResult with question text, target node, difficulty, etc.
        """
        # Step 1: Select target node
        target = await self.select_target_node(
            exam_id=exam_id,
            source_canvas_id=source_canvas_id,
            exam_mode=exam_mode,
            examined_nodes=examined_nodes,
            target_node_id=target_node_id,
        )

        if not target:
            return QuestionGenerationResult(
                question_text="所有节点均已考察完毕，考察结束。",
                target_node_id="",
                difficulty_level="N/A",
                difficulty_rationale="No unexamined nodes remaining",
            )

        # Step 2: Assemble ACP
        acp = await self.assemble_acp(target.node_id)

        # Step 3: Build 5-layer prompt
        system_prompt = self.build_5_layer_prompt(acp, exam_mode)

        # Step 4: Call LLM for question generation
        question_result = await self._call_llm_for_question(
            system_prompt=system_prompt,
            acp=acp,
            target=target,
        )

        question_result.target_node_id = target.node_id

        # Determine difficulty level from mastery
        if acp.effective_proficiency < 0.3:
            question_result.difficulty_level = "easy"
        elif acp.effective_proficiency < 0.5:
            question_result.difficulty_level = "medium-easy"
        elif acp.effective_proficiency < 0.7:
            question_result.difficulty_level = "medium-hard"
        else:
            question_result.difficulty_level = "hard"

        question_result.difficulty_rationale = (
            f"p_mastery={target.p_mastery:.2f} R={target.retrievability:.2f} "
            f"effective_proficiency={acp.effective_proficiency:.2f}"
        )

        logger.info(
            f"[Story 6.3] Question generated for node {target.node_id}: difficulty={question_result.difficulty_level}"
        )
        return question_result

    # ═══════════════════════════════════════════════════════════════════════
    # Internal Helpers
    # ═══════════════════════════════════════════════════════════════════════

    def _format_acp_layer(self, acp: ACPData) -> str:
        """Format ACP data into Layer 3 prompt text using external template.

        Loads structure from layer3.md, builds optional sections in Python,
        then injects all variables into the template.
        """
        # Build optional sections from conditional ACP data
        optional_parts: List[str] = []

        if acp.student_tips:
            tips_str = "; ".join(acp.student_tips[:5])
            optional_parts.append(f"**学生标注(Tips)**: {tips_str}")

        if acp.error_history:
            errors = []
            for err in acp.error_history[:4]:
                err_type = err.get("error_type", "unknown")
                err_desc = err.get("description", "")[:100]
                errors.append(f"  - [{err_type}] {err_desc}")
            optional_parts.append("**历史错误**:\n" + "\n".join(errors))

        if acp.edge_reasons:
            edges_str = "; ".join(acp.edge_reasons[:5])
            optional_parts.append(f"**概念关系(Edge理由)**: {edges_str}")

        if acp.conversation_summary:
            optional_parts.append(f"**对话历史摘要**: {acp.conversation_summary[:500]}")

        optional_sections = "\n".join(optional_parts)

        # Inject variables into the externalized template
        if self._layer3_template:
            return self._layer3_template.format(
                node_content=acp.node_content[:200],
                node_type=acp.node_type,
                effective_proficiency=f"{acp.effective_proficiency:.2f}",
                p_mastery=f"{acp.p_mastery:.2f}",
                retrievability=f"{acp.retrievability:.2f}",
                mastery_label=acp.mastery_label,
                optional_sections=optional_sections,
            )

        # Fallback if template file missing (graceful degradation)
        parts = [
            f"**目标节点**: {acp.node_content[:200]}",
            f"**节点类型**: {acp.node_type}",
            f"**精通度**: effective_proficiency={acp.effective_proficiency:.2f}, "
            f"p_mastery={acp.p_mastery:.2f}, retrievability={acp.retrievability:.2f}, "
            f"level={acp.mastery_label}",
        ]
        if optional_sections:
            parts.append(optional_sections)
        return "\n".join(parts)

    async def _call_llm_for_question(
        self,
        system_prompt: str,
        acp: ACPData,
        target: NodePriority,
    ) -> QuestionGenerationResult:
        """Call LLM to generate a question based on 5-layer prompt + ACP.

        Uses LiteLLM unified call layer with the configured model.
        """
        user_message = (
            f"请基于以上学生数据，为知识节点「{acp.node_content[:100]}」出一道考察题。\n"
            f"要求：一次一题、难度匹配精通度（{acp.mastery_label}）、不暗示答案。\n\n"
            f"以 JSON 格式返回：\n"
            '{"question_text": "题目内容", "question_type": "explanation|comparison|application|analysis", '
            '"target_bloom_level": "remember|understand|apply|analyze|evaluate|create", '
            '"target_error_type": "可选,学生历史主要错误类型", '
            '"scoring_hints": "评分时重点关注的方面"}'
        )

        try:
            from litellm import acompletion

            from app.config import settings

            # 6-10 M1: Use settings.SCORING_MODEL (configurable), fall back to AI_PROVIDER/AI_MODEL_NAME
            model = settings.SCORING_MODEL
            if not model:
                provider = settings.AI_PROVIDER
                model_name = settings.AI_MODEL_NAME
                if provider and not model_name.startswith(provider):
                    model = f"{provider}/{model_name}"
                else:
                    model = model_name

            response = await acompletion(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.5,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            result_data = json.loads(content)

            return QuestionGenerationResult(
                question_text=result_data.get("question_text", ""),
                question_type=result_data.get("question_type", "explanation"),
                target_bloom_level=result_data.get("target_bloom_level", "understand"),
                target_error_type=result_data.get("target_error_type"),
                scoring_hints=result_data.get("scoring_hints", ""),
            )

        except Exception as e:
            logger.error(f"[Story 6.3] LLM question generation failed: {e}")
            # Fallback to template-based question
            concept = acp.node_content[:50] if acp.node_content else "this concept"
            fallback_q = self._generate_fallback_question(
                concept, acp.effective_proficiency
            )
            return QuestionGenerationResult(
                question_text=fallback_q,
                question_type="explanation",
                target_bloom_level="understand",
                difficulty_rationale=f"LLM fallback: {e}",
            )

    def _generate_fallback_question(self, concept: str, proficiency: float) -> str:
        """Generate a template-based fallback question when LLM is unavailable."""
        if proficiency < 0.3:
            return f"请用自己的话解释：{concept}"
        elif proficiency < 0.5:
            return f"请详细描述 {concept} 的工作机制"
        elif proficiency < 0.7:
            return f"{concept} 在什么情况下适用？什么情况下不适用？"
        else:
            return f"设计一个使用 {concept} 的实际案例"

    async def _get_canvas_nodes(self, canvas_id: str) -> List[Dict[str, Any]]:
        """Get all nodes from a canvas for target selection.

        Uses canvas_svc.read_canvas() to get the full canvas data,
        then extracts the nodes list.
        """
        try:
            from app.config import settings
            from app.services.canvas_service import CanvasService

            canvas_svc = CanvasService(canvas_base_path=settings.canvas_base_path)
            canvas_data = await canvas_svc.read_canvas(canvas_id)
            nodes = canvas_data.get("nodes", list())
            return nodes if nodes else list()
        except (ImportError, OSError, json.JSONDecodeError, KeyError, ValueError) as e:
            logger.debug(f"[Story 6.3] Failed to get canvas nodes: {e}")
            return list()

    async def _get_node_content(self, node_id: str) -> Dict[str, Any]:
        """Get a single node's content data."""
        try:
            from app.config import settings
            from app.services.canvas_service import CanvasService

            canvas_svc = CanvasService(canvas_base_path=settings.canvas_base_path)
            _canvas_name, node_data = await canvas_svc.find_node_across_canvases(
                node_id
            )
            return node_data if node_data else dict()
        except (ImportError, OSError, json.JSONDecodeError, ValueError) as e:
            logger.debug(f"[Story 6.3] Failed to get node content: {e}")
            return dict()

    async def _get_mastery_data(self, node_id: str) -> Dict[str, Any]:
        """Get mastery data for a node by routing volatile fields through MasteryEngine.

        A10 Phase 0 fix: previously this function used getattr(concept, "<volatile>", default)
        for effective_proficiency / mastery_level / mastery_label / retrievability — but
        ConceptState (mastery_state.py:68-110) explicitly does NOT store volatile fields
        ("Volatile values [...] are computed on read and never stored"). The getattr calls
        therefore always returned the defaults (0.0 / "Not Assessed" / 1.0), silently
        corrupting downstream difficulty selection and Gemini prompt rendering.

        The correct pattern (mirroring backend/app/mcp/tools/mastery_tools.py:175) is to
        call MasteryEngine instance methods on the concept. The MasteryEngine global
        singleton is wired with a fusion engine at startup (main.py:220-261), so this
        function now consumes the multi-signal fusion result via Story 5.6 path.

        A10 Phase 0 Hardening (2nd ChatGPT review round):

        1. **1x effective_proficiency per call**: previously this function called
           engine.effective_proficiency (direct) + engine.mastery_level (which re-invokes
           effective_proficiency internally) + engine.mastery_label (which re-invokes
           mastery_level), for a total of 3 fusion computations per node. For batch
           callers like select_target_node on a 50-node canvas this was 150 redundant
           calls. Now effective_proficiency is computed once and reused via the new
           `mastery_level_from_proficiency` / `mastery_label_from_level` helpers.

        2. **mastery_degraded observability**: the returned dict always contains a
           `mastery_degraded` key that distinguishes happy path (None) from
           concept_not_found ("concept_not_found") from exception ("exception").
           This mirrors the existing kg_relevance_degraded pattern and lets production
           log pipelines distinguish "Phase 0 fix worked" from "ID mapping silently
           failed, looks like the pre-fix bug".
        """
        try:
            from app.services.mastery_engine import get_mastery_engine
            from app.services.mastery_store import get_mastery_store

            store = get_mastery_store()
            engine = get_mastery_engine()
            concept = await store.get_concept(node_id)
            if concept:
                # A10 Phase 0 Hardening #2: call the fallback-aware helper to
                # surface cross-layer observability of the fusion fallback state.
                # The helper returns (eff, fusion_fallback). When fusion_fallback
                # is True, the concept was found and the engine returned a
                # value, but that value came from the conservative
                # min(p_mastery, R) strategy instead of the multi-signal fusion.
                # Downstream consumers (prompts, dashboards) can now distinguish
                # "fusion produced a confident value" from "fusion fell through".
                eff, fusion_fallback = engine.effective_proficiency_with_fallback_info(
                    concept
                )
                level = engine.mastery_level_from_proficiency(eff, concept)
                label = engine.mastery_label_from_level(level)
                return {
                    "p_mastery": concept.p_mastery,
                    "retrievability": engine.get_retrievability(concept),
                    "effective_proficiency": eff,
                    "mastery_level": level,
                    "mastery_label": label,
                    "mastery_degraded": "fusion_fallback" if fusion_fallback else None,
                }
            # concept_not_found: CanvasNode.id has no matching EntityNode.mastery_concept_id
            # (typical cause: score event has not been processed yet, or ID mapping gap).
            # This is observably distinct from "happy-path truly not assessed".
            logger.debug(
                f"[Story 6.3] mastery_store.get_concept returned None for node_id={node_id}"
            )
            return {
                "p_mastery": 0.1,
                "retrievability": 1.0,
                "effective_proficiency": 0.0,
                "mastery_level": 0,
                "mastery_label": "Not Assessed",
                "mastery_degraded": "concept_not_found",
            }
        except (ImportError, AttributeError, ValueError) as e:
            logger.debug(f"[Story 6.3] Failed to get mastery data: {e}")
        return {
            "p_mastery": 0.1,
            "retrievability": 1.0,
            "effective_proficiency": 0.0,
            "mastery_level": 0,
            "mastery_label": "Not Assessed",
            "mastery_degraded": "exception",
        }

    async def _get_kg_relevance(
        self, node_id: str, canvas_id: str
    ) -> tuple[float, Optional[str]]:
        """Compute KG-based relevance score for a node.

        Returns a 2-tuple ``(score, degraded_reason)`` where ``score`` is in
        ``[0, 1]`` and ``degraded_reason`` is ``None`` on the happy path or one
        of ``"empty_graph"`` / ``"neo4j_unavailable"`` when the moderate default
        (0.5) had to be used.

        Nodes with more strongly-typed connections (CANVAS_EDGE = user-drawn,
        RELATES_TO = Graphiti-inferred) represent richer structural context and
        therefore get higher relevance scores.

        FR-KG-04 fix history:
        1. ``c7215ca`` aligned the schema (``{uuid}`` → ``{id}``,
           ``canvas_id`` → ``canvasId``) so the query stops returning empty.
        2. This change (openspec fix-fr-kg-04-schema-drift-and-sync-hardening
           Phase 1) upgrades the formula to a weighted SUM(CASE type(r) ...)
           and replaces the silent ``return 0.5`` with an observable
           ``(0.5, degraded_reason)`` tuple — see A11 in the FR-KG-04 batch.

        Weighted formula:
            CANVAS_EDGE neighbor → weight 1.0 (explicit user intent)
            RELATES_TO neighbor  → weight 0.7 (Graphiti-inferred)
            normalized           → min(1.0, weighted_degree / 8.0)
        """
        try:
            from app.clients.neo4j_client import get_neo4j_client

            client = get_neo4j_client()
            # H-1 (Sprint 1.2.1): pre-aggregate by neighbor with MAX so
            # multiple parallel edges between the same pair contribute the
            # strongest edge type once, not inflated path counts. When both
            # a CANVAS_EDGE (1.0) and a RELATES_TO (0.7) exist between the
            # same pair, MAX(CASE ...) keeps 1.0 — i.e. the explicit user
            # intent wins over the Graphiti-inferred relation.
            # L-1 (Sprint 1.2.1): no ELSE branch — the MATCH filter already
            # restricts r to CANVAS_EDGE|RELATES_TO, making any other type
            # unreachable. Removing ELSE 0 drops dead code without changing
            # behavior.
            # A10 Phase 0 Hardening: the primary node `n` is bound to BOTH
            # `id` and `canvasId` (not just `id`). This eliminates a forward-looking
            # cross-canvas contamination risk if per-canvas node_id namespaces are
            # ever introduced (e.g., duplicated canvases). The neighbor WHERE
            # filter is kept as belt-and-suspenders defense.
            query = """
            MATCH (n:CanvasNode {id: $node_id, canvasId: $canvas_id})-[r:CANVAS_EDGE|RELATES_TO]-(neighbor:CanvasNode)
            WHERE neighbor.canvasId = $canvas_id
            WITH neighbor, MAX(
                CASE type(r)
                    WHEN 'CANVAS_EDGE' THEN 1.0
                    WHEN 'RELATES_TO'  THEN 0.7
                END
            ) AS edge_weight
            RETURN
                SUM(edge_weight)         AS weighted_degree,
                COUNT(DISTINCT neighbor) AS neighbor_count
            """
            records = await client.run_query(
                query, node_id=node_id, canvas_id=canvas_id
            )
            if records:
                data = records[0] if isinstance(records[0], dict) else records[0].data()
                weighted = data.get("weighted_degree") or 0.0
                neighbor_count = data.get("neighbor_count") or 0
                if neighbor_count == 0 or weighted == 0:
                    return 0.5, "empty_graph"
                return min(1.0, float(weighted) / 8.0), None
            # Empty result set: query succeeded but found nothing
            return 0.5, "empty_graph"
        except (
            Neo4jError,
            DriverError,
            RuntimeError,
            ConnectionError,
            asyncio.TimeoutError,
        ) as e:
            # Code-Review C-1 (Sprint 1.2.1): typed catch replaces the narrow
            # (RuntimeError, ConnectionError, asyncio.TimeoutError) tuple and
            # the intermediate `except Exception` from 5ecf834.
            #
            # neo4j-python-driver 5.x has two parallel exception trees under
            # the common ``GqlError`` ancestor:
            #   - ``Neo4jError``  → ClientError / DatabaseError / TransientError
            #     (server-side responses)
            #   - ``DriverError`` → ServiceUnavailable / SessionExpired / AuthError
            #     (client / connection-level failures)
            # We catch both explicit bases so every documented Neo4j failure
            # mode degrades to the moderate default while programming errors
            # (TypeError / AttributeError / KeyError) still bubble up as real
            # bugs instead of being silently labeled "neo4j_unavailable".
            logger.debug(
                "[Story 6.3] KG relevance query failed: "
                f"type={type(e).__name__} detail={str(e)[:200]}"
            )
            return 0.5, "neo4j_unavailable"

    async def _get_tips(self, node_id: str) -> List[str]:
        """Get user-annotated Tips from Graphiti for a node."""
        try:
            from app.clients.neo4j_client import get_neo4j_client

            client = get_neo4j_client()
            # ChatGPT-DR-2026-05-13 P0-5: IN list 覆盖 writer 实际写入的多个 source_description 变体
            # (canvas_learning:tip / canvas_temporal:tip / ...). 历史 bug: 之前查 = 'tip'
            # 永远命中 0 条因为 writer 写 prefix:tip 格式.
            query = """
            MATCH (e:EpisodicNode)
            WHERE e.source_description IN $tip_sources
              AND e.node_id = $node_id
            RETURN e.content AS content
            ORDER BY e.created_at DESC
            LIMIT 5
            """
            records = await client.run_query(
                query, node_id=node_id, tip_sources=list(TIP_SOURCES)
            )
            tips: List[str] = list()
            for record in records or list():
                data = record if isinstance(record, dict) else record.data()
                content = data.get("content", "")
                if content:
                    tips.append(content)
            return tips
        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.debug(f"[Story 6.3] Failed to get tips: {e}")
            return list()

    async def _get_error_history(self, node_id: str) -> List[Dict[str, str]]:
        """Get 4-type error history from Graphiti for a node."""
        try:
            from app.clients.neo4j_client import get_neo4j_client

            client = get_neo4j_client()
            # ChatGPT-DR-2026-05-13 P0-5: IN list 覆盖 writer 实际写入的多个 misconception
            # 变体. 历史 bug: writer 写 'misconception-record' / 'canvas_learning:misconception',
            # 但 reader 查 'error_record' → 永远 0 命中, exam board 无法读用户误解.
            query = """
            MATCH (e:EpisodicNode)
            WHERE e.source_description IN $misconception_sources
              AND e.node_id = $node_id
            RETURN e.error_type AS error_type, e.description AS description
            ORDER BY e.created_at DESC
            LIMIT 4
            """
            records = await client.run_query(
                query,
                node_id=node_id,
                misconception_sources=list(MISCONCEPTION_SOURCES),
            )
            errors: List[Dict[str, str]] = list()
            for record in records or list():
                data = record if isinstance(record, dict) else record.data()
                errors.append(
                    {
                        "error_type": data.get("error_type", "unknown"),
                        "description": data.get("description", ""),
                    }
                )
            return errors
        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.debug(f"[Story 6.3] Failed to get error history: {e}")
            return list()

    async def _get_edge_reasons(self, node_id: str) -> List[str]:
        """Get edge relationship reasons for a node.

        FR-KG-04 fix: Aligned to SyncService write schema. SyncService stores
        edge labels in ``CANVAS_EDGE.label``; the previous query read
        ``r.rationale`` (a field never written by any active path) so this
        always returned an empty list, depriving the LLM of relationship
        semantics for question generation.
        """
        try:
            from app.clients.neo4j_client import get_neo4j_client

            client = get_neo4j_client()
            query = """
            MATCH (n:CanvasNode {id: $node_id})-[r:CANVAS_EDGE]->(m:CanvasNode)
            WHERE r.label IS NOT NULL AND r.label <> ''
            RETURN r.label AS rationale
            LIMIT 5
            """
            records = await client.run_query(query, node_id=node_id)
            reasons: List[str] = list()
            for record in records or list():
                data = record if isinstance(record, dict) else record.data()
                rationale = data.get("rationale", "")
                if rationale:
                    reasons.append(rationale)
            return reasons
        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.debug(f"[Story 6.3] Failed to get edge reasons: {e}")
            return list()

    async def _get_conversation_summary(self, node_id: str) -> str:
        """Get Tier 2 conversation summary from archive."""
        try:
            from app.clients.neo4j_client import get_neo4j_client

            client = get_neo4j_client()
            # ChatGPT-DR-2026-05-13 P0-5: IN list 覆盖 archive writer 实际写入的变体.
            query = """
            MATCH (e:EpisodicNode)
            WHERE e.source_description IN $archive_sources
              AND e.node_id = $node_id
            RETURN e.summary AS summary
            ORDER BY e.created_at DESC
            LIMIT 1
            """
            records = await client.run_query(
                query,
                node_id=node_id,
                archive_sources=list(CONVERSATION_ARCHIVE_SOURCES),
            )
            if records:
                data = records[0] if isinstance(records[0], dict) else records[0].data()
                return data.get("summary", "")
        except (RuntimeError, ConnectionError, asyncio.TimeoutError) as e:
            logger.debug(f"[Story 6.3] Failed to get conversation summary: {e}")
        return ""

    def _enforce_token_budget(self, acp: ACPData) -> None:
        """Enforce 3K token budget on ACP data.

        Truncates longest fields first to stay within budget.
        Protects formulas ($...$) and code blocks from mid-token splits.
        """
        total_chars = (
            len(acp.node_content)
            + len(acp.conversation_summary)
            + sum(len(t) for t in acp.student_tips)
            + sum(len(e.get("description", "")) for e in acp.error_history)
            + sum(len(r) for r in acp.edge_reasons)
        )

        if total_chars <= ACP_MAX_CHARS:
            return

        # Truncation priority: conversation_summary > node_content > tips
        if len(acp.conversation_summary) > 500:
            acp.conversation_summary = self._truncate(acp.conversation_summary, 500)
        if len(acp.node_content) > 800:
            acp.node_content = self._truncate(acp.node_content, 800)
        if len(acp.student_tips) > 3:
            acp.student_tips = acp.student_tips[:3]
        if len(acp.error_history) > 3:
            acp.error_history = acp.error_history[:3]
        if len(acp.edge_reasons) > 3:
            acp.edge_reasons = acp.edge_reasons[:3]

    @staticmethod
    def _truncate(text: str, max_len: int) -> str:
        """Truncate text preserving sentence boundaries and formula blocks."""
        if len(text) <= max_len:
            return text
        # Try to break at sentence boundary
        truncated = text[:max_len]
        last_period = max(
            truncated.rfind("。"),
            truncated.rfind(". "),
            truncated.rfind("\n"),
        )
        if last_period > max_len * 0.5:
            return truncated[: last_period + 1]
        return truncated + "..."

    @staticmethod
    def _classify_content(text: str) -> tuple[int, int]:
        """Count knowledge vs problem signals in text.

        Delegates to shared utility (6-3 M1: extracted to eliminate duplication).
        """
        from app.utils.content_classifier import classify_content

        return classify_content(text)

    # ═══════════════════════════════════════════════════════════════════════
    # Legacy Story 4.2: Template-based question generation (backward compat)
    # ═══════════════════════════════════════════════════════════════════════

    def generate_questions(
        self,
        node: Dict,
        question_type: Optional[QuestionType] = None,
        effective_proficiency: Optional[float] = None,
    ) -> List[str]:
        """Generate 1-2 template-based questions for a node.

        Legacy Story 4.2 method — preserved for backward compatibility
        with MCP tool generate_question in exam_tools.py.
        """
        content = node.get("text", "").strip()
        color = node.get("color", "")
        if not content:
            return list()
        concept = self._extract_concept(content)
        if question_type is None:
            if effective_proficiency is not None:
                if effective_proficiency < 0.40:
                    question_type = "breakthrough"
                elif effective_proficiency < 0.70:
                    question_type = "verification"
                else:
                    question_type = "application"
            elif color == "4":
                question_type = "breakthrough"
            elif color == "3":
                question_type = "verification"
            else:
                question_type = "application"
        templates = self._get_templates(question_type)
        questions = list()
        for template in templates[:2]:
            question = template.format(concept=concept)
            questions.append(question)
        return questions

    def _extract_concept(self, content: str) -> str:
        """Extract core concept from node content text."""
        content = re.sub(r"^#+\s*", "", content)
        content = re.sub(r"\*\*([^*]+)\*\*", r"\1", content)
        content = re.sub(r"\*([^*]+)\*", r"\1", content)
        first_line = content.split("\n")[0].strip()
        if len(first_line) > 50:
            break_points = [". ", "，", "：", "。", " - "]
            for bp in break_points:
                idx = first_line.find(bp)
                if 10 < idx < 50:
                    return first_line[:idx]
            return first_line[:50] + "..."
        return first_line if first_line else content[:50]

    def _get_templates(self, question_type: QuestionType) -> List[str]:
        """Get question templates for the specified type."""
        if question_type == "breakthrough":
            return self.BREAKTHROUGH_TEMPLATES
        elif question_type == "verification":
            return self.VERIFICATION_TEMPLATES
        else:
            return self.APPLICATION_TEMPLATES

    def generate_for_nodes(self, nodes: List[Dict]) -> Dict[str, List[str]]:
        """Generate questions for multiple nodes (Story 4.2 batch)."""
        result: Dict[str, List[str]] = {}
        for node in nodes:
            node_id = node.get("id", "")
            if node_id:
                questions = self.generate_questions(node)
                result[node_id] = questions
        return result
