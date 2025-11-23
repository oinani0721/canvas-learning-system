# `/learning start` 启动验证检查清单

**版本**: 1.0
**最后更新**: 2025-10-30
**用途**: 验证`/learning start`命令真实启动记忆系统（修复错误#9）

---

## 📚 相关文档

- **命令文档**: [.claude/commands/learning.md](../.claude/commands/learning.md) - `/learning`命令完整使用说明
- **错误日志**: [CANVAS_ERROR_LOG.md](../CANVAS_ERROR_LOG.md) - 错误#9的详细记录和修复说明
- **Story 10.10**: [docs/stories/10.10.story.md](stories/10.10.story.md) - 修复核心逻辑
- **Story 10.11**: [docs/stories/10.11.story.md](stories/10.11.story.md) - 实现诚实状态报告和优雅降级
- **Story 10.12**: [docs/stories/10.12.story.md](stories/10.12.story.md) - 添加启动验证测试和文档更新

---

## 📋 启动前检查清单

### 系统依赖检查

- [ ] **Neo4j数据库**
  ```bash
  neo4j status
  # 期望输出: Neo4j is running
  ```

- [ ] **MCP服务器**
  ```bash
  # 在Claude Code中测试MCP工具
  mcp__graphiti-memory__list_memories()
  # 期望: 返回记忆列表或空列表（不抛出异常）
  ```

- [ ] **Python依赖**
  ```bash
  pip list | grep -E "neo4j|loguru|graphiti"
  # 期望: 显示已安装的库版本
  ```

### 环境变量检查

- [ ] **NEO4J_PASSWORD**
  ```bash
  echo $NEO4J_PASSWORD
  # 期望: 显示Neo4j密码（非空）
  ```

---

## 🚀 启动后验证步骤

### Step 1: 执行启动命令

```bash
/learning start "tests/fixtures/test.canvas"
```

**期望输出示例** (所有系统成功):
```
📊 学习会话启动报告

✅ Graphiti知识图谱: 运行中
   Memory ID: mem_20251030_185905_3321
   ...

✅ 时序记忆管理器: 运行中
   ...

✅ 语义记忆管理器: 运行中
   ...

✅ 会话已启动，3/3 记忆系统正常运行
```

### Step 2: 检查会话JSON文件

```bash
# 找到最新的会话JSON
ls -lt .learning_sessions/*.json | head -1

# 查看内容
cat .learning_sessions/session_*.json
```

**验证要点**:
- [ ] `session_id`字段存在
- [ ] `memory_systems`字段存在，包含`graphiti`、`temporal`、`semantic`
- [ ] 每个系统有`status`字段，值为`"running"`或`"unavailable"`
- [ ] `"running"`状态有`initialized_at`时间戳
- [ ] `"unavailable"`状态有`error`和`attempted_at`字段

### Step 3: 验证Graphiti真实记录

```bash
# 使用MCP工具查询Graphiti记忆
mcp__graphiti-memory__search_memories(query="开始学习会话")
```

**期望**:
- [ ] 返回包含会话启动记录的结果
- [ ] `memory_id`与会话JSON中的一致

### Step 4: 检查日志文件

```bash
# 查看最新日志
cat .ai/debug-log.md | tail -50
```

**验证要点**:
- [ ] 如果有系统启动失败，日志中有详细错误信息
- [ ] 日志包含时间戳和错误类型
- [ ] 没有虚假的成功日志（如果系统实际失败）

---

## 🧪 降级场景测试

### 场景1: Neo4j不可用

**前置条件**: 停止Neo4j数据库
```bash
neo4j stop
```

**执行**: 启动学习会话
```bash
/learning start "test.canvas"
```

**预期行为**:
- [ ] Graphiti状态为`"unavailable"`
- [ ] 错误消息包含"Neo4j连接失败"
- [ ] Temporal和Semantic仍然尝试启动
- [ ] 如果其他系统成功，会话仍然标记为启动成功

### 场景2: MCP服务器不可用

**前置条件**: 重启Claude Code但不连接MCP服务器

**预期行为**:
- [ ] Graphiti和Semantic状态为`"unavailable"`
- [ ] 错误消息包含"MCP服务器不可用"或"MCP工具未加载"
- [ ] Temporal可能成功（如果使用本地SQLite模式）

### 场景3: 所有系统不可用

**前置条件**: Neo4j停止 + MCP服务器不可用

**预期行为**:
- [ ] 所有系统状态为`"unavailable"`
- [ ] 状态报告显示"0/3 记忆系统可用"
- [ ] 提供"基础功能模式"建议
- [ ] 会话JSON仍然创建（记录失败原因）

---

## 🔍 常见问题 (FAQ)

### Q1: 启动报告显示"运行中"，但如何确认真实启动？

**A**: 执行以下验证步骤：
1. 检查会话JSON中的`memory_id`或`session_record_id`（非空）
2. 使用MCP工具查询Graphiti记忆，验证记录存在
3. 检查`.ai/debug-log.md`，确保没有错误日志

### Q2: 如何区分真实启动和虚假启动？

**A**: 真实启动的特征：
- ✅ 会话JSON包含`initialized_at`时间戳
- ✅ Graphiti有`memory_id`字段（非占位符）
- ✅ 可以通过MCP工具查询到对应的记忆记录
- ✅ 日志中有"初始化成功"消息

虚假启动的特征（错误#9）：
- ❌ 只有静态JSON文件，没有`memory_id`
- ❌ MCP工具查询不到任何记录
- ❌ 日志中没有真实的初始化消息

### Q3: 部分系统失败是否影响学习？

**A**: 不会影响核心学习功能。Canvas学习系统的核心功能（拆解、解释、评分）不依赖记忆系统。记忆系统主要用于：
- 记录学习历程（可选）
- 跨Canvas知识关联（可选）
- 学习分析和推荐（可选）

即使所有记忆系统不可用，您仍然可以使用Canvas进行学习。

### Q4: 如何手动验证TemporalMemoryManager是否真实初始化？

**A**: 检查以下指标：
1. 会话JSON中`temporal`有`session_record_id`字段
2. 如果使用SQLite，检查数据库文件是否存在：
   ```bash
   ls memory_system/temporal_memory.db
   ```
3. 查询SQLite数据库：
   ```bash
   sqlite3 memory_system/temporal_memory.db "SELECT * FROM sessions;"
   ```

---

## 📊 验证通过标准

当满足以下所有条件时，`/learning start`真实启动验证通过：

- [ ] 启动报告显示至少1个系统"运行中"
- [ ] 会话JSON格式正确，包含所有必需字段
- [ ] Graphiti记忆可以通过MCP工具查询到
- [ ] 降级场景测试通过（某系统失败不影响其他系统）
- [ ] 日志中没有虚假的成功消息
- [ ] 会话JSON与实际系统状态一致

---

**文档版本**: 1.0
**维护者**: SM Agent (Bob)
**相关Story**: Story 10.10, 10.11, 10.12
