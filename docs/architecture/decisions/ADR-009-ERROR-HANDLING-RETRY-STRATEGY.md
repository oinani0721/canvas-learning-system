# ADR-009: 错误处理与重试策略

## 状态

**已接受** | 2025-11-24

## 背景

Canvas Learning System 涉及多种可能失败的操作：

1. **LLM API调用** - 速率限制、超时、API错误
2. **数据库操作** - SQLite锁、连接错误
3. **文件操作** - Canvas文件读写
4. **网络请求** - SSE连接、HTTP请求
5. **Agent执行** - 状态错误、超时

需要统一的错误处理策略来：
- 提供可靠的重试机制
- 快速失败避免资源浪费
- 给用户清晰的错误反馈
- 便于问题排查和分析

## 决策

### 核心组件

| 组件 | 方案 | 用途 |
|------|------|------|
| **重试库** | tenacity | 指数退避重试 |
| **熔断器** | 轻量级自实现 | 连续失败时快速失败 |
| **错误存储** | SQLite | 结构化错误记录 |
| **用户通知** | 分级通知 | Notice/Modal/状态栏 |

### 依赖

```toml
# pyproject.toml
[project.dependencies]
tenacity = ">=8.2"
```

## 实现细节

### 1. 错误分类体系

```python
# src/errors.py
from enum import Enum
from typing import Optional

class ErrorCategory(Enum):
    """错误分类"""
    RETRYABLE = "retryable"
    NON_RETRYABLE = "non_retryable"
    FATAL = "fatal"

class ErrorCode(Enum):
    """错误码"""
    # LLM相关 (1xxx)
    LLM_RATE_LIMIT = 1001
    LLM_TIMEOUT = 1002
    LLM_API_ERROR = 1003
    LLM_INVALID_RESPONSE = 1004

    # 熔断器 (1xxx)
    CIRCUIT_BREAKER_OPEN = 1100

    # 数据库相关 (2xxx)
    DB_CONNECTION_ERROR = 2001
    DB_LOCK_ERROR = 2002
    DB_QUERY_ERROR = 2003

    # 文件相关 (3xxx)
    FILE_NOT_FOUND = 3001
    FILE_PERMISSION_ERROR = 3002
    FILE_FORMAT_ERROR = 3003

    # 网络相关 (4xxx)
    NETWORK_TIMEOUT = 4001
    NETWORK_CONNECTION_ERROR = 4002
    SSE_DISCONNECTED = 4003

    # Agent相关 (5xxx)
    AGENT_STATE_ERROR = 5001
    AGENT_TIMEOUT = 5002
    AGENT_INVALID_INPUT = 5003

class CanvasError(Exception):
    """Canvas系统基础异常"""
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        category: ErrorCategory = ErrorCategory.NON_RETRYABLE,
        original_error: Optional[Exception] = None,
        context: Optional[dict] = None,
    ):
        self.code = code
        self.message = message
        self.category = category
        self.original_error = original_error
        self.context = context or {}
        super().__init__(message)

    @property
    def is_retryable(self) -> bool:
        return self.category == ErrorCategory.RETRYABLE

class LLMError(CanvasError):
    """LLM调用异常"""
    pass

class DatabaseError(CanvasError):
    """数据库异常"""
    pass

class FileError(CanvasError):
    """文件操作异常"""
    pass

class NetworkError(CanvasError):
    """网络异常"""
    pass

class AgentError(CanvasError):
    """Agent执行异常"""
    pass

class CircuitBreakerError(CanvasError):
    """熔断器打开异常"""
    def __init__(self, status: dict):
        super().__init__(
            code=ErrorCode.CIRCUIT_BREAKER_OPEN,
            message=f"Circuit breaker is open. Retry after {status.get('can_retry_at')}",
            category=ErrorCategory.RETRYABLE,
        )
        self.status = status
```

### 2. 重试策略配置

