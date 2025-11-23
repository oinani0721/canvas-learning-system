---
name: learning
description: 统一学习会话管理系统 - 真实启动和管理记忆系统
tools: Bash, Read, Write
model: sonnet
---

# Canvas学习会话统一管理系统

## 概述

提供统一的学习会话启动和管理功能，真实初始化三个记忆系统（Graphiti知识图谱、时序记忆管理器、语义记忆管理器），实现一键启动的便捷体验。

**性能优化**: Story 10.13实现快速启动，目标<5秒（绕过命令解析时）、<20秒（优化命令）、<2秒（缓存命中）。

## 核心命令

### `/learning start <canvas_path> [options]`

启动学习会话，真实初始化所有记忆系统。

**参数:**
- `canvas_path`: Canvas文件路径（必需）
- `--user-id`: 用户ID（默认: default）
- `--session-name`: 会话名称（默认: 自动生成）
- `--duration`: 预计学习时长（分钟，默认: 60）

**示例:**
```bash
/learning start "笔记库/离散数学/离散数学.canvas"
/learning start "笔记库/线性代数/线性代数.canvas" --user-id user123
/learning start "笔记库/概率论/概率论.canvas" --session-name "概率论复习"
```

**启动流程** (Story 10.10修复):
1. 系统可用性预检测（Neo4j、MCP服务器、Python依赖）
2. 真实启动三个记忆系统（并行执行，Story 10.13优化）
3. 捕获启动结果（优雅降级，部分失败不影响其他系统）
4. 生成状态报告（诚实反映各系统真实状态）
5. 保存会话JSON（记录真实状态和时间戳）

**性能优化** (Story 10.13):
- 快速启动脚本: `python scripts/quick_start_learning.py <canvas_path>` (目标<5秒)
- 循环依赖修复: 懒加载模式，避免7-8x重复初始化
- 并行启动: 三系统并行初始化，从60-120秒降至20-40秒
- 实例缓存: 使用工厂方法`LearningSessionManager.get_instance()`，缓存命中<2秒

### `/learning status`

显示当前学习会话状态。

**输出示例:**
```
📊 当前学习会话状态
🎯 会话ID: session_20251030_185905
📚 Canvas: 离散数学
⏱️ 开始时间: 2025-10-30 18:59:05
✅ Graphiti: 运行中 (Memory ID: mem_xxx)
✅ Temporal: 运行中 (Session ID: temporal_sess_xxx)
✅ Semantic: 运行中 (Memory ID: semantic_mem_xxx)
```

### `/learning stop`

停止当前学习会话并生成报告（保存会话JSON）。

### `/learning report`

生成综合学习报告（基于真实记录的学习数据）。

## 记忆系统真实启动

### 1. Graphiti知识图谱
通过MCP工具真实调用:
```python
from claude_tools import mcp__graphiti_memory__add_episode
result = await mcp__graphiti_memory__add_episode(
    content=f"开始学习会话: {session_name}, Canvas: {canvas_path}"
)
# 返回: {'memory_id': 'mem_xxx', ...}
```

### 2. 时序记忆管理器
真实初始化并创建会话:
```python
from memory_system.temporal_memory_manager import TemporalMemoryManager
temporal_manager = TemporalMemoryManager()
session = temporal_manager.create_learning_session(
    canvas_id=canvas_path,
    user_id=user_id
)
# 返回: LearningSession对象，包含session_id
```

### 3. 语义记忆管理器
真实初始化并检查MCP可用性:
```python
from memory_system.semantic_memory_manager import SemanticMemoryManager
semantic_manager = SemanticMemoryManager()
if semantic_manager.mcp_client is not None:
    memory_id = semantic_manager.store_semantic_memory(...)
# 返回: memory_id字符串
```

## 会话状态JSON

每次启动会话时，系统创建包含真实状态的JSON文件 (`.learning_sessions/session_*.json`):

