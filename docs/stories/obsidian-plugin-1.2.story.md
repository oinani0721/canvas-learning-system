# Story Obsidian-Plugin-1.2: 命令包装器实现

## Status
Pending

## Story

**As a** Canvas学习系统用户,
**I want** 在Obsidian中使用图形界面操作现有的斜杠命令,
**so that** 我可以无需离开Obsidian环境就能进行复习管理和学习操作。

## Acceptance Criteria

1. 实现CommandWrapper类，能够通过HTTP API与Claude Code通信
2. 包装核心复习命令：/review show, /review complete, /generate-review
3. 实现命令输出解析器，将命令行输出转换为结构化数据
4. 添加命令缓存机制，提高响应速度（缓存5分钟）
5. 实现错误处理和重试机制（最多3次重试）
6. 创建ReviewTask和ReviewPlan数据类型定义

## Tasks / Subtasks

- [ ] Task 1: 实现HTTP命令执行器 (AC: 1, 5)
  - [ ] 创建HttpCommandExecutor类实现ICommandExecutor接口
  - [ ] 实现execute()方法，支持POST请求到Claude Code API
  - [ ] 添加超时控制（默认30秒）和错误处理
  - [ ] 实现重试机制，支持指数退避策略
  - [ ] 添加请求头和认证支持

- [ ] Task 2: 实现命令输出解析器 (AC: 3)
  - [ ] 创建OutputParser接口和具体实现类
  - [ ] 实现ReviewOutputParser，解析/review show命令输出
  - [ ] 实现GenerateReviewOutputParser，解析/generate-review命令输出
  - [ ] 实现CompleteReviewOutputParser，解析/review complete命令输出
  - [ ] 添加解析错误处理和降级机制

- [ ] Task 3: 实现CommandWrapper主类 (AC: 1, 2)
  - [ ] 创建CommandWrapper类，集成执行器和解析器
  - [ ] 实现getReviewTasks()方法，包装/review show命令
  - [ ] 实现generateReviewPlan()方法，包装/generate-review命令
  - [ ] 实现completeReview()方法，包装/review complete命令
  - [ ] 添加命令参数验证和格式化

- [ ] Task 4: 实现缓存机制 (AC: 4)
  - [ ] 创建CommandCache类，支持TTL缓存
  - [ ] 实现内存缓存和持久化缓存策略
  - [ ] 添加缓存键生成和失效逻辑
  - [ ] 实现缓存命中率统计和监控
  - [ ] 配置默认缓存时间为5分钟

- [ ] Task 5: 定义数据类型 (AC: 6)
  - [ ] 创建ReviewTask接口，包含任务优先级、记忆强度等字段
  - [ ] 创建ReviewPlan接口，包含计划类型、难度、目标等字段
  - [ ] 创建ReviewResult接口，包含复习结果和统计数据
  - [ ] 创建CommandResult接口，统一命令执行结果格式
  - [ ] 添加所有类型的完整TypeScript类型注解

- [ ] Task 6: 集成测试和验证 (ALL AC)
  - [ ] 创建单元测试，测试每个命令包装器方法
  - [ ] 测试缓存机制的正确性和性能
  - [ ] 验证错误处理和重试逻辑
  - [ ] 测试解析器对各种输出格式的处理
  - [ ] 验证与Claude Code API的端到端通信

## Dev Notes

### 架构上下文

