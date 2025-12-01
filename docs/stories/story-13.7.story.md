# Story 13.7: 错误处理

## Status
Pending

## Story

**As a** Obsidian Plugin用户,
**I want** 插件能够优雅地处理所有错误情况，提供清晰的错误提示和恢复选项,
**so that** 在遇到问题时能快速理解错误原因并采取相应措施，而不会因插件崩溃而丢失工作进度。

## Acceptance Criteria

1. 实现全局错误捕获机制，确保所有未处理的异常都被捕获并记录
2. 使用Obsidian Notice API提供用户友好的错误提示（按错误严重程度分级）
3. 实现结构化的错误日志记录系统，记录错误类型、时间戳、上下文信息
4. 对网络请求实现智能重试机制（指数退避、最大重试次数限制）
5. 实现错误恢复策略，包括自动降级和手动恢复选项
6. 创建错误处理测试用例，覆盖所有主要错误场景（网络失败、Canvas解析错误、API错误等）
7. 提供错误报告导出功能，便于用户反馈问题

## Tasks / Subtasks

- [ ] Task 1: 实现错误分类系统 (AC: 1, 2)
  - [ ] 定义错误类型层级（NetworkError, CanvasError, APIError, ValidationError）
  - [ ] 创建PluginError基类，继承自Error
  - [ ] 为每种错误类型实现专门的子类（保留错误上下文）
  - [ ] 定义错误严重程度等级（Critical, Warning, Info）
  - [ ] 实现错误到Notice样式的映射（红色提示框用于Critical，橙色用于Warning）

- [ ] Task 2: 实现全局错误处理器 (AC: 1, 3)
  - [ ] 创建GlobalErrorHandler单例类
  - [ ] 实现uncaughtException和unhandledRejection的全局监听器
  - [ ] 集成结构化日志系统（使用Obsidian的console API）
  - [ ] 记录错误堆栈、时间戳、用户操作上下文
  - [ ] 实现错误去重逻辑（避免重复报告相同错误）

- [ ] Task 3: 实现用户友好的错误提示 (AC: 2)
  - [ ] 创建ErrorNotifier类封装Notice API
  - [ ] 实现showError()方法，根据错误类型选择Notice样式
  - [ ] 添加可操作的错误提示（带"重试"或"查看详情"按钮）
  - [ ] 实现错误消息国际化支持（中英文错误提示）
  - [ ] 创建错误详情模态框，显示完整错误堆栈和上下文

- [ ] Task 4: 实现网络请求重试机制 (AC: 4)
  - [ ] 创建RetryPolicy类定义重试策略
  - [ ] 实现指数退避算法（initialDelay: 1s, maxDelay: 30s, backoffFactor: 2）
  - [ ] 添加最大重试次数限制（默认3次）
  - [ ] 实现智能重试判断（只重试可恢复的错误，如网络超时、503错误）
  - [ ] 集成到API客户端（APIClient类），包装所有HTTP请求

- [ ] Task 5: 实现错误恢复策略 (AC: 5)
  - [ ] 创建ErrorRecoveryManager类
  - [ ] 实现自动降级策略（API失败时使用缓存数据）
  - [ ] 添加手动恢复选项（"刷新数据"、"清除缓存"、"重启插件"）
  - [ ] 实现状态回滚机制（操作失败时恢复到之前的状态）
  - [ ] 添加错误恢复状态通知（告知用户插件已自动降级）

- [ ] Task 6: 实现错误日志系统 (AC: 3, 7)
  - [ ] 创建ErrorLogger类管理错误日志
  - [ ] 实现日志持久化（存储到插件数据目录）
  - [ ] 定义日志文件格式（JSON Lines，每行一个错误记录）
  - [ ] 实现日志轮转策略（保留最近7天的日志）
  - [ ] 创建错误报告导出功能（生成markdown格式的错误报告）

