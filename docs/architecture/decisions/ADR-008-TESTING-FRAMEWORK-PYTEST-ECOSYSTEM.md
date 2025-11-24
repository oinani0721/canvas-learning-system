# ADR-008: 测试框架选型 - pytest 生态系统

## 状态

**已接受** | 2025-11-23

## 背景

Canvas Learning System 包含多个技术层级：

1. **Python 后端** - FastAPI + LangGraph Agents
2. **TypeScript 前端** - React 组件
3. **数据存储** - SQLite (Checkpointer + Cache)
4. **API 契约** - OpenAPI 规范

需要统一的测试策略来确保：
- 代码质量和覆盖率
- API 契约一致性
- Agent 行为正确性
- CI/CD 效率

### 测试规模预估

| 阶段 | 测试数量 | 串行耗时 |
|------|----------|----------|
| 当前 (Epic 12) | ~400 | ~4分钟 |
| Epic 14 完成 | ~800 | ~8分钟 |
| 全部完成 | ~1000+ | ~12分钟 |

## 决策

**采用 pytest 生态系统作为核心测试框架，配合 Schemathesis 契约测试和 pytest-xdist 并行执行**

### 核心框架

| 层级 | 框架 | 用途 |
|------|------|------|
| Python 测试 | pytest | 单元测试、集成测试、Agent测试 |
| 契约测试 | Schemathesis | OpenAPI 合规验证 |
| 并行执行 | pytest-xdist | CI 加速 |
| 前端测试 | Vitest + RTL | React 组件测试 |

### 依赖配置

```toml
# pyproject.toml
[project.optional-dependencies]
test = [
    # 核心
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.1",
    "pytest-mock>=3.12",
    "pytest-timeout>=2.2",

    # 并行执行
    "pytest-xdist>=3.5",

    # API测试
    "httpx>=0.26",
    "schemathesis>=3.25",

    # 工具
    "factory-boy>=3.3",
    "faker>=22.0",
]
```

### pytest 配置

```ini
# pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
addopts =
    -v
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    -n auto
    --dist loadfile
    --timeout=30
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    contract: marks tests as contract tests
```

### 覆盖率配置

```toml
# pyproject.toml
[tool.coverage.run]
source = ["src"]
omit = [
    "tests/*",
    "*/__pycache__/*",
    "*/migrations/*",
]
branch = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
fail_under = 80
show_missing = true
```

## 实现细节

### 1. 目录结构

```
tests/
├── conftest.py                 # 全局Fixtures
├── unit/                       # 单元测试 (60%)
│   ├── test_cache.py
│   ├── test_fusion.py
│   └── test_reranking.py
├── integration/                # 集成测试 (15%)
│   ├── test_api_analysis.py
│   ├── test_api_review.py
│   └── test_memory_pipeline.py
├── agents/                     # Agent测试 (20%)
│   ├── test_scoring_agent.py
│   ├── test_decomposition_agent.py
│   └── test_state_graph.py
├── contract/                   # 契约测试 (5%)
│   ├── conftest.py
│   └── test_openapi_compliance.py
└── fixtures/                   # 测试数据
    ├── canvas_samples/
    ├── mock_responses/
    └── factories.py
```

### 2. 并行友好的 Fixtures

