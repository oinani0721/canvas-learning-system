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

# Epic 11: 数据模型设计

**文档类型**: Data Model Design Document
**Epic**: Epic 11 - FastAPI后端基础架构搭建
**版本**: v1.0
**创建日期**: 2025-11-13
**负责人**: PM Agent (John) + Architect Agent (Morgan)
**状态**: 已批准

---

## 📋 目录

1. [数据模型概览](#-数据模型概览)
2. [Pydantic模型设计](#-pydantic模型设计)
3. [Canvas模型](#-canvas模型)
4. [Agent模型](#-agent模型)
5. [Review模型](#-review模型)
6. [通用模型](#-通用模型)
7. [数据验证规则](#-数据验证规则)
8. [模型关系图](#-模型关系图)

---

## 🌐 数据模型概览

### 设计原则

#### 1. 基于Pydantic (v2.5+)
使用Pydantic进行数据验证和序列化，利用Python类型提示。

#### 2. 请求/响应分离
明确区分请求模型（Request）和响应模型（Response），避免混淆。

#### 3. 基础模型复用
定义基础模型（Base），通过继承减少重复代码。

#### 4. 严格验证
使用Field定义验证规则（长度、范围、格式等）。

#### 5. 清晰的类型提示
所有字段使用明确的类型（str, int, Optional等）。

### 模型层次结构

```
CommonModels (通用模型)
    ├── SuccessResponse
    ├── ErrorResponse
    └── PaginationMeta

CanvasModels (Canvas相关模型)
    ├── NodeBase → NodeCreate, NodeUpdate, NodeRead
    ├── EdgeBase → EdgeCreate, EdgeUpdate, EdgeRead
    └── CanvasBase → CanvasRead

AgentModels (Agent相关模型)
    ├── AgentRequestBase → BasicDecomposeRequest, DeepDecomposeRequest, ...
    └── AgentResponseBase → DecomposeResponse, ScoreResponse, ...

ReviewModels (检验白板相关模型)
    ├── ReviewGenerateRequest
    ├── ReviewProgressResponse
    └── ReviewSyncRequest
```

---

## 📐 Pydantic模型设计

### 基础配置

所有模型使用统一的配置基类：

```python
# 来源: Context7 /websites/fastapi_tiangolo
# Topic: Pydantic models configuration
from pydantic import BaseModel, ConfigDict

class BaseModelConfig(BaseModel):
    """所有模型的基础配置"""

    model_config = ConfigDict(
        # 从ORM对象加载数据
        from_attributes=True,
        # 使用枚举值而非枚举对象
        use_enum_values=True,
        # 严格模式
        strict=False,
        # JSON schema额外信息
        json_schema_extra={
            "examples": []
        }
    )
```

### 字段验证

使用Field定义验证规则：

```python
# 来源: Context7 /websites/fastapi_tiangolo
# Topic: Field validation
from pydantic import Field, validator
from typing import Optional

class NodeCreate(BaseModel):
    text: str = Field(
        ...,  # 必需字段
        description="节点文本内容",
        min_length=1,
        max_length=10000,
        examples=["逆否命题的定义是..."]
    )

    color: Optional[str] = Field(
        None,
        description="节点颜色代码（1-6）",
        pattern=r"^[1-6]$"
    )

    x: int = Field(
        ...,
        description="X坐标",
        ge=0,  # 大于等于0
        le=10000  # 小于等于10000
    )

    @validator('color')
    def validate_color(cls, v):
        """自定义颜色验证"""
        if v and v not in ['1', '2', '3', '4', '5', '6']:
            raise ValueError('Color must be between 1 and 6')
        return v
```

---

## 📊 Canvas模型

### 文件位置
`app/models/canvas.py`

### 模型定义

#### 1. NodeBase（节点基础模型）

```python
# app/models/canvas.py
from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum

class NodeType(str, Enum):
    """节点类型枚举"""
    TEXT = "text"
    FILE = "file"
    LINK = "link"

class NodeColor(str, Enum):
    """节点颜色枚举"""
    RED = "1"      # 不理解
    GREEN = "2"    # 完全理解
    PURPLE = "3"   # 似懂非懂
    BLUE = "5"     # AI解释
    YELLOW = "6"   # 个人理解

class NodeBase(BaseModel):
    """节点基础模型"""

    type: NodeType = Field(
        ...,
        description="节点类型"
    )

    # 文本节点字段
    text: Optional[str] = Field(
        None,
        description="节点文本内容（text类型必需）",
        min_length=1,
        max_length=50000
    )

    # 文件节点字段
    file: Optional[str] = Field(
        None,
        description="文件路径（file类型必需）",
        max_length=500
    )

    # 链接节点字段
    url: Optional[str] = Field(
        None,
        description="URL地址（link类型必需）",
        max_length=2000
    )

    # 通用字段
    color: Optional[NodeColor] = Field(
        None,
        description="节点颜色代码"
    )

    x: int = Field(
        ...,
        description="X坐标",
        ge=0,
        le=100000
    )

    y: int = Field(
        ...,
        description="Y坐标",
        ge=0,
        le=100000
    )

    width: int = Field(
        400,
        description="节点宽度",
        ge=100,
        le=2000
    )

    height: int = Field(
        200,
        description="节点高度",
        ge=50,
        le=2000
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "type": "text",
                "text": "逆否命题的定义",
                "color": "1",
                "x": 100,
                "y": 200,
                "width": 400,
                "height": 200
            }]
        }
    )

    @model_validator(mode='after')
    def validate_node_type_fields(self):
        """验证节点类型对应的字段必须存在"""
        if self.type == NodeType.TEXT and not self.text:
            raise ValueError("text field is required for text type node")
        elif self.type == NodeType.FILE and not self.file:
            raise ValueError("file field is required for file type node")
        elif self.type == NodeType.LINK and not self.url:
            raise ValueError("url field is required for link type node")
        return self
```

#### 2. NodeCreate（创建节点请求）

```python
class NodeCreate(NodeBase):
    """创建节点请求模型"""

    canvas_name: str = Field(
        ...,
        description="Canvas文件名（不含.canvas后缀）",
        min_length=1,
        max_length=200,
        pattern=r"^[^./\\]+$"  # 防止路径遍历
    )

    @validator('canvas_name')
    def validate_canvas_name(cls, v):
        """验证Canvas名称安全性"""
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError('Invalid canvas name: path traversal detected')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "canvas_name": "离散数学",
                "type": "text",
                "text": "我的理解：逆否命题是...",
                "color": "6",
                "x": 100,
                "y": 450,
                "width": 400,
                "height": 200
            }]
        }
    )
```

#### 3. NodeUpdate（更新节点请求）

```python
class NodeUpdate(BaseModel):
    """更新节点请求模型（所有字段可选）"""

    text: Optional[str] = Field(
        None,
        description="更新节点文本",
        min_length=1,
        max_length=50000
    )

    color: Optional[NodeColor] = Field(
        None,
        description="更新节点颜色"
    )

    x: Optional[int] = Field(
        None,
        description="更新X坐标",
        ge=0
    )

    y: Optional[int] = Field(
        None,
        description="更新Y坐标",
        ge=0
    )

    width: Optional[int] = Field(
        None,
        description="更新宽度",
        ge=100,
        le=2000
    )

    height: Optional[int] = Field(
        None,
        description="更新高度",
        ge=50,
        le=2000
    )

    @model_validator(mode='after')
    def validate_at_least_one_field(self):
        """至少提供一个更新字段"""
        if not any([self.text, self.color, self.x, self.y, self.width, self.height]):
            raise ValueError('At least one field must be provided for update')
        return self
```

#### 4. NodeRead（节点响应）

```python
from datetime import datetime

class NodeRead(NodeBase):
    """节点响应模型"""

    id: str = Field(
        ...,
        description="节点ID"
    )

    created_at: Optional[datetime] = Field(
        None,
        description="创建时间"
    )

    updated_at: Optional[datetime] = Field(
        None,
        description="更新时间"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [{
                "id": "node_123",
                "type": "text",
                "text": "逆否命题的定义",
                "color": "1",
                "x": 100,
                "y": 200,
                "width": 400,
                "height": 200,
                "created_at": "2025-11-13T10:30:00Z"
            }]
        }
    )
```

#### 5. EdgeBase（边基础模型）

```python
class EdgeSide(str, Enum):
    """边的连接侧"""
    TOP = "top"
    RIGHT = "right"
    BOTTOM = "bottom"
    LEFT = "left"

class EdgeBase(BaseModel):
    """边基础模型"""

    fromNode: str = Field(
        ...,
        description="起始节点ID",
        min_length=1
    )

    toNode: str = Field(
        ...,
        description="目标节点ID",
        min_length=1
    )

    fromSide: Optional[EdgeSide] = Field(
        None,
        description="起始侧"
    )

    toSide: Optional[EdgeSide] = Field(
        None,
        description="目标侧"
    )

    label: Optional[str] = Field(
        None,
        description="边标签",
        max_length=200
    )
```

#### 6. EdgeCreate（创建边请求）

```python
class EdgeCreate(EdgeBase):
    """创建边请求模型"""

    canvas_name: str = Field(
        ...,
        description="Canvas文件名",
        min_length=1,
        max_length=200
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "canvas_name": "离散数学",
                "fromNode": "node_1",
                "toNode": "node_2",
                "fromSide": "right",
                "toSide": "left",
                "label": "理解输出"
            }]
        }
    )
```

#### 7. EdgeRead（边响应）

```python
class EdgeRead(EdgeBase):
    """边响应模型"""

    id: str = Field(
        ...,
        description="边ID"
    )
```

#### 8. CanvasRead（Canvas响应）

```python
class CanvasRead(BaseModel):
    """Canvas响应模型"""

    name: str = Field(
        ...,
        description="Canvas文件名"
    )

    nodes: list[NodeRead] = Field(
        default_factory=list,
        description="节点列表"
    )

    edges: list[EdgeRead] = Field(
        default_factory=list,
        description="边列表"
    )

    meta: Optional[dict] = Field(
        None,
        description="元数据"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "name": "离散数学",
                "nodes": [
                    {
                        "id": "node_1",
                        "type": "text",
                        "text": "逆否命题",
                        "color": "1",
                        "x": 100,
                        "y": 200,
                        "width": 400,
                        "height": 200
                    }
                ],
                "edges": [
                    {
                        "id": "edge_1",
                        "fromNode": "node_1",
                        "toNode": "node_2",
                        "fromSide": "right",
                        "toSide": "left"
                    }
                ],
                "meta": {
                    "node_count": 1,
                    "edge_count": 1
                }
            }]
        }
    )
```

---

## 🤖 Agent模型

### 文件位置
`app/models/agent.py`

### 模型定义

#### 1. AgentRequestBase（Agent请求基础）

```python
class AgentRequestBase(BaseModel):
    """Agent请求基础模型"""

    canvas_name: str = Field(
        ...,
        description="Canvas文件名",
        min_length=1,
        max_length=200
    )

    concept: str = Field(
        ...,
        description="需要处理的概念",
        min_length=1,
        max_length=500
    )

    context: Optional[str] = Field(
        None,
        description="学习上下文",
        max_length=2000
    )
```

#### 2. BasicDecomposeRequest（基础拆解请求）

```python
class BasicDecomposeRequest(AgentRequestBase):
    """基础拆解Agent请求"""

    node_id: str = Field(
        ...,
        description="红色节点ID（完全不懂的节点）"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "canvas_name": "离散数学",
                "node_id": "node_1",
                "concept": "逆否命题",
                "context": "在学习命题逻辑时遇到的概念"
            }]
        }
    )
```

#### 3. DeepDecomposeRequest（深度拆解请求）

```python
class DeepDecomposeRequest(AgentRequestBase):
    """深度拆解Agent请求"""

    node_id: str = Field(
        ...,
        description="紫色节点ID（似懂非懂的节点）"
    )

    understanding: str = Field(
        ...,
        description="用户已有的理解",
        min_length=1,
        max_length=5000
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{
                "canvas_name": "离散数学",
                "node_id": "node_2",
                "concept": "逆否命题",
                "understanding": "我的理解：逆否命题就是把原命题的条件和结论都取反...",
                "context": "已经学习了基础定义，但对应用场景不清楚"
            }]
        }
    )
```

#### 4. ScoreRequest（评分请求）

```python
class ScoreRequest(AgentRequestBase):
    """评分Agent请求"""

    node_id: str = Field(
        ...,
        description="黄色节点ID（个人理解输出节点）"
    )

    understanding: str = Field(
        ...,
        description="用户的理解内容",
        min_length=1,
        max_length=10000
    )
```

#### 5. ExplanationRequest（解释请求）

```python
class ExplanationType(str, Enum):
    """解释类型"""
    ORAL = "oral"                    # 口语化解释
    CLARIFICATION = "clarification"  # 澄清路径
    COMPARISON = "comparison"        # 对比表
    MEMORY = "memory"                # 记忆锚点
    FOUR_LEVEL = "four_level"        # 四层次解释
    EXAMPLE = "example"              # 例题教学

class ExplanationRequest(AgentRequestBase):
    """解释Agent请求（通用）"""

    type: ExplanationType = Field(
        ...,
        description="解释类型"
    )

    target_node_id: Optional[str] = Field(
        None,
        description="目标节点ID（在此节点旁创建file节点）"
    )

    # 对比表专用
    concept2: Optional[str] = Field(
        None,
        description="第二个概念（对比表专用）"
    )
```

#### 6. DecomposeResponse（拆解响应）

```python
class QuestionItem(BaseModel):
    """问题项"""

    type: str = Field(
        ...,
        description="问题类型（定义型/实例型/对比型/探索型等）"
    )

    question: str = Field(
        ...,
        description="问题内容"
    )

    guide: Optional[str] = Field(
        None,
        description="引导说明"
    )

    purpose: Optional[str] = Field(
        None,
        description="问题目的"
    )

class DecomposeResponse(BaseModel):
    """拆解Agent响应"""

    questions: list[QuestionItem] = Field(
        ...,
        description="生成的问题列表"
    )

    nodes_created: list[str] = Field(
        default_factory=list,
        description="创建的节点ID列表"
    )

    message: str = Field(
        ...,
        description="操作结果消息"
    )
```

#### 7. ScoreResponse（评分响应）

```python
class ScoreDimensions(BaseModel):
    """评分维度"""

    accuracy: int = Field(
        ...,
        description="准确性评分（0-25）",
        ge=0,
        le=25
    )

    imagery: int = Field(
        ...,
        description="具象性评分（0-25）",
        ge=0,
        le=25
    )

    completeness: int = Field(
        ...,
        description="完整性评分（0-25）",
        ge=0,
        le=25
    )

    originality: int = Field(
        ...,
        description="原创性评分（0-25）",
        ge=0,
        le=25
    )

    total: int = Field(
        ...,
        description="总分（0-100）",
        ge=0,
        le=100
    )

class ScoreFeedback(BaseModel):
    """评分反馈"""

    accuracy: str = Field(..., description="准确性反馈")
    imagery: str = Field(..., description="具象性反馈")
    completeness: str = Field(..., description="完整性反馈")
    originality: str = Field(..., description="原创性反馈")

class ScoreResponse(BaseModel):
    """评分Agent响应"""

    scores: ScoreDimensions = Field(
        ...,
        description="4维评分"
    )

    level: str = Field(
        ...,
        description="理解等级（红色/紫色/绿色）"
    )

    feedback: ScoreFeedback = Field(
        ...,
        description="评分反馈"
    )

    recommendations: list[str] = Field(
        default_factory=list,
        description="推荐的Agent列表"
    )

    color_updated: bool = Field(
        ...,
        description="颜色是否更新"
    )

    new_color: Optional[NodeColor] = Field(
        None,
        description="新颜色代码"
    )

    message: str = Field(
        ...,
        description="操作结果消息"
    )
```

#### 8. ExplanationResponse（解释响应）

```python
class ExplanationResponse(BaseModel):
    """解释Agent响应"""

    explanation_file: str = Field(
        ...,
        description="生成的解释文档路径"
    )

    file_node_id: str = Field(
        ...,
        description="创建的file节点ID"
    )

    word_count: int = Field(
        ...,
        description="文档字数",
        ge=0
    )

    sections: list[str] = Field(
        default_factory=list,
        description="文档章节列表"
    )

    message: str = Field(
        ...,
        description="操作结果消息"
    )
```

---

## 📝 Review模型

### 文件位置
`app/models/review.py`

### 模型定义

#### 1. ReviewGenerateRequest（生成检验白板请求）

```python
class ReviewOptions(BaseModel):
    """检验白板生成选项"""

    auto_generate_questions: bool = Field(
        True,
        description="自动生成检验问题"
    )

    cluster_by_topic: bool = Field(
        True,
        description="按主题聚类"
    )

class ReviewGenerateRequest(BaseModel):
    """生成检验白板请求"""

    source_canvas: str = Field(
        ...,
        description="原Canvas文件名",
        min_length=1,
        max_length=200
    )

    include_colors: list[NodeColor] = Field(
        default_factory=lambda: [NodeColor.RED, NodeColor.PURPLE],
        description="包含的节点颜色"
    )

    options: ReviewOptions = Field(
        default_factory=ReviewOptions,
        description="生成选项"
    )
```

#### 2. ReviewGenerateResponse（生成检验白板响应）

```python
class ReviewGenerateResponse(BaseModel):
    """生成检验白板响应（后台任务）"""

    task_id: str = Field(
        ...,
        description="任务ID"
    )

    status: Literal["processing", "completed", "failed"] = Field(
        ...,
        description="任务状态"
    )

    review_canvas_name: str = Field(
        ...,
        description="检验白板文件名"
    )

    estimated_time: int = Field(
        ...,
        description="预计完成时间（秒）",
        ge=0
    )

    message: str = Field(
        ...,
        description="操作结果消息"
    )
```

#### 3. ReviewProgressResponse（检验进度响应）

```python
class ColorDistribution(BaseModel):
    """颜色分布"""

    red: int = Field(0, ge=0)
    green: int = Field(0, ge=0)
    purple: int = Field(0, ge=0)
    yellow: int = Field(0, ge=0)

class ProgressMetrics(BaseModel):
    """进度指标"""

    green_percentage: float = Field(..., ge=0, le=100)
    purple_percentage: float = Field(..., ge=0, le=100)
    red_percentage: float = Field(..., ge=0, le=100)

class CompletionCriteria(BaseModel):
    """完成标准"""

    green_target: float = Field(80, ge=0, le=100)
    current: float = Field(..., ge=0, le=100)
    met: bool = Field(...)

class ReviewProgressResponse(BaseModel):
    """检验进度响应"""

    canvas_name: str = Field(...)
    total_nodes: int = Field(..., ge=0)

    color_distribution: ColorDistribution = Field(...)
    progress: ProgressMetrics = Field(...)
    completion_criteria: CompletionCriteria = Field(...)
```

#### 4. ReviewSyncRequest（同步进度请求）

```python
class SyncOptions(BaseModel):
    """同步选项"""

    update_colors: bool = Field(
        True,
        description="更新颜色"
    )

    merge_new_nodes: bool = Field(
        True,
        description="合并新节点"
    )

class ReviewSyncRequest(BaseModel):
    """同步进度请求"""

    review_canvas: str = Field(
        ...,
        description="检验白板文件名"
    )

    source_canvas: str = Field(
        ...,
        description="原Canvas文件名"
    )

    sync_options: SyncOptions = Field(
        default_factory=SyncOptions,
        description="同步选项"
    )
```

---

## 🔧 通用模型

### 文件位置
`app/models/common.py`

### 模型定义

#### 1. SuccessResponse（成功响应）

```python
from typing import TypeVar, Generic
from datetime import datetime

T = TypeVar('T')

class ResponseMeta(BaseModel):
    """响应元数据"""

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="响应时间戳"
    )

    version: str = Field(
        "1.0.0",
        description="API版本"
    )

class SuccessResponse(BaseModel, Generic[T]):
    """成功响应通用模型"""

    data: T = Field(
        ...,
        description="响应数据"
    )

    meta: ResponseMeta = Field(
        default_factory=ResponseMeta,
        description="响应元数据"
    )
```

#### 2. ErrorResponse（错误响应）

```python
class ErrorDetail(BaseModel):
    """错误详情"""

    code: str = Field(
        ...,
        description="错误代码"
    )

    message: str = Field(
        ...,
        description="错误消息"
    )

    detail: Optional[str | dict] = Field(
        None,
        description="详细错误信息"
    )

class ErrorResponse(BaseModel):
    """错误响应模型"""

    error: ErrorDetail = Field(
        ...,
        description="错误信息"
    )
```

#### 3. PaginationMeta（分页元数据）

```python
class PaginationMeta(BaseModel):
    """分页元数据"""

    page: int = Field(..., ge=1, description="当前页码")
    size: int = Field(..., ge=1, le=100, description="每页大小")
    total: int = Field(..., ge=0, description="总记录数")
    pages: int = Field(..., ge=0, description="总页数")
```

---

## ✅ 数据验证规则

### 字符串验证

| 字段类型 | 验证规则 |
|---------|---------|
| Canvas名称 | 长度1-200，不含`../`，不含`/` |
| 节点文本 | 长度1-50000 |
| 节点ID | 非空字符串 |
| 文件路径 | 长度≤500，相对路径 |
| URL | 长度≤2000，有效URL格式 |

### 数值验证

| 字段类型 | 验证规则 |
|---------|---------|
| 坐标(x,y) | 0-100000 |
| 宽度 | 100-2000 |
| 高度 | 50-2000 |
| 评分 | 0-25（单维度），0-100（总分） |

### 枚举验证

| 字段类型 | 有效值 |
|---------|-------|
| 节点类型 | text, file, link |
| 节点颜色 | 1, 2, 3, 5, 6 |
| 边的侧 | top, right, bottom, left |
| 解释类型 | oral, clarification, comparison, memory, four_level, example |

---

## 🗺️ 模型关系图

```
CanvasRead
    ├── nodes: list[NodeRead]
    │       ├── id: str
    │       ├── type: NodeType
    │       ├── text/file/url: str
    │       ├── color: NodeColor
    │       └── x, y, width, height: int
    │
    └── edges: list[EdgeRead]
            ├── id: str
            ├── fromNode: str (→ NodeRead.id)
            ├── toNode: str (→ NodeRead.id)
            └── fromSide, toSide: EdgeSide

AgentRequest
    ├── BasicDecomposeRequest
    │       ├── canvas_name: str
    │       ├── node_id: str (红色节点)
    │       └── concept: str
    │
    ├── DeepDecomposeRequest
    │       ├── canvas_name: str
    │       ├── node_id: str (紫色节点)
    │       ├── concept: str
    │       └── understanding: str
    │
    └── ScoreRequest
            ├── canvas_name: str
            ├── node_id: str (黄色节点)
            ├── concept: str
            └── understanding: str

AgentResponse
    ├── DecomposeResponse
    │       ├── questions: list[QuestionItem]
    │       └── nodes_created: list[str]
    │
    ├── ScoreResponse
    │       ├── scores: ScoreDimensions
    │       ├── level: str
    │       ├── feedback: ScoreFeedback
    │       └── new_color: NodeColor
    │
    └── ExplanationResponse
            ├── explanation_file: str
            ├── file_node_id: str
            └── word_count: int

ReviewModels
    ├── ReviewGenerateRequest
    │       ├── source_canvas: str
    │       └── include_colors: list[NodeColor]
    │
    └── ReviewProgressResponse
            ├── color_distribution: ColorDistribution
            ├── progress: ProgressMetrics
            └── completion_criteria: CompletionCriteria
```

---

## 📚 使用示例

### 示例1: 创建节点

```python
# 请求
node_create = NodeCreate(
    canvas_name="离散数学",
    type="text",
    text="我的理解：逆否命题是...",
    color="6",
    x=100,
    y=450,
    width=400,
    height=200
)

# 响应
node_response = NodeRead(
    id="node_3",
    type="text",
    text="我的理解：逆否命题是...",
    color="6",
    x=100,
    y=450,
    width=400,
    height=200,
    created_at=datetime.utcnow()
)
```

### 示例2: Agent调用

```python
# 基础拆解请求
decompose_request = BasicDecomposeRequest(
    canvas_name="离散数学",
    node_id="node_1",
    concept="逆否命题",
    context="在学习命题逻辑时遇到的概念"
)

# 拆解响应
decompose_response = DecomposeResponse(
    questions=[
        QuestionItem(
            type="定义型",
            question="什么是逆否命题？",
            guide="从定义入手理解基本概念"
        )
    ],
    nodes_created=["node_4", "node_5"],
    message="Basic decomposition completed"
)
```

---

**文档状态**: ✅ 完成
**最后更新**: 2025-11-13
**版本**: v1.0
**负责人**: PM Agent (John) + Architect Agent (Morgan)

---

## 附录：完整模型清单

### Canvas模型 (app/models/canvas.py)
- NodeBase
- NodeCreate
- NodeUpdate
- NodeRead
- EdgeBase
- EdgeCreate
- EdgeRead
- CanvasRead

### Agent模型 (app/models/agent.py)
- AgentRequestBase
- BasicDecomposeRequest
- DeepDecomposeRequest
- ScoreRequest
- ExplanationRequest
- QuestionItem
- DecomposeResponse
- ScoreDimensions
- ScoreFeedback
- ScoreResponse
- ExplanationResponse

### Review模型 (app/models/review.py)
- ReviewOptions
- ReviewGenerateRequest
- ReviewGenerateResponse
- ColorDistribution
- ProgressMetrics
- CompletionCriteria
- ReviewProgressResponse
- SyncOptions
- ReviewSyncRequest

### 通用模型 (app/models/common.py)
- ResponseMeta
- SuccessResponse
- ErrorDetail
- ErrorResponse
- PaginationMeta

**总计**: 31个数据模型
