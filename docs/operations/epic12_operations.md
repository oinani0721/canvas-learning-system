# Epic 12 运维手册

## 1. 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    Canvas Learning System v2.0                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐│
│  │     Graphiti     │  │     LanceDB      │  │    Temporal      ││
│  │    (Layer 1)     │  │    (Layer 2)     │  │    (Layer 3)     ││
│  │  时序知识图谱     │  │   向量数据库      │  │  FSRS复习调度    ││
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘│
│           │                     │                      │          │
│           └─────────────────────┼──────────────────────┘          │
│                                 │                                 │
│                         ┌───────▼───────┐                         │
│                         │  Agentic RAG  │                         │
│                         │  (LangGraph)  │                         │
│                         │               │                         │
│                         │ - 并行检索    │                         │
│                         │ - 融合策略    │                         │
│                         │ - Reranking   │                         │
│                         │ - 质量控制    │                         │
│                         └───────────────┘                         │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
        ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
        │   Neo4j   │   │  LanceDB  │   │  LangSmith│
        │  (Graph)  │   │  (Vector) │   │ (Tracing) │
        │           │   │           │   │           │
        │ Port:7687 │   │ 嵌入式    │   │  云服务   │
        └───────────┘   └───────────┘   └───────────┘
```

## 2. 依赖服务部署

### 2.1 Neo4j

**Docker部署（推荐）**:
```bash
# 创建数据卷
docker volume create neo4j_data

# 启动Neo4j
docker run -d \
  --name neo4j-canvas \
  --restart unless-stopped \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password123 \
  -e NEO4J_PLUGINS='["apoc"]' \
  -v neo4j_data:/data \
  neo4j:5.15

# 验证启动
curl http://localhost:7474
```

**本地安装**:
```bash
# macOS
brew install neo4j

# Windows (下载安装包)
# https://neo4j.com/download/

# 启动
neo4j start

# 设置密码
cypher-shell -u neo4j -p neo4j
# > ALTER CURRENT USER SET PASSWORD FROM 'neo4j' TO 'password123';
```

**验证连接**:
```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "password123")
)
driver.verify_connectivity()
print("Neo4j connection OK")
driver.close()
```

### 2.2 LanceDB

LanceDB是嵌入式数据库，无需单独部署服务。

```bash
# 安装
pip install lancedb>=0.6.0

# 创建数据目录
mkdir -p data/lancedb

# 验证
python -c "import lancedb; db = lancedb.connect('./data/lancedb'); print('LanceDB OK')"
```

**数据目录结构**:
```
data/lancedb/
├── canvas_nodes.lance/     # Canvas节点向量
├── concepts.lance/         # 概念向量
└── metadata.json           # 元数据
```

### 2.3 CUDA加速（可选）

如果有NVIDIA GPU，可启用CUDA加速：

```bash
# 检查CUDA
nvidia-smi

# 安装PyTorch CUDA版本
pip install torch --index-url https://download.pytorch.org/whl/cu118

# 验证
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

## 3. 环境变量配置

创建 `.env` 文件：

```bash
# ====================
# Neo4j配置
# ====================
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123
NEO4J_DATABASE=canvas_memory

# ====================
# LanceDB配置
# ====================
LANCEDB_PATH=./data/lancedb

# ====================
# Cohere配置（可选，用于高质量Reranking）
# ====================
COHERE_API_KEY=your_cohere_api_key

# ====================
# LangSmith配置（可选，用于追踪）
# ====================
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=ls_your_key
LANGSMITH_PROJECT=canvas-learning-system

# ====================
# OpenAI配置（用于Query重写）
# ====================
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o-mini

# ====================
# 性能配置
# ====================
AGENTIC_RAG_TIMEOUT_MS=5000
AGENTIC_RAG_MAX_RETRIES=2
PARALLEL_RETRIEVAL_WORKERS=4

# ====================
# 成本控制
# ====================
COHERE_MONTHLY_BUDGET=3.0
OPENAI_MONTHLY_BUDGET=1.0
TOTAL_MONTHLY_BUDGET=5.0
```

## 4. 健康检查

### 4.1 服务健康检查脚本

```bash
# 运行完整健康检查
python scripts/health_check_epic12.py

# 预期输出:
# ========================================
# Epic 12 Health Check
# ========================================
# [OK] Neo4j: Connected (bolt://localhost:7687)
# [OK] LanceDB: Ready (./data/lancedb)
# [OK] Graphiti: Initialized (15 nodes, 42 edges)
# [OK] Agentic RAG: Compiled
# [OK] FSRS: Initialized
# [OK] LangSmith: Connected
# ========================================
# All checks passed!
# ========================================
```

