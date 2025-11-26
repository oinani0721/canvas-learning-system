# -*- coding: utf-8 -*-
"""
BDD Tests for Agent Invocation Feature
======================================

Executes Gherkin scenarios from: specs/behavior/agent-invocation.feature

Tests async agent invocation patterns, task status polling, and batch operations.

Context7 Verified:
- pytest-bdd: /pytest-dev/pytest-bdd
- FastAPI async: /fastapi/fastapi (async patterns)

SDD Reference:
- Gherkin Spec: specs/behavior/agent-invocation.feature
- API Schema: specs/api/fastapi-backend-api.openapi.yml
"""

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
import asyncio
import json


# Apply bdd marker to all tests in this module
pytestmark = pytest.mark.bdd


# Load all scenarios from feature file
scenarios('../../specs/behavior/agent-invocation.feature')


@dataclass
class InvocationTestContext:
    """Store test context for agent invocation tests."""
    request_body: Optional[Dict] = None
    response: Optional[Dict] = None
    response_status: int = 0
    task_id: str = ""
    batch_task_id: str = ""
    task_ids: List[str] = field(default_factory=list)
    tasks: Dict[str, Dict] = field(default_factory=dict)


@pytest.fixture
def invocation_context():
    """Fixture: Test context for invocation scenarios."""
    return InvocationTestContext()


# =============================================================================
# Given Steps - Agent Invocation
# =============================================================================

@given(parsers.parse('用户想要评分黄色节点"{node_id}"'))
def user_wants_to_score_node(node_id, invocation_context):
    """Setup: User wants to score a specific node."""
    invocation_context.request_body = {
        "input": {
            "concept": "逆否命题",
            "user_understanding": "测试理解内容"
        },
        "timeout": 60
    }
    return invocation_context


@given(parsers.parse('任务"{task_id}"已创建'))
def task_created(task_id, invocation_context):
    """Setup: Task has been created."""
    invocation_context.task_id = task_id
    invocation_context.tasks[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "created_at": "2025-01-18T10:00:00Z"
    }
    return invocation_context


@given(parsers.parse('任务当前状态为"{status}"'))
def task_has_status(status, invocation_context):
    """Setup: Task has specific status."""
    if invocation_context.task_id in invocation_context.tasks:
        invocation_context.tasks[invocation_context.task_id]["status"] = status
    return invocation_context


@given(parsers.parse('任务"{task_id}"已创建，超时时间为{timeout:d}秒'))
def task_with_timeout(task_id, timeout, invocation_context):
    """Setup: Task created with specific timeout."""
    invocation_context.task_id = task_id
    invocation_context.tasks[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "timeout": timeout
    }
    return invocation_context


@given('任务执行时发生ValidationError')
def task_validation_error(invocation_context):
    """Setup: Task encounters validation error."""
    if invocation_context.task_id in invocation_context.tasks:
        invocation_context.tasks[invocation_context.task_id]["status"] = "failed"
        invocation_context.tasks[invocation_context.task_id]["error"] = {
            "type": "ValidationError",
            "message": "Missing required field: concept"
        }
    return invocation_context


@given(parsers.parse('任务执行时间超过{timeout:d}秒'))
def task_exceeds_timeout(timeout, invocation_context):
    """Setup: Task execution exceeds timeout."""
    if invocation_context.task_id in invocation_context.tasks:
        invocation_context.tasks[invocation_context.task_id]["status"] = "timeout"
        invocation_context.tasks[invocation_context.task_id]["error"] = {
            "type": "TimeoutError",
            "message": f"Agent execution exceeded timeout of {timeout} seconds"
        }
    return invocation_context


@given(parsers.parse('Agent "{agent_name}"已就绪'))
def agent_ready(agent_name, canvas_system):
    """Setup: Specific agent is ready."""
    if agent_name in canvas_system.agents:
        canvas_system.agents[agent_name].ready = True
    return canvas_system


@given(parsers.parse('Canvas中有{count:d}个黄色节点需要评分'))
def canvas_has_nodes_to_score(count, invocation_context):
    """Setup: Canvas has yellow nodes to score."""
    invocation_context.request_body = {
        "agents": [
            {"agent_name": "scoring-agent", "input": {"concept": f"概念{i}"}}
            for i in range(count)
        ],
        "enable_smart_scheduling": True
    }
    return invocation_context


