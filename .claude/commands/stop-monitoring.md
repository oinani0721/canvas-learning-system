---
name: stop-monitoring
description: Stop Canvas file monitoring system and save final statistics
---

# 停止Canvas监控系统

---

## 🛑 正在停止监控系统

正在安全停止Canvas文件监控系统...

---

{{#if (canvas_monitoring_status.is_running)}}

## 📊 最终统计报告

**会话开始时间**: `{{canvas_monitoring_status.session_start_time}}`
**本次运行时长**: `{{canvas_monitoring_status.session_duration}}`

### 📈 本次会话统计
- **监控文件变更**: `{{canvas_monitoring_status.session_changes}}` 次
- **处理学习事件**: `{{canvas_monitoring_status.session_events}}` 次
- **学习时长**: `{{canvas_monitoring_status.session_learning_time}}` 分钟
- **知识点处理**: `{{canvas_monitoring_status.session_nodes_processed}}` 个

### 🎯 理解进展
- **红色→黄色**: `{{canvas_monitoring_status.red_to_yellow}}` 个
- **黄色→紫色**: `{{canvas_monitoring_status.yellow_to_purple}}` 个
- **紫色→绿色**: `{{canvas_monitoring_status.purple_to_green}}` 个
- **总理解提升**: `{{canvas_monitoring_status.total_improvements}}` 个

---

## ✅ 停止完成

**监控系统已安全停止**

### 💾 数据已保存
- ✅ 学习记录已保存
- ✅ 性能统计已保存
- ✅ 系统状态已保存
- ✅ 配置文件已更新

### 📂 数据存储位置
```
C:\Users\ROG\托福\canvas_progress_tracker\
├── data\
│   ├── learning_analytics\     # 本次学习分析
│   ├── change_history\          # 变更历史
│   └── session_reports\         # 会话报告
└── logs\
    ├── canvas_monitor.log       # 监控日志
    └── session_YYYYMMDD.log     # 本次会话日志
```

---

## 🎉 学习成就

### 🏆 本次会话亮点
{{#if (gt canvas_monitoring_status.session_nodes_processed 0)}}
- 📚 处理了 `{{canvas_monitoring_status.session_nodes_processed}}` 个知识点
{{/if}}
{{#if (gt canvas_monitoring_status.total_improvements 0)}}
- 🎯 实现了 `{{canvas_monitoring_status.total_improvements}}` 次理解提升
{{/if}}
{{#if (gt canvas_monitoring_status.session_learning_time 0)}}
- ⏰ 投入了 `{{canvas_monitoring_status.session_learning_time}}` 分钟学习时间
{{/if}}

### 📈 长期统计
- **累计学习天数**: `{{canvas_monitoring_status.total_learning_days}}` 天
- **累计掌握知识点**: `{{canvas_monitoring_status.total_mastered_nodes}}` 个
- **累计学习时长**: `{{canvas_monitoring_status.total_learning_hours}}` 小时

---

## 🔄 重新启动

当你想要重新开始学习时，可以使用：

```
/canvas --with-monitoring
```

或者单独启动监控系统：

```bash
python canvas_progress_tracker/monitoring_manager.py start
```

---

## 📊 查看历史数据

### 生成学习报告
```
/learning-report --days 7    # 最近7天
/learning-report --days 30   # 最近30天
```

### 查看历史统计
```bash
python canvas_progress_tracker/monitoring_manager.py status
python canvas_progress_tracker/monitoring_manager.py report --days 30
```

---

## 💡 下次学习建议

基于本次学习表现的建议：

{{#each canvas_monitoring_status.next_session_recommendations}}
- {{this}}
{{/each}}

---

**感谢使用Canvas监控系统！你的每一次学习都被记录和珍惜。** 🌟

*学习数据已安全保存，随时可以查看和分析。期待下次再见！*

{{else}}

## ⚠️ 监控系统未运行

**当前状态**: 监控系统未在运行

**可能原因**:
- 监控系统从未启动
- 监控系统已经停止
- 系统出现异常

---

## 🚀 如何启动监控系统

### 方法1: 集成启动
```
/canvas --with-monitoring
```

### 方法2: 独立启动
```bash
python canvas_progress_tracker/monitoring_manager.py start --daemon
```

---

## 📊 查看可用数据

即使监控系统未运行，你仍然可以：

- **查看历史学习记录**
- **生成过往学习报告**
- **分析已保存的学习数据**

使用以下命令：
```
/learning-report --days 30
```

---

**准备好重新开始智能学习体验了吗？** 🚀

{{/if}}

---

*提示：所有学习数据都安全存储在本地，你可以随时访问和分析。*