```python
# tests/conftest.py
import pytest
from pathlib import Path

@pytest.fixture(scope="session")
def worker_data_dir(tmp_path_factory, worker_id):
    """每个Worker独立的数据目录"""
    if worker_id == "master":
        return tmp_path_factory.mktemp("data")
    return tmp_path_factory.mktemp(f"data_{worker_id}")

@pytest.fixture
def checkpointer(worker_data_dir):
    """并行安全的Checkpointer"""
    from langgraph.checkpoint.sqlite import SqliteSaver
    db_path = worker_data_dir / "checkpoints.db"
    return SqliteSaver.from_conn_string(str(db_path))

@pytest.fixture
def cache(worker_data_dir):
    """并行安全的Cache"""
    from src.cache import TieredCache, CacheConfig
    config = CacheConfig()
    config.SQLITE_CONFIG["db_path"] = str(worker_data_dir / "cache.db")
    return TieredCache(config)

@pytest.fixture
def test_canvas(tmp_path):
    """每个测试独立的Canvas文件"""
    canvas_file = tmp_path / "test.canvas"
    canvas_file.write_text('{"nodes": [], "edges": []}')
    return canvas_file

@pytest.fixture
def mock_llm(mocker):
    """Mock LLM客户端"""
    mock = mocker.patch("src.agents.llm_client")
    mock.return_value.ainvoke.return_value = "Mocked LLM response"
    return mock
```

### 3. 契约测试配置

```python
# tests/contract/conftest.py
import pytest
import schemathesis
from pathlib import Path

# 加载OpenAPI规范
SPEC_PATH = Path(__file__).parent.parent.parent / "specs" / "api" / "canvas-api.openapi.yml"
schema = schemathesis.from_path(str(SPEC_PATH))

# 安装兼容性修复
schemathesis.fixups.install()

@pytest.fixture(scope="session")
def api_schema():
    return schema
```

```python
# tests/contract/test_openapi_compliance.py
import pytest
import schemathesis
from .conftest import schema

@schema.parametrize()
def test_api_contract(case):
    """所有端点契约测试"""
    response = case.call_and_validate()

@schema.parametrize(endpoint="/api/v1/analysis/node")
def test_node_analysis_contract(case):
    """节点分析端点深度测试"""
    response = case.call_and_validate()

    if response.status_code == 200:
        data = response.json()
        assert "task_id" in data
        assert "status" in data

@schema.parametrize(endpoint="/api/v1/review/schedule")
def test_review_schedule_contract(case):
    """复习调度端点测试"""
    response = case.call_and_validate()

    if response.status_code == 200:
        data = response.json()
        assert "review_items" in data
```

### 4. Agent 测试示例

```python
# tests/agents/test_scoring_agent.py
import pytest
from langgraph.checkpoint.memory import MemorySaver

@pytest.fixture
def scoring_graph(mock_llm):
    """测试用评分Agent图"""
    from src.agents.scoring import create_scoring_graph

    checkpointer = MemorySaver()
    return create_scoring_graph(checkpointer=checkpointer)

@pytest.mark.asyncio
async def test_scoring_agent_basic(scoring_graph, mock_llm):
    """测试基础评分流程"""
    config = {"configurable": {"thread_id": "test-scoring-1"}}

    result = await scoring_graph.ainvoke(
        {
            "node_content": "逆否命题是...",
            "user_explanation": "如果不是B，那么不是A",
        },
        config
    )

    assert "scores" in result
    assert all(dim in result["scores"] for dim in ["accuracy", "imagery", "completeness", "originality"])
    assert all(0 <= score <= 10 for score in result["scores"].values())

@pytest.mark.asyncio
async def test_scoring_agent_state_persistence(scoring_graph):
    """测试状态持久化"""
    config = {"configurable": {"thread_id": "test-persistence-1"}}

    # 第一次调用
    result1 = await scoring_graph.ainvoke({"node_content": "概念A"}, config)

    # 第二次调用（应该能看到历史）
    result2 = await scoring_graph.ainvoke({"node_content": "概念B"}, config)

    assert result2.get("previous_scores") is not None
```

### 5. API 集成测试示例

