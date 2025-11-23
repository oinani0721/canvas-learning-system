---
document_type: "Architecture"
version: "1.1.0"
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

# Canvas布局算法 v1.1

**版本**: v1.1
**最后更新**: 2025-01-14
**用户偏好版本**: ✅

---

## 🎯 v1.1布局特点

v1.1布局算法是**用户偏好版本**，核心特点：

- ✅ **黄色理解节点在问题节点正下方**（垂直对齐）
- ✅ **水平偏移为0**（不向右偏移）
- ✅ **视觉清晰**（一眼看到问题-理解对应关系）

### v1.0 vs v1.1 对比

```
v1.0布局（已废弃）:
┌─────────┐
│ 材料节点 │──────→ ┌───────┐
└─────────┘         │ 问题1 │──────→ ┌─────────┐
                    └───────┘         │ 黄色理解 │
                                      └─────────┘
                    ┌───────┐
                    │ 问题2 │──────→ ┌─────────┐
                    └───────┘         │ 黄色理解 │
                                      └─────────┘

v1.1布局（当前）:
┌─────────┐
│ 材料节点 │──────→ ┌───────┐
└─────────┘         │ 问题1 │
                    └───┬───┘
                        ↓
                    ┌───────┐
                    │ 黄色  │  ← 正下方，水平对齐
                    │ 理解  │
                    └───────┘

                    ┌───────┐
                    │ 问题2 │
                    └───┬───┘
                        ↓
                    ┌───────┐
                    │ 黄色  │
                    │ 理解  │
                    └───────┘
```

---

## 📐 布局参数表

### 节点尺寸参数

| 参数名称 | 值 | 说明 | 使用场景 |
|---------|---|------|---------|
| `DEFAULT_NODE_WIDTH` | 400 | 默认节点宽度 | 材料节点、问题节点 |
| `DEFAULT_NODE_HEIGHT` | 300 | 默认节点高度 | 材料节点 |
| `QUESTION_NODE_HEIGHT` | 120 | 问题节点高度 | 子问题节点 |
| `YELLOW_NODE_WIDTH` | 350 | 黄色理解节点宽度 | 个人理解输出区 |
| `YELLOW_NODE_HEIGHT` | 150 | 黄色理解节点高度 | 个人理解输出区 |

### 间距参数

| 参数名称 | 值 | 说明 | 图示 |
|---------|---|------|-----|
| `HORIZONTAL_SPACING` | 450 | 材料到问题的水平间距 | `[材料] ←450px→ [问题]` |
| `VERTICAL_SPACING_BASE` | 380 | 问题+黄色组合的垂直间距 | 问题1底部到问题2顶部 |
| `YELLOW_OFFSET_X` | 0 | 黄色节点水平偏移 | ⭐ v1.1核心：水平对齐 |
| `YELLOW_OFFSET_Y` | 30 | 黄色节点垂直偏移 | 问题底部到黄色顶部 |
| `EXPLANATION_CHAIN_SPACING` | 80 | 解释节点链式展开间距 | 多个解释节点之间 |

### 计算公式

```python
# 问题节点位置
question_x = material_x + material_width + HORIZONTAL_SPACING
question_y = material_y + (existing_question_count * VERTICAL_SPACING_BASE)

# 黄色节点位置（v1.1核心公式）
yellow_x = question_x + YELLOW_OFFSET_X  # = question_x（水平对齐）
yellow_y = question_y + QUESTION_NODE_HEIGHT + YELLOW_OFFSET_Y

# 组合总高度
combo_height = QUESTION_NODE_HEIGHT + YELLOW_OFFSET_Y + YELLOW_NODE_HEIGHT
# 120 + 30 + 150 = 300px
```

---

## 🎨 视觉规范

### 颜色使用

