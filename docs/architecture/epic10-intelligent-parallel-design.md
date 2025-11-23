---
document_type: "Architecture"
version: "1.0.0"
last_modified: "2025-11-19"
status: "approved"
iteration: 1

authors:
  - name: "Architect Agent"
    role: "Solution Architect"

reviewers:
  - name: "PO Agent"
    role: "Product Owner"
    approved: true

compatible_with:
  prd: "v1.0"
  api_spec: "v1.0"

api_spec_hash: "0dc1d3610d28bf99"

changes_from_previous:
  - "Initial Architecture with frontmatter metadata"

git:
  commit_sha: ""
  tag: ""

metadata:
  components_count: 0
  external_services: []
  technology_stack:
    frontend: []
    backend: ["Python 3.11", "asyncio"]
    database: []
    infrastructure: []
---

# Epic 10: 智能并行处理系统 - 整体设计文档

## 概述

Epic 10是Canvas学习系统的重大升级，旨在通过智能并行处理大幅提升学习效率。本系统包含4个核心组件，实现从Agent多推荐到自动节点生成的完整工作流。

## 系统架构

### 组件关系图

```
┌─────────────────────────────────────────────────────────────┐
│                    Epic 10 智能并行处理架构                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Story 10.1           Story 10.2           Story 10.3        │
│  ReviewBoardAgent    IntelligentParalle   IntelligentParallel  │
│  Selector多推荐      lScheduler调度器     Command Interface   │
│      │                      │                     │          │
│      ▼                      ▼                     ▼          │
│  ┌────────────┐      ┌────────────┐      ┌────────────┐     │
│  │ 多Agent    │      │ 智能分组   │      │ 用户命令    │     │
│  │ 推荐(1-5)  │ ---> │ 和调度     │ ---> │ 接口        │     │
│  └────────────┘      └────────────┘      └────────────┘     │
│                                            │                │
│                                            ▼                │
│                                      ┌────────────┐         │
│                                      │ 执行计划    │         │
│                                      │ 和进度跟踪  │         │
│                                      └────────────┘         │
│                                            │                │
│                                            ▼                │
│  Story 10.4                              ┌────────────┐     │
│  AutoNodeGenerator                       │ Canvas     │     │
│  自动节点生成   ───────────────────────> │ 文件更新    │     │
│  (蓝色+黄色)                             └────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈

- **核心框架**: Python 3.9+, asyncio
- **架构**: 3层Canvas操作架构
- **并发**: asyncio.Semaphore, ConcurrentAgentProcessor
- **AI服务**: 智谱API, GLMInstancePool
- **配置**: YAML配置文件
- **测试**: pytest, asyncio测试

## 组件详细设计

### 1. Story 10.1: ReviewBoardAgentSelector增强

#### 接口定义

```python
class ReviewBoardAgentSelector:
    """Agent选择器 - 支持多Agent推荐"""

    async def analyze_understanding_quality(
        self,
        node_text: str,
        context: Dict = None
    ) -> Dict:
        """分析理解质量"""
        return {
            "accuracy_score": float,      # 0-1
            "completeness_score": float,  # 0-1
            "clarity_score": float,       # 0-1
            "overall_quality": float       # 0-1
        }

    async def recommend_multiple_agents(
        self,
        quality_analysis: Dict,
        max_recommendations: int = 5
    ) -> Dict:
        """推荐多个Agent"""
        return {
            "analysis_id": "rec-{uuid16}",
            "node_id": str,
            "recommended_agents": [
                {
                    "agent_name": str,           # Agent类型
                    "confidence_score": float,    # 0-1
                    "reasoning": str,            # 推荐理由
                    "priority": int,             # 1-N
                    "estimated_duration": str,    # "15-20秒"
                    "suggested_follow_up": List[str]  # 后续建议
                }
            ],
            "processing_strategy": {
                "execution_mode": "parallel",     # parallel/sequential
                "max_concurrent": int,           # 1-20
                "total_estimated_duration": str  # 预估时间
            }
        }

    async def process_agents_parallel(
        self,
        agent_recommendations: Dict,
        canvas_path: str,
        node_id: str
    ) -> Dict:
        """并行处理推荐的多Agent"""
        return {
            "execution_id": "exec-{uuid16}",
            "results": [
                {
                    "agent_name": str,
                    "success": bool,
                    "result": Dict,
                    "execution_time": float,
                    "error": Optional[str]
                }
            ],
            "execution_summary": {
                "total_agents": int,
                "successful_agents": int,
                "total_time": float,
                "parallel_efficiency": float  # 实际时间/串行时间
            }
        }
