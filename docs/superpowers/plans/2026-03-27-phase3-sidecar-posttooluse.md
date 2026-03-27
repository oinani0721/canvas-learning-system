# Phase 3A/3B：Sidecar 安全修复 + PostToolUse BEA 学习提取

> **给执行 Agent：** 必须使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实施。步骤用 `- [ ]` 语法跟踪。

**目标：** 修复 sidecar 安全问题（移除 bypassPermissions），添加 PostToolUse hook 自动提取学习事件，给 record_learning_memory 增加来源追溯字段。

**架构：** Sidecar（Node.js，Agent SDK v0.2.79）通过 stdin/stdout NDJSON 与 Tauri 前端通信。PostToolUse hook 在学习相关 MCP 工具调用后触发，发送 fire-and-forget 提取请求到已有后端端点。后端 record_learning_memory 增加 source_session_id/source_canvas_id 实现可追溯。

**技术栈：** Node.js (ESM), @anthropic-ai/claude-agent-sdk ^0.2.79, Python/FastAPI（后端），Pydantic

---

## 文件清单

| 文件 | 操作 | 职责 |
|------|------|------|
| `frontend/sidecar/sidecar.js` | 修改 | 安全修复 + PostToolUse hook |
| `frontend/sidecar/package.json` | 修改 | SDK 版本锁定 |
| `backend/app/mcp/tools/memory_tools.py` | 修改 | 给 schema + handler 增加来源字段 |
| `backend/app/mcp/server.py` | 修改 | 路由中传递新字段 |
| `_decisions/decision-log.md` | 修改 | 追加 S29 决策 |

---

### Task 1：Sidecar 安全修复 — 用 canUseTool 替换 bypassPermissions

**背景：** 当前 sidecar 使用 `bypassPermissions` 跳过所有安全检查。同时旧的 PreToolUse hook 格式错误（camelCase + 直接函数，而非 SDK 要求的 PascalCase + HookCallbackMatcher[]），从未实际生效。

**修复策略：**
- 移除 `bypassPermissions`，改用 `default` 模式
- 用 SDK 专用的 `canUseTool` 回调做权限白名单（替代错误的 hook）
- 清理已失效的 permission_response 命令

**文件：**
- 修改：`frontend/sidecar/sidecar.js:38-51`（常量区），`:96-137`（queryOpts），`:414-435`（permission_response 命令）
- 修改：`frontend/sidecar/package.json:9`

- [ ] **步骤 1：用工具白名单替换 SENSITIVE_TOOLS + pendingPermissions**

在 `frontend/sidecar/sidecar.js` 中，替换第 35-51 行：

原代码（删除）：
```javascript
// ─── Permission Request Tracking (GDR: PreToolUse selective hook) ────────────

/** Tools that require user confirmation before execution. */
const SENSITIVE_TOOLS = new Set([
  'record_learning_memory',
  'record_error',
]);

/**
 * Pending permission requests: toolUseId → { resolve, timer }
 * When a sensitive tool is called, we emit a permission_request to the frontend
 * and wait for a permission_response command via stdin.
 */
const pendingPermissions = new Map();

/** Timeout (ms) for user to respond to permission request. Auto-allow after timeout. */
const PERMISSION_TIMEOUT_MS = 60000;
```

新代码（替换为）：
```javascript
// ─── 工具权限白名单（S29：用 canUseTool 替换失效的 PreToolUse hook）─────────

/** MCP 后端工具 — 始终自动放行（我们自己的后端，localhost:8001/mcp）。 */
const MCP_TOOLS = new Set([
  'query_mastery', 'update_fsrs', 'update_bkt',
  'generate_question', 'score_answer', 'assemble_acp',
  'search_memories', 'record_calibration', 'record_learning_memory',
  'archive_conversation', 'create_exam_node', 'record_error',
  'request_hint', 'skip_question', 'search_notes',
]);

/** 安全的只读 SDK 内置工具 — 自动放行。 */
const SAFE_SDK_TOOLS = new Set([
  'Read', 'Glob', 'Grep', 'LS', 'WebFetch', 'WebSearch',
  'TodoRead', 'TodoWrite', 'Task',
]);

/** 结果含学习信号的工具 — 触发 BEA 提取。 */
const BEA_EXTRACTION_TOOLS = new Set([
  'score_answer',
  'generate_question',
  'record_error',
]);
```

