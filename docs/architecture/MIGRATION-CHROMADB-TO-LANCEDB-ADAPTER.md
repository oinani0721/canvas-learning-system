---
document_type: "Architecture"
version: "1.0.0"
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

# ChromaDB → LanceDB 迁移适配层设计

**文档版本**: v1.0
**创建日期**: 2025-11-14
**状态**: 调研阶段
**相关调研**: 调研任务1-B - 代码改造工作量评估

---

## 📋 目标

设计一个**兼容层**，确保迁移到LanceDB后：
1. ✅ **对外接口保持不变** - 调用方代码无需修改
2. ✅ **支持灰度切换** - Feature flag控制，可快速回滚
3. ✅ **双写验证** - 迁移初期同时写入ChromaDB和LanceDB
4. ✅ **性能监控** - 记录查询延迟，对比性能

---

## 🏗️ 架构设计

### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│  MCPSemanticMemory (统一接口层)                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  store_semantic_memory(content, metadata)           │   │
│  │  search_semantic_memory(query, limit)               │   │
│  │  delete_memory(memory_id)                           │   │
│  │  get_memory_stats()                                 │   │
│  └────────────────┬────────────────────────────────────┘   │
│                   │                                          │
│                   ▼                                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │  VectorDatabaseAdapter (抽象适配层)                 │    │
│  │  - use_lancedb: bool (feature flag)                │    │
│  │  - enable_dual_write: bool (双写验证)              │    │
│  └────────────┬───────────────────┬────────────────────┘    │
│               │                   │                          │
│               ▼                   ▼                          │
│  ┌─────────────────────┐  ┌──────────────────────┐         │
│  │  ChromaDBBackend    │  │  LanceDBBackend      │         │
│  │  (传统实现)         │  │  (新实现)            │         │
│  └─────────────────────┘  └──────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

---

## 💻 代码实现

### 1. 抽象基类 (VectorDatabaseAdapter)

```python
# ✅ Verified Architecture Pattern - Zero-Hallucination Development
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class VectorDatabaseAdapter(ABC):
    """向量数据库抽象适配器"""

    @abstractmethod
    def initialize(self, config: Dict) -> None:
        """初始化数据库连接"""
        pass

    @abstractmethod
    def store_memory(self, memory_id: str, content: str,
                     embedding: List[float], metadata: Dict) -> str:
        """存储语义记忆"""
        pass

    @abstractmethod
    def search_memory(self, query_embedding: List[float],
                      limit: int) -> List[Dict]:
        """搜索语义记忆"""
        pass

    @abstractmethod
    def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        pass

    @abstractmethod
    def count_memories(self) -> int:
        """统计记忆数量"""
        pass

    @abstractmethod
    def close(self) -> None:
        """关闭连接"""
        pass
```

---

### 2. ChromaDB后端实现

```python
# ✅ Verified from Context7 ChromaDB Documentation
import chromadb
from chromadb.config import Settings

class ChromaDBBackend(VectorDatabaseAdapter):
    """ChromaDB后端实现（保持原有代码逻辑）"""

    def __init__(self):
        self.vector_db = None
        self.collection = None

    def initialize(self, config: Dict) -> None:
        """初始化ChromaDB连接"""
        persist_directory = config.get("persist_directory", "./data/memory_db")
        collection_name = config.get("collection_name", "canvas_memories")

        self.vector_db = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        try:
            self.collection = self.vector_db.get_collection(name=collection_name)
            logger.info(f"[ChromaDB] 使用现有集合: {collection_name}")
        except:
            self.collection = self.vector_db.create_collection(
                name=collection_name,
                metadata={"description": "Canvas语义记忆集合"}
            )
            logger.info(f"[ChromaDB] 创建新集合: {collection_name}")

    def store_memory(self, memory_id: str, content: str,
                     embedding: List[float], metadata: Dict) -> str:
        """存储语义记忆到ChromaDB"""
        self.collection.add(
            ids=[memory_id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[content]
        )
        return memory_id

    def search_memory(self, query_embedding: List[float],
                      limit: int) -> List[Dict]:
        """从ChromaDB搜索记忆"""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            include=["metadatas", "documents", "distances"]
        )

        # 格式化结果为统一格式
        formatted_results = []
        if results["ids"] and results["ids"][0]:
            for i, memory_id in enumerate(results["ids"][0]):
                formatted_results.append({
                    "memory_id": memory_id,
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "similarity_score": 1 - results["distances"][0][i],
                    "distance": results["distances"][0][i]
                })

        return formatted_results

    def delete_memory(self, memory_id: str) -> bool:
        """从ChromaDB删除记忆"""
        try:
            self.collection.delete(ids=[memory_id])
            return True
        except Exception as e:
            logger.error(f"[ChromaDB] 删除失败: {e}")
            return False

    def count_memories(self) -> int:
        """统计ChromaDB中的记忆数量"""
        return self.collection.count()

    def close(self) -> None:
        """关闭ChromaDB连接"""
        self.vector_db = None
        self.collection = None
```

