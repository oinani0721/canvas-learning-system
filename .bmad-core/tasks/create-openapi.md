# Create OpenAPI Specification Task

**Purpose**: 创建经过严格验证的OpenAPI规范文件
**Output**: `specs/api/{api-name}.openapi.yml`

---

## 🔴 SDD验证协议 (Anti-Hallucination Critical)

### 强制验证规则

1. **每个端点定义前必须验证技术格式**
   - 使用Context7查询OpenAPI 3.0规范语法
   - 验证HTTP方法、路径参数、请求体、响应格式

2. **每个数据模型必须有来源标注**
   - 来自PRD的需求定义
   - 来自架构文档的设计
   - 来自官方规范的格式要求

3. **禁止假设或臆测任何字段**
   - 所有字段必须有明确来源
   - 不确定的部分必须询问用户

---

## 执行步骤

### Step 1: 加载上下文

**必须读取的文件**:
- PRD文档 (从core-config.yaml获取路径)
- 相关Epic文档
- 现有架构文档

```
🔴 Quality Gate: 如果找不到PRD → HALT并通知用户
```

### Step 2: 查询技术规范 (Context7/Skill)

**强制查询**:
```
Context7: /oai/openapi-specification
Topics: schema object, paths, components, requestBody, responses
```

**记录验证来源**:
```yaml
# 每个定义必须标注来源
# Example:
paths:
  /api/v1/canvas/{name}:
    get:
      # Source: PRD Epic 11 Story 11.1
      # Format: Verified from Context7 /oai/openapi-specification
```

### Step 3: 增量创建模式 (Elicit = True)

**对每个API端点，向用户确认**:

```markdown
## 端点确认: POST /api/v1/canvas/{name}/nodes

**来源**: PRD Epic 11 - Story 11.2
**功能**: 创建Canvas节点

**请求体Schema**:
- id: string (必填)
- type: enum["text", "file", "group", "link"]
- x, y: integer (必填)
- color: enum["1"-"6"]

**响应Schema**:
- 201: NodeCreated
- 400: ValidationError
- 404: CanvasNotFound

❓ **请确认**:
1. 请求体字段是否正确？
2. 响应状态码是否完整？
3. 是否需要添加其他字段？

(输入 'y' 确认, 或提供修改意见)
```

### Step 4: 验证与交叉检查

**对每个Schema组件**:

1. **字段类型验证**
   - 使用Context7验证OpenAPI类型语法
   - 确保format、pattern等属性正确

2. **引用验证**
   - 所有$ref引用指向存在的组件
   - 避免循环引用

3. **示例验证**
   - 每个Schema提供有效示例
   - 示例必须符合定义的约束

### Step 5: 添加x-source-verification标记 (MANDATORY)

**🔴 强制要求**: 每个OpenAPI文件必须包含`x-source-verification`元数据，用于追踪验证来源。

**标记格式**:
```yaml
info:
  title: {API名称}
  version: {版本}
  x-source-verification:
    verified_at: "{YYYY-MM-DDTHH:MM:SSZ}"
    format_source:
      type: context7
      library_id: "/oai/openapi-specification"
      topic: "schema object, paths, components"
    business_source:
      prd_version: "{PRD版本号}"
      epic: "{Epic编号}"
      story_refs: ["{Story引用列表}"]
```

**Quality Gate**:
- 缺少x-source-verification → 文件创建失败
- 无效的library_id格式 → 文件创建失败
- 缺少verified_at时间戳 → 文件创建失败

### Step 6: 最终输出

**输出格式**:
```yaml
openapi: 3.0.3
info:
  title: {API名称}
  description: |
    {描述}

    ## 验证来源
    - OpenAPI格式: Context7 /oai/openapi-specification
    - 业务需求: PRD {版本}
    - 架构设计: {架构文档}
  version: {版本}
  x-source-verification:
    verified_at: "{ISO8601时间戳}"
    format_source:
      type: context7
      library_id: "/oai/openapi-specification"
    business_source:
      prd_version: "{版本}"
      epic: "{Epic编号}"

# ... 其余内容
```

---

## 🔴 Anti-Hallucination Quality Gates

| 检查项 | 要求 | 失败操作 |
|--------|------|----------|
| OpenAPI版本语法 | 必须经Context7验证 | HALT |
| 每个端点来源 | 必须有PRD/Epic引用 | HALT |
| 每个Schema字段 | 必须有来源标注 | HALT |
| 用户确认 | 关键端点必须用户确认 | HALT |
| 示例有效性 | 示例必须符合Schema | 警告并修复 |

---

## 增量模式交互模板

```markdown
---
## OpenAPI创建进度: {当前端点} / {总端点数}

### 当前端点: {HTTP方法} {路径}

**需求来源**: {PRD/Epic引用}

**技术验证**:
- [ ] 路径参数格式已验证 (Context7)
- [ ] 请求体Schema已验证
- [ ] 响应格式已验证

**Schema预览**:
```yaml
{YAML预览}
```

**需要您确认**:
1. 字段定义是否正确？
2. 是否遗漏了必要字段？
3. 响应状态码是否完整？

→ 输入确认或修改意见:
---
```

---

## 完成检查清单

- [ ] 所有端点都有PRD来源引用
- [ ] 所有Schema都经过Context7格式验证
- [ ] 关键端点已获得用户确认
- [ ] 输出文件包含验证来源说明
- [ ] 示例数据有效且符合Schema
- [ ] **x-source-verification字段已添加** (Section 16.5.6 Required)
- [ ] **library_id格式正确** (/org/project)
- [ ] **verified_at时间戳已记录**
