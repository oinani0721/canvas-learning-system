# Story 12.F.2: 实现对比表功能

**Story ID**: STORY-12.F.2
**Epic**: Epic 12.F - Agent 功能完整性修复
**优先级**: P0
**状态**: Todo
**预估时间**: 4 小时
**创建日期**: 2025-12-16

---

## 用户故事

**作为** 使用 Canvas 学习系统的用户
**我希望** 能够通过右键菜单生成对比表
**以便** 快速对比相似概念的异同

---

## 问题背景

### 当前问题

对比表菜单项存在，但只是一个占位符。

**代码位置**: `canvas-progress-tracker/obsidian-plugin/main.ts:382-383`

```typescript
generateComparisonTable: async (context: MenuContext) => {
    new Notice('对比表功能开发中...');  // ← 只是占位符！
},
```

### 问题影响

- 用户点击"生成对比表"菜单后无任何效果
- 功能可用性: 0%

---

## 验收标准

- [ ] 点击"生成对比表"菜单调用后端 API
- [ ] 正确传递 `canvas_name`, `node_id`, `node_content` 参数
- [ ] API 响应后创建新节点显示对比表
- [ ] 加载中显示进度提示
- [ ] 错误时显示友好提示
- [ ] 与其他 Agent 调用行为一致

---

## 技术方案

### 修改文件

- `canvas-progress-tracker/obsidian-plugin/main.ts`

### 后端端点验证

先验证后端端点是否存在:

```
GET /api/v1/agents/types
→ 确认包含 "comparison-table" 类型
```

### 实现代码

```typescript
generateComparisonTable: async (context: MenuContext) => {
    const { nodeId, nodeContent, canvasPath } = context;

    // 参数校验
    if (!nodeContent || nodeContent.trim() === '') {
        new Notice('无法获取节点内容');
        return;
    }

    if (!canvasPath || canvasPath.trim() === '') {
        new Notice('无法获取 Canvas 路径');
        return;
    }

    try {
        // 显示加载提示
        new Notice('正在生成对比表... (预计30秒)');

        // 调用后端 API
        const response = await this.apiClient.callAgent({
            agent_type: 'comparison-table',
            canvas_name: this.extractCanvasName(canvasPath),
            node_id: nodeId,
            node_content: nodeContent,
        });

        if (response.success && response.content) {
            // 创建新节点
            await this.createNewNode(canvasPath, response.content, nodeId, {
                color: '3',  // 绿色 - 对比表
                offset: { x: 400, y: 0 },
            });
            new Notice('对比表生成成功');
        } else {
            new Notice('对比表生成失败: ' + (response.error || '未知错误'));
        }
    } catch (error) {
        console.error('[ERROR] generateComparisonTable:', error);
        new Notice('对比表生成出错: ' + (error.message || '网络错误'));
    }
},

// 辅助方法: 从路径提取 Canvas 名称
private extractCanvasName(canvasPath: string): string {
    const parts = canvasPath.split('/');
    const filename = parts[parts.length - 1];
    return filename.replace('.canvas', '');
}
```

### API 请求格式

```typescript
interface AgentCallParams {
    agent_type: 'comparison-table';
    canvas_name: string;
    node_id: string;
    node_content: string;
}
```

### API 响应格式

```typescript
interface AgentResponse {
    success: boolean;
    content?: string;
    error?: string;
}
```

---

## 测试用例

### 手动测试

1. **正常流程测试**
   - 选择包含多个概念的节点
   - 右键 → 生成对比表
   - 预期: 显示加载提示 → 生成新节点

2. **空内容测试**
   - 选择空节点
   - 右键 → 生成对比表
   - 预期: 显示"无法获取节点内容"

3. **网络错误测试**
   - 断开后端连接
   - 右键 → 生成对比表
   - 预期: 显示"网络错误"提示

4. **超时测试**
   - 选择大型节点
   - 等待超过 60 秒
   - 预期: 显示超时错误提示

### 自动化测试

```typescript
describe('generateComparisonTable', () => {
    it('should call API with correct parameters', async () => {
        const mockApiClient = {
            callAgent: jest.fn().mockResolvedValue({
                success: true,
                content: '| 概念A | 概念B |\n|---|---|'
            })
        };

        await generateComparisonTable({
            nodeId: 'node-1',
            nodeContent: '概念A vs 概念B',
            canvasPath: 'test.canvas'
        });

        expect(mockApiClient.callAgent).toHaveBeenCalledWith({
            agent_type: 'comparison-table',
            canvas_name: 'test',
            node_id: 'node-1',
            node_content: '概念A vs 概念B'
        });
    });

    it('should show error for empty content', async () => {
        const noticeSpy = jest.spyOn(Notice.prototype, 'constructor');

        await generateComparisonTable({
            nodeId: 'node-1',
            nodeContent: '',
            canvasPath: 'test.canvas'
        });

        expect(noticeSpy).toHaveBeenCalledWith('无法获取节点内容');
    });
});
```

---

## 依赖关系

- **前置依赖**: Story 12.F.1 (Topic 提取)
- **被依赖**: 无

---

## Definition of Done

- [ ] 占位符代码被完整实现替换
- [ ] API 调用正常工作
- [ ] 新节点正确创建
- [ ] 加载/错误提示完善
- [ ] 手动测试通过
- [ ] 代码 Review 通过
