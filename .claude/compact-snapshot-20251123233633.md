# Context Snapshot Before Compression

**Generated**: 2025-11-23 23:36:33
**Filled By**: PowerShell PreCompact hook (automated)
**Trigger**: auto
**Session ID**: 18cfc2cf-9af3-4a6e-8843-86110ca5cceb
**Valid For**: 2 hours
**Status**: 鉁?COMPLETE

---

## Current BMad Status

**Active Agent**: none
**Executing Function**: extracted from conversation history
**Core Content**:
**Current Epic/Story**: none

**Relevant Files**:
- `C:\Users\ROG\托福\Canvas\docs\architecture\decisions\ADR-007-CACHING-STRATEGY-TIERED.md`

**Next Actions**:
- 鈴?Verify PowerShell transcript parsing works correctly
- 鈴?Test fifth /compact with automated snapshot fill
- 鈴?Update COMPRESSION_WORKAROUND_README.md with real solution

**Key Technical Decisions**:
1. **PowerShell reads transcript_path directly**: PreCompact hook receives transcript_path via stdin, reads JSONL file, and extracts conversation history automatically. (Rejected: Waiting for Claude to fill snapshot - timing issue discovered)
2. **Snapshot filled immediately by PowerShell**: No dependency on Claude, no timing issues. PowerShell completes all work before compression executes. (Rejected: SNAPSHOT_FILL_INSTRUCTION approach - compression executes too fast)
3. **JSONL parsing in PowerShell**: Parse each line as JSON, extract user/assistant messages, build conversation history array. (Rejected: Complex regex parsing)

---

## Last 20 Conversation Turns

### Turn 1: Assistant

✅ **ADR-006 已创建**

**文件**: `docs/architecture/decisions/ADR-006-REALTIME-COMMUNICATION-SSE-HTTP.md`

---

## 决策摘要

| 项目 | 决策 |
|------|------|
| **方案** | SSE + HTTP |
| **推送机制** | Server-Sent Events (服务端 → 客户端) |
| **操作机制** | HTTP POST (客户端 → 服务端) |
| **推送间隔** | 500ms (进度) / 5s (监控指标) |

---

## 核心端点

| 类型 | 端点 | 用途 |
|------|------|------|
| SSE | `GET /events/{task_id}` | 任务进度推送 |
| SSE | `GET /events/metrics/stream` | 性能指标推送 |
| HTTP | `POST /tasks/{task_id}/cancel` | 取消任务 |

---

## 事件类型

```typescript
// 4 种标准事件
- progress   // 进度更新
- completed  // 任务完成
- cancelled  // 任务取消
- error      // 错误发生
```

---

## 关键实现

1. **后端**: FastAPI + sse-starlette
2. **前端**: 原生 EventSource API
3. **状态管理**: 内存字典 (生产环境可换 Redis)

---

## ADR 进度

| ADR | 状态 | 主题 |
|-----|------|------|
| ADR-001 | ✅ 已存在 | 本地模型优先策略 |
| ADR-002 | ✅ 已存在 | 向量数据库选型 |
| ADR-003 | ✅ 已存在 | Agentic RAG架构 |
| ADR-004 | ✅ 已存在 | GraphRAG评估 |
| ADR-005 | ✅ 刚创建 | LangGraph Checkpointer |
| **ADR-006** | ✅ 刚创建 | 实时通信方案 |
| ADR-007 | ⏳ 待创建 | 缓存策略 |

---

是否继续创建 **ADR-007: 缓存策略**？或者分析其他技术选型？

### Turn 2: User

创建 ADR-007: 缓存策略，给我提供技术选型方案

### Turn 3: Assistant



### Turn 4: Assistant

## ADR-007: 缓存策略技术选型

### 缓存场景分析

| 场景 | 数据类型 | 大小 | 生命周期 | 访问频率 |
|------|----------|------|----------|----------|
| **LLM 响应** | 文本 | 1-10KB | 会话级 | 中 |
| **Embedding 向量** | float[] | 3KB/个 | 持久 | 高 |
| **记忆检索结果** | JSON | 5-50KB | 短期 | 高 |
| **Canvas 文件内容** | JSON | 10-500KB | 会话级 | 高 |
| **评分历史** | JSON | 1-5KB | 持久 | 低 |

---

### 技术选项对比

