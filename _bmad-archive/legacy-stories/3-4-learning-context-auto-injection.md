# Story 3.4: 学习上下文自动注入

Status: ready-for-dev

## Story

As a 用户,
I want Agent 对话时自动知道我在这个节点写过的 Tips、犯过的错、连线的理由,
so that Agent 的回答基于我的学习历史，而不是从零开始。

## Acceptance Criteria

1. **AC-1: --append-system-prompt 动态注入**
   - **Given** 用户打开一个有学习历史的节点对话
   - **When** ClaudeCodeEngine spawn 子进程
   - **Then** 通过 `--append-system-prompt` 参数注入该节点的学习上下文
   - **And** 上下文包含：该节点的 Tips、历史错误记录、相关 Edge 理由
   - **And** 上下文格式为结构化 Markdown（Agent 可理解的格式）

2. **AC-2: 三层上下文管理（Tier 1/2/3）**
   - **Given** 节点 A 有学习历史，且与节点 B、C 有连线
   - **When** 组装上下文
   - **Then** Tier 1：当前节点 A 的全量上下文（所有 Tips + 所有错误 + 精通度）
   - **And** Tier 2：相邻节点 B、C 的摘要上下文（概要 + 关系理由）
   - **And** Tier 3：远端节点的上下文不预加载（通过 MCP search_memories 按需检索）
   - **And** 总上下文长度控制在合理范围（Tier 1 + Tier 2 < 4K tokens）

3. **AC-3: 双向链接引用**
   - **Given** Agent 在回复中引用用户的笔记
   - **When** 引用内容来自 Obsidian vault 中的文件
   - **Then** 附带可点击 Obsidian 双向链接 `[[文件名#章节标题]]`
   - **And** 前端通过 `MarkdownRenderer.render()` + 事件 hook 实现点击跳转
   - **And** 链接精度到章节级（非仅文件级）

4. **AC-4: 上下文动态更新**
   - **Given** 用户在对话过程中标记了新 Tips 或产生了新错误
   - **When** 下一轮对话发送消息
   - **Then** 上下文自动包含最新的 Tips/错误数据
   - **And** 不需要用户关闭重开对话

## Tasks / Subtasks

