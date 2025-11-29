"""
E2E 测试配置

提供 E2E 测试所需的 fixtures 和配置。

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
"""

import asyncio
import sys
from pathlib import Path

import pytest

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def reset_global_clients():
    """每个测试后重置全局客户端单例"""
    yield
    # 重置全局客户端
    try:
        import agentic_rag.nodes as nodes_module
        nodes_module._graphiti_client = None
        nodes_module._lancedb_client = None
        nodes_module._temporal_client = None
    except (ImportError, AttributeError):
        pass
