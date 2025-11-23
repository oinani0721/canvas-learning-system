Feature: Agent异步调用和任务管理
  作为一个Canvas学习系统用户
  我想要异步调用各种Agent并查询任务状态
  以便在不阻塞的情况下获取Agent执行结果

  Background:
    Given Agent API服务器已启动
    And 所有14个Agents已就绪

  Rule: 异步调用模式
    所有Agent调用都是异步的：
    1. POST /agents/{agentName}/invoke → 返回task_id（202状态码）
    2. GET /agents/tasks/{taskId} → 轮询任务状态
    3. 当status=completed时，result字段包含执行结果

  Rule: 任务状态流转
    任务状态必须按照以下顺序流转：
    - pending → running → completed (成功)
    - pending → running → failed (失败)
    - pending → running → timeout (超时)

  Scenario: 异步调用scoring-agent成功
    Given 用户想要评分黄色节点"yellow-001"
    When 用户POST请求到"/agents/scoring-agent/invoke"，请求体为：
      """json
      {
        "input": {
          "concept": "逆否命题",
          "user_understanding": "逆否命题是将原命题的条件和结论都否定后再交换位置"
        },
        "timeout": 60
      }
      """
    Then 响应状态码为202
    And 响应包含"task_id"字段
    And 响应包含"status"字段，值为"pending"
    And 响应包含"agent_name"字段，值为"scoring-agent"
    And 响应包含"created_at"时间戳

  Scenario: 轮询任务状态 - 任务完成
    Given 任务"task-20250118-001"已创建
    And 任务当前状态为"running"
    When 用户GET请求到"/agents/tasks/task-20250118-001"
    And 等待2秒后再次查询
    Then 响应状态码为200
    And 任务状态为"completed"
    And 响应包含"result"字段，内容为：
      """json
      {
        "accuracy": 22,
        "imagery": 18,
        "completeness": 20,
        "originality": 15,
        "total_score": 75,
        "color": "3"
      }
      """
    And 响应包含"completed_at"时间戳

  Scenario: 轮询任务状态 - 任务失败
    Given 任务"task-20250118-002"已创建
    And 任务执行时发生ValidationError
    When 用户GET请求到"/agents/tasks/task-20250118-002"
    Then 响应状态码为200
    And 任务状态为"failed"
    And 响应包含"error"字段：
      """json
      {
        "type": "ValidationError",
        "message": "Missing required field: concept"
      }
      """
    And 响应不包含"result"字段

  Scenario: 轮询任务状态 - 任务超时
    Given 任务"task-20250118-003"已创建，超时时间为30秒
    And 任务执行时间超过30秒
    When 用户GET请求到"/agents/tasks/task-20250118-003"
    Then 响应状态码为200
    And 任务状态为"timeout"
    And 响应包含"error"字段：
      """json
      {
        "type": "TimeoutError",
        "message": "Agent execution exceeded timeout of 30 seconds"
      }
      """

  Scenario: 查询不存在的任务
    When 用户GET请求到"/agents/tasks/nonexistent-task-id"
    Then 响应状态码为404
    And 错误类型为"TaskNotFoundError"
    And 错误信息包含"Task 'nonexistent-task-id' not found"

  Scenario: 调用不存在的Agent
    When 用户POST请求到"/agents/invalid-agent-name/invoke"
    Then 响应状态码为404
    And 错误类型为"AgentNotFoundError"
    And 错误信息包含"Agent 'invalid-agent-name' not found"

  Scenario Outline: 调用所有14个Agents
    Given Agent "<agent_name>"已就绪
    When 用户调用Agent "<agent_name>"，输入为<input>
    Then 任务创建成功，返回task_id
    And 任务最终状态为"completed"
    And 响应符合<agent_name>的output_schema

    Examples:
      | agent_name                    | input                                                    |
      | basic-decomposition           | {"concept": "逆否命题"}                                   |
      | deep-decomposition            | {"concept": "逆否命题", "user_understanding": "..."}     |
      | oral-explanation              | {"concept": "逆否命题"}                                   |
      | clarification-path            | {"concept": "逆否命题"}                                   |
      | comparison-table              | {"concepts": ["逆否命题", "否命题"]}                      |
      | memory-anchor                 | {"concept": "逆否命题"}                                   |
      | four-level-explanation        | {"concept": "逆否命题"}                                   |
      | example-teaching              | {"concept": "逆否命题在证明中的应用"}                      |
      | scoring-agent                 | {"concept": "逆否命题", "user_understanding": "..."}     |
      | verification-question-agent   | {"canvas_path": "离散数学.canvas"}                        |
      | canvas-orchestrator           | {"operation": "decompose", "node_id": "question-001"}  |
      | review-board-agent-selector   | {"yellow_nodes": [...]}                                  |
      | graphiti-memory-agent         | {"session_data": {...}}                                  |

  Scenario: 批量Agent调用 - 智能并行处理
    Given Canvas中有10个黄色节点需要评分
    When 用户POST请求到"/agents/batch/invoke"，请求体为：
      """json
      {
        "agents": [
          {"agent_name": "scoring-agent", "input": {...}},
          {"agent_name": "oral-explanation", "input": {...}},
          {"agent_name": "clarification-path", "input": {...}}
        ],
        "enable_smart_scheduling": true
      }
      """
    Then 响应状态码为202
    And 响应包含"batch_task_id"
    And 响应包含"task_ids"数组，长度为3

  Scenario: 查询批量任务状态 - 所有成功
    Given 批量任务"batch-20250118-001"包含3个子任务
    And 所有子任务都已完成
    When 用户GET请求到"/agents/batch/tasks/batch-20250118-001"
    Then 响应状态码为200
    And 批量任务状态为"completed"
    And completed_count为3
    And failed_count为0
    And 响应包含3个子任务的详细结果

  Scenario: 查询批量任务状态 - 部分失败
    Given 批量任务"batch-20250118-002"包含5个子任务
    And 3个子任务成功，2个子任务失败
    When 用户GET请求到"/agents/batch/tasks/batch-20250118-002"
    Then 响应状态码为200
    And 批量任务状态为"partial_failure"
    And completed_count为3
    And failed_count为2
    And 响应包含所有5个子任务的状态

  Scenario: 性能要求 - 批量并行加速
    Given 批量任务包含10个Agent调用
    And 每个Agent平均执行时间为10秒
    When 使用智能并行处理（最多12个并发）
    Then 总执行时间应小于15秒
    And 并行效率（加速比）应≥6倍

  Scenario: 超时控制 - 自定义超时时间
    Given Agent默认超时时间为60秒
    When 用户调用Agent时指定timeout为30秒
    And Agent执行时间超过30秒
    Then 任务状态流转为"timeout"
    And 错误信息显示"exceeded timeout of 30 seconds"

  Scenario: 超时控制 - 最大超时限制
    When 用户调用Agent时指定timeout为600秒（10分钟）
    Then 响应状态码为400
    And 错误类型为"ValidationError"
    And 错误信息包含"timeout exceeds maximum of 300 seconds"
