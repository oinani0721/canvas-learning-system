"""
Contract Testing Configuration (pytest-based)

配置Schemathesis和pytest用于Canvas Learning System的Contract Testing。

测试目标:
- Canvas API (specs/api/canvas-api.openapi.yml)
- Agent API (specs/api/agent-api.openapi.yml)

Contract Testing原则:
1. API实现必须100%符合OpenAPI规范
2. 所有请求/响应必须通过JSON Schema验证
3. 错误响应必须符合标准格式
4. HTTP状态码必须符合规范定义

Dependencies:
- schemathesis: Contract testing framework
- pytest: Test runner
- hypothesis: Property-based testing (used by schemathesis)

Installation:
```bash
pip install schemathesis pytest hypothesis
```

Usage:
```bash
# 运行所有contract tests
pytest tests/contract/

# 运行Canvas API contract tests
pytest tests/contract/test_canvas_contracts.py

# 运行Agent API contract tests
pytest tests/contract/test_agent_contracts.py

# 生成详细报告
pytest tests/contract/ -v --tb=short

# 使用schemathesis CLI直接测试
schemathesis run specs/api/canvas-api.openapi.yml --base-url http://localhost:8000
```

References:
- Schemathesis文档: https://schemathesis.readthedocs.io/
- OpenAPI 3.0规范: https://swagger.io/specification/
- Task 6 (BMad Integration Plan): 创建Contract Testing测试套件
"""

import os
from pathlib import Path
import pytest
import schemathesis
from typing import Dict, Any

# ============================================================================
# Project Paths Configuration
# ============================================================================

# conftest.py is at: Canvas/src/tests/contract/conftest.py
# So we need 4 levels up to get to Canvas/
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
SPECS_DIR = PROJECT_ROOT / "specs" / "api"
CANVAS_API_SPEC = SPECS_DIR / "canvas-api.openapi.yml"
AGENT_API_SPEC = SPECS_DIR / "agent-api.openapi.yml"

# ============================================================================
# pytest Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def project_root() -> Path:
    """返回项目根目录路径"""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def canvas_api_spec_path() -> Path:
    """返回Canvas API OpenAPI规范文件路径"""
    if not CANVAS_API_SPEC.exists():
        pytest.skip(f"Canvas API spec not found: {CANVAS_API_SPEC}")
    return CANVAS_API_SPEC


@pytest.fixture(scope="session")
def agent_api_spec_path() -> Path:
    """返回Agent API OpenAPI规范文件路径"""
    if not AGENT_API_SPEC.exists():
        pytest.skip(f"Agent API spec not found: {AGENT_API_SPEC}")
    return AGENT_API_SPEC


@pytest.fixture(scope="session")
def canvas_api_schema(canvas_api_spec_path: Path) -> schemathesis.schemas.BaseSchema:
    """
    加载Canvas API OpenAPI规范为Schemathesis schema对象

    Returns:
        schemathesis.schemas.BaseSchema: Schemathesis schema对象
    """
    return schemathesis.openapi.from_path(str(canvas_api_spec_path))


@pytest.fixture(scope="session")
def agent_api_schema(agent_api_spec_path: Path) -> schemathesis.schemas.BaseSchema:
    """
    加载Agent API OpenAPI规范为Schemathesis schema对象

    Returns:
        schemathesis.schemas.BaseSchema: Schemathesis schema对象
    """
    return schemathesis.openapi.from_path(str(agent_api_spec_path))


@pytest.fixture(scope="session")
def mock_canvas_server_url() -> str:
    """
    返回Mock Canvas API服务器URL

    Note: 实际测试时需要启动Mock服务器或真实API服务器
    可以使用环境变量 CANVAS_API_BASE_URL 覆盖默认值
    """
    return os.environ.get("CANVAS_API_BASE_URL", "http://127.0.0.1:8000/api/v1")


@pytest.fixture(scope="session")
def mock_agent_server_url() -> str:
    """
    返回Mock Agent API服务器URL

    Note: 实际测试时需要启动Mock服务器或真实API服务器
    可以使用环境变量 AGENT_API_BASE_URL 覆盖默认值
    """
    return os.environ.get("AGENT_API_BASE_URL", "http://127.0.0.1:8001/api/v1")