| 节点类型 | 颜色代码 | 视觉颜色 | 含义 |
|---------|---------|---------|------|
| 材料节点 | 无 | 灰色（默认） | 原始学习材料 |
| 问题节点 | `"1"` | 🔴 红色 | 不理解/未通过 |
| 问题节点（通过后） | `"2"` | 🟢 绿色 | 完全理解/已通过 |
| 理解节点 | `"6"` | 🟡 黄色 | 个人理解输出区 |
| 解释笔记节点 | `"3"` | 🟣 紫色 | 补充解释（待检验） |

### 边的连接方式

```
材料 → 问题:
  from_side: "right"
  to_side: "left"

问题 → 黄色理解:
  from_side: "bottom"
  to_side: "top"

问题 → 解释笔记:
  from_side: "right"
  to_side: "left"
```

---

## 📏 完整布局示例

### 场景：一个材料节点，3个子问题

```
材料节点位置: (100, 200)
材料节点尺寸: 400 x 300

计算：
─────────────────────────────────────

问题1:
  x = 100 + 400 + 450 = 950
  y = 200 + (0 * 380) = 200
  尺寸: 400 x 120

黄色理解1:
  x = 950 + 0 = 950  ← 水平对齐！
  y = 200 + 120 + 30 = 350
  尺寸: 350 x 150

─────────────────────────────────────

问题2:
  x = 950
  y = 200 + (1 * 380) = 580
  尺寸: 400 x 120

黄色理解2:
  x = 950 + 0 = 950  ← 水平对齐！
  y = 580 + 120 + 30 = 730
  尺寸: 350 x 150

─────────────────────────────────────

问题3:
  x = 950
  y = 200 + (2 * 380) = 960
  尺寸: 400 x 120

黄色理解3:
  x = 950 + 0 = 950  ← 水平对齐！
  y = 960 + 120 + 30 = 1110
  尺寸: 350 x 150
```

### 视觉效果

```
     ┌─────────────┐
     │   材料节点   │ (100, 200)
     │   400x300   │
     └──────┬──────┘
            │
            │ 450px
            ↓
     ┌─────────────┐
     │   问题1     │ (950, 200)
     │   400x120   │
     └──────┬──────┘
            │ 30px
            ↓
     ┌────────────┐
     │  黄色理解1  │ (950, 350)  ← 水平对齐
     │  350x150   │
     └────────────┘

     ↓ 380px

     ┌─────────────┐
     │   问题2     │ (950, 580)
     │   400x120   │
     └──────┬──────┘
            │ 30px
            ↓
     ┌────────────┐
     │  黄色理解2  │ (950, 730)  ← 水平对齐
     │  350x150   │
     └────────────┘

     ↓ 380px

     ┌─────────────┐
     │   问题3     │ (950, 960)
     │   400x120   │
     └──────┬──────┘
            │ 30px
            ↓
     ┌────────────┐
     │  黄色理解3  │ (950, 1110) ← 水平对齐
     │  350x150   │
     └────────────┘
```

---

## 🔍 特殊场景处理

### 场景1：解释笔记的链式展开

当添加多个解释笔记（如口语化解释、对比表等）时：

```python
# 第1个解释节点
explanation1_x = question_x + 400 + EXPLANATION_CHAIN_SPACING
explanation1_y = question_y

# 第2个解释节点
explanation2_x = explanation1_x + 400 + EXPLANATION_CHAIN_SPACING
explanation2_y = question_y

# 依此类推...
```

**视觉效果**:
```
┌────────┐      ┌────────┐      ┌────────┐
│ 问题1  │─────→│口语化  │─────→│对比表  │
└────────┘  80px│解释    │  80px│        │
                └────────┘      └────────┘
```

### 场景2：Canvas边界处理

当节点接近Canvas边界时：

```python
# 检查是否超出边界（假设Canvas宽度限制为3000px）
MAX_CANVAS_WIDTH = 3000

if calculated_x + node_width > MAX_CANVAS_WIDTH:
    # 自动换行：将节点放到下一行
    calculated_x = base_x
    calculated_y += (max_node_height + 100)
```

