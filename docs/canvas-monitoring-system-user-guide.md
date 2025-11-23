# Canvas监控系统用户手册

**版本**: 1.0
**最后更新**: 2025-01-24
**适用于**: Canvas Learning System v2.0

---

## 📋 目录

1. [系统概览](#系统概览)
2. [安装步骤](#安装步骤)
3. [启动和停止](#启动和停止)
4. [配置说明](#配置说明)
5. [使用指南](#使用指南)
6. [常见问题](#常见问题)
7. [故障排除](#故障排除)

---

## 🎯 系统概览

### 什么是Canvas监控系统？

Canvas监控系统是Canvas学习系统的自动化学习进度跟踪组件，它能够：

- **实时监控** Canvas文件变更
- **自动记录** 学习事件（节点添加、颜色流转、理解提升）
- **智能分析** 学习模式和进度
- **生成报告** 每日/每周学习统计和建议

### 核心功能

| 功能 | 说明 | 使用场景 |
|------|------|---------|
| **文件监控** | 自动检测Canvas文件修改 | 无需手动记录学习活动 |
| **热数据存储** | < 20ms写入性能，实时记录 | 即时反馈学习行为 |
| **冷数据归档** | SQLite持久化存储 | 长期数据分析和统计 |
| **学习分析** | 6种事件类型自动识别 | 理解学习模式 |
| **报告生成** | 每日/每周/Canvas分析 | 掌握学习进度 |
| **Agent追踪** | 记录AI Agent使用情况 | 优化学习策略 |

### 系统架构

```
Canvas文件修改
    ↓
文件监控引擎 (Debounce: 600ms)
    ↓
学习事件分析 (6种事件类型)
    ↓
热数据存储 (JSON, <20ms)
    ↓
定时同步调度器 (每小时)
    ↓
冷数据存储 (SQLite)
    ↓
报告生成器 (每日/每周)
```

---

## 📦 安装步骤

### 前置要求

| 组件 | 版本要求 | 说明 |
|------|----------|------|
| **Python** | 3.9+ | 推荐3.11以获得更好性能 |
| **Obsidian** | 1.4.0+ | 用于编辑Canvas文件 |
| **磁盘空间** | 100MB+ | 用于数据存储和日志 |
| **内存** | 512MB可用 | 监控进程约占100MB |

### 安装步骤

#### 1. 检查Python环境

```bash
# Windows
python --version

# 应输出: Python 3.9.x 或更高
```

#### 2. 安装依赖

```bash
cd "C:\Users\ROG\托福"
pip install -r requirements.txt
```

#### 3. 验证安装

```bash
# 验证核心模块可导入
python -c "from canvas_progress_tracker.canvas_monitor_engine import CanvasMonitorEngine; print('✓ 监控引擎安装成功')"
python -c "from canvas_progress_tracker.data_stores import HotDataStore, ColdDataStore; print('✓ 数据存储安装成功')"
python -c "from canvas_progress_tracker.report_generator import LearningReportGenerator; print('✓ 报告生成器安装成功')"
```

#### 4. 初始化配置

```bash
# 复制配置模板（如果存在）
copy config.template.yaml config.yaml

# 或手动创建配置文件（参见"配置说明"章节）
```

---

## ▶️ 启动和停止

### 启动监控系统

#### 方法1: Windows批处理脚本（推荐）

```bash
# 双击运行或命令行执行
start-monitoring.bat
```

#### 方法2: Python直接启动

```bash
python canvas_progress_tracker/start_monitoring.py

# 或指定配置文件
python canvas_progress_tracker/start_monitoring.py --config config.yaml
```

#### 方法3: 后台运行

```bash
# Windows后台运行
start /B python canvas_progress_tracker/start_monitoring.py

# 或使用nohup（如果安装了Git Bash）
nohup python canvas_progress_tracker/start_monitoring.py &
```

### 验证系统运行

```bash
# 检查健康状态（如果健康检查端点已启用）
curl http://localhost:8080/health

# 或查看日志文件
type logs\canvas_monitor_*.log
```

### 停止监控系统

```bash
# 如果在前台运行: 按 Ctrl+C

# 如果在后台运行: 查找进程并终止
tasklist | findstr python
taskkill /PID <进程ID> /F
```

---

## ⚙️ 配置说明

### 配置文件结构

创建或编辑 `config.yaml`:

```yaml
# Canvas监控配置
monitoring:
  # 监控的Canvas目录
  canvas_dir: "C:/Users/ROG/托福/笔记库"

  # 防抖延迟（毫秒）
  debounce_delay_ms: 600

  # 文件监控模式
  watch_recursive: true

  # 重试配置
  retry_attempts: 3
  retry_delays: [100, 500, 2000]  # 毫秒

# 数据存储配置
data_storage:
  # 热数据目录（JSON）
  hot_data_dir: "data/hot"

  # 冷数据数据库路径（SQLite）
  cold_data_db: "data/learning_data.db"

  # 数据同步间隔（秒）
  sync_interval_seconds: 3600  # 每小时同步一次

# 日志配置
logging:
  # 日志级别 (DEBUG, INFO, WARNING, ERROR)
  level: "INFO"

  # 日志文件目录
  log_dir: "logs"

  # 日志轮转设置
  rotation: "10 MB"  # 每10MB轮转
  retention: "30 days"  # 保留30天

# 性能配置
performance:
  # 异步处理工作线程数
  worker_threads: 4

  # 队列最大长度
  max_queue_size: 1000

  # 回调超时（秒）
  callback_timeout: 2

# 健康检查配置（可选）
health_check:
  enabled: false
  port: 8080
  host: "127.0.0.1"
```

### 环境变量配置

创建或编辑 `.env` 文件:

```bash
# Canvas监控系统环境变量配置

# 数据目录
CANVAS_DATA_DIR=C:/Users/ROG/托福/data

# 日志级别
LOG_LEVEL=INFO

# 监控目录
CANVAS_WATCH_DIR=C:/Users/ROG/托福/笔记库
```

---

## 📖 使用指南

### 基本工作流程

#### 1. 启动监控

```bash
start-monitoring.bat
```

预期输出:
```
[INFO] Canvas Monitor Engine starting...
[INFO] Watching directory: C:/Users/ROG/托福/笔记库
[INFO] Debounce delay: 600ms
[INFO] Monitoring started successfully
```

#### 2. 正常使用Obsidian

在Obsidian中正常编辑Canvas文件，监控系统会自动：

- ✅ 检测文件修改（防抖600ms后处理）
- ✅ 识别学习事件类型
- ✅ 写入热数据（JSON）
- ✅ 定时同步到SQLite

#### 3. 查看学习报告

```bash
# 生成今日报告
python -c "
from canvas_progress_tracker.report_generator import LearningReportGenerator
from canvas_progress_tracker.data_stores import ColdDataStore
from datetime import datetime

gen = LearningReportGenerator(ColdDataStore('data/learning_data.db'))
report = gen.generate_daily_report('离散数学', datetime.now().date())
print(report)
"
```

### 高级功能

#### Agent使用统计

监控系统自动记录AI Agent调用情况（来自Story 11.3）:

```python
# 查询Agent使用统计
from canvas_progress_tracker.data_stores import ColdDataStore
import sqlite3

db = ColdDataStore('data/learning_data.db')
conn = sqlite3.connect('data/learning_data.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT agent_type, COUNT(*) as count
    FROM agent_call_records
    WHERE canvas_id = '离散数学'
    GROUP BY agent_type
    ORDER BY count DESC
    LIMIT 5
""")

print("Top 5 Agents:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} 次调用")

conn.close()
```

#### 学习趋势分析

```python
# 查看7天学习趋势
from datetime import datetime, timedelta

for i in range(7):
    date = (datetime.now() - timedelta(days=i)).date()
    report = gen.generate_daily_report('离散数学', date)
    print(f"{date}: {report['summary']['total_events']} 事件")
```

---

## ❓ 常见问题

### Q1: 监控系统占用多少资源？

**A**: 根据Story 11.8性能测试：
- **CPU**: 平均 < 5%，峰值 < 15%
- **内存**: 约100MB
- **磁盘IO**: JSON写入 < 1MB/小时，SQLite < 10MB/天

### Q2: 防抖延迟600ms是什么意思？

**A**: 当Canvas文件被修改后，系统会等待600ms再处理，这样可以：
- 避免重复处理（如Obsidian自动保存）
- 减少性能开销
- 合并连续的小修改

### Q3: 热数据和冷数据有什么区别？

**A**:
- **热数据**: JSON文件，写入速度 < 20ms，用于实时记录
- **冷数据**: SQLite数据库，每小时同步一次，用于长期存储和查询

### Q4: 可以监控多个Canvas吗？

**A**: 可以！监控系统会自动监控配置目录下的所有.canvas文件。

### Q5: 如何备份学习数据？

**A**:
```bash
# 备份SQLite数据库
copy data\learning_data.db data\learning_data_backup.db

# 备份热数据
xcopy data\hot data\hot_backup /E /I
```

### Q6: 监控系统崩溃后数据会丢失吗？

**A**: 不会！热数据采用原子写入（临时文件→重命名），冷数据采用事务保证，确保数据完整性。

---

## 🔧 故障排除

详见 [故障排除指南](canvas-monitoring-troubleshooting.md)

### 快速诊断

#### 症状: 监控系统无法启动

```bash
# 检查Python版本
python --version

# 检查依赖
pip list | findstr watch

# 查看错误日志
type logs\canvas_monitor_*.log | findstr ERROR
```

#### 症状: 文件修改未被检测

```bash
# 检查监控目录配置
echo %CANVAS_WATCH_DIR%

# 验证文件在监控范围内
dir "C:\Users\ROG\托福\笔记库\*.canvas"

# 检查防抖延迟（等待600ms后查看日志）
```

#### 症状: 数据库查询很慢

```bash
# 检查数据库大小
dir data\learning_data.db

# 重建索引
sqlite3 data\learning_data.db "REINDEX;"

# 清理过期数据（如需要）
sqlite3 data\learning_data.db "DELETE FROM learning_events WHERE timestamp < datetime('now', '-90 days');"
```

---

## 📞 获取帮助

### 日志文件位置

```
logs/
├── canvas_monitor_2025-01-24.log    # 主日志
├── canvas_monitor_error.log         # 错误日志
└── canvas_monitor_debug.log         # 调试日志（DEBUG模式）
```

### 联系支持

- **项目文档**: `docs/`
- **架构说明**: `docs/architecture/`
- **故障排除**: `docs/canvas-monitoring-troubleshooting.md`
- **API参考**: `docs/canvas-monitoring-api-reference.md`

---

**文档版本**: 1.0
**最后更新**: 2025-01-24
**维护者**: Canvas Learning System Team
**反馈**: 发现问题请查看 `docs/canvas-monitoring-troubleshooting.md`