| 维度 | 内存缓存 | Redis | SQLite 缓存 | 文件缓存 |
|------|----------|-------|-------------|----------|
| **外部依赖** | 无 | Redis 服务 | 无 | 无 |
| **持久化** | ❌ 重启丢失 | ✅ | ✅ | ✅ |
| **速度** | ⭐⭐⭐ 最快 | ⭐⭐ 快 | ⭐⭐ 快 | ⭐ 较慢 |
| **容量限制** | 受内存限制 | 可配置 | 无限制 | 无限制 |
| **TTL 支持** | 需手动 | ✅ 原生 | 需手动 | 需手动 |
| **并发安全** | 需加锁 | ✅ 原生 | ✅ | ⚠️ 文件锁 |
| **查询能力** | 仅 key | key + 模式 | SQL | 仅文件名 |
| **部署复杂度** | ⭐ | ⭐⭐⭐ | ⭐ | ⭐ |

---

### 方案 A: 纯内存缓存 (最简单)

```python
from functools import lru_cache
from cachetools import TTLCache

# LRU 缓存 - 固定大小
@lru_cache(maxsize=100)
def get_embedding(text: str) -> list[float]:
    return embedding_model.encode(text)

# TTL 缓存 - 自动过期
memory_cache = TTLCache(maxsize=1000, ttl=3600)  # 1小时过期

def get_memory_results(query: str):
    if query in memory_cache:
        return memory_cache[query]
    result = graphiti.search(query)
    memory_cache[query] = result
    return result
```

**优点**: 零依赖、最快速度
**缺点**: 重启丢失、内存受限

---

### 方案 B: Redis (功能最全)

```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_memory_results(query: str):
    cache_key = f"memory:{hash(query)}"

    # 尝试从缓存获取
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # 查询并缓存
    result = graphiti.search(query)
    redis_client.setex(cache_key, 3600, json.dumps(result))  # 1小时过期
    return result
```

**优点**: TTL 原生支持、持久化、高性能
**缺点**: 需要安装运行 Redis

---

### 方案 C: SQLite 缓存表 (平衡方案)

```python
import sqlite3
import json
import time

class SQLiteCache:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute('''
 ... [truncated]

### Turn 5: User

  1. 缓存存储位置: 与 Checkpointer 共用 checkpoints.db 还是单独 cache.db？ 阐述一下共用和单独的区别

### Turn 6: Assistant



### Turn 7: Assistant

## 缓存存储位置：共用 vs 单独

### 方案对比

| 维度 | 共用 `checkpoints.db` | 单独 `cache.db` |
|------|----------------------|-----------------|
| **文件数量** | 1 个 | 2 个 |
| **备份复杂度** | 简单 (一个文件) | 稍复杂 |
| **数据耦合** | 高 | 低 |
| **独立清理** | ❌ 需小心 | ✅ 可直接删除 |
| **迁移灵活性** | 低 | 高 |
| **连接管理** | 共享连接 | 独立连接 |

---

### 共用 `checkpoints.db`

**数据库结构**:
```sql
-- LangGraph Checkpointer 表 (自动创建)
checkpoints (...)
checkpoint_writes (...)
checkpoint_blobs (...)

-- 缓存表 (我们添加)
cache (
    key TEXT PRIMARY KEY,
    value TEXT,
    expires_at REAL,
    category TEXT  -- 'embedding', 'memory', 'llm'
)

