---
doc_type: story
story_id: "2.1"
epic_id: "EPIC-2"
prd_id: "PRD14"
status: ready-for-dev
priority: "P0"
estimate_hours: 8
depends_on: ["1.2"]
blocks: []
trace:
  decisions: []
  bugs: []
---

# Story 2.1: AI 对话 + wikilink 上下文注入

## Story

As a 学习者,
I want 启动 AI 对话时，系统自动通过 wikilink 图遍历发现当前笔记的相邻概念，读取 frontmatter 和内容作为对话上下文,
so that AI 对话具有充分的知识背景，回答更精准。

## Acceptance Criteria

1. **Given** 学习者在某笔记页面启动 AI 对话
   **When** 对话启动
   **Then** 系统调用 Story 1.2 的 wikilink 遍历获取 2-hop 邻居
   **And** 将当前笔记 + 邻居的 frontmatter 和内容摘要注入 LLM 上下文
   **And** 上下文压缩后不超过 3K tokens（AR7）
   **And** 公式和代码块整块保护不被截断（AR7）

2. **Given** LLM 上下文已注入
   **When** 学习者提出问题
   **Then** AI 回答引用了相邻概念的知识
   **And** LLM 出题/评分延迟 < 5s（NFR-PERF-1）

## Tasks / Subtasks

