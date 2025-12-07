---
name: learning-session
description: 统一学习会话管理系统 - 包装现有记忆命令
tools: Bash, Read, Write, Edit
model: sonnet
---

# Canvas学习会话统一管理系统

## 概述

实现统一的学习会话启动命令，包装现有的 `/graph start`、`/memory-start` 和 `/unified-memory-*` 命令，提供一键启动所有记忆系统的便捷体验。

## 核心功能

### 🚀 **一键启动所有记忆系统**
- 同时启动Graphiti知识图谱录制
- 同时启动实时学习行为记录
- 同时启动统一记忆接口
- 智能协调各记忆系统工作

### 📊 **跨Canvas连续学习支持**
- 支持多个Canvas的连续学习会话
- 自动跨Canvas的知识关联分析
- 学习进度的连续追踪

### 🎯 **智能学习体验增强**
- 提供综合的学习报告
- 智能推荐学习策略
- 学习薄弱环节识别

## 主要命令

### `/learning start <canvas_path> [options]`

启动统一学习会话，包装所有记忆系统。

**参数:**
- `canvas_path`: Canvas文件路径（必需）
- `--user-id`: 用户ID（默认: default）
- `--session-name`: 会话名称（默认: 自动生成）
- `--duration`: 预计学习时长（分钟，默认: 60）
- `--enable-graphiti`: 启用Graphiti（默认: true）
- `--enable-memory`: 启用行为记忆（默认: true）
- `--enable-semantic`: 启用语义记忆（默认: true）

**示例:**
```bash
/learning start "笔记库/离散数学/离散数学.canvas"
/learning start "笔记库/线性代数/线性代数.canvas" --user-id user123 --duration 120
/learning start "笔记库/概率论/概率论.canvas" --session-name "概率论复习"
```

### `/learning status`

显示当前学习会话状态。

**输出示例:**
```
📊 当前学习会话状态
🎯 会话ID: session_20251025_193000
📚 Canvas: 离散数学
⏱️ 开始时间: 2025-10-25 19:30:00
⏰ 已用时: 15分钟
✅ Graphiti: 运行中 (15个概念记录)
✅ Memory: 运行中 (32个行为记录)
✅ Semantic: 运行中 (语义分析中)
```

### `/learning stop [options]`

停止当前学习会话并生成报告。

**参数:**
- `--save-report`: 保存学习报告（默认: true）
- `--report-path`: 报告保存路径（可选）
- `--continue-session`: 继续下一个Canvas（默认: false）

**示例:**
```bash
/learning stop
/learning stop --save-report --report-path "学习报告/离散数学_20251025.md"
```

### `/learning report [options]`

生成综合学习报告。

**参数:**
- `--format`: 报告格式（markdown/json，默认: markdown）
- `--include-graph`: 包含知识图谱可视化（默认: true）
- `--include-behavior`: 包含行为分析（默认: true）

### `/learning switch <canvas_path>`

切换到新的Canvas（保持当前会话继续）。

**示例:**
```bash
/learning switch "笔记库/线性代数/线性代数.canvas"
```

### `/learning add-canvas <canvas_path>`

向当前会话添加新的Canvas（支持并行学习）。

**示例:**
```bash
/learning add-canvas "笔记库/概率论/概率论.canvas"
```

## 使用工作流

### 典型的学习会话流程:

1. **开始学习会话**
   ```bash
   /learning start "笔记库/数学分析/数学分析.canvas"
   ```

2. **进行Canvas学习活动**
   - 使用各种Sub-agent进行学习
   - 填写黄色理解节点
   - 进行评分和反馈

3. **切换到其他Canvas（如需要）**
   ```bash
   /learning switch "笔记库/线性代数/线性代数.canvas"
   ```

4. **查看学习状态**
   ```bash
   /learning status
   ```

5. **获取学习报告**
   ```bash
   /learning report
   ```

6. **结束学习会话**
   ```bash
   /learning stop
   ```

## 技术实现

### 核心组件

- **LearningSessionWrapper**: 会话包装器主类
- **CommandCoordinator**: 命令协调器
- **SessionManager**: 会话状态管理
- **ReportGenerator**: 报告生成器

### 包装的现有命令

| 现有命令 | 包装方式 | 功能 |
|---------|---------|------|
| `/graph start <path>` | 直接调用 + 参数包装 | Graphiti知识图谱启动 |
| `/memory-start` | 直接调用 + 会话关联 | 实时行为记录启动 |
| `/unified-memory-store` | 智能调用 + 内容分析 | 统一记忆存储 |

### 会话数据结构

```python
@dataclass
class LearningSession:
    session_id: str
    user_id: str
    canvas_path: str
    start_time: datetime
    end_time: Optional[datetime] = None
    active_canvases: List[str] = field(default_factory=list)
    memory_systems: Dict[str, bool] = field(default_factory=dict)
    session_metadata: Dict[str, Any] = field(default_factory=dict)
```

## 配置

### 配置文件位置: `config/learning_session_config.yaml`

```yaml
learning_session:
  default_duration_minutes: 60
  auto_save_interval_minutes: 5
  max_concurrent_canvases: 3
  session_timeout_hours: 8

memory_systems:
  graphiti:
    enabled: true
    command_path: "/graph"
    auto_extract_concepts: true
    relationship_depth: 2

  behavioral:
    enabled: true
    command_path: "/memory-start"
    capture_frequency_ms: 100
    auto_analyze_patterns: true

  semantic:
    enabled: true
    command_prefix: "/unified-memory"
    auto_tag_content: true
    similarity_threshold: 0.7

reports:
  auto_save: true
  output_directory: "学习报告"
  include_visualizations: true
  template: "comprehensive"

coordination:
  startup_timeout_seconds: 30
  health_check_interval_seconds: 60
  auto_recovery: true
```

## 故障排除

### 常见问题

1. **会话启动失败**
   - 检查Canvas文件是否存在
   - 确保相关记忆命令可用
   - 检查配置文件是否正确

2. **记忆系统启动失败**
   - 单独测试各个记忆命令
   - 检查系统权限
   - 查看详细错误日志

3. **跨Canvas切换失败**
   - 确保前一个Canvas已正确保存
   - 检查Canvas文件路径格式
   - 验证会话状态是否正常

### 调试模式

启用详细日志:
```bash
export LEARNING_SESSION_DEBUG=true
/learning start "测试.canvas"
```

## 扩展性

### 添加新功能

1. 在 `LearningSessionWrapper` 中添加新方法
2. 更新配置文件模板
3. 添加相应的命令行选项
4. 更新使用文档

### 集成新的记忆系统

在配置文件中添加新的记忆系统配置:
```yaml
memory_systems:
  new_system:
    enabled: true
    command_prefix: "/new-memory"
    integration_type: "wrapper"
```

## 性能优化

- **异步启动**: 并行启动多个记忆系统
- **智能缓存**: 缓存会话状态和配置
- **懒加载**: 按需加载记忆系统组件
- **健康检查**: 定期检查记忆系统状态

## 版本信息

- **版本**: 1.0
- **最后更新**: 2025-10-25
- **兼容性**: Canvas Learning System v2.0+
- **依赖**: 现有记忆命令系统

## 安全和隐私

- 用户数据本地存储
- 会话数据加密保存
- 支持数据导出和删除
- 符合隐私保护要求
