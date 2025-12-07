"""
Agents Router for Canvas Learning System API

Provides endpoints for AI Agent invocation (decompose, score, explain).

✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter)
"""

import uuid

from fastapi import APIRouter

from ..models import (
    DecomposeRequest,
    DecomposeResponse,
    ErrorResponse,
    ExplainRequest,
    ExplainResponse,
    NodeRead,
    NodeScore,
    ScoreRequest,
    ScoreResponse,
)

router = APIRouter(prefix="/agents", tags=["Agents"])


def _generate_mock_node(text: str, color: str = "5") -> NodeRead:
    """Generate a mock node for testing."""
    return NodeRead(
        id=uuid.uuid4().hex[:8],
        type="text",
        text=text,
        x=100,
        y=100,
        width=300,
        height=100,
        color=color
    )


@router.post(
    "/decompose/basic",
    response_model=DecomposeResponse,
    summary="基础概念拆解",
    operation_id="decompose_basic",
    responses={
        400: {"model": ErrorResponse, "description": "验证错误"}
    }
)
async def decompose_basic(request: DecomposeRequest) -> DecomposeResponse:
    """
    Basic concept decomposition.

    Decomposes a difficult concept into basic guiding questions.

    Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1decompose~1basic
    """
    # Mock response for testing
    questions = [
        f"关于'{request.node_id}'的基础问题1：这个概念的定义是什么？",
        f"关于'{request.node_id}'的基础问题2：它有哪些核心组成部分？",
        f"关于'{request.node_id}'的基础问题3：它的应用场景是什么？"
    ]

    created_nodes = [
        _generate_mock_node(q, "1") for q in questions
    ]

    return DecomposeResponse(
        questions=questions,
        created_nodes=created_nodes
    )


@router.post(
    "/decompose/deep",
    response_model=DecomposeResponse,
    summary="深度概念拆解",
    operation_id="decompose_deep",
    responses={
        400: {"model": ErrorResponse, "description": "验证错误"}
    }
)
async def decompose_deep(request: DecomposeRequest) -> DecomposeResponse:
    """
    Deep concept decomposition.

    Creates deep verification questions to test true understanding.

    Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1decompose~1deep
    """
    questions = [
        f"深度问题1：为什么'{request.node_id}'是这样设计的？",
        "深度问题2：如果改变条件会发生什么？",
        "深度问题3：这个概念与其他相关概念有什么联系？"
    ]

    created_nodes = [
        _generate_mock_node(q, "6") for q in questions
    ]

    return DecomposeResponse(
        questions=questions,
        created_nodes=created_nodes
    )


@router.post(
    "/score",
    response_model=ScoreResponse,
    summary="评分用户理解",
    operation_id="score_understanding",
    responses={
        400: {"model": ErrorResponse, "description": "验证错误"}
    }
)
async def score_understanding(request: ScoreRequest) -> ScoreResponse:
    """
    Score user's understanding.

    Evaluates user's understanding using 4-dimension scoring.

    Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1score
    """
    scores = []
    for node_id in request.node_ids:
        # Mock scoring
        accuracy = 8.0
        imagery = 7.0
        completeness = 8.0
        originality = 6.0
        total = accuracy + imagery + completeness + originality

        # Determine color based on total
        if total >= 32:
            new_color = "2"  # Green
        elif total >= 24:
            new_color = "3"  # Yellow
        else:
            new_color = "4"  # Red

        scores.append(NodeScore(
            node_id=node_id,
            accuracy=accuracy,
            imagery=imagery,
            completeness=completeness,
            originality=originality,
            total=total,
            new_color=new_color
        ))

    return ScoreResponse(scores=scores)


@router.post(
    "/explain/oral",
    response_model=ExplainResponse,
    summary="口语化解释",
    operation_id="explain_oral",
    responses={
        400: {"model": ErrorResponse, "description": "验证错误"}
    }
)
async def explain_oral(request: ExplainRequest) -> ExplainResponse:
    """
    Generate oral-style explanation.

    Creates professor-like teaching explanation.

    Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1explain~1oral
    """
    explanation = (
        f"好，同学们，今天我们来讲一讲'{request.node_id}'这个概念。"
        "你们可以把它想象成...（口语化解释内容）"
    )

    return ExplainResponse(
        explanation=explanation,
        created_node_id=uuid.uuid4().hex[:8]
    )


