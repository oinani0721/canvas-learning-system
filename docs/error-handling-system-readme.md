# 错误处理和故障恢复系统

## 概述

Canvas学习系统的错误处理和故障恢复系统，提供了完整的错误处理机制，确保系统在遇到错误时能够稳定运行。

## 系统组件

### 1. 错误隔离管理器 (ErrorIsolationManager)
- **文件**: `error_isolation_manager.py`
- **功能**:
  - 实例级错误隔离
  - 错误传播控制
  - 故障实例自动检测和隔离
  - 错误模式分析

### 2. 重试管理器 (RetryManager)
- **文件**: `retry_manager.py`
- **功能**:
  - 多种重试策略（指数退避、线性退避、随机抖动等）
  - 可配置重试策略
  - 重试状态跟踪
  - 智能重试决策

### 3. 优雅降级管理器 (GracefulDegradationManager)
- **文件**: `graceful_degradation_manager.py`
- **功能**:
  - 部分失败处理
  - 部分结果收集
  - 恢复建议生成
  - 用户通知

### 4. 错误日志和诊断系统 (ErrorLogger & DiagnosticCollector)
- **文件**: `error_logger.py`
- **功能**:
  - 结构化错误日志记录
  - 日志轮转和压缩
  - 错误分类和标签
  - 诊断报告生成

### 5. 熔断器管理器 (CircuitBreakerManager)
- **文件**: `circuit_breaker_manager.py`
- **功能**:
  - Circuit Breaker模式实现
  - 自动熔断和恢复
  - 故障阈值检测
  - 状态监控

## 快速开始

### 基本使用

```python
from error_isolation_manager import ErrorIsolationManager
from retry_manager import RetryManager
from graceful_degradation_manager import GracefulDegradationManager
from error_logger import ErrorLogger
from circuit_breaker_manager import CircuitBreakerManager

# 初始化组件
isolation_manager = ErrorIsolationManager()
retry_manager = RetryManager()
degradation_manager = GracefulDegradationManager()
error_logger = ErrorLogger()
circuit_manager = CircuitBreakerManager()

# 启动监控
await isolation_manager.start_monitoring()
await retry_manager.start_cleanup_task()
await circuit_manager.start_monitoring()
```

### 使用重试机制

```python
async def risky_operation():
    # 可能失败的操作
    pass

# 带重试执行
result = await retry_manager.execute_with_retry(
    "task-id",
    risky_operation,
    policy_id="default"
)
```

### 使用熔断器

```python
# 创建熔断器
await circuit_manager.create_circuit_breaker(
    "my-service",
    {
        'failure_threshold': 5,
        'recovery_timeout': 60.0
    }
)

# 通过熔断器调用
result = await circuit_manager.call_through_circuit_breaker(
    "my-service",
    risky_operation
)
```

## 配置

### 配置文件位置
- 主配置文件: `config/error_handling_config.yaml`

### 主要配置项

```yaml
# 错误隔离配置
error_isolation:
  monitoring_interval: 60  # 监控间隔（秒）
  heartbeat_timeout: 120   # 心跳超时（秒）
  error_rate_threshold: 0.1  # 错误率阈值

# 重试配置
retry_manager:
  enabled: true
  default_policy_id: default
  global_max_retries: 5

# 熔断器配置
circuit_breaker:
  global:
    failure_threshold: 5
    recovery_timeout: 60.0
    timeout: 30.0
```

## 监控和诊断

### 查看错误统计

```python
# 获取错误隔离统计
stats = isolation_manager.get_error_statistics()

# 获取重试统计
retry_stats = retry_manager.get_retry_statistics()

# 获取熔断器状态
circuit_states = await circuit_manager.get_all_circuit_states()
```

### 生成诊断报告

```python
from error_logger import DiagnosticCollector, DiagnosticLevel

collector = DiagnosticCollector()
report = await collector.generate_diagnostic_report(
    diagnostic_level=DiagnosticLevel.COMPREHENSIVE
)
```

## 最佳实践

1. **合理配置重试策略**: 根据服务特性选择合适的重试策略
2. **设置合理的阈值**: 避免过于敏感或过于宽松的故障检测
3. **监控关键指标**: 定期检查错误率、响应时间等指标
4. **定期清理日志**: 避免日志文件占用过多磁盘空间
5. **使用结构化日志**: 便于后续的错误分析和诊断

## 故障排查

### 常见问题

1. **熔断器频繁打开**
   - 检查服务是否真的不稳定
   - 调整失败阈值
   - 检查网络连接

2. **重试次数过多**
   - 调整重试策略
   - 检查错误类型是否可重试
   - 考虑使用指数退避

3. **日志文件过大**
   - 启用日志压缩
   - 调整日志轮转策略
   - 定期清理旧日志

### 日志位置
- 错误日志: `logs/errors/`
- 诊断报告: `logs/diagnostics/`

## 测试

运行测试套件：

```bash
python -m pytest tests/test_error_handling_system.py -v
```

## 依赖

- Python 3.9+
- asyncio
- typing extensions (for Python < 3.8)

## 许可证

MIT License