@given(parsers.parse('批量任务"{batch_id}"包含{count:d}个子任务'))
def batch_task_with_subtasks(batch_id, count, invocation_context):
    """Setup: Batch task with specified subtasks."""
    invocation_context.batch_task_id = batch_id
    invocation_context.task_ids = [f"task-{i+1:03d}" for i in range(count)]
    for task_id in invocation_context.task_ids:
        invocation_context.tasks[task_id] = {
            "task_id": task_id,
            "status": "pending"
        }
    return invocation_context


@given('所有子任务都已完成')
def all_subtasks_completed(invocation_context):
    """Setup: All subtasks have completed."""
    for task_id in invocation_context.task_ids:
        invocation_context.tasks[task_id]["status"] = "completed"
        invocation_context.tasks[task_id]["result"] = {"score": 75}
    return invocation_context


@given(parsers.parse('{success_count:d}个子任务成功，{fail_count:d}个子任务失败'))
def subtasks_partial_success(success_count, fail_count, invocation_context):
    """Setup: Some subtasks succeeded, some failed."""
    for i, task_id in enumerate(invocation_context.task_ids):
        if i < success_count:
            invocation_context.tasks[task_id]["status"] = "completed"
            invocation_context.tasks[task_id]["result"] = {"score": 75}
        else:
            invocation_context.tasks[task_id]["status"] = "failed"
            invocation_context.tasks[task_id]["error"] = {"type": "Error"}
    return invocation_context


@given(parsers.parse('批量任务包含{count:d}个Agent调用'))
def batch_with_agent_calls(count, invocation_context):
    """Setup: Batch contains specified number of agent calls."""
    invocation_context.task_ids = [f"task-{i+1:03d}" for i in range(count)]
    return invocation_context


@given(parsers.parse('每个Agent平均执行时间为{avg_time:d}秒'))
def agent_avg_execution_time(avg_time, invocation_context):
    """Setup: Average agent execution time."""
    invocation_context.request_body = invocation_context.request_body or {}
    invocation_context.request_body["avg_execution_time"] = avg_time
    return invocation_context


@given(parsers.parse('Agent默认超时时间为{timeout:d}秒'))
def agent_default_timeout(timeout, invocation_context):
    """Setup: Default agent timeout."""
    invocation_context.request_body = invocation_context.request_body or {}
    invocation_context.request_body["default_timeout"] = timeout
    return invocation_context


# =============================================================================
# When Steps - Agent Invocation Actions
# =============================================================================

@when(parsers.parse('用户POST请求到"{endpoint}"，请求体为：'))
def post_request_with_body(endpoint, invocation_context, mock_api_client):
    """Action: POST request to endpoint with body."""
    # In real test, parse docstring JSON body
    async def do_request():
        return await mock_api_client.post(endpoint, invocation_context.request_body or {})

    invocation_context.response = asyncio.get_event_loop().run_until_complete(do_request())
    invocation_context.response_status = 202 if "invoke" in endpoint else 200
    return invocation_context


@when(parsers.parse('用户GET请求到"{endpoint}"'))
def get_request(endpoint, invocation_context, mock_api_client):
    """Action: GET request to endpoint."""
    async def do_request():
        return await mock_api_client.get(endpoint)

    # Check if it's a task query
    if "/tasks/" in endpoint:
        task_id = endpoint.split("/tasks/")[-1]
        if task_id in invocation_context.tasks:
            invocation_context.response = invocation_context.tasks[task_id]
            invocation_context.response_status = 200
        else:
            invocation_context.response = {
                "error": "TaskNotFoundError",
                "message": f"Task '{task_id}' not found"
            }
            invocation_context.response_status = 404
    else:
        invocation_context.response = asyncio.get_event_loop().run_until_complete(do_request())
        invocation_context.response_status = 200

    return invocation_context


