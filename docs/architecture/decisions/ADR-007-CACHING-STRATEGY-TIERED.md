# ADR-007: 缓存策略 - 分层缓存

## 状态

**已接受** | 2025-11-23

## 背景

Canvas Learning System 需要缓存策略来优化以下场景的性能：

### 缓存场景

| 场景 | 数据类型 | 大小 | 访问频率 | 计算成本 |
|------|----------|------|----------|----------|
| Embedding 向量 | float[] | 3KB/个 | 高 | 高 (模型推理) |
| 记忆检索结果 | JSON | 10-50KB | 高 | 中 (数据库查询) |
| Canvas 文件内容 | JSON | 10-500KB | 高 | 低 (文件 I/O) |
| LLM 响应 | 文本 | 2-10KB | 中 | 极高 (API 调用) |

### 技术约束

1. **本地 Obsidian 插件** - 不应依赖 Redis 等外部服务
2. **32GB 内存环境** - 可以使用较大的内存缓存
3. **数据持久化需求** - Embedding 等高成本数据应持久化
4. **与 Checkpointer 分离** - 缓存是可丢弃数据，状态不可丢失

## 决策

**采用分层缓存方案 (L1 内存 + L2 SQLite)**

### 存储架构

```
{Vault}/.canvas-learning/
├── checkpoints.db    # LangGraph 状态 (必须保留)
├── cache.db          # 缓存数据 (可删除重建)
└── config.yaml       # 用户配置
```

### 分层策略

```
┌─────────────────────────────────────────────┐
│ L1: 内存缓存 (TTLCache)                      │
│ - 热数据，亚毫秒访问                          │
│ - 重启后丢失                                 │
│ - 容量限制 + TTL 自动清理                     │
└─────────────────┬───────────────────────────┘
                  │ 未命中
                  ▼
┌─────────────────────────────────────────────┐
│ L2: SQLite 缓存 (cache.db)                   │
│ - 温/冷数据，毫秒级访问                       │
│ - 持久化存储                                 │
│ - 定期清理过期数据                            │
└─────────────────────────────────────────────┘
```

## 理由

### 1. 为什么分层缓存？

| 单层方案 | 问题 |
|----------|------|
| 纯内存 | Embedding 重启后需重新计算，浪费资源 |
| 纯 SQLite | 热数据访问慢 (5ms vs 0.1ms) |
| Redis | 需要额外服务，增加用户配置负担 |

**分层方案兼顾**：
- 热数据在内存，极速访问
- 冷数据在 SQLite，持久保存

### 2. 为什么单独 cache.db？

| 维度 | 单独 cache.db | 共用 checkpoints.db |
|------|---------------|---------------------|
| 数据安全 | ✅ 缓存损坏不影响状态 | ❌ 可能连带损坏 |
| 清理方便 | ✅ 直接删除重建 | ❌ 需要复杂操作 |
| 迁移灵活 | ✅ 可独立替换 | ❌ 耦合紧密 |

### 3. 为什么 Embedding 永久缓存？

```python
# Embedding 计算成本
time_to_compute = 50-200ms  # 模型推理
time_to_cache_hit = 0.1ms   # 内存命中

# 1000 个节点的 Embedding
without_cache = 1000 × 100ms = 100s
with_cache = 1000 × 0.1ms = 0.1s

# 性能提升 1000 倍
```

## 实现细节

### 配置定义

```python
class CacheConfig:
    """Canvas Learning System - 32GB 内存优化配置"""

    # ===== L1 内存缓存 =====

    MEMORY_CACHES = {
        # Embedding 向量 - 最高优先级
        "embedding": {
            "maxsize": 5000,     # 5000 个向量
            "ttl": None,        # 永不过期，LRU 淘汰
        },

        # 记忆检索结果
        "memory_results": {
            "maxsize": 2000,     # 2000 条查询结果
            "ttl": 600,         # 10 分钟过期
        },

        # Canvas 文件内容
        "canvas_files": {
            "maxsize": 200,      # 200 个文件
            "ttl": 3600,        # 1 小时过期
        },

        # LLM 响应
        "llm_responses": {
            "maxsize": 500,      # 500 条响应
            "ttl": 1800,        # 30 分钟过期
        },
    }

    # 内存缓存总容量估算: ~100MB

    # ===== L2 SQLite 缓存 =====

    SQLITE_CONFIG = {
        "db_path": ".canvas-learning/cache.db",
        "max_size_mb": 500,           # 最大 500MB
        "cleanup_interval": 3600,     # 每小时清理
        "cleanup_old_days": 30,       # 删除 30 天前数据
        "vacuum_interval": 86400,     # 每天 VACUUM
    }

    # ===== 各类数据 TTL =====

    TTL_CONFIG = {
        "embedding": None,            # 永久
        "memory_results": 7 * 86400,  # 7 天
        "llm_responses": 1 * 86400,   # 1 天
        "canvas_files": 7 * 86400,    # 7 天
    }
```

