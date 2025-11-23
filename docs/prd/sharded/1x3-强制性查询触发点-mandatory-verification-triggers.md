# 1.X.3 强制性查询触发点 (Mandatory Verification Triggers)

### 🔴 Level 1: SM Agent编写Story时 (CRITICAL)

**触发条件**: 编写任何包含技术实现细节的Story

**强制操作**:
1. **识别技术栈**: 列出Story涉及的所有技术（FastAPI、Neo4j、LangGraph等）
2. **查询官方文档**:
   - 使用Context7查询相关API/配置
   - 或激活本地Skill (`@langgraph`, `@obsidian-canvas`)
3. **在Story中引用**: 添加"技术验证"section（见1.X.5模板）

**示例Story片段**:
```markdown
### Story 11.2: 实现Canvas节点查询API