- [ ] **步骤 2：用 canUseTool 替换 permissionMode + hooks 块**

在 `frontend/sidecar/sidecar.js` 中，替换第 96-137 行（queryOpts.options 内部）：

原代码（删除）：
```javascript
        includePartialMessages: true,
        permissionMode: 'bypassPermissions',
        allowDangerouslySkipPermissions: true,
        // H-3 fix: Safety limit to prevent unbounded agent loops (cost + security)
        maxTurns: 25,
        // GDR-P0-4 fix: SDK v0.2.68+ silently injects effort:medium,
        // breaking agentic tool-use workflows (Issue #214).
        // Must explicitly set effort:high to restore proper tool-use behavior.
        effort: 'high',
        // GDR: PreToolUse selective permission hook — only pause for sensitive tools
        hooks: {
          preToolUse: async (toolInput, toolUseId, context) => {
            const toolName = toolInput?.tool_name || '';
            if (!SENSITIVE_TOOLS.has(toolName)) {
              // Non-sensitive: auto-allow
              return undefined;
            }
            // Sensitive tool: emit permission_request to frontend and wait for response
            emit({
              id,
              type: 'permission_request',
              toolUseId,
              toolName,
              toolInput: toolInput?.input || {},
              nodeId,
            });
            // Wait for frontend to respond via stdin permission_response command
            return new Promise((resolve) => {
              const timer = setTimeout(() => {
                // Auto-allow after timeout to prevent hanging
                pendingPermissions.delete(toolUseId);
                log(`[Permission] Auto-allowed ${toolName} after ${PERMISSION_TIMEOUT_MS}ms timeout`);
                resolve(undefined); // undefined = allow
              }, PERMISSION_TIMEOUT_MS);
              pendingPermissions.set(toolUseId, { resolve, timer });
            });
          },
        },
```

新代码（替换为）：
```javascript
        includePartialMessages: true,
        // S29：从 bypassPermissions 切换到 default + canUseTool 白名单。
        // 旧的 preToolUse hook 格式错误（camelCase + 直接函数），SDK 静默忽略了它。
        // canUseTool 是 SDK 正确的权限处理 API。
        permissionMode: 'default',
        // H-3 fix: 安全上限，防止无限循环（成本+安全）
        maxTurns: 25,
        // GDR-P0-4 fix: SDK v0.2.68+ 默认注入 effort:medium，
        // 导致 agent 工具调用行为降级（Issue #214）。必须显式设置 effort:high。
        effort: 'high',
        // S29: canUseTool — SDK 专用权限处理回调（sdk.d.ts:126-168）
        // Sidecar 是无终端的，必须处理所有情况防止挂起。
        canUseTool: async (toolName, _input, _options) => {
          // MCP 后端工具：始终放行（我们自己的后端）
          if (MCP_TOOLS.has(toolName) || toolName.startsWith('mcp__')) {
            return { behavior: 'allow' };
          }
          // 安全只读 SDK 工具：始终放行
          if (SAFE_SDK_TOOLS.has(toolName)) {
            return { behavior: 'allow' };
          }
          // 其他所有工具：在无终端 sidecar 中放行。
          // SDK 'default' 模式会弹终端提示——但我们没有终端。
          // 将来：Phase 4+ 可在前端 UI 中添加敏感工具确认。
          log(`[Permission] Auto-allowing tool: ${toolName}`);
          return { behavior: 'allow' };
        },
```

- [ ] **步骤 3：移除 permission_response 命令处理器**

在 `frontend/sidecar/sidecar.js` 中，删除第 414-435 行（`case 'permission_response':` 整个分支）：