### 4.2 API健康端点

```bash
# 基础健康检查
curl http://localhost:8000/health
# {"status": "healthy", "version": "2.0.0"}

# 详细健康检查
curl http://localhost:8000/health/detailed
# {
#   "status": "healthy",
#   "components": {
#     "neo4j": {"status": "ok", "latency_ms": 5},
#     "lancedb": {"status": "ok", "tables": 3},
#     "agentic_rag": {"status": "ok", "compiled": true},
#     "langsmith": {"status": "ok", "tracing": true}
#   }
# }
```

### 4.3 定时健康检查

添加到crontab：
```bash
# 每5分钟检查一次
*/5 * * * * python /path/to/scripts/health_check_epic12.py >> /var/log/canvas_health.log 2>&1
```

## 5. 故障排查

### 5.1 Neo4j连接失败

**症状**:
```
ConnectionError: Unable to connect to Neo4j at bolt://localhost:7687
```

**排查步骤**:
```bash
# 1. 检查Neo4j容器状态
docker ps | grep neo4j
docker logs neo4j-canvas --tail 50

# 2. 检查端口占用
netstat -an | grep 7687

# 3. 测试连接
curl http://localhost:7474

# 4. 重启Neo4j
docker restart neo4j-canvas

# 5. 检查防火墙
# Windows: netsh advfirewall firewall show rule name=all | findstr 7687
# Linux: sudo ufw status | grep 7687
```

**常见原因**:
- Docker未启动
- 端口被占用
- 密码错误
- 内存不足

### 5.2 检索延迟过高

**症状**:
```
P95 latency > 400ms
```

**排查步骤**:
```bash
# 1. 检查Neo4j查询性能
cypher-shell -u neo4j -p password123
> PROFILE MATCH (n:Concept) RETURN n LIMIT 100;

# 2. 检查索引
> SHOW INDEXES;
> CREATE INDEX FOR (n:Concept) ON (n.name);

# 3. 检查LangSmith追踪
# 访问 https://smith.langchain.com/ 查看详细延迟

# 4. 检查网络延迟
ping localhost

# 5. 检查系统资源
top -p $(pgrep -f neo4j)
```

**优化建议**:
- 添加必要的索引
- 增加Neo4j内存配置
- 启用查询缓存
- 考虑使用SSD

### 5.3 Cohere API失败

**症状**:
```
WARNING: Cohere rerank failed, falling back to local
```

**排查步骤**:
```bash
# 1. 检查API Key
echo $COHERE_API_KEY

# 2. 测试API连接
curl -X POST "https://api.cohere.ai/v1/rerank" \
  -H "Authorization: Bearer $COHERE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "documents": ["doc1"]}'

# 3. 检查限流状态
# 访问 https://dashboard.cohere.com/ 查看用量

# 4. 检查网络
curl -I https://api.cohere.ai
```

**处理方式**:
- 系统会自动降级到Local Reranking
- 检查API配额
- 考虑增加重试次数

### 5.4 LanceDB写入失败

**症状**:
```
OSError: Failed to write to LanceDB
```

**排查步骤**:
```bash
# 1. 检查磁盘空间
df -h ./data/lancedb

# 2. 检查目录权限
ls -la ./data/lancedb

# 3. 检查文件锁
lsof +D ./data/lancedb

# 4. 验证数据完整性
python -c "
import lancedb
db = lancedb.connect('./data/lancedb')
for table in db.table_names():
    print(f'{table}: {len(db.open_table(table))} rows')
"
```

### 5.5 FSRS调度异常

**症状**:
```
复习提醒时间不合理或缺失
```

**排查步骤**:
```python
# 检查FSRS状态
from src.agentic_rag.clients.fsrs_client import FSRSClient

client = FSRSClient()
status = client.get_status()
print(f"Cards: {status['total_cards']}")
print(f"Due today: {status['due_today']}")
print(f"Last sync: {status['last_sync']}")
```

## 6. 成本监控

### 6.1 成本阈值配置

| 服务 | 月度阈值 | 告警级别 |
|------|----------|----------|
| Cohere | $3 | Warning at 80%, Critical at 100% |
| OpenAI | $1 | Warning at 80%, Critical at 100% |
| 总计 | $5 | Critical at 100% |

