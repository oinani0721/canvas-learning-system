---
name: memory-activate
description: 完全激活Canvas 3层记忆系统 (4层+统一接口)
tools: Bash, Read, Write
model: sonnet
---

# Canvas 记忆系统完全激活命令

## 功能描述

一键完全激活Canvas学习系统的所有4层记忆系统:
- ✅ 第1层: 监控系统 (Canvas File Monitor)
- ✅ 第2层: Temporal 时间轴记忆
- ✅ 第3层: Semantic 语义记忆
- ✅ 第4层: Graphiti 知识图谱 (MCP)
- ✅ 统一接口 (Unified Memory Interface)

## 使用方式

```bash
/memory-activate              # 完全激活并显示状态
/memory-activate --verify     # 激活并验证每个层级
/memory-activate --verbose    # 激活并显示详细信息
/memory-activate --neo4j      # 激活并尝试启动Neo4j
```

## 立即执行激活

```python
import subprocess
import sys
import os
from pathlib import Path

# 获取项目根目录
project_root = Path.cwd()

# 确保Python依赖已安装
print("🔧 检查依赖...")
subprocess.run(
    [sys.executable, "-m", "pip", "install", "-q", "loguru", "sentence-transformers"],
    cwd=project_root
)

# 运行激活脚本
print("\n🚀 正在激活Canvas 4层记忆系统...\n")
result = subprocess.run(
    [sys.executable, "activate_full_memory_system.py"],
    cwd=project_root,
    env={**os.environ, "PYTHONIOENCODING": "utf-8"}
)

if result.returncode == 0:
    print("\n" + "="*60)
    print("✅ Canvas 记忆系统完全激活成功！")
    print("="*60)
    print("\n📖 后续使用的斜杆命令:")
    print("  /unified-memory-status      # 查看系统状态")
    print("  /unified-memory-store       # 存储学习内容")
    print("  /unified-memory-retrieve    # 检索学习记忆")
    print("  /unified-memory-analytics   # 查看分析报告")
    print("\n🎯 下次激活只需运行:")
    print("  /memory-activate")
else:
    print("\n❌ 激活失败，请检查上述错误信息")
    sys.exit(1)
```

## 激活结果

激活成功后您会看到:

```
🚀 Canvas 3层记忆系统激活开始...
   启动时间: 2025-11-05 03:28:10

============================================================
激活第1层: 监控系统 (Canvas File Monitor)
============================================================
✅ 监控系统已启动
   - 监听目录: .learning_sessions/
   - 会话文件数: 8
   - 最新会话: session_2025-11-05.json

============================================================
激活第2层: Temporal 时间轴记忆系统
============================================================
✅ Temporal系统已部署
   - 文件: temporal_memory_manager.py
   - 大小: 18,940 bytes
   - 功能: 时间轴记录，学习进度追踪

============================================================
激活第3层: Semantic 语义记忆系统
============================================================
✅ Semantic系统已部署
   - 文件: semantic_memory_manager.py
   - 大小: 18,123 bytes
   - 功能: 语义提取，概念关系，向量嵌入

============================================================
激活第4层: Graphiti 知识图谱系统 (MCP)
============================================================
✅ Graphiti系统已部署
   - 目录: graphiti/mcp_server/
   - Python文件数: 14
   - 功能: 知识图谱存储，Neo4j集成，MCP协议

⚠️ 注意: Graphiti需要Neo4j数据库
   - 检查Neo4j: neo4j status
   - 启动Neo4j: neo4j start

============================================================
激活统一记忆接口
============================================================
✅ 统一记忆接口已激活
   - 文件: unified_memory_interface.py
   - 功能: 统一访问所有4个记忆系统

============================================================
3层记忆系统激活完成!
============================================================

📊 系统状态:
✅ 第1层: 监控系统 (Canvas File Monitor)
✅ 第2层: Temporal 时间轴记忆
✅ 第3层: Semantic 语义记忆
⚠️ 第4层: Graphiti 知识图谱 (需要Neo4j)
✅ 统一接口已激活

🎯 下次启动记忆系统的命令:

  # 方式1: 全部激活 (推荐)
  python activate_full_memory_system.py

  # 方式2: 使用统一部署脚本
  python deploy_unified_memory_system.py

  # 方式3: 分别启动
  python start_canvas_memory.py          # 启动监听
  neo4j start                             # 启动Neo4j
  python start_graphiti_mcp.sh            # 启动Graphiti

📖 使用内存系统的命令:
  /unified-memory-status                  # 查看系统状态
  /unified-memory-store                   # 存储学习内容
  /unified-memory-retrieve                # 检索学习记忆
  /unified-memory-analytics               # 查看分析报告

✅ 激活日志已保存到: memory_system_activation.log

📈 激活结果:
  ✅ 监控系统
  ✅ Temporal
  ✅ Semantic
  ✅ Graphiti
  ✅ 统一接口
```