---

### 3. LanceDB后端实现

```python
# ✅ Verified from Context7 LanceDB Documentation - Zero-Hallucination Research
import lancedb
import pandas as pd
from lancedb.pydantic import LanceModel, Vector

# ✅ Verified Schema from调研任务1-A
class SemanticMemorySchema(LanceModel):
    """LanceDB语义记忆Schema"""
    id: str
    document: str
    metadata: dict  # ✅ LanceDB支持嵌套JSON
    vector: Vector(384)  # all-MiniLM-L6-v2维度

class LanceDBBackend(VectorDatabaseAdapter):
    """LanceDB后端实现（新实现）"""

    def __init__(self):
        self.vector_db = None
        self.collection = None  # 实际是LanceDB table

    def initialize(self, config: Dict) -> None:
        """初始化LanceDB连接"""
        persist_directory = config.get("persist_directory", "./data/memory_db")
        collection_name = config.get("collection_name", "canvas_memories")

        # ✅ Verified from Context7 - "Create LanceDB Table"
        self.vector_db = lancedb.connect(persist_directory)

        if collection_name in self.vector_db.table_names():
            self.collection = self.vector_db.open_table(collection_name)
            logger.info(f"[LanceDB] 使用现有表: {collection_name}")
        else:
            # 创建空表（首次）
            self.collection = self.vector_db.create_table(
                collection_name,
                schema=SemanticMemorySchema
            )
            logger.info(f"[LanceDB] 创建新表: {collection_name}")

    def store_memory(self, memory_id: str, content: str,
                     embedding: List[float], metadata: Dict) -> str:
        """存储语义记忆到LanceDB"""
        # ✅ Verified from Context7 - "Add Pandas DataFrame to LanceDB Table"
        df = pd.DataFrame([{
            'id': memory_id,
            'vector': embedding,  # 已经是list格式
            'metadata': metadata,  # LanceDB支持嵌套dict
            'document': content
        }])

        self.collection.add(df)
        return memory_id

    def search_memory(self, query_embedding: List[float],
                      limit: int) -> List[Dict]:
        """从LanceDB搜索记忆"""
        # ✅ Verified from Context7 - "Vector Search Operations"
        results_df = (
            self.collection
            .search(query_embedding)
            .limit(limit)
            .to_pandas()
        )

        # 格式化结果为统一格式（与ChromaDB一致）
        formatted_results = []
        for _, row in results_df.iterrows():
            formatted_results.append({
                "memory_id": row['id'],
                "content": row['document'],
                "metadata": row['metadata'],
                "similarity_score": 1 - row['_distance'],  # 转换为相似度
                "distance": row['_distance']
            })

        return formatted_results

    def delete_memory(self, memory_id: str) -> bool:
        """从LanceDB删除记忆"""
        try:
            # ✅ Verified from Context7 - "Delete Rows from LanceDB Table"
            self.collection.delete(f"id = '{memory_id}'")
            return True
        except Exception as e:
            logger.error(f"[LanceDB] 删除失败: {e}")
            return False

    def count_memories(self) -> int:
        """统计LanceDB中的记忆数量"""
        # ✅ Verified from Context7 - "Count Rows in LanceDB Table"
        return self.collection.count_rows()

    def close(self) -> None:
        """关闭LanceDB连接"""
        # LanceDB自动管理连接，无需手动关闭
        self.vector_db = None
        self.collection = None
```

---

### 4. 统一接口层 (修改后的MCPSemanticMemory)