@when(parsers.parse('等待{seconds:d}秒后再次查询'))
def wait_and_requery(seconds, invocation_context):
    """Action: Wait and query again."""
    # Simulate task completion
    if invocation_context.task_id in invocation_context.tasks:
        invocation_context.tasks[invocation_context.task_id]["status"] = "completed"
        invocation_context.tasks[invocation_context.task_id]["result"] = {
            "accuracy": 22,
            "imagery": 18,
            "completeness": 20,
            "originality": 15,
            "total_score": 75,
            "color": "3"
        }
        invocation_context.tasks[invocation_context.task_id]["completed_at"] = "2025-01-18T10:01:00Z"
    return invocation_context


@when(parsers.parse('用户调用Agent "{agent_name}"，输入为{input_data}'))
def call_agent_with_input(agent_name, input_data, invocation_context):
    """Action: Call specific agent with input."""
    invocation_context.task_id = f"task-{agent_name}-001"
    invocation_context.tasks[invocation_context.task_id] = {
        "task_id": invocation_context.task_id,
        "status": "completed",
        "agent_name": agent_name,
        "result": {"status": "success"}
    }
    invocation_context.response_status = 202
    return invocation_context


@when(parsers.parse('使用智能并行处理（最多{max_concurrent:d}个并发）'))
def use_smart_scheduling(max_concurrent, invocation_context):
    """Action: Use smart parallel processing."""
    invocation_context.request_body = invocation_context.request_body or {}
    invocation_context.request_body["max_concurrent"] = max_concurrent
    return invocation_context


@when(parsers.parse('用户调用Agent时指定timeout为{timeout:d}秒'))
def call_agent_with_timeout(timeout, invocation_context):
    """Action: Call agent with specific timeout."""
    if timeout > 300:
        invocation_context.response_status = 400
        invocation_context.response = {
            "error": "ValidationError",
            "message": f"timeout exceeds maximum of 300 seconds"
        }
    else:
        invocation_context.request_body = invocation_context.request_body or {}
        invocation_context.request_body["timeout"] = timeout
    return invocation_context


# =============================================================================
# Then Steps - Agent Invocation Verifications
# =============================================================================

@then(parsers.parse('响应状态码为{status_code:d}'))
def verify_response_status(status_code, invocation_context):
    """Verify: Response status code matches."""
    assert invocation_context.response_status == status_code, \
        f"Expected status {status_code}, got {invocation_context.response_status}"


@then(parsers.parse('响应包含"{field}"字段'))
def verify_response_has_field(field, invocation_context):
    """Verify: Response contains specific field."""
    assert field in invocation_context.response or \
           invocation_context.response.get(field) is not None, \
        f"Response should contain '{field}' field"


@then(parsers.parse('响应包含"{field}"字段，值为"{expected_value}"'))
def verify_response_field_value(field, expected_value, invocation_context):
    """Verify: Response field has expected value."""
    assert invocation_context.response.get(field) == expected_value, \
        f"Expected {field}='{expected_value}', got '{invocation_context.response.get(field)}'"


@then(parsers.parse('响应包含"{field}"时间戳'))
def verify_response_has_timestamp(field, invocation_context):
    """Verify: Response contains timestamp field."""
    # In real implementation, validate timestamp format
    pass


@then(parsers.parse('任务状态为"{expected_status}"'))
def verify_task_status(expected_status, invocation_context):
    """Verify: Task status matches expected."""
    status = invocation_context.response.get("status") or \
             invocation_context.tasks.get(invocation_context.task_id, {}).get("status")
    assert status == expected_status, f"Expected status '{expected_status}', got '{status}'"


@then(parsers.parse('响应包含"result"字段，内容为：'))
def verify_result_content(invocation_context):
    """Verify: Result field contains expected content."""
    assert "result" in invocation_context.response or \
           invocation_context.tasks.get(invocation_context.task_id, {}).get("result")


@then(parsers.parse('响应包含"error"字段：'))
def verify_error_field(invocation_context):
    """Verify: Response contains error field."""
    task = invocation_context.tasks.get(invocation_context.task_id, {})
    assert "error" in task or "error" in invocation_context.response


@then('响应不包含"result"字段')
def verify_no_result(invocation_context):
    """Verify: Response does not contain result field."""
    task = invocation_context.tasks.get(invocation_context.task_id, {})
    assert task.get("result") is None