```

#### 关键约束

- **响应时间**: 分析 < 1秒, 推荐 < 0.5秒
- **推荐数量**: 1-5个Agent
- **并发限制**: 单节点最多20个Agent
- **成功率**: > 95%

### 2. Story 10.2: IntelligentParallelScheduler调度器

#### 接口定义

```python
class IntelligentParallelScheduler:
    """智能并行调度器"""

    def __init__(self, config: Dict = None):
        self.max_concurrent_groups = config.get('max_concurrent_groups', 12)
        self.agent_selector = ReviewBoardAgentSelector()
        self.resource_monitor = ResourceMonitor()
        self.execution_engine = ConcurrentAgentProcessor()

    async def analyze_canvas_nodes(
        self,
        canvas_path: str,
        node_filter: Optional[Dict] = None
    ) -> Dict:
        """分析Canvas中的黄色节点"""
        return {
            "analysis_id": "analysis-{uuid16}",
            "canvas_path": str,
            "timestamp": str,
            "node_analysis": {
                "total_nodes": int,
                "yellow_nodes": int,
                "filled_nodes": int,      # 有内容的黄色节点
                "empty_nodes": int,       # 空的黄色节点
                "groupable_nodes": int    # 可以分组的节点
            },
            "nodes": [
                {
                    "node_id": str,
                    "position": Dict,      # {x, y, width, height}
                    "content_preview": str,
                    "quality_score": float,
                    "similar_nodes": List[str],  # 相似节点ID
                    "recommended_agents": List[str],  # 推荐Agent
                    "cluster_id": Optional[str]  # 所属聚类
                }
            ]
        }

    async def create_scheduling_plan(
        self,
        analysis_result: Dict,
        optimization_goals: List[str] = None
    ) -> Dict:
        """创建智能调度计划"""
        return {
            "plan_id": "schedule-{uuid16}",
            "canvas_path": str,
            "created_at": str,
            "optimization_goals": optimization_goals or ["speed", "efficiency"],
            "task_groups": [
                {
                    "group_id": "group-{uuid8}",
                    "agent_type": str,
                    "nodes": List[str],
                    "estimated_duration": str,
                    "priority_score": float,
                    "dependencies": List[str],  # 依赖的group_id
                    "resource_requirements": {
                        "concurrent_slots": int,
                        "memory_estimate": str,
                        "api_calls_estimate": int
                    }
                }
            ],
            "execution_strategy": {
                "max_concurrent_groups": int,
                "total_estimated_duration": str,
                "optimization_strategy": str,
                "fallback_strategy": str
            }
        }

    async def execute_plan_with_progress(
        self,
        plan: Dict,
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """执行计划并返回进度"""
        return {
            "execution_id": "exec-{uuid16}",
            "plan_id": str,
            "status": "running|completed|failed|cancelled",
            "progress": {
                "percentage": float,
                "current_task": str,
                "completed_tasks": int,
                "total_tasks": int,
                "estimated_remaining": str
            },
            "results": {
                "task_groups": [
                    {
                        "group_id": str,
                        "status": str,
                        "nodes_processed": int,
                        "agents_executed": int,
                        "execution_time": float,
                        "results": List[Dict]  # Agent执行结果
                    }
                ],
                "summary": {
                    "total_nodes_processed": int,
                    "total_agents_executed": int,
                    "total_execution_time": float,
                    "success_rate": float,
                    "parallel_efficiency": float
                }
            }
        }
```

#### 核心算法

```python
# 节点相似度计算
def calculate_node_similarity(
    node1: Dict,
    node2: Dict,
    weights: Dict = None
) -> float:
    """计算两个节点的相似度 (0-1)"""
    weights = weights or {
        "semantic": 0.4,      # 文本语义相似度
        "quality": 0.25,      # 质量评分相似度
        "position": 0.15,     # 位置关系相似度
        "agents": 0.20        # Agent推荐重叠度
    }

    # 计算各维度得分
    semantic_score = _calculate_semantic_similarity(
        node1["content_preview"],
        node2["content_preview"]
    )
    quality_score = 1 - abs(
        node1["quality_score"] - node2["quality_score"]
    )
    position_score = _calculate_position_similarity(
        node1["position"],
        node2["position"]
    )
    agents_score = _calculate_agent_overlap(
        node1["recommended_agents"],
        node2["recommended_agents"]
    )

    # 加权平均
    total_score = (
        semantic_score * weights["semantic"] +
        quality_score * weights["quality"] +
        position_score * weights["position"] +
        agents_score * weights["agents"]
    )

    return total_score

# 依赖分析
def analyze_task_dependencies(
    task_groups: List[Dict]
) -> Dict:
    """分析任务组间依赖关系"""
    dependencies = {}

    for group in task_groups:
        group_id = group["group_id"]
        deps = []

        # 基于Agent类型的依赖规则
        if group["agent_type"] == "scoring-agent":
            # 评分依赖其他Agent的结果
            deps.extend([
                g["group_id"] for g in task_groups
                if g["agent_type"] in [
                    "clarification-path",
                    "oral-explanation",
                    "comparison-table"
                ]
            ])

        # 基于节点位置的依赖
        # 如果节点A在节点B后面，可能需要先处理B
        for other_group in task_groups:
            if _has_positional_dependency(
                group["nodes"],
                other_group["nodes"]
            ):
                if other_group["group_id"] not in deps:
                    deps.append(other_group["group_id"])

        dependencies[group_id] = deps

    return dependencies
```

### 3. Story 10.3: IntelligentParallelCommand命令接口

#### 命令定义

```yaml
# .claude/commands/intelligent-parallel.md
---
name: intelligent-parallel
description: 智能并行处理Canvas学习系统中的黄色节点
version: "1.0"
usage: "*intelligent-parallel [options] [canvas_file]"
parameters:
  - name: canvas_file
    type: string
    required: false
    description: Canvas文件路径（默认使用当前Canvas）
    position: 0

  - name: max
    alias: m
    type: integer
    required: false
    default: 12
    range: [1, 20]
    description: 最大并发任务组数量（1-20，默认12）

  - name: auto
    alias: a
    type: boolean
    required: false
    default: false
    description: 自动执行，跳过用户确认

  - name: dry_run
    alias: d
    type: boolean
    required: false
    default: false
    description: 预览模式，只生成计划不执行

  - name: verbose
    alias: v
    type: boolean
    required: false
    default: false
    description: 显示详细执行信息
---
```

#### 处理流程

```python
async def handle_intelligent_parallel_command(
    params: Dict,
    canvas_orchestrator: CanvasOrchestrator
) -> Dict:
    """处理*intelligent-parallel命令"""

    # 1. 参数验证
    validated = validate_command_params(params)

    # 2. 创建调度器
    scheduler = IntelligentParallelScheduler({
        "max_concurrent_groups": validated["max"]
    })

    # 3. 分析节点
    analysis = await scheduler.analyze_canvas_nodes(
        validated["canvas_path"]
    )

    # 4. 创建计划
    plan = await scheduler.create_scheduling_plan(
        analysis,
        optimization_goals=["speed", "efficiency"]
    )

    # 5. 预览模式
    if validated["dry_run"]:
        return format_plan_preview(plan)

    # 6. 用户确认
    if not validated["auto"]:
        if not await request_user_confirmation(plan):
            return {"status": "cancelled", "message": "用户取消执行"}

    # 7. 执行计划
    progress_callback = create_progress_callback(validated["verbose"])
    results = await scheduler.execute_plan_with_progress(
        plan,
        progress_callback
    )

    # 8. 应用结果到Canvas
    await apply_results_to_canvas(
        validated["canvas_path"],
        results
    )

    return format_execution_results(results)
```

### 4. Story 10.4: AutoNodeGenerator自动节点生成

#### 接口定义

```python
class AutoNodeGenerator:
    """自动节点生成器"""

    def __init__(self):
        self.canvas_operator = CanvasJSONOperator()
        self.layout_algorithm = CanvasLayoutAlgorithm()

    async def generate_nodes_from_results(
        self,
        canvas_path: str,
        execution_results: Dict
    ) -> Dict:
        """从执行结果生成节点"""
        return {
            "generation_id": "gen-{uuid16}",
            "canvas_path": str,
            "generated_nodes": [
                {
                    "node_id": str,
                    "node_type": str,      # explanation/summary
                    "agent_source": str,   # 生成该节点的Agent
                    "reference_node": str, # 关联的原黄色节点
                    "position": Dict,
                    "content": str,
                    "connections": List[str]
                }
            ],
            "updated_connections": [
                {
                    "from_node": str,
                    "to_node": str,
                    "connection_type": str,
                    "style": Dict
                }
            ]
        }

    def create_explanation_node(
        self,
        agent_result: Dict,
        reference_node: Dict
    ) -> Dict:
        """创建蓝色解释节点"""
        return {
            "id": f"exp-{uuid8()}",
            "type": "text",
            "text": format_explanation_content(agent_result),
            "x": reference_node["x"] + reference_node["width"] + 50,
            "y": reference_node["y"],
            "width": 320,
            "height": 200,
            "color": "5",  # 蓝色
            "metadata": {
                "node_type": "ai_explanation",
                "agent_name": agent_result["agent_name"],
                "generated_from": reference_node["id"],
                "generation_time": datetime.now().isoformat(),
                "version": "1.0"
            }
        }

    def create_summary_node(
        self,
        explanation_node: Dict,
        reference_node: Dict
    ) -> Dict:
        """创建黄色总结节点"""
        return {
            "id": f"sum-{uuid8()}",
            "type": "text",
            "text": format_summary_prompt(explanation_node),
            "x": explanation_node["x"],
            "y": explanation_node["y"] + explanation_node["height"] + 30,
            "width": 300,
            "height": 180,
            "color": "6",  # 黄色
            "metadata": {
                "node_type": "user_summary",
                "generated_from": explanation_node["id"],
                "reference_node": reference_node["id"],
                "generation_time": datetime.now().isoformat(),
                "prompt_type": "summary_reflection",
                "version": "1.0"
            }
        }

    def connect_nodes_intelligently(
        self,
        canvas_data: Dict,
        new_nodes: List[Dict],
        connections: List[Dict]
    ) -> None:
        """智能连接节点"""
        for conn in connections:
            edge = {
                "id": f"edge-{uuid8()}",
                "fromNode": conn["from_node"],
                "toNode": conn["to_node"],
                "fromSide": "right",
                "toSide": "left",
                "color": conn["style"]["color"],
                "style": conn["style"]["style"],
                "label": conn["style"]["label"]
            }
            self.canvas_operator.add_edge(canvas_data, edge)
```

## 组件间接口规范

### 1. 数据交换格式

```yaml
# Agent推荐结果格式 (10.1 → 10.2)
agent_recommendation:
  analysis_id: str
  node_id: str
  recommended_agents: List[agent_info]
  processing_strategy:
    execution_mode: str
    max_concurrent: int
    total_estimated_duration: str

agent_info:
  agent_name: str
  confidence_score: float
  reasoning: str
  priority: int
  estimated_duration: str

# 调度计划格式 (10.2 → 10.3)
scheduling_plan:
  plan_id: str
  task_groups: List[task_group]
  execution_strategy: Dict

task_group:
  group_id: str
  agent_type: str
  nodes: List[str]
  estimated_duration: str
  priority_score: float
  dependencies: List[str]
  resource_requirements: Dict

# 执行结果格式 (10.2 → 10.4)
execution_results:
  execution_id: str
  plan_id: str
  status: str
  results:
    task_groups: List[task_group_result]
    summary: Dict

task_group_result:
  group_id: str
  agent_results: List[agent_result]
  nodes_processed: List[str]
  execution_time: float
```

### 2. 错误处理标准

```python
# 统一错误响应格式
class Epic10Error(Exception):
    """Epic 10 统一错误基类"""

    def __init__(
        self,
        error_code: str,
        message: str,
        source_story: str,
        technical_detail: str = None,
        recovery_suggestion: str = None,
        original_error: Exception = None
    ):
        self.error_code = error_code
        self.message = message
        self.source_story = source_story
        self.technical_detail = technical_detail
        self.recovery_suggestion = recovery_suggestion
        self.original_error = original_error
        super().__init__(self.message)

# 错误代码规范
ERROR_CODES = {
    # Story 10.1
    "EPIC10_1001": "Agent推荐失败",
    "EPIC10_1002": "质量分析超时",
    "EPIC10_1003": "并发执行超过限制",

    # Story 10.2
    "EPIC10_2001": "节点分析失败",
    "EPIC10_2002": "调度计划创建失败",
    "EPIC10_2003": "任务执行异常",

    # Story 10.3
    "EPIC10_3001": "命令参数无效",
    "EPIC10_3002": "Canvas文件不存在",
    "EPIC10_3003": "用户取消执行",

    # Story 10.4
    "EPIC10_4001": "节点生成失败",
    "EPIC10_4002": "布局优化失败",
    "EPIC10_4003": "Canvas更新失败"
}
```

### 3. 配置集成规范

```yaml
# config/epic10-intelligent-parallel.yaml
epic10:
  version: "1.0.0"
  created_date: "2025-01-27"

  # Story 10.1 - Agent选择器配置
  agent_selector:
    max_recommendations: 5
    default_confidence_threshold: 0.7
    enable_follow_up_suggestions: true

  # Story 10.2 - 调度器配置
  scheduler:
    analysis:
      similarity_threshold: 0.75
      max_cluster_size: 8
      min_cluster_size: 2
      enable_semantic_analysis: true

    scheduling:
      default_max_concurrent_groups: 12
      max_execution_time: 600  # 10分钟
      enable_dependency_analysis: true
      fallback_to_sequential: true

    resources:
      memory_limit_per_task: 200  # MB
      max_api_calls_per_batch: 50
      resource_check_interval: 5  # seconds

  # Story 10.3 - 命令接口配置
  command_interface:
    defaults:
      max_concurrent: 12
      auto_confirm: false
      dry_run_first: true
      verbose_output: false

    ui:
      show_progress_bar: true
      show_detailed_stats: true
      auto_save_results: true
      confirm_threshold: 5

    limits:
      max_nodes_per_command: 100
      max_execution_time: 600
      max_memory_usage: 1000  # MB

  # Story 10.4 - 节点生成配置
  node_generation:
    node_styles:
      explanation:
        color: "5"  # 蓝色
        width: 320
        height: 200
        font_size: 14

      summary:
        color: "6"  # 黄色
        width: 300
        height: 180
        font_size: 12

    layout:
      horizontal_offset: 50
      vertical_spacing: 120
      min_node_spacing: 100
      enable_grid_alignment: true
      grid_size: 50

    connections:
      auto_connect: true
      styles:
        explanation:
          color: "#4A90E2"
          style: "dashed"

        summary:
          color: "#F5A623"
          style: "solid"

        cross_reference:
          color: "#7ED321"
          style: "dotted"
```

## 并发层次定义

### 三级并发模型

```yaml
# 第一级：Agent级别并发 (Story 10.1)
agent_level:
  description: "单个节点的多个Agent并行处理"
  max_concurrent: 20
  use_case: "一个黄色节点需要多个Agent同时处理"
  example: "同时运行clarification-path、comparison-table、memory-anchor"

# 第二级：节点级别并发 (Story 10.2)
node_level:
  description: "多个节点的批处理并发"
  max_concurrent: 12
  use_case: "多个黄色节点分组并行处理"
  example: "3个节点组同时运行不同Agent"

# 第三级：任务级别并发 (Story 10.2/10.3)
task_level:
  description: "任务组的调度并发"
  max_concurrent: 5
  use_case: "有依赖关系的任务组按最优顺序执行"
  example: "5个任务组按依赖图并行执行"
```

### 并发限制矩阵

| 场景 | Agent限制 | 节点限制 | 任务限制 | 总并发 |
|------|-----------|----------|----------|--------|
| 单节点多Agent | 20 | 1 | 1 | 20 |
| 多节点批处理 | 5/节点 | 12 | 5 | 60 |
| 系统最大并发 | 20 | 12 | 5 | 100 |

## 性能指标

### 关键指标定义

```yaml
# 响应时间指标
response_time:
  agent_analysis: "< 1秒"
  node_clustering: "< 2秒"
  plan_generation: "< 1秒"
  command_parsing: "< 0.5秒"
  node_generation: "< 0.5秒/节点"

# 吞吐量指标
throughput:
  nodes_per_minute: "> 60个"
  agents_per_second: "> 10个"
  commands_per_hour: "> 30个"

# 资源使用指标
resource_usage:
  memory_per_agent: "< 100MB"
  memory_per_node: "< 200MB"
  cpu_usage: "< 80%"
  api_rate_limit: "< 90%"

# 质量指标
quality:
  recommendation_accuracy: "> 85%"
  clustering_precision: "> 90%"
  task_success_rate: "> 95%"
  user_satisfaction: "> 90%"
```

## 测试策略

### 测试文件命名规范

```
tests/
├── epic10/                               # Epic 10专用测试目录
│   ├── test_10.1_agent_selector.py      # Story 10.1测试
│   ├── test_10.2_scheduler.py           # Story 10.2测试
│   ├── test_10.3_command.py             # Story 10.3测试
│   ├── test_10.4_node_generation.py     # Story 10.4测试
│   ├── test_epic10_integration.py       # Epic 10集成测试
│   ├── test_epic10_performance.py       # 性能测试
│   └── test_epic10_e2e.py             # 端到端测试
```

### 测试覆盖率要求

- **单元测试**: 每个组件 > 90%
- **集成测试**: 组件间接口 > 95%
- **端到端测试**: 完整流程 > 90%
- **性能测试**: 所有关键路径 100%

## 部署和监控

### 部署检查清单

```yaml
deployment_checklist:
  pre_deployment:
    - [ ] 所有单元测试通过
    - [ ] 集成测试通过
    - [ ] 性能基准达标
    - [ ] 配置文件验证
    - [ ] 文档更新完成

  post_deployment:
    - [ ] 系统健康检查
    - [ ] 功能回归测试
    - [ ] 性能监控启用
    - [ ] 错误告警配置
    - [ ] 用户培训完成
```

### 监控指标

```yaml
monitoring:
  metrics:
    - epic10_agent_recommendations_total
    - epic10_scheduler_execution_time
    - epic10_command_usage_count
    - epic10_node_generation_rate

  alerts:
    - agent_recommendation_failure_rate > 5%
    - scheduler_queue_depth > 100
    - command_error_rate > 3%
    - node_generation_failure > 2%
```

## 版本规划

### v1.0.0 - 核心功能实现
- ✅ Story 10.1: ReviewBoardAgentSelector多推荐
- ✅ Story 10.2: IntelligentParallelScheduler调度
- ✅ Story 10.3: IntelligentParallel命令接口
- ✅ Story 10.4: AutoNodeGenerator节点生成

### v1.1.0 - 性能优化
- 智能缓存机制
- 自适应并发调整
- 批处理优化

### v1.2.0 - 功能增强
- 自定义Agent配置
- 高级依赖管理
- 可视化执行监控

## 总结

Epic 10通过4个紧密协作的组件，实现了Canvas学习系统的智能化并行处理升级。本设计文档定义了清晰的组件接口、数据交换格式、错误处理标准和配置规范，确保系统的高效、稳定和可维护性。

关键成功因素：
1. **清晰的组件职责分工**
2. **标准化的接口设计**
3. **统一的错误处理机制**
4. **完善的测试覆盖**
5. **灵活的配置管理**

通过遵循本设计文档，可以确保Epic 10的成功实施和长期维护。