# README更新指南 - 技术验证部分

**文件**: README.md
**更新日期**: 2025-11-13
**更新原因**: 添加技术验证协议说明

---

## 插入位置

在README.md的第12行之后（v2.0重大升级section之前）插入以下内容：

**当前内容**:
```markdown
> **"通过输出倒逼输入,通过检验暴露盲区" - 费曼学习法的数字化实践**

## 🚀 v2.0 重大升级
```

**修改为**:
```markdown
> **"通过输出倒逼输入,通过检验暴露盲区" - 费曼学习法的数字化实践**

## 🔍 技术验证要求 (Technical Verification)

### ⚠️ 重要：零幻觉政策 (Zero Hallucination Policy)

**v1.2新增** (2025-11-13): 本项目采用**学术论文级别的引用标准**进行开发。所有技术实现必须可追溯到官方文档。

### 技术栈文档来源

#### 通过Context7 MCP访问
- **FastAPI**: `/websites/fastapi_tiangolo` (22,734 snippets)
- **Neo4j Cypher**: `/websites/neo4j_cypher-manual_25` (2,032 snippets)
- **Neo4j Operations**: `/websites/neo4j_operations-manual-current` (4,940 snippets)

#### 通过本地Skills访问
- **LangGraph**: `@langgraph` (952页完整文档)
- **Graphiti**: `@graphiti` (完整框架文档)
- **Obsidian Canvas**: `@obsidian-canvas` (Canvas API文档)

### 开发流程

#### SM Agent编写Story时
1. 识别Story涉及的技术栈
2. 查询Context7或激活本地Skill
3. 在Story中添加"技术验证"section
4. 记录所有查询结果和文档引用

#### Dev Agent开发时
1. 阅读Story的"技术验证"section
2. 开发前查询官方文档确认API用法
3. 在代码中添加文档来源注释
4. 执行UltraThink检查点避免幻觉

**详细流程请参见**:
- 技术验证协议: `docs/prd/SECTION-1X-TECHNICAL-VERIFICATION-PROTOCOL.md`
- Epic 0详情: `docs/prd/EPIC-0-TECHNICAL-DOCUMENTATION-SETUP.md`
- 示例Story: `docs/examples/story-12-1-verification-demo.md` (待Epic 0创建)

---

## 🚀 v2.0 重大升级
```

---

## 完整的新增内容（Copy-Paste Ready）

```markdown
## 🔍 技术验证要求 (Technical Verification)

### ⚠️ 重要：零幻觉政策 (Zero Hallucination Policy)

**v1.2新增** (2025-11-13): 本项目采用**学术论文级别的引用标准**进行开发。所有技术实现必须可追溯到官方文档。

### 技术栈文档来源

#### 通过Context7 MCP访问
- **FastAPI**: `/websites/fastapi_tiangolo` (22,734 snippets)
- **Neo4j Cypher**: `/websites/neo4j_cypher-manual_25` (2,032 snippets)
- **Neo4j Operations**: `/websites/neo4j_operations-manual-current` (4,940 snippets)

#### 通过本地Skills访问
- **LangGraph**: `@langgraph` (952页完整文档)
- **Graphiti**: `@graphiti` (完整框架文档)
- **Obsidian Canvas**: `@obsidian-canvas` (Canvas API文档)

### 开发流程

#### SM Agent编写Story时
1. 识别Story涉及的技术栈
2. 查询Context7或激活本地Skill
3. 在Story中添加"技术验证"section
4. 记录所有查询结果和文档引用

#### Dev Agent开发时
1. 阅读Story的"技术验证"section
2. 开发前查询官方文档确认API用法
3. 在代码中添加文档来源注释
4. 执行UltraThink检查点避免幻觉

**详细流程请参见**:
- 技术验证协议: `docs/prd/SECTION-1X-TECHNICAL-VERIFICATION-PROTOCOL.md`
- Epic 0详情: `docs/prd/EPIC-0-TECHNICAL-DOCUMENTATION-SETUP.md`
- 示例Story: `docs/examples/story-12-1-verification-demo.md` (待Epic 0创建)

---
```

---

## 验收标准

- [ ] README.md已插入新的section
- [ ] 插入位置正确（在v2.0 section之前）
- [ ] 格式与现有README保持一致
- [ ] 所有链接可访问

---

**更新责任人**: PM Agent (Story 0.4)
**预计时间**: 10分钟
