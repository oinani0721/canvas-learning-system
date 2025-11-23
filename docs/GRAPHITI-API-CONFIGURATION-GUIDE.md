# Graphiti API配置完整指南

**版本**: v1.0
**创建日期**: 2025-01-22
**目标用户**: Canvas学习系统用户
**预计完成时间**: 2-4小时

---

## 🎯 **配置目标**

将您已完成的Graphiti知识图谱系统从"代码完成但未激活"状态转变为"完全可用"状态，实现：

- ✅ Canvas概念的智能提取和分析
- ✅ 跨Canvas知识关联和推荐
- ✅ 学习进度的时序追踪
- ✅ 智能检验白板生成优化

---

## 📋 **前置条件检查**

### ✅ **系统状态确认**
运行以下命令确认系统完整性：

```bash
# 1. 检查核心文件存在性
ls -la graphiti_integration.py concept_extractor.py graph_commands.py graph_visualizer.py

# 2. 检查依赖包安装
pip list | grep -E "(graphiti|anthropic|voyage)"

# 3. 检查Neo4j Docker配置
ls -la docker/neo4j-docker-compose.yml
```

**预期结果：**
- ✅ 所有核心文件存在
- ✅ graphiti-core, anthropic包已安装
- ✅ Docker配置文件存在

### ✅ **Neo4j服务启动**
```bash
# 启动Neo4j服务
cd docker
docker-compose -f neo4j-docker-compose.yml up -d

# 验证服务状态
docker-compose -f neo4j-docker-compose.yml ps
```

**预期结果：** Neo4j容器运行正常

---

## 🔑 **步骤1：获取API Keys**

### **1.1 Anthropic API Key**
1. **访问控制台**: https://console.anthropic.com
2. **登录账户**: 使用您的Claude账户
3. **创建API Key**:
   - 点击 "API Keys"
   - 点击 "Create Key"
   - 命名: "Canvas-Graphiti-Integration"
   - 复制生成的Key (格式: `sk-ant-xxx`)
4. **记录Key**: 保存到安全位置

### **1.2 Voyage AI API Key**
1. **访问控制台**: https://dash.voyageai.com
2. **注册/登录**: 创建账户或登录
3. **获取API Key**:
   - 导航到API Keys页面
   - 创建新Key
   - 复制生成的Key (格式: `voyage-xxx`)
4. **记录Key**: 保存到安全位置

**💡 成本预估:**
- Anthropic: ~$2-5/月 (10-20万tokens)
- Voyage AI: ~$1-2/月
- **总计**: ~$3-7/月

---

## ⚙️ **步骤2：配置API Keys**

### **2.1 方法1：配置文件 (推荐)**

创建或编辑配置文件：

```yaml
# config/graphiti_api_config.yaml
api_keys:
  anthropic_api_key: "sk-ant-您的真实API-Key"
  voyage_api_key: "voyage-您的真实API-Key"

llm_provider: "anthropic"
model: "claude-3-5-sonnet-20241022"
embedding_model: "voyage-3"

# 成本控制设置
daily_limits:
  max_requests: 1000
  max_tokens: 100000
  max_cost: 10.0

# 缓存优化
cache_enabled: true
cache_ttl: 3600  # 1小时
```

### **2.2 方法2：环境变量**

```bash
# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="sk-ant-您的真实API-Key"
$env:VOYAGE_API_KEY="voyage-您的真实API-Key"

# Windows (CMD)
set ANTHROPIC_API_KEY=sk-ant-您的真实API-Key
set VOYAGE_API_KEY=voyage-您的真实API-Key

# Linux/MacOS
export ANTHROPIC_API_KEY="sk-ant-您的真实API-Key"
export VOYAGE_API_KEY="voyage-您的真实API-Key"
```

### **2.3 方法3：代码内配置 (临时测试)**

```python
# 测试脚本 test_api_config.py
from graphiti_integration import GraphitiKnowledgeGraph

# 直接传入API Keys进行测试
graphiti = GraphitiKnowledgeGraph(
    anthropic_api_key="sk-ant-您的真实API-Key",
    voyage_api_key="voyage-您的真实API-Key"
)

print("✅ API配置测试成功！")
```

---

## 🔍 **步骤3：验证配置**

### **3.1 基础连接测试**
```python
# test_connection.py
import asyncio
from graphiti_integration import GraphitiKnowledgeGraph

async def test_connection():
    try:
        # 初始化Graphiti
        graphiti = GraphitiKnowledgeGraph()

        # 异步初始化
        await graphiti.initialize()
        print("✅ Neo4j连接成功")

        # 测试基本功能
        test_session = {
            "canvas_file": "test.canvas",
            "session_type": "test",
            "duration_minutes": 5,
            "nodes_interacted": [],
            "learning_outcomes": {"new_concepts_learned": 1}
        }

        session_id = await graphiti.record_learning_session(test_session)
        print(f"✅ 学习会话记录成功: {session_id}")

        await graphiti.close()
        print("✅ 所有测试通过！")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

    return True

# 运行测试
if __name__ == "__main__":
    asyncio.run(test_connection())
```

### **3.2 Canvas集成测试**
```bash
# 测试命令行接口
python -m graph_commands --help

# 测试Canvas分析
python -c "
from graph_commands import GraphCommandHandler
handler = GraphCommandHandler()
print('✅ Graph命令接口正常')
"
```

