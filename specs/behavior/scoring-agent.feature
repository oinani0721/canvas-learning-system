Feature: Scoring Agent - 4维评分系统
  作为一个Canvas学习系统用户
  我想要对我的个人理解（黄色节点）进行4维评分
  以便量化评估我的理解质量并获得智能推荐

  Background:
    Given Canvas学习系统已启动
    And scoring-agent已就绪
    And Canvas文件"笔记库/离散数学/离散数学.canvas"存在

  Rule: 4维评分机制
    每个黄色节点的理解文本必须按照4个维度评分：
    - Accuracy (准确性): 0-25分
    - Imagery (具象性): 0-25分
    - Completeness (完整性): 0-25分
    - Originality (原创性): 0-25分
    总分 = 4个维度之和 (0-100分)

  Rule: 颜色流转规则
    根据总分判断节点颜色：
    - 总分 ≥ 80分 → 绿色 (2) - 完全理解
    - 总分 60-79分 → 紫色 (3) - 似懂非懂
    - 总分 < 60分 → 保持红色 (1) - 不理解

  Scenario: 评分黄色节点 - 完全理解（绿色）
    Given 黄色节点"yellow-001"存在
    And 节点内容为"逆否命题是原命题否定后再交换条件和结论，且与原命题逻辑等价。例如：原命题'若p则q'，逆否命题为'若非q则非p'。常用于数学证明中的反证法。"
    When 用户调用scoring-agent评分节点"yellow-001"
    Then scoring-agent返回成功响应
    And Accuracy评分为24分
    And Imagery评分为23分
    And Completeness评分为22分
    And Originality评分为18分
    And 总分为87分
    And 颜色判断为"2"（绿色）
    And 推荐agents列表为空（因为已完全理解）

  Scenario: 评分黄色节点 - 似懂非懂（紫色）
    Given 黄色节点"yellow-002"存在
    And 节点内容为"逆否命题是将原命题的条件和结论都否定后再交换位置"
    When 用户调用scoring-agent评分节点"yellow-002"
    Then scoring-agent返回成功响应
    And Accuracy评分在20-25分之间
    And Imagery评分在15-20分之间
    And Completeness评分在15-22分之间
    And Originality评分在10-18分之间
    And 总分在60-79分之间
    And 颜色判断为"3"（紫色）
    And 推荐agents列表包含2-5个agents
    And 推荐列表可能包含"clarification-path"（针对Accuracy低）
    And 推荐列表可能包含"oral-explanation"（针对Imagery低）
    And 推荐列表可能包含"memory-anchor"（针对Originality低）

  Scenario: 评分黄色节点 - 不理解（红色）
    Given 黄色节点"yellow-003"存在
    And 节点内容为"逆否命题就是把命题反过来"
    When 用户调用scoring-agent评分节点"yellow-003"
    Then scoring-agent返回成功响应
    And Accuracy评分小于15分
    And 总分小于60分
    And 颜色判断为"1"（红色）
    And 推荐agents列表包含"basic-decomposition"
    And 推荐agents列表包含"oral-explanation"

  Scenario: 批量评分Canvas中所有黄色节点
    Given Canvas中存在3个黄色节点
      | node_id    | text                                          |
      | yellow-001 | 逆否命题是原命题否定后再交换，且逻辑等价         |
      | yellow-002 | 充分条件：p成立能推出q成立                     |
      | yellow-003 | 必要条件：缺少q则p不成立                       |
    When 用户调用scoring-agent批量评分所有黄色节点
    Then scoring-agent返回3个评分结果
    And 每个结果都包含4维分数和总分
    And 每个结果都包含颜色判断
    And 平均处理时间小于3秒/节点

  Scenario: Story 2.9智能推荐 - 基于维度弱项推荐agents
    Given 黄色节点"yellow-004"的评分结果为：
      | dimension     | score |
      | Accuracy      | 15    |
      | Imagery       | 20    |
      | Completeness  | 18    |
      | Originality   | 22    |
    When scoring-agent生成智能推荐
    Then 推荐列表包含"clarification-path"（因为Accuracy最低）
    And 推荐列表包含"oral-explanation"（因为Imagery较低）
    And 推荐理由说明"Accuracy较低（15/25），需要系统化澄清概念"

  Scenario: 错误处理 - 缺少必需字段
    Given scoring-agent调用请求缺少"concept"字段
    When 用户调用scoring-agent
    Then scoring-agent返回400错误
    And 错误类型为"ValidationError"
    And 错误信息包含"Missing required field: concept"

  Scenario: 错误处理 - 空白理解文本
    Given 黄色节点"yellow-005"的内容为空字符串
    When 用户调用scoring-agent评分节点"yellow-005"
    Then scoring-agent返回400错误
    And 错误类型为"ValidationError"
    And 错误信息包含"user_understanding cannot be empty"

  Scenario: 性能要求 - 单节点评分响应时间
    Given 黄色节点"yellow-006"存在且内容长度为200字
    When 用户调用scoring-agent评分节点"yellow-006"
    Then 响应时间小于5秒
    And 返回完整的4维评分结果

  Scenario: 颜色流转 - 从红色到紫色
    Given 红色节点"question-001"经过学习后添加了黄色理解节点"yellow-007"
    And 黄色节点"yellow-007"的理解质量达到60-79分
    When scoring-agent评分完成
    Then 原红色节点"question-001"应该流转为紫色（3）
    And Canvas文件中节点"question-001"的color字段更新为"3"

  Scenario: 颜色流转 - 从紫色到绿色
    Given 紫色节点"question-002"经过深度学习后优化了黄色节点"yellow-008"
    And 黄色节点"yellow-008"的理解质量达到≥80分
    When scoring-agent评分完成
    Then 原紫色节点"question-002"应该流转为绿色（2）
    And Canvas文件中节点"question-002"的color字段更新为"2"
