# Story 12.F.6: 超时优化与重试

**Story ID**: STORY-12.F.6
**Epic**: Epic 12.F - Agent 功能完整性修复
**优先级**: P2
**状态**: Todo
**预估时间**: 3 小时
**创建日期**: 2025-12-16

---

## 用户故事

**作为** 使用 Canvas 学习系统的用户
**我希望** Agent 调用不会因为网络波动而失败
**以便** 获得更稳定的使用体验

---

## 问题背景

### 当前问题

Agent API 调用耗时较长 (3.7-19 秒)，经常触发 HTTP 408 超时错误。

**调用链分析**:
```
前端请求
    ↓ (网络延迟 ~100ms)
后端接收
    ↓ (RAG 查询 ~1-3s)
上下文富化
    ↓ (2-hop 遍历 ~1-2s)
Gemini API 调用
    ↓ (生成响应 ~2-15s)
返回前端
```

**总耗时**: 4-20 秒

### 问题影响

- HTTP 408 Request Timeout 错误频繁
- 用户不知道请求是否在处理中
- 网络波动导致请求失败

---

## 验收标准

- [ ] 前端 timeout 从 30s 增加到 60s
- [ ] 显示进度提示 ("正在分析... 预计30秒")
- [ ] 超时后显示友好提示
- [ ] 可选: 实现自动重试 (最多 1 次)
- [ ] 可选: 后端 streaming 响应 (进阶)

---

## 技术方案

### 修改文件

- `canvas-progress-tracker/obsidian-plugin/src/api/ApiClient.ts`
- `canvas-progress-tracker/obsidian-plugin/main.ts`
- `backend/app/api/v1/endpoints/agents.py` (可选)

### 方案 1: 延长超时 + 进度提示 (推荐)

#### ApiClient.ts

```typescript
class ApiClient {
    // 默认超时时间
    private readonly DEFAULT_TIMEOUT = 60000; // 60 秒

    // Agent 类型对应的预估时间
    private readonly ESTIMATED_TIME: Record<string, number> = {
        'clarification-path': 30,
        'four-level-explanation': 45,
        'basic-decomposition': 20,
        'deep-decomposition': 40,
        'oral-explanation': 25,
        'example-teaching': 35,
        'memory-anchor': 20,
        'comparison-table': 30,
        'question-decomposition': 25,
        'verification-question': 30,
        'scoring': 15,
    };

    /**
     * 调用 Agent API (带超时控制)
     */
    async callAgent(params: AgentCallParams): Promise<AgentResponse> {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.DEFAULT_TIMEOUT);

        try {
            const response = await fetch(this.buildUrl('/api/v1/agents/' + params.agent_type), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(params),
                signal: controller.signal,
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                return {
                    success: false,
                    error: `服务器错误: ${response.status}`,
                };
            }

            return await response.json();

        } catch (error) {
            clearTimeout(timeoutId);

            if (error.name === 'AbortError') {
                return {
                    success: false,
                    error: '请求超时 (60秒)，请稍后重试',
                };
            }

            return {
                success: false,
                error: `网络错误: ${error.message}`,
            };
        }
    }

    /**
     * 获取预估处理时间
     */
    getEstimatedTime(agentType: string): number {
        return this.ESTIMATED_TIME[agentType] || 30;
    }
}
```

#### main.ts 调用示例

```typescript
generateClarificationPath: async (context: MenuContext) => {
    const agentType = 'clarification-path';
    const estimatedTime = this.apiClient.getEstimatedTime(agentType);

    // 显示带预估时间的提示
    new Notice(`正在生成澄清路径... (预计 ${estimatedTime} 秒)`);

    const response = await this.apiClient.callAgent({
        agent_type: agentType,
        canvas_name: context.canvasName,
        node_id: context.nodeId,
        node_content: context.nodeContent,
    });

    if (!response.success) {
        new Notice(`生成失败: ${response.error}`);
        return;
    }

    // 处理成功响应
    await this.createNewNode(...);
    new Notice('澄清路径生成成功');
},
```

### 方案 2: 自动重试 (可选)

```typescript
/**
 * 带重试的 API 调用
 */
async callAgentWithRetry(
    params: AgentCallParams,
    maxRetries: number = 1
): Promise<AgentResponse> {
    let lastError: string = '';

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        const response = await this.callAgent(params);

        if (response.success) {
            return response;
        }

        lastError = response.error;

        // 只对超时和网络错误重试
        if (
            !response.error.includes('超时') &&
            !response.error.includes('网络')
        ) {
            return response;
        }

        // 重试前等待
        if (attempt < maxRetries) {
            console.log(`[RETRY] Attempt ${attempt + 1} failed, retrying...`);
            await this.delay(2000); // 等待 2 秒
        }
    }

    return {
        success: false,
        error: `${lastError} (已重试 ${maxRetries} 次)`,
    };
}

private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
}
```

### 方案 3: 后端 Streaming (进阶，可选)

#### agents.py

```python
from fastapi.responses import StreamingResponse

@router.post("/{agent_type}/stream")
async def call_agent_stream(
    agent_type: AgentType,
    request: AgentRequest,
):
    """
    Streaming 版本的 Agent 调用
    返回 SSE (Server-Sent Events) 流
    """
    async def generate():
        yield f"data: {json.dumps({'status': 'started'})}\n\n"

        # RAG 查询
        yield f"data: {json.dumps({'status': 'rag_query'})}\n\n"
        context = await agent_service.get_rag_context(request)

        # 上下文富化
        yield f"data: {json.dumps({'status': 'enriching'})}\n\n"
        enriched = await agent_service.enrich_context(context)

        # AI 生成
        yield f"data: {json.dumps({'status': 'generating'})}\n\n"
        result = await agent_service.generate(enriched)

        # 完成
        yield f"data: {json.dumps({'status': 'done', 'content': result})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

**注意**: Streaming 方案复杂度较高，建议作为后续优化。

---

## 测试用例

### 手动测试

1. **正常超时测试**
   - 选择大型节点
   - 调用 Agent
   - 等待 60 秒以上
   - 预期: 显示"请求超时 (60秒)，请稍后重试"

2. **进度提示测试**
   - 调用任意 Agent
   - 预期: 显示"正在生成... (预计 X 秒)"

3. **网络断开测试**
   - 断开网络
   - 调用 Agent
   - 预期: 显示"网络错误"提示

### 性能测试

```typescript
describe('timeout configuration', () => {
    it('should use 60s timeout', () => {
        expect(apiClient.DEFAULT_TIMEOUT).toBe(60000);
    });

    it('should provide estimated times for all agent types', () => {
        const agentTypes = [
            'clarification-path',
            'four-level-explanation',
            // ... 所有类型
        ];

        agentTypes.forEach(type => {
            const time = apiClient.getEstimatedTime(type);
            expect(time).toBeGreaterThan(0);
            expect(time).toBeLessThan(120);
        });
    });
});
```

---

## 依赖关系

- **前置依赖**: Story 12.F.5 (参数校验)
- **被依赖**: 无 (最后实施)

---

## Definition of Done

- [ ] 超时时间调整为 60 秒
- [ ] 所有 Agent 调用显示预估时间
- [ ] 超时错误提示友好
- [ ] 可选: 重试机制实现
- [ ] 手动测试通过
- [ ] 代码 Review 通过