### **3.3 预期成功标志**
- ✅ Neo4j连接成功
- ✅ API认证通过
- ✅ 学习会话记录成功
- ✅ 概念提取功能正常
- ✅ 错误日志无关键错误

---

## 🚀 **步骤4：首次使用验证**

### **4.1 测试Canvas分析**
选择一个简单的Canvas文件进行测试：

```bash
# 使用您现有的Canvas文件
python -c "
from concept_extractor import ConceptExtractor
extractor = ConceptExtractor()
result = extractor.extract_concepts_from_canvas('笔记库/离散数学/离散数学.canvas')
print(f'提取概念数量: {len(result[\"concepts\"])}')
print(f'提取关系数量: {len(result[\"relationships\"])}')
"
```

### **4.2 测试知识图谱功能**
```bash
# 测试知识图谱记录
python -c "
import asyncio
from graphiti_integration import GraphitiKnowledgeGraph

async def test():
    graphiti = GraphitiKnowledgeGraph()
    await graphiti.initialize()

    # 模拟学习会话
    session = {
        'canvas_file': '笔记库/离散数学/离散数学.canvas',
        'session_type': 'decomposition',
        'duration_minutes': 15,
        'nodes_interacted': [
            {
                'node_id': 'test-node',
                'node_type': 'question',
                'concept_name': '逆否命题',
                'interaction_type': 'created',
                'interaction_outcome': 'success'
            }
        ],
        'learning_outcomes': {
            'new_concepts_learned': 1,
            'concepts_reviewed': 0,
            'weaknesses_identified': 0
        }
    }

    session_id = await graphiti.record_learning_session(session)
    print(f'✅ 知识图谱记录成功: {session_id}')

    await graphiti.close()

asyncio.run(test())
"
```

---

## 📊 **步骤5：成本监控设置**

### **5.1 配置成本限制**
在 `config/graphiti_api_config.yaml` 中设置：

```yaml
# 成本监控配置
cost_monitoring:
  daily_budget: 10.0  # 每日预算($)
  warning_threshold: 8.0  # 警告阈值($)
  enable_alerts: true

# 使用量限制
usage_limits:
  max_daily_requests: 500
  max_daily_tokens: 50000
```

### **5.2 监控脚本**
```python
# monitor_usage.py
from graphiti_api_manager import GraphitiAPIManager

def check_daily_usage():
    manager = GraphitiAPIManager()
    stats = manager.get_usage_stats()

    print("📊 今日使用统计:")
    print(f"请求数量: {stats['daily']['requests']}")
    print(f"Token使用: {stats['daily']['tokens']}")
    print(f"预计成本: ${stats['daily']['cost']:.2f}")

    # 成本警告
    if stats['daily']['cost'] > 8.0:
        print("⚠️ 接近日成本预算！")

if __name__ == "__main__":
    check_daily_usage()
```

---

## 🔧 **步骤6：故障排除**

### **6.1 常见问题及解决方案**

#### **问题1：API Key无效**
```
错误: Authentication failed
解决: 检查API Key是否正确复制，账户是否有足够余额
```

#### **问题2：Neo4j连接失败**
```
错误: Connection to Neo4j failed
解决: 确认Docker容器运行正常，端口7687可访问
```

#### **问题3：依赖包缺失**
```
错误: ModuleNotFoundError: No module named 'graphiti_core'
解决: pip install graphiti-core[anthropic,voyage]
```

#### **问题4：权限错误**
```
错误: Permission denied
解决: 检查文件权限，确保可读写配置文件
```

### **6.2 日志检查**
```bash
# 查看应用日志
tail -f logs/graphiti.log

# 查看Neo4j日志
docker logs neo4j-container
```

---

## 📈 **步骤7：性能优化建议**

### **7.1 缓存优化**
```yaml
# 在配置文件中启用缓存
cache_enabled: true
cache_ttl: 7200  # 2小时缓存
```

### **7.2 批处理优化**
```yaml
# 批处理设置
batch_size: 10
batch_enabled: true
```

### **7.3 模型选择优化**
- **复杂分析**: 使用 `claude-3-5-sonnet-20241022`
- **简单任务**: 可考虑使用更便宜的模型
- **嵌入**: `voyage-3` 已是性价比最佳选择

---

## 🎉 **验证完成清单**

当您完成以下所有项目时，配置即完成：

- [ ] API Keys已获取并安全存储
- [ ] 配置文件已正确设置
- [ ] Neo4j服务正常运行
- [ ] 基础连接测试通过
- [ ] Canvas分析功能正常
- [ ] 知识图谱记录成功
- [ ] 成本监控已设置
- [ ] 故障排除脚本已准备

---

## 📞 **技术支持**

如果遇到问题：

1. **查看日志**: `logs/graphiti.log`
2. **运行诊断**: `python test_connection.py`
3. **检查配置**: `python -c "import yaml; print(yaml.safe_load(open('config/graphiti_api_config.yaml')))"`
4. **重启服务**: 重启Neo4j Docker容器

---

## 🚀 **下一步行动**

配置完成后，您可以：

1. **开始使用**：在Canvas学习中启用知识图谱功能
2. **监控成本**：每日检查API使用情况
3. **优化设置**：根据使用习惯调整配置
4. **扩展功能**：探索高级知识图谱功能

**🎯 您的Graphiti知识图谱系统即将完全激活！**