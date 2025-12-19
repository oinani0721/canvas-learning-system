# Story 12.F.3: FILE 节点内容读取修复

**Story ID**: STORY-12.F.3
**Epic**: Epic 12.F - Agent 功能完整性修复
**优先级**: P0
**状态**: Todo
**预估时间**: 3 小时
**创建日期**: 2025-12-16

---

## 用户故事

**作为** 使用 Canvas 学习系统的用户
**我希望** 能够对 FILE 类型节点 (嵌入的 .md 文件) 使用 Agent 功能
**以便** 获得与文件内容相关的解释和分析

---

## 问题背景

### 当前问题

FILE 类型节点的内容读取失败，控制台显示:

```
[Story 12.D.3] Node content trace:
  - node_id: original-lecture
  - node_type: unknown        ← 类型识别失败
  - content_source: empty     ← 内容为空
  - content_length: 0 chars   ← 没有读取到内容
```

### 问题影响

- FILE 节点 (嵌入 .md 文件) 无法使用任何 Agent 功能
- `original-lecture` 等关键节点完全不可用

---

## 验收标准

- [ ] FILE 类型节点正确识别 (`node_type: file`)
- [ ] 文件内容成功读取 (`content_length > 0`)
- [ ] 支持 `.md` 文件读取
- [ ] 支持相对路径和绝对路径
- [ ] 错误时有清晰的日志输出
- [ ] 日志追踪链完整

---

## 技术方案

### 修改文件

- `canvas-progress-tracker/obsidian-plugin/src/managers/ContextMenuManager.ts`

### 问题分析

Canvas 节点有两种主要类型:
1. **text**: 直接包含文本内容
2. **file**: 引用外部文件 (通过 `node.file` 属性)

当前代码可能的问题:
1. `node.type` 判断逻辑错误
2. 文件路径处理不正确
3. `vault.read()` 调用失败

### 实现代码

```typescript
/**
 * 获取节点内容
 * 支持 text 和 file 两种类型
 */
private async getNodeContent(node: CanvasNode): Promise<string> {
    const nodeId = node.id || 'unknown';

    // 日志追踪: 开始
    console.log(`[Story 12.F.3] getNodeContent start:`, {
        nodeId,
        nodeType: node.type,
        hasText: !!node.text,
        hasFile: !!node.file,
    });

    // 处理 TEXT 类型节点
    if (node.type === 'text') {
        const content = node.text || '';
        console.log(`[Story 12.F.3] TEXT node content:`, {
            nodeId,
            contentLength: content.length,
        });
        return content;
    }

    // 处理 FILE 类型节点
    if (node.type === 'file' || node.file) {
        const filePath = node.file;

        if (!filePath) {
            console.warn(`[Story 12.F.3] FILE node missing file path:`, { nodeId });
            return '';
        }

        console.log(`[Story 12.F.3] FILE node detected:`, {
            nodeId,
            filePath,
        });

        try {
            // 尝试获取文件
            const abstractFile = this.app.vault.getAbstractFileByPath(filePath);

            if (!abstractFile) {
                // 尝试添加 .md 扩展名
                const mdPath = filePath.endsWith('.md') ? filePath : `${filePath}.md`;
                const mdFile = this.app.vault.getAbstractFileByPath(mdPath);

                if (!mdFile) {
                    console.warn(`[Story 12.F.3] File not found:`, {
                        nodeId,
                        triedPaths: [filePath, mdPath],
                    });
                    return '';
                }

                abstractFile = mdFile;
            }

            // 检查是否为文件 (而非文件夹)
            if (!(abstractFile instanceof TFile)) {
                console.warn(`[Story 12.F.3] Path is not a file:`, {
                    nodeId,
                    filePath,
                    type: abstractFile.constructor.name,
                });
                return '';
            }

            // 读取文件内容
            const content = await this.app.vault.read(abstractFile);

            console.log(`[Story 12.F.3] FILE content loaded successfully:`, {
                nodeId,
                filePath,
                contentLength: content.length,
                preview: content.substring(0, 100),
            });

            return content;

        } catch (error) {
            console.error(`[Story 12.F.3] Failed to read file:`, {
                nodeId,
                filePath,
                error: error.message,
            });
            return '';
        }
    }

    // 未知类型
    console.warn(`[Story 12.F.3] Unknown node type:`, {
        nodeId,
        nodeType: node.type,
        nodeKeys: Object.keys(node),
    });

    return '';
}
```

### 路径处理辅助方法

```typescript
/**
 * 规范化文件路径
 */
private normalizeFilePath(filePath: string): string {
    // 移除开头的斜杠
    if (filePath.startsWith('/')) {
        filePath = filePath.substring(1);
    }

    // 移除 vault 路径前缀 (如果有)
    const vaultPath = this.app.vault.getRoot().path;
    if (filePath.startsWith(vaultPath)) {
        filePath = filePath.substring(vaultPath.length);
    }

    return filePath;
}
```

---

## 测试用例

### 手动测试

1. **TEXT 节点测试**
   - 选择 TEXT 类型节点
   - 右键 → 任意 Agent 功能
   - 预期: 正常工作

2. **FILE 节点测试 (.md)**
   - 选择嵌入的 .md 文件节点
   - 右键 → 任意 Agent 功能
   - 预期: 正确读取文件内容，Agent 正常工作

3. **文件不存在测试**
   - 删除节点引用的文件
   - 右键 → 任意 Agent 功能
   - 预期: 显示友好错误提示

### 日志验证

正确的日志输出应该是:

```
[Story 12.F.3] getNodeContent start: {nodeId: "original-lecture", nodeType: "file", ...}
[Story 12.F.3] FILE node detected: {nodeId: "original-lecture", filePath: "Lecture5.md"}
[Story 12.F.3] FILE content loaded successfully: {nodeId: "original-lecture", contentLength: 5432, ...}
```

而不是:

```
[Story 12.D.3] Node content trace:
  - node_type: unknown
  - content_source: empty
```

---

## 依赖关系

- **前置依赖**: Story 12.F.1 (Topic 提取)
- **被依赖**: Story 12.F.2 依赖本 Story

---

## Definition of Done

- [ ] TEXT 节点内容正确读取
- [ ] FILE 节点内容正确读取
- [ ] 日志追踪链完整清晰
- [ ] 错误处理完善
- [ ] 手动测试通过
- [ ] 代码 Review 通过
