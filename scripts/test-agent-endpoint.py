#!/usr/bin/env python3
# Canvas Learning System - Agent Endpoint Test Script
# ✅ Verified from ADR-008: Testing Framework - pytest Ecosystem (httpx client)
"""
Agent端点测试脚本 - 用于快速验证所有Agent端点的可用性。

Usage:
    # 测试单个端点
    python scripts/test-agent-endpoint.py --endpoint memory

    # 测试所有端点
    python scripts/test-agent-endpoint.py --all

    # 详细输出模式
    python scripts/test-agent-endpoint.py --all -v

    # 自定义base URL
    python scripts/test-agent-endpoint.py --all --base-url http://localhost:8080

    # 只测试健康检查端点
    python scripts/test-agent-endpoint.py --health-only

Exit Codes:
    0 - 所有测试通过
    1 - 有测试失败

[Source: docs/stories/21.5.6.story.md]
[Source: docs/prd/EPIC-21.5-AGENT-RELIABILITY-FIX.md#story-21-5-6]
"""

import argparse
import io
import json
import sys
from typing import Any, Dict, List, Optional, Tuple

# Fix Windows console encoding for Unicode characters (emojis)
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ✅ Verified from ADR-008: httpx for HTTP client
import httpx

# ════════════════════════════════════════════════════════════════════════════════
# Endpoint Configuration
# ════════════════════════════════════════════════════════════════════════════════

# Agent endpoints [Source: specs/api/fastapi-backend-api.openapi.yml]
AGENT_ENDPOINTS: Dict[str, str] = {
    "memory": "/api/v1/agents/explain/memory",
    "oral": "/api/v1/agents/explain/oral",
    "four-level": "/api/v1/agents/explain/four-level",
    "basic": "/api/v1/agents/decompose/basic",
    "deep": "/api/v1/agents/decompose/deep",
    "clarification": "/api/v1/agents/explain/clarification",
    "comparison": "/api/v1/agents/explain/comparison",
    "example": "/api/v1/agents/explain/example",
    "scoring": "/api/v1/agents/scoring",
    "verification": "/api/v1/agents/verification/question",
    "canvas-orchestrator": "/api/v1/agents/canvas/orchestrate",
}

# Health check endpoints [Source: Story 21.5.4]
HEALTH_ENDPOINTS: Dict[str, str] = {
    "health": "/api/v1/health",
    "health-ai": "/api/v1/health/ai",
    "health-agents": "/api/v1/health/agents",
    "health-full": "/api/v1/health/full",
}

# Test payload for agent endpoints
# [Source: specs/api/fastapi-backend-api.openapi.yml#DecomposeRequest]
DEFAULT_PAYLOAD: Dict[str, Any] = {
    "canvas_name": "test.canvas",
    "node_id": "test-node-001",
}

# Default timeout (30s for agent calls that may be slow)
# [Source: ADR-008 - Constraint]
DEFAULT_TIMEOUT = 30.0


# ════════════════════════════════════════════════════════════════════════════════
# Test Functions
# ════════════════════════════════════════════════════════════════════════════════


