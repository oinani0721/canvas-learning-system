# Gemini API 快速配置指南

**版本**: v1.0
**创建日期**: 2025-01-22
**适用系统**: Canvas学习系统 + Graphiti知识图谱

---

## 🎯 **配置完成状态检查**

恭喜！您的Gemini API配置文件已创建完成。现在需要进行最后的验证和启动。

### ✅ **已完成的工作**
1. **API配置文件**: `config/gemini_api_config.yaml`
2. **Gemini客户端**: `gemini_llm_client.py`
3. **Graphiti集成**: `graphiti_gemini_integration.py`
4. **测试脚本**: `test_gemini_setup.py`

---

## 🚀 **立即执行步骤**

### **步骤1：启动Neo4j数据库**
```bash
# 进入docker目录
cd docker

# 启动Neo4j服务
docker-compose -f neo4j-docker-compose.yml up -d

# 验证服务状态
docker-compose -f neo4j-docker-compose.yml ps
```

**预期结果：** Neo4j容器运行状态为 "Up"

### **步骤2：验证配置**
```bash
# 运行测试脚本
python test_gemini_setup.py
```

**预期成功标志：**
- ✅ API连接测试通过
- ✅ Neo4j连接测试通过
- ✅ Canvas分析测试通过
- ✅ 知识图谱测试通过

### **步骤3：开始使用**

#### **3.1 Canvas分析测试**
```python
# 创建测试脚本
python -c "
import asyncio
from graphiti_gemini_integration import GraphitiGeminiIntegration

async def test():
    integration = GraphitiGeminiIntegration()
    await integration.initialize()

    # 分析您的Canvas文件
    result = await integration.analyze_canvas_with_gemini('笔记库/离散数学/离散数学.canvas')
    print(f'分析完成: {len(result[\"analysis_result\"][\"concepts\"])} 个概念')

    await integration.close()

asyncio.run(test())
"
```

#### **3.2 学习会话记录**
```python
# 记录学习会话
python -c "
import asyncio
from graphiti_gemini_integration import GraphitiGeminiIntegration

async def test():
    integration = GraphitiGeminiIntegration()
    await integration.initialize()

    session_data = {
        'canvas_file': '笔记库/离散数学/离散数学.canvas',
        'session_type': 'decomposition',
        'duration_minutes': 15,
        'learning_outcomes': {
            'new_concepts_learned': 3,
            'concepts_reviewed': 2
        }
    }

    session_id = await integration.record_learning_session(session_data)
    print(f'学习会话记录成功: {session_id}')

    await integration.close()

asyncio.run(test())
"
```

---

## 📊 **API配置详情**

### **您的API信息**
- **API地址**: `https://binapi.shop/v1`
- **API Key**: `sk-Bu198hR8AgONygQQnVfWeZ2cS4lzryBgN0pSRubmSurAK4IF`
- **模型**: `gemini-2.5-flash-preview-05-20-thinking`

### **配置文件位置**
- **主配置**: `config/gemini_api_config.yaml`
- **日志文件**: `logs/gemini_graphiti.log`

### **成本预估**
- **Gemini 2.5 Flash Thinking**: ~$0.000125/1K tokens (更经济)
- **预估月度成本**: $1-3 (正常使用)
- **首次测试成本**: ~$0.05

**优势**: Gemini 2.5 Flash Thinking 模型不仅成本更低，还具备更强的推理能力！

---

## 🔧 **故障排除**

### **问题1：API连接失败**
```
错误: Connection failed
解决:
1. 检查网络连接
2. 确认API Key正确
3. 验证API地址可用性
```

### **问题2：Neo4j连接失败**
```
错误: Neo4j connection failed
解决:
1. 确认Docker运行: docker ps
2. 重启服务: docker-compose restart
3. 检查端口: netstat -an | grep 7687
```

### **问题3：Canvas文件不存在**
```
错误: Canvas文件不存在
解决:
1. 确认文件路径正确
2. 检查文件权限
3. 使用绝对路径
```

### **问题4：权限错误**
```
错误: Permission denied
解决:
1. 检查文件读写权限
2. 确认目录存在
3. 使用管理员权限运行
```

---

## 📈 **性能优化建议**

### **API调用优化**
1. **批量处理**: 一次分析多个概念
2. **缓存启用**: 已在配置中启用
3. **温度设置**: 0.7 (平衡创造性和准确性)

### **数据库优化**
1. **索引已创建**: 自动建立必要索引
2. **连接池**: 使用连接池提高性能
3. **定期维护**: 建议每周清理旧数据

---

## 🎉 **成功验证标志**

当您看到以下内容时，配置完成：

```
🚀 开始Graphiti-Gemini集成测试
============================================================
✅ API连接测试通过
✅ Neo4j连接测试通过
✅ Canvas分析测试通过
✅ 知识图谱测试通过

📊 测试结果总结
============================================================
API连接              ✅ 通过
Neo4j连接            ✅ 通过
Canvas分析          ✅ 通过
知识图谱            ✅ 通过

总计: 4/4 项测试通过

🎉 所有测试通过！您的Graphiti-Gemini系统配置成功！
```

---

## 📞 **技术支持**

如果遇到问题：

1. **查看日志**: `tail -f logs/gemini_graphiti.log`
2. **重新测试**: `python test_gemini_setup.py`
3. **检查配置**: 确认 `config/gemini_api_config.yaml` 内容正确
4. **重启服务**: 重启Neo4j Docker容器

---

## 🚀 **下一步行动**

配置完成后，您可以：

1. **开始学习**: 在Canvas中使用智能分析功能
2. **记录进度**: 自动记录学习会话到知识图谱
3. **查看统计**: 监控API使用和成本
4. **优化设置**: 根据使用习惯调整配置

**您的Gemini驱动的智能学习系统已经准备就绪！🎯**