### 核心实现

```python
from cachetools import TTLCache, LRUCache
import sqlite3
import json
import time
import hashlib
from typing import Any, Optional

class TieredCache:
    """分层缓存实现"""

    def __init__(self, config: CacheConfig):
        self.config = config

        # L1: 内存缓存
        self.l1_caches = {}
        for name, cfg in config.MEMORY_CACHES.items():
            if cfg["ttl"]:
                self.l1_caches[name] = TTLCache(
                    maxsize=cfg["maxsize"],
                    ttl=cfg["ttl"]
                )
            else:
                self.l1_caches[name] = LRUCache(maxsize=cfg["maxsize"])

        # L2: SQLite 缓存
        self.l2_cache = SQLiteCache(
            config.SQLITE_CONFIG["db_path"],
            config.SQLITE_CONFIG["max_size_mb"]
        )

    def get(self, category: str, key: str) -> Optional[Any]:
        """获取缓存数据"""
        cache_key = self._make_key(category, key)

        # 1. 查 L1
        l1 = self.l1_caches.get(category)
        if l1 and cache_key in l1:
            return l1[cache_key]

        # 2. 查 L2
        value = self.l2_cache.get(cache_key)
        if value is not None:
            # 提升到 L1
            if l1:
                l1[cache_key] = value
            return value

        return None

    def set(self, category: str, key: str, value: Any) -> None:
        """设置缓存数据"""
        cache_key = self._make_key(category, key)
        ttl = self.config.TTL_CONFIG.get(category, 3600)

        # 写入 L1
        l1 = self.l1_caches.get(category)
        if l1:
            l1[cache_key] = value

        # 写入 L2
        self.l2_cache.set(cache_key, value, category, ttl)

    def _make_key(self, category: str, key: str) -> str:
        """生成缓存键"""
        return f"{category}:{hashlib.md5(key.encode()).hexdigest()}"

    def get_stats(self) -> dict:
        """获取缓存统计"""
        stats = {
            "l1": {},
            "l2": {
                "size_mb": self.l2_cache.get_db_size_mb(),
                "total_items": self.l2_cache.count()
            }
        }

        for name, cache in self.l1_caches.items():
            stats["l1"][name] = {
                "current": len(cache),
                "maxsize": cache.maxsize
            }

        return stats

    def clear(self, category: Optional[str] = None) -> None:
        """清空缓存"""
        if category:
            # 清空特定类别
            if category in self.l1_caches:
                self.l1_caches[category].clear()
            self.l2_cache.delete_category(category)
        else:
            # 清空所有
            for cache in self.l1_caches.values():
                cache.clear()
            self.l2_cache.clear()


class SQLiteCache:
    """SQLite 缓存层"""

    def __init__(self, db_path: str, max_size_mb: int = 500):
        self.db_path = db_path
        self.max_size_mb = max_size_mb
        self.conn = sqlite3.connect(db_path)
        self._init_schema()

    def _init_schema(self):
        self.conn.executescript('''
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT,
                category TEXT,
                expires_at REAL,
                created_at REAL
            );

            CREATE INDEX IF NOT EXISTS idx_cache_category
            ON cache(category);

            CREATE INDEX IF NOT EXISTS idx_cache_expires
            ON cache(expires_at);

            CREATE INDEX IF NOT EXISTS idx_cache_created
            ON cache(created_at);
        ''')
        self.conn.commit()

    def get(self, key: str) -> Optional[Any]:
        row = self.conn.execute(
            'SELECT value, expires_at FROM cache WHERE key = ?',
            (key,)
        ).fetchone()

        if row:
            value, expires_at = row
            # 检查是否过期 (None 表示永不过期)
            if expires_at is None or expires_at > time.time():
                return json.loads(value)
            else:
                # 过期则删除
                self.conn.execute('DELETE FROM cache WHERE key = ?', (key,))
                self.conn.commit()

        return None

    def set(self, key: str, value: Any, category: str, ttl: Optional[int] = None):
        expires_at = time.time() + ttl if ttl else None

        self.conn.execute('''
            INSERT OR REPLACE INTO cache (key, value, category, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (key, json.dumps(value), category, expires_at, time.time()))
        self.conn.commit()

    def delete_category(self, category: str):
        self.conn.execute('DELETE FROM cache WHERE category = ?', (category,))
        self.conn.commit()

    def clear(self):
        self.conn.execute('DELETE FROM cache')
        self.conn.commit()
        self.vacuum()

    def cleanup_expired(self):
        """清理过期数据"""
        self.conn.execute(
            'DELETE FROM cache WHERE expires_at IS NOT NULL AND expires_at < ?',
            (time.time(),)
        )
        self.conn.commit()

    def cleanup_old(self, days: int, exclude_categories: list = None):
        """清理旧数据"""
        exclude = exclude_categories or ['embedding']
        cutoff = time.time() - (days * 86400)

        placeholders = ','.join('?' * len(exclude))
        self.conn.execute(f'''
            DELETE FROM cache
            WHERE created_at < ? AND category NOT IN ({placeholders})
        ''', (cutoff, *exclude))
        self.conn.commit()

    def cleanup_by_size(self):
        """当超过大小限制时清理"""
        while self.get_db_size_mb() > self.max_size_mb:
            # 删除最旧的非 Embedding 数据
            self.conn.execute('''
                DELETE FROM cache
                WHERE key IN (
                    SELECT key FROM cache
                    WHERE category != 'embedding'
                    ORDER BY created_at ASC
                    LIMIT 100
                )
            ''')
            self.conn.commit()
            self.vacuum()

    def vacuum(self):
        """回收空间"""
        self.conn.execute('VACUUM')

    def get_db_size_mb(self) -> float:
        import os
        return os.path.getsize(self.db_path) / (1024 * 1024)

    def count(self) -> int:
        return self.conn.execute('SELECT COUNT(*) FROM cache').fetchone()[0]
```

