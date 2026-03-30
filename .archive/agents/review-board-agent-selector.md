---
name: review-board-agent-selector
title: 智能Agent选择器
version: "10.1.0"  # Story 10.1版本
description: |
  Canvas学习系统的智能Agent选择器，支持单Agent和多Agent推荐。
  基于黄色理解节点的质量分析，智能推荐最适合的Agent类型，
  并支持并行执行以提升学习效率。

epic: 10
story: 10.1
status: implemented
last_updated: "2025-01-27"

# 功能特性
features:
  - ✅ 单Agent推荐（向后兼容）
  - ✅ 多Agent推荐（1-5个Agent）
  - ✅ 理解质量四维分析
  - ✅ 并行执行支持（最多20个Agent）
  - ✅ 置信度评分系统
  - ✅ Agent组合优化建议
  - ✅ 执行时间估算
  - ✅ 后续学习建议

# 核心方法
methods:
  analyze_understanding_quality:
    description: 分析黄色理解节点的质量
    input:
      - node_text: str - 节点文本内容
      - context: Dict (可选) - 上下文信息
    output:
      has_content: bool
      word_count: int
      quality_score: float (0-1)

  analyze_understanding_quality_advanced:
    description: 高级理解质量分析（Story 10.1新增）
    input:
      - node_text: str - 节点文本内容
      - context: Dict (可选) - 上下文信息
    output:
      accuracy_score: float - 准确性评分
      completeness_score: float - 完整性评分
      clarity_score: float - 清晰度评分
      originality_score: float - 原创性评分
      overall_quality: float - 总体质量评分
      analysis_time_ms: float - 分析耗时

  recommend_multiple_agents:
    description: 推荐多个Agent（Story 10.1核心功能）
    input:
      - quality_analysis: Dict - 质量分析结果
      - max_recommendations: int (可选) - 最大推荐数
      - context: Dict (可选) - 上下文信息
    output:
      analysis_id: str - 分析ID
      node_id: str - 节点ID
      recommended_agents: List[AgentRecommendation] - 推荐的Agent列表
      processing_strategy: ProcessingStrategy - 处理策略
      complementary_combinations: List[Combination] - 互补组合

  process_agents_parallel:
    description: 并行处理多个Agent（Story 10.1核心功能）
    input:
      - agent_recommendations: Dict - Agent推荐结果
      - canvas_path: str - Canvas文件路径
      - node_id: str - 目标节点ID
      - max_concurrent: int (可选) - 最大并发数
    output:
      execution_id: str - 执行ID
      status: str - 执行状态
      results: List[ExecutionResult] - 执行结果
      execution_summary: ExecutionSummary - 执行摘要

# 数据模型
data_models:
  AgentRecommendation:
    agent_name: str - Agent类型名称
    confidence_score: float - 置信度评分(0-1)
    reasoning: str - 推荐理由
    priority: int - 优先级(1-N)
    estimated_duration: str - 预估执行时间
    suggested_follow_up: List[str] - 后续建议

  ProcessingStrategy:
    execution_mode: str - 执行模式(single/parallel/batch_parallel)
    max_concurrent: int - 最大并发数
    total_estimated_duration: str - 总预估时间
    optimization_suggestions: List[str] - 优化建议

  Combination:
    type: str - 组合类型(complementary/sequential)
    agents: List[str] - 组合中的Agent
    description: str - 组合描述
    efficiency_boost: str - 效率提升百分比

  ExecutionResult:
    agent_name: str - Agent名称
    success: bool - 是否成功
    result: Any - 执行结果
    execution_time: float - 执行时间
    confidence: float - 置信度
    priority: int - 优先级

  ExecutionSummary:
    total_execution_time: float - 总执行时间
    average_time_per_agent: float - 平均每个Agent时间
    parallel_efficiency: float - 并行效率
    success_rate: float - 成功率
    max_concurrent_used: int - 使用的最大并发数

