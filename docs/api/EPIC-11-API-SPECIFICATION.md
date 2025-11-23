# Epic 11: API接口规范

**文档类型**: API Specification
**Epic**: Epic 11 - FastAPI后端基础架构搭建
**API版本**: v1
**创建日期**: 2025-11-13
**负责人**: PM Agent (John)
**状态**: 已批准

---

## 📋 目录

1. [API概览](#-api概览)
2. [通用规范](#-通用规范)
3. [Canvas操作API](#-canvas操作api)
4. [Agent调用API](#-agent调用api)
5. [检验白板API](#-检验白板api)
6. [健康检查API](#-健康检查api)
7. [错误处理](#-错误处理)
8. [数据模型](#-数据模型)

---

## 🌐 API概览

### Base URL

**开发环境**:
```
http://localhost:8000
```

**生产环境**（未来）:
```
https://api.canvas-learning.com
```

### API版本控制

所有API使用URL路径版本控制：

```
/api/v1/...    # API版本1（当前版本）
/api/v2/...    # API版本2（未来）
```

### 认证

**Epic 11阶段**: 无需认证（本地开发）

**未来版本**: JWT Bearer Token

```
Authorization: Bearer <token>
```

### 请求格式

- **Content-Type**: `application/json`
- **字符编码**: UTF-8
- **日期格式**: ISO 8601 (`2025-11-13T10:30:00Z`)

### 响应格式

所有响应使用JSON格式：

```json
{
  "data": {
    // 响应数据
  },
  "meta": {
    "timestamp": "2025-11-13T10:30:00Z",
    "version": "1.0.0"
  }
}
```

错误响应：

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message",
    "detail": "Detailed error information"
  }
}
```

### HTTP状态码

| 状态码 | 含义 | 使用场景 |
|-------|------|---------|
| **200** | OK | 成功（GET, PUT, DELETE） |
| **201** | Created | 成功创建（POST） |
| **204** | No Content | 成功删除 |
| **400** | Bad Request | 请求参数错误 |
| **404** | Not Found | 资源未找到 |
| **422** | Unprocessable Entity | 数据验证失败 |
| **500** | Internal Server Error | 服务器错误 |
| **503** | Service Unavailable | 服务不可用 |

---

## 📐 通用规范

### 分页

**查询参数**:
- `page`: 页码（从1开始，默认1）
- `size`: 每页大小（默认20，最大100）

**响应格式**:
```json
{
  "data": [...],
  "meta": {
    "page": 1,
    "size": 20,
    "total": 150,
    "pages": 8
  }
}
```

### 排序

**查询参数**:
- `sort`: 排序字段
- `order`: 排序方向（`asc` / `desc`）

**示例**:
```
GET /api/v1/canvas?sort=updated_at&order=desc
```

### 过滤

**查询参数**:
- `filter[field]`: 字段过滤

**示例**:
```
GET /api/v1/canvas?filter[color]=1
```

---

## 📊 Canvas操作API

### 1. 读取Canvas文件

**Endpoint**: `GET /api/v1/canvas/{canvas_name}`

**描述**: 读取指定Canvas文件的完整内容

**路径参数**:
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `canvas_name` | string | ✅ | Canvas文件名（不含.canvas后缀） |

**查询参数**: 无

**请求示例**:
```http
GET /api/v1/canvas/离散数学 HTTP/1.1
Host: localhost:8000
```

**成功响应** (200 OK):
```json
{
  "data": {
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
      },
      {
        "id": "node_2",
        "type": "file",
        "file": "docs/逆否命题-口语化解释-20251113.md",
        "x": 550,
        "y": 200,
        "width": 600,
        "height": 400
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
    ]
  },
  "meta": {
    "timestamp": "2025-11-13T10:30:00Z",
    "version": "1.0.0",
    "node_count": 2,
    "edge_count": 1
  }
}
```

**错误响应** (404 Not Found):
```json
{
  "error": {
    "code": "CANVAS_NOT_FOUND",
    "message": "Canvas not found",
    "detail": "Canvas '离散数学' does not exist"
  }
}
```

---

### 2. 添加节点到Canvas

**Endpoint**: `POST /api/v1/canvas/nodes`

**描述**: 向指定Canvas添加新节点

**请求体**:
```json
{
  "canvas_name": "离散数学",
  "node": {
    "type": "text",
    "text": "我的理解：逆否命题是...",
    "color": "6",
    "x": 100,
    "y": 450,
    "width": 400,
    "height": 200
  }
}
```

**请求体字段**:
| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `canvas_name` | string | ✅ | Canvas文件名 |
| `node.type` | string | ✅ | 节点类型（`text` / `file` / `link`） |
| `node.text` | string | ⚠️ | 节点文本（text类型必需） |
| `node.file` | string | ⚠️ | 文件路径（file类型必需） |
| `node.url` | string | ⚠️ | URL（link类型必需） |
| `node.color` | string | ❌ | 颜色代码（1-6） |
| `node.x` | integer | ✅ | X坐标 |
| `node.y` | integer | ✅ | Y坐标 |
| `node.width` | integer | ❌ | 宽度（默认400） |
| `node.height` | integer | ❌ | 高度（默认200） |

**成功响应** (201 Created):
```json
{
  "data": {
    "node_id": "node_3",
    "canvas_name": "离散数学",
    "message": "Node created successfully"
  },
  "meta": {
    "timestamp": "2025-11-13T10:30:00Z"
  }
}
```

**错误响应** (400 Bad Request):
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "detail": {
      "node.text": "Field required for text type node"
    }
  }
}
```

---

### 3. 更新节点

**Endpoint**: `PUT /api/v1/canvas/nodes/{node_id}`

**描述**: 更新指定节点的属性

**路径参数**:
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `node_id` | string | ✅ | 节点ID |

**查询参数**:
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `canvas_name` | string | ✅ | Canvas文件名 |

**请求体**:
```json
{
  "text": "更新后的理解：逆否命题是...",
  "color": "3"
}
```

**请求体字段** (所有字段可选):
| 字段 | 类型 | 描述 |
|------|------|------|
| `text` | string | 更新文本 |
| `color` | string | 更新颜色 |
| `x` | integer | 更新X坐标 |
| `y` | integer | 更新Y坐标 |
| `width` | integer | 更新宽度 |
| `height` | integer | 更新高度 |

**成功响应** (200 OK):
```json
{
  "data": {
    "node_id": "node_3",
    "updated_fields": ["text", "color"],
    "message": "Node updated successfully"
  },
  "meta": {
    "timestamp": "2025-11-13T10:30:00Z"
  }
}
```

**错误响应** (404 Not Found):
```json
{
  "error": {
    "code": "NODE_NOT_FOUND",
    "message": "Node not found",
    "detail": "Node 'node_999' does not exist in canvas '离散数学'"
  }
}
```

---

### 4. 删除节点

**Endpoint**: `DELETE /api/v1/canvas/nodes/{node_id}`

**描述**: 删除指定节点

**路径参数**:
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `node_id` | string | ✅ | 节点ID |

**查询参数**:
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `canvas_name` | string | ✅ | Canvas文件名 |

**请求示例**:
```http
DELETE /api/v1/canvas/nodes/node_3?canvas_name=离散数学 HTTP/1.1
Host: localhost:8000
```

**成功响应** (200 OK):
```json
{
  "data": {
    "node_id": "node_3",
    "message": "Node deleted successfully"
  },
  "meta": {
    "timestamp": "2025-11-13T10:30:00Z"
  }
}
```

---

### 5. 添加边

**Endpoint**: `POST /api/v1/canvas/edges`

**描述**: 在两个节点之间添加连接线

**请求体**:
```json
{
  "canvas_name": "离散数学",
  "edge": {
    "fromNode": "node_1",
    "toNode": "node_3",
    "fromSide": "bottom",
    "toSide": "top",
    "label": "理解输出"
  }
}
```

**请求体字段**:
| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `canvas_name` | string | ✅ | Canvas文件名 |
| `edge.fromNode` | string | ✅ | 起始节点ID |
| `edge.toNode` | string | ✅ | 目标节点ID |
| `edge.fromSide` | string | ❌ | 起始侧（top/right/bottom/left） |
| `edge.toSide` | string | ❌ | 目标侧（top/right/bottom/left） |
| `edge.label` | string | ❌ | 边标签 |

**成功响应** (201 Created):
```json
{
  "data": {
    "edge_id": "edge_2",
    "message": "Edge created successfully"
  }
}
```

---

### 6. 删除边

**Endpoint**: `DELETE /api/v1/canvas/edges/{edge_id}`

**描述**: 删除指定的边

**路径参数**:
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `edge_id` | string | ✅ | 边ID |

**查询参数**:
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `canvas_name` | string | ✅ | Canvas文件名 |

**成功响应** (200 OK):
```json
{
  "data": {
    "edge_id": "edge_2",
    "message": "Edge deleted successfully"
  }
}
```

---

## 🤖 Agent调用API

### 1. 基础拆解Agent

**Endpoint**: `POST /api/v1/agent/decompose/basic`

**描述**: 调用basic-decomposition Agent拆解难懂概念

**请求体**:
```json
{
  "canvas_name": "离散数学",
  "node_id": "node_1",
  "concept": "逆否命题",
  "context": "在学习命题逻辑时遇到的概念"
}
```

**请求体字段**:
| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `canvas_name` | string | ✅ | Canvas文件名 |
| `node_id` | string | ✅ | 红色节点ID |
| `concept` | string | ✅ | 需要拆解的概念 |
| `context` | string | ❌ | 学习上下文 |

**成功响应** (200 OK):
```json
{
  "data": {
    "questions": [
      {
        "type": "定义型",
        "question": "什么是逆否命题？",
        "guide": "从定义入手理解基本概念"
      },
      {
        "type": "实例型",
        "question": "能举一个逆否命题的例子吗？",
        "guide": "通过具体例子理解抽象概念"
      },
      {
        "type": "对比型",
        "question": "逆否命题和原命题有什么关系？",
        "guide": "对比理解概念之间的联系"
      }
    ],
    "nodes_created": ["node_4", "node_5", "node_6"],
    "message": "Basic decomposition completed"
  }
}
```

---

### 2. 深度拆解Agent

**Endpoint**: `POST /api/v1/agent/decompose/deep`

**描述**: 调用deep-decomposition Agent深度拆解似懂非懂的概念

**请求体**:
```json
{
  "canvas_name": "离散数学",
  "node_id": "node_2",
  "concept": "逆否命题",
  "understanding": "我的理解：逆否命题就是把原命题的条件和结论都取反...",
  "context": "已经学习了基础定义，但对应用场景不清楚"
}
```

**请求体字段**:
| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `canvas_name` | string | ✅ | Canvas文件名 |
| `node_id` | string | ✅ | 紫色节点ID |
| `concept` | string | ✅ | 需要拆解的概念 |
| `understanding` | string | ✅ | 用户已有的理解 |
| `context` | string | ❌ | 学习上下文 |

**成功响应** (200 OK):
```json
{
  "data": {
    "questions": [
      {
        "type": "对比型",
        "question": "逆否命题和否命题的区别是什么？",
        "purpose": "暴露概念混淆点"
      },
      {
        "type": "原因型",
        "question": "为什么逆否命题和原命题等价？",
        "purpose": "深入理解本质"
      },
      {
        "type": "应用型",
        "question": "如何用逆否命题证明定理？",
        "purpose": "测试迁移能力"
      }
    ],
    "nodes_created": ["node_7", "node_8", "node_9"],
    "message": "Deep decomposition completed"
  }
}
```

---

### 3. 评分Agent

**Endpoint**: `POST /api/v1/agent/score`

**描述**: 调用scoring-agent对黄色节点评分

**请求体**:
```json
{
  "canvas_name": "离散数学",
  "node_id": "node_10",
  "concept": "逆否命题",
  "understanding": "逆否命题是对原命题p→q的条件和结论都取反，得到¬q→¬p。逆否命题和原命题真值相同，可用于反证法证明。例如：原命题'若x>0则x²>0'的逆否命题是'若x²≤0则x≤0'。"
}
```

**成功响应** (200 OK):
```json
{
  "data": {
    "scores": {
      "accuracy": 22,
      "imagery": 18,
      "completeness": 20,
      "originality": 15,
      "total": 75
    },
    "level": "紫色",
    "feedback": {
      "accuracy": "定义准确，符号表示正确",
      "imagery": "缺少生动类比，建议增加具体情境",
      "completeness": "涵盖了定义、性质和应用",
      "originality": "主要是教材内容的复述，缺少个人思考"
    },
    "recommendations": [
      "clarification-path",
      "memory-anchor"
    ],
    "color_updated": true,
    "new_color": "3",
    "message": "Scoring completed"
  }
}
```

---

### 4. 口语化解释Agent

**Endpoint**: `POST /api/v1/agent/explain/oral`

**描述**: 调用oral-explanation Agent生成口语化解释

**请求体**:
```json
{
  "canvas_name": "离散数学",
  "concept": "逆否命题",
  "target_node_id": "node_1"
}
```

**成功响应** (200 OK):
```json
{
  "data": {
    "explanation_file": "docs/逆否命题-口语化解释-20251113103000.md",
    "file_node_id": "node_11",
    "word_count": 1050,
    "sections": ["背景铺垫", "核心解释", "生动举例", "常见误区"],
    "message": "Oral explanation generated"
  }
}
```

---

### 5. 其他解释Agent

其他解释Agent的API格式类似，包括：

- `POST /api/v1/agent/explain/clarification` - 澄清路径
- `POST /api/v1/agent/explain/comparison` - 对比表
- `POST /api/v1/agent/explain/memory` - 记忆锚点
- `POST /api/v1/agent/explain/four-level` - 四层次解释
- `POST /api/v1/agent/explain/example` - 例题教学

**请求体**和**响应格式**类似oral-explanation。

---

## 📝 检验白板API

### 1. 生成检验白板

**Endpoint**: `POST /api/v1/review/generate`

**描述**: 从原白板生成检验白板（后台任务）

**请求体**:
```json
{
  "source_canvas": "离散数学",
  "include_colors": ["1", "3"],
  "options": {
    "auto_generate_questions": true,
    "cluster_by_topic": true
  }
}
```

**请求体字段**:
| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `source_canvas` | string | ✅ | 原Canvas文件名 |
| `include_colors` | array | ❌ | 包含的节点颜色（默认["1","3"]） |
| `options.auto_generate_questions` | boolean | ❌ | 自动生成检验问题（默认true） |
| `options.cluster_by_topic` | boolean | ❌ | 按主题聚类（默认true） |

**成功响应** (202 Accepted):
```json
{
  "data": {
    "task_id": "task_a1b2c3d4",
    "status": "processing",
    "review_canvas_name": "离散数学-检验白板-20251113",
    "estimated_time": 30,
    "message": "Review canvas generation started"
  }
}
```

**任务状态查询**: 使用`task_id`查询进度

---

### 2. 获取检验进度

**Endpoint**: `GET /api/v1/review/progress/{canvas_name}`

**描述**: 获取检验白板的学习进度

**路径参数**:
| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `canvas_name` | string | ✅ | 检验白板文件名 |

**成功响应** (200 OK):
```json
{
  "data": {
    "canvas_name": "离散数学-检验白板-20251113",
    "total_nodes": 15,
    "color_distribution": {
      "red": 2,
      "green": 10,
      "purple": 3,
      "yellow": 15
    },
    "progress": {
      "green_percentage": 66.7,
      "purple_percentage": 20.0,
      "red_percentage": 13.3
    },
    "completion_criteria": {
      "green_target": 80,
      "current": 66.7,
      "met": false
    }
  }
}
```

---

### 3. 同步学习进度

**Endpoint**: `POST /api/v1/review/sync`

**描述**: 将检验白板的进度同步回原白板

**请求体**:
```json
{
  "review_canvas": "离散数学-检验白板-20251113",
  "source_canvas": "离散数学",
  "sync_options": {
    "update_colors": true,
    "merge_new_nodes": true
  }
}
```

**成功响应** (200 OK):
```json
{
  "data": {
    "nodes_updated": 8,
    "nodes_merged": 3,
    "color_changes": {
      "red_to_green": 5,
      "purple_to_green": 3
    },
    "message": "Progress synced successfully"
  }
}
```

---

## ❤️ 健康检查API

### 健康检查

**Endpoint**: `GET /api/v1/health`

**描述**: 检查API服务状态

**成功响应** (200 OK):
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-11-13T10:30:00Z",
  "services": {
    "canvas_utils": "ok",
    "agent_connection": "ok"
  }
}
```

---

## ⚠️ 错误处理

### 错误响应格式

所有错误响应遵循统一格式：

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "detail": "Detailed error information or validation errors"
  }
}
```

### 错误码列表

| 错误码 | HTTP状态码 | 描述 |
|--------|-----------|------|
| `CANVAS_NOT_FOUND` | 404 | Canvas文件未找到 |
| `NODE_NOT_FOUND` | 404 | 节点未找到 |
| `EDGE_NOT_FOUND` | 404 | 边未找到 |
| `VALIDATION_ERROR` | 400 | 请求参数验证失败 |
| `INVALID_COLOR` | 400 | 无效的颜色代码 |
| `INVALID_NODE_TYPE` | 400 | 无效的节点类型 |
| `AGENT_CALL_FAILED` | 500 | Agent调用失败 |
| `FILE_WRITE_ERROR` | 500 | 文件写入错误 |
| `INTERNAL_ERROR` | 500 | 内部服务器错误 |

### 验证错误详情

Pydantic验证错误包含详细字段信息：

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "detail": {
      "loc": ["body", "node", "text"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  }
}
```

---

## 📊 数据模型

### Canvas模型

```typescript
interface Canvas {
  name: string;
  nodes: Node[];
  edges: Edge[];
}
```

### Node模型

```typescript
interface Node {
  id: string;
  type: "text" | "file" | "link";
  text?: string;          // text类型必需
  file?: string;          // file类型必需
  url?: string;           // link类型必需
  color?: "1" | "2" | "3" | "4" | "5" | "6";
  x: number;
  y: number;
  width?: number;         // 默认400
  height?: number;        // 默认200
}
```

### Edge模型

```typescript
interface Edge {
  id: string;
  fromNode: string;
  toNode: string;
  fromSide?: "top" | "right" | "bottom" | "left";
  toSide?: "top" | "right" | "bottom" | "left";
  label?: string;
}
```

### 颜色代码

| 代码 | 颜色 | 含义 |
|------|------|------|
| `"1"` | 红色 | 不理解/未通过 |
| `"2"` | 绿色 | 完全理解/已通过 |
| `"3"` | 紫色 | 似懂非懂/待检验 |
| `"5"` | 蓝色 | AI补充解释 |
| `"6"` | 黄色 | 个人理解输出区 |

---

## 🔐 API安全

### CORS配置

允许的来源：
- `http://localhost:3000`（开发环境）
- `http://127.0.0.1:3000`（开发环境）

允许的方法：
- `GET`
- `POST`
- `PUT`
- `DELETE`

### 输入验证

所有输入通过Pydantic模型验证：
- 类型检查
- 长度限制
- 格式验证
- 范围验证

### 路径遍历防护

Canvas名称限制：
- 不允许 `..`
- 不允许 `/`
- 只允许字母、数字、中文、下划线、连字符

---

## 📈 速率限制（未来）

**Epic 11不实现**，但为未来预留接口：

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1700000000
```

限制策略（未来）：
- 普通API：100请求/分钟
- Agent调用：10请求/分钟
- 检验白板生成：5请求/小时

---

## 📚 OpenAPI文档

### 自动生成文档

FastAPI自动生成OpenAPI schema：

**Swagger UI**: `http://localhost:8000/docs`

**ReDoc**: `http://localhost:8000/redoc`

**OpenAPI JSON**: `http://localhost:8000/api/v1/openapi.json`

### 文档增强

为endpoints添加描述和示例：

```python
@router.post(
    "/nodes",
    response_model=NodeCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="添加节点到Canvas",
    description="向指定Canvas文件添加新节点，支持text/file/link三种类型",
    response_description="返回新创建节点的ID",
    responses={
        201: {
            "description": "节点创建成功",
            "content": {
                "application/json": {
                    "example": {
                        "data": {
                            "node_id": "node_3",
                            "message": "Node created successfully"
                        }
                    }
                }
            }
        },
        400: {"description": "请求参数错误"},
        404: {"description": "Canvas未找到"}
    }
)
async def create_node(...):
    ...
```

---

**文档状态**: ✅ 完成
**最后更新**: 2025-11-13
**版本**: v1.0
**负责人**: PM Agent (John)

---

## 附录：完整API清单

### Canvas操作

- `GET /api/v1/canvas/{canvas_name}` - 读取Canvas
- `POST /api/v1/canvas/nodes` - 添加节点
- `PUT /api/v1/canvas/nodes/{node_id}` - 更新节点
- `DELETE /api/v1/canvas/nodes/{node_id}` - 删除节点
- `POST /api/v1/canvas/edges` - 添加边
- `DELETE /api/v1/canvas/edges/{edge_id}` - 删除边

### Agent调用

- `POST /api/v1/agent/decompose/basic` - 基础拆解
- `POST /api/v1/agent/decompose/deep` - 深度拆解
- `POST /api/v1/agent/score` - 评分
- `POST /api/v1/agent/explain/oral` - 口语化解释
- `POST /api/v1/agent/explain/clarification` - 澄清路径
- `POST /api/v1/agent/explain/comparison` - 对比表
- `POST /api/v1/agent/explain/memory` - 记忆锚点
- `POST /api/v1/agent/explain/four-level` - 四层次解释
- `POST /api/v1/agent/explain/example` - 例题教学

### 检验白板

- `POST /api/v1/review/generate` - 生成检验白板
- `GET /api/v1/review/progress/{canvas_name}` - 获取进度
- `POST /api/v1/review/sync` - 同步进度

### 健康检查

- `GET /api/v1/health` - 健康检查

**总计**: 19个API endpoints
