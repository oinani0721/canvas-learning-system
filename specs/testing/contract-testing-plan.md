# Contract Testing Implementation Plan

**Version**: 1.0.0
**Date**: 2025-11-19
**Status**: Planning Phase
**Epic**: BMad 4.0 Integration - Phase 2

---

## 📋 Overview

Contract Testing是BMad 4.0集成的核心组件，用于**消除API幻觉**，确保实际代码实现符合OpenAPI规范定义的契约。

### 目标

1. **防止API幻觉**：确保所有Canvas API调用都符合OpenAPI规范
2. **数据结构验证**：确保Node/Edge/Canvas数据符合JSON Schema定义
3. **持续集成**：在CI/CD流程中自动验证契约合规性

---

## 🔍 Canvas Learning System的特殊性

### 问题分析

Canvas Learning System与传统Web API服务器有本质区别：

| 维度 | 传统Web API | Canvas Learning System |
|------|-----------|----------------------|
| 架构模式 | RESTful API服务器 | **Python库** |
| 调用方式 | HTTP请求 | **Python函数调用** |
| 部署方式 | 独立服务 | **嵌入式库** |
| Contract Testing工具 | Schemathesis, Dredd, Pact | **不直接适用** |

### 核心挑战

1. **Schemathesis等工具要求HTTP端点** → Canvas是Python库，没有HTTP端点
2. **OpenAPI规范定义的是REST API** → 需要桥接到Python函数调用
3. **现有测试框架（pytest）不验证契约** → 需要自定义验证层

---

## 🚀 实施方案对比

### 方案A: 创建FastAPI Wrapper【推荐短期方案】

**描述**：创建一个轻量级FastAPI服务器，将canvas_utils.py的函数暴露为REST API

**优点**：
- ✅ 可以直接使用Schemathesis进行Contract Testing
- ✅ 自动生成的OpenAPI文档可以验证
- ✅ 未来可以作为Web服务使用

**缺点**：
- ❌ 增加额外的架构层
- ❌ 需要维护API wrapper代码
- ❌ 不是Canvas的核心用例（目前是本地工具）

**实施路径**：
1. 创建`src/api_server.py` - FastAPI应用
2. 为每个Layer 1-3函数创建对应的REST端点
3. 配置Schemathesis测试
4. 集成到CI/CD流程

**工作量估算**：2-3天

---

### 方案B: 自定义Python Contract Validator【推荐长期方案】

**描述**：创建一个Python装饰器/测试工具，验证函数签名和返回值是否符合OpenAPI规范

**优点**：
- ✅ 无需额外架构层
- ✅ 直接测试Python函数
- ✅ 可以深度集成pytest
- ✅ 符合Canvas的本地工具定位

**缺点**：
- ❌ 需要开发自定义验证工具
- ❌ 需要解析OpenAPI规范并映射到Python类型
- ❌ 初期开发成本较高

**实施路径**：
1. 创建`src/testing/contract_validator.py`
2. 实现OpenAPI → Python类型映射
3. 创建装饰器`@contract_verified(operation_id="readCanvas")`
4. 集成到现有pytest测试
5. CI/CD集成

**工作量估算**：4-5天

---

### 方案C: JSON Schema验证 + 文档【当前实施】

**描述**：使用JSON Schema验证数据结构，OpenAPI规范作为文档和设计契约

**优点**：
- ✅ 立即可实施
- ✅ 无需额外架构
- ✅ JSON Schema验证已经是标准工具（jsonschema库）
- ✅ 符合BMad"先文档后实施"的原则

**缺点**：
- ❌ 不验证函数签名
- ❌ 不验证HTTP语义
- ❌ 只验证数据结构，不验证API行为

**实施路径**：
1. ✅ 创建JSON Schema文件（已完成）
2. ⏳ 创建pytest fixtures验证Canvas数据符合schema
3. ⏳ 在devLoadAlwaysFiles中引用OpenAPI规范
4. ⏳ 文档化"如何验证你的代码符合契约"

**工作量估算**：0.5-1天

---

## 📌 推荐实施策略：分阶段渐进式

### Phase 2.3 (当前 - BMad集成修正)：方案C

