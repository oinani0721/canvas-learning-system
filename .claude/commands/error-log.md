---
name: error-log
description: Display recent errors with detailed information and resolution suggestions
tools: Read, Write, Edit
model: sonnet
---

# Canvas学习系统 - 错误日志查看

## 🎯 功能概述

显示系统最近的错误记录，包括：
- 📋 最近10个错误及其详细信息
- 🔍 错误上下文和触发条件
- 💡 自动修复建议和预防措施
- 📊 错误分类统计和趋势分析
- 🎯 错误解决状态跟踪

## 📋 输入参数

```json
{
  "limit": 10,              // 显示错误数量限制
  "severity": null,         // 错误严重性过滤: "critical" | "high" | "medium" | "low"
  "component": null,        // 组件过滤: "canvas_operations" | "agent_system" | "error_logging"
  "resolved": false,        // 是否只显示已解决的错误
  "hours": 24,              // 时间范围（小时）
  "format": "summary"       // 输出格式: summary | detailed | json
}
```

## 🎨 输出格式

### 基础错误概览
```
🔴 最近错误报告 (最近24小时)

📊 错误统计:
• 总错误数: 8个
• 严重错误: 0个
• 高优先级: 2个
• 已解决: 6个 (75%)
• 未解决: 2个

🔍 最新错误:
1. [MEDIUM] Canvas文件读取超时
   • 时间: 2025-01-22 14:20:15
   • 组件: canvas_operations
   • 文件: 笔记库/大型文件.canvas (15.2MB)
   • 状态: ✅ 已解决 (耗时: 5分钟)
   • 解决方案: 增加文件读取超时时间

2. [HIGH] Agent调用超时
   • 时间: 2025-01-22 13:45:30
   • 组件: agent_system
   • Agent: oral-explanation
   • 状态: ⚠️ 未解决
   • 建议: 检查网络连接，尝试重新调用

💡 预防措施:
• 大文件处理前进行大小检查
• 网络不稳定时降低并发度
• 定期清理临时文件释放空间
```

### 详细错误信息
```
🔴 错误详情 #001

基本信息:
• 错误ID: error-uuid16
• 时间: 2025-01-22 14:20:15Z
• 严重性: MEDIUM
• 组件: canvas_operations
• 状态: 已解决

错误描述:
Canvas文件读取操作超时，可能原因：文件过大或磁盘IO繁忙

上下文信息:
• 操作类型: read
• 文件路径: 笔记库/大型文件.canvas
• 文件大小: 15.2MB
• 超时设置: 30秒

解决过程:
• 发现时间: 14:20:15
• 解决时间: 14:25:15
• 解决耗时: 5分钟
• 解决方法: 增加读取超时到60秒

预防措施:
• 实现文件大小预检查
• 大文件分块读取机制
• 添加读取进度显示
```

### JSON格式输出
```json
{
  "error_summary": {
    "total_errors": 8,
    "critical_errors": 0,
    "high_errors": 2,
    "resolved_errors": 6,
    "unresolved_errors": 2,
    "resolution_rate": 75.0
  },
  "recent_errors": [
    {
      "error_id": "error-uuid16",
      "timestamp": "2025-01-22T14:20:15Z",
      "component": "canvas_operations",
      "severity": "medium",
      "message": "Canvas文件读取超时",
      "context": {
        "file_path": "笔记库/大型文件.canvas",
        "operation": "read",
        "file_size_mb": 15.2
      },
      "resolution_status": "resolved",
      "resolution_time_minutes": 5,
      "prevention_measures": [
        "增加文件读取超时时间",
        "添加文件大小预检查",
        "实现大文件处理优化"
      ]
    }
  ]
}
```

## 🔧 系统实现

使用 `CanvasErrorLogger` 和 `SystemHealthMonitor` 类实现：

1. **错误检索**: 从错误日志系统获取指定条件的错误
2. **状态过滤**: 按严重性、组件、解决状态等条件过滤
3. **统计分析**: 计算错误分布和解决率
4. **建议生成**: 基于错误类型提供修复建议
5. **趋势分析**: 分析错误发生趋势和模式

## 📝 使用示例

### 基础错误查看
输入: `{"limit": 10, "format": "summary"}`
输出: 最近10个错误的概览

### 严重错误查看
输入: `{"severity": "critical", "limit": 5, "format": "detailed"}`
输出: 最近5个严重错误的详细信息

### 组件错误查看
输入: `{"component": "agent_system", "hours": 12, "format": "summary"}`
输出: Agent系统最近12小时的错误

### 未解决错误
输入: `{"resolved": false, "format": "detailed"}`
输出: 所有未解决错误的详细信息

### JSON格式输出
输入: `{"format": "json", "limit": 20}`
输出: 结构化JSON数据，便于程序处理

## 🎯 错误分类说明

### 按严重性分类
- 🔴 **CRITICAL**: 系统无法正常运行，需要立即处理
- 🟠 **HIGH**: 功能受限，影响用户体验
- 🟡 **MEDIUM**: 部分功能异常，有workaround
- 🟢 **LOW**: 轻微问题，不影响主要功能

### 按组件分类
- **canvas_operations**: Canvas文件操作相关错误
- **agent_system**: AI Agent调用相关错误
- **error_logging**: 错误日志系统自身错误
- **review_scheduler**: 复习调度系统错误
- **graphiti_knowledge_graph**: 知识图谱系统错误
- **mcp_memory_service**: MCP记忆服务错误

## 💡 智能建议

系统会根据错误类型自动生成建议：

### Canvas操作错误
• 检查文件权限和路径
• 验证文件格式完整性
• 增加操作超时时间
• 实现重试机制

### Agent系统错误
• 检查网络连接状态
• 验证Agent配置正确性
• 降低并发请求数量
• 检查API配额限制

### 系统资源错误
• 释放磁盘空间
• 重启相关服务
• 优化内存使用
• 检查系统负载

## ⚠️ 重要提醒

- 错误日志需要 `canvas_error_logger.py` 正常运行
- 错误信息会自动保存30天
- 严重错误会触发实时告警
- 建议定期检查并处理未解决错误

---

**执行方式**: 在Claude Code中输入 `/error-log` 或 `/error-log --severity high`