@pytest.fixture
def sample_canvas_data() -> Dict[str, Any]:
    """
    返回示例Canvas数据（用于测试）

    Returns:
        Dict: Canvas JSON数据
    """
    return {
        "nodes": [
            {
                "id": "test-question-001",
                "type": "text",
                "x": 100,
                "y": 200,
                "width": 300,
                "height": 100,
                "color": "1",  # 红色（不理解）
                "text": "什么是逆否命题？"
            },
            {
                "id": "test-yellow-001",
                "type": "text",
                "x": 150,
                "y": 360,
                "width": 300,
                "height": 100,
                "color": "6",  # 黄色（个人理解）
                "text": "逆否命题是将原命题的条件和结论都否定后再交换位置"
            },
            {
                "id": "test-file-001",
                "type": "file",
                "x": 500,
                "y": 200,
                "width": 400,
                "height": 300,
                "color": "5",  # 蓝色（AI解释）
                "file": "docs/逆否命题-口语化解释-20250115.md"
            }
        ],
        "edges": [
            {
                "id": "test-edge-001",
                "fromNode": "test-question-001",
                "toNode": "test-yellow-001",
                "fromSide": "bottom",
                "toSide": "top"
            }
        ]
    }


@pytest.fixture
def sample_agent_invoke_request() -> Dict[str, Any]:
    """
    返回示例Agent调用请求数据（用于测试）

    Returns:
        Dict: Agent调用请求JSON
    """
    return {
        "input": {
            "canvas_path": "笔记库/离散数学/离散数学.canvas",
            "node_id": "test-yellow-001",
            "concept": "逆否命题",
            "user_understanding": "逆否命题是将原命题的条件和结论都否定后再交换位置"
        },
        "timeout": 60,
        "metadata": {
            "user_id": "test-user-001",
            "session_id": "test-session-001"
        }
    }


# ============================================================================
# Schemathesis Configuration
# ============================================================================

# 配置Schemathesis全局选项
# Note: schemathesis.experimental API在新版本中已移除，现在默认支持OpenAPI 3.1

# 配置Hypothesis（Schemathesis使用Hypothesis进行property-based testing）
# 参见: https://hypothesis.readthedocs.io/
from hypothesis import settings, Verbosity

# 设置Hypothesis配置文件
settings.register_profile(
    "contract_testing",
    max_examples=50,  # 每个测试生成50个随机样本
    verbosity=Verbosity.normal,
    deadline=10000,  # 10秒超时
    suppress_health_check=[  # 抑制某些健康检查（加快测试）
        # HealthCheck.too_slow,
        # HealthCheck.data_too_large,
    ]
)

# 激活contract_testing配置
settings.load_profile("contract_testing")


# ============================================================================
# Helper Functions
# ============================================================================

def validate_color_code(color: str) -> bool:
    """
    验证Canvas颜色代码是否合法

    Args:
        color: 颜色代码字符串

    Returns:
        bool: 是否合法
    """
    valid_colors = {"1", "2", "3", "5", "6"}
    return color in valid_colors


def validate_node_structure(node: Dict[str, Any]) -> bool:
    """
    验证Canvas节点结构是否合法

    Args:
        node: 节点数据字典

    Returns:
        bool: 是否合法
    """
    # 必需字段
    required_fields = {"id", "type", "x", "y", "width", "height"}
    if not all(field in node for field in required_fields):
        return False

    # 类型检查
    if node["type"] == "text" and "text" not in node:
        return False
    if node["type"] == "file" and "file" not in node:
        return False

    # 颜色代码检查（如果有）
    if "color" in node and not validate_color_code(node["color"]):
        return False

    return True


def validate_edge_structure(edge: Dict[str, Any]) -> bool:
    """
    验证Canvas边结构是否合法

    Args:
        edge: 边数据字典

    Returns:
        bool: 是否合法
    """
    # 必需字段
    required_fields = {"id", "fromNode", "toNode"}
    if not all(field in edge for field in required_fields):
        return False

    # Side字段检查（如果有）
    valid_sides = {"top", "right", "bottom", "left"}
    if "fromSide" in edge and edge["fromSide"] not in valid_sides:
        return False
    if "toSide" in edge and edge["toSide"] not in valid_sides:
        return False

    return True


# ============================================================================
# pytest Hooks
# ============================================================================

def pytest_configure(config):
    """pytest配置hook - 注册自定义marker"""
    config.addinivalue_line(
        "markers",
        "contract: Contract testing marker (OpenAPI specification validation)"
    )
    config.addinivalue_line(
        "markers",
        "canvas_api: Canvas API contract tests"
    )
    config.addinivalue_line(
        "markers",
        "agent_api: Agent API contract tests"
    )
    config.addinivalue_line(
        "markers",
        "slow: Slow running tests (may take >10 seconds)"
    )


def pytest_collection_modifyitems(config, items):
    """pytest collection hook - 自动添加marker到contract tests"""
    for item in items:
        # 为所有contract tests添加marker
        if "contract" in str(item.fspath):
            item.add_marker(pytest.mark.contract)

        # 根据文件名添加特定marker
        if "test_canvas_contracts" in str(item.fspath):
            item.add_marker(pytest.mark.canvas_api)
        elif "test_agent_contracts" in str(item.fspath):
            item.add_marker(pytest.mark.agent_api)