# 配置参数
configuration:
  recommendations:
    max_recommendations: 5 - 最大推荐Agent数量
    default_confidence_threshold: 0.7 - 默认置信度阈值
    min_confidence_threshold: 0.5 - 最小置信度阈值
    enable_follow_up_suggestions: true - 启用后续建议
    priority_sorting: true - 启用优先级排序

  quality_weights:
    accuracy: 0.3 - 准确性权重
    completeness: 0.3 - 完整性权重
    clarity: 0.2 - 清晰度权重
    originality: 0.2 - 原创性权重

  concurrency:
    max_agents_per_node: 20 - 单节点最大Agent并发数
    parallel_execution_timeout: 300 - 并行执行超时(秒)
    retry_attempts: 3 - 重试次数

# Agent类型
agent_types:
  decomposition:
    - basic-decomposition - 基础拆解
    - deep-decomposition - 深度拆解

  explanation:
    - oral-explanation - 口语化解释
    - clarification-path - 澄清路径
    - four-level-explanation - 四层次解释
    - comparison-table - 对比表
    - memory-anchor - 记忆锚点

  application:
    - example-teaching - 例题教学

  evaluation:
    - scoring-agent - 评分
    - verification-question-agent - 检验问题

# 使用示例
usage_examples:
  # 基础使用 - 单Agent推荐
  yellow_text = "我对逆否命题的理解是：如果P→Q，那么¬Q→¬P"
  analysis = selector.analyze_understanding_quality(yellow_text)
  recommendation = selector.recommend_agents(analysis)

  # 高级使用 - 多Agent推荐
  quality_analysis = await selector.analyze_understanding_quality_advanced(
      yellow_text,
      context={"node_id": "node-123"}
  )
  multi_recommendations = await selector.recommend_multiple_agents(
      quality_analysis,
      max_recommendations=3
  )

  # 并行执行
  execution_result = await selector.process_agents_parallel(
      multi_recommendations,
      "path/to/canvas.canvas",
      "node-123",
      max_concurrent=5
  )

# 性能指标
performance_metrics:
  analysis_time: "< 1秒" - 分析响应时间
  recommendation_time: "< 0.5秒" - 推荐生成时间
  parallel_execution: "< 5秒" - 并行执行时间
  recommendation_accuracy: "> 85%" - 推荐准确率
  execution_success_rate: "> 95%" - 执行成功率
  concurrent_support: "最多20个Agent" - 并发支持

# 依赖关系
dependencies:
  - ConcurrentAgentProcessor - 并行Agent处理器
  - CanvasJSONOperator - Canvas JSON操作器
  - GLMInstancePool - GLM实例池
  - config/epic10-intelligent-parallel.yaml - Epic 10配置文件

# 错误处理
error_handling:
  EPIC10_1001: "Agent推荐失败"
  EPIC10_1002: "质量分析超时"
  EPIC10_1003: "并发执行超过限制"
  EPIC10_1004: "配置文件加载失败"
  EPIC10_1005: "无效的Agent类型"

# 向后兼容性
backward_compatibility:
  - ✅ 保留所有原有方法
  - ✅ 支持原有调用格式
  - ✅ 渐进式增强，不破坏现有功能
  - ✅ 可选的新功能，默认启用原行为

# 测试覆盖
test_coverage:
  - test_10.1_agent_selector.py - Story 10.1专用测试
  - 单元测试覆盖率 > 90%
  - 集成测试覆盖率 > 95%
  - 性能测试覆盖所有关键路径

# 更新日志
changelog:
  - "v10.1.0 (2025-01-27)":
    - ✅ 实现多Agent推荐功能
    - ✅ 添加四维质量分析
    - ✅ 支持并行执行(最多20个Agent)
    - ✅ 添加置信度评分系统
    - ✅ 实现Agent组合优化
    - ✅ 完全向后兼容

  - "v1.0.0 (原始版本)":
    - ✅ 基础Agent选择功能
    - ✅ 单Agent推荐
    - ✅ 理解质量分析

# 注意事项
notes:
  - 使用process_agents_parallel前确保ConcurrentAgentProcessor已初始化
  - 多Agent推荐会增加API使用量，请注意速率限制
  - 并发执行数量应根据系统资源动态调整
  - 配置文件路径相对于项目根目录