**命令包装层架构** [Source: canvas-progress-tracker/docs/obsidian-plugin-architecture.md#命令包装层]

本Story实现命令包装层，作为插件与现有斜杠命令系统之间的桥梁：

```mermaid
graph TB
    subgraph "Obsidian插件层"
        UI[React UI组件]
        CW[CommandWrapper] ⭐ 本Story实现
        API[API桥接层]
    end

    subgraph "现有系统"
        REVIEW[/review命令系统]
        GENERATE[/generate-review命令]
        CANVAS[/canvas-*命令]
    end

    subgraph "外部服务"
        CLAUDE[Claude Code API]
    end

    UI --> CW
    CW --> API
    API --> REVIEW
    API --> GENERATE
    REVIEW --> CLAUDE
    GENERATE --> CLAUDE
```

**核心设计原则** [Source: canvas-progress-tracker/docs/obsidian-plugin-architecture.md#命令包装层]
- **异步优先**: 所有命令执行都是异步操作
- **错误隔离**: 单个命令失败不影响其他功能
- **缓存优化**: 避免重复执行相同命令
- **类型安全**: 严格的TypeScript类型定义

### HTTP通信协议

**Claude Code API接口** [Source: canvas-progress-tracker/docs/obsidian-plugin-architecture.md#HTTP执行器实现]
```typescript
interface ExecuteOptions {
  timeout?: number;
  parseOutput?: boolean;
  input?: string;
  context?: Record<string, any>;
}

interface CommandResult {
  success: boolean;
  output?: string;
  error?: string;
  metadata?: {
    executionTime: number;
    cacheHit: boolean;
    retryCount: number;
  };
}
```

**API请求格式**:
```typescript
const payload = {
  command: '/review show',
  format: 'json',
  timeout: 10000,
  parseOutput: true,
  context: {
    source: 'obsidian-plugin',
    version: PLUGIN_VERSION,
  }
};
```

### 核心命令实现

**getReviewTasks方法** [Source: canvas-progress-tracker/docs/obsidian-plugin-architecture.md#命令包装器主类]
```typescript
async getReviewTasks(options?: ReviewOptions): Promise<ReviewTask[]> {
  const command = '/review show';
  const cacheKey = `${command}_${JSON.stringify(options)}`;

  // 检查缓存
  const cached = this.cache.get(cacheKey);
  if (cached && !this.isCacheExpired(cached)) {
    return cached.data;
  }

  // 执行命令
  const result = await this.executor.execute(command, {
    timeout: 10000,
    parseOutput: true,
  });

  if (!result.success) {
    throw new CommandExecutionError(result.error || '获取复习任务失败');
  }

  // 解析输出
  const parser = this.parsers.get(command);
  if (!parser) {
    throw new Error(`未找到命令 ${command} 的解析器`);
  }

  const tasks = parser.parse(result.output);

  // 缓存结果
  this.cache.set(cacheKey, tasks, 5 * 60 * 1000); // 5分钟缓存

  return tasks;
}
```

**generateReviewPlan方法**:
```typescript
async generateReviewPlan(
  canvas: string,
  options: ReviewPlanOptions = {}
): Promise<ReviewPlan> {
  const params = new URLSearchParams();

  if (options.planType) params.set('plan-type', options.planType);
  if (options.difficulty) params.set('difficulty', options.difficulty);
  if (options.duration) params.set('duration', String(options.duration));
  if (options.maxConcepts) params.set('max-concepts', String(options.maxConcepts));

  const command = `/generate-review ${canvas}${params.toString() ? ` --${params.toString()}` : ''}`;

  const result = await this.executor.execute(command, {
    timeout: 30000,
    parseOutput: true,
  });

  if (!result.success) {
    throw new CommandExecutionError(result.error || '生成复习计划失败');
  }

  const parser = this.parsers.get('/generate-review');
  return parser.parse(result.output);
}
```

### 数据类型定义

**ReviewTask接口** [Source: canvas-progress-tracker/docs/obsidian-plugin-architecture.md#数据模型]
```typescript
interface ReviewTask {
  id: string;
  canvasId: string;
  canvasTitle: string;
  conceptName: string;

  // 优先级和紧急度
  priority: 'critical' | 'high' | 'medium' | 'low';
  urgency: number; // 0-100

  // 记忆指标
  memoryStrength: number; // 记忆强度
  retentionRate: number; // 记忆保持率
  forgettingCurvePosition: number; // 遗忘曲线位置

  // 时间信息
  dueDate: Date;
  overdueDays: number;
  estimatedDuration: number; // 分钟

  // 学习状态
  lastReviewDate?: Date;
  streak: number; // 连续复习天数
  skipCount: number;
}
```

**ReviewPlan接口**:
```typescript
interface ReviewPlan {
  id: string;
  canvasId: string;
  canvasTitle: string;

  // 计划信息
  planType: 'weakness-focused' | 'comprehensive' | 'targeted';
  difficulty: 'easy' | 'medium' | 'hard' | 'adaptive';
  estimatedDuration: number;

  // 目标
  targetMastery: number;
  focusAreas: string[];
  maxConcepts: number;

  // 内容结构
  sections: ReviewSection[];
  resources: Resource[];

  // 生成信息
  generatedAt: Date;
  basedOnData: string[];
}
```

### 缓存策略

**多层缓存设计** [Source: canvas-progress-tracker/docs/obsidian-plugin-architecture.md#数据缓存策略]
```typescript
class CommandCache {
  private memoryCache: Map<string, CacheItem>;
  private persistentCache: IDBObjectStore;

  async get<T>(key: string): Promise<T | null> {
    // 1. 检查内存缓存
    const memoryItem = this.memoryCache.get(key);
    if (memoryItem && !this.isExpired(memoryItem)) {
      return memoryItem.data;
    }

    // 2. 检查持久化缓存
    const persistentItem = await this.persistentCache.get(key);
    if (persistentItem && !this.isExpired(persistentItem)) {
      this.memoryCache.set(key, persistentItem);
      return persistentItem.data;
    }

    return null;
  }

  async set<T>(key: string, data: T, ttl: number = 300000): Promise<void> {
    const item: CacheItem = {
      data,
      timestamp: Date.now(),
      ttl,
    };

    // 同时写入内存和持久化缓存
    this.memoryCache.set(key, item);
    await this.persistentCache.put(key, item);
  }
}
```

### 错误处理策略

**重试机制**:
```typescript
class HttpCommandExecutor implements ICommandExecutor {
  async execute(command: string, options?: ExecuteOptions): Promise<CommandResult> {
    const maxRetries = 3;
    let lastError: Error;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await this.attemptExecution(command, options);
      } catch (error) {
        lastError = error;

        if (attempt < maxRetries) {
          const delay = Math.pow(2, attempt) * 1000; // 指数退避
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }

    throw new CommandExecutionError(
      `命令执行失败，已重试${maxRetries}次: ${lastError.message}`,
      'RETRY_EXHAUSTED'
    );
  }
}
```

### 解析器实现

**ReviewOutputParser**:
```typescript
class ReviewOutputParser implements OutputParser {
  parse(output: string): ReviewTask[] {
    try {
      // 尝试解析JSON输出
      const data = JSON.parse(output);
      return this.transformToReviewTasks(data);
    } catch (error) {
      // 降级到文本解析
      return this.parseTextOutput(output);
    }
  }

  private transformToReviewTasks(data: any): ReviewTask[] {
    // 实现JSON到ReviewTask的转换逻辑
    return data.tasks?.map(task => ({
      id: task.id,
      canvasId: task.canvas_id,
      canvasTitle: task.canvas_title,
      conceptName: task.concept_name,
      priority: this.mapPriority(task.priority),
      urgency: task.urgency || 0,
      memoryStrength: task.memory_strength || 0,
      retentionRate: task.retention_rate || 0,
      dueDate: new Date(task.due_date),
      // ... 其他字段映射
    })) || [];
  }
}
```

### 性能优化

**批量命令执行**:
```typescript
class CommandWrapper {
  async executeBatch(commands: BatchCommand[]): Promise<CommandResult[]> {
    const promises = commands.map(cmd =>
      this.execute(cmd.command, cmd.options)
    );

    return Promise.allSettled(promises);
  }
}
```

**并发控制**:
```typescript
class CommandQueue {
  private queue: Array<() => Promise<any>> = [];
  private running = 0;
  private maxConcurrent = 3;

  async add<T>(task: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push(async () => {
        try {
          const result = await task();
          resolve(result);
        } catch (error) {
          reject(error);
        }
      });

      this.process();
    });
  }
}
```

### 测试要求

**单元测试覆盖**:
- 测试HTTP命令执行器的成功和失败场景
- 测试所有解析器的输出转换逻辑
- 测试缓存机制的读写和失效
- 测试重试机制的正确性
- 测试错误处理和异常情况

**集成测试**:
- 端到端测试命令包装器的完整流程
- 测试与真实Claude Code API的通信
- 性能测试确保响应时间符合要求

**Mock测试**:
```typescript
// 创建Mock执行器用于测试
class MockCommandExecutor implements ICommandExecutor {
  private responses: Map<string, any> = new Map();

  setResponse(command: string, response: any): void {
    this.responses.set(command, response);
  }

  async execute(command: string, options?: ExecuteOptions): Promise<CommandResult> {
    const response = this.responses.get(command);
    if (!response) {
      throw new Error(`未找到命令 ${command} 的模拟响应`);
    }

    return response;
  }
}
```

### 安全考虑

**输入验证**:
- 验证命令参数的合法性
- 防止命令注入攻击
- 限制命令执行超时时间

**数据安全**:
- API密钥的安全存储
- 敏感数据的加密传输
- 缓存数据的访问控制

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-01-27 | 1.0 | 初始Story创建 | PM Agent (Sarah) |

## Dev Agent Record

### Agent Model Used
待开发

### Debug Log References
待开发

### Completion Notes
待开发

### File List
**计划创建的文件：**
- `canvas-progress-tracker/obsidian-plugin/src/managers/CommandWrapper.ts` - 命令包装器主类
- `canvas-progress-tracker/obsidian-plugin/src/executors/HttpCommandExecutor.ts` - HTTP执行器
- `canvas-progress-tracker/obsidian-plugin/src/parsers/ReviewOutputParser.ts` - 复习命令解析器
- `canvas-progress-tracker/obsidian-plugin/src/parsers/GenerateReviewOutputParser.ts` - 生成复习计划解析器
- `canvas-progress-tracker/obsidian-plugin/src/cache/CommandCache.ts` - 命令缓存实现
- `canvas-progress-tracker/obsidian-plugin/src/types/ReviewTypes.ts` - 复习相关类型定义
- `canvas-progress-tracker/obsidian-plugin/src/utils/CommandUtils.ts` - 命令工具函数

**修改的文件：**
- `canvas-progress-tracker/obsidian-plugin/main.ts` - 集成CommandWrapper

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

**本Story完成后，用户将能够在Obsidian中通过图形界面无缝使用现有的斜杠命令功能，实现复习管理的现代化体验。**