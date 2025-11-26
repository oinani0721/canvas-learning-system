# Create JSON Schemas Task

**Purpose**: 创建经过严格验证的JSON Schema文件
**Output**: `specs/data/{schema-name}.schema.json`

---

## 🔴 SDD验证协议 (Anti-Hallucination Critical)

### 强制验证规则

1. **每个Schema必须验证格式规范**
   - 使用Context7查询JSON Schema Draft-07规范
   - 验证$schema、type、properties等属性

2. **每个字段必须有实际来源**
   - 来自实际文件格式分析 (如.canvas文件)
   - 来自官方文档规范
   - 来自PRD需求定义

3. **禁止假设任何字段类型或枚举值**
   - 枚举值必须从实际样本或官方文档提取
   - 不确定的部分必须询问用户

---

## 执行步骤

### Step 1: 识别Schema需求

**读取文件**:
- PRD文档 (确定需要哪些数据模型)
- 相关架构文档
- **实际样本文件** (关键！)

```
🔴 Quality Gate:
- 如果是外部格式(如Obsidian Canvas) → 必须读取实际文件样本
- 如果找不到样本 → 查询官方文档
```

### Step 2: 查询技术规范

**JSON Schema格式查询**:
```
Context7: JSON Schema Draft-07
Topics: type, properties, required, enum, allOf, if/then
```

**外部格式查询** (如适用):
```
# Obsidian Canvas
WebFetch: https://jsoncanvas.org/spec/1.0/

# 其他格式
查询相应官方文档
```

### Step 3: 分析实际样本

**对于外部格式，必须分析实际文件**:

```python
# 示例: 分析Canvas文件
1. Glob("**/*.canvas") 找到样本文件
2. Read 至少3个不同的样本
3. 提取所有出现的字段
4. 记录字段类型和可能的值
```

**输出分析结果**:
```markdown
## 实际文件分析: {文件类型}

**样本文件**:
- sample1.canvas
- sample2.canvas
- sample3.canvas

**发现的字段**:
| 字段 | 类型 | 示例值 | 必填 |
|------|------|--------|------|
| id | string | "b33c50660173e5d3" | ✅ |
| type | enum | "text", "file" | ✅ |
| color | enum | "1", "2", "3", "4", "5", "6" | ❌ |

**官方文档验证**: {URL}
```

### Step 4: 增量创建模式 (Elicit = True)

**对每个Schema，向用户确认**:

```markdown
## Schema确认: {Schema名称}

**需求来源**: PRD {引用}
**格式来源**: {官方文档URL或样本分析}

**字段定义**:

| 字段 | 类型 | 必填 | 来源 |
|------|------|------|------|
| id | string | ✅ | 样本分析 + 官方文档 |
| type | enum["text","file","group","link"] | ✅ | JSON Canvas Spec 1.0 |
| color | enum["1"-"6"] | ❌ | JSON Canvas Spec 1.0 |

**条件逻辑**:
- 当 type="text" 时，text字段必填
- 当 type="file" 时，file字段必填

❓ **请确认**:
1. 字段列表是否完整？
2. 类型定义是否正确？
3. 必填字段是否正确标记？

(输入 'y' 确认, 或提供修改意见)
```

### Step 5: 添加x-source-verification标记 (MANDATORY)

**🔴 强制要求**: 每个JSON Schema必须包含`x-source-verification`元数据，用于追踪验证来源。

**标记格式**:
```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "x-source-verification": {
    "verified_at": "YYYY-MM-DDTHH:MM:SSZ",
    "sources": [
      {
        "type": "context7",
        "library_id": "/jsoncanvas/spec",
        "topic": "node structure"
      },
      {
        "type": "official_doc",
        "url": "https://jsoncanvas.org/spec/1.0/"
      },
      {
        "type": "sample_analysis",
        "files": ["sample1.canvas", "sample2.canvas"]
      }
    ]
  }
}
```

**Quality Gate**:
- 缺少x-source-verification → Schema创建失败
- 外部格式无sample_analysis → Schema创建失败
- 无效的library_id格式 → Schema创建失败

### Step 6: 生成Schema并标注来源

**输出格式**:
```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "$id": "https://canvas-learning-system.com/schemas/{name}.schema.json",
  "title": "{Schema名称}",
  "description": "{描述}. Verified from {来源URL}",
  "x-source-verification": {
    "verified_at": "{ISO8601时间戳}",
    "sources": [
      {"type": "context7", "library_id": "{Context7 ID}", "topic": "{查询主题}"},
      {"type": "official_doc", "url": "{官方文档URL}"}
    ]
  },
  "type": "object",
  "properties": {
    "fieldName": {
      "type": "string",
      "description": "{描述} (Source: {来源})"
    }
  }
}
```

---

## 🔴 Anti-Hallucination Quality Gates

| 检查项 | 要求 | 失败操作 |
|--------|------|----------|
| JSON Schema语法 | 必须经Context7验证 | HALT |
| 外部格式字段 | 必须分析实际样本或查官方文档 | HALT |
| 枚举值 | 必须有实际来源，禁止臆测 | HALT |
| 用户确认 | 每个Schema必须用户确认 | HALT |
| 示例有效性 | 示例必须来自实际文件 | 警告并修复 |

---

## 增量模式交互模板

```markdown
---
## Schema创建进度: {当前} / {总数}

### 当前Schema: {Schema名称}

**来源分析**:
- 实际样本: {已分析的文件}
- 官方文档: {URL}

**字段验证状态**:
- [x] id: string - 来自样本分析
- [x] type: enum - 来自官方文档
- [ ] customField: ? - 需要确认

**Schema预览**:
```json
{JSON预览}
```

**需要您确认**:
1. 以上字段是否正确反映了实际需求？
2. 是否有遗漏的字段？
3. 枚举值是否完整？

→ 输入确认或修改意见:
---
```

---

## 特别说明: 项目语义映射

当Schema同时涉及外部格式和项目语义时，必须明确区分：

```json
{
  "color": {
    "type": "string",
    "enum": ["1", "2", "3", "4", "5", "6"],
    "description": "颜色代码 (Verified from {官方URL}). 官方色值: 1=红, 2=橙, 3=黄, 4=绿, 5=青, 6=紫. 项目语义映射: {项目特定映射}"
  }
}
```

---

## 完成检查清单

- [ ] 所有外部格式都分析了实际样本文件
- [ ] 所有Schema都经过Context7/官方文档验证
- [ ] 每个字段都有来源标注
- [ ] 用户确认了所有Schema
- [ ] 示例数据来自实际文件
- [ ] 项目语义映射已明确说明
- [ ] **x-source-verification字段已添加** (Section 16.5.7 Required)
- [ ] **library_id格式正确** (/org/project)
- [ ] **verified_at时间戳已记录**
- [ ] **外部格式包含sample_analysis**
