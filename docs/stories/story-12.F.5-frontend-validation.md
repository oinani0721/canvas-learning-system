# Story 12.F.5: 前端参数校验

**Story ID**: STORY-12.F.5
**Epic**: Epic 12.F - Agent 功能完整性修复
**优先级**: P1
**状态**: Todo
**预估时间**: 2 小时
**创建日期**: 2025-12-16

---

## 用户故事

**作为** 使用 Canvas 学习系统的用户
**我希望** 在参数无效时看到清晰的错误提示
**以便** 知道问题出在哪里并采取正确行动

---

## 问题背景

### 当前问题

前端传递空参数 (如 `canvas_name: ""`) 导致后端抛出 HTTP 500 错误。

**错误示例**:
```
POST /api/v1/agents/clarification-path
Body: { "canvas_name": "", "node_id": "...", ... }
Response: 500 Internal Server Error - CanvasNotFoundException
```

### 问题原因

1. 前端未校验参数有效性
2. 空字符串被当作有效值发送
3. 错误信息不友好 (HTTP 500 + 技术堆栈)

### 问题影响

- 用户看到"服务器错误"而非具体原因
- 无法自助解决问题
- 后端日志充满无意义的错误

---

## 验收标准

- [ ] `canvas_name` 空值时显示"请先打开 Canvas 文件"
- [ ] `node_id` 空值时显示"请选择一个节点"
- [ ] `node_content` 空值时显示"节点内容为空"
- [ ] 所有 Agent API 调用都有参数校验
- [ ] 错误提示用中文且可操作

---

## 技术方案

### 修改文件

- `canvas-progress-tracker/obsidian-plugin/src/api/ApiClient.ts`
- `canvas-progress-tracker/obsidian-plugin/main.ts` (可选)

### 校验规则

| 参数 | 校验规则 | 错误提示 |
|------|----------|----------|
| `canvas_name` | 非空非空白 | "请先打开 Canvas 文件" |
| `node_id` | 非空非空白 | "请选择一个节点" |
| `node_content` | 非空 (可为空白) | "节点内容为空，无法生成解释" |
| `agent_type` | 在有效类型列表中 | "不支持的 Agent 类型" |

### 实现代码

#### ApiClient.ts

```typescript
interface AgentCallParams {
    agent_type: string;
    canvas_name: string;
    node_id: string;
    node_content: string;
    [key: string]: any;
}

interface ValidationError {
    field: string;
    message: string;
}

class ApiClient {
    /**
     * 调用 Agent API
     * 包含参数校验
     */
    async callAgent(params: AgentCallParams): Promise<AgentResponse> {
        // 参数校验
        const validationError = this.validateAgentParams(params);
        if (validationError) {
            return {
                success: false,
                error: validationError.message,
            };
        }

        // 继续原有 API 调用逻辑
        try {
            const response = await this.fetch('/api/v1/agents/' + params.agent_type, {
                method: 'POST',
                body: JSON.stringify(params),
            });

            return await response.json();
        } catch (error) {
            return {
                success: false,
                error: this.formatNetworkError(error),
            };
        }
    }

    /**
     * 校验 Agent 调用参数
     */
    private validateAgentParams(params: AgentCallParams): ValidationError | null {
        // 校验 canvas_name
        if (!params.canvas_name || params.canvas_name.trim() === '') {
            return {
                field: 'canvas_name',
                message: '请先打开 Canvas 文件',
            };
        }

        // 校验 node_id
        if (!params.node_id || params.node_id.trim() === '') {
            return {
                field: 'node_id',
                message: '请选择一个节点',
            };
        }

        // 校验 node_content (允许空白，但不允许 undefined/null)
        if (params.node_content === undefined || params.node_content === null) {
            return {
                field: 'node_content',
                message: '节点内容为空，无法生成解释',
            };
        }

        // 校验 agent_type
        const validAgentTypes = [
            'clarification-path',
            'four-level-explanation',
            'basic-decomposition',
            'deep-decomposition',
            'oral-explanation',
            'example-teaching',
            'memory-anchor',
            'comparison-table',
            'question-decomposition',
            'verification-question',
            'scoring',
        ];

        if (!validAgentTypes.includes(params.agent_type)) {
            return {
                field: 'agent_type',
                message: `不支持的 Agent 类型: ${params.agent_type}`,
            };
        }

        return null;
    }

    /**
     * 格式化网络错误为用户友好消息
     */
    private formatNetworkError(error: any): string {
        if (error.name === 'AbortError') {
            return '请求超时，请稍后重试';
        }
        if (error.message?.includes('Failed to fetch')) {
            return '无法连接后端服务，请检查服务是否启动';
        }
        return `网络错误: ${error.message || '未知错误'}`;
    }
}
```

#### main.ts 调用示例

```typescript
generateClarificationPath: async (context: MenuContext) => {
    const response = await this.apiClient.callAgent({
        agent_type: 'clarification-path',
        canvas_name: context.canvasName || '',  // 可能为空
        node_id: context.nodeId || '',          // 可能为空
        node_content: context.nodeContent || '',
    });

    if (!response.success) {
        // 显示校验错误
        new Notice(response.error);
        return;
    }

    // 处理成功响应
    await this.createNewNode(...);
},
```

---

## 测试用例

### 手动测试

1. **空 canvas_name 测试**
   - 不打开任何 Canvas
   - 尝试调用 Agent
   - 预期: 显示"请先打开 Canvas 文件"

2. **空 node_id 测试**
   - 打开 Canvas 但不选择节点
   - 尝试调用 Agent
   - 预期: 显示"请选择一个节点"

3. **正常参数测试**
   - 打开 Canvas 并选择节点
   - 调用 Agent
   - 预期: 正常工作

### 自动化测试

```typescript
describe('validateAgentParams', () => {
    it('should reject empty canvas_name', () => {
        const error = apiClient.validateAgentParams({
            agent_type: 'clarification-path',
            canvas_name: '',
            node_id: 'node-1',
            node_content: 'content',
        });

        expect(error).toEqual({
            field: 'canvas_name',
            message: '请先打开 Canvas 文件',
        });
    });

    it('should reject whitespace-only canvas_name', () => {
        const error = apiClient.validateAgentParams({
            agent_type: 'clarification-path',
            canvas_name: '   ',
            node_id: 'node-1',
            node_content: 'content',
        });

        expect(error?.field).toBe('canvas_name');
    });

    it('should reject empty node_id', () => {
        const error = apiClient.validateAgentParams({
            agent_type: 'clarification-path',
            canvas_name: 'test',
            node_id: '',
            node_content: 'content',
        });

        expect(error?.message).toBe('请选择一个节点');
    });

    it('should reject invalid agent_type', () => {
        const error = apiClient.validateAgentParams({
            agent_type: 'invalid-type',
            canvas_name: 'test',
            node_id: 'node-1',
            node_content: 'content',
        });

        expect(error?.message).toContain('不支持的 Agent 类型');
    });

    it('should pass valid params', () => {
        const error = apiClient.validateAgentParams({
            agent_type: 'clarification-path',
            canvas_name: 'test',
            node_id: 'node-1',
            node_content: 'content',
        });

        expect(error).toBeNull();
    });
});
```

---

## 依赖关系

- **前置依赖**: 无
- **被依赖**: 无 (独立功能)

---

## Definition of Done

- [ ] 参数校验逻辑实现
- [ ] 所有 Agent 调用都经过校验
- [ ] 错误提示中文且可操作
- [ ] 单元测试通过
- [ ] 手动测试通过
- [ ] 代码 Review 通过
