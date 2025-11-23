# Canvas监控系统故障排除指南

**版本**: 1.0
**最后更新**: 2025-01-24
**适用于**: Canvas Learning System v2.0

---

## 📋 目录

1. [常见错误](#常见错误)
2. [日志分析](#日志分析)
3. [性能调优](#性能调优)
4. [数据修复](#数据修复)
5. [诊断工具](#诊断工具)

---

## ⚠️ 常见错误

### 错误1: FileNotFoundError - Canvas文件不存在

**症状**:
```
ERROR: FileNotFoundError: Canvas文件不存在: C:\Users\ROG\托福\笔记库\test.canvas
```

**原因**:
- Canvas文件被删除或移动
- 文件路径配置错误
- 权限问题导致无法访问

**解决方案**:

```bash
# 步骤1: 验证文件是否存在
dir "C:\Users\ROG\托福\笔记库\test.canvas"

# 步骤2: 检查监控配置
type config.yaml | findstr canvas_dir

# 步骤3: 验证文件权限
icacls "C:\Users\ROG\托福\笔记库\test.canvas"

# 步骤4: 如果路径错误，更新配置
# 编辑 config.yaml，修正 canvas_dir 路径
```

---

### 错误2: JSONDecodeError - Canvas文件JSON格式错误

**症状**:
```
ERROR: JSONDecodeError: Canvas文件JSON格式错误: Expecting ',' delimiter: line 10 column 5
```

**原因**:
- Canvas文件被损坏
- 手动编辑导致JSON格式错误
- Obsidian未正常保存文件

**解决方案**:

```bash
# 步骤1: 验证JSON格式
python -c "import json; json.load(open('path/to/canvas.canvas'))"

# 步骤2: 使用在线JSON验证器
# 将文件内容复制到 https://jsonlint.com/ 验证

# 步骤3: 如果有备份，恢复备份
copy "path\to\canvas.canvas.backup" "path\to\canvas.canvas"

# 步骤4: 如果无备份，手动修复JSON
# 使用VSCode或其他编辑器打开文件，修复语法错误
```

**JSON常见错误**:
- ❌ 缺少逗号: `{"a": 1 "b": 2}`
  ✅ 正确: `{"a": 1, "b": 2}`

- ❌ 多余逗号: `{"a": 1, "b": 2,}`
  ✅ 正确: `{"a": 1, "b": 2}`

- ❌ 单引号: `{'a': 1}`
  ✅ 正确: `{"a": 1}`

---

### 错误3: PermissionError - 数据库文件权限错误

**症状**:
```
ERROR: PermissionError: [Errno 13] Permission denied: 'data/learning_data.db'
```

**原因**:
- 数据库文件被其他进程锁定
- 文件权限不足
- 多个监控实例同时运行

**解决方案**:

```bash
# 步骤1: 检查是否有多个监控进程
tasklist | findstr python

# 步骤2: 如有多个，终止旧进程
taskkill /PID <进程ID> /F

# 步骤3: 检查文件权限
icacls data\learning_data.db

# 步骤4: 修复权限（如需要）
icacls data\learning_data.db /grant %USERNAME%:F

# 步骤5: 重启监控系统
start-monitoring.bat
```

---

### 错误4: OperationalError - SQLite数据库锁定

**症状**:
```
ERROR: sqlite3.OperationalError: database is locked
```

**原因**:
- 另一个进程正在访问数据库
- 长时间事务未提交
- 数据库文件损坏

**解决方案**:

```bash
# 步骤1: 等待5秒后重试（系统会自动重试3次）

# 步骤2: 如果持续失败，检查锁定进程
# 使用Process Explorer或类似工具查找占用数据库的进程

# 步骤3: 强制解锁（谨慎！）
sqlite3 data\learning_data.db "PRAGMA locking_mode=NORMAL; VACUUM;"

# 步骤4: 如果数据库损坏，尝试恢复
sqlite3 data\learning_data.db ".dump" > dump.sql
sqlite3 data\learning_data_new.db < dump.sql
move /Y data\learning_data_new.db data\learning_data.db
```

---

### 错误5: TimeoutError - 回调执行超时

**症状**:
```
WARNING: Callback execution timeout after 2.0s
```

**原因**:
- 回调函数执行时间过长
- 网络请求或I/O阻塞
- 系统资源不足

**解决方案**:

```bash
# 步骤1: 检查回调超时配置
type config.yaml | findstr callback_timeout

# 步骤2: 增加超时时间（如需要）
# 编辑 config.yaml:
# performance:
#   callback_timeout: 5  # 增加到5秒

# 步骤3: 优化回调函数（移除耗时操作）

# 步骤4: 监控系统资源
# 打开任务管理器，查看CPU和内存使用率
```

---

## 📊 日志分析

### 日志级别说明

| 级别 | 含义 | 使用场景 |
|------|------|---------|
| **DEBUG** | 详细调试信息 | 开发和深度诊断 |
| **INFO** | 正常操作信息 | 日常监控 |
| **WARNING** | 警告信息 | 需要关注但不致命 |
| **ERROR** | 错误信息 | 需要立即处理 |

### 查看日志

```bash
# 查看最近的INFO日志
type logs\canvas_monitor_*.log | findstr INFO | more

# 查看所有ERROR
type logs\canvas_monitor_*.log | findstr ERROR

# 查看特定Canvas的事件
type logs\canvas_monitor_*.log | findstr "离散数学"

# 实时监控日志（PowerShell）
Get-Content logs\canvas_monitor_*.log -Wait -Tail 20
```

### 日志模式识别

#### 正常运行模式
```
[INFO] Canvas Monitor Engine starting...
[INFO] Watching directory: C:/Users/ROG/托福/笔记库
[INFO] Debounce delay: 600ms
[INFO] Monitoring started successfully
[INFO] Canvas change detected: 离散数学.canvas
[INFO] Event written to hot store: color_change
[INFO] Data synced to cold store: 15 events
```

#### 性能问题模式
```
[WARNING] Queue length: 950/1000
[WARNING] Processing delay: 1523ms
[WARNING] Hot data write slow: 85ms
```
**分析**: 队列接近满载，处理延迟高，需要优化性能

#### 数据一致性问题
```
[ERROR] Hot data read failed: FileNotFoundError
[WARNING] Retry attempt 2/3
[INFO] Retry successful
```
**分析**: 存在临时性I/O问题，但重试机制生效

#### 监控失效模式
```
[ERROR] Observer stopped unexpectedly
[ERROR] Failed to restart monitoring: ...
[ERROR] Critical failure: shutting down
```
**分析**: 监控系统崩溃，需要手动重启

---

## 🚀 性能调优

### 性能指标

#### 当前性能目标 (Story 11.8)
- **P50** < 800ms (中位数响应时间)
- **P95** < 1200ms (95%请求在1.2秒内)
- **CPU** < 5% (平均)
- **内存** < 100MB

#### 监控性能指标

```python
# 性能监控脚本
import psutil
import time

process = psutil.Process()

while True:
    cpu = process.cpu_percent(interval=1)
    mem = process.memory_info().rss / 1024 / 1024  # MB
    print(f"CPU: {cpu:.1f}%, Memory: {mem:.1f}MB")
    time.sleep(5)
```

### 性能调优策略

#### 1. 调整防抖延迟

**问题**: 变更检测过于频繁
**解决**: 增加防抖延迟

```yaml
# config.yaml
monitoring:
  debounce_delay_ms: 1000  # 从600增加到1000
```

**效果**: 减少30%的处理事件数

#### 2. 优化工作线程数

**问题**: 异步处理瓶颈
**解决**: 根据CPU核心数调整

```yaml
# config.yaml
performance:
  worker_threads: 8  # 从4增加到8（如果CPU允许）
```

**效果**: 提升并发处理能力

#### 3. 启用批量写入

**问题**: 频繁的SQLite写入
**解决**: 启用批量插入

```python
# 修改同步配置
data_storage:
  sync_batch_size: 100  # 每次同步100条记录
  sync_interval_seconds: 1800  # 30分钟同步一次
```

**效果**: 减少80%的数据库I/O

#### 4. 数据库索引优化

**问题**: 查询性能慢
**解决**: 添加组合索引

```sql
-- 连接数据库
sqlite3 data/learning_data.db

-- 创建组合索引
CREATE INDEX IF NOT EXISTS idx_canvas_time_type
ON learning_events(canvas_id, timestamp, event_type);

-- 创建颜色流转索引
CREATE INDEX IF NOT EXISTS idx_transitions_canvas_time
ON color_transitions(canvas_id, timestamp);

-- 重建索引
REINDEX;

-- 退出
.quit
```

**效果**: 查询速度提升5-10倍

#### 5. 清理过期数据

**问题**: 数据库过大
**解决**: 定期清理旧数据

```bash
# 清理90天前的数据
sqlite3 data\learning_data.db "
DELETE FROM learning_events
WHERE timestamp < datetime('now', '-90 days');

VACUUM;
"
```

**效果**: 减少数据库大小，提升查询速度

### 性能基准测试

```bash
# 运行性能测试
python -m pytest tests/test_monitoring_performance_benchmarks.py -v

# 查看报告
type test_results/performance_report.txt
```

---

## 🔧 数据修复

### 场景1: 热数据丢失

**症状**: `data/hot/canvas_xxx.json` 文件不存在

**恢复步骤**:
```bash
# 步骤1: 检查备份
dir data\hot_backup

# 步骤2: 从SQLite恢复最近数据
python -c "
from canvas_progress_tracker.data_stores import ColdDataStore, HotDataStore
from datetime import datetime, timedelta

cold = ColdDataStore('data/learning_data.db')
hot = HotDataStore('data/hot')

# 恢复最近1小时的数据
recent = datetime.now() - timedelta(hours=1)
# (简化示例，实际需要实现恢复逻辑)
"

# 步骤3: 重新初始化热数据文件
# 监控系统会自动重新创建
```

### 场景2: SQLite数据库损坏

**症状**: `Error: database disk image is malformed`

**恢复步骤**:
```bash
# 步骤1: 立即备份损坏的数据库
copy data\learning_data.db data\learning_data_corrupted.db

# 步骤2: 尝试导出数据
sqlite3 data\learning_data_corrupted.db ".dump" > repair.sql

# 步骤3: 创建新数据库并导入
sqlite3 data\learning_data_new.db < repair.sql

# 步骤4: 如果成功，替换旧数据库
move /Y data\learning_data_new.db data\learning_data.db

# 步骤5: 重启监控系统
start-monitoring.bat
```

### 场景3: 数据不一致

**症状**: 热数据和冷数据记录数不匹配

**检查脚本**:
```python
import json
import sqlite3

# 读取热数据
with open('data/hot/canvas_test.json') as f:
    hot_data = json.load(f)
hot_count = len(hot_data)

# 查询冷数据
conn = sqlite3.connect('data/learning_data.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM learning_events WHERE canvas_id='test'")
cold_count = cursor.fetchone()[0]
conn.close()

print(f"热数据: {hot_count} 条")
print(f"冷数据: {cold_count} 条")
print(f"差异: {hot_count - cold_count} 条")
```

**修复方案**:
```bash
# 强制同步
python -c "
from canvas_progress_tracker.system_integration import DataSyncScheduler

scheduler = DataSyncScheduler()
scheduler.force_sync_now()  # 立即同步所有热数据
"
```

---

## 🛠️ 诊断工具

### 工具1: 系统健康检查

```bash
# 创建健康检查脚本: health_check.bat
@echo off
echo ===== Canvas监控系统健康检查 =====
echo.

echo [1/5] 检查监控进程...
tasklist | findstr python
echo.

echo [2/5] 检查数据目录...
dir data\hot
dir data\learning_data.db
echo.

echo [3/5] 检查日志文件...
dir logs\canvas_monitor_*.log
echo.

echo [4/5] 检查最近错误...
type logs\canvas_monitor_*.log | findstr ERROR | more
echo.

echo [5/5] 检查数据库状态...
sqlite3 data\learning_data.db "PRAGMA integrity_check;"
echo.

echo ===== 健康检查完成 =====
pause
```

### 工具2: 性能分析器

```python
# performance_analyzer.py
import time
import psutil
from canvas_progress_tracker.canvas_monitor_engine import CanvasMonitorEngine

process = psutil.Process()

# 性能采样
samples = []
for i in range(60):  # 采样60秒
    cpu = process.cpu_percent(interval=1)
    mem = process.memory_info().rss / 1024 / 1024
    samples.append({"cpu": cpu, "mem": mem})

# 统计
avg_cpu = sum(s["cpu"] for s in samples) / len(samples)
max_mem = max(s["mem"] for s in samples)

print(f"平均CPU: {avg_cpu:.2f}%")
print(f"最大内存: {max_mem:.1f}MB")

if avg_cpu > 10:
    print("⚠️  CPU使用率偏高")
if max_mem > 150:
    print("⚠️  内存使用偏高")
```

### 工具3: 数据一致性验证器

```python
# data_validator.py
import json
import sqlite3
from datetime import datetime, timedelta

def validate_data_consistency(canvas_id):
    """验证热数据和冷数据一致性"""

    # 读取热数据
    try:
        with open(f'data/hot/canvas_{canvas_id}.json') as f:
            hot_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ 热数据文件不存在: {canvas_id}")
        return False

    # 查询冷数据
    conn = sqlite3.connect('data/learning_data.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM learning_events WHERE canvas_id=?",
        (canvas_id,)
    )
    cold_count = cursor.fetchone()[0]
    conn.close()

    # 对比
    hot_count = len(hot_data)
    diff = hot_count - cold_count

    if diff == 0:
        print(f"✓ 数据一致: {hot_count} 条")
        return True
    elif diff > 0:
        print(f"⚠️  热数据多 {diff} 条，等待同步")
        return True
    else:
        print(f"❌ 冷数据多 {-diff} 条，数据异常")
        return False

# 使用
validate_data_consistency("离散数学")
```

---

## 🆘 紧急恢复流程

### 完全系统重置

⚠️ **警告**: 此操作将清空所有监控数据！

```bash
# 步骤1: 停止监控系统
taskkill /F /IM python.exe

# 步骤2: 备份数据（重要！）
xcopy data data_backup_%date:~0,10% /E /I

# 步骤3: 清空数据目录
del /Q data\hot\*
del /Q data\learning_data.db

# 步骤4: 重新初始化
python canvas_progress_tracker\start_monitoring.py --init

# 步骤5: 验证系统
python -c "from canvas_progress_tracker.canvas_monitor_engine import CanvasMonitorEngine; print('✓ 系统重置成功')"
```

---

## 📞 获取支持

### 诊断信息收集

提交问题时，请提供：

1. **系统信息**:
   ```bash
   python --version
   type config.yaml
   ```

2. **错误日志**:
   ```bash
   type logs\canvas_monitor_*.log | findstr ERROR > error_report.txt
   ```

3. **性能数据**:
   ```bash
   python performance_analyzer.py > performance_report.txt
   ```

### 相关文档

- **用户手册**: `docs/canvas-monitoring-system-user-guide.md`
- **API参考**: `docs/canvas-monitoring-api-reference.md`
- **开发者指南**: `docs/canvas-monitoring-developer-guide.md`

---

**文档版本**: 1.0
**最后更新**: 2025-01-24
**维护者**: Canvas Learning System Team
