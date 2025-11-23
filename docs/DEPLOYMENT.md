# Canvas Learning System - 部署文档

**版本**: v1.0
**最后更新**: 2025-10-31
**预计部署时间**: ≤ 5分钟 (假设Neo4j已安装)

---

## 📋 目录

- [首次部署（5分钟）](#首次部署5分钟)
- [常见问题排查](#常见问题排查)
- [环境配置参考](#环境配置参考)
- [Troubleshooting快速参考](#troubleshooting快速参考)

---

## 🚀 首次部署（5分钟）

### 前置要求

在开始部署前，请确保以下软件已安装:

| 软件 | 版本要求 | 用途 | 下载链接 |
|------|---------|------|---------|
| **Windows** | 10/11 | 操作系统 | - |
| **Python** | 3.9+ | 运行环境 | [python.org](https://www.python.org/downloads/) |
| **Neo4j** | 4.4+ | 图数据库 | [neo4j.com](https://neo4j.com/download/) |

**注意**: 本系统已在 **Neo4j 6.0.2 Desktop** 上测试通过。

---

### 部署步骤

#### **步骤1: 安装Python依赖** (1分钟)

```bash
cd "C:\Users\ROG\托福"
pip install -r requirements.txt
```

**验证**: 运行以下命令应无错误输出
```bash
python -c "import graphiti_core, neo4j, dotenv; print('所有依赖已安装')"
```

---

#### **步骤2: 配置环境变量** (1分钟)

```bash
# 1. 复制.env模板
copy .env.example .env

# 2. 编辑.env文件，填写Neo4j密码
notepad .env
```

**必填字段**:
```ini
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password    # ⚠️ 请修改为实际密码
NEO4J_DATABASE=ultrathink
```

---

#### **步骤3: 验证Neo4j连接** (30秒)

```bash
# 1. 确保Neo4j已启动
neo4j.bat console

# 2. 等待启动完成（看到 "Started" 消息）

# 3. 运行连接测试
python deployment\test_neo4j_setup.py
```

**成功标志**:
```
✅ Socket连接: PASS
✅ Authentication: PASS
✅ Database available: PASS
```

---

#### **步骤4: 启动MCP服务器** (30秒)

```bash
deployment\start_all_mcp_servers.bat
```

**预期输出**:
```
正在启动 MCP Graphiti 服务器...
服务器已启动 (PID: XXXX)
```

---

#### **步骤5: 运行环境诊断** (30秒)

```bash
python deployment\diagnose_environment.py
```

**成功标志**: 所有7项检查应显示 ✅
```
[✅] Python版本: Python 3.x.x
[✅] pip包: 所有必需包已安装
[✅] 环境变量: 所有环境变量已设置
[✅] Neo4j连接: Neo4j连接成功
[✅] Neo4j数据库: 数据库 'ultrathink' 存在并可用
[✅] MCP Graphiti服务器: MCP Graphiti服务器运行正常
[✅] MCP memory client导入: mcp_memory_client.py 可以正常导入
```

---

#### **步骤6: 运行完整启动测试** (1分钟)

```bash
pytest deployment\test_full_startup.py -v
```

**成功标志**:
```
test_startup_full_mode PASSED
test_startup_partial_mode_graphiti_down PASSED
test_startup_basic_mode PASSED
```

---

#### **步骤7: 启动Canvas Learning System** (30秒)

```bash
# 在Claude Code中运行
/learning
```

**成功标志**:
```
✅ 会话已启动，3/3 记忆系统正常运行
```

---

## 🔧 常见问题排查

### 问题1: Neo4j连接失败 - "Connection Refused"

**症状**:
```
❌ Neo4j连接: Neo4j端口7687不可达
```

**原因**: Neo4j数据库未启动

**解决方案**:
```bash
neo4j.bat console
```

**预计修复时间**: 1分钟

---

### 问题2: Neo4j认证失败 - "Authentication Failed"

**症状**:
```
❌ Neo4j连接: 身份验证失败
```

**原因**: .env文件中的NEO4J_PASSWORD不正确

**解决方案**:
1. 检查.env文件: `notepad .env`
2. 验证NEO4J_PASSWORD是否正确
3. 如忘记密码，重置: `neo4j-admin set-initial-password new_password`

**预计修复时间**: 2分钟

---

### 问题3: 数据库不存在

**症状**:
```
❌ Neo4j数据库: 数据库 'ultrathink' 不存在
```

**解决方案**:
在Neo4j Browser中执行:
```cypher
CREATE DATABASE ultrathink
```

**预计修复时间**: 30秒

---

### 问题4: MCP服务器不可用

**症状**:
```
❌ MCP Graphiti服务器: MCP服务器不可用
```

**解决方案**:
```bash
deployment\start_all_mcp_servers.bat
```

**预计修复时间**: 30秒

---

### 问题5: mcp_memory_client导入失败

**症状**:
```
❌ MCP memory client导入: 导入错误
```

**解决方案**:
```bash
python deployment\diagnose_mcp_client.py
pip install chromadb sentence-transformers torch
```

**预计修复时间**: 2分钟

---

### 问题6: Python版本过低

**症状**:
```
❌ Python版本: Python 3.8.x
```

**解决方案**:
下载并安装Python 3.9+: https://www.python.org/downloads/

**预计修复时间**: 10分钟

---

### 问题7: pip包缺失

**症状**:
```
❌ pip包: 缺少包
```

**解决方案**:
```bash
pip install -r requirements.txt
```

**预计修复时间**: 2分钟

---

### 问题8: 环境变量未设置

**症状**:
```
❌ 环境变量: 缺少环境变量
```

**解决方案**:
```bash
copy .env.example .env
notepad .env
```

**预计修复时间**: 30秒

---

## ⚙️ 环境配置参考

### 环境变量说明

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `NEO4J_URI` | ✅ | `bolt://localhost:7687` | Neo4j连接URI |
| `NEO4J_USERNAME` | ✅ | `neo4j` | Neo4j用户名 |
| `NEO4J_PASSWORD` | ✅ | (无默认值) | Neo4j密码 |
| `NEO4J_DATABASE` | ✅ | `ultrathink` | 数据库名称 |

---

### 目录结构

```
C:/Users/ROG/托福/
├── .env                              # 环境变量配置（必需）
├── .semantic_cache.db                # 语义记忆SQLite缓存（自动创建）
├── deployment/
│   ├── diagnose_environment.py       # 环境诊断工具
│   ├── setup_environment.bat         # 环境配置向导
│   ├── start_all_mcp_servers.bat     # MCP服务器启动脚本
│   └── test_full_startup.py          # 完整启动测试
└── graphiti/
    └── mcp_server/
        └── start_graphiti_mcp.bat    # Graphiti MCP服务器启动脚本
```

---

## 📊 Troubleshooting快速参考

| 错误症状 | 可能原因 | 诊断命令 | 快速修复 | 预计时间 |
|---------|---------|---------|---------|---------|
| "Connection Refused" | Neo4j未启动 | `neo4j.bat status` | `neo4j.bat console` | 1分钟 |
| "Authentication Failed" | 密码错误 | 检查.env文件 | 修改NEO4J_PASSWORD | 30秒 |
| "MCP服务器不可用" | MCP未启动 | `tasklist \| find "python"` | `start_all_mcp_servers.bat` | 30秒 |
| "数据库'ultrathink'不存在" | 数据库未创建 | Neo4j Browser | `CREATE DATABASE ultrathink` | 30秒 |
| "导入mcp_memory_client失败" | 模块缺失 | `diagnose_mcp_client.py` | `pip install chromadb` | 2分钟 |
| "Python版本过低" | Python<3.9 | `python --version` | 升级Python | 10分钟 |
| "pip包缺失" | 依赖未安装 | `pip list` | `pip install -r requirements.txt` | 2分钟 |
| "环境变量未设置" | .env文件缺失 | `if exist .env` | `copy .env.example .env` | 30秒 |

---

## 🛟 获取帮助

如果遇到问题:

1. **运行综合诊断**:
   ```bash
   python deployment\diagnose_environment.py
   ```

2. **查看错误日志**:
   - Canvas错误日志: `CANVAS_ERROR_LOG.md`
   - Debug日志: `.ai/debug-log.md`

3. **联系支持**:
   - GitHub Issues
   - 文档中心: `docs/`

---

**文档版本**: v1.0
**最后更新**: 2025-10-31
**维护者**: Canvas Learning System Team
