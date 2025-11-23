# Story GraphRAG.2: 本地模型集成与混合策略

---
**Status**: ❌ **Deprecated (已废弃)**
**Deprecated Date**: 2025-11-14
**Deprecated Reason**: 父Epic (EPIC-GraphRAG) 因过度设计问题已暂停
**Replacement**: EPIC-Neo4j-GDS-Integration
**Decision Record**: ADR-004, SCP-005
---

## ⚠️ Story状态：已废弃

**废弃日期**: 2025-11-14
**废弃原因**: 父Epic (EPIC-GraphRAG) 因过度设计问题已暂停

**替代方案**:
- Epic层面：EPIC-Neo4j-GDS-Integration (Neo4j GDS提供等效能力，无需本地模型)
- 功能实现：Neo4j GDS原生算法，无需LLM调用

**详情参见**:
- Sprint Change Proposal: SCP-005 (GraphRAG过度设计纠偏)
- Architecture Decision Record: ADR-004 (Do Not Integrate GraphRAG)

**历史价值**: 保留此Story作为本地模型集成参考案例

---

## 原始Story定义（以下内容为历史记录）

---

## Status
~~In Progress~~ ❌ Deprecated

## Story

**As a** Canvas学习系统,
**I want** 集成Qwen2.5-14B本地模型作为GraphRAG的默认LLM，并实现与OpenAI API的混合策略,
**so that** 系统能够在保证85%+提取质量的同时，将月度API成本从$570降低到$57（节省90%）。

## Acceptance Criteria

1. Qwen2.5-14B-Instruct成功通过Ollama集成
2. 本地模型推理延迟<8秒/节点（P95）
3. API降级触发条件明确：本地超时（>8秒）或失败时自动切换到gpt-4o-mini
4. 混合策略实现：90%请求使用本地模型，10%请求使用API（用于质量对比）
5. 提取质量≥85%（与GPT-4o基线对比，F1 Score）
6. 成本监控：月度API调用成本<$100（预算上限）
7. 降级率<5%（本地成功率≥95%）
8. 配置化LLM提供商（可通过配置文件切换本地/API/混合模式）

## Tasks / Subtasks

### Task 1: 安装和配置Qwen2.5-14B本地环境 (AC: 1, 2)

- [ ] **Subtask 1.1**: 安装Ollama和Qwen2.5模型
  - [ ] 安装Ollama（Linux/Mac: curl脚本，Windows: 官方安装包）
  - [ ] 拉取Qwen2.5-14B-Instruct模型：`ollama pull qwen2.5:14b-instruct`
  - [ ] 验证模型可用：`ollama run qwen2.5:14b-instruct "Hello"`
  - [ ] 测试模型响应速度（单次推理<5秒）

- [ ] **Subtask 1.2**: 配置Ollama服务
  - [ ] 配置Ollama环境变量：`OLLAMA_HOST=0.0.0.0:11434`
  - [ ] 配置Ollama模型存储路径（如需自定义）
  - [ ] 启动Ollama服务：`ollama serve`
  - [ ] 验证服务可访问：`curl http://localhost:11434/api/tags`

- [ ] **Subtask 1.3**: 硬件资源验证
  - [ ] 验证GPU可用性（NVIDIA GPU推荐，RTX 4090 / A100）
  - [ ] 验证VRAM≥24GB（Qwen2.5-14B需要）
  - [ ] 如无GPU，验证CPU性能（推理时间<15秒可接受）
  - [ ] 测试并发推理能力（同时处理3个请求）

- [ ] **Subtask 1.4**: 性能基准测试
  - [ ] 测试单次推理延迟（目标<5秒）
  - [ ] 测试批量推理延迟（10个请求，目标P95<8秒）
  - [ ] 测试内存使用（目标<16GB）
  - [ ] 测试并发推理（3个请求，目标<12秒）

### Task 2: 实现LangChain Ollama集成 (AC: 1, 2, 8)

- [ ] **Subtask 2.1**: 创建`GraphRAGLLMConfig`配置类
  - [ ] 定义配置字段：provider（local/api/hybrid）, model_name, temperature, timeout
  - [ ] 支持从环境变量读取配置（`GRAPHRAG_LLM_PROVIDER`）
  - [ ] 支持从配置文件读取（`config/graphrag_llm.json`）
  - [ ] 实现配置验证（provider必须为有效值）