embedding_cache (
    text_hash TEXT PRIMARY KEY,
    vector BLOB,
    model TEXT,
    created_at REAL
)
```

**优点**:

1. **简化备份** - 用户只需备份一个文件
   ```
   .canvas-learning/
   └── checkpoints.db  ← 所有数据都在这里
   ```

2. **共享连接** - 减少数据库连接开销
   ```python
   # 一个连接处理所有操作
   conn = sqlite3.connect("checkpoints.db")
   checkpointer = SqliteSaver(conn)
   cache = SQLiteCache(conn)
   ```

3. **事务一致性** - 可以在同一事务中更新状态和缓存
   ```python
   with conn:
       # 原子操作
       checkpointer.put(config, checkpoint)
       cache.set(f"result:{task_id}", result)
   ```

**缺点**:

1. **数据耦合** - 删除缓存可能影响 Checkpointer
   ```python
   # 危险操作
   conn.execute("DELETE FROM cache")  # OK
   conn.execute("DROP TABLE cache")   # 可能破坏数据库完整性
   ```

2. **清理困难** - 无法简单地"重置缓存"
   ```bash
   # 想清空缓存？不能直接删除文件
   # 因为会丢失学习状态
   ```

3. **迁移复杂** - 如果未来要把缓存换成 Redis
   ```python
   # 需要从混合数据库中剥离缓存表
   # 比较麻烦
   ```

---

### 单独 `cache.db`

**文件结构**:
```
.canvas-learning/
├── checkpoints.db  ← LangGraph 状态
└── cache.db        ← 缓存数据
```

**优点**:

1. **独立生命周期** - 缓存可以随时清空
   ```bash
   # 缓存出问题？直接删除重建
   rm cache.db
   # 学习状态完全不受影响
   ```

2. **灵活迁移** - 未来可以轻松替换缓存方案
   ```python
   # 从 SQLite 迁移到 Redis
   # 只需修改 cache 模块，checkpointer 不变
   ```

3. **职责清晰** - 代码结构更清晰
   ```python
   # checkpointer.py - 只管状态
   # cache.py - 只管缓存
   # 互不干扰
   ```

4. **独立优化** - 可以针对不同用途优化
   ```python
   # checkpoints.db - WAL 模式，优化并发写
   # cache.db - 普通模式，优化读取
   ```

*... [truncated]

### Turn 8: User

单独 cache.db单独 cache.db，  2. Embedding 缓存策略:
    - 永久缓存 (节省计算)，3. 缓存大小限制:
    - 内存缓存上限？(默认 500 条)
    - SQLite 缓存是否需要大小限制？关于缓存大小限制需要你来进一步的阐述

### Turn 9: Assistant



### Turn 10: Assistant

## 缓存大小限制详解

### 数据增长预估

先估算各类缓存的数据量：

#### 1. Embedding 缓存

| 数据项 | 单条大小 | 预估数量 | 总大小 |
|--------|----------|----------|--------|
| 节点内容 Embedding | 3KB (768维 float32) | 1000 节点 | 3MB |
| 查询 Embedding | 3KB | 5000 查询 | 15MB |
| **合计** | | | **~20MB** |

**增长速度**: 慢 (新节点/新查询才增加)

---

#### 2. 记忆检索缓存

| 数据项 | 单条大小 | 预估数量 | 总大小 |
|--------|----------|----------|--------|
| Graphiti 查询结果 | 10-50KB | 1000 查询 | 10-50MB |
| LanceDB 查询结果 | 5-20KB | 1000 查询 | 5-20MB |
| **合计** | | | **~30-70MB** |

**增长速度**: 中等 (每次学习会话产生新查询)

---

#### 3. LLM 响应缓存

| 数据项 | 单条大小 | 预估数量 | 总大小 |
|--------|----------|----------|--------|
| Agent 响应 | 2-10KB | 500 条 | 1-5MB |
| **合计** | | | **~5MB** |

**增长速度**: 快 (但有 TTL 自动过期)

---

#### 4. Canvas 文件缓存

| 数据项 | 单条大小 | 预估数量 | 总大小 |
|--------|----------|----------|--------|
| Canvas JSON | 10-500KB | 50 文件 | 0.5-25MB |
| **合计** | | | **~10MB** |

**增长速度**: 慢 (文件数量有限)

---

### 内存缓存限制分析

#### 为什么需要限制？

```python
# 内存缓存无限制的风险
cache = {}

# 随着使用时间增长
len(cache) → 10,000 条
memory_usage → 500MB  # 可能导致 Obsidian 卡顿
```

#### 限制策略对比

| 策略 | 实现 | 优点 | 缺点 |
|------|------|------|------|
| **LRU (最近最少使用)** | `lru_cache(maxsize=N)` | 保留热数据 | 可能误删将用数据 |
| **TTL (过期时间)** | `TTLCache(ttl=N)` | 自动清理 | 热数据也会过期 |
| **LRU + TTL** | `TTLCache(maxsize=N, ttl=T)` | 两者兼顾 | 配置稍复杂 |

#### 推荐配置

```python
from cachetools import TTLCache