```python
# src/retry_config.py
from tenacity import (
    retry,
    stop_after_attempt,
    stop_after_delay,
    wait_random_exponential,
    wait_fixed,
    retry_if_exception_type,
    before_sleep_log,
    after_log,
)
import logging

logger = logging.getLogger(__name__)

class RetryConfig:
    """重试策略配置"""

    # LLM API调用
    LLM_API = {
        "stop": stop_after_attempt(5) | stop_after_delay(60),
        "wait": wait_random_exponential(multiplier=1, min=2, max=30),
        "retry": retry_if_exception_type((
            LLMError,
            TimeoutError,
            ConnectionError,
        )),
        "before_sleep": before_sleep_log(logger, logging.WARNING),
    }

    # 数据库操作
    DATABASE = {
        "stop": stop_after_attempt(3),
        "wait": wait_fixed(0.5),
        "retry": retry_if_exception_type((DatabaseError,)),
    }

    # 网络请求
    NETWORK = {
        "stop": stop_after_attempt(3) | stop_after_delay(30),
        "wait": wait_random_exponential(multiplier=0.5, min=1, max=10),
        "retry": retry_if_exception_type((
            NetworkError,
            TimeoutError,
        )),
    }

    # Embedding生成
    EMBEDDING = {
        "stop": stop_after_attempt(2),
        "wait": wait_fixed(2),
        "retry": retry_if_exception_type((TimeoutError,)),
    }

def with_retry(config_name: str):
    """重试装饰器工厂"""
    config = getattr(RetryConfig, config_name)
    return retry(**config)
```

### 3. 轻量级熔断器

```python
# src/circuit_breaker.py
from datetime import datetime, timedelta
from typing import Optional

class LightweightCircuitBreaker:
    """轻量级熔断器"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._is_open = False

    @property
    def is_open(self) -> bool:
        if not self._is_open:
            return False
        if self._should_try_reset():
            return False
        return True

    def _should_try_reset(self) -> bool:
        if self._last_failure_time is None:
            return True
        elapsed = datetime.now() - self._last_failure_time
        return elapsed > timedelta(seconds=self.recovery_timeout)

    def record_success(self):
        self._failure_count = 0
        self._is_open = False

    def record_failure(self):
        self._failure_count += 1
        self._last_failure_time = datetime.now()
        if self._failure_count >= self.failure_threshold:
            self._is_open = True

    def get_status(self) -> dict:
        return {
            "is_open": self.is_open,
            "failure_count": self._failure_count,
            "last_failure": (
                self._last_failure_time.isoformat()
                if self._last_failure_time else None
            ),
            "can_retry_at": (
                (self._last_failure_time + timedelta(seconds=self.recovery_timeout)).isoformat()
                if self._is_open and self._last_failure_time else None
            ),
        }
```

### 4. LLM客户端集成示例

```python
# src/llm_client.py
from tenacity import retry
from src.retry_config import RetryConfig
from src.circuit_breaker import LightweightCircuitBreaker
from src.errors import LLMError, ErrorCode, ErrorCategory, CircuitBreakerError
import logging

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.circuit_breaker = LightweightCircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
        )

    @retry(**RetryConfig.LLM_API)
    async def generate(self, prompt: str) -> str:
        # 检查熔断器
        if self.circuit_breaker.is_open:
            raise CircuitBreakerError(self.circuit_breaker.get_status())

        try:
            result = await self._call_api(prompt)
            self.circuit_breaker.record_success()
            return result

        except RateLimitError as e:
            self.circuit_breaker.record_failure()
            raise LLMError(
                code=ErrorCode.LLM_RATE_LIMIT,
                message=f"Rate limit exceeded: {e}",
                category=ErrorCategory.RETRYABLE,
                original_error=e,
            )

        except TimeoutError as e:
            self.circuit_breaker.record_failure()
            raise LLMError(
                code=ErrorCode.LLM_TIMEOUT,
                message=f"LLM timeout: {e}",
                category=ErrorCategory.RETRYABLE,
                original_error=e,
            )

        except Exception as e:
            self.circuit_breaker.record_failure()
            raise LLMError(
                code=ErrorCode.LLM_API_ERROR,
                message=f"LLM API error: {e}",
                category=ErrorCategory.NON_RETRYABLE,
                original_error=e,
            )

    def get_status(self) -> dict:
        return self.circuit_breaker.get_status()
```