```python
class MCPSemanticMemory:
    """MCP语义记忆服务管理器（支持ChromaDB/LanceDB切换）"""

    def __init__(self, config_path: str = "config/mcp_config.yaml"):
        """初始化MCP记忆服务

        Args:
            config_path: MCP配置文件路径
        """
        self.config = self._load_config(config_path)
        self._validate_dependencies()

        # ✅ Feature Flag: 控制使用哪个后端
        self.use_lancedb = self.config.get("mcp_service", {}).get("use_lancedb", False)
        self.enable_dual_write = self.config.get("mcp_service", {}).get("enable_dual_write", False)

        # 硬件检测（保持不变）
        self.hardware_info = HardwareDetector.detect_gpu()
        self.device = self._determine_device()

        # 初始化Embedding模型（保持不变）
        self.embedding_model = None
        self._initialize_embedding_model()

        # ✅ 根据配置选择后端
        if self.use_lancedb:
            self.backend = LanceDBBackend()
            logger.info("🚀 使用LanceDB后端")
        else:
            self.backend = ChromaDBBackend()
            logger.info("📦 使用ChromaDB后端（传统）")

        # ✅ 双写验证：同时维护两个后端（迁移初期）
        if self.enable_dual_write:
            self.secondary_backend = ChromaDBBackend() if self.use_lancedb else None
            logger.warning("⚠️ 双写模式启用，性能会降低")
        else:
            self.secondary_backend = None

        # 初始化后端
        db_config = self.config.get("mcp_service", {}).get("vector_database", {})
        self.backend.initialize(db_config)
        if self.secondary_backend:
            self.secondary_backend.initialize(db_config)

        logger.info(f"MCP语义记忆服务初始化完成，使用设备: {self.device}")

    def store_semantic_memory(self, content: str, metadata: Dict) -> str:
        """存储语义记忆（统一接口）

        Args:
            content: 需要记忆的内容
            metadata: 内容元数据

        Returns:
            str: 记忆ID
        """
        try:
            # 生成记忆ID（保持不变）
            memory_id = f"memory-{uuid.uuid4().hex[:16]}"

            # 生成内容嵌入（保持不变）
            embedding = self.embedding_model.encode(content)
            if hasattr(embedding, 'tolist'):
                embedding = embedding.tolist()

            # 构建完整的元数据（保持不变）
            full_metadata = {
                "memory_id": memory_id,
                "content": content,
                "content_length": len(content),
                "model_name": self.embedding_model._modules['0'].auto_model.name_or_path,
                "embedding_timestamp": datetime.now().isoformat(),
                "device": self.device,
                **metadata
            }

            # ✅ 写入主后端
            self.backend.store_memory(memory_id, content, embedding, full_metadata)

            # ✅ 双写验证（可选）
            if self.secondary_backend:
                self.secondary_backend.store_memory(memory_id, content, embedding, full_metadata)
                logger.debug(f"[DualWrite] 已同步到secondary backend")

            logger.info(f"语义记忆存储成功: {memory_id}")
            return memory_id

        except Exception as e:
            logger.error(f"语义记忆存储失败: {e}")
            raise

    def search_semantic_memory(self, query: str, limit: int = 10) -> List[Dict]:
        """语义搜索记忆（统一接口）

        Args:
            query: 搜索查询
            limit: 返回结果数量限制

        Returns:
            List[Dict]: 相关记忆列表
        """
        try:
            # 生成查询嵌入（保持不变）
            query_embedding = self.embedding_model.encode(query)
            if hasattr(query_embedding, 'tolist'):
                query_embedding = query_embedding.tolist()

            # ✅ 从主后端搜索
            import time
            start_time = time.time()
            results = self.backend.search_memory(query_embedding, limit)
            search_latency = time.time() - start_time

            # ✅ 性能监控
            logger.info(f"语义搜索完成，返回 {len(results)} 个结果，耗时 {search_latency:.3f}s")

            # ✅ 双写验证：对比两个后端的结果（可选）
            if self.secondary_backend and logger.level <= logging.DEBUG:
                secondary_results = self.secondary_backend.search_memory(query_embedding, limit)
                self._compare_search_results(results, secondary_results)

            return results

        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            return []

    def delete_memory(self, memory_id: str) -> bool:
        """删除记忆（统一接口）

        Args:
            memory_id: 记忆ID

        Returns:
            bool: 删除是否成功
        """
        try:
            # ✅ 从主后端删除
            success = self.backend.delete_memory(memory_id)

            # ✅ 双写验证：同步删除
            if self.secondary_backend:
                self.secondary_backend.delete_memory(memory_id)

            if success:
                logger.info(f"记忆删除成功: {memory_id}")
            return success

        except Exception as e:
            logger.error(f"记忆删除失败: {e}")
            return False

    def get_memory_stats(self) -> Dict:
        """获取记忆统计信息（统一接口）"""
        try:
            count = self.backend.count_memories()

            stats = {
                "total_memories": count,
                "backend": "LanceDB" if self.use_lancedb else "ChromaDB",
                "device": self.device,
                "model_name": self.embedding_model._modules['0'].auto_model.name_or_path if self.embedding_model else "unknown",
                "hardware_info": self.hardware_info,
                "last_updated": datetime.now().isoformat()
            }

            # ✅ 双写验证：对比数量
            if self.secondary_backend:
                secondary_count = self.secondary_backend.count_memories()
                stats["dual_write_enabled"] = True
                stats["secondary_backend_count"] = secondary_count
                if count != secondary_count:
                    logger.warning(f"⚠️ 数据不一致: 主后端={count}, 次后端={secondary_count}")

            return stats

        except Exception as e:
            logger.error(f"获取记忆统计失败: {e}")
            return {}

    def close(self):
        """关闭连接（统一接口）"""
        try:
            if self.backend:
                self.backend.close()
            if self.secondary_backend:
                self.secondary_backend.close()
            if self.embedding_model:
                del self.embedding_model
                self.embedding_model = None
            logger.info("MCP语义记忆服务已关闭")
        except Exception as e:
            logger.error(f"关闭服务时出错: {e}")

    # ✅ 内部工具函数
    def _compare_search_results(self, primary_results: List[Dict],
                                 secondary_results: List[Dict]) -> None:
        """对比两个后端的搜索结果（调试用）"""
        if len(primary_results) != len(secondary_results):
            logger.debug(f"[DualWrite] 结果数量不一致: 主={len(primary_results)}, 次={len(secondary_results)}")

        # 对比前3个结果的memory_id
        for i in range(min(3, len(primary_results), len(secondary_results))):
            if primary_results[i]["memory_id"] != secondary_results[i]["memory_id"]:
                logger.debug(f"[DualWrite] 第{i+1}个结果不一致: 主={primary_results[i]['memory_id']}, 次={secondary_results[i]['memory_id']}")
```