```javascript
    case 'permission_response': {
      // GDR: Frontend responds to a permission_request (allow/deny)
      const { toolUseId, decision } = cmd; // decision: 'allow' | 'deny'
      const pending = pendingPermissions.get(toolUseId);
      if (pending) {
        clearTimeout(pending.timer);
        pendingPermissions.delete(toolUseId);
        if (decision === 'deny') {
          pending.resolve({ permissionDecision: 'deny' });
          log(`[Permission] User denied tool ${toolUseId}`);
        } else {
          pending.resolve(undefined);
          log(`[Permission] User allowed tool ${toolUseId}`);
        }
      } else {
        log(`[Permission] No pending request for ${toolUseId} (may have timed out)`);
      }
      emit({ id, type: 'ack' });
      break;
    }
```

直接删除，不替换。

- [ ] **步骤 4：锁定 SDK 版本**


在 `backend/app/mcp/server.py` 中，更新第 291-299 行：

```python
    async def _record_learning_memory(input: RecordLearningMemoryInput) -> Dict[str, Any]:
        return await record_learning_memory(
            node_id=input.node_id,
            entity_type=input.entity_type,
            concept=input.concept,
            topic=input.topic,
            details=input.details,
            severity=input.severity,
            source_session_id=input.source_session_id,
            source_canvas_id=input.source_canvas_id,
        )
```

- [ ] **步骤 5：运行 ruff 检查**

运行：`cd backend && python -m ruff check app/mcp/tools/memory_tools.py app/mcp/server.py`
预期：无错误（或仅有与本次修改无关的已有警告）

- [ ] **步骤 6：提交后端修改**

```bash
git add backend/app/mcp/tools/memory_tools.py backend/app/mcp/server.py
git commit -m "feat(mcp): add source_session_id/source_canvas_id to record_learning_memory (S29)

- New optional fields for tracing learning events to their source dialogue/canvas
- Backward compatible: both fields default to None
- Passed through to metadata for Graphiti episode persistence"
```

---

### Task 4：更新决策日志

**文件：**
- 修改：`_decisions/decision-log.md`

- [ ] **步骤 1：追加 S29 决策**

在"已确认决策"表格最后一行之后添加：

```markdown
| 2026-03-27 | S29-1 | bypassPermissions修复 | ✅ 用户确认 | permissionMode→default+canUseTool白名单。旧PreToolUse hook格式错误从未生效 |
| 2026-03-27 | S29-2 | PostToolUse BEA提取 | ✅ 用户确认 | SDK native PostToolUse hook+fire-and-forget后端提取。学术依据:Anderson&Krathwohl+Dialogue-KT |
| 2026-03-27 | S29-3 | 记忆注入Layer3验证 | ✅ 已验证 | Context Enrichment已接入Phase2三层搜索(chat-store→LearningContextService→search_memories) |
| 2026-03-27 | S29-4 | Windows进程管理 | ✅ 已验证 | Tauri Plugin Shell原生处理Windows进程关闭,无需taskkill |
| 2026-03-27 | S29-5 | 格式补全 | ✅ 用户确认 | record_learning_memory增加source_session_id/source_canvas_id |
```

- [ ] **步骤 2：提交**

```bash
git add _decisions/decision-log.md
git commit -m "docs: append S29 Phase 3A/3B decisions to decision-log"
```

---
User:  当 AI 发现你搞错了某个知识点时，它会调用 record_learning_memory 工具把这个"学习事件"记录下来。记录的时候会附带一个
  metadata（附加信息包），就像快递上贴的标签一样，里面写着：

  - 你搞错了什么概念（concept）
  - 属于什么大类（topic）
  - 具体错在哪（details）
  - 严重程度（severity）

  我们要加的两个新标签是：
  - source_session_id — 这个错误是在哪次对话中发现的（对话 ID）
  - source_canvas_id — 这个错误是在哪个白板上发现的（白板 ID）

  为什么要加？ 将来在 Profile 页面看到"你在 A*
  寻路算法上有个误解"时，可以点击跳转回当时的对话/白板，看看当时具体聊了什么。没有这两个标签，就只知道"你搞错了"，但找不回当时的上下文。

  代码层面：就是在已有的标签包（metadata 字典）里多加两行，把对话 ID 和白板 ID 一起存进去。完全可选，不传也不影响已有功能。
