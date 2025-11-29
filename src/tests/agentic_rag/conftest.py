"""
Agentic RAG 测试共享 Fixtures

提供测试所需的模拟对象和配置。

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

# ============================================================
# Pytest 配置
# ============================================================

# Configure pytest-asyncio mode
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# ============================================================
# 模拟数据 Fixtures
# ============================================================

@pytest.fixture
def sample_search_results() -> List[Dict[str, Any]]:
    """标准化的搜索结果样例"""
    return [
        {
            "doc_id": "doc_001",
            "content": "逆否命题是原命题的等价形式，如果原命题是'如果p则q'，逆否命题是'如果非q则非p'",
            "score": 0.92,
            "metadata": {
                "source": "graphiti",
                "timestamp": datetime.now().isoformat(),
                "canvas_file": "离散数学.canvas",
                "concept": "逆否命题"
            }
        },
        {
            "doc_id": "doc_002",
            "content": "充分必要条件表示两个命题互为充分条件和必要条件",
            "score": 0.85,
            "metadata": {
                "source": "lancedb",
                "timestamp": datetime.now().isoformat(),
                "canvas_file": "离散数学.canvas",
                "concept": "充分必要条件"
            }
        },
        {
            "doc_id": "doc_003",
            "content": "反证法是通过假设结论不成立来导出矛盾的证明方法",
            "score": 0.78,
            "metadata": {
                "source": "temporal",
                "timestamp": datetime.now().isoformat(),
                "canvas_file": "离散数学.canvas",
                "concept": "反证法"
            }
        }
    ]


@pytest.fixture
def sample_weak_concepts() -> List[Dict[str, Any]]:
    """薄弱概念列表样例"""
    return [
        {
            "concept": "逆否命题",
            "stability": 1.2,
            "error_rate": 0.35,
            "weakness_score": 0.82,
            "last_review": datetime.now().isoformat(),
            "reps": 2
        },
        {
            "concept": "充分必要条件",
            "stability": 2.5,
            "error_rate": 0.25,
            "weakness_score": 0.65,
            "last_review": datetime.now().isoformat(),
            "reps": 3
        }
    ]


@pytest.fixture
def sample_graphiti_results() -> List[Dict[str, Any]]:
    """Graphiti 原始结果样例"""
    return [
        {
            "id": "node_001",
            "content": "逆否命题的定义",
            "score": 0.89,
            "created_at": datetime.now().isoformat(),
            "entity_type": "concept"
        },
        {
            "id": "node_002",
            "name": "命题逻辑",
            "score": 0.75,
            "created_at": datetime.now().isoformat(),
            "entity_type": "topic"
        }
    ]


@pytest.fixture
def sample_lancedb_results() -> List[Dict[str, Any]]:
    """LanceDB 原始结果样例"""
    return [
        {
            "doc_id": "lancedb_001",
            "content": "口语化解释-逆否命题",
            "_distance": 0.12,
            "canvas_file": "离散数学.canvas",
            "concept": "逆否命题"
        },
        {
            "doc_id": "lancedb_002",
            "content": "澄清路径-命题逻辑",
            "_distance": 0.25,
            "canvas_file": "离散数学.canvas",
            "concept": "命题逻辑"
        }
    ]


@pytest.fixture
def sample_fsrs_card() -> Dict[str, Any]:
    """FSRS 卡片样例"""
    return {
        "concept": "逆否命题",
        "canvas_file": "离散数学.canvas",
        "difficulty": 0.6,
        "stability": 1.2,
        "due": datetime.now().isoformat(),
        "state": "Learning",
        "last_review": datetime.now().isoformat(),
        "reps": 2
    }


# ============================================================
# Mock Fixtures
# ============================================================

@pytest.fixture
def mock_neo4j_client():
    """模拟 Neo4j 客户端"""
    mock = MagicMock()
    mock.health_check.return_value = True
    mock.run.return_value = []
    return mock


@pytest.fixture
def mock_lancedb_connection():
    """模拟 LanceDB 连接"""
    mock_db = MagicMock()
    mock_db.table_names.return_value = ["canvas_explanations", "canvas_concepts"]

    mock_table = MagicMock()
    mock_table.search.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.where.return_value = mock_table
    mock_table.to_list.return_value = []

    mock_db.open_table.return_value = mock_table
    mock_db.create_table.return_value = mock_table

    return mock_db


@pytest.fixture
def mock_sqlite_connection():
    """模拟 SQLite 连接用于 Temporal Memory"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = []
    mock_cursor.fetchone.return_value = None
    mock_cursor.lastrowid = 1
    mock_conn.execute.return_value = mock_cursor
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn


@pytest.fixture
def mock_embedder():
    """模拟嵌入器"""
    async def _embed(text: str) -> List[float]:
        # 返回固定维度的随机向量
        import random
        return [random.random() for _ in range(1536)]
    return _embed


# ============================================================
# 环境检测 Fixtures
# ============================================================

@pytest.fixture
def lancedb_available():
    """检测 LanceDB 是否可用"""
    import importlib.util
    return importlib.util.find_spec("lancedb") is not None


@pytest.fixture
def neo4j_available():
    """检测 Neo4j 是否可用"""
    import importlib.util
    return importlib.util.find_spec("neo4j") is not None


@pytest.fixture
def fsrs_available():
    """检测 FSRS 是否可用"""
    import importlib.util
    return importlib.util.find_spec("fsrs") is not None