**注意**: 此功能在v1.0暂未实现，但架构支持扩展

### 场景3：深度拆解（子问题的子问题）

```
材料节点 → 问题1 → 黄色理解1
              ↓
           子问题1.1 → 黄色理解1.1
              ↓
           子问题1.2 → 黄色理解1.2
```

布局策略：
- 子问题的子问题向右偏移 `HORIZONTAL_SPACING`
- 使用相同的垂直间距规则

---

## 📊 布局算法性能

### 时间复杂度

| 操作 | 复杂度 | 说明 |
|------|--------|------|
| 添加单个问题+黄色节点 | O(n) | n = 现有问题数量（需遍历边） |
| 添加n个问题 | O(n²) | 每次添加都要统计现有问题 |
| 优化版（批量添加） | O(n) | 一次统计，批量创建 |

### 空间占用估算

```
单个材料节点 + 5个子问题:
  宽度: 400 + 450 + 400 = 1250px
  高度: max(300, 5 * 380) = 1900px
  总面积: 1250 x 1900 = 2,375,000 px²

Canvas文件大小增长:
  每添加1个节点: ~200 bytes（JSON）
  5个问题 + 5个黄色 = 10个节点 = ~2KB
```

---

## ✅ 布局验证测试

### 单元测试用例

```python
def test_v11_layout_yellow_below_question():
    """验证v1.1布局：黄色节点在问题正下方"""
    # Arrange
    material_node = {"id": "m1", "x": 100, "y": 200, "width": 400, "height": 300}

    # Act
    question_pos = calculate_question_position(material_node, existing_count=0)
    yellow_pos = calculate_yellow_position(question_pos)

    # Assert
    assert question_pos["x"] == 550  # 100 + 400 + 50
    assert question_pos["y"] == 200

    # ⭐ 核心验证：水平对齐
    assert yellow_pos["x"] == question_pos["x"]  # 水平对齐！
    assert yellow_pos["y"] == question_pos["y"] + 120 + 30  # 在下方

def test_multiple_questions_vertical_spacing():
    """验证多个问题的垂直间距"""
    material_node = {"id": "m1", "x": 100, "y": 200, "width": 400, "height": 300}

    # 第1个问题
    q1_pos = calculate_question_position(material_node, existing_count=0)
    assert q1_pos["y"] == 200

    # 第2个问题
    q2_pos = calculate_question_position(material_node, existing_count=1)
    assert q2_pos["y"] == 200 + 380  # 580

    # 第3个问题
    q3_pos = calculate_question_position(material_node, existing_count=2)
    assert q3_pos["y"] == 200 + 2 * 380  # 960
```

### 视觉验证

1. 打开生成的Canvas文件
2. 检查黄色节点是否在问题节点正下方
3. 检查水平对齐（x坐标相同）
4. 检查垂直间距一致性

---

## 🔄 版本历史

### v1.0（已废弃）
- 黄色节点在问题节点右侧
- `YELLOW_OFFSET_X = 450`
- 用户反馈：不直观，难以看出对应关系

### v1.1（当前）
- ✅ 黄色节点在问题节点下方
- ✅ `YELLOW_OFFSET_X = 0`（水平对齐）
- ✅ 用户偏好版本
- ✅ 视觉清晰，易于理解

---

## 📞 布局调整建议

如果需要调整布局参数：

1. 修改 `docs/architecture/canvas-layout-v1.1.md` 的参数表
2. 修改 `canvas_utils.py` 的常量定义
3. 运行布局验证测试
4. 更新相关Story的Dev Notes

**⚠️ 不要直接修改硬编码的数值**，始终使用常量！

---

**文档版本**: v1.1
**最后更新**: 2025-01-14
**维护者**: Architect Agent

**相关文档**:
- [canvas-3-layer-architecture.md](canvas-3-layer-architecture.md) - 3层架构实现
- [coding-standards.md](coding-standards.md) - 编码规范