@router.post(
    "/explain/clarification",
    response_model=ExplainResponse,
    summary="澄清路径生成",
    operation_id="explain_clarification",
    responses={
        400: {"model": ErrorResponse, "description": "验证错误"}
    }
)
async def explain_clarification(request: ExplainRequest) -> ExplainResponse:
    """
    Generate clarification path.

    Creates systematic clarification document (1500+ words).

    Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1explain~1clarification
    """
    explanation = (
        f"# 澄清路径：{request.node_id}\n\n"
        "## 第一步：理解基础概念\n\n"
        "...（澄清内容）"
    )

    return ExplainResponse(
        explanation=explanation,
        created_node_id=uuid.uuid4().hex[:8]
    )


@router.post(
    "/explain/comparison",
    response_model=ExplainResponse,
    summary="对比表格生成",
    operation_id="explain_comparison",
    responses={
        400: {"model": ErrorResponse, "description": "验证错误"}
    }
)
async def explain_comparison(request: ExplainRequest) -> ExplainResponse:
    """
    Generate comparison table.

    Creates structured comparison table.

    Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1explain~1comparison
    """
    explanation = (
        f"# 对比表格：{request.node_id}\n\n"
        "| 维度 | 概念A | 概念B |\n"
        "|------|-------|-------|\n"
        "| 定义 | ... | ... |"
    )

    return ExplainResponse(
        explanation=explanation,
        created_node_id=uuid.uuid4().hex[:8]
    )


@router.post(
    "/explain/memory",
    response_model=ExplainResponse,
    summary="记忆锚点生成",
    operation_id="explain_memory",
    responses={
        400: {"model": ErrorResponse, "description": "验证错误"}
    }
)
async def explain_memory(request: ExplainRequest) -> ExplainResponse:
    """
    Generate memory anchor.

    Creates vivid analogies and mnemonics.

    Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1explain~1memory
    """
    explanation = (
        f"# 记忆锚点：{request.node_id}\n\n"
        "## 类比故事\n"
        "想象一下你正在...（记忆锚点内容）"
    )

    return ExplainResponse(
        explanation=explanation,
        created_node_id=uuid.uuid4().hex[:8]
    )


@router.post(
    "/explain/four-level",
    response_model=ExplainResponse,
    summary="四层次解释",
    operation_id="explain_four_level",
    responses={
        400: {"model": ErrorResponse, "description": "验证错误"}
    }
)
async def explain_four_level(request: ExplainRequest) -> ExplainResponse:
    """
    Generate four-level explanation.

    Creates progressive 4-level explanations.

    Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1explain~1four-level
    """
    explanation = (
        f"# 四层次解释：{request.node_id}\n\n"
        "## Level 1: 入门级\n...\n\n"
        "## Level 2: 进阶级\n...\n\n"
        "## Level 3: 专业级\n...\n\n"
        "## Level 4: 创新级\n..."
    )

    return ExplainResponse(
        explanation=explanation,
        created_node_id=uuid.uuid4().hex[:8]
    )


@router.post(
    "/explain/example",
    response_model=ExplainResponse,
    summary="例题教学",
    operation_id="explain_example",
    responses={
        400: {"model": ErrorResponse, "description": "验证错误"}
    }
)
async def explain_example(request: ExplainRequest) -> ExplainResponse:
    """
    Generate example teaching.

    Creates complete problem-solving tutorials.

    Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1explain~1example
    """
    explanation = (
        f"# 例题教学：{request.node_id}\n\n"
        "## 题目\n...\n\n"
        "## 解题思路\n...\n\n"
        "## 详细解答\n...\n\n"
        "## 总结与拓展\n..."
    )

    return ExplainResponse(
        explanation=explanation,
        created_node_id=uuid.uuid4().hex[:8]
    )
