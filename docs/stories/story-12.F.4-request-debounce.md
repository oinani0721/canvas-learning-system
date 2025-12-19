# Story 12.F.4: 请求去重机制

**Story ID**: STORY-12.F.4
**Epic**: Epic 12.F - Agent 功能完整性修复
**优先级**: P1
**状态**: Todo
**预估时间**: 2 小时
**创建日期**: 2025-12-16

---

## 用户故事

**作为** 使用 Canvas 学习系统的用户
**我希望** 点击一次菜单只生成一份文档
**以便** 避免 Canvas 被重复内容污染

---

## 问题背景

### 当前问题

用户点击一次"澄清路径"等菜单项，可能生成多份相同的文档。

### 问题原因

1. 用户快速双击触发多次调用
2. 点击事件冒泡导致重复触发
3. 无防抖 (debounce) 或节流 (throttle) 保护

### 问题影响

- Canvas 被重复内容污染
- 用户需要手动清理重复节点
- 后端资源浪费

---

## 验收标准

- [ ] 快速多次点击只触发一次 API 调用
- [ ] 加载中禁止重复调用
- [ ] 用户能看到"正在处理中"状态
- [ ] 处理完成后可再次调用
- [ ] 所有 Agent 菜单项都有保护

---

## 技术方案

### 修改文件

- `canvas-progress-tracker/obsidian-plugin/main.ts`
- `canvas-progress-tracker/obsidian-plugin/src/managers/ContextMenuManager.ts` (可选)

### 方案 A: 请求锁机制

```typescript
class CanvasReviewPlugin extends Plugin {
    // 请求锁: 记录正在进行的请求
    private pendingRequests: Map<string, boolean> = new Map();

    /**
     * 带去重保护的 Agent 调用包装器
     */
    private async callAgentWithLock<T>(
        lockKey: string,
        fn: () => Promise<T>
    ): Promise<T | null> {
        // 检查是否已有相同请求在进行
        if (this.pendingRequests.get(lockKey)) {
            console.log(`[DEBOUNCE] Request "${lockKey}" already in progress, skipping`);
            new Notice('请求处理中，请稍候...');
            return null;
        }

        try {
            // 设置锁
            this.pendingRequests.set(lockKey, true);
            console.log(`[DEBOUNCE] Request "${lockKey}" started`);

            // 执行实际调用
            const result = await fn();

            return result;
        } finally {
            // 释放锁
            this.pendingRequests.delete(lockKey);
            console.log(`[DEBOUNCE] Request "${lockKey}" completed`);
        }
    }
}
```

### 使用示例

```typescript
generateClarificationPath: async (context: MenuContext) => {
    const lockKey = `clarification-${context.nodeId}`;

    await this.callAgentWithLock(lockKey, async () => {
        // 原有逻辑
        new Notice('正在生成澄清路径...');

        const response = await this.apiClient.callAgent({
            agent_type: 'clarification-path',
            canvas_name: context.canvasName,
            node_id: context.nodeId,
            node_content: context.nodeContent,
        });

        if (response.success) {
            await this.createNewNode(context.canvasPath, response.content, context.nodeId);
            new Notice('澄清路径生成成功');
        }
    });
},
```

### 方案 B: Debounce 装饰器 (替代方案)

```typescript
/**
 * Debounce 装饰器
 * 在指定时间内只执行一次
 */
function debounce(delay: number = 500) {
    const timers: Map<string, NodeJS.Timeout> = new Map();

    return function(
        target: any,
        propertyKey: string,
        descriptor: PropertyDescriptor
    ) {
        const originalMethod = descriptor.value;

        descriptor.value = function(...args: any[]) {
            const key = `${propertyKey}-${JSON.stringify(args[0]?.nodeId || '')}`;

            // 清除之前的定时器
            if (timers.has(key)) {
                clearTimeout(timers.get(key)!);
            }

            // 设置新定时器
            return new Promise((resolve) => {
                const timer = setTimeout(async () => {
                    timers.delete(key);
                    const result = await originalMethod.apply(this, args);
                    resolve(result);
                }, delay);

                timers.set(key, timer);
            });
        };

        return descriptor;
    };
}

// 使用
@debounce(500)
async generateClarificationPath(context: MenuContext) {
    // ...
}
```

### 推荐方案

**方案 A (请求锁机制)** - 原因:
1. 更直观易懂
2. 不需要装饰器语法
3. 可以显示"处理中"提示
4. 处理完成后立即可用

---

## 需要保护的菜单项

| 菜单项 | 锁 Key 格式 |
|--------|------------|
| 澄清路径 | `clarification-${nodeId}` |
| 四层次解释 | `four-level-${nodeId}` |
| 基础拆解 | `basic-decomp-${nodeId}` |
| 深度拆解 | `deep-decomp-${nodeId}` |
| 口语化解释 | `oral-${nodeId}` |
| 例题教学 | `example-${nodeId}` |
| 记忆锚点 | `memory-${nodeId}` |
| 对比表 | `comparison-${nodeId}` |
| 问题拆解 | `question-${nodeId}` |
| 生成检验问题 | `verify-${nodeId}` |
| 评分 | `scoring-${nodeId}` |

---

## 测试用例

### 手动测试

1. **快速双击测试**
   - 快速双击"澄清路径"
   - 预期: 只生成一份文档

2. **处理中再次点击**
   - 点击"澄清路径"
   - 在加载中再次点击
   - 预期: 显示"请求处理中，请稍候..."

3. **处理完成后再次点击**
   - 点击"澄清路径"，等待完成
   - 再次点击
   - 预期: 正常生成第二份文档

### 自动化测试

```typescript
describe('callAgentWithLock', () => {
    it('should prevent duplicate requests', async () => {
        const mockFn = jest.fn().mockResolvedValue('result');

        // 同时发起两个相同请求
        const promise1 = plugin.callAgentWithLock('test-key', mockFn);
        const promise2 = plugin.callAgentWithLock('test-key', mockFn);

        await Promise.all([promise1, promise2]);

        // 应该只执行一次
        expect(mockFn).toHaveBeenCalledTimes(1);
    });

    it('should allow different keys', async () => {
        const mockFn = jest.fn().mockResolvedValue('result');

        await plugin.callAgentWithLock('key-1', mockFn);
        await plugin.callAgentWithLock('key-2', mockFn);

        // 不同 key 应该都执行
        expect(mockFn).toHaveBeenCalledTimes(2);
    });

    it('should release lock after completion', async () => {
        const mockFn = jest.fn().mockResolvedValue('result');

        await plugin.callAgentWithLock('test-key', mockFn);
        await plugin.callAgentWithLock('test-key', mockFn);

        // 串行执行应该都成功
        expect(mockFn).toHaveBeenCalledTimes(2);
    });
});
```

---

## 依赖关系

- **前置依赖**: 无
- **被依赖**: 无 (独立功能)

---

## Definition of Done

- [ ] 请求锁机制实现
- [ ] 所有 Agent 菜单项都有保护
- [ ] 用户可见"处理中"状态
- [ ] 手动测试验证无重复文档
- [ ] 代码 Review 通过