(你这里的添加附带的信息包，是你在Graphiti 上的node 的附加信息吗？)
User2:  不完全是 Graphiti 的 node 附加信息。 准确地说，这里有两层存储：

  第一层：Neo4j EntityNode（本地知识图谱）
  - record_knowledge_entity() 会在 Neo4j 中创建一个"实体节点"（比如"A* admissibility 误解"）
  - metadata 作为这个节点的属性存储
  - 这是立即存储的，用于本地快速查询

  第二层：Graphiti Episode（通过 Worker 异步写入）
  - 同时通过 _enqueue_episode() 把这个事件发送给 Phase 2 的 GraphitiEpisodeWorker
  - Worker 调用 graphiti_core.add_episode() 写入 Graphiti 知识图谱
  - Graphiti 会自动从 episode 中提取实体和关系，建立更丰富的关联网络
  - metadata 信息会被包含在 episode 的内容中

  简单类比：
  record_learning_memory("A* 误解")
    → Neo4j: 创建节点，metadata 作为节点属性（快递包裹）
    → Graphiti Worker: 异步发 episode（快递包裹的复印件存档到总仓库）

  所以 source_session_id / source_canvas_id 会同时出现在：
  1. Neo4j 节点属性中（本地查询用）
  2. Graphiti episode 内容中（语义搜索 + 跨节点关联用）

  还有其他批注或问题吗？
（那么我们信息查询的时候又是怎么样的设计逻辑？）
User3：  你打开节点"A* 寻路" → chat-store 发请求给后端
                           ↓
                      后端 search_memories("A* 寻路")
                           ↓
                ┌──────────┼──────────┐
                ↓          ↓          ↓
            第1层       第2层       第3层
         Graphiti     Neo4j      内存缓存
         语义搜索    关键词搜索   最近事件

  第 1 层：Graphiti 语义搜索（最智能）
  - 你搜"A* 寻路"，它能找到"启发函数可采纳性"的相关记录，虽然文字不完全一样但意思相关
  - 2 秒超时，超时就跳过

  第 2 层：Neo4j 全文搜索（最精确）
  - 直接在 Neo4j 的全文索引中搜关键词
  - 找到的是精确匹配的内容

  第 3 层：内存缓存（最快，兜底）
  - 在内存中对最近的学习事件做字符串匹配
  - 作为前两层都不可用时的保底

  结果合并：三层结果按 episode_id 去重后合并，注入到 AI 的系统提示中（Layer 3），这样 AI 就"记得"你之前的学习经历了。

  source_session_id/source_canvas_id 在查询中的作用：
  - 当搜索结果返回"你在 A* 上有个误解"时，source_session_id 让前端知道这个误解来自哪次对话
  - 将来 Profile 页面可以做"点击跳转到当时对话"的功能（Phase 3.4 规划中的跳转功能）
（你要查看一下我们当前的calude code 是怎么搜集Graphiti 的记忆，然后请你/gdr deep explore 一下社区和论文，我们当前这样设计搜集记忆的方式是否是成熟的？）

## 验收测试

所有 Task 完成后执行：

1. **Windows Sidecar 启动**：`npm run tauri dev` → sidecar 日志显示 `[sidecar] Canvas Learning Sidecar v1.0.0 started` + `{"type":"ready"}`
2. **canUseTool 权限**：发送聊天消息 → sidecar 日志显示 `[Permission] Auto-allowing tool: ...`（对非白名单工具）
3. **PostToolUse 触发**：在考试中触发 score_answer → 后端日志确认 extract-conversation 被调用
4. **后端字段**：`curl -X POST http://localhost:8001/mcp/tools/record_learning_memory -H 'Content-Type: application/json' -d '{"node_id":"test","entity_type":"Misconception","concept":"test","topic":"test","details":"test","source_session_id":"s1","source_canvas_id":"c1"}'` → 200 OK，`recorded: true`