- [ ] Task 7: 集成到现有代码 (AC: 1, 4, 5)
  - [ ] 在CanvasReviewPlugin.onload()中初始化全局错误处理器
  - [ ] 为所有async操作添加try-catch错误处理
  - [ ] 在API客户端中集成重试机制
  - [ ] 在命令处理器中添加错误恢复逻辑
  - [ ] 更新PluginSettingsTab，添加错误日志查看入口

- [ ] Task 8: 编写错误处理测试 (AC: 6)
  - [ ] 测试网络失败场景（超时、断网、404、500错误）
  - [ ] 测试Canvas文件解析错误（无效JSON、缺失字段）
  - [ ] 测试API响应错误（验证错误、业务逻辑错误）
  - [ ] 测试重试机制（验证指数退避、最大重试次数）
  - [ ] 测试错误恢复（验证自动降级、手动恢复）
  - [ ] 测试错误日志记录和导出功能

## Dev Notes

### 架构上下文

**错误处理在Obsidian Plugin中的作用** [Source: canvas-progress-tracker/docs/obsidian-plugin-architecture.md#错误处理层]

本Story实现插件的全局错误处理系统，确保所有错误被妥善处理：

```
Obsidian插件错误处理架构:
├── GlobalErrorHandler (全局捕获)
├── ErrorNotifier (用户提示)
├── RetryPolicy (重试策略)
├── ErrorRecoveryManager (恢复策略)
└── ErrorLogger (日志记录)
```

**后端错误分类参考** [Source: backend/app/exceptions/canvas_exceptions.py]
Canvas Learning System后端已定义的错误类型：
- `CanvasException` (基类, 500)
- `CanvasNotFoundError` (404)
- `NodeNotFoundError` (404)
- `ValidationError` (400)
- `AgentExecutionError` (500)

插件端错误分类应与后端保持一致，便于前后端错误映射。

### 错误分类设计

**插件错误类型层级** [Source: canvas-progress-tracker/docs/obsidian-plugin-prd.md#错误处理需求]

```typescript
// ✅ Verified from Obsidian Plugin API (Notice API)
abstract class PluginError extends Error {
  constructor(
    message: string,
    public severity: 'critical' | 'warning' | 'info',
    public context?: Record<string, any>,
    public recoverable: boolean = true
  ) {
    super(message);
    this.name = this.constructor.name;
  }
}

// Network-related errors (可重试)
class NetworkError extends PluginError {
  constructor(message: string, public statusCode?: number, context?: any) {
    super(message, 'critical', context, true);
  }
}

// Canvas file parsing errors (不可重试)
class CanvasParseError extends PluginError {
  constructor(message: string, public filePath: string, context?: any) {
    super(message, 'critical', { ...context, filePath }, false);
  }
}

// API business logic errors (部分可重试)
class APIError extends PluginError {
  constructor(
    message: string,
    public code: number,
    public apiEndpoint: string,
    context?: any
  ) {
    const recoverable = code >= 500; // 5xx errors are retryable
    super(message, code >= 500 ? 'critical' : 'warning', context, recoverable);
  }
}

// Validation errors (不可重试)
class ValidationError extends PluginError {
  constructor(message: string, public field: string, context?: any) {
    super(message, 'warning', { ...context, field }, false);
  }
}
```

### Notice API使用

**Obsidian Notice API规范** [Source: .claude/skills/obsidian-canvas/references/README.md#Notice]

```typescript
// ✅ Verified from @obsidian-canvas Skill (Notice API)
import { Notice } from 'obsidian';

class ErrorNotifier {
  showError(error: PluginError): void {
    // Critical errors: red notice, 10s duration
    if (error.severity === 'critical') {
      new Notice(
        `❌ 错误: ${error.message}`,
        10000 // 10 seconds
      );
    }
    // Warning: orange notice, 5s duration
    else if (error.severity === 'warning') {
      new Notice(
        `⚠️ 警告: ${error.message}`,
        5000
      );
    }
    // Info: default notice, 3s duration
    else {
      new Notice(
        `ℹ️ ${error.message}`,
        3000
      );
    }
  }

  showRecoveryOptions(error: PluginError, onRetry: () => void): void {
    // Create notice with button fragment
    const frag = document.createDocumentFragment();
    const span = frag.createEl('span', { text: `❌ ${error.message} ` });
    const retryBtn = frag.createEl('button', { text: '重试' });
    retryBtn.addEventListener('click', () => {
      onRetry();
    });
    frag.appendChild(retryBtn);

    new Notice(frag, 0); // 0 = doesn't auto-dismiss
  }
}
```

### 重试机制设计

**指数退避算法** [Source: canvas-progress-tracker/docs/obsidian-plugin-prd.md#网络请求重试策略]

```typescript
class RetryPolicy {
  constructor(
    public maxRetries: number = 3,
    public initialDelay: number = 1000, // 1s
    public maxDelay: number = 30000,    // 30s
    public backoffFactor: number = 2
  ) {}

  async executeWithRetry<T>(
    operation: () => Promise<T>,
    onRetry?: (attempt: number, delay: number) => void
  ): Promise<T> {
    let lastError: Error;

    for (let attempt = 1; attempt <= this.maxRetries + 1; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error as Error;

        // Don't retry if not recoverable
        if (error instanceof PluginError && !error.recoverable) {
          throw error;
        }

        // No more retries
        if (attempt > this.maxRetries) {
          throw error;
        }

        // Calculate delay with exponential backoff
        const delay = Math.min(
          this.initialDelay * Math.pow(this.backoffFactor, attempt - 1),
          this.maxDelay
        );

        onRetry?.(attempt, delay);

        // Wait before retry
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }

    throw lastError!;
  }
}
```

### 错误日志格式

**JSON Lines日志格式** [Source: canvas-progress-tracker/docs/obsidian-plugin-prd.md#错误日志规范]

```typescript
interface ErrorLogEntry {
  timestamp: string;        // ISO 8601 format
  errorType: string;        // PluginError subclass name
  severity: 'critical' | 'warning' | 'info';
  message: string;
  stack?: string;           // Error stack trace
  context?: Record<string, any>;
  userAction?: string;      // What the user was doing
  pluginVersion: string;
  obsidianVersion: string;
}

// Example log entry
{
  "timestamp": "2025-01-27T10:30:45.123Z",
  "errorType": "NetworkError",
  "severity": "critical",
  "message": "Failed to connect to API server",
  "stack": "NetworkError: Failed to connect...\n  at APIClient.request...",
  "context": {
    "url": "http://localhost:3005/api/v1/canvas/decompose",
    "statusCode": null,
    "retryAttempt": 3
  },
  "userAction": "Executing decompose command on node-abc123",
  "pluginVersion": "1.0.0",
  "obsidianVersion": "1.5.3"
}
```

### 错误恢复策略

**自动降级示例** [Source: canvas-progress-tracker/docs/obsidian-plugin-architecture.md#错误恢复机制]

```typescript
class ErrorRecoveryManager {
  async recoverFromAPIError(
    error: APIError,
    operation: string,
    fallbackData?: any
  ): Promise<any> {
    // Strategy 1: Use cached data if available
    if (fallbackData) {
      new Notice(
        `⚠️ API服务暂时不可用，已使用缓存数据`,
        5000
      );
      return fallbackData;
    }

    // Strategy 2: Prompt user for manual recovery
    if (error.recoverable) {
      return this.promptManualRecovery(error, operation);
    }

    // Strategy 3: Graceful degradation (disable feature)
    new Notice(
      `❌ ${operation}功能暂时不可用，请稍后重试`,
      10000
    );
    throw error;
  }

  private async promptManualRecovery(
    error: PluginError,
    operation: string
  ): Promise<any> {
    // Show modal with recovery options
    const modal = new RecoveryModal(
      this.app,
      error,
      operation,
      {
        retry: () => { /* retry logic */ },
        clearCache: () => { /* clear cache */ },
        reportIssue: () => { /* export error report */ }
      }
    );

    return modal.open();
  }
}
```

### 集成到API客户端

**API客户端错误处理** [Source: Story 13.3 - API客户端实现]

```typescript
// ✅ Verified from @obsidian-canvas Skill (Plugin API)
class APIClient {
  private retryPolicy: RetryPolicy;
  private errorHandler: GlobalErrorHandler;

  async request<T>(
    endpoint: string,
    options: RequestOptions
  ): Promise<T> {
    return this.retryPolicy.executeWithRetry(
      async () => {
        try {
          const response = await fetch(
            `${this.baseURL}${endpoint}`,
            options
          );

          if (!response.ok) {
            throw new APIError(
              `API request failed: ${response.statusText}`,
              response.status,
              endpoint
            );
          }

          return await response.json();

        } catch (error) {
          if (error instanceof TypeError) {
            // Network error (fetch failed)
            throw new NetworkError(
              'Unable to connect to API server',
              undefined,
              { endpoint, originalError: error.message }
            );
          }
          throw error;
        }
      },
      (attempt, delay) => {
        console.log(`Retry attempt ${attempt} after ${delay}ms`);
        new Notice(
          `正在重试连接... (尝试 ${attempt}/${this.retryPolicy.maxRetries})`,
          2000
        );
      }
    );
  }
}
```

### 测试要求

**错误场景测试清单** [Source: canvas-progress-tracker/docs/obsidian-plugin-prd.md#测试需求]

1. **网络错误测试**:
   - 模拟网络超时（使用延迟的mock server）
   - 模拟连接失败（关闭API服务器）
   - 验证重试机制（检查重试次数和延迟）
   - 验证最终失败通知

2. **Canvas解析错误测试**:
   - 无效JSON格式
   - 缺失必需字段（nodes, edges）
   - 无效节点类型
   - 验证错误提示和日志记录

3. **API业务逻辑错误测试**:
   - 404错误（Canvas不存在）
   - 400错误（验证失败）
   - 500错误（服务器内部错误）
   - 验证错误分类和重试策略

4. **错误恢复测试**:
   - 测试自动降级（使用缓存）
   - 测试手动恢复选项
   - 测试状态回滚

5. **日志系统测试**:
   - 验证日志文件创建
   - 验证日志条目格式
   - 验证日志轮转
   - 验证错误报告导出

### 性能考虑

**错误处理性能优化** [Source: canvas-progress-tracker/docs/obsidian-plugin-prd.md#性能要求]

1. **避免过度日志记录**:
   - 实现错误去重（相同错误1分钟内只记录一次）
   - 使用异步日志写入（不阻塞主线程）
   - 限制日志文件大小（单文件最大1MB）

2. **重试策略优化**:
   - 快速失败原则（明确不可恢复的错误立即停止）
   - 避免雪崩效应（限制并发重试数量）
   - 添加断路器模式（连续失败后暂停重试）

3. **内存管理**:
   - 限制错误上下文大小（避免记录大对象）
   - 定期清理过期日志
   - 使用弱引用存储错误上下文

### 编码规范

**错误处理最佳实践** [Source: canvas-progress-tracker/docs/obsidian-plugin-architecture.md#开发规范]

```typescript
// ✅ DO: 始终为async操作添加错误处理
try {
  const result = await this.apiClient.request('/endpoint');
  return result;
} catch (error) {
  if (error instanceof NetworkError) {
    return this.errorRecovery.recoverFromNetworkError(error);
  }
  throw error; // Let global handler catch it
}

// ❌ DON'T: 吞掉错误而不记录
try {
  await someOperation();
} catch (error) {
  // Silent failure - bad practice
}

// ✅ DO: 提供上下文信息
throw new ValidationError(
  'Invalid node color',
  'color',
  { providedValue: userInput, allowedValues: ['red', 'green', 'blue'] }
);

// ❌ DON'T: 抛出通用错误
throw new Error('Something went wrong');
```

### 集成考虑

**与现有系统集成** [Source: Story 13.1 - Plugin项目初始化]

1. **插件主类集成**:
   ```typescript
   // In CanvasReviewPlugin.onload()
   async onload() {
     // Initialize global error handler FIRST
     this.errorHandler = new GlobalErrorHandler(this);

     try {
       await this.loadSettings();
       this.initializeManagers();
       this.registerCommands();
       // ...
     } catch (error) {
       this.errorHandler.handleFatalError(error);
     }
   }
   ```

2. **命令处理器集成**:
   ```typescript
   // In command callbacks
   this.addCommand({
     id: 'decompose-node',
     name: 'Decompose Node',
     callback: async () => {
       try {
         await this.commandExecutor.decomposeNode();
       } catch (error) {
         this.errorHandler.handleCommandError(error, 'decompose-node');
       }
     }
   });
   ```

3. **设置界面集成**:
   ```typescript
   // Add error log viewer in PluginSettingsTab
   new Setting(containerEl)
     .setName('错误日志')
     .setDesc('查看和导出插件错误日志')
     .addButton(button => button
       .setButtonText('查看日志')
       .onClick(async () => {
         const logs = await this.plugin.errorLogger.getRecentLogs();
         new ErrorLogModal(this.app, logs).open();
       }));
   ```

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-01-27 | 1.0 | 初始Story创建 | SM Agent (Bob) |

## Dev Agent Record

### Agent Model Used
待开发

### Debug Log References
待开发

### Completion Notes
待开发

### File List
**计划创建的文件：**
- `canvas-progress-tracker/obsidian-plugin/src/errors/PluginError.ts` - 错误基类和子类定义
- `canvas-progress-tracker/obsidian-plugin/src/errors/GlobalErrorHandler.ts` - 全局错误处理器
- `canvas-progress-tracker/obsidian-plugin/src/errors/ErrorNotifier.ts` - 错误通知管理器
- `canvas-progress-tracker/obsidian-plugin/src/errors/RetryPolicy.ts` - 重试策略实现
- `canvas-progress-tracker/obsidian-plugin/src/errors/ErrorRecoveryManager.ts` - 错误恢复管理器
- `canvas-progress-tracker/obsidian-plugin/src/errors/ErrorLogger.ts` - 错误日志系统
- `canvas-progress-tracker/obsidian-plugin/src/modals/ErrorLogModal.ts` - 错误日志查看模态框
- `canvas-progress-tracker/obsidian-plugin/src/modals/RecoveryModal.ts` - 错误恢复选项模态框
- `canvas-progress-tracker/obsidian-plugin/tests/errors/` - 错误处理测试目录

**修改的文件：**
- `canvas-progress-tracker/obsidian-plugin/main.ts` - 集成全局错误处理器
- `canvas-progress-tracker/obsidian-plugin/src/api/APIClient.ts` - 添加重试机制（依赖Story 13.3）
- `canvas-progress-tracker/obsidian-plugin/src/settings/PluginSettingsTab.ts` - 添加错误日志查看入口
- `canvas-progress-tracker/obsidian-plugin/src/commands/` - 为所有命令添加错误处理

## QA Results

### Review Date: 待开发

### Reviewed By: 待开发

### Code Quality Assessment
待开发

### Compliance Check
待开发

### Security Review
待开发

### Performance Considerations
待开发

### Architecture & Design Review
待开发

### Test Quality Review
待开发

### Final Status
待开发

---

**本Story完成后，Obsidian插件将具备完整的错误处理能力，确保在各种异常情况下都能优雅地处理错误，提供清晰的用户反馈，并记录详细的错误信息以便问题排查。**