- [ ] Task 1: 构建对话上下文组装服务 (AC: #1)
  - [ ] 1.1 在 `backend/app/services/` 新建 `dialog_context_service.py`，定义 `DialogContextService` 类
  - [ ] 1.2 实现 `build_context(note_path: str) -> DialogContext`：调用 `WikilinkGraph.get_neighbors(hop=2)` 获取邻居节点
  - [ ] 1.3 实现上下文内容摘要提取：读取每个邻居的 frontmatter（含 mastery_score）+ 正文前 500 字
  - [ ] 1.4 实现 3K token 预算分配：当前笔记优先，邻居按 hop_distance 排序，超出预算截断末尾邻居
  - [ ] 1.5 实现公式/代码块保护：用正则识别 `$$...$$`、`` ```...``` `` 块，整块保留或整块丢弃，不在块中间截断

- [ ] Task 2: LLM 对话 API endpoint (AC: #1, #2)
  - [ ] 2.1 在 `backend/app/api/v1/endpoints/` 新建 `dialog.py`，添加 `POST /api/v1/dialog/start` endpoint
  - [ ] 2.2 请求体：`DialogStartRequest(note_path: str, user_message: str)`
  - [ ] 2.3 调用 `DialogContextService.build_context()` 组装系统 prompt
  - [ ] 2.4 调用 LLM（通过 `backend/app/services/llm_service.py` 或等价模块）发送请求，流式或一次性返回
  - [ ] 2.5 响应体：`DialogResponse(reply: str, context_tokens: int, neighbors_used: List[str])`
  - [ ] 2.6 记录耗时（structlog），确保端到端延迟 < 5s（NFR-PERF-1）

- [ ] Task 3: 前端对话面板集成 (AC: #1, #2)
  - [ ] 3.1 在 `frontend/src/components/` 新建 `ChatPanel.tsx`（如已存在则复用）对话面板组件
  - [ ] 3.2 对话面板从 Zustand store 读取当前活跃笔记路径（`activeNotePath`）
  - [ ] 3.3 用户发送消息时调用 `POST /api/v1/dialog/start`，传入 `note_path` 和 `user_message`
  - [ ] 3.4 显示 AI 回复，loading 状态用骨架屏（不显示评分/后台细节）
  - [ ] 3.5 在 `frontend/src/stores/` 新建或扩展 `dialog-store.ts`，管理对话历史列表

- [ ] Task 4: 编写测试 (AC: #1, #2)
  - [ ] 4.1 单元测试 `backend/tests/unit/test_dialog_context_service.py`：
    - `build_context()` 返回正确的邻居节点内容
    - 3K token 上限强制：超出时截断末尾邻居，不截断当前笔记
    - 公式块 `$$...$$` 不被中间截断
  - [ ] 4.2 集成测试 `backend/tests/integration/test_dialog_api.py`：
    - `POST /api/v1/dialog/start` 返回非空 reply
    - context_tokens 字段 ≤ 3072
    - 延迟 < 5000ms（实测 with Ollama）
  - [ ] 4.3 前端测试 `frontend/src/components/__tests__/ChatPanel.test.tsx`：
    - 用户输入消息后发起 API 调用
    - loading 状态正确显示/隐藏
    - AI 回复文本渲染在消息列表中

## Dev Notes

- **依赖 Story 1.2 的 WikilinkGraph**：`DialogContextService` 通过依赖注入接收 `WikilinkGraph` 实例（FastAPI `Depends`），不能直接 import 构建新实例，避免重复构建 vault 图
- **3K token 计算**：使用 tiktoken 库估算 token 数（cl100k_base 编码），而非字符数。tiktoken 已是 openai 依赖的传递依赖，不需额外安装
- **公式/代码块保护实现**：先 split 成 blocks（保护块 + 普通段落），贪心填充，保护块整块处理——如果当前保护块放入后超出预算则整块丢弃，不能分割
- **LLM 调用**：通过项目已有的 LLM 调用入口（参考 `backend/app/services/rag_service.py` 中的模式），不要绕过统一入口直接调 openai/ollama
- **structlog 日志字段**：`dialog_context_tokens`、`dialog_neighbors_count`、`dialog_latency_ms`，均用 snake_case
- **AR7 token 预算**：当前笔记分配 1500 tokens，邻居共享剩余 1500 tokens，系统 prompt 预留约 500 tokens 给指令

### Project Structure Notes

- 新建文件：`backend/app/services/dialog_context_service.py`
- 新建文件：`backend/app/api/v1/endpoints/dialog.py`
- 新建/扩展文件：`frontend/src/components/ChatPanel.tsx`
- 新建/扩展文件：`frontend/src/stores/dialog-store.ts`
- 测试文件：
  - `backend/tests/unit/test_dialog_context_service.py`
  - `backend/tests/integration/test_dialog_api.py`
  - `frontend/src/components/__tests__/ChatPanel.test.tsx`
- 样式参考：`backend/app/services/rag_service.py`（service 结构）、`backend/app/api/v1/endpoints/canvas.py`（router 结构）、`frontend/src/stores/chat-store.ts`（Zustand store 结构）、`frontend/src/components/ChatPanel.tsx`（前端组件）

### References

- [Source: backend/app/services/wikilink_graph.py] — Story 1.2 实现的 WikilinkGraph，本 story 的核心依赖
- [Source: backend/app/services/context_enrichment_service.py] — 上下文组装参考实现
- [Source: backend/app/services/rag_service.py] — LLM 调用和 service 结构范式
- [Source: frontend/src/stores/chat-store.ts] — Zustand store 参考（对话状态管理）
- [Source: frontend/src/components/ChatPanel.tsx] — 前端对话面板参考组件
- [Source: _bmad-output/planning-artifacts/epics.md#Story-2.1] — AC 原文和 FR/AR 映射
- [Source: _bmad-output/planning-artifacts/prd.md#FR1-AR7] — FR1 原文：AI 对话上下文注入；AR7：token 预算约束

## UAT Script

> 非技术用户验收脚本：只描述用户操作和预期看到的内容，不含代码术语。

1. **验证 AI 对话能感知当前笔记内容** (AC: #1)
   - 打开应用，打开 Obsidian 中一篇有双链的笔记（例如"线性变换"，其中链接了"矩阵"这篇笔记）
   - 点击应用中的"AI 对话"按钮启动对话面板
   - 在对话框中输入："请解释一下这个概念和矩阵的关系"
   - 点击发送
   - AI 的回复中应该能看到关于"矩阵"这篇笔记内容的引用
   - 如果 AI 回复完全不提矩阵，或者说"我不了解矩阵相关内容"，请记录 Story 2.1

2. **验证回复速度** (AC: #2)
   - 发送任意一个问题后，计时从点击发送到回复完整显示
   - 应在 5 秒内看到完整回复
   - 如果超过 5 秒没有任何回复出现，请记录 Story 2.1 和等待时间

3. **验证公式不被截断** (AC: #1)
   - 打开一篇包含数学公式（被 $$ 包围的内容）的笔记
   - 启动 AI 对话并提问关于该笔记的问题
   - AI 回复中如果引用了公式，公式应该是完整的（不会出现公式只显示一半的情况）
   - 如果公式被截断，请记录 Story 2.1 和截断的公式截图

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-2.1.1 | pytest | `.venv/bin/pytest backend/tests/unit/test_dialog_context_service.py -x -q` | 0 failed |
| CP-2.1.2 | pytest | `.venv/bin/pytest backend/tests/integration/test_dialog_api.py -x -q` | 0 failed |
| CP-2.1.3 | vitest | `cd frontend && npx vitest run src/components/__tests__/ChatPanel.test.tsx` | 0 failed |
| CP-2.1.4 | ruff | `ruff check backend/app/services/dialog_context_service.py backend/app/api/v1/endpoints/dialog.py` | exit 0 |

## User Feedback & Changes

### Feedback Log

<!-- Users write BMAD-ANNO callouts below. Claude scans and dispatches by intent. -->

### Deviation Notes

<!-- Claude auto-fills: summary of historically processed feedback -->

## Dev Agent Record

### Agent Model Used

(to be filled by Dev agent)

### Debug Log References

### Completion Notes List

### File List

## Relations

- EPIC: [[EPIC-2]]
- PRD: [[PRD14]]
- Depends on: [[1.2]]