### 使用示例

```python
# 初始化
cache = TieredCache(CacheConfig())

# ===== Embedding 缓存 =====

def get_embedding(text: str) -> list[float]:
    # 尝试从缓存获取
    cached = cache.get("embedding", text)
    if cached:
        return cached

    # 计算 Embedding
    vector = embedding_model.encode(text)

    # 缓存结果 (永久)
    cache.set("embedding", text, vector.tolist())

    return vector

# ===== 记忆检索缓存 =====

async def search_memory(query: str) -> list[dict]:
    cached = cache.get("memory_results", query)
    if cached:
        return cached

    # 执行检索
    results = await graphiti.search(query)

    # 缓存 7 天
    cache.set("memory_results", query, results)

    return results

# ===== Canvas 文件缓存 =====

def read_canvas(path: str) -> dict:
    cached = cache.get("canvas_files", path)
    if cached:
        return cached

    # 读取文件
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 缓存 1 小时
    cache.set("canvas_files", path, data)

    return data

# ===== LLM 响应缓存 =====

async def call_llm(prompt: str, **kwargs) -> str:
    # 生成缓存键 (包含参数)
    cache_key = f"{prompt}:{json.dumps(kwargs, sort_keys=True)}"

    cached = cache.get("llm_responses", cache_key)
    if cached:
        return cached

    # 调用 LLM
    response = await llm.ainvoke(prompt, **kwargs)

    # 缓存 30 分钟
    cache.set("llm_responses", cache_key, response)

    return response
```

### 后台清理任务

