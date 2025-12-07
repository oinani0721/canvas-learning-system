"""Epic 10 测试配置和共享fixtures"""

import asyncio
import json
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock

import pytest

# 假设这些模块存在，实际使用时需要调整导入
# from canvas_utils import CanvasOrchestrator, ReviewBoardAgentSelector
# from canvas_utils import IntelligentParallelScheduler, AutoNodeGenerator


@pytest.fixture
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_canvas_data():
    """标准Canvas文件样本数据"""
    return {
        "nodes": [
            {
                "id": "node1",
                "type": "text",
                "text": "什么是逆否命题？",
                "x": 100,
                "y": 100,
                "width": 300,
                "height": 100,
                "color": "1"  # 红色
            },
            {
                "id": "node2",
                "type": "text",
                "text": "逆否命题的定义：如果命题P→Q，那么逆否命题是¬Q→¬P",
                "x": 450,
                "y": 100,
                "width": 300,
                "height": 100,
                "color": "6"  # 黄色，已填写
            },
            {
                "id": "node3",
                "type": "text",
                "text": "请用对比表的方式解释逆否命题和否命题的区别",
                "x": 100,
                "y": 250,
                "width": 300,
                "height": 100,
                "color": "6"  # 黄色，已填写
            },
            {
                "id": "node4",
                "type": "text",
                "text": "",  # 空的黄色节点
                "x": 450,
                "y": 250,
                "width": 300,
                "height": 100,
                "color": "6"  # 黄色，未填写
            }
        ],
        "edges": [
            {
                "id": "edge1",
                "fromNode": "node1",
                "toNode": "node2",
                "color": "#999999"
            }
        ]
    }