- [ ] **Subtask 2.2**: 集成LangChain Ollama
  - [ ] ✅ 查询LangGraph Skills获取Ollama集成最佳实践
  - [ ] 实现`OllamaLLMProvider`类
  - [ ] 使用LangChain的`Ollama`类连接本地模型
  - [ ] 配置参数：model="qwen2.5:14b-instruct", temperature=0.2, timeout=8s
  - [ ] 实现重试机制（最多3次，指数退避）

- [ ] **Subtask 2.3**: 实现OpenAI API Provider
  - [ ] ✅ 查询Context7 FastAPI/LangChain文档获取API集成方法
  - [ ] 实现`OpenAILLMProvider`类
  - [ ] 使用LangChain的`ChatOpenAI`类连接gpt-4o-mini
  - [ ] 配置参数：model="gpt-4o-mini", temperature=0.2, timeout=5s
  - [ ] 添加API密钥管理（从环境变量`OPENAI_API_KEY`读取）
  - [ ] 实现速率限制（最多60 requests/min）

- [ ] **Subtask 2.4**: 创建统一LLM接口
  - [ ] 定义`BaseLLMProvider`抽象类
  - [ ] 实现`invoke(prompt: str) -> str`方法
  - [ ] 实现`ainvoke(prompt: str) -> str`异步方法
  - [ ] 实现超时和错误处理
  - [ ] 添加日志记录（记录每次调用的延迟和状态）

- [ ] **Subtask 2.5**: 单元测试
  - [ ] 测试Ollama连接成功
  - [ ] 测试OpenAI连接成功
  - [ ] 测试超时处理（mock慢响应）
  - [ ] 测试配置读取和验证

### Task 3: 实现混合LLM策略 (AC: 3, 4, 7)

- [ ] **Subtask 3.1**: 创建`HybridLLMProvider`类
  - [ ] 实现90%本地 + 10%API的流量分配算法
  - [ ] 使用随机数决定路由（random.random() < 0.9 → 本地）
  - [ ] 实现本地优先策略（先尝试本地，失败或超时则降级到API）
  - [ ] 记录路由决策（日志记录使用了本地还是API）

- [ ] **Subtask 3.2**: 实现API降级机制
  - [ ] 定义降级触发条件：
    - 本地推理超时（>8秒）
    - 本地推理失败（异常或连接错误）
    - 本地推理返回无效JSON
  - [ ] 降级时自动切换到OpenAI API
  - [ ] 记录降级事件（日志 + 指标）
  - [ ] 实现降级告警（降级率>5%时发送告警）

- [ ] **Subtask 3.3**: 实现成本跟踪
  - [ ] 创建`CostTracker`类
  - [ ] 跟踪本地调用次数（成本=$0）
  - [ ] 跟踪API调用次数和token消耗
  - [ ] 计算API成本（gpt-4o-mini: $0.15/1M input tokens, $0.60/1M output tokens）
  - [ ] 实现月度成本累计和重置（每月1日重置）
  - [ ] 提供成本查询接口：`get_monthly_cost() -> float`

- [ ] **Subtask 3.4**: 实现成本预算控制
  - [ ] 设置月度预算上限（$100）
  - [ ] 当成本接近预算（>$90）时发送告警
  - [ ] 当成本超过预算时停止API调用（强制使用本地模型）
  - [ ] 提供预算重置接口（管理员手动重置）

- [ ] **Subtask 3.5**: 实现降级率监控
  - [ ] 计算降级率（API调用次数 / 总调用次数）
  - [ ] 记录降级原因统计（超时 vs 失败 vs 无效输出）
  - [ ] 当降级率>5%时触发告警
  - [ ] 提供降级率查询接口：`get_degradation_rate() -> float`

- [ ] **Subtask 3.6**: 单元测试
  - [ ] 测试90/10流量分配准确性（1000次调用，误差<5%）
  - [ ] 测试本地超时自动降级
  - [ ] 测试本地失败自动降级
  - [ ] 测试成本累计准确性
  - [ ] 测试预算控制触发
  - [ ] 测试降级率计算

### Task 4: 实现质量对比验证 (AC: 5)

- [ ] **Subtask 4.1**: 创建质量评估数据集
  - [ ] 收集100个Canvas节点样本（涵盖不同主题和复杂度）
  - [ ] 人工标注Ground Truth（实体和关系）
  - [ ] 存储为JSON格式：`tests/fixtures/graphrag_quality_dataset.json`
  - [ ] 包含多样性：简单（30%）、中等（50%）、复杂（20%）