```python
import asyncio

async def cache_maintenance_task(cache: TieredCache):
    """后台缓存维护任务"""

    cleanup_interval = CacheConfig.SQLITE_CONFIG["cleanup_interval"]
    vacuum_interval = CacheConfig.SQLITE_CONFIG["vacuum_interval"]

    last_vacuum = time.time()

    while True:
        await asyncio.sleep(cleanup_interval)

        try:
            # 1. 清理过期数据
            cache.l2_cache.cleanup_expired()

            # 2. 清理 30 天前的旧数据 (Embedding 除外)
            cache.l2_cache.cleanup_old(
                days=CacheConfig.SQLITE_CONFIG["cleanup_old_days"],
                exclude_categories=['embedding']
            )

            # 3. 检查大小限制
            if cache.l2_cache.get_db_size_mb() > CacheConfig.SQLITE_CONFIG["max_size_mb"]:
                cache.l2_cache.cleanup_by_size()

            # 4. 定期 VACUUM
            if time.time() - last_vacuum > vacuum_interval:
                cache.l2_cache.vacuum()
                last_vacuum = time.time()

            # 5. 记录统计
            stats = cache.get_stats()
            logger.info(f"Cache stats: {stats}")

        except Exception as e:
            logger.error(f"Cache maintenance error: {e}")
```

### 缓存失效策略

```python
class CacheInvalidator:
    """缓存失效管理"""

    def __init__(self, cache: TieredCache):
        self.cache = cache

    def on_canvas_modified(self, canvas_path: str):
        """Canvas 文件被修改时"""
        # 清除该文件的缓存
        self.cache.l1_caches["canvas_files"].pop(
            self.cache._make_key("canvas_files", canvas_path),
            None
        )

    def on_memory_updated(self):
        """记忆系统更新时"""
        # 清除所有记忆检索缓存
        self.cache.l1_caches["memory_results"].clear()
        self.cache.l2_cache.delete_category("memory_results")

    def on_embedding_model_changed(self):
        """Embedding 模型变更时"""
        # 清除所有 Embedding 缓存
        self.cache.clear("embedding")
```

### 内存占用估算

| 缓存类型 | maxsize | 单条大小 | 最大内存 |
|----------|---------|----------|----------|
| embedding | 5000 | 3KB | 15MB |
| memory_results | 2000 | 30KB | 60MB |
| canvas_files | 200 | 100KB | 20MB |
| llm_responses | 500 | 5KB | 2.5MB |
| **合计** | | | **~100MB** |

## 影响

### 正面影响

1. **性能提升显著**
   - Embedding 访问: 50ms → 0.1ms (500x)
   - 记忆检索: 100ms → 5ms (20x)
   - Canvas 读取: 10ms → 0.1ms (100x)

2. **成本节省**
   - 重复 LLM 调用减少 80%+
   - 重复 Embedding 计算减少 95%+

3. **用户体验**
   - 操作响应更快
   - 学习流程更流畅

### 负面影响

1. **内存占用** - ~100MB (对 32GB 可忽略)
2. **磁盘占用** - 最大 500MB
3. **数据一致性** - 需要正确处理失效

### 缓解措施

1. **内存监控** - 提供缓存统计 API
2. **手动清理** - 用户可删除 cache.db 重建
3. **失效策略** - 文件修改时自动清除相关缓存

## 替代方案记录

### 方案 A: Redis

**未选择原因**：
- 需要安装运行 Redis 服务
- 增加用户配置复杂度
- 本地单用户场景过于重型

### 方案 B: 纯内存缓存

**未选择原因**：
- Embedding 等高成本数据重启后需重算
- 浪费计算资源

### 方案 C: 与 Checkpointer 共用数据库

**未选择原因**：
- 缓存损坏可能影响学习状态
- 清理操作复杂
- 职责不清晰

## 实现计划

| 阶段 | 内容 | Story |
|------|------|-------|
| Phase 1 | TieredCache 核心实现 | Story 11.x |
| Phase 2 | Embedding 缓存集成 | Story 12.x |
| Phase 3 | 记忆检索缓存 | Story 12.x |
| Phase 4 | 后台清理任务 | Story 11.x |
| Phase 5 | 缓存统计 API | Story 17.x |

## 参考资料

- [cachetools Documentation](https://cachetools.readthedocs.io/)
- [SQLite Performance](https://www.sqlite.org/performance.html)
- ADR-005: LangGraph Checkpointer (存储分离参考)

---

**作者**: Winston (Architect Agent)
**审核**: 待定
**批准**: 待定