### 6.2 查看成本

```bash
# 命令行查看
python scripts/check_costs.py

# 输出示例:
# ========================================
# Epic 12 Cost Report (2025-11)
# ========================================
# Cohere:  $1.25 / $3.00 (41.7%)
# OpenAI:  $0.35 / $1.00 (35.0%)
# Total:   $1.60 / $5.00 (32.0%)
# ========================================
# Status: OK
# ========================================
```

### 6.3 LangSmith成本面板

访问: https://smith.langchain.com/

查看:
- 按项目的成本分布
- 按时间的成本趋势
- 按操作类型的成本明细

### 6.4 成本告警配置

```python
# config/cost_alerts.py
COST_ALERTS = {
    "cohere": {
        "warning_threshold": 0.8,  # 80%
        "critical_threshold": 1.0,  # 100%
        "action": "notify_admin"
    },
    "openai": {
        "warning_threshold": 0.8,
        "critical_threshold": 1.0,
        "action": "switch_to_local"
    }
}
```

## 7. 备份和恢复

### 7.1 Neo4j备份

```bash
# 创建备份
docker exec neo4j-canvas neo4j-admin database dump neo4j --to-path=/backup

# 从容器复制备份
docker cp neo4j-canvas:/backup ./backups/neo4j_$(date +%Y%m%d)

# 恢复备份
docker cp ./backups/neo4j_20251128 neo4j-canvas:/backup
docker exec neo4j-canvas neo4j-admin database load neo4j --from-path=/backup --overwrite-destination=true
```

### 7.2 LanceDB备份

```bash
# LanceDB是文件型数据库，直接复制目录即可

# 备份
cp -r data/lancedb backups/lancedb_$(date +%Y%m%d)

# 恢复
rm -rf data/lancedb
cp -r backups/lancedb_20251128 data/lancedb
```

### 7.3 完整系统备份

```bash
# 运行备份脚本
./scripts/backup_epic12.sh

# 脚本内容:
#!/bin/bash
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Neo4j
docker exec neo4j-canvas neo4j-admin database dump neo4j --to-path=/tmp/neo4j_backup
docker cp neo4j-canvas:/tmp/neo4j_backup $BACKUP_DIR/neo4j

# LanceDB
cp -r data/lancedb $BACKUP_DIR/lancedb

# 配置文件
cp .env $BACKUP_DIR/

# 压缩
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR

echo "Backup created: $BACKUP_DIR.tar.gz"
```

### 7.4 定时备份

```bash
# 每日凌晨2点备份
0 2 * * * /path/to/scripts/backup_epic12.sh >> /var/log/canvas_backup.log 2>&1
```

## 8. 性能调优

### 8.1 Neo4j调优

```bash
# neo4j.conf
dbms.memory.heap.initial_size=512m
dbms.memory.heap.max_size=1G
dbms.memory.pagecache.size=512m

# 查询缓存
dbms.query_cache_size=1000

# 连接池
dbms.connector.bolt.thread_pool_min_size=4
dbms.connector.bolt.thread_pool_max_size=40
```

### 8.2 LanceDB调优

```python
# 配置并行度
import lancedb

db = lancedb.connect(
    "./data/lancedb",
    read_consistency_interval=timedelta(seconds=0),  # 实时一致性
)

# 批量写入优化
table.add(data, mode="append")  # 追加模式
table.create_index(metric="cosine")  # 创建向量索引
```

### 8.3 并行检索调优

```python
# config/agentic_rag.py
PARALLEL_RETRIEVAL_CONFIG = {
    "max_workers": 4,
    "timeout_per_source": 2.0,  # 秒
    "retry_count": 2,
    "backoff_factor": 0.5
}
```

---

## 附录: 常用命令

```bash
# 启动所有服务
./scripts/start_services.sh

# 停止所有服务
./scripts/stop_services.sh

# 查看日志
tail -f logs/canvas.log

# 运行健康检查
python scripts/health_check_epic12.py

# 查看成本报告
python scripts/check_costs.py

# 创建备份
./scripts/backup_epic12.sh

# 恢复备份
./scripts/restore_epic12.sh backups/20251128_020000.tar.gz

# 清理旧数据
python scripts/cleanup_old_data.py --days 30

# 重建索引
python scripts/rebuild_indexes.py
```

---

## 版本信息

- **文档版本**: 1.0
- **适用版本**: Epic 12 (v2.0.0)
- **最后更新**: 2025-11-29