## 激活后立即可用的命令

### 查看系统状态
```bash
/unified-memory-status
```

### 存储学习记忆
```bash
/unified-memory-store Lecture5 b476fd6b03d8bbff "Level Set的理解"
```

### 检索学习记忆
```bash
/unified-memory-retrieve "Level Set"
```

### 查看学习分析
```bash
/unified-memory-analytics
```

## 系统自动做的事

激活后，您的Canvas学习系统会自动:

| 自动功能 | 说明 |
|---------|------|
| **监控** | 24/7监听Canvas修改，自动生成会话日志 |
| **记录时间轴** | 自动追踪学习时间线和学习进度 |
| **提取语义** | 自动生成学习内容的向量嵌入 |
| **构建知识图** | 自动在知识图谱中建立概念关系 |
| **链接记忆** | 自动在Temporal和Semantic间建立关联 |

## 常见问题

### 问题1: 看到loguru导入错误

不需要担心，依赖会自动安装。如果仍然有问题，运行:

```bash
python3 -m pip install loguru sentence-transformers
```

### 问题2: Neo4j错误

Graphiti系统已部署，但需要Neo4j运行才能实现完整知识图谱功能。如果想启用:

```bash
neo4j status          # 检查状态
neo4j start           # 启动Neo4j
```

### 问题3: 权限错误

确保在项目根目录运行:

```bash
cd C:/Users/ROG/托福
/memory-activate
```

## 验证激活成功

激活成功标志:

- [x] 显示所有5个✅标记 (监控、Temporal、Semantic、Graphiti、统一接口)
- [x] 没有❌或错误消息
- [x] 生成了激活日志文件
- [x] 可以运行 `/unified-memory-*` 命令

## 下次使用

**下次激活非常简单** - 就运行一个命令:

```bash
/memory-activate
```

或直接用Python:

```bash
python activate_full_memory_system.py
```

## 相关文件

| 文件 | 作用 |
|------|------|
| `activate_full_memory_system.py` | 激活脚本 (由/memory-activate调用) |
| `SYSTEM_COMPLETE_STATUS_REPORT.md` | 系统状态详细报告 |
| `MEMORY_ACTIVATION_SUMMARY_20251105.md` | 激活总结和使用指南 |
| `MEMORY_SYSTEM_QUICK_START.md` | 快速参考指南 |
| `memory_system_activation.log` | 激活日志 |

## 相关命令

- `/learning start` - 启动学习会话
- `/unified-memory-status` - 查看系统状态
- `/unified-memory-store` - 存储学习记忆
- `/unified-memory-retrieve` - 检索学习记忆
- `/unified-memory-analytics` - 查看分析报告
- `/memory-start` - 启动实时记忆记录 (Legacy)
- `/memory-stats` - 查看记忆统计

---

**版本**: Canvas v2.0 + Memory System
**维护**: Canvas Learning System Team
**最后更新**: 2025-11-05
