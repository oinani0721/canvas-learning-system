---
name: health-check
description: Run comprehensive health diagnostics and verify all core functionality
tools: Read, Write, Edit
model: sonnet
---

# Canvas学习系统 - 全面健康检查

## 🎯 功能概述

运行完整的系统健康诊断，验证所有核心功能：
- 🔍 深度系统诊断分析
- ⚡ 性能基准测试和瓶颈识别
- 🔗 组件间依赖关系验证
- 📈 预测性健康分析
- 🛠️ 自动修复建议和执行方案

## 📋 输入参数

```json
{
  "comprehensive": true,      // 是否进行全面检查
  "component": null,          // 指定检查组件（可选）
  "benchmark": false,         // 是否运行性能基准测试
  "predictive": true,         // 是否启用预测性分析
  "auto_fix": false,          // 是否尝试自动修复问题
  "format": "detailed"        // 输出格式: summary | detailed | json
}
```

## 🎨 输出格式

### 全面诊断报告
```
🏥 Canvas学习系统 - 全面健康检查
🕒 检查时间: 2025-01-22 15:30:00
⏱️  检查耗时: 8.5秒

🎯 总体评估:
🟢 系统健康状态: 良好 (88.5/100)
✅ 核心功能: 全部正常
⚠️  性能警告: 1个
❌ 严重问题: 0个

🔍 组件诊断详情:

1. 🟢 Canvas操作组件 (95.0/100)
   ✅ 文件读写: 正常 (45ms)
   ✅ 节点操作: 正常 (12ms)
   ✅ 布局算法: 正常 (85ms)
   💡 建议: 性能优秀，保持当前配置

2. 🟡 Agent系统组件 (78.5/100)
   ✅ Agent配置: 正常 (13个Agent)
   ⚠️  响应时间: 偏慢 (平均4200ms)
   ✅ 成功率: 良好 (95.2%)
   🔧 建议: 优化Agent并发处理，考虑增加缓存

3. 🟢 错误日志系统 (98.0/100)
   ✅ 日志记录: 正常
   ✅ 文件轮转: 正常
   ✅ 存储空间: 充足 (12.5GB)
   💡 建议: 系统运行良好

4. 🟢 复习调度器 (91.2/100)
   ✅ 配置文件: 正常
   ✅ 数据库连接: 正常
   ✅ 任务调度: 正常
   💡 建议: 定期检查复习任务完成情况

5. 🟢 知识图谱系统 (89.8/100)
   ✅ MCP连接: 正常
   ✅ 查询性能: 良好 (120ms)
   ✅ 数据完整性: 正常
   💡 建议: 考虑定期备份图谱数据

6. 🟢 MCP记忆服务 (87.5/100)
   ✅ 服务连接: 正常
   ✅ 向量数据库: 正常
   ✅ 嵌入性能: 良好 (85ms)
   💡 建议: 监控内存使用趋势

📊 性能基准测试结果:
• Canvas文件加载: 优秀 (45ms vs 基准100ms)
• Agent响应时间: 良好 (3200ms vs 基准5000ms)
• 错误记录速度: 优秀 (5ms vs 基准20ms)
• 内存使用效率: 良好 (256MB vs 限制512MB)

🔮 预测性分析:
• 未来7天健康趋势: 稳定 ✅
• 潜在风险: Agent响应时间可能继续增加
• 建议措施: 优化网络连接和Agent配置
• 预计维护窗口: 无需紧急维护

🛠️ 修复建议 (按优先级排序):

1. [MEDIUM] 优化Agent系统性能
   • 问题: 响应时间略高于理想值
   • 影响: 用户体验轻微下降
   • 解决方案: 启用Agent响应缓存
   • 预期改善: 响应时间减少30-40%
   • 实施难度: 低
   • 预估工时: 2小时

2. [LOW] 增加系统监控
   • 问题: 缺少实时性能监控
   • 影响: 无法及时发现性能问题
   • 解决方案: 配置性能告警阈值
   • 预期改善: 提前发现并解决问题
   • 实施难度: 低
   • 预估工时: 1小时

✅ 自动修复结果:
• 无需自动修复的问题
• 系统状态良好，建议定期监控
```