### 5. 错误存储

```python
# src/error_store.py
import sqlite3
import json
from datetime import datetime
from pathlib import Path

class ErrorStore:
    """本地错误存储"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    error_code INTEGER,
                    error_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    stack_trace TEXT,
                    context TEXT,
                    resolved INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_errors_timestamp
                ON errors(timestamp DESC)
            """)

    def record_error(
        self,
        error_type: str,
        message: str,
        error_code: int | None = None,
        stack_trace: str | None = None,
        context: dict | None = None,
    ):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO errors (timestamp, error_code, error_type, message, stack_trace, context)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(),
                    error_code,
                    error_type,
                    message,
                    stack_trace,
                    json.dumps(context) if context else None,
                ),
            )

    def get_recent_errors(self, limit: int = 50) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM errors ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_error_summary(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            # 按类型统计
            cursor = conn.execute("""
                SELECT error_type, COUNT(*) as count
                FROM errors
                WHERE timestamp > datetime('now', '-7 days')
                GROUP BY error_type
                ORDER BY count DESC
            """)
            by_type = {row[0]: row[1] for row in cursor.fetchall()}

            # 总数
            cursor = conn.execute("SELECT COUNT(*) FROM errors")
            total = cursor.fetchone()[0]

            # 最近24小时
            cursor = conn.execute("""
                SELECT COUNT(*) FROM errors
                WHERE timestamp > datetime('now', '-1 day')
            """)
            last_24h = cursor.fetchone()[0]

            return {
                "total": total,
                "last_24h": last_24h,
                "by_type": by_type,
            }

    def cleanup_old_errors(self, days: int = 30):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM errors WHERE timestamp < datetime('now', ?)",
                (f"-{days} days",),
            )
```

### 6. 统一错误上报器

```python
# src/error_reporter.py
import logging
import traceback
from typing import Optional
from src.error_store import ErrorStore
from src.errors import CanvasError

logger = logging.getLogger(__name__)

class ErrorReporter:
    """统一错误上报器"""

    def __init__(
        self,
        error_store: ErrorStore,
        sentry_dsn: Optional[str] = None,
    ):
        self.error_store = error_store
        self.sentry_enabled = sentry_dsn is not None

        if self.sentry_enabled:
            import sentry_sdk
            sentry_sdk.init(dsn=sentry_dsn, send_default_pii=False)

    def report(
        self,
        error: Exception,
        context: Optional[dict] = None,
    ) -> str:
        """上报错误，返回用户友好消息"""
        # 1. 记录到日志
        logger.error(f"{type(error).__name__}: {error}", exc_info=True)

        # 2. 存储到SQLite
        error_code = error.code.value if isinstance(error, CanvasError) else None
        self.error_store.record_error(
            error_type=type(error).__name__,
            message=str(error),
            error_code=error_code,
            stack_trace=traceback.format_exc(),
            context=context,
        )

        # 3. 可选：上报到Sentry
        if self.sentry_enabled:
            import sentry_sdk
            sentry_sdk.capture_exception(error)

        # 4. 返回用户友好消息
        return self._get_user_message(error)

    def _get_user_message(self, error: Exception) -> str:
        if isinstance(error, CanvasError):
            messages = {
                1001: "LLM服务繁忙，请稍后重试",
                1002: "请求超时，请检查网络连接",
                1003: "API Key无效或账户余额不足",
                1100: "LLM服务暂时不可用，稍后自动重试",
                2001: "数据库连接失败",
                3001: "Canvas文件不存在",
                3003: "Canvas文件格式错误",
            }
            return messages.get(error.code.value, error.message)
        return "发生未知错误，请查看日志"

    def get_summary(self) -> dict:
        return self.error_store.get_error_summary()
```

### 7. 用户通知系统