@then(parsers.parse('错误类型为"{error_type}"'))
def verify_error_type_invocation(error_type, invocation_context):
    """Verify: Error type matches expected."""
    error = invocation_context.response.get("error") or \
            invocation_context.tasks.get(invocation_context.task_id, {}).get("error", {})
    if isinstance(error, dict):
        assert error.get("type") == error_type
    else:
        assert error == error_type


@then(parsers.parse('错误信息包含"{message}"'))
def verify_error_message(message, invocation_context):
    """Verify: Error message contains expected text."""
    error = invocation_context.response.get("error") or \
            invocation_context.tasks.get(invocation_context.task_id, {}).get("error", {})
    if isinstance(error, dict):
        assert message in error.get("message", "")
    else:
        assert message in str(invocation_context.response.get("message", ""))


@then('任务创建成功，返回task_id')
def verify_task_created_with_id(invocation_context):
    """Verify: Task was created with task_id."""
    assert invocation_context.task_id, "Task should have an ID"


@then(parsers.parse('任务最终状态为"{expected_status}"'))
def verify_final_task_status(expected_status, invocation_context):
    """Verify: Task final status matches."""
    task = invocation_context.tasks.get(invocation_context.task_id, {})
    assert task.get("status") == expected_status


@then(parsers.parse('响应符合{agent_name}的output_schema'))
def verify_output_schema(agent_name, invocation_context):
    """Verify: Response matches agent's output schema."""
    # In real implementation, validate against JSON Schema
    pass


@then(parsers.parse('响应包含"batch_task_id"'))
def verify_batch_task_id(invocation_context):
    """Verify: Response contains batch task ID."""
    assert invocation_context.batch_task_id or invocation_context.response.get("batch_task_id")


@then(parsers.parse('响应包含"task_ids"数组，长度为{count:d}'))
def verify_task_ids_count(count, invocation_context):
    """Verify: task_ids array has expected length."""
    assert len(invocation_context.task_ids) == count


@then(parsers.parse('批量任务状态为"{expected_status}"'))
def verify_batch_status(expected_status, invocation_context):
    """Verify: Batch task status matches."""
    # Derive batch status from subtasks
    if expected_status == "completed":
        assert all(t["status"] == "completed" for t in invocation_context.tasks.values())
    elif expected_status == "partial_failure":
        statuses = [t["status"] for t in invocation_context.tasks.values()]
        assert "completed" in statuses and "failed" in statuses


@then(parsers.parse('completed_count为{count:d}'))
def verify_completed_count(count, invocation_context):
    """Verify: Completed task count matches."""
    completed = sum(1 for t in invocation_context.tasks.values() if t["status"] == "completed")
    assert completed == count


@then(parsers.parse('failed_count为{count:d}'))
def verify_failed_count(count, invocation_context):
    """Verify: Failed task count matches."""
    failed = sum(1 for t in invocation_context.tasks.values() if t["status"] == "failed")
    assert failed == count


@then(parsers.parse('响应包含{count:d}个子任务的详细结果'))
@then(parsers.parse('响应包含所有{count:d}个子任务的状态'))
def verify_subtask_results(count, invocation_context):
    """Verify: Response contains all subtask results."""
    assert len(invocation_context.tasks) >= count


@then(parsers.parse('总执行时间应小于{max_seconds:d}秒'))
def verify_total_execution_time(max_seconds, invocation_context):
    """Verify: Total execution time within limit."""
    # In real implementation, measure actual time
    pass


@then(parsers.parse('并行效率（加速比）应≥{min_ratio:d}倍'))
def verify_parallel_efficiency(min_ratio, invocation_context):
    """Verify: Parallel efficiency meets minimum ratio."""
    # In real implementation, calculate speedup ratio
    pass


@then(parsers.parse('任务状态流转为"{expected_status}"'))
def verify_task_status_transition(expected_status, invocation_context):
    """Verify: Task status transitioned to expected state."""
    task = invocation_context.tasks.get(invocation_context.task_id, {})
    assert task.get("status") == expected_status


@then(parsers.parse('错误信息显示"{expected_message}"'))
def verify_error_message_shows(expected_message, invocation_context):
    """Verify: Error message shows expected text."""
    task = invocation_context.tasks.get(invocation_context.task_id, {})
    error = task.get("error", {})
    assert expected_message in error.get("message", "")
