---
name: memory-export
description: 导出Canvas学习记忆数据 (Story 8.17)
tools: Read, Write, Bash
model: sonnet
---

# Canvas学习记忆数据导出命令

## 功能描述

导出Story 8.17记录的学习记忆数据，支持多种格式和筛选条件。

## 使用方式

```bash
/memory-export                           # 导出全部数据
/memory-export --format json            # 导出JSON格式
/memory-export --format csv             # 导出CSV格式
/memory-export --format xlsx            # 导出Excel格式
/memory-export --days 30                # 导出最近30天数据
/memory-export --user-id user123        # 导出指定用户数据
/memory-export --type activities        # 仅导出学习活动
/memory-export --type patterns          # 仅导出学习模式
/memory-export --type insights          # 仅导出个人洞察
```

## 导出格式

### 📄 JSON格式 (默认)
- 完整的结构化数据
- 保留所有元数据和时间戳
- 适合程序处理和备份

### 📊 CSV格式
- 表格化数据，易于Excel分析
- 包含主要学习指标
- 适合数据分析和可视化

### 📈 Excel格式
- 多工作表组织数据
- 包含图表和统计
- 适合报告和展示

## 数据类型

### 📚 学习活动数据
- 节点交互记录
- Agent调用历史
- 理解输入过程
- 评分结果
- 时间统计

### 🎯 学习模式分析
- 8维度学习风格
- 行为模式识别
- Agent偏好分析
- 时间分配模式

### 💡 个人洞察
- 个性化建议
- 学习趋势分析
- 知识薄弱环节
- 优化建议

### 🔒 隐私控制数据
- 隐私设置
- 数据权限
- 访问日志

## 使用示例

### 基础数据导出
```bash
/memory-export
```

输出：
```
📤 正在导出学习记忆数据...
✅ 导出完成: C:\Users\ROG\托福\exports\memory_export_20250125_203000.json
📊 导出统计:
  • 学习活动: 1,247条记录
  • 模式分析: 15份报告
  • 个人洞察: 8条建议
  • 文件大小: 2.8MB
```

### CSV格式导出
```bash
/memory-export --format csv --days 30
```

生成CSV文件包含以下工作表：
- **learning_activities.csv** - 学习活动记录
- **session_summary.csv** - 会话汇总
- **agent_usage.csv** - Agent使用统计
- **learning_progress.csv** - 学习进度

### Excel报告导出
```bash
/memory-export --format xlsx --type insights
```

生成的Excel包含：
- 📊 学习概览仪表板
- 📈 学习进度图表
- 🎯 个性化建议报告
- 📚 知识掌握热力图

### 筛选导出
```bash
/memory-export --user-id your_id --type activities --days 7 --format json
```

### 特定时间范围导出
```bash
/memory-export --start 2025-01-01 --end 2025-01-31
```

## 导出文件结构

### JSON格式结构
```json
{
  "export_info": {
    "timestamp": "2025-01-25T20:30:00Z",
    "user_id": "your_user_id",
    "time_range": {
      "start": "2025-01-01T00:00:00Z",
      "end": "2025-01-25T20:30:00Z"
    },
    "total_records": 1247,
    "file_size": "2.8MB"
  },
  "learning_activities": [...],
  "pattern_analysis": {...},
  "personal_insights": [...],
  "privacy_settings": {...}
}
```

### CSV格式列名
- learning_activities.csv:
  - timestamp, activity_type, canvas_path, node_id, details, duration

- session_summary.csv:
  - session_id, start_time, end_time, duration, canvas_count, total_activities

- agent_usage.csv:
  - agent_name, call_count, success_rate, avg_duration, user_satisfaction

## 数据安全

- ✅ 所有导出数据保持加密状态
- ✅ 敏感信息自动脱敏处理
- ✅ 导出文件包含完整性校验
- ✅ 支持密码保护压缩包

## 导出位置

默认导出到：`exports/` 目录
```
exports/
├── memory_export_20250125_203000.json
├── learning_activities_20250125.csv
├── learning_report_20250125.xlsx
└── export_logs/
    └── 20250125_export.log
```

## 高级选项

### 自定义导出配置
```bash
/memory-export --config export_config.yaml
```

配置文件示例：
```yaml
export:
  format: "xlsx"
  include_types: ["activities", "patterns", "insights"]
  date_range:
    start: "2025-01-01"
    end: "2025-01-31"
  privacy:
    anonymize: true
    remove_sensitive_data: true
  compression:
    enabled: true
    password: "your_password"
```

### 批量导出
```bash
/memory-export --batch --users user1,user2,user3 --format csv
```

## 相关命令

- `/memory-stats` - 查看数据统计
- `/memory-analyze` - 分析学习模式
- `/memory-clean` - 清理过期数据
- `/memory-backup` - 创建数据备份

---

**Story 8.17 数据导出 - 您的学习数据，随时掌控**