### JSON格式输出
```json
{
  "health_check_report": {
    "check_timestamp": "2025-01-22T15:30:00Z",
    "check_duration_seconds": 8.5,
    "overall_assessment": {
      "status": "healthy",
      "health_score": 88.5,
      "core_functions_status": "all_normal",
      "performance_warnings": 1,
      "critical_issues": 0
    },
    "component_diagnostics": [
      {
        "component": "canvas_operations",
        "status": "healthy",
        "health_score": 95.0,
        "diagnostics": { ... },
        "recommendations": [ ... ]
      }
    ],
    "performance_benchmarks": { ... },
    "predictive_analysis": { ... },
    "repair_recommendations": [ ... ],
    "auto_fix_results": { ... }
  }
}
```

## 🔧 系统实现

使用 `SystemHealthMonitor` 和各组件检查器实现：

1. **深度诊断**: 运行各组件的详细健康检查
2. **性能测试**: 执行标准性能基准测试
3. **依赖验证**: 检查组件间依赖关系
4. **预测分析**: 基于历史数据预测未来趋势
5. **修复建议**: 生成优先级排序的修复方案

## 📝 使用示例

### 标准健康检查
输入: `{"comprehensive": true, "format": "detailed"}`
输出: 完整的系统诊断报告

### 快速状态检查
输入: `{"comprehensive": false, "format": "summary"}`
输出: 简化的状态概览

### 特定组件检查
输入: `{"component": "agent_system", "benchmark": true, "format": "detailed"}`
输出: Agent系统的深度检查和性能测试

### 性能基准测试
输入: `{"benchmark": true, "comprehensive": false, "format": "detailed"}`
输出: 详细的性能基准测试结果

### 预测性分析
输入: `{"predictive": true, "format": "detailed"}`
输出: 基于趋势的预测性分析报告

### 自动修复模式
输入: `{"auto_fix": true, "comprehensive": true, "format": "detailed"}`
输出: 包含自动修复结果的完整报告

## 🎯 诊断维度

### 功能性检查
- ✅ 核心功能可用性
- ✅ API接口响应性
- ✅ 数据完整性验证
- ✅ 配置正确性检查

### 性能检查
- ⚡ 响应时间基准测试
- 📊 吞吐量压力测试
- 💾 内存使用效率分析
- 🔥 CPU使用率监控

### 可靠性检查
- 🔄 错误恢复能力测试
- 💔 故障转移机制验证
- 📈 数据一致性检查
- 🔒 安全性验证

### 可维护性检查
- 📝 日志记录完整性
- 🗂️ 配置管理规范性
- 📚 文档更新及时性
- 🔧 监控覆盖率

## 🔮 预测性分析

### 趋势预测
- 📈 基于历史数据的健康趋势分析
- 🎯 性能瓶颈预测和预警
- 💾 资源使用趋势预测
- 🔄 系统负载增长预测

### 风险评估
- ⚠️ 潜在故障点识别
- 🎯 性能下降风险评估
- 🔒 安全风险分析
- 📊 容量规划建议

## 🛠️ 自动修复能力

### 轻量级修复
- 🔄 重启异常服务
- 🗂️ 清理临时文件
- 📝 重建配置文件
- 💾 优化数据库索引

### 配置优化
- ⚙️ 调整性能参数
- 🔄 优化缓存设置
- 📊 更新告警阈值
- 🔧 修改连接池配置

### 数据维护
- 🗑️ 清理过期日志
- 💾 压缩历史数据
- 🔄 重建统计索引
- 📊 优化查询性能

## ⚠️ 重要提醒

- 全面检查需要更多时间和系统资源
- 性能基准测试可能影响系统性能
- 自动修复功能建议在非高峰期使用
- 建议定期（每周）运行全面健康检查

---

**执行方式**: 在Claude Code中输入 `/health-check` 或 `/health-check --comprehensive`