@pytest.fixture
def multiple_yellow_nodes_canvas():
    """包含多个黄色节点的Canvas数据"""
    nodes = []
    edges = []

    # 创建10个黄色节点
    for i in range(10):
        node = {
            "id": f"yellow_node_{i+1}",
            "type": "text",
            "text": f"这是我对概念{i+1}的理解：需要进一步澄清" if i % 2 == 0 else "",
            "x": 100 + (i % 3) * 350,
            "y": 100 + (i // 3) * 150,
            "width": 300,
            "height": 100,
            "color": "6"  # 黄色
        }
        nodes.append(node)

    # 添加一些连接
    for i in range(9):
        edge = {
            "id": f"edge_{i+1}",
            "fromNode": nodes[i]["id"],
            "toNode": nodes[i+1]["id"],
            "color": "#999999"
        }
        edges.append(edge)

    return {"nodes": nodes, "edges": edges}


@pytest.fixture
def agent_recommendation_result():
    """Agent推荐结果样本"""
    return {
        "analysis_id": "rec-1234567890abcdef",
        "node_id": "yellow_node_1",
        "understanding_quality": {
            "accuracy_score": 0.75,
            "completeness_score": 0.68,
            "clarity_score": 0.82,
            "overall_quality": 0.75
        },
        "recommended_agents": [
            {
                "agent_name": "clarification-path",
                "confidence_score": 0.92,
                "reasoning": "理解不完整，需要深度澄清",
                "priority": 1,
                "estimated_duration": "15-20秒"
            },
            {
                "agent_name": "comparison-table",
                "confidence_score": 0.78,
                "reasoning": "与相关概念对比有助于理解",
                "priority": 2,
                "estimated_duration": "10-15秒"
            },
            {
                "agent_name": "memory-anchor",
                "confidence_score": 0.65,
                "reasoning": "需要生动的类比帮助记忆",
                "priority": 3,
                "estimated_duration": "8-12秒"
            }
        ],
        "processing_strategy": {
            "execution_mode": "parallel",
            "max_concurrent": 3,
            "total_estimated_duration": "20-25秒"
        }
    }


@pytest.fixture
def scheduling_plan():
    """调度计划样本"""
    return {
        "plan_id": "schedule-abcdef1234567890",
        "canvas_path": "/path/to/canvas.canvas",
        "created_at": "2025-01-27T10:00:00Z",
        "optimization_goals": ["speed", "efficiency"],
        "task_groups": [
            {
                "group_id": "group-1111",
                "agent_type": "clarification-path",
                "nodes": ["yellow_node_1", "yellow_node_3", "yellow_node_5"],
                "estimated_duration": "45-60秒",
                "priority_score": 0.85,
                "dependencies": [],
                "resource_requirements": {
                    "concurrent_slots": 3,
                    "memory_estimate": "150MB",
                    "api_calls_estimate": 15
                }
            },
            {
                "group_id": "group-2222",
                "agent_type": "comparison-table",
                "nodes": ["yellow_node_2", "yellow_node_4"],
                "estimated_duration": "25-35秒",
                "priority_score": 0.72,
                "dependencies": ["group-1111"],
                "resource_requirements": {
                    "concurrent_slots": 2,
                    "memory_estimate": "100MB",
                    "api_calls_estimate": 8
                }
            },
            {
                "group_id": "group-3333",
                "agent_type": "memory-anchor",
                "nodes": ["yellow_node_6", "yellow_node_7", "yellow_node_8"],
                "estimated_duration": "30-40秒",
                "priority_score": 0.68,
                "dependencies": [],
                "resource_requirements": {
                    "concurrent_slots": 3,
                    "memory_estimate": "120MB",
                    "api_calls_estimate": 12
                }
            }
        ],
        "execution_strategy": {
            "max_concurrent_groups": 3,
            "total_estimated_duration": "90-120秒",
            "optimization_strategy": "dependency_aware",
            "fallback_strategy": "sequential_processing"
        },
        "user_confirmation_required": True
    }


@pytest.fixture
def execution_results():
    """执行结果样本"""
    return {
        "execution_id": "exec-1234567890abcdef",
        "plan_id": "schedule-abcdef1234567890",
        "status": "completed",
        "progress": {
            "percentage": 100.0,
            "current_task": "任务组3完成",
            "completed_tasks": 3,
            "total_tasks": 3,
            "estimated_remaining": "0秒"
        },
        "results": {
            "task_groups": [
                {
                    "group_id": "group-1111",
                    "status": "completed",
                    "nodes_processed": 3,
                    "agents_executed": 3,
                    "execution_time": 52.3,
                    "results": [
                        {
                            "agent_name": "clarification-path",
                            "success": True,
                            "result": {
                                "content": "深度澄清解释内容...",
                                "file_path": "/path/to/clarification-20250127.md"
                            },
                            "execution_time": 17.5,
                            "error": None
                        }
                    ]
                }
            ],
            "summary": {
                "total_nodes_processed": 8,
                "total_agents_executed": 15,
                "total_execution_time": 105.7,
                "success_rate": 100.0,
                "parallel_efficiency": 0.78
            }
        }
    }


@pytest.fixture
def temp_canvas_file(sample_canvas_data):
    """创建临时Canvas文件"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.canvas', delete=False) as f:
        json.dump(sample_canvas_data, f)
        temp_path = f.name

    yield temp_path

    # 清理
    os.unlink(temp_path)


@pytest.fixture
def mock_canvas_orchestrator():
    """模拟CanvasOrchestrator"""
    mock = AsyncMock()
    mock.read_canvas = AsyncMock()
    mock.write_canvas = AsyncMock()
    mock.find_node_by_id = AsyncMock()
    mock.get_filled_yellow_nodes = AsyncMock(return_value=["node1", "node2"])
    return mock


@pytest.fixture
def mock_agent_selector():
    """模拟ReviewBoardAgentSelector"""
    mock = AsyncMock()
    mock.analyze_understanding_quality = AsyncMock(return_value={
        "accuracy_score": 0.75,
        "completeness_score": 0.68,
        "clarity_score": 0.82,
        "overall_quality": 0.75
    })
    mock.recommend_multiple_agents = AsyncMock()
    mock.process_agents_parallel = AsyncMock()
    return mock


@pytest.fixture
def mock_scheduler():
    """模拟IntelligentParallelScheduler"""
    mock = AsyncMock()
    mock.analyze_canvas_nodes = AsyncMock()
    mock.create_scheduling_plan = AsyncMock()
    mock.execute_plan_with_progress = AsyncMock()
    return mock


@pytest.fixture
def mock_node_generator():
    """模拟AutoNodeGenerator"""
    mock = AsyncMock()
    mock.generate_nodes_from_results = AsyncMock()
    mock.create_explanation_node = MagicMock()
    mock.create_summary_node = MagicMock()
    mock.connect_nodes_intelligently = AsyncMock()
    return mock


@pytest.fixture
def epic10_config():
    """Epic 10配置数据"""
    return {
        "agent_selector": {
            "max_recommendations": 5,
            "default_confidence_threshold": 0.7,
            "max_agents_per_node": 20
        },
        "scheduler": {
            "default_max_concurrent_groups": 12,
            "similarity_threshold": 0.75,
            "max_execution_time": 600
        },
        "command_interface": {
            "defaults": {
                "max_concurrent": 12,
                "auto_confirm": False
            },
            "limits": {
                "max_nodes_per_command": 100,
                "max_execution_time": 600
            }
        },
        "node_generation": {
            "node_styles": {
                "explanation": {"width": 320, "height": 200},
                "summary": {"width": 300, "height": 180}
            },
            "layout": {
                "horizontal_offset": 50,
                "vertical_spacing": 120
            }
        }
    }


# 性能测试标记
pytest.mark.slow = pytest.mark.skipif(
    not os.getenv("RUN_SLOW_TESTS"),
    reason="Slow tests disabled. Set RUN_SLOW_TESTS=true to run."
)

# 集成测试标记
pytest.mark.integration = pytest.mark.integration

# 性能测试标记
pytest.mark.performance = pytest.mark.performance