- [ ] **Subtask 4.2**: 实现质量评估指标
  - [ ] 实现实体提取评估：Precision, Recall, F1 Score
  - [ ] 实现关系提取评估：Precision, Recall, F1 Score
  - [ ] 实现整体质量分数计算（实体F1 * 0.6 + 关系F1 * 0.4）
  - [ ] 创建`QualityEvaluator`类封装评估逻辑

- [ ] **Subtask 4.3**: 对比Qwen2.5 vs GPT-4o质量
  - [ ] 使用100个样本分别调用Qwen2.5和GPT-4o
  - [ ] 计算两者的F1 Score
  - [ ] 生成对比报告：`quality_comparison_report.md`
  - [ ] 验证Qwen2.5 F1 ≥ 0.85 * GPT-4o F1（相对质量≥85%）

- [ ] **Subtask 4.4**: 分析质量差距原因
  - [ ] 识别Qwen2.5表现不佳的样本类型
  - [ ] 分析错误模式（漏提、误提、关系错误）
  - [ ] 提出Prompt优化建议（如需改进）
  - [ ] 记录质量对比结论到ADR-001文档

- [ ] **Subtask 4.5**: 实现持续质量监控
  - [ ] 每周自动运行质量评估（使用10%API流量的样本）
  - [ ] 记录质量趋势（F1 Score时间序列）
  - [ ] 当质量下降>10%时触发告警
  - [ ] 提供质量查询接口：`get_quality_metrics() -> Dict`

- [ ] **Subtask 4.6**: 单元测试
  - [ ] 测试质量评估计算准确性
  - [ ] 测试对比报告生成
  - [ ] 测试质量监控告警触发

### Task 5: 优化Prompt模板 (AC: 5)

- [ ] **Subtask 5.1**: 分析Qwen2.5的Prompt响应特性
  - [ ] 测试不同Prompt格式对质量的影响
  - [ ] 测试Few-shot示例数量的影响（3 vs 5 vs 10个）
  - [ ] 测试思维链（Chain-of-Thought）的效果
  - [ ] 测试中文 vs 英文Prompt的效果

- [ ] **Subtask 5.2**: 优化实体提取Prompt
  - [ ] 增加Few-shot示例数量（从3个增加到10个）
  - [ ] 添加思维链指导："首先识别关键概念，然后提取相关属性"
  - [ ] 明确输出格式约束（JSON Schema）
  - [ ] 添加负面示例（不应提取什么）

- [ ] **Subtask 5.3**: 优化关系提取Prompt
  - [ ] 增加关系类型定义和示例
  - [ ] 添加关系强度评分指导
  - [ ] 强调前后依赖关系的方向性
  - [ ] 添加相似概念识别指导

- [ ] **Subtask 5.4**: A/B测试优化效果
  - [ ] 使用100个样本对比优化前后的F1 Score
  - [ ] 验证优化后F1提升≥5%
  - [ ] 记录最优Prompt模板到代码库
  - [ ] 更新Story GraphRAG.1的Prompt模板

- [ ] **Subtask 5.5**: 单元测试
  - [ ] 测试优化后Prompt的输出格式
  - [ ] 测试Few-shot示例的正确性
  - [ ] 测试Prompt长度不超过4000 tokens

### Task 6: 集成测试和文档 (ALL AC)

- [ ] **Subtask 6.1**: 端到端集成测试
  - [ ] 测试本地模型调用成功
  - [ ] 测试API降级触发（mock本地超时）
  - [ ] 测试混合策略流量分配（90/10）
  - [ ] 测试成本跟踪准确性
  - [ ] 测试预算控制触发

- [ ] **Subtask 6.2**: 性能基准测试
  - [ ] 测试本地推理延迟P50, P95, P99（目标P95<8秒）
  - [ ] 测试API推理延迟P50, P95, P99（目标P95<5秒）
  - [ ] 测试并发推理性能（10个请求同时）
  - [ ] 生成性能基准报告：`performance_benchmark_report.md`

- [ ] **Subtask 6.3**: 降级率和成本验证
  - [ ] 运行1000次推理请求
  - [ ] 验证降级率<5%（本地成功率≥95%）
  - [ ] 验证月度成本<$100（基于10%API流量估算）
  - [ ] 验证成本节省≥90%（对比全用GPT-4o）

