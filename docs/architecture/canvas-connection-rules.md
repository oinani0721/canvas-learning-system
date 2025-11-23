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

# Canvas连接规则 - 标准化指南

**版本**: 1.0
**日期**: 2025-10-16
**状态**: 生产规范

---

## 目的

本文档定义Canvas学习系统中所有节点连接的标准化规则，确保：
1. **逻辑清晰** - 用户能快速理解Canvas的学习流程
2. **语义正确** - 连线反映真实的知识流动关系
3. **一致性** - 所有Canvas遵循相同的连接模式

---

## 核心原则

### 原则1: 对话式学习流程

Canvas应该反映**"用户输出 → AI回应"**的对话流程：

```
问题 → 用户理解 → AI补充 → 用户优化理解
```

**反例** ❌:
```
问题 → AI解释  # 缺少"用户先思考"的环节
```

### 原则2: 费曼学习法

**强制用户先输出，再获得AI帮助**：

```
红色问题节点
  ↓ 用户填写
黄色理解节点 (用户必须先表达)
  ↓ 然后AI补充
蓝色AI文档节点
```

### 原则3: 颜色语义

| 颜色 | 含义 | 连接规则 |
|------|------|---------|
| 🔴 红色(4) | 不理解/问题 | 作为起点，连向拆解问题 |
| 🟡 黄色(6) | 个人理解 | 接收来自问题，发出到AI文档 |
| 🔵 蓝色(5) | AI补充 | 接收来自黄色节点 |
| 🟢 绿色(2) | 完全理解 | 评分≥80后的终点 |
| 🟣 紫色(3) | 似懂非懂 | 评分60-79，需要深度拆解 |

---

## 标准连接模式

### 模式1: 基础拆解问题

**场景**: 用户完全不懂某个材料，需要拆解

```
原问题节点 (黄色，用户的困惑)
  ↓ [基础拆解问题]
拆解问题1 (红色, color="4")
  ↓ [个人理解]
黄色理解节点1 (color="6")

拆解问题2 (红色)
  ↓ [个人理解]
黄色理解节点2
...
```

**代码示例**:
```python
# 从原问题到拆解问题
edge_origin_to_question = {
    'fromNode': origin_yellow_node_id,
    'fromSide': 'right',
    'toNode': question_node_id,
    'toSide': 'left',
    'label': '基础拆解问题' if i == 0 else ''
}

# 从拆解问题到用户理解
edge_question_to_yellow = {
    'fromNode': question_node_id,
    'fromSide': 'bottom',
    'toNode': yellow_node_id,
    'toSide': 'top',
    'label': '个人理解'
}
```

**关键点**:
- ✅ 每个拆解问题都要连接到对应的黄色节点
- ✅ 第一个问题的连线标签是"基础拆解问题"，其他为空（避免视觉混乱）
- ✅ 所有问题从同一个原节点发出（保证连接完整性）

---

### 模式2: AI补充解释（最重要！）

**场景**: 用户填写了理解，需要AI补充解释

```
黄色理解节点 (用户填写："我需要详细解释...")
  ↓ [鸽笼原理详细解释 (AI)]
蓝色AI文档节点 (澄清路径.md)
```

**代码示例**:
```python
# ✅ 正确：从用户理解连接到AI文档
edge_yellow_to_ai = {
    'fromNode': user_yellow_node_id,  # 黄色节点
    'fromSide': 'right',
    'toNode': ai_doc_node_id,         # 蓝色文档节点
    'toSide': 'left',
    'color': '5',                     # 蓝色连线
    'label': 'XX解释 (AI)'
}

# ❌ 错误：不要从问题节点连接
edge_question_to_ai = {
    'fromNode': question_node_id,     # ❌ 问题节点
    'toNode': ai_doc_node_id
}
```

**关键规则** (必须遵守):

| 规则 | 说明 | 原因 |
|------|------|------|
| ✅ fromNode必须是黄色节点 | AI文档连接到用户理解 | 体现"用户先输出，AI后补充" |
| ❌ 不能从问题节点连接 | 问题节点只连向拆解 | 避免跳过用户思考环节 |
| ✅ 连线颜色必须是蓝色(5) | 表示AI内容 | 视觉上区分AI和用户内容 |
| ✅ 标签包含"(AI)" | 明确标识AI生成 | 帮助用户识别 |

