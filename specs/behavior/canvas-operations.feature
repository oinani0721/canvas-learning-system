Feature: Canvas文件操作和节点管理
  作为一个Canvas学习系统用户
  我想要对Canvas文件进行读写和节点管理操作
  以便维护我的学习白板和知识结构

  Background:
    Given Canvas API服务器已启动
    And Canvas文件目录"笔记库/离散数学"存在

  Rule: Canvas颜色系统
    Canvas使用5种颜色代码：
    - "1" (红色): 不理解/未通过
    - "2" (绿色): 完全理解/已通过
    - "3" (紫色): 似懂非懂/待检验
    - "5" (蓝色): AI补充解释
    - "6" (黄色): 个人理解输出区

  Rule: 节点类型
    Canvas支持4种节点类型：
    - text: 文本节点
    - file: 文件节点（引用markdown/图片等）
    - group: 分组节点
    - link: 超链接节点

  Scenario: 读取Canvas文件
    Given Canvas文件"笔记库/离散数学/离散数学.canvas"存在
    When 用户GET请求到"/canvas?path=笔记库/离散数学/离散数学.canvas"
    Then 响应状态码为200
    And 响应包含"nodes"数组
    And 响应包含"edges"数组
    And nodes数组长度大于0

  Scenario: 读取不存在的Canvas文件
    When 用户GET请求到"/canvas?path=笔记库/不存在的文件.canvas"
    Then 响应状态码为404
    And 错误类型为"FileNotFoundError"
    And 错误信息包含"Canvas文件不存在"

  Scenario: 写入Canvas文件
    Given Canvas数据包含3个节点和2条边
    When 用户POST请求到"/canvas"，请求体为：
      """json
      {
        "path": "笔记库/测试/test.canvas",
        "data": {
          "nodes": [...],
          "edges": [...]
        }
      }
      """
    Then 响应状态码为200
    And 响应包含"success"字段，值为true
    And 响应包含"nodes_count"字段，值为3
    And 响应包含"edges_count"字段，值为2

  Scenario: 添加新节点到Canvas
    Given Canvas文件"笔记库/离散数学/离散数学.canvas"已加载
    When 用户POST请求到"/canvas/discrete-math/nodes"，请求体为：
      """json
      {
        "type": "text",
        "x": 100,
        "y": 200,
        "width": 300,
        "height": 100,
        "color": "1",
        "text": "什么是充分条件？"
      }
      """
    Then 响应状态码为201
    And 响应包含自动生成的"id"字段
    And 响应包含所有提供的节点属性

  Scenario: 查询Canvas中的所有黄色节点
    Given Canvas文件包含15个节点，其中3个是黄色节点
    When 用户GET请求到"/canvas/discrete-math/nodes?color=6"
    Then 响应状态码为200
    And 响应包含"nodes"数组，长度为3
    And 响应包含"total"字段，值为3
    And 所有返回的节点color字段都为"6"

  Scenario: 更新节点颜色（颜色流转）
    Given 节点"question-001"当前颜色为"1"（红色）
    When 用户PATCH请求到"/canvas/discrete-math/nodes/question-001"，请求体为：
      """json
      {
        "color": "3"
      }
      """
    Then 响应状态码为200
    And 响应中节点"question-001"的color字段为"3"

  Scenario: 更新节点文本内容
    Given 黄色节点"yellow-001"存在
    And 当前文本为"逆否命题是..."
    When 用户PATCH请求到"/canvas/discrete-math/nodes/yellow-001"，请求体为：
      """json
      {
        "text": "逆否命题是原命题否定后再交换条件和结论，且与原命题逻辑等价"
      }
      """
    Then 响应状态码为200
    And 响应中节点"yellow-001"的text字段已更新

  Scenario: 删除节点
    Given 节点"temporary-node-001"存在
    When 用户DELETE请求到"/canvas/discrete-math/nodes/temporary-node-001"
    Then 响应状态码为204
    And 节点"temporary-node-001"不再存在于Canvas中

  Scenario: 添加边（连接两个节点）
    Given 节点"question-001"和"yellow-001"都存在
    When 用户POST请求到"/canvas/discrete-math/edges"，请求体为：
      """json
      {
        "fromNode": "question-001",
        "toNode": "yellow-001",
        "fromSide": "bottom",
        "toSide": "top"
      }
      """
    Then 响应状态码为201
    And 响应包含自动生成的边ID
    And 边成功连接"question-001"和"yellow-001"

  Scenario: 删除边
    Given 边"edge-001"存在，连接"question-001"到"yellow-001"
    When 用户DELETE请求到"/canvas/discrete-math/edges/edge-001"
    Then 响应状态码为204
    And 边"edge-001"不再存在于Canvas中

  Scenario: 分析Canvas统计信息
    Given Canvas文件包含如下节点：
      | color | count |
      | 1     | 3     |
      | 2     | 5     |
      | 3     | 2     |
      | 5     | 3     |
      | 6     | 2     |
    When 用户POST请求到"/canvas/discrete-math/analyze"
    Then 响应状态码为200
    And 响应包含"total_nodes"字段，值为15
    And 响应包含"nodes_by_color"对象：
      """json
      {
        "red": 3,
        "green": 5,
        "purple": 2,
        "blue": 3,
        "yellow": 2
      }
      """
    And 响应包含"yellow_nodes"数组，长度为2
    And 响应包含"verification_nodes"数组，长度为5（红色3 + 紫色2）

  Scenario: v1.1布局算法 - 黄色节点定位
    Given 问题节点"question-001"位于(100, 200)，尺寸为300x100
    When 系统为其创建配套黄色节点
    Then 黄色节点x坐标应为150（question_x + 50px）
    And 黄色节点y坐标应为360（question_y + question_height + 30px间隔 + 30px黄色上边距）
    And 黄色节点与问题节点垂直对齐

  Scenario: 批量节点创建 - 拆解结果
    Given basic-decomposition返回3个问题
    When 系统批量创建3个红色问题节点 + 3个黄色理解节点
    Then Canvas中新增6个节点
    And 每个问题节点都配有正下方的黄色节点
    And 所有节点都有连接边

  Scenario: 错误处理 - 无效的节点类型
    When 用户创建节点时提供type="invalid-type"
    Then 响应状态码为400
    And 错误类型为"ValidationError"
    And 错误信息包含"Invalid node type"

  Scenario: 错误处理 - 无效的颜色代码
    When 用户更新节点颜色为"7"
    Then 响应状态码为400
    And 错误类型为"ValidationError"
    And 错误信息包含"Invalid color code"

  Scenario: 错误处理 - 缺少必需字段
    When 用户创建text节点但未提供"text"字段
    Then 响应状态码为400
    And 错误类型为"ValidationError"
    And 错误信息包含"text field is required for text nodes"

  Scenario: 性能要求 - 大型Canvas读取
    Given Canvas文件包含500个节点和400条边
    When 用户读取Canvas文件
    Then 响应时间应小于2秒
    And 所有节点和边数据完整返回

  Scenario: 并发安全 - 多用户同时写入
    Given 2个用户同时修改同一个Canvas文件
    When 用户A更新节点"yellow-001"的文本
    And 用户B更新节点"yellow-002"的颜色
    Then 两个操作都应成功完成
    And 不应出现数据丢失或覆盖

  Scenario: UTF-8编码支持 - 中文内容
    Given 节点文本包含中文字符"什么是逆否命题？"
    When 写入Canvas文件并重新读取
    Then 中文字符应正确显示
    And 不应出现编码问题或乱码