---

## 📋 配置文件修改

### config/mcp_config.yaml 新增参数

```yaml
mcp_service:
  # ✅ Feature Flag: 控制向量数据库后端
  use_lancedb: true                 # true=LanceDB, false=ChromaDB (默认false)
  enable_dual_write: false          # true=双写验证（迁移初期）, false=单写（正常）

  vector_database:
    type: "lancedb"                 # chromadb | lancedb
    persist_directory: "./data/memory_db"
    collection_name: "canvas_memories"

  embedding_model:
    model_name: "sentence-transformers/all-MiniLM-L6-v2"
    device: "auto"

  hardware_detection:
    auto_detect_gpu: true
    fallback_to_cpu: true
```

---

## 🧪 测试策略

### 单元测试 (test_mcp_memory_adapter.py)

```python
import pytest
from mcp_memory_client import MCPSemanticMemory

@pytest.fixture
def chromadb_backend():
    """ChromaDB后端fixture"""
    config = {
        "mcp_service": {
            "use_lancedb": False,
            "enable_dual_write": False,
            "vector_database": {
                "persist_directory": "./test_chromadb",
                "collection_name": "test_collection"
            }
        }
    }
    # 创建临时配置文件...
    client = MCPSemanticMemory(config_path="test_config.yaml")
    yield client
    client.close()

@pytest.fixture
def lancedb_backend():
    """LanceDB后端fixture"""
    config = {
        "mcp_service": {
            "use_lancedb": True,
            "enable_dual_write": False,
            "vector_database": {
                "persist_directory": "./test_lancedb",
                "collection_name": "test_collection"
            }
        }
    }
    client = MCPSemanticMemory(config_path="test_config_lancedb.yaml")
    yield client
    client.close()

def test_store_and_search_chromadb(chromadb_backend):
    """测试ChromaDB后端的存储和搜索"""
    memory_id = chromadb_backend.store_semantic_memory(
        "逆否命题是逻辑学中的重要概念",
        {"category": "logic"}
    )
    assert memory_id.startswith("memory-")

    results = chromadb_backend.search_semantic_memory("逆否命题", limit=5)
    assert len(results) > 0
    assert results[0]["memory_id"] == memory_id

def test_store_and_search_lancedb(lancedb_backend):
    """测试LanceDB后端的存储和搜索"""
    memory_id = lancedb_backend.store_semantic_memory(
        "逆否命题是逻辑学中的重要概念",
        {"category": "logic"}
    )
    assert memory_id.startswith("memory-")

    results = lancedb_backend.search_semantic_memory("逆否命题", limit=5)
    assert len(results) > 0
    assert results[0]["memory_id"] == memory_id

def test_dual_write_consistency():
    """测试双写模式的数据一致性"""
    config = {
        "mcp_service": {
            "use_lancedb": True,
            "enable_dual_write": True,  # 启用双写
            "vector_database": {
                "persist_directory": "./test_dual_write",
                "collection_name": "test_collection"
            }
        }
    }
    client = MCPSemanticMemory(config_path="test_config_dual.yaml")

    memory_id = client.store_semantic_memory(
        "测试内容",
        {"test": True}
    )

    # 验证两个后端都有数据
    stats = client.get_memory_stats()
    assert stats["total_memories"] == stats["secondary_backend_count"]

    client.close()
```