**常见错误** ❌:

```python
# 错误1: 从问题连接（2025-10-16错误日志）
edge = {
    'fromNode': problem_node_id,  # ❌ 应该是黄色节点
    'toNode': ai_doc_id
}

# 错误2: 没有蓝色标识
edge = {
    'fromNode': yellow_node_id,
    'toNode': ai_doc_id,
    'color': '4'  # ❌ 应该是'5'(蓝色)
}

# 错误3: 标签没有标注AI
edge = {
    'fromNode': yellow_node_id,
    'toNode': ai_doc_id,
    'label': '详细解释'  # ❌ 应该是 '详细解释 (AI)'
}
```

---

### 模式3: 深度拆解

**场景**: 用户似懂非懂（紫色节点），需要深度拆解

```
紫色节点 (评分60-79)
  ↓ [深度拆解]
深度问题1 (红色)
  ↓ [个人理解]
黄色节点1
```

**代码示例**:
```python
edge_purple_to_deep_question = {
    'fromNode': purple_node_id,
    'toNode': deep_question_id,
    'label': '深度拆解'
}
```

---

### 模式4: 评分流转

**场景**: 对用户理解进行评分，改变颜色

```
黄色节点 (个人理解)
  ↓ [评分]

评分≥80 → 绿色节点
评分60-79 → 紫色节点
评分<60 → 保持红色
```

**代码示例**:
```python
# 评分不需要创建新边，只需要修改节点颜色
if score >= 80:
    node['color'] = '2'  # 绿色
elif score >= 60:
    node['color'] = '3'  # 紫色
else:
    node['color'] = '4'  # 红色
```

**注意**: 评分是修改现有节点，不创建新连线。

---

## 连接矩阵（快速查找）

| 起点节点 | 终点节点 | 连线标签 | 颜色 | 使用场景 |
|---------|---------|---------|------|---------|
| 原问题(黄) | 拆解问题(红) | "基础拆解问题" (仅第一个) | 默认 | 基础拆解 |
| 拆解问题(红) | 理解(黄) | "个人理解" | 默认 | 用户填写理解 |
| **理解(黄)** | **AI文档(蓝)** | **"XX解释 (AI)"** | **蓝(5)** | **AI补充** ⭐ |
| 理解(紫) | 深度问题(红) | "深度拆解" | 默认 | 深度拆解 |
| 原文档(蓝) | 子节点(紫) | 自定义 | 默认 | 知识展开 |

---

## 验证清单

在添加AI文档节点时，请检查：

- [ ] AI文档节点的颜色是蓝色(5)吗？
- [ ] AI文档的**起点是黄色理解节点**吗？（不是问题节点！）
- [ ] 连线颜色是蓝色(5)吗？
- [ ] 连线标签包含"(AI)"标识吗？
- [ ] 逻辑流程是：用户理解 → AI补充吗？（不是：问题 → AI）

---

## 代码模板

### 模板1: 创建AI文档连接

```python
def create_ai_doc_connection(
    user_yellow_node_id: str,
    ai_doc_file_path: str,
    label: str,
    canvas_data: dict
) -> tuple[dict, dict]:
    """
    创建AI文档节点及其与用户理解节点的连接

    Args:
        user_yellow_node_id: 用户黄色理解节点的ID
        ai_doc_file_path: AI文档的相对路径（如 "CS70/XX.md"）
        label: 连线标签（必须包含 "(AI)"）
        canvas_data: Canvas数据

    Returns:
        (ai_doc_node, edge) 元组

    示例:
        node, edge = create_ai_doc_connection(
            'text-pigeonhole-y2',
            'CS70/鸽笼原理-澄清路径-20251016.md',
            '鸽笼原理详细解释 (AI)',
            canvas_data
        )
    """
    # 验证：起点必须是黄色节点
    source_node = find_node_by_id(canvas_data, user_yellow_node_id)
    assert source_node['color'] == '6', \
        f"起点节点 {user_yellow_node_id} 不是黄色节点！"

    # 验证：标签必须包含 (AI)
    assert '(AI)' in label or '(ai)' in label, \
        f"标签 '{label}' 必须包含 '(AI)' 标识！"

    # 创建AI文档节点
    ai_doc_node = {
        'id': f'file-ai-{generate_id()}',
        'type': 'file',
        'file': ai_doc_file_path,
        'x': source_node['x'] + 700,  # 在用户节点右侧
        'y': source_node['y'],
        'width': 600,
        'height': 400,
        'color': '5'  # ✅ 蓝色
    }

    # 创建连接
    edge = {
        'id': f'edge-{user_yellow_node_id}-{ai_doc_node["id"]}',
        'fromNode': user_yellow_node_id,  # ✅ 从黄色节点
        'fromSide': 'right',
        'toNode': ai_doc_node['id'],
        'toSide': 'left',
        'color': '5',  # ✅ 蓝色连线
        'label': label
    }

    return ai_doc_node, edge
```

