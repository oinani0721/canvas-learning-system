# ADR-005: LangGraph Checkpointer 持久化方案

## 状态

**已接受** | 2025-11-23

## 背景

Canvas Learning System 使用 LangGraph StateGraph 编排多 Agent 学习流程（Epic 12）。LangGraph 的 Checkpointer 机制用于：

1. **会话状态持久化** - 用户中断学习后可恢复
2. **多线程隔离** - 不同 Canvas 文件的学习状态独立
3. **历史回溯** - 支持学习进度时间线查看
4. **错误恢复** - Agent 执行失败后可从检查点重试

### 当前约束

- 本项目是 **Obsidian 本地插件**，不应依赖外部数据库服务
- 用户数据应存储在 **Obsidian Vault** 中，便于备份/同步
- 需要支持 **并发学习会话**（多窗口操作）
- 敏感学习数据可能需要 **加密存储**

### LangGraph 提供的选项

| Checkpointer | 持久化 | 依赖 | 适用场景 |
|--------------|--------|------|----------|
| `InMemorySaver` | 内存 | 无 | 开发/测试 |
| `SqliteSaver` | SQLite文件 | sqlite3 | 本地应用 |
| `PostgresSaver` | PostgreSQL | psycopg | 服务端应用 |
| `AsyncPostgresSaver` | PostgreSQL | psycopg (async) | 高并发服务 |

## 决策

**采用 SqliteSaver 作为 Checkpointer 持久化方案**

### 实现细节

```python
# ✅ Verified from LangGraph Context7 (persistence.md, checkpoint-sqlite README)
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.serde.encrypted import EncryptedSerializer
import os

# 数据库存储在 Obsidian Vault 的 .canvas-learning/ 目录
VAULT_PATH = os.environ.get("OBSIDIAN_VAULT_PATH", ".")
DB_PATH = os.path.join(VAULT_PATH, ".canvas-learning", "checkpoints.db")

# 生产环境使用加密
if os.environ.get("CANVAS_ENCRYPT_STATE"):
    serde = EncryptedSerializer.from_pycryptodome_aes()  # 读取 LANGGRAPH_AES_KEY
    checkpointer = SqliteSaver.from_conn_string(DB_PATH, serde=serde)
else:
    checkpointer = SqliteSaver.from_conn_string(DB_PATH)

# 编译 StateGraph
graph = builder.compile(checkpointer=checkpointer)

# 每个 Canvas 文件使用独立的 thread_id
config = {
    "configurable": {
        "thread_id": f"canvas:{canvas_path}",
        "checkpoint_ns": ""
    }
}
```

### Thread ID 命名规范

```python
# Canvas 学习会话
thread_id = f"canvas:{canvas_path}"

# 复习会话
thread_id = f"review:{concept_id}:{timestamp}"

# 并行处理任务
thread_id = f"parallel:{task_id}:{group_id}"
```

## 理由

### 为什么选择 SqliteSaver

1. **零外部依赖**
   - 不需要 PostgreSQL 服务
   - Python 标准库自带 sqlite3
   - 用户无需额外配置

2. **与 Obsidian Vault 集成**
   - 数据库文件存储在 Vault 目录
   - 随 Vault 一起备份/同步
   - 支持 .gitignore 排除

3. **并发支持**
   - SQLite WAL 模式支持并发读
   - 足以满足本地多窗口场景
   - 无需 PostgreSQL 的连接池管理

4. **加密选项**
   - 支持 AES 加密 (EncryptedSerializer)
   - 保护敏感学习数据
   - 密钥通过环境变量管理

### 为什么不选择其他方案

**InMemorySaver**
- ❌ 应用重启后状态丢失
- ❌ 无法跨会话恢复
- ✅ 仅用于单元测试

**PostgresSaver**
- ❌ 需要安装/运行 PostgreSQL 服务
- ❌ 增加用户配置复杂度
- ❌ Obsidian 本地应用不需要
- ✅ 适合 SaaS 多租户场景

**自定义 FileCheckpointer**
- ❌ 需要自行实现序列化/并发控制
- ❌ 维护成本高
- ❌ 无官方支持

## 影响

### 正面影响

1. **简化部署** - 用户安装插件即可使用，无需数据库
2. **数据可移植** - SQLite 文件可直接复制/备份
3. **调试友好** - 可用 SQLite 工具直接查看状态
4. **性能足够** - 本地单用户场景无瓶颈

### 负面影响

1. **写入并发限制** - SQLite 写锁，高并发写入会排队
2. **数据库文件增长** - 需定期清理历史检查点
3. **迁移成本** - 如未来需要云同步，需迁移方案

### 缓解措施

```python
# 定期清理过期检查点（保留最近7天）
async def cleanup_old_checkpoints(checkpointer: SqliteSaver, days: int = 7):
    cutoff = datetime.now() - timedelta(days=days)
    # 实现清理逻辑
    pass

# 数据库文件大小监控
def get_db_size_mb(db_path: str) -> float:
    return os.path.getsize(db_path) / (1024 * 1024)
```

## 替代方案（未来考虑）

如果项目扩展到云端场景，可考虑：

1. **Supabase PostgreSQL** - 免费 tier 足够小团队
2. **LangGraph Cloud** - 官方托管服务
3. **SQLite + Litestream** - SQLite 实时备份到 S3

## 实现计划

| 阶段 | 内容 | Story |
|------|------|-------|
| Phase 1 | 基础 SqliteSaver 集成 | Story 12.5 |
| Phase 2 | 加密支持 | Story 12.5 |
| Phase 3 | 检查点清理机制 | Story 12.13 |
| Phase 4 | 状态查看 UI | Story 13.x |

## 参考资料

- [LangGraph Persistence Concepts](https://github.com/langchain-ai/langgraph/blob/main/docs/docs/concepts/persistence.md)
- [LangGraph Checkpoint SQLite](https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint-sqlite/README.md)
- [LangGraph Add Memory How-To](https://github.com/langchain-ai/langgraph/blob/main/docs/docs/how-tos/memory/add-memory.md)
- ADR-003: Agentic RAG Architecture (相关)

---

**作者**: Winston (Architect Agent)
**审核**: 待定
**批准**: 待定
