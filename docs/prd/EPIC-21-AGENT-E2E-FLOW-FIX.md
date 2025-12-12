---
document_type: "PRD"
version: "1.0.0"
last_modified: "2025-12-11"
status: "draft"
iteration: 1

authors:
  - name: "PM Agent"
    role: "Product Manager"

reviewers:
  - name: "PO Agent"
    role: "Product Owner"
    approved: false

compatible_with:
  architecture: "v1.0"
  api_spec: "v1.0"

changes_from_previous:
  - "Initial Epic created for Agent end-to-end flow fix"

git:
  commit_sha: ""
  tag: ""

metadata:
  project_name: "Canvas Learning System"
  epic_count: 1
  fr_count: 6
  nfr_count: 4
---

# Epic 21: Agent端到端流程修复

**Epic ID**: Epic 21
**Epic名称**: Agent端到端流程修复
**优先级**: P0 (最高) - 🔴 核心问题
**预计时间**: 2周 (40小时)
**状态**: 准备启动
**创建日期**: 2025-12-11
**负责PM**: PM Agent (John)
**依赖**: Epic 20完成 (多Provider稳定性) ✅
**阻塞**: Epic 22 (记忆系统)、Epic 23 (RAG系统)、Epic 24 (检验白板)

---

## 目录

1. [Epic概述](#epic概述)
2. [问题分析 (Bug 2 & Bug 8详解)](#问题分析-bug-2--bug-8详解)
3. [业务价值和目标](#业务价值和目标)
4. [技术架构](#技术架构)
5. [Story详细分解](#story详细分解)
6. [验收标准](#验收标准)
7. [风险评估](#风险评估)

---

## Epic概述

### 问题陈述

Canvas Learning System 的Agent功能存在**两个严重问题**：

1. **Bug 2: Agent生成幻觉** - Agent只能看到单节点内容，不了解Canvas结构、Edge关系和相邻节点
2. **Bug 8: Agent不返回结果** - 四层级解释正常工作，但基础拆解/深度拆解/口语解释等都不返回任何结果

**现象描述**:
- 调用基础拆解后，Canvas上没有新节点创建
- 调用口语解释后，没有Edge连接生成
- 生成的内容与Canvas上下文脱节（幻觉）
- **唯独四层级解释 (four-level) 正常工作**

### 核心发现

**四层级解释正常工作的原因**:

| 差异点 | 四层级解释 | 其他Agent |
|--------|-----------|-----------|
| 位置信息提取 | ✅ 从Canvas节点读取精确坐标 | ❌ 使用默认值 (0,0,400,200) |
| ContextEnrichmentService | ✅ 调用了上下文服务 | ❌ 未调用或部分调用 |
| Response解析 | ✅ 有结构化输出模式 | ❌ 可能格式不匹配 |
| Edge连接 | ✅ 创建正确的Edge | ❌ Edge创建失败或跳过 |

### 解决方案

**统一Agent端到端流程**，确保所有Agent与四层级解释具有相同的：

1. ✅ 源节点位置信息提取
2. ✅ ContextEnrichmentService上下文丰富
3. ✅ API响应解析和容错
4. ✅ 节点创建和Edge连接逻辑
5. ✅ 个人理解节点自动创建

### Epic范围

**包含在Epic 21中**:
- ✅ 统一所有Agent端点的位置信息提取
- ✅ 扩展ContextEnrichmentService支持Edge和相邻节点
- ✅ 修复explanation_text为空导致节点不创建的问题
- ✅ 添加API响应解析的日志和fallback机制
- ✅ 个人理解黄色节点自动创建
- ✅ Edge连接逻辑统一化

**不包含在Epic 21中** (后续Epic):
- ❌ 记忆系统集成 (Epic 22)
- ❌ RAG智能推理 (Epic 23)
- ❌ 检验白板重新设计 (Epic 24)

---

## 问题分析 (Bug 2 & Bug 8详解)

### Bug 2: Agent生成幻觉 - 根因分析

```
用户调用 decompose_basic()
            │
            ▼
┌─────────────────────────────────────────────────────────┐
│ 问题: decompose_basic() 不使用 ContextEnrichmentService  │
│ ─────────────────────────────────────────────────────── │
│ 代码位置: backend/app/api/v1/endpoints/agents.py        │
│                                                         │
│ @agents_router.post("/decompose/basic")                │
│ async def decompose_basic(request: DecomposeRequest):  │
│     node = next((n for n in canvas_data...))           │
│     content = node.get("text", "")  # ← 只有单节点内容   │
│     result = await agent_service.decompose_basic(      │
│         content=content  # ← 无上下文!                  │
│     )                                                   │
└─────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────┐
│ 结果: Agent只看到单节点内容，不知道Canvas结构            │
│ ─────────────────────────────────────────────────────── │
│ Agent不知道:                                            │
│   • 节点在Canvas中的位置                                 │
│   • 与其他节点的Edge关系                                 │
│   • 相邻节点的内容                                       │
│   • Edge标签语义 (如"基础拆解"、"个人理解")              │
└─────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────┐
│ 后果: 生成与节点无关的幻觉内容                           │
└─────────────────────────────────────────────────────────┘
```

**对比: 四层级解释的正确实现**:

```python
# ✅ explain_oral - 有上下文enrichment
@agents_router.post("/explain/oral")
async def explain_oral(
    request: ExplainRequest,
    context_service: ContextEnrichmentService = Depends(get_context_service)
):
    enriched = await context_service.enrich_context(
        canvas_path=request.canvas_path,
        target_node_id=request.node_id
    )
    # enriched 包含: 相邻节点、Edge关系、位置信息
```

### Bug 8: Agent不返回结果 - 根因分析

```
Agent API返回response
            │
            ▼
┌─────────────────────────────────────────────────────────┐
│ agent_service.py:994-1008 - 提取explanation_text        │
│ ─────────────────────────────────────────────────────── │
│ explanation_text = ""                                   │
│ if hasattr(response, 'text'):                          │
│     explanation_text = response.text                    │
│ elif isinstance(response, dict):                        │
│     explanation_text = response.get('text', '')         │
│     # ... 其他提取逻辑                                  │
└─────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────┐
│ agent_service.py:1036 - 关键检查点                       │
│ ─────────────────────────────────────────────────────── │
│ if explanation_text:  # ← 如果为空，跳过整个节点创建!    │
│     created_nodes.append({...})                         │
│     created_edges.append({...})                         │
│                                                         │
│ # 如果explanation_text为空，直接返回空数组               │
│ return {                                                │
│     "created_nodes": [],   # ← 空!                      │
│     "created_edges": [],   # ← 空!                      │
│ }                                                       │
└─────────────────────────────────────────────────────────┘
```

**为什么四层级解释不受影响**:

```python
# agents.py:627-644 - 四层级特殊处理
# 1. 提取源节点位置
source_x = enriched_context.target_node.get("x", 0)
source_y = enriched_context.target_node.get("y", 0)
source_width = enriched_context.target_node.get("width", 400)
source_height = enriched_context.target_node.get("height", 200)

# 2. 传给generate_explanation
result = await agent_service.generate_explanation(
    ...,
    source_x=source_x,          # ← 正确的位置
    source_y=source_y,
    source_width=source_width,
    source_height=source_height
)
```

**其他Agent缺少这些参数**，导致使用默认值(0,0)，可能与Canvas外的区域交互。

### 缺失的上下文类型

| 上下文类型 | 当前状态 | 影响 |
|------------|----------|------|
| Canvas内部Edge关系 | ❌ 未提取 | 不知道父/子/同级节点 |
| 相邻节点内容 | ❌ 未提取 | 生成内容与相邻节点重复或矛盾 |
| Edge标签语义 | ❌ 未提取 | 不知道"基础拆解"、"个人理解"等关系 |
| 跨Canvas关联 | ❌ 未提取 | 题目Canvas和讲座Canvas无法关联 |
| 教材上下文 | ❌ 未提取 | 不知道挂载的PDF/笔记内容 |

---

## 业务价值和目标

### 业务价值

| 价值项 | 重要性 | 说明 |
|--------|--------|------|
| **Agent可用性** | ⭐⭐⭐⭐⭐ | 所有12个Agent正常工作，而非只有四层级 |
| **学习效果** | ⭐⭐⭐⭐⭐ | Agent生成内容与学习上下文相关，不再幻觉 |
| **用户信任** | ⭐⭐⭐⭐⭐ | 用户可以信赖Agent的输出质量 |
| **功能完整性** | ⭐⭐⭐⭐ | 基础拆解、深度拆解、口语解释等恢复正常 |

### 目标

#### 短期目标 (Epic 21完成后)
- [ ] 所有12个学习Agent正常返回结果
- [ ] Agent生成内容与Canvas上下文相关 (无幻觉)
- [ ] 自动创建个人理解黄色节点
- [ ] Edge连接正确创建

#### 质量指标
- [ ] Agent调用成功率 > 99%
- [ ] 生成内容与上下文相关度评分 > 4/5
- [ ] 节点创建成功率 100%
- [ ] Edge连接成功率 100%

---

## 技术架构

### 统一Agent流程架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    统一Agent端到端流程                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Step 1: 位置信息提取 (统一化)                            │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ source_x = node.get("x", 0)                             │   │
│  │ source_y = node.get("y", 0)                             │   │
│  │ source_width = node.get("width", 400)                   │   │
│  │ source_height = node.get("height", 200)                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          │                                       │
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Step 2: ContextEnrichmentService 上下文丰富              │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ enriched_context = await context_service.enrich(        │   │
│  │     canvas_path,                                        │   │
│  │     target_node_id,                                     │   │
│  │     include_edges=True,      # 新增: Edge关系            │   │
│  │     include_neighbors=True,  # 新增: 相邻节点内容        │   │
│  │     include_textbook=True    # 新增: 教材上下文          │   │
│  │ )                                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          │                                       │
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Step 3: Agent AI调用 (带完整上下文)                      │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ response = await agent_service.generate_*(              │   │
│  │     content=enriched_context.target_content,            │   │
│  │     context=enriched_context.full_context,              │   │
│  │     source_x, source_y, source_width, source_height     │   │
│  │ )                                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          │                                       │
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Step 4: Response解析 (带容错)                            │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ explanation_text = extract_text(response)               │   │
│  │ if not explanation_text:                                │   │
│  │     # Fallback: 尝试其他解析方式                         │   │
│  │     explanation_text = fallback_extract(response)       │   │
│  │     log.warning("Used fallback extraction")             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          │                                       │
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Step 5: 节点和Edge创建 (统一化)                          │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ # 创建解释节点                                           │   │
│  │ explanation_node = create_node(                         │   │
│  │     text=explanation_text,                              │   │
│  │     x=source_x + source_width + 50,  # 正确偏移         │   │
│  │     y=source_y,                                         │   │
│  │     color="3"  # 绿色                                   │   │
│  │ )                                                        │   │
│  │                                                          │   │
│  │ # 创建个人理解节点                                       │   │
│  │ personal_node = create_node(                            │   │
│  │     text="",  # 空白供用户填写                          │   │
│  │     color="4"  # 黄色                                   │   │
│  │ )                                                        │   │
│  │                                                          │   │
│  │ # 创建Edge连接                                           │   │
│  │ edges = create_edges(                                   │   │
│  │     source_node, explanation_node, personal_node        │   │
│  │ )                                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### ContextEnrichmentService 扩展设计

```python
# backend/app/services/context_enrichment_service.py - 扩展

@dataclass
class EnrichedContext:
    """丰富的上下文信息"""

    # 目标节点
    target_node: Dict[str, Any]
    target_content: str

    # 位置信息
    x: int
    y: int
    width: int
    height: int

    # Edge关系 (新增)
    incoming_edges: List[Dict]  # 指向当前节点的Edge
    outgoing_edges: List[Dict]  # 从当前节点出发的Edge
    edge_labels: List[str]      # Edge标签列表

    # 相邻节点 (新增)
    parent_nodes: List[Dict]    # 父节点内容
    child_nodes: List[Dict]     # 子节点内容
    sibling_nodes: List[Dict]   # 同级节点内容

    # 教材上下文 (新增)
    textbook_context: Optional[str]  # 挂载的教材相关段落

    # 完整上下文字符串
    full_context: str

class ContextEnrichmentService:
    async def enrich_context(
        self,
        canvas_path: str,
        target_node_id: str,
        include_edges: bool = True,
        include_neighbors: bool = True,
        include_textbook: bool = False,
        max_neighbor_depth: int = 1
    ) -> EnrichedContext:
        """
        丰富节点上下文信息

        Args:
            canvas_path: Canvas文件路径
            target_node_id: 目标节点ID
            include_edges: 是否包含Edge关系
            include_neighbors: 是否包含相邻节点
            include_textbook: 是否包含教材上下文
            max_neighbor_depth: 相邻节点最大深度
        """
        pass
```

---

## Story详细分解

### Story 21.1: 统一位置信息提取

**Story ID**: Story-21.1
**标题**: 统一explain/decompose端点位置信息提取
**优先级**: P0
**预计时间**: 4小时
**状态**: 待开发

#### 用户故事
```
作为Agent服务
我希望所有Agent端点都能正确提取源节点位置信息
以便生成的新节点能够正确放置在Canvas上
```

#### 验收标准 (AC)
- [ ] AC-21.1.1: decompose_basic 提取完整位置信息 (x, y, width, height)
- [ ] AC-21.1.2: decompose_deep 提取完整位置信息
- [ ] AC-21.1.3: explain_oral 保持现有正确实现
- [ ] AC-21.1.4: 所有Agent端点使用统一的位置提取函数
- [ ] AC-21.1.5: 单元测试覆盖位置提取逻辑

#### 技术任务
1. **创建统一位置提取函数**
   ```python
   # backend/app/api/v1/endpoints/agents.py
   def extract_node_position(node: Dict) -> Tuple[int, int, int, int]:
       """统一提取节点位置信息"""
       return (
           node.get("x", 0),
           node.get("y", 0),
           node.get("width", 400),
           node.get("height", 200)
       )
   ```

2. **更新decompose_basic端点**
3. **更新decompose_deep端点**
4. **更新其他缺失位置信息的端点**

#### 关键文件
- `backend/app/api/v1/endpoints/agents.py` (修改)
- `backend/tests/unit/test_agent_position.py` (新增)

---

### Story 21.2: ContextEnrichmentService扩展

**Story ID**: Story-21.2
**标题**: ContextEnrichmentService扩展 (Edge/相邻节点)
**优先级**: P0
**预计时间**: 8小时
**状态**: 待开发

#### 用户故事
```
作为Agent服务
我希望能够获取目标节点的完整上下文
包括Edge关系、相邻节点内容和教材上下文
以便生成与Canvas结构相关的内容
```

#### 验收标准 (AC)
- [ ] AC-21.2.1: 支持提取incoming/outgoing Edge关系
- [ ] AC-21.2.2: 支持提取Edge标签 (如"基础拆解"、"个人理解")
- [ ] AC-21.2.3: 支持提取父/子/同级节点内容
- [ ] AC-21.2.4: 支持可配置的相邻节点深度 (默认1层)
- [ ] AC-21.2.5: 返回结构化EnrichedContext对象

#### 技术任务
1. **定义EnrichedContext数据类**
2. **实现Edge关系提取**
   ```python
   async def _extract_edges(self, canvas_data: Dict, node_id: str):
       edges = canvas_data.get("edges", [])
       incoming = [e for e in edges if e.get("toNode") == node_id]
       outgoing = [e for e in edges if e.get("fromNode") == node_id]
       return incoming, outgoing
   ```
3. **实现相邻节点提取**
4. **实现TextbookContextService集成** (可选)
5. **更新enrich_context方法**

#### 关键文件
- `backend/app/services/context_enrichment_service.py` (修改)
- `backend/app/models/schemas.py` (新增EnrichedContext)
- `backend/tests/unit/test_context_enrichment.py` (新增)

---

### Story 21.3: 修复explanation_text为空问题

**Story ID**: Story-21.3
**标题**: 修复explanation_text为空问题
**优先级**: P0
**预计时间**: 6小时
**状态**: 待开发

#### 用户故事
```
作为Agent服务
我希望即使API响应格式不完全匹配
也能尽最大努力提取有效内容
以便用户始终能看到Agent的输出
```

#### 验收标准 (AC)
- [ ] AC-21.3.1: explanation_text提取有多重fallback机制
- [ ] AC-21.3.2: 每次提取失败都有详细日志
- [ ] AC-21.3.3: 如果所有提取都失败，返回友好错误信息而非空结果
- [ ] AC-21.3.4: 添加response格式验证

#### 技术任务
1. **重构explanation_text提取逻辑**
   ```python
   # backend/app/services/agent_service.py:994-1036

   def extract_explanation_text(response: Any) -> Tuple[str, bool]:
       """
       提取explanation_text，带多重fallback

       Returns:
           (text, success) - text为提取的内容，success表示是否成功
       """
       extractors = [
           lambda r: r.text if hasattr(r, 'text') else None,
           lambda r: r.get('text') if isinstance(r, dict) else None,
           lambda r: r.get('content') if isinstance(r, dict) else None,
           lambda r: str(r) if r else None,  # 最终fallback
       ]

       for i, extractor in enumerate(extractors):
           try:
               text = extractor(response)
               if text and text.strip():
                   if i > 0:
                       logger.warning(f"Used fallback extractor #{i}")
                   return text.strip(), True
           except Exception as e:
               logger.debug(f"Extractor #{i} failed: {e}")

       logger.error("All extractors failed", extra={"response": str(response)[:500]})
       return "", False
   ```

2. **添加友好错误处理**
3. **添加response格式日志**
4. **更新节点创建逻辑**

#### 关键文件
- `backend/app/services/agent_service.py` (修改)
- `backend/tests/unit/test_text_extraction.py` (新增)

---

### Story 21.4: API响应解析日志和fallback

**Story ID**: Story-21.4
**标题**: 添加API响应解析日志和fallback
**优先级**: P1
**预计时间**: 4小时
**状态**: 待开发

#### 用户故事
```
作为开发者
我希望能够追踪每次Agent调用的完整流程
以便在出现问题时快速定位原因
```

#### 验收标准 (AC)
- [ ] AC-21.4.1: 每次Agent调用记录request和response摘要
- [ ] AC-21.4.2: 解析失败时记录完整response (截断到500字符)
- [ ] AC-21.4.3: 添加结构化日志字段 (agent_type, node_id, success, latency)
- [ ] AC-21.4.4: 日志级别可配置 (DEBUG/INFO/WARNING)

#### 技术任务
1. **实现结构化日志**
   ```python
   logger.info(
       "Agent call completed",
       extra={
           "agent_type": "decompose_basic",
           "node_id": node_id,
           "success": True,
           "latency_ms": 1234,
           "response_length": len(response_text)
       }
   )
   ```

2. **添加response摘要日志**
3. **添加错误追踪**

#### 关键文件
- `backend/app/services/agent_service.py` (修改)
- `backend/app/utils/logging.py` (新增)

---

### Story 21.5: 个人理解节点自动创建

**Story ID**: Story-21.5
**标题**: 个人理解节点自动创建
**优先级**: P0
**预计时间**: 6小时
**状态**: 待开发

#### 用户故事
```
作为学习者
我希望每次Agent生成解释后
自动创建一个空白黄色节点供我填写个人理解
以便践行费曼学习法
```

#### 验收标准 (AC)
- [ ] AC-21.5.1: 每个Agent解释节点旁自动创建黄色个人理解节点
- [ ] AC-21.5.2: 个人理解节点包含提示文字 "在此填写你的个人理解..."
- [ ] AC-21.5.3: 个人理解节点通过Edge与解释节点连接
- [ ] AC-21.5.4: 支持配置是否自动创建 (默认开启)
- [ ] AC-21.5.5: 个人理解节点位置在解释节点下方

#### 技术任务
1. **定义个人理解节点模板**
   ```python
   PERSONAL_UNDERSTANDING_TEMPLATE = {
       "type": "text",
       "text": "在此填写你的个人理解...",
       "width": 400,
       "height": 150,
       "color": "4"  # 黄色
   }
   ```

2. **更新节点创建逻辑**
3. **创建Edge连接**
4. **添加配置开关**

#### 关键文件
- `backend/app/services/agent_service.py` (修改)
- `backend/app/services/canvas_service.py` (修改)
- `backend/app/config.py` (添加配置项)

---

### Story 21.6: Edge连接逻辑修复

**Story ID**: Story-21.6
**标题**: Edge连接逻辑修复
**优先级**: P0
**预计时间**: 4小时
**状态**: 待开发

#### 用户故事
```
作为Canvas系统
我希望所有新创建的节点都有正确的Edge连接
以便用户能够清晰看到节点之间的关系
```

#### 验收标准 (AC)
- [ ] AC-21.6.1: 源节点 → 解释节点 Edge创建成功
- [ ] AC-21.6.2: 解释节点 → 个人理解节点 Edge创建成功
- [ ] AC-21.6.3: Edge包含正确的标签 (如"基础拆解"、"个人理解")
- [ ] AC-21.6.4: Edge样式正确 (颜色、箭头)
- [ ] AC-21.6.5: 不创建重复Edge

#### 技术任务
1. **统一Edge创建函数**
   ```python
   def create_edge(
       from_node_id: str,
       to_node_id: str,
       label: str = "",
       color: str = "5"  # 默认颜色
   ) -> Dict:
       return {
           "id": str(uuid.uuid4()),
           "fromNode": from_node_id,
           "toNode": to_node_id,
           "fromSide": "right",
           "toSide": "left",
           "label": label,
           "color": color
       }
   ```

2. **检查重复Edge逻辑**
3. **更新所有Agent的Edge创建调用**

#### 关键文件
- `backend/app/services/agent_service.py` (修改)
- `backend/app/services/canvas_service.py` (修改)

---

## 验收标准

### Epic级别验收标准

| ID | 验收标准 | 验证方法 |
|----|----------|----------|
| AC-21.E1 | 所有12个Agent正常返回结果 | 逐个测试每个Agent |
| AC-21.E2 | 生成内容与Canvas上下文相关 | 人工评估 (评分>4/5) |
| AC-21.E3 | 个人理解节点自动创建 | 功能测试 |
| AC-21.E4 | Edge连接正确 | Canvas文件检查 |
| AC-21.E5 | 无幻觉内容生成 | 人工评估 |

### 测试计划

1. **单元测试**
   - 位置提取测试
   - Context enrichment测试
   - Text extraction测试
   - Edge创建测试

2. **集成测试**
   - Agent端到端流程测试
   - Canvas文件更新测试
   - 多Agent并行测试

3. **人工验证**
   - 12个Agent逐个测试
   - 生成内容质量评估
   - Canvas结构正确性检查

---

## 风险评估

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| Context提取性能下降 | 中 | 中 | 添加缓存，限制相邻节点深度 |
| 不同Provider响应格式不一致 | 高 | 中 | 多重fallback，格式适配层 |
| 现有四层级解释被影响 | 低 | 高 | 回归测试，Feature flag |
| 大Canvas文件处理慢 | 中 | 中 | 分页加载，懒加载 |

---

## 依赖关系

### 上游依赖
- Epic 20: 多Provider稳定性 ⏳ (并行进行)

### 下游依赖
- Epic 22: 记忆系统 (需要Agent正常工作)
- Epic 23: RAG智能推理 (需要上下文服务)
- Epic 24: 检验白板 (需要Agent正常工作)

---

## 附录

### A. 受影响的Agent列表

| Agent | 当前状态 | 问题 |
|-------|----------|------|
| basic-decomposition | ❌ 不工作 | 无上下文，无位置 |
| deep-decomposition | ❌ 不工作 | 无上下文，无位置 |
| four-level-explanation | ✅ 正常 | 参考实现 |
| oral-explanation | ❌ 不工作 | 可能缺少位置 |
| clarification-path | ❌ 不工作 | 无上下文 |
| comparison-table | ❌ 不工作 | 无上下文 |
| memory-anchor | ❌ 不工作 | 无上下文 |
| example-teaching | ❌ 不工作 | 无上下文 |
| question-decomposition | ❌ 不工作 | 无上下文 |
| verification-question | ❌ 不工作 | 无上下文 |
| scoring-agent | ⚠️ 待验证 | 可能工作 |
| canvas-orchestrator | ⚠️ 待验证 | 系统级Agent |

### B. 代码位置参考

| 功能 | 文件 | 行号 |
|------|------|------|
| 四层级位置提取 | agents.py | 627-644 |
| explanation_text提取 | agent_service.py | 994-1008 |
| 节点创建检查 | agent_service.py | 1036 |
| ContextEnrichmentService | context_enrichment_service.py | 全文件 |
| Canvas节点创建 | canvas_service.py | 待定位 |
