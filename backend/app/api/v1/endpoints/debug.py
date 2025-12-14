# Canvas Learning System - Debug Endpoints
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: path operation decorators)
"""
Debug endpoints for Canvas Learning System API.

This module provides debug endpoints for:
- Retrieving recent bug logs
- Getting specific bug details by ID

[Source: docs/stories/21.5.3.story.md - AC-3, AC-4]
[Source: docs/prd/EPIC-21.5-AGENT-RELIABILITY-FIX.md#story-21-5-3]
"""

import logging
from typing import Any, Dict, List

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter)
from fastapi import APIRouter, HTTPException, Query

from app.core.bug_tracker import bug_tracker

# Get logger for this module
logger = logging.getLogger(__name__)

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter)
# Pattern: Create router instance with tags for OpenAPI grouping
router = APIRouter()


@router.get(
    "/bugs",
    response_model=List[Dict[str, Any]],
    summary="获取最近的Bug日志",
    description="返回最近记录的Bug列表，按时间倒序排列（最新在前）",
    operation_id="get_recent_bugs",
    responses={
        200: {
            "description": "Bug日志列表",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "bug_id": "BUG-A1B2C3D4",
                            "timestamp": "2025-12-14T10:30:00Z",
                            "endpoint": "/api/v1/agents/scoring",
                            "error_type": "ValueError",
                            "error_message": "Invalid input"
                        }
                    ]
                }
            }
        }
    }
)
async def get_recent_bugs(
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="返回的最大记录数（1-200）"
    )
) -> List[Dict[str, Any]]:
    """
    获取最近的Bug日志记录。

    返回最近记录的Bug列表，用于调试和问题追踪。
    结果按时间倒序排列（最新在前）。

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: Query parameters)

    [Source: docs/stories/21.5.3.story.md - AC-3]
    [Source: docs/prd/EPIC-21.5-AGENT-RELIABILITY-FIX.md#story-21-5-3]

    Args:
        limit: 返回的最大记录数（默认50，最大200）

    Returns:
        List[Dict]: Bug记录列表

    Example Response:
        [
            {
                "bug_id": "BUG-A1B2C3D4",
                "timestamp": "2025-12-14T10:30:00Z",
                "endpoint": "/api/v1/agents/scoring",
                "error_type": "ValueError",
                "error_message": "Invalid input",
                "request_params": {"canvas_path": "test.canvas"},
                "stack_trace": "Traceback (most recent call last)..."
            }
        ]
    """
    logger.debug(f"Fetching recent bugs, limit={limit}")

    bugs = bug_tracker.get_recent_bugs(limit=limit)

    # ✅ Verified from Context7:/websites/pydantic_dev (topic: model_dump)
    # Convert Pydantic models to dicts with ISO format timestamps
    return [bug.model_dump(mode="json") for bug in bugs]


# ✅ IMPORTANT: Static routes MUST be defined before path parameter routes
# FastAPI matches routes in order - /bugs/stats must come before /bugs/{bug_id}
# Otherwise "stats" would be matched as a bug_id parameter
# [Source: CODE-001 fix from QA review docs/qa/gates/21.5.3-bug-tracking-log-system.yml]
@router.get(
    "/bugs/stats",
    response_model=Dict[str, Any],
    summary="获取Bug统计信息",
    description="返回Bug日志的统计摘要，包括总数、按类型分组等",
    operation_id="get_bug_stats",
    responses={
        200: {
            "description": "Bug统计信息",
            "content": {
                "application/json": {
                    "example": {
                        "total_bugs": 42,
                        "by_error_type": {
                            "ValueError": 15,
                            "KeyError": 10,
                            "TypeError": 17
                        },
                        "by_endpoint": {
                            "/api/v1/agents/scoring": 20,
                            "/api/v1/canvas/nodes": 22
                        }
                    }
                }
            }
        }
    }
)
async def get_bug_stats() -> Dict[str, Any]:
    """
    获取Bug日志的统计摘要。

    返回Bug的总数、按错误类型分组的计数、按端点分组的计数等统计信息。

    [Source: docs/stories/21.5.3.story.md - AC-5]

    Returns:
        Dict: Bug统计信息
    """
    logger.debug("Fetching bug statistics")

    bugs = bug_tracker.get_recent_bugs(limit=1000)

    # 统计按错误类型分组
    by_error_type: Dict[str, int] = {}
    for bug in bugs:
        error_type = bug.error_type
        by_error_type[error_type] = by_error_type.get(error_type, 0) + 1

    # 统计按端点分组
    by_endpoint: Dict[str, int] = {}
    for bug in bugs:
        endpoint = bug.endpoint
        by_endpoint[endpoint] = by_endpoint.get(endpoint, 0) + 1

    return {
        "total_bugs": len(bugs),
        "by_error_type": by_error_type,
        "by_endpoint": by_endpoint,
    }


@router.get(
    "/bugs/{bug_id}",
    response_model=Dict[str, Any],
    summary="获取特定Bug详情",
    description="根据bug_id获取特定Bug的详细信息",
    operation_id="get_bug_by_id",
    responses={
        200: {
            "description": "Bug详细信息",
            "content": {
                "application/json": {
                    "example": {
                        "bug_id": "BUG-A1B2C3D4",
                        "timestamp": "2025-12-14T10:30:00Z",
                        "endpoint": "/api/v1/agents/scoring",
                        "error_type": "ValueError",
                        "error_message": "Invalid input",
                        "request_params": {"canvas_path": "test.canvas"},
                        "stack_trace": "Traceback..."
                    }
                }
            }
        },
        404: {
            "description": "Bug不存在",
            "content": {
                "application/json": {
                    "example": {
                        "code": 404,
                        "message": "Bug 'BUG-A1B2C3D4' not found"
                    }
                }
            }
        }
    }
)
async def get_bug_by_id(bug_id: str) -> Dict[str, Any]:
    """
    根据bug_id获取特定Bug的详细信息。

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: path parameters)

    [Source: docs/stories/21.5.3.story.md - AC-4]
    [Source: docs/prd/EPIC-21.5-AGENT-RELIABILITY-FIX.md#story-21-5-3]

    Args:
        bug_id: Bug的唯一标识符（格式: BUG-{uuid8}）

    Returns:
        Dict: Bug详细信息

    Raises:
        HTTPException: 404 如果Bug不存在
    """
    logger.debug(f"Fetching bug details for {bug_id}")

    # 搜索所有bug记录
    bugs = bug_tracker.get_recent_bugs(limit=1000)  # 搜索最近1000条

    for bug in bugs:
        if bug.bug_id == bug_id:
            return bug.model_dump(mode="json")

    # Bug不存在
    raise HTTPException(
        status_code=404,
        detail=f"Bug '{bug_id}' not found"
    )
