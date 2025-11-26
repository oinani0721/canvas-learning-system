# SDD验证检查清单

**Purpose**: 验证任何SDD规范(OpenAPI/JSON Schema)的准确性和完整性
**使用时机**:
- 创建新的SDD规范后
- 修改现有SDD规范后
- Code Review涉及SDD时

---

## 🔴 强制验证项 (Blocking)

### 1. 来源验证

- [ ] **每个字段都有明确来源标注**
  - PRD需求引用
  - 架构文档引用
  - 官方文档URL

- [ ] **外部格式已查询官方规范**
  - 示例: Obsidian Canvas → https://jsoncanvas.org/spec/1.0/
  - 示例: OpenAPI → Context7 /oai/openapi-specification

- [ ] **枚举值来自实际样本或官方文档**
  - 禁止臆测枚举值
  - 必须有样本文件或文档支持

### 2. 技术格式验证

- [ ] **OpenAPI语法正确**
  - openapi版本声明 (3.0.x 或 3.1.x)
  - paths结构正确
  - components/schemas引用正确

- [ ] **JSON Schema语法正确**
  - $schema声明 (draft-07或更高)
  - type声明正确
  - required数组正确

- [ ] **$ref引用验证**
  - 所有$ref指向存在的定义
  - 无循环引用

### 3. 用户确认

- [ ] **关键端点/Schema已获用户确认**
  - 使用增量模式逐个确认
  - 记录用户反馈和修改

---

## ⚠️ 推荐验证项 (Warning)

### 4. 示例验证

- [ ] **示例数据有效**
  - 符合定义的类型
  - 符合定义的约束(pattern, enum等)
  - 来自实际文件(非臆造)

- [ ] **示例覆盖边界情况**
  - 必填字段示例
  - 可选字段示例
  - 条件字段示例

### 5. 文档完整性

- [ ] **每个字段都有description**
  - 说明用途
  - 说明来源

- [ ] **验证来源记录在文档头部**
  ```yaml
  info:
    description: |
      ## 验证来源
      - 格式规范: {URL}
      - 需求来源: PRD {版本}
  ```

### 6. 一致性检查

- [ ] **命名风格一致**
  - camelCase或snake_case统一
  - 术语统一

- [ ] **类型使用一致**
  - 相同概念使用相同类型
  - 避免string/number混用

---

## 🔍 验证流程

### Step 1: 自动化检查

```bash
# OpenAPI语法检查
npx @redocly/openapi-cli lint specs/api/*.yml

# JSON Schema语法检查
npx ajv validate -s specs/data/*.schema.json
```

### Step 2: 来源追溯

对每个定义，回答：

1. **这个字段从哪里来？**
   - PRD Section X.Y
   - 架构文档 Section Z
   - 官方规范 URL

2. **这个枚举值完整吗？**
   - 分析了多少样本？
   - 官方文档是否列出所有可能值？

3. **这个类型正确吗？**
   - 实际文件中的类型是什么？
   - 是否与官方规范一致？

### Step 3: 交叉验证

- [ ] **Schema与实际文件对比**
  ```python
  # 读取实际文件
  actual = json.load(open("sample.canvas"))
  # 验证所有字段都在Schema中定义
  for field in actual["nodes"][0]:
      assert field in schema["properties"]
  ```

- [ ] **端点与代码对比**
  - 路由定义与OpenAPI一致
  - 参数类型与OpenAPI一致

---

## 📋 检查报告模板

```markdown
# SDD验证报告

**文件**: {文件路径}
**验证日期**: {日期}
**验证人**: {Agent/人员}

## 验证结果

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 来源标注 | ✅/❌ | {说明} |
| 格式语法 | ✅/❌ | {说明} |
| 枚举完整 | ✅/❌ | {说明} |
| 示例有效 | ✅/❌ | {说明} |
| 用户确认 | ✅/❌ | {说明} |

## 发现的问题

1. {问题描述}
   - 位置: {行号/字段}
   - 修复建议: {建议}

## 验证来源

- OpenAPI规范: Context7 /oai/openapi-specification
- JSON Schema: Context7 JSON Schema Draft-07
- 外部格式: {URL}
- 实际样本: {文件列表}
```

---

## 🚫 常见幻觉模式 (Anti-Patterns)

### 1. 臆测枚举值
```json
// ❌ 错误: 假设颜色只有5个
"color": { "enum": ["1", "2", "3", "5", "6"] }

// ✅ 正确: 从官方文档获取完整列表
"color": {
  "enum": ["1", "2", "3", "4", "5", "6"],
  "description": "Verified from JSON Canvas Spec 1.0"
}
```

### 2. 假设ID格式
```json
// ❌ 错误: 假设是UUID格式
"id": { "pattern": "^[a-f0-9]{8}-...$" }

// ✅ 正确: 从实际文件分析
"id": {
  "pattern": "^[a-f0-9]+$",
  "description": "Hex string (from sample analysis)"
}
```

### 3. 遗漏条件逻辑
```json
// ❌ 错误: 所有字段都标记必填
"required": ["id", "type", "text", "file", "url"]

// ✅ 正确: 使用条件逻辑
"allOf": [{
  "if": { "properties": { "type": { "const": "text" } } },
  "then": { "required": ["text"] }
}]
```

---

## ✅ 验证通过标准

SDD规范必须满足以下条件才能标记为"已验证":

1. **所有🔴强制项通过**
2. **至少80%推荐项通过**
3. **无已知幻觉模式**
4. **用户已确认关键定义**
5. **验证来源已记录在文档中**