def test_endpoint(
    client: httpx.Client,
    name: str,
    path: str,
    method: str = "POST",
    payload: Optional[Dict[str, Any]] = None,
    verbose: bool = False,
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Test a single endpoint.

    Args:
        client: httpx Client instance
        name: Endpoint name for display
        path: API path
        method: HTTP method (GET or POST)
        payload: Request payload for POST requests
        verbose: Show detailed output

    Returns:
        Tuple of (success, message, response_data)

    [Source: docs/stories/21.5.6.story.md - AC 2, 3]
    """
    try:
        if method == "GET":
            response = client.get(path)
        else:
            response = client.post(path, json=payload or DEFAULT_PAYLOAD)

        status_code = response.status_code

        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"raw": response.text[:500]}

        if status_code == 200:
            return True, "SUCCESS", data
        elif status_code == 202:
            # Accepted - async task started
            return True, "ACCEPTED (async task)", data
        else:
            # Error response
            # [Source: ADR-009 - Error code classification]
            error_type = data.get("error_type", data.get("detail", "Unknown"))
            bug_id = data.get("bug_id", "")
            msg = f"FAILED ({status_code})"
            if bug_id:
                msg += f" [Bug ID: {bug_id}]"
            return False, msg, data

    except httpx.ConnectError:
        return False, "CONNECTION_ERROR (server not running?)", None
    except httpx.TimeoutException:
        return False, "TIMEOUT (>30s)", None
    except Exception as e:
        return False, f"ERROR: {type(e).__name__}: {str(e)}", None


def test_health_endpoints(
    client: httpx.Client,
    verbose: bool = False,
) -> Tuple[int, int]:
    """
    Test all health check endpoints.

    Returns:
        Tuple of (passed_count, total_count)

    [Source: docs/stories/21.5.6.story.md - Task 4]
    """
    passed = 0
    total = len(HEALTH_ENDPOINTS)

    print("\n" + "=" * 60)
    print("Health Check Endpoints")
    print("=" * 60)

    for name, path in HEALTH_ENDPOINTS.items():
        success, message, data = test_endpoint(
            client, name, path, method="GET", verbose=verbose
        )

        if success:
            print(f"  ✅ {name}: {message}")
            passed += 1
        else:
            print(f"  ❌ {name}: {message}")

        if verbose and data:
            print(f"     Response: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")

    return passed, total


def test_agent_endpoints(
    client: httpx.Client,
    endpoints: Optional[List[str]] = None,
    verbose: bool = False,
) -> Tuple[int, int]:
    """
    Test agent endpoints.

    Args:
        client: httpx Client instance
        endpoints: List of endpoint names to test (None = all)
        verbose: Show detailed output

    Returns:
        Tuple of (passed_count, total_count)

    [Source: docs/stories/21.5.6.story.md - Task 2, 3]
    """
    # Determine which endpoints to test
    if endpoints:
        targets = {k: v for k, v in AGENT_ENDPOINTS.items() if k in endpoints}
    else:
        targets = AGENT_ENDPOINTS

    passed = 0
    total = len(targets)

    print("\n" + "=" * 60)
    print("Agent Endpoints")
    print("=" * 60)

    for name, path in targets.items():
        success, message, data = test_endpoint(
            client, name, path, method="POST", payload=DEFAULT_PAYLOAD, verbose=verbose
        )

        if success:
            print(f"  ✅ {name}: {message}")
            passed += 1
        else:
            print(f"  ❌ {name}: {message}")
            if data and verbose:
                # Show error details
                detail = data.get("detail", data.get("message", ""))
                if detail:
                    print(f"     Detail: {detail}")

        if verbose and data:
            # Truncate large responses
            response_str = json.dumps(data, indent=2, ensure_ascii=False)
            if len(response_str) > 500:
                response_str = response_str[:500] + "..."
            print(f"     Response: {response_str}")

    return passed, total


def print_summary(
    health_results: Tuple[int, int],
    agent_results: Tuple[int, int],
) -> bool:
    """
    Print test summary and return overall success.

    [Source: docs/stories/21.5.6.story.md - AC 2]
    """
    health_passed, health_total = health_results
    agent_passed, agent_total = agent_results

    total_passed = health_passed + agent_passed
    total_tests = health_total + agent_total

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"  Health Endpoints: {health_passed}/{health_total} 通过")
    print(f"  Agent Endpoints:  {agent_passed}/{agent_total} 通过")
    print("-" * 60)
    print(f"  总计: {total_passed}/{total_tests} 通过")

    if total_passed == total_tests:
        print("\n✅ All tests passed!")
        return True
    else:
        print(f"\n❌ {total_tests - total_passed} test(s) failed!")
        return False


# ════════════════════════════════════════════════════════════════════════════════
# Main Entry Point
# ════════════════════════════════════════════════════════════════════════════════


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code (0=success, 1=failure)

    [Source: docs/stories/21.5.6.story.md - AC 4, 5]
    """
    parser = argparse.ArgumentParser(
        description="Canvas Learning System - Agent端点测试脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 测试单个端点
  python scripts/test-agent-endpoint.py --endpoint memory

  # 测试所有端点
  python scripts/test-agent-endpoint.py --all

  # 详细输出
  python scripts/test-agent-endpoint.py --all -v

  # 只测试健康检查
  python scripts/test-agent-endpoint.py --health-only
        """,
    )

    # Mutually exclusive group for test scope
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--endpoint", "-e",
        type=str,
        choices=list(AGENT_ENDPOINTS.keys()),
        help="测试指定的Agent端点",
    )
    group.add_argument(
        "--all", "-a",
        action="store_true",
        help="测试所有端点 (健康检查 + Agent)",
    )
    group.add_argument(
        "--health-only",
        action="store_true",
        help="只测试健康检查端点",
    )

    # Optional arguments
    parser.add_argument(
        "--base-url", "-b",
        type=str,
        default="http://localhost:8000",
        help="后端服务器URL (默认: http://localhost:8000)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细输出 (包括完整响应)",
    )
    parser.add_argument(
        "--timeout", "-t",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"请求超时时间(秒) (默认: {DEFAULT_TIMEOUT})",
    )

    args = parser.parse_args()

    # Print header
    print("=" * 60)
    print("Canvas Learning System - Agent Endpoint Test")
    print("=" * 60)
    print(f"Base URL: {args.base_url}")
    print(f"Timeout: {args.timeout}s")
    print(f"Verbose: {args.verbose}")

    # Create HTTP client
    # ✅ Verified from ADR-008: httpx client with timeout
    client = httpx.Client(
        base_url=args.base_url,
        timeout=args.timeout,
    )

    try:
        if args.health_only:
            # Only test health endpoints
            health_results = test_health_endpoints(client, args.verbose)
            agent_results = (0, 0)

        elif args.endpoint:
            # Test single endpoint
            health_results = (0, 0)
            agent_results = test_agent_endpoints(
                client, [args.endpoint], args.verbose
            )

        else:
            # Test all endpoints
            health_results = test_health_endpoints(client, args.verbose)
            agent_results = test_agent_endpoints(client, None, args.verbose)

        # Print summary and determine exit code
        success = print_summary(health_results, agent_results)
        return 0 if success else 1

    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