```json
{
  "session_id": "session_20251030_185905",
  "session_name": "离散数学学习会话",
  "user_id": "default",
  "start_time": "2025-10-30T18:59:05.123456",
  "canvas_path": "/absolute/path/to/canvas.canvas",
  "memory_systems": {
    "graphiti": {
      "status": "running",
      "memory_id": "mem_abc123",
      "storage": "Neo4j图数据库",
      "initialized_at": "2025-10-30T18:59:06.456789"
    },
    "temporal": {
      "status": "running",
      "session_id": "temporal_session_xyz789",
      "storage": "本地SQLite数据库",
      "initialized_at": "2025-10-30T18:59:07.012345"
    },
    "semantic": {
      "status": "running",
      "memory_id": "semantic_mem_def456",
      "storage": "向量数据库",
      "initialized_at": "2025-10-30T18:59:07.678901"
    }
  }
}
```

**优雅降级**: 如果任何系统失败，会记录错误但不影响其他系统:
```json
{
  "graphiti": {
    "status": "unavailable",
    "error": "Neo4j连接失败 (Connection refused)",
    "attempted_at": "2025-10-30T18:59:06.456789",
    "storage": "Neo4j图数据库",
    "suggestion": "运行 'neo4j start' 启动数据库"
  }
}
```

## 技术架构 (Story 10.13优化)

```
LearningSessionManager (with caching)
├── 快速启动脚本 (scripts/quick_start_learning.py)
├── 懒加载模块 (canvas_utils/__init__.py)
├── 并行初始化 (asyncio.gather)
└── 真实记忆系统
    ├── Graphiti (MCP工具)
    ├── TemporalMemoryManager (SQLite/Neo4j)
    └── SemanticMemoryManager (MCP/向量数据库)
```

**关键优化**:
- **循环依赖修复**: 使用工厂函数 `get_canvas_json_operator()` 等懒加载
- **并行启动**: `asyncio.gather(..., return_exceptions=True)` 同时启动三系统
- **实例缓存**: `await LearningSessionManager.get_instance()` 复用实例

## 使用工作流

### 典型学习会话:

```bash
# 1. 启动会话（快速脚本，<5秒）
python scripts/quick_start_learning.py "笔记库/数学分析/数学分析.canvas"

# 或使用命令（<20秒）
/learning start "笔记库/数学分析/数学分析.canvas"

# 2. 进行Canvas学习活动
# - 使用各种Sub-agent进行学习
# - 填写黄色理解节点
# - 进行评分和反馈

# 3. 查看学习状态
/learning status

# 4. 结束会话
/learning stop
```

## 故障排除

### 常见问题及解决方案

**Graphiti启动失败** (Neo4j连接失败):
```bash
neo4j start  # 启动Neo4j数据库
```

**时序记忆管理器失败**:
- 检查 `memory_system/temporal_memory_manager.py` 是否存在
- 验证Python依赖: `pip list | grep -E "neo4j|loguru"`

**语义记忆管理器不可用** (MCP服务未连接):
- 重启Claude Code CLI重新连接MCP服务器
- 或继续（语义记忆是可选功能）

**详细诊断**: 查看 `.ai/debug-log.md` 了解启动错误详情

## 实现状态

✅ **Story 10.10**: 真实启动逻辑（修复错误#9）
✅ **Story 10.11**: 系统模式检测和优雅降级
✅ **Story 10.13**: 性能优化（<5秒启动）

**核心实现**:
- **源代码**: `command_handlers/learning_commands.py`
- **快速脚本**: `scripts/quick_start_learning.py`
- **懒加载**: `canvas_utils/__init__.py`
- **单元测试**: `tests/test_learning_start_fix.py` (14个测试，100%通过)
- **集成测试**: `tests/test_learning_start_integration.py` (8个测试，100%通过)

## 相关文档

- **错误日志**: [CANVAS_ERROR_LOG.md](../../CANVAS_ERROR_LOG.md#错误-9)
- **Story 10.10**: [docs/stories/10.10.story.md](../docs/stories/10.10.story.md)
- **Story 10.11**: [docs/stories/10.11.story.md](../docs/stories/10.11.story.md)
- **Story 10.13**: [docs/stories/10.13.story.md](../docs/stories/10.13.story.md)
- **会话目录说明**: `.learning_sessions/README_learning_sessions.md`

---

**最后更新**: 2025-11-03
**版本**: 1.3 (Story 10.13性能优化版)
**更新内容**: 精简文档，移除冗长的实现细节和故障排除，保留核心用法
