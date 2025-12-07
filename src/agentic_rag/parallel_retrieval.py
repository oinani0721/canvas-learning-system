"""
并行检索实现 (LangGraph Send模式)

Story 12.6: 实现fan_out_retrieval函数，使用LangGraph Send模式
并行dispatch到Graphiti和LanceDB检索节点。

✅ Verified from LangGraph Skill:
- Pattern: Parallel Processing with Send
- Send(node_name, payload) for parallel dispatch
- RetryPolicy for connection error handling

Acceptance Criteria:
- AC 1: fan_out_retrieval()正确dispatch
- AC 2: 并行查询延迟 < 100ms (P95)
- AC 3: RetryPolicy处理异常
- AC 4: 结果正确汇聚到fuse_results节点

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# ✅ Verified from Context7 LangGraph docs - langgraph.types.Send
from langgraph.types import RetryPolicy, Send

from .state import CanvasRAGState

# ========================================
# Parallel Retrieval Configuration
# ========================================

@dataclass
class ParallelRetrievalConfig:
    """并行检索配置"""
    num_results: int = 10
    graphiti_enabled: bool = True
    lancedb_enabled: bool = True
    timeout_ms: float = 5000.0


# Default retry policy for retrieval nodes
# ✅ Verified from LangGraph Skill - Adding Retry Policies
DEFAULT_RETRY_POLICY = RetryPolicy(
    retry_on=(ConnectionError, TimeoutError),
    max_attempts=3,
    backoff_factor=2.0,
    initial_interval=1.0,
    max_interval=10.0
)


# ========================================
# Fan-Out Retrieval Function
# ========================================

def fan_out_retrieval(state: CanvasRAGState) -> List[Send]:
    """
    并行dispatch到Graphiti和LanceDB检索节点

    ✅ Verified from LangGraph Skill - Pattern: Parallel Processing with Send

    使用LangGraph Send模式实现并行检索:
    1. 从state提取query和canvas_path
    2. 构造Send对象列表，发送到不同检索节点
    3. LangGraph自动并行执行所有Send目标

    Args:
        state: 当前CanvasRAGState，包含messages和配置

    Returns:
        List[Send]: 包含两个Send对象，分别指向graphiti和lancedb节点

    Example:
        >>> state = {"messages": [{"content": "什么是逆否命题?"}]}
        >>> sends = fan_out_retrieval(state)
        >>> len(sends)
        2
        >>> sends[0].node
        'retrieve_graphiti'
    """
    # 从messages提取查询
    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        if isinstance(last_msg, dict):
            query = last_msg.get("content", "")
        else:
            query = getattr(last_msg, "content", "")
    else:
        query = state.get("original_query", "")

    # 获取canvas文件路径
    canvas_path = state.get("canvas_file", "")

    # 获取检索数量配置
    num_results = 10  # Default, can be overridden by runtime config

    # ✅ Verified from LangGraph Skill - Send for parallel processing
    # Send(node_name, payload) dispatches to node with given payload
    return [
        Send("retrieve_graphiti", {
            "query": query,
            "canvas_path": canvas_path,
            "num_results": num_results,
            "source": "graphiti"
        }),
        Send("retrieve_lancedb", {
            "query": query,
            "canvas_path": canvas_path,
            "num_results": num_results,
            "source": "lancedb"
        })
    ]


def fan_out_retrieval_selective(
    state: CanvasRAGState,
    config: Optional[ParallelRetrievalConfig] = None
) -> List[Send]:
    """
    可配置的并行检索dispatch

    允许选择性启用Graphiti/LanceDB检索，
    用于测试或特定场景。

    Args:
        state: 当前状态
        config: 检索配置，None时使用默认配置

    Returns:
        List[Send]: 根据配置的Send对象列表
    """
    if config is None:
        config = ParallelRetrievalConfig()

    # 从messages提取查询
    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        if isinstance(last_msg, dict):
            query = last_msg.get("content", "")
        else:
            query = getattr(last_msg, "content", "")
    else:
        query = state.get("original_query", "")

    canvas_path = state.get("canvas_file", "")

    sends = []

    if config.graphiti_enabled:
        sends.append(Send("retrieve_graphiti", {
            "query": query,
            "canvas_path": canvas_path,
            "num_results": config.num_results,
            "source": "graphiti"
        }))

    if config.lancedb_enabled:
        sends.append(Send("retrieve_lancedb", {
            "query": query,
            "canvas_path": canvas_path,
            "num_results": config.num_results,
            "source": "lancedb"
        }))

    return sends


# ========================================
# Retry Policy Factory
# ========================================

def create_retrieval_retry_policy(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    initial_interval: float = 1.0
) -> RetryPolicy:
    """
    创建检索节点的RetryPolicy

    ✅ Verified from LangGraph Skill - Adding Retry Policies

    配置指数退避重试策略:
    - 第1次失败 → 等待initial_interval秒 → 重试
    - 第2次失败 → 等待initial_interval * backoff_factor秒 → 重试
    - 第3次失败 → 抛出最终异常

    Args:
        max_attempts: 最大重试次数 (默认3)
        backoff_factor: 退避倍数 (默认2.0)
        initial_interval: 初始等待时间秒 (默认1.0)

    Returns:
        RetryPolicy: 配置好的重试策略
    """
    return RetryPolicy(
        retry_on=(ConnectionError, TimeoutError, OSError),
        max_attempts=max_attempts,
        backoff_factor=backoff_factor,
        initial_interval=initial_interval,
        max_interval=30.0  # 最大等待30秒
    )


# ========================================
# Result Aggregation Helpers
# ========================================

def aggregate_parallel_results(
    graphiti_update: Dict[str, Any],
    lancedb_update: Dict[str, Any]
) -> Dict[str, Any]:
    """
    汇聚并行检索结果

    LangGraph会自动合并并行节点的返回值到state，
    此函数用于手动汇聚场景或测试。

    Args:
        graphiti_update: Graphiti节点返回的state更新
        lancedb_update: LanceDB节点返回的state更新

    Returns:
        合并后的state更新字典
    """
    return {
        "graphiti_results": graphiti_update.get("graphiti_results", []),
        "lancedb_results": lancedb_update.get("lancedb_results", []),
        "graphiti_latency_ms": graphiti_update.get("graphiti_latency_ms", 0.0),
        "lancedb_latency_ms": lancedb_update.get("lancedb_latency_ms", 0.0)
    }


def calculate_parallel_latency(
    graphiti_latency_ms: float,
    lancedb_latency_ms: float,
    overhead_ms: float = 5.0
) -> Dict[str, float]:
    """
    计算并行检索的总延迟

    并行执行的总延迟 ≈ max(各节点延迟) + 并发开销

    Args:
        graphiti_latency_ms: Graphiti检索延迟
        lancedb_latency_ms: LanceDB检索延迟
        overhead_ms: 并发调度开销

    Returns:
        延迟统计字典
    """
    parallel_latency = max(graphiti_latency_ms, lancedb_latency_ms) + overhead_ms
    serial_latency = graphiti_latency_ms + lancedb_latency_ms
    speedup = serial_latency / parallel_latency if parallel_latency > 0 else 1.0

    return {
        "parallel_latency_ms": parallel_latency,
        "serial_latency_ms": serial_latency,
        "speedup_ratio": speedup,
        "graphiti_latency_ms": graphiti_latency_ms,
        "lancedb_latency_ms": lancedb_latency_ms
    }