- [ ] **Subtask 6.4**: 创建用户文档
  - [ ] 编写`docs/user-guides/graphrag-local-model-setup.md`
  - [ ] 包含：Ollama安装、模型拉取、配置文件说明
  - [ ] 添加故障排查章节（Ollama连接失败、GPU不可用等）
  - [ ] 添加性能调优建议（GPU加速、批处理等）

- [ ] **Subtask 6.5**: 创建开发者文档
  - [ ] 编写`docs/architecture/graphrag-llm-provider-architecture.md`
  - [ ] 包含：LLM Provider设计、混合策略算法、成本跟踪机制
  - [ ] 添加扩展指南（如何添加新的LLM Provider）
  - [ ] 添加配置参考（所有配置选项说明）

- [ ] **Subtask 6.6**: 更新ADR-001文档
  - [ ] 记录本地模型 vs API的技术决策
  - [ ] 记录质量对比结果
  - [ ] 记录成本对比结果
  - [ ] 记录选择Qwen2.5-14B的原因

## Dev Notes

### 架构上下文

**本地模型优先架构** [Source: docs/epics/epic-graphrag-integration.md#解决方案]

本Story实现的核心架构决策：使用本地模型替代API，实现90%成本节省。

```
┌──────────────────────────────────────────────────────┐
│  混合LLM层（Hybrid LLM Provider）                     │
│  ┌─────────────────┐  ┌─────────────────┐            │
│  │ Qwen2.5-14B     │  │ GPT-4o-mini     │            │
│  │ (Ollama本地)    │  │ (API降级)       │            │
│  │ 成本: $0        │  │ 成本: $0.02/次  │            │
│  │ 质量: 85%       │  │ 质量: 90%       │            │
│  │ 延迟: 3-8秒     │  │ 延迟: 2-5秒     │            │
│  └─────────────────┘  └─────────────────┘            │
│  使用率: 90%              使用率: 10%                  │
│                                                       │
│  降级触发条件:                                        │
│  1. 本地超时 (>8秒)                                   │
│  2. 本地失败 (异常)                                   │
│  3. 本地返回无效JSON                                  │
└──────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────┐
│  成本跟踪与预算控制                                   │
│  月度预算: $100  |  月度成本: $57 (估算)             │
│  降级率: <5%     |  本地成功率: ≥95%                 │
│  质量指标: F1≥85% (相对GPT-4o)                        │
└──────────────────────────────────────────────────────┘
```

**四层记忆架构集成** [Source: docs/architecture/LANGGRAPH-MEMORY-INTEGRATION-DESIGN.md]

本地LLM将用于所有四层记忆系统的推理任务：
- Layer 1: LanceDB - 嵌入生成（local-embedding-model）
- Layer 2: Graphiti - 实体提取（Qwen2.5）
- Layer 3: Temporal - 行为分析（Qwen2.5）
- Layer 4: GraphRAG - 社区检测和摘要（Qwen2.5）

### 技术栈

**LangChain Ollama集成** [Source: LangGraph Skill - Ollama Integration Pattern]

```python
# ✅ Verified from LangGraph Skill - Ollama集成最佳实践
from langchain_community.llms import Ollama
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

class OllamaLLMProvider:
    def __init__(
        self,
        model: str = "qwen2.5:14b-instruct",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.2,
        timeout: int = 8
    ):
        # ✅ Verified from LangGraph Skill
        self.llm = Ollama(
            model=model,
            base_url=base_url,
            temperature=temperature,
            timeout=timeout,
            # 禁用流式输出（GraphRAG需要完整JSON）
            callback_manager=None
        )

    def invoke(self, prompt: str) -> str:
        """同步调用LLM"""
        try:
            response = self.llm.invoke(prompt)
            return response
        except TimeoutError:
            raise Exception("Ollama推理超时（>8秒）")
        except Exception as e:
            raise Exception(f"Ollama推理失败: {e}")

    async def ainvoke(self, prompt: str) -> str:
        """异步调用LLM"""
        # ✅ Verified from LangGraph Skill - 异步调用模式
        try:
            response = await self.llm.ainvoke(prompt)
            return response
        except Exception as e:
            raise Exception(f"Ollama异步推理失败: {e}")
```

**LangChain OpenAI集成** [Source: Context7 LangChain文档]

```python
# ✅ Verified from Context7 LangChain - ChatOpenAI集成
from langchain_openai import ChatOpenAI
import os

class OpenAILLMProvider:
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
        timeout: int = 5
    ):
        # ✅ Verified from Context7 LangChain文档
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            timeout=timeout,
            api_key=os.getenv("OPENAI_API_KEY"),
            max_retries=3,
            request_timeout=timeout
        )

    def invoke(self, prompt: str) -> str:
        """同步调用OpenAI API"""
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            raise Exception(f"OpenAI API调用失败: {e}")
```

**混合策略实现** [Source: Epic设计 + 最佳实践]

```python
import random
from typing import Optional
from enum import Enum

class LLMProviderType(Enum):
    LOCAL = "local"
    API = "api"
    HYBRID = "hybrid"

class HybridLLMProvider:
    def __init__(
        self,
        local_provider: OllamaLLMProvider,
        api_provider: OpenAILLMProvider,
        local_ratio: float = 0.9,  # 90%本地
        cost_tracker: Optional['CostTracker'] = None
    ):
        self.local = local_provider
        self.api = api_provider
        self.local_ratio = local_ratio
        self.cost_tracker = cost_tracker or CostTracker()

    def invoke(self, prompt: str) -> str:
        """混合策略调用"""
        # Step 1: 决定使用本地还是API（90/10分配）
        use_local = random.random() < self.local_ratio

        if use_local:
            try:
                # Step 2: 尝试本地推理
                response = self.local.invoke(prompt)
                self.cost_tracker.record_local_call()
                return response
            except Exception as e:
                # Step 3: 本地失败，降级到API
                print(f"[DEGRADATION] 本地推理失败，降级到API: {e}")
                self.cost_tracker.record_degradation("local_failure")
                return self._invoke_api(prompt)
        else:
            # Step 4: 直接使用API（10%流量，用于质量对比）
            return self._invoke_api(prompt)

    def _invoke_api(self, prompt: str) -> str:
        """调用API并记录成本"""
        response = self.api.invoke(prompt)

        # 估算token消耗（简化：response长度/4）
        input_tokens = len(prompt) / 4
        output_tokens = len(response) / 4

        self.cost_tracker.record_api_call(
            input_tokens=int(input_tokens),
            output_tokens=int(output_tokens)
        )

        return response
```

**成本跟踪实现**

```python
from datetime import datetime
from typing import Dict

class CostTracker:
    """成本跟踪器"""

    # gpt-4o-mini价格（2025年1月）
    INPUT_TOKEN_COST = 0.15 / 1_000_000   # $0.15/1M tokens
    OUTPUT_TOKEN_COST = 0.60 / 1_000_000  # $0.60/1M tokens

    def __init__(self, monthly_budget: float = 100.0):
        self.monthly_budget = monthly_budget
        self.local_calls = 0
        self.api_calls = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.degradations = {"local_failure": 0, "local_timeout": 0}
        self.month_start = datetime.now().replace(day=1)

    def record_local_call(self):
        """记录本地调用"""
        self.local_calls += 1

    def record_api_call(self, input_tokens: int, output_tokens: int):
        """记录API调用和token消耗"""
        self.api_calls += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

    def record_degradation(self, reason: str):
        """记录降级事件"""
        if reason in self.degradations:
            self.degradations[reason] += 1

    def get_monthly_cost(self) -> float:
        """计算月度成本"""
        input_cost = self.total_input_tokens * self.INPUT_TOKEN_COST
        output_cost = self.total_output_tokens * self.OUTPUT_TOKEN_COST
        return input_cost + output_cost

    def get_degradation_rate(self) -> float:
        """计算降级率"""
        total_calls = self.local_calls + self.api_calls
        if total_calls == 0:
            return 0.0
        # 降级 = API调用中因本地失败而触发的次数
        degradation_count = sum(self.degradations.values())
        return degradation_count / total_calls

    def is_budget_exceeded(self) -> bool:
        """检查是否超预算"""
        return self.get_monthly_cost() > self.monthly_budget

    def get_stats(self) -> Dict:
        """获取完整统计"""
        return {
            "local_calls": self.local_calls,
            "api_calls": self.api_calls,
            "total_calls": self.local_calls + self.api_calls,
            "degradation_rate": self.get_degradation_rate(),
            "monthly_cost": self.get_monthly_cost(),
            "monthly_budget": self.monthly_budget,
            "budget_utilization": self.get_monthly_cost() / self.monthly_budget,
            "degradations": self.degradations,
        }
```

### 配置文件设计

**配置文件位置**: `config/graphrag_llm.json`

```json
{
  "llm": {
    "provider": "hybrid",
    "local": {
      "model": "qwen2.5:14b-instruct",
      "base_url": "http://localhost:11434",
      "temperature": 0.2,
      "timeout": 8
    },
    "api": {
      "provider": "openai",
      "model": "gpt-4o-mini",
      "temperature": 0.2,
      "timeout": 5,
      "max_retries": 3
    },
    "hybrid": {
      "local_ratio": 0.9,
      "degradation_threshold": 0.05,
      "monthly_budget": 100.0
    }
  },
  "quality": {
    "min_f1_score": 0.85,
    "evaluation_interval": "weekly",
    "alert_on_quality_drop": true
  },
  "monitoring": {
    "log_level": "INFO",
    "cost_alert_threshold": 0.9,
    "degradation_alert_threshold": 0.05
  }
}
```

**环境变量配置** (`.env`文件)

```bash
# LLM Provider配置
GRAPHRAG_LLM_PROVIDER=hybrid  # local | api | hybrid
OLLAMA_HOST=http://localhost:11434
OPENAI_API_KEY=sk-...

# 成本控制
GRAPHRAG_MONTHLY_BUDGET=100.0
GRAPHRAG_LOCAL_RATIO=0.9

# 质量控制
GRAPHRAG_MIN_F1_SCORE=0.85
```

### 质量评估数据集设计

**数据集格式**: `tests/fixtures/graphrag_quality_dataset.json`

```json
{
  "version": "1.0",
  "created_at": "2025-01-14",
  "samples": [
    {
      "id": "sample_001",
      "canvas_content": "线性代数中，特征向量是矩阵的重要属性，用于主成分分析（PCA）",
      "ground_truth": {
        "entities": [
          {
            "name": "特征向量",
            "type": "Concept",
            "description": "矩阵的特殊向量"
          },
          {
            "name": "主成分分析",
            "type": "Skill",
            "description": "降维技术"
          },
          {
            "name": "线性代数",
            "type": "Topic",
            "description": "数学分支"
          }
        ],
        "relationships": [
          {
            "source": "特征向量",
            "target": "主成分分析",
            "type": "PREREQUISITE_OF"
          },
          {
            "source": "特征向量",
            "target": "线性代数",
            "type": "RELATED_TO"
          }
        ]
      },
      "difficulty": "medium",
      "category": "数学"
    }
  ]
}
```

### 性能要求

**延迟目标** [Source: Epic AC]

| LLM Provider | P50延迟 | P95延迟 | P99延迟 |
|-------------|---------|---------|---------|
| Qwen2.5本地 | <5秒    | <8秒    | <10秒   |
| GPT-4o-mini API | <3秒 | <5秒    | <7秒    |
| 混合策略    | <5秒    | <8秒    | <10秒   |

**质量目标** [Source: Epic AC]
- 实体提取F1 Score: ≥0.85 (相对GPT-4o)
- 关系提取F1 Score: ≥0.80 (相对GPT-4o)
- 整体质量分数: ≥0.85 (0.6 * 实体F1 + 0.4 * 关系F1)

**成本目标** [Source: Epic设计]
- 月度API成本: <$100
- 成本节省: ≥90% (对比全用GPT-4o)
- 降级率: <5%

### 依赖项

**Python依赖** [Source: requirements.txt]
```
# LLM集成
langchain-community>=0.0.20
langchain-openai>=0.0.5
ollama>=0.1.0

# 配置管理
pydantic>=2.0.0
python-dotenv>=1.0.0

# 质量评估
scikit-learn>=1.3.0  # Precision, Recall, F1计算
```

**系统依赖**
- **Ollama**: ≥0.1.0
  - 安装: `curl -fsSL https://ollama.com/install.sh | sh` (Linux/Mac)
  - Windows: 下载官方安装包
  - 拉取模型: `ollama pull qwen2.5:14b-instruct`

- **GPU（推荐）**:
  - NVIDIA GPU: RTX 4090 / A100 / H100
  - VRAM: ≥24GB
  - CUDA: ≥12.0
  - cuDNN: ≥8.9

- **CPU（备选）**:
  - 如无GPU，Qwen2.5可使用CPU推理（延迟<15秒可接受）
  - 推荐: AMD Ryzen 9 / Intel i9（16核以上）
  - 内存: ≥32GB

### 测试要求

**测试覆盖率目标** [Source: CLAUDE.md#测试规范]
- 单元测试覆盖率: ≥90%
- 集成测试覆盖关键流程: 100%

**关键测试用例**

1. **LLM Provider测试**
   - Ollama连接成功
   - OpenAI连接成功
   - 超时处理
   - 重试机制
   - 异步调用

2. **混合策略测试**
   - 90/10流量分配准确性（1000次调用，误差<5%）
   - 本地超时降级
   - 本地失败降级
   - 成本累计准确性
   - 预算控制触发

3. **质量评估测试**
   - F1 Score计算准确性
   - 质量对比报告生成
   - 质量监控告警触发

4. **性能测试**
   - 本地推理延迟P50/P95/P99
   - API推理延迟P50/P95/P99
   - 并发推理性能（10个请求）

### 故障排查

**问题1: Ollama连接失败**
- **症状**: `ConnectionError: Ollama服务不可达`
- **原因**: Ollama服务未启动或端口错误
- **解决**:
  1. 启动Ollama: `ollama serve`
  2. 检查端口: `curl http://localhost:11434/api/tags`
  3. 检查防火墙是否阻止11434端口
  4. 配置环境变量: `OLLAMA_HOST=http://localhost:11434`

**问题2: GPU不可用或VRAM不足**
- **症状**: `CUDA out of memory` 或推理速度慢
- **原因**: VRAM不足或CUDA未正确配置
- **解决**:
  1. 检查GPU: `nvidia-smi`
  2. 释放GPU内存（关闭其他GPU程序）
  3. 使用量化模型: `ollama pull qwen2.5:14b-instruct-q4`（4-bit量化，VRAM需求减半）
  4. 降级到CPU推理（设置`CUDA_VISIBLE_DEVICES=""`）

**问题3: 本地推理质量<85%**
- **原因**: Prompt模板不适合或Few-shot示例不足
- **解决**:
  1. 增加Few-shot示例数量（3→10个）
  2. 添加思维链提示词
  3. 调整temperature（0.2→0.1）
  4. 使用更大模型（qwen2.5:32b）

**问题4: 降级率>5%**
- **原因**: 本地推理超时频繁或GPU不稳定
- **解决**:
  1. 增加timeout（8秒→12秒）
  2. 检查GPU稳定性（温度、功耗）
  3. 优化Prompt长度（减少token消耗）
  4. 增加并发限制（避免GPU过载）

**问题5: API成本超预算**
- **原因**: 降级率过高或API流量分配错误
- **解决**:
  1. 检查降级原因统计（超时 vs 失败）
  2. 优化本地推理稳定性（减少降级）
  3. 降低API流量分配（10%→5%）
  4. 启用成本告警（成本>$90时停止API调用）

### 监控指标

**关键监控指标** [Source: Epic成功指标]

1. **LLM性能**
   - 本地推理延迟P50/P95/P99
   - API推理延迟P50/P95/P99
   - 降级率（<5%）
   - 本地成功率（≥95%）

2. **成本指标**
   - 月度API成本（<$100）
   - 预算利用率（<90%）
   - 本地/API调用比例（90/10）
   - 成本节省率（≥90%）

3. **质量指标**
   - 实体提取F1 Score（≥0.85）
   - 关系提取F1 Score（≥0.80）
   - 质量趋势（周对比）

4. **系统健康**
   - GPU利用率（<90%）
   - GPU温度（<80°C）
   - 内存使用（<16GB）
   - Ollama服务可用性（>99.5%）

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-01-14 | 1.0 | 初始Story创建，基于Epic GraphRAG集成和成本优化需求 | SM Agent (Bob) |

## Dev Agent Record

### Agent Model Used
claude-sonnet-4.5 (claude-sonnet-4-5-20250929)

### Debug Log References
待开发

### Completion Notes
待开发

### File List
待开发

## QA Results

### Review Date
待QA审查

### Reviewed By
Quinn (Senior Developer QA)

### Code Quality Assessment
待QA审查

### Compliance Check
待QA审查

### Final Status
In Progress - 等待开发开始