- [ ] **Task 1: 上下文组装器** (AC: #1, #2)
  - [ ] 1.1 创建 `obsidian-canvas-learning/src/services/context-assembler.ts`
  - [ ] 1.2 实现 `assembleTier1(nodeId)`: 从后端 API / Graphiti 获取当前节点全量数据
    - Tips 列表（标题 + 内容 + 来源对话时间）
    - 错误记录（4 类分类 + 错误描述 + 补救建议）
    - 精通度状态（BKT p_mastery + FSRS 稳定性 + 下次复习时间）
  - [ ] 1.3 实现 `assembleTier2(nodeId)`: 获取相邻节点摘要
    - 通过 Neo4j 查询 1-hop 邻居节点
    - 每个邻居：节点标题 + 精通度 + Edge 理由
  - [ ] 1.4 实现 `assembleContext(nodeId): string`: 合并 Tier 1 + Tier 2 为结构化 Markdown
  - [ ] 1.5 Token 控制：Tier 1 + Tier 2 总量 < 4K tokens（超出时优先截断 Tier 2）

- [ ] **Task 2: 上下文 Markdown 模板** (AC: #1)
  - [ ] 2.1 设计上下文注入模板格式：
    ```markdown
    ## 当前节点：{nodeName}
    ### 精通度
    - BKT掌握概率: {p_mastery}
    - FSRS记忆稳定性: {stability}
    - 下次复习: {nextReview}
    ### 关键笔记 (Tips)
    - {tip1}
    - {tip2}
    ### 历史错误
    - [{errorType}] {description} → 建议: {remedy}
    ### 相关节点
    - {neighborName}: {edgeReason} (精通度: {level})
    ```
  - [ ] 2.2 模板支持空数据优雅处理（新节点无历史时不注入空 section）

- [ ] **Task 3: ClaudeCodeEngine 上下文集成** (AC: #1, #4)
  - [ ] 3.1 扩展 `claude-code-engine.ts`（Story 3.1）的 `sendMessage` 方法
  - [ ] 3.2 每次 sendMessage 前调用 `assembleContext(nodeId)` 获取最新上下文
  - [ ] 3.3 将上下文通过 `--append-system-prompt` 传入 spawn 参数
  - [ ] 3.4 上下文动态更新：每次发消息重新组装（确保包含最新 Tips/错误）

- [ ] **Task 4: 双向链接渲染** (AC: #3)
  - [ ] 4.1 扩展 `MessageBubble.svelte`（Story 3.3）的 Markdown 渲染逻辑
  - [ ] 4.2 Agent 引用附带 `[[文件名#章节标题]]` 格式的 Obsidian 链接
  - [ ] 4.3 使用 `MarkdownRenderer.render()` 原生支持 `[[wikilink]]` 渲染
  - [ ] 4.4 添加 click 事件 hook：点击链接 → `app.workspace.openLinkText(linkPath, sourcePath)`
  - [ ] 4.5 链接精度：索引时保留 `source_file` + `heading` 元数据 → Agent 引用时使用

- [ ] **Task 5: 后端上下文 API** (AC: #1, #2)
  - [ ] 5.1 创建 `backend/app/api/v1/context.py`：`GET /api/v1/context/{node_id}`
  - [ ] 5.2 端点返回 Tier 1 + Tier 2 数据（JSON 格式）
  - [ ] 5.3 数据来源：Graphiti（Tips/错误/Edge 理由）+ mastery_engine（精通度）+ Neo4j（邻居节点）
  - [ ] 5.4 端点结果缓存 30s（同一节点短时间内多次请求不重复查询）

## Dev Notes

### 上下文三层管理架构

```
Tier 1: 当前节点全量
  └── Tips（全部）+ 错误记录（全部）+ 精通度 + Edge 理由
  └── 来源：Graphiti + mastery_engine

Tier 2: 相邻节点摘要
  └── 1-hop 邻居的标题 + 精通度 + Edge 关系理由
  └── 来源：Neo4j 图查询

Tier 3: 远端 RAG 按需（本 Story 不实现预加载）
  └── Agent 通过 MCP search_memories 工具按需检索
  └── 来源：LanceDB + Graphiti
```

### --append-system-prompt 使用方式

```bash
claude -p "请解释贝叶斯定理" \
  --resume abc123 \
  --append-system-prompt "## 当前节点：贝叶斯定理\n### 精通度\n- BKT: 0.45\n### Tips\n- 先验概率是关键..." \
  --output-format stream-json
```

### 双向链接格式

Agent 在回复中可以使用 Obsidian wikilink 格式引用笔记：
```markdown
根据你的笔记 [[概率论笔记#贝叶斯公式]] 中的推导...
```

`MarkdownRenderer.render()` 原生支持 wikilink 渲染和跳转。

### 关键约束

1. **上下文每次重新组装**：不缓存在前端（确保 Tips/错误实时性）
2. **Token 控制**：Tier 1 + Tier 2 合计 < 4K tokens，防止 system prompt 过长
3. **Tier 3 不预加载**：远端上下文通过 MCP `search_memories` 工具按需检索（Agent 自主决定）
4. **空节点优雅处理**：新建节点无历史时，上下文仅包含节点标题和精通度默认值
5. **Claude Compaction 兜底**：Tier 1 过长时，Claude API 自动 Server-Side Compaction 处理

### 不做的事项（防蔓延）

- 不实现 Tier 3 预加载（通过 MCP 按需检索）
- 不实现上下文压缩到 3K token（Story 2.10 的 RAG 上下文压缩）
- 不实现 Tips/错误的写入逻辑（Story 3.6）
- 不实现 Edge 理由的写入逻辑（Story 4.2）
- 不实现掌握度注入 prompt 最前端（Story 2.10 的 Lost in Middle 缓解）

### Project Structure Notes

- 前端新建：`obsidian-canvas-learning/src/services/context-assembler.ts`
- 后端新建：`backend/app/api/v1/context.py`
- 扩展：`claude-code-engine.ts`（Story 3.1）添加上下文注入
- 扩展：`MessageBubble.svelte`（Story 3.3）添加双向链接跳转

### References

- [Source: _decisions/ADR-001-dialogue-engine.md#具体实现方案] — --append-system-prompt 用法
- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.4] — Story 需求和 AC
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements Overview] — Tier 1/2/3 三层上下文管理
- [Source: _bmad-output/planning-artifacts/architecture.md#Communication Patterns] — Obsidian 双向链接格式

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List