### 模板2: 验证AI文档连接

```python
def validate_ai_doc_connections(canvas_data: dict) -> list[str]:
    """
    验证Canvas中所有AI文档的连接是否符合规则

    Returns:
        错误列表（空列表表示全部正确）
    """
    errors = []

    # 找出所有蓝色AI文档节点
    ai_docs = [n for n in canvas_data['nodes']
               if n.get('color') == '5' and n.get('type') == 'file']

    for ai_doc in ai_docs:
        # 找出指向这个AI文档的连线
        incoming_edges = [e for e in canvas_data['edges']
                          if e['toNode'] == ai_doc['id']]

        if not incoming_edges:
            errors.append(f"AI文档 {ai_doc.get('file')} 没有入边！")
            continue

        for edge in incoming_edges:
            source = find_node_by_id(canvas_data, edge['fromNode'])

            # 规则1: 起点必须是黄色节点
            if source['color'] != '6':
                errors.append(
                    f"AI文档 {ai_doc.get('file')} 的起点不是黄色节点！"
                    f"当前起点颜色: {source['color']}"
                )

            # 规则2: 连线必须是蓝色
            if edge.get('color') != '5':
                errors.append(
                    f"AI文档 {ai_doc.get('file')} 的连线不是蓝色！"
                )

            # 规则3: 标签必须包含 (AI)
            label = edge.get('label', '')
            if '(AI)' not in label and '(ai)' not in label:
                errors.append(
                    f"AI文档 {ai_doc.get('file')} 的标签缺少 '(AI)' 标识！"
                )

    return errors
```

---

## 常见问题FAQ

### Q1: 为什么AI文档必须连接到黄色节点，而不是问题节点？

**A**: 体现费曼学习法和对话式学习：

1. **费曼学习法** - 强制用户先输出（黄色节点），再获得帮助（AI文档）
2. **对话流程** - 用户提问 → AI回答，而不是 问题 → AI直接解答
3. **逻辑清晰** - 用户能快速看出"这个AI文档是回应我哪个理解的"

### Q2: 如果用户还没填写黄色节点，我能先创建AI文档吗？

**A**: 不建议。正确流程：

1. 生成拆解问题（红色）
2. 等待用户填写黄色理解
3. 根据用户的理解生成AI文档
4. 连接到对应的黄色节点

如果提前生成，会打破"用户先思考"的学习流程。

### Q3: 一个黄色节点可以连接多个AI文档吗？

**A**: 可以，但要注意：

```
黄色节点: "我需要详细解释和应试技巧"
  ├─→ AI澄清路径文档 (详细解释)
  └─→ AI记忆锚点文档 (应试技巧)
```

建议：如果用户需求明确分为多个方面，可以创建多个文档，但标签要说明侧重点。

### Q4: 原问题节点可以连接到AI文档吗？

**A**: 只有一种情况可以：**参考资料**

```
原问题节点 (黄色，用户的材料)
  ↓ [参考资料]
AI笔记文档 (蓝色, 如老师讲义的翻译)
```

但这不是"补充解释"，而是"参考资料"，标签应该是"参考资料"或"补充材料"，不是"XX解释 (AI)"。

---

## 历史错误记录

### 错误1: AI文档连接到问题节点 (2025-10-16)

**详情**: `docs/issues/canvas-ai-doc-connection-error.md`

**错误**: 将鸽笼原理的AI解释文档连接到原问题节点，而不是用户理解节点

**教训**: 始终遵循"用户输出 → AI回应"的原则

---

**文档作者**: Canvas Learning System Team
**最后更新**: 2025-10-16
**文档版本**: 1.0