```typescript
// src/notification.ts
import { App, Notice, Modal, ButtonComponent } from 'obsidian';

export enum NotificationLevel {
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  FATAL = 'fatal',
}

export class NotificationManager {
  private statusBar: HTMLElement;

  constructor(private app: App, statusBar: HTMLElement) {
    this.statusBar = statusBar;
  }

  notify(
    level: NotificationLevel,
    message: string,
    options?: {
      duration?: number;
      action?: { label: string; callback: () => void };
    }
  ) {
    switch (level) {
      case NotificationLevel.INFO:
        this.showNotice(message, options?.duration || 3000);
        break;

      case NotificationLevel.WARNING:
        this.showNotice(`⚠️ ${message}`, options?.duration || 5000);
        this.updateStatusBar('warning', message);
        break;

      case NotificationLevel.ERROR:
        this.showNotice(`❌ ${message}`, options?.duration || 8000);
        this.updateStatusBar('error', message);
        break;

      case NotificationLevel.FATAL:
        this.showErrorModal(message, options?.action);
        this.updateStatusBar('error', message);
        break;
    }
  }

  private showNotice(message: string, duration: number) {
    new Notice(message, duration);
  }

  private showErrorModal(
    message: string,
    action?: { label: string; callback: () => void }
  ) {
    const modal = new ErrorModal(this.app, message, action);
    modal.open();
  }

  private updateStatusBar(
    status: 'ready' | 'warning' | 'error',
    message: string
  ) {
    const icons = { ready: '✅', warning: '⚠️', error: '❌' };
    this.statusBar.setText(`${icons[status]} Canvas: ${message.slice(0, 30)}`);

    if (status !== 'error') {
      setTimeout(() => {
        this.statusBar.setText('✅ Canvas: Ready');
      }, 5000);
    }
  }

  clearError() {
    this.statusBar.setText('✅ Canvas: Ready');
  }
}

class ErrorModal extends Modal {
  constructor(
    app: App,
    private message: string,
    private action?: { label: string; callback: () => void }
  ) {
    super(app);
  }

  onOpen() {
    const { contentEl } = this;

    contentEl.createEl('h2', { text: '❌ 操作失败' });
    contentEl.createEl('p', { text: this.message });

    const buttonContainer = contentEl.createDiv({ cls: 'modal-button-container' });

    if (this.action) {
      new ButtonComponent(buttonContainer)
        .setButtonText(this.action.label)
        .setCta()
        .onClick(() => {
          this.close();
          this.action!.callback();
        });
    }

    new ButtonComponent(buttonContainer)
      .setButtonText('关闭')
      .onClick(() => this.close());
  }
}
```

### 8. 错误码与通知级别映射

```typescript
// src/error-notification-map.ts
import { NotificationLevel } from './notification';

export const ERROR_NOTIFICATION_MAP: Record<number, {
  level: NotificationLevel;
  message: string;
  action?: { label: string; settingsTab?: string };
}> = {
  // LLM相关
  1001: {
    level: NotificationLevel.WARNING,
    message: 'LLM服务繁忙，正在重试...',
  },
  1002: {
    level: NotificationLevel.WARNING,
    message: '请求超时，正在重试...',
  },
  1003: {
    level: NotificationLevel.FATAL,
    message: 'API Key无效或账户余额不足',
    action: { label: '打开设置', settingsTab: 'api' },
  },

  // 熔断器
  1100: {
    level: NotificationLevel.ERROR,
    message: 'LLM服务暂时不可用，稍后自动重试',
  },

  // 文件相关
  3001: {
    level: NotificationLevel.ERROR,
    message: 'Canvas文件不存在',
  },
  3003: {
    level: NotificationLevel.FATAL,
    message: 'Canvas文件格式错误',
    action: { label: '查看帮助' },
  },

  // 数据库相关
  2001: {
    level: NotificationLevel.ERROR,
    message: '数据库连接失败，请重启插件',
  },
};
```

### 9. API错误响应

