# Epic 12.F: Agent 功能完整性修复

**Epic ID**: EPIC-12.F
**Epic类型**: Bug修复 + 功能实现 (Brownfield Enhancement)
**状态**: Ready for Development
**优先级**: P0 Critical
**创建日期**: 2025-12-16
**更新日期**: 2025-12-16
**预计完成**: 2025-12-20 (4 个工作日)

---

## 目录

1. [Epic概述](#epic概述)
2. [问题诊断报告](#问题诊断报告)
3. [Story概览](#story概览)
4. [技术方案](#技术方案)
5. [验收标准](#验收标准)
6. [风险与缓解](#风险与缓解)
7. [依赖关系](#依赖关系)

---

## Epic概述

### 简述

**修复 Agent 系统的 6 个核心功能问题**，确保右键菜单所有选项正常工作：

1. **Topic 提取机制缺陷**: `_extract_topic_from_content()` 只取第一行，导致 AI 收到元数据
2. **对比表功能未实现**: 菜单项存在但只是占位符
3. **FILE 节点内容读取失败**: `content_source: empty`
4. **无请求去重机制**: 一次点击生成多份文档
5. **空参数导致 HTTP 500**: `canvas_name` 为空字符串
6. **调用链超时**: API 响应 3.7-19 秒导致 HTTP 408

### 问题陈述

**核心问题**: Epic 12.E 只有文档，**代码从未实现**。Git 提交 `eca1746a` 仅包含文档和测试框架，核心业务逻辑未修改。

| 项目 | 状态 |
|------|------|
| Epic 12.E 文档 | 存在 |
| Epic 12.E 代码 | **未实现** |
| 6 个 Story 状态 | 全部 "Ready for Development" |

**症状表现**:
- 错误日志显示 HTTP 500, HTTP 408
- 控制台显示 `node_type: unknown`, `content_source: empty`
- 对比表菜单点击无效果
- 一次点击生成多份重复文档

### 解决方案

完整实现 6 个修复 Story：
1. **Story 12.F.1**: Topic 智能提取 (实现 Epic 12.E 核心逻辑)
2. **Story 12.F.2**: 对比表功能实现
3. **Story 12.F.3**: FILE 节点内容读取修复
4. **Story 12.F.4**: 请求去重机制
5. **Story 12.F.5**: 前端参数校验
6. **Story 12.F.6**: 超时优化与重试

### 预期影响

**功能修复**:
- 右键菜单 100% 功能可用
- 主题正确率: 0% → 95%+
- HTTP 错误率: 大幅降低
- 用户体验: 显著改善

---

## 问题诊断报告

### 诊断方法

1. **错误日志分析**: Obsidian Developer Console 日志
2. **代码追踪**: 3 个并行 Explore Agent 深度调研
3. **Epic 历史审查**: 验证 Epic 12.E 实际实现状态

### 6 个根本问题详解

#### 问题 1: Topic 提取只取第一行 [P0]

**代码位置**: `backend/app/services/agent_service.py:1089-1127`

```python
def _extract_topic_from_content(self, content: str, max_length: int = 50) -> str:
    # BUG: 只取第一行！
    first_line = content.strip().split('\n')[0].strip()
    return first_line if first_line else "Unknown"
```

**问题**: 当节点内容第一行是元数据 (如 `🧭 知识图谱控制中心...`)，AI 收到的 `topic` 是错误的。

**影响**: AI 生成内容与选择节点完全无关

---

#### 问题 2: 对比表功能未实现 [P0]

**代码位置**: `canvas-progress-tracker/obsidian-plugin/main.ts:382-383`

```typescript
generateComparisonTable: async (context: MenuContext) => {
    new Notice('对比表功能开发中...');  // ← 只是占位符！
},
```

**问题**: 菜单项存在但点击后无任何实际功能

**影响**: 对比表功能 100% 不可用

---

#### 问题 3: FILE 节点内容读取失败 [P0]

**证据**: 控制台日志

```
[Story 12.D.3] Node content trace:
  - node_id: original-lecture
  - node_type: unknown        ← 类型识别失败
  - content_source: empty     ← 内容为空
  - content_length: 0 chars   ← 没有读取到内容
```

**代码位置**: `canvas-progress-tracker/obsidian-plugin/src/managers/ContextMenuManager.ts`

**问题**: `this.app.vault.read(file)` 返回空值

---

#### 问题 4: 无请求去重机制 [P1]

**症状**: 用户点击一次菜单，生成多份相同文档

**原因**: 前端 click handler 无 debounce/throttle 保护

**影响**: Canvas 被重复内容污染

---

#### 问题 5: canvas_name 空值导致 HTTP 500 [P1]

**错误**: `CanvasNotFoundException`

**原因**: 前端传递空字符串 `""` 作为 `canvas_name`

**影响**: API 调用失败

---

#### 问题 6: 调用链超时 [P2]

**数据**: API 响应时间 3.7-19 秒

**调用链**:
```
RAG Query (1-3s) → Context Enrichment (1-2s) → Gemini API (2-15s) = 累计超时
```

**影响**: HTTP 408 Request Timeout

---

## Story概览

| Story ID | 标题 | 优先级 | 预估时间 | 状态 |
|----------|------|--------|----------|------|
| 12.F.1 | Topic 智能提取 | P0 BLOCKER | 4h | Todo |
| 12.F.2 | 实现对比表功能 | P0 | 4h | Todo |
| 12.F.3 | FILE 节点内容读取修复 | P0 | 3h | Todo |
| 12.F.4 | 请求去重机制 | P1 | 2h | Todo |
| 12.F.5 | 前端参数校验 | P1 | 2h | Todo |
| 12.F.6 | 超时优化 | P2 | 3h | Todo |

**总预估**: 18 小时 (约 2-3 个工作日)

---

## 技术方案

### Story 12.F.1: Topic 智能提取

**修改文件**: `backend/app/services/agent_service.py`

**实现方案**:

```python
def _extract_topic_from_content(self, content: str, max_length: int = 50) -> str:
    """
    智能提取 topic，跳过元数据行
    """
    if not content or not content.strip():
        return "Unknown"

    lines = content.strip().split('\n')

    for line in lines:
        line = line.strip()

        # 跳过空行
        if not line:
            continue

        # 跳过元数据行 (emoji 开头、特殊标记等)
        if self._is_metadata_line(line):
            continue

        # 跳过 markdown 标题标记
        if line.startswith('#'):
            line = line.lstrip('#').strip()

        # 找到有效 topic
        if line:
            return line[:max_length] if len(line) > max_length else line

    return "Unknown"

def _is_metadata_line(self, line: str) -> bool:
    """判断是否为元数据行"""
    metadata_patterns = [
        '🧭', '📊', '📋', '🔗',  # 导航 emoji
        '**[', '---', '<!--',    # markdown 元素
        'canvas:', 'note:',      # 元数据前缀
    ]
    return any(line.startswith(p) for p in metadata_patterns)
```

---

### Story 12.F.2: 实现对比表功能

**修改文件**: `canvas-progress-tracker/obsidian-plugin/main.ts`

**实现方案**:

```typescript
generateComparisonTable: async (context: MenuContext) => {
    const { nodeId, nodeContent, canvasPath } = context;

    if (!nodeContent || !canvasPath) {
        new Notice('无法获取节点内容或 Canvas 路径');
        return;
    }

    try {
        new Notice('正在生成对比表...');

        const response = await this.apiClient.callAgent({
            agent_type: 'comparison-table',
            canvas_name: canvasPath,
            node_id: nodeId,
            node_content: nodeContent,
        });

        if (response.success && response.content) {
            await this.createNewNode(canvasPath, response.content, nodeId);
            new Notice('对比表生成成功');
        } else {
            new Notice('对比表生成失败: ' + (response.error || '未知错误'));
        }
    } catch (error) {
        new Notice('对比表生成出错: ' + error.message);
    }
},
```

---

### Story 12.F.3: FILE 节点内容读取修复

**修改文件**: `canvas-progress-tracker/obsidian-plugin/src/managers/ContextMenuManager.ts`

**实现方案**:

```typescript
private async getNodeContent(node: any): Promise<string> {
    if (node.type === 'text') {
        return node.text || '';
    }

    if (node.type === 'file') {
        try {
            const filePath = node.file;
            const file = this.app.vault.getAbstractFileByPath(filePath);

            if (file instanceof TFile) {
                const content = await this.app.vault.read(file);
                console.log(`[DEBUG] FILE node content loaded: ${content.length} chars`);
                return content;
            } else {
                console.warn(`[WARN] File not found: ${filePath}`);
                return '';
            }
        } catch (error) {
            console.error(`[ERROR] Failed to read file: ${error.message}`);
            return '';
        }
    }

    console.warn(`[WARN] Unknown node type: ${node.type}`);
    return '';
}
```

---

### Story 12.F.4: 请求去重机制

**修改文件**: `canvas-progress-tracker/obsidian-plugin/main.ts`

**实现方案**:

```typescript
// 在类顶部添加
private pendingRequests: Set<string> = new Set();

// 包装所有 Agent 调用
private async callAgentWithDebounce(
    key: string,
    fn: () => Promise<void>
): Promise<void> {
    if (this.pendingRequests.has(key)) {
        console.log(`[DEBOUNCE] Request ${key} already in progress`);
        return;
    }

    try {
        this.pendingRequests.add(key);
        await fn();
    } finally {
        this.pendingRequests.delete(key);
    }
}

// 使用示例
generateClarificationPath: async (context: MenuContext) => {
    const key = `clarification-${context.nodeId}`;
    await this.callAgentWithDebounce(key, async () => {
        // 原有逻辑
    });
},
```

---

### Story 12.F.5: 前端参数校验

**修改文件**: `canvas-progress-tracker/obsidian-plugin/src/api/ApiClient.ts`

**实现方案**:

```typescript
async callAgent(params: AgentCallParams): Promise<AgentResponse> {
    // 参数校验
    if (!params.canvas_name || params.canvas_name.trim() === '') {
        throw new Error('canvas_name 不能为空');
    }

    if (!params.node_id || params.node_id.trim() === '') {
        throw new Error('node_id 不能为空');
    }

    // 继续原有逻辑...
}
```

---

### Story 12.F.6: 超时优化

**修改文件**: 多个

**实现方案**:

1. 增加前端 timeout: `30s → 60s`
2. 添加进度提示: `正在分析... (预计30秒)`
3. 后端添加 streaming 响应 (可选)

---

## 验收标准

| Story | 验收标准 |
|-------|----------|
| 12.F.1 | Topic 提取跳过元数据行，正确返回概念名 |
| 12.F.2 | 对比表菜单点击后调用 API 并创建新节点 |
| 12.F.3 | FILE 节点内容正确读取，日志显示 content_length > 0 |
| 12.F.4 | 重复点击不生成多份文档 |
| 12.F.5 | 空参数时显示用户友好错误提示 |
| 12.F.6 | API 超时时间延长，有进度提示 |

### 整体验收标准

- [ ] 所有右键菜单选项可正常工作
- [ ] HTTP 500/408 错误率 < 5%
- [ ] 无重复文档生成
- [ ] 单元测试覆盖率 > 80%

---

## 风险与缓解

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| Topic 提取逻辑过于激进 | 中 | 中 | 添加配置项，允许用户选择策略 |
| 对比表 API 端点不存在 | 低 | 高 | 先验证后端端点存在 |
| FILE 节点路径处理差异 | 中 | 中 | 添加多种路径格式支持 |

---

## 依赖关系

### 依赖图

```
┌─────────────────────────────────────────┐
│           Epic 12.F                      │
├─────────────────────────────────────────┤
│                                         │
│  12.F.1 (Topic) ◄─────────────────────┐ │
│       │                               │ │
│       ▼                               │ │
│  12.F.3 (FILE) ◄──── 12.F.5 (校验)    │ │
│       │                               │ │
│       ▼                               │ │
│  12.F.2 (对比表)                       │ │
│       │                               │ │
│       ▼                               │ │
│  12.F.4 (去重) ──────────────────────►│ │
│       │                               │ │
│       ▼                               │ │
│  12.F.6 (超时)                         │ │
│                                         │
└─────────────────────────────────────────┘
```

### 实施顺序

1. **Story 12.F.1** → Topic 提取 (根本问题，必须先修)
2. **Story 12.F.3** → FILE 节点 (阻塞其他功能)
3. **Story 12.F.2** → 对比表 (核心功能)
4. **Story 12.F.5** → 参数校验 (防御性)
5. **Story 12.F.4** → 去重机制 (体验优化)
6. **Story 12.F.6** → 超时优化 (性能优化)

---

## Definition of Done

- [ ] 6 个 Story 全部完成
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 代码 Review 通过
- [ ] 文档更新
- [ ] Git 提交包含实际代码修改 (非仅文档)

---

## Epic 签名

| 角色 | 姓名 | 日期 | 状态 |
|------|------|------|------|
| PM | John (PM Agent) | 2025-12-16 | 已创建 |
| Tech Lead | - | - | 待审批 |
| QA | - | - | 待审批 |

---

**注意**: 本 Epic 是对 Epic 12.E 的**实际代码实现**，Epic 12.E 仅包含文档和测试框架，核心业务逻辑未实现。

## Relations