```python
# tests/integration/test_api_analysis.py
import pytest
from httpx import AsyncClient

@pytest.fixture
async def async_client(app):
    """异步HTTP客户端"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
@pytest.mark.integration
async def test_node_analysis_flow(async_client, test_canvas):
    """测试完整的节点分析流程"""
    # 1. 创建分析任务
    response = await async_client.post(
        "/api/v1/analysis/node",
        json={
            "canvas_path": str(test_canvas),
            "node_id": "node-1",
            "analysis_type": "deep"
        }
    )
    assert response.status_code == 200
    task_id = response.json()["task_id"]

    # 2. 查询任务状态
    response = await async_client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["status"] in ["pending", "running", "completed"]

@pytest.mark.asyncio
@pytest.mark.integration
async def test_batch_analysis(async_client, test_canvas):
    """测试批量分析"""
    response = await async_client.post(
        "/api/v1/analysis/batch",
        json={
            "canvas_path": str(test_canvas),
            "node_ids": ["node-1", "node-2", "node-3"],
            "parallel": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["total_nodes"] == 3
```

## CI 配置

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -e ".[test]"

      - name: Run tests (parallel)
        run: |
          pytest -n auto --dist loadfile --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: coverage.xml

  contract-test:
    runs-on: ubuntu-latest
    needs: test

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -e ".[test]"

      - name: Run contract tests
        run: |
          pytest tests/contract/ --hypothesis-max-examples=100
```

### 本地开发命令

```bash
# 运行所有测试（并行）
pytest

# 运行特定类型
pytest tests/unit/
pytest tests/integration/ -m integration
pytest tests/contract/ -m contract

# 跳过慢测试
pytest -m "not slow"

# 单Worker调试
pytest -n 0 tests/unit/test_cache.py

# 覆盖率报告
pytest --cov-report=html && open htmlcov/index.html

# 契约测试（详细）
schemathesis run specs/api/canvas-api.openapi.yml --hypothesis-max-examples=50
```

## 理由

### 为什么选择 pytest

1. **语法简洁** - 比 unittest 更Pythonic
2. **Fixture系统** - 强大的依赖注入
3. **插件生态** - 丰富的扩展能力
4. **异步支持** - pytest-asyncio 完美支持 FastAPI/LangGraph
5. **社区活跃** - 文档完善，问题容易解决

### 为什么使用 Schemathesis

1. **已有OpenAPI** - `canvas-api.openapi.yml` 已定义完整
2. **自动发现边界问题** - 无需手动编写边界测试
3. **防止回归** - API变更时自动检测Breaking Changes
4. **配置简单** - 几行代码覆盖数百场景

### 为什么使用 pytest-xdist

1. **测试增长快** - Epic 14完成后将有1000+测试
2. **CI时间关键** - 并行可将10分钟缩短到2-3分钟
3. **提前准备** - 现在设计并行友好的Fixtures
4. **本地可选** - 开发时可以用 `-n 0` 禁用

### 为什么 80% 覆盖率

1. **平衡质量与速度** - 100%覆盖率ROI低
2. **关注关键路径** - Agent逻辑、API端点、融合算法
3. **允许例外** - 错误处理、日志等可略低
4. **渐进提升** - 从80%开始，逐步提高

## 影响

### 正面影响

1. **开发效率** - 快速反馈循环
2. **代码质量** - 高覆盖率保障
3. **API稳定性** - 契约测试防止Breaking Changes
4. **CI速度** - 并行执行节省时间

### 负面影响

1. **学习成本** - 团队需熟悉pytest生态
2. **Fixture复杂度** - 并行需要额外设计
3. **契约测试时间** - Schemathesis生成大量用例

### 缓解措施

1. **文档完善** - 提供测试编写指南
2. **模板提供** - conftest.py 预设常用Fixtures
3. **CI分层** - 快速检查 vs 完整测试

## 实现计划

| 阶段 | 内容 | Story |
|------|------|-------|
| Phase 1 | pytest基础配置 + conftest.py | Story 12.15 |
| Phase 2 | 契约测试集成 | Story 12.15 |
| Phase 3 | 并行执行优化 | Story 12.15 |
| Phase 4 | CI/CD集成 | Story 12.15 |

## 参考资料

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-xdist](https://pytest-xdist.readthedocs.io/)
- [Schemathesis](https://schemathesis.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

---

**作者**: Winston (Architect Agent)
**审核**: 待定
**批准**: 待定