**目标**：建立契约规范基础，数据结构验证

**交付物**：
- ✅ OpenAPI 3.0规范文件 (`specs/api/canvas-api.openapi.yml`)
- ✅ JSON Schema文件 (`specs/data/*.schema.json`)
- ⏳ pytest测试用例 - 验证Canvas数据符合schema
- ⏳ 文档 - Contract Testing使用指南

**代码示例**（pytest fixture）：

```python
# tests/conftest.py
import json
import jsonschema
from pathlib import Path

SCHEMA_DIR = Path(__file__).parent.parent / "specs" / "data"

@pytest.fixture
def canvas_file_schema():
    """加载Canvas文件JSON Schema"""
    with open(SCHEMA_DIR / "canvas-file.schema.json") as f:
        return json.load(f)

@pytest.fixture
def validate_canvas_data(canvas_file_schema):
    """验证Canvas数据符合schema的fixture"""
    def _validate(canvas_data: dict):
        jsonschema.validate(instance=canvas_data, schema=canvas_file_schema)
        return True
    return _validate

# tests/test_contract_validation.py
def test_read_canvas_returns_valid_schema(validate_canvas_data):
    """测试read_canvas返回的数据符合JSON Schema"""
    from src.canvas_utils import CanvasJSONOperator

    canvas_data = CanvasJSONOperator.read_canvas("test.canvas")

    # 验证数据符合契约
    assert validate_canvas_data(canvas_data)
```

---

### Phase 3 (Epic 15-16 - API服务化)：方案A

**前提条件**：Canvas需要暴露为Web API（如Obsidian插件后端）

**目标**：完整的Contract Testing with Schemathesis

**交付物**：
- FastAPI wrapper (`src/api_server.py`)
- Schemathesis配置文件
- CI/CD集成

---

### Phase 4 (未来优化)：方案B

**目标**：深度集成到Python开发流程

**交付物**：
- 自定义Contract Validator工具
- Python装饰器
- IDE集成（类型提示）

---

## 📚 Phase 2.3具体实施 - 当前Sprint

### 任务清单

- [x] 创建Contract Testing计划文档（本文档）
- [ ] 创建`tests/test_contract_validation.py`
- [ ] 添加JSON Schema验证fixtures到`tests/conftest.py`
- [ ] 为Layer 1 API添加contract validation测试
- [ ] 更新devLoadAlwaysFiles引用OpenAPI规范
- [ ] 创建`docs/guides/contract-testing-guide.md`使用指南

### 验收标准

1. ✅ 所有Canvas数据读写操作通过JSON Schema验证
2. ✅ pytest测试套件包含contract validation测试
3. ✅ 文档解释如何验证代码符合契约
4. ✅ devLoadAlwaysFiles自动加载OpenAPI规范

---

## 🔧 工具和依赖

### 当前阶段（Phase 2.3）

```bash
# JSON Schema验证
pip install jsonschema

# pytest集成
pip install pytest pytest-json-schema
```

### 未来阶段（Phase 3）

```bash
# API服务器
pip install fastapi uvicorn

# Contract Testing
pip install schemathesis
```

---

## 📖 参考资料

- **OpenAPI 3.0规范**：`specs/api/canvas-api.openapi.yml`
- **JSON Schemas**：`specs/data/*.schema.json`
- **BMad文档**：`docs/RESEARCH_REPORT_BMAD_INTEGRATION.md`
- **Schemathesis官方文档**：https://schemathesis.readthedocs.io/
- **JSON Schema官方网站**：https://json-schema.org/

---

## ✅ 下一步行动

**当前任务**：完成Phase 2.3 - JSON Schema验证

1. 创建`tests/test_contract_validation.py`
2. 添加pytest fixtures
3. 运行测试验证
4. 更新`docs/architecture/coding-standards.md`添加契约验证要求

**未来任务**（Epic 15+）：

- 考虑是否需要API服务化
- 如需要，实施方案A（FastAPI + Schemathesis）

---

**最后更新**：2025-11-19
**维护者**：Dev Agent (James)
**状态**：✅ 计划完成，准备实施
