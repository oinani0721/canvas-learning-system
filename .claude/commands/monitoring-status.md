---
name: monitoring-status
description: Display Canvas monitoring system status and learning statistics (Story 11.9)
---

# Canvas监控系统状态查询

执行以下步骤查询并展示Canvas监控系统的实时状态：

## 步骤1: 查询健康状态

首先，尝试调用健康检查端点：

```bash
python -c "import requests; r = requests.get('http://localhost:5678/health', timeout=2); print(r.json())" 2>/dev/null || echo "HTTP服务器未启动"
```

## 步骤2: 查询详细状态

如果健康检查通过，查询详细状态：

```bash
python -c "import requests; r = requests.get('http://localhost:5678/status', timeout=2); print(r.json())"
```

## 步骤3: 查询统计数据

查询今日统计数据：

```bash
python -c "import requests; r = requests.get('http://localhost:5678/stats?period=today', timeout=2); print(r.json())"
```

## 步骤4: 格式化输出

根据上述API返回的JSON数据，格式化输出为Markdown表格。

**输出格式示例**：

```markdown
## Canvas监控系统状态

### 🟢 系统健康状态

| 指标 | 数值 |
|------|------|
| **状态** | 🟢 运行中 |
| **运行时间** | 2小时35分钟 |
| **版本** | 1.0.0 |

---

### 📊 监控状态

| 指标 | 数值 |
|------|------|
| **监控文件数** | 12个Canvas文件 |
| **队列长度** | 3个待处理任务 |
| **数据库状态** | ✅ 已连接 |
| **最后处理时间** | 2025-11-02 14:30:25 |

---

### 📈 性能统计（今日）

| 指标 | 数值 |
|------|------|
| **总变更数** | 156次 |
| **平均解析时间** | 124ms |
| **回调执行次数** | 468次 |
| **错误次数** | 2次 |

---

## 🛠️ 快捷操作

手动触发数据同步：
```bash
python -c "import requests; r = requests.post('http://localhost:5678/sync', timeout=5); print(r.json())"
```

优雅停止监控：
```bash
python -c "import requests; r = requests.post('http://localhost:5678/stop', timeout=2); print(r.json())"
```

---

## 📚 相关命令

- `/start-monitoring` - 启动监控系统
- `/stop-monitoring` - 停止监控系统
- `/learning-report` - 查看学习报告
```

---

## 错误处理

如果HTTP服务器未启动（步骤1失败），显示以下消息：

```markdown
## 🔴 监控仪表板未启动

Canvas监控系统可能正在运行，但HTTP仪表板服务未启动。

**建议操作**：

1. 检查监控系统是否运行：
   ```bash
   ps aux | grep canvas_monitor
   ```

2. 如果监控系统未运行，启动它：
   ```bash
   /start-monitoring
   ```

3. 如果监控系统运行但仪表板未启动，检查配置：
   - 确保 `canvas_progress_tracker/config/config.yaml` 中 `dashboard_enabled: true`
   - 确保端口5678未被占用

4. 重启监控系统：
   ```bash
   /stop-monitoring && /start-monitoring
   ```

---

**故障排查提示**：
- HTTP仪表板默认绑定到 `http://127.0.0.1:5678`
- 只允许localhost访问（安全限制）
- 启动时间通常< 1秒

如果问题持续，请检查日志文件获取详细错误信息。
```

---

**实现说明**：

1. 此命令通过Python requests库调用HTTP API获取实时数据
2. 所有数据来自 `MonitoringDashboardServer` 提供的REST API
3. 响应时间优化：health < 50ms, status < 100ms, stats < 200ms
4. 如果HTTP服务器未启动，提供友好的错误提示和解决方案
5. 支持快捷操作（手动同步、停止监控）

---

*Story 11.9: 监控仪表板与运维工具 - HTTP API集成版本*