# L1 内存缓存配置
memory_caches = {
    # 记忆检索结果 - 高频访问，短期有效
    "memory_results": TTLCache(
        maxsize=500,      # 最多 500 条
        ttl=300           # 5 分钟过期
    ),

    # Canvas 文件内容 - 中频访问，会话级有效
    "canvas_files": TTLCache(
        maxsize=50,       # 最多 50 个文件
        ttl=1800          # 30 分钟过期
    ),

    # LLM 响应 - 低频重复，短期有效
    "llm_responses": TTLCache(
        maxsize=200,      # 最多 200 条
        ttl=600           # 10 分钟过期
    )
}
```

#### 内存占用估算

| 缓存类型 | maxsize | 单条大小 | 最大内存 |
|----------|---------|----------|----------|
| memory_results | 500 | 30KB | 15MB |
| canvas_files | 50 | 100KB | 5MB |
| llm_responses | 20... [truncated]

### Turn 11: User

我的电脑内存是32G

### Turn 12: Assistant



### Turn 13: Assistant

## 32GB 内存优化配置

### 内存分配分析

| 用途 | 预估占用 | 说明 |
|------|----------|------|
| 系统 | 3-4GB | Windows/macOS |
| Obsidian | 1-2GB | 含其他插件 |
| 其他应用 | 4-8GB | 浏览器等 |
| **可用于缓存** | **~10GB** | 保守估计 |

对于本地学习工具，分配 **200-500MB** 给缓存完全合理。

---

### 优化后的配置

```python
class CacheConfig:
    """32GB 内存优化配置"""

    # ===== 内存缓存 (L1) =====

    # 记忆检索结果 - 大幅提升
    MEMORY_RESULTS_MAX = 2000     # 500 → 2000
    MEMORY_RESULTS_TTL = 600      # 5分钟 → 10分钟

    # Canvas 文件 - 缓存更多文件
    CANVAS_FILES_MAX = 200        # 50 → 200
    CANVAS_FILES_TTL = 3600       # 30分钟 → 1小时

    # LLM 响应 - 适度提升
    LLM_RESPONSES_MAX = 500       # 200 → 500
    LLM_RESPONSES_TTL = 1800      # 10分钟 → 30分钟

    # Embedding 向量 - 全部放内存
    EMBEDDING_MEMORY_MAX = 5000   # 新增：内存缓存 Embedding
    EMBEDDING_MEMORY_TTL = None   # 不过期，LRU 淘汰

    # ===== SQLite 缓存 (L2) =====
    CACHE_DB_MAX_SIZE_MB = 500    # 200MB → 500MB
```

---

### 内存占用对比

| 缓存类型 | 保守配置 | 32GB 优化 | 最大内存 |
|----------|----------|-----------|----------|
| memory_results | 500 × 30KB | 2000 × 30KB | **60MB** |
| canvas_files | 50 × 100KB | 200 × 100KB | **20MB** |
| llm_responses | 200 × 5KB | 500 × 5KB | **2.5MB** |
| embedding | 0 | 5000 × 3KB | **15MB** |
| **合计** | ~21MB | | **~100MB** |

**结论**: 即使全部命中，也只占用 ~100MB，对 32GB 内存毫无压力。

---

### 性能收益

| 优化项 | 效果 |
|--------|------|
| Embedding 内存缓存 | 向量检索 **从 5ms → 0.1ms** |
| 更多 Canvas 文件 | 切换文件 **无需重新读取** |
| 更长 TTL | 减少重复计算，**节省 LLM 调用** |
| 更大容量 | 缓存命中率 **从 60% → 90%+** |

---

### 最终推荐配置

```python
class CacheConfig:
    """Canvas Learning System - 32GB 内存配置"""

    # ===== L1 内存缓存 =====

    MEMORY_CACHES = {
        "embedding": {
            "maxsize": 5000,
            "ttl": None,        # LRU 淘汰，不过期
        },
        "memory_results": {
            "maxsize": 2000,
            "ttl": 600,         # 10 分钟
        },
        "canvas_files": {
            "maxsize": 200,
            "ttl": 3600,        # 1 小时
        },
        "llm_responses": {
            ... [truncated]

### Turn 14: User

确认

### Turn 15: Assistant



### Turn 16: Assistant



### Turn 17: User



### Turn 18: Assistant



### Turn 19: Assistant



### Turn 20: User



---

## Transcript Analysis

**Transcript Path**: `C:\Users\ROG\.claude\projects\C--Users-ROG----Canvas\18cfc2cf-9af3-4a6e-8843-86110ca5cceb.jsonl`
**Transcript Exists**: 鉁?Yes
**Transcript Lines**: 267
**Parsed Messages**: 20
**Files Mentioned**: 1

---

## Status Log

- 鉁?File created by PowerShell hook at: 2025-11-23 23:36:33
- 鉁?Content filled by PowerShell (automated transcript parsing)
- 鉁?Real solution implemented: No dependency on Claude timing
- 馃摑 **Discovery**: PreCompact hook can access full conversation via transcript_path