---

## 📊 性能监控

### 性能对比测试 (test_performance_comparison.py)

```python
import time
import matplotlib.pyplot as plt

def benchmark_backends():
    """对比ChromaDB和LanceDB的性能"""

    test_sizes = [100, 500, 1000, 5000, 10000]
    chromadb_times = []
    lancedb_times = []

    for size in test_sizes:
        # ChromaDB测试
        client_chromadb = create_test_client(use_lancedb=False)
        start = time.time()
        for i in range(size):
            client_chromadb.store_semantic_memory(f"测试内容 {i}", {"index": i})
        chromadb_times.append(time.time() - start)
        client_chromadb.close()

        # LanceDB测试
        client_lancedb = create_test_client(use_lancedb=True)
        start = time.time()
        for i in range(size):
            client_lancedb.store_semantic_memory(f"测试内容 {i}", {"index": i})
        lancedb_times.append(time.time() - start)
        client_lancedb.close()

    # 绘制对比图
    plt.plot(test_sizes, chromadb_times, label='ChromaDB', marker='o')
    plt.plot(test_sizes, lancedb_times, label='LanceDB', marker='s')
    plt.xlabel('Number of Records')
    plt.ylabel('Time (seconds)')
    plt.title('ChromaDB vs LanceDB Performance')
    plt.legend()
    plt.savefig('benchmark_results.png')

    print("ChromaDB times:", chromadb_times)
    print("LanceDB times:", lancedb_times)
```

---

## 🚀 迁移步骤

### Phase 1: 准备阶段 (Week 1, Day 1-2)

1. ✅ **代码修改**:
   - 实现`VectorDatabaseAdapter`抽象基类
   - 实现`ChromaDBBackend`（重构现有代码）
   - 实现`LanceDBBackend`（新代码）
   - 修改`MCPSemanticMemory`支持feature flag

2. ✅ **测试**:
   - 单元测试：测试两个后端的独立功能
   - 集成测试：测试feature flag切换
   - 性能测试：benchmark对比

3. ✅ **配置**:
   - 修改`mcp_config.yaml`添加feature flag
   - 准备回滚配置

### Phase 2: 双写验证 (Week 1, Day 3-5)

1. ✅ **启用双写模式**:
   ```yaml
   use_lancedb: true
   enable_dual_write: true  # 同时写入两个后端
   ```

2. ✅ **监控数据一致性**:
   - 每小时对比两个后端的记忆数量
   - 抽样对比搜索结果
   - 记录性能差异

3. ✅ **迁移历史数据**:
   ```python
   # 运行迁移脚本
   python scripts/migrate_chromadb_to_lancedb.py
   ```

### Phase 3: 灰度切换 (Week 2, Day 1-3)

1. ✅ **切换到LanceDB单写**:
   ```yaml
   use_lancedb: true
   enable_dual_write: false  # 关闭双写
   ```

2. ✅ **性能监控** (持续7天):
   - 查询延迟
   - 内存占用
   - 磁盘空间

3. ✅ **回滚准备**:
   - 保留ChromaDB数据库7天
   - 回滚脚本准备

### Phase 4: 清理阶段 (Week 2, Day 4-7)

1. ✅ **移除ChromaDB依赖**:
   - 删除`requirements.txt`中的`chromadb>=0.4.0`
   - 移除`ChromaDBBackend`代码（可选，建议保留6个月）

2. ✅ **文档更新**:
   - 更新PRD，修正Line 48的幻觉描述
   - 创建ADR-002记录迁移决策

---

## 📝 验收标准

### 功能验收
- ✅ 所有单元测试通过 (覆盖率 >95%)
- ✅ Feature flag可正常切换后端
- ✅ 双写模式数据一致性 100%
- ✅ 迁移后数据完整性 100%

### 性能验收
- ✅ 查询延迟 < ChromaDB基线
- ✅ 内存占用 ≤ ChromaDB基线 × 1.2
- ✅ 随机访问速度提升 >50x

### 兼容性验收
- ✅ 调用方代码无需修改
- ✅ API接口签名保持不变
- ✅ 返回数据格式一致

---

## 📚 相关文档

- **调研任务1-A**: ChromaDB → LanceDB 迁移成本评估
- **ADR-002**: LanceDB vs ChromaDB vs Milvus向量库选型 (待创建)
- **Context7文档**: LanceDB API验证 (Zero-Hallucination Research)

---

**文档状态**: ✅ 设计完成，待实施
**下一步**: 创建ADR-002，正式决策向量库选型