```python
# src/api/error_handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse
from src.errors import CanvasError, ErrorCode

async def canvas_error_handler(request: Request, exc: CanvasError):
    return JSONResponse(
        status_code=get_http_status(exc.code),
        content={
            "error": {
                "code": exc.code.value,
                "message": exc.message,
                "retryable": exc.is_retryable,
                "context": exc.context,
            }
        }
    )

def get_http_status(code: ErrorCode) -> int:
    mapping = {
        ErrorCode.LLM_RATE_LIMIT: 429,
        ErrorCode.LLM_TIMEOUT: 504,
        ErrorCode.CIRCUIT_BREAKER_OPEN: 503,
        ErrorCode.DB_CONNECTION_ERROR: 503,
        ErrorCode.FILE_NOT_FOUND: 404,
        ErrorCode.AGENT_INVALID_INPUT: 400,
    }
    return mapping.get(code, 500)

# 注册到FastAPI
# app.add_exception_handler(CanvasError, canvas_error_handler)
```

### 10. 日志配置

```python
# src/logging_config.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging(vault_path: str):
    log_dir = Path(vault_path) / ".canvas-learning" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # 主日志
    main_handler = RotatingFileHandler(
        log_dir / "canvas-learning.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    main_handler.setLevel(logging.INFO)
    main_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    ))

    # 错误日志
    error_handler = RotatingFileHandler(
        log_dir / "errors.log",
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d\n%(message)s"
    ))

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(main_handler)
    root_logger.addHandler(error_handler)

    return root_logger
```

## 配置汇总

### 熔断器配置

| 参数 | 值 | 说明 |
|------|-----|------|
| failure_threshold | 5 | 连续失败5次触发熔断 |
| recovery_timeout | 60s | 60秒后尝试恢复 |

### 重试配置

| 场景 | 最大重试 | 最大延迟 | 退避策略 |
|------|----------|----------|----------|
| LLM API | 5次 / 60s | 30s | 指数退避+抖动 |
| 数据库 | 3次 | 0.5s | 固定延迟 |
| 网络 | 3次 / 30s | 10s | 指数退避+抖动 |
| Embedding | 2次 | 2s | 固定延迟 |

### 通知级别映射

| 错误类型 | 级别 | 通知方式 |
|----------|------|----------|
| 致命错误 (API Key失效) | FATAL | Modal + 状态栏 |
| 熔断触发 | ERROR | Notice (8s) + 状态栏 |
| 单次超时 | WARNING | Notice (5s) |
| 任务完成 | INFO | Notice (3s) |

### 错误存储

| 参数 | 值 |
|------|-----|
| 存储位置 | `.canvas-learning/errors.db` |
| 保留天数 | 30天 |
| 云端上报 | 默认关闭，用户可选开启 |

## 理由

### 为什么选择 tenacity

1. **功能全面** - 支持多种退避策略
2. **异步支持** - 完美支持 FastAPI/LangGraph
3. **装饰器语法** - 代码简洁
4. **社区活跃** - 文档完善

### 为什么使用轻量级熔断器

1. **简单可靠** - ~50行代码
2. **避免无效调用** - 节省LLM费用
3. **快速失败** - 用户立即知道状态
4. **自动恢复** - 服务恢复后自动重连

### 为什么分级通知

1. **避免过度打扰** - 大多数用Notice即可
2. **重要错误强调** - Fatal用Modal强制处理
3. **持续状态** - 状态栏显示熔断状态
4. **用户体验** - 清晰的错误反馈

### 为什么默认不启用Sentry

1. **隐私优先** - Canvas内容敏感
2. **本地足够** - SQLite存储+日志可排查
3. **用户选择** - 可在设置中开启

## 影响

### 正面影响

1. **可靠性** - 自动重试提高成功率
2. **资源保护** - 熔断避免无效调用
3. **用户体验** - 清晰的错误反馈
4. **可维护性** - 结构化错误记录

### 负面影响

1. **代码复杂度** - 增加错误处理逻辑
2. **调试难度** - 重试可能掩盖问题

### 缓解措施

1. **详细日志** - 记录每次重试
2. **统一接口** - 使用装饰器简化代码
3. **监控面板** - 可选的错误统计UI

## 参考资料

- [Tenacity Documentation](https://tenacity.readthedocs.io/)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Obsidian Plugin API](https://docs.obsidian.md/Plugins/User+interface)

---

**作者**: Winston (Architect Agent)
**审核**: 待定
**批准**: 待定
