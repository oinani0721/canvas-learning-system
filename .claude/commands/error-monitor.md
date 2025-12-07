---
name: error-monitor
description: Enable Loguru-based enterprise error monitoring and diagnostics
---

# Enterprise Error Monitoring System

## Metadata
- **Command**: /error-monitor
- **Description**: Enable Loguru-based enterprise error monitoring and diagnostics
- **Bmad Pattern**: Comprehensive logging with intelligent error analysis
- **Keywords**: *monitor, *error, *diagnostic

## Usage

### Monitoring Operations
```bash
/error-monitor             # Show error monitoring dashboard
/error-monitor *enable     # Enable enterprise monitoring
/error-monitor report      # Generate error analysis report
/error-monitor alerts      # Configure error alerts
```

### Diagnostics
```bash
/error-check              # Quick system health check
/error-debug              # Debug current Canvas operation
/error-fix                # Auto-fix common errors
/error-log                # View detailed error logs
```

## Implementation

基于Loguru的企业级错误监控系统，提供完整的错误追踪和性能监控。

**核心技术**: Loguru + Sentry (Trust Score: 8.0/10)

**多级日志系统**:
```python
# 自动配置的多级日志
logger.info("Canvas处理开始")     # 控制台 + 文件
logger.debug("节点详细信息")      # 调试文件
logger.error("处理失败")         # 错误单独记录 + 完整堆栈
logger.critical("系统故障")      # 严重错误立即通知
```

**文件管理**:
- 普通日志: 10MB轮转，保留30天
- 错误日志: 50MB轮转，保留90天
- 调试日志: 5MB轮转，保留7天
- 自动压缩: zip格式，节省空间

**性能追踪**:
- 操作耗时: 自动记录每个Canvas操作时间
- 资源监控: CPU/内存使用情况实时追踪
- 错误诊断: 变量值 + 完整调用栈
- 性能分析: 识别性能瓶颈和优化建议

**智能分析**:
- 错误模式识别: 自动识别常见错误模式
- 趋势分析: 错误发生趋势和频率分析
- 根因分析: 深度分析错误根本原因
- 预警机制: 错误率超阈值自动预警

**Agent改进**:
- 错误学习: Agent从错误中学习改进策略
- 自动修复: 常见错误自动修复机制
- 知识库: 构建错误解决方案知识库
- 反馈循环: 持续优化Agent性能

**可视化仪表板**:
- 实时监控: 系统状态实时显示
- 错误统计: 多维度错误统计分析
- 性能图表: 系统性能趋势图表
- 健康评分: 系统整体健康度评分

为Canvas Learning System v2.0提供企业级运维支持。
