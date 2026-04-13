---
story_id: "1.3"
epic_id: "1"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 8
depends_on: ["1.2"]
blocks: ["2.1"]
trace:
  - "FR-ADAPT-02"
---

# Story 1.3: Wikilink 上下文组装

Status: ready-for-dev

## Story

As a 系统,
I want 基于 wikilink 图为 AI 对话组装完整上下文包,
So that AI 能理解当前概念与邻居的关系、掌握度、Tips 和错误记录。

## Acceptance Criteria

1. **Given** 学习者在某概念笔记上启动 AI 对话
   **When** 系统组装上下文
   **Then** 上下文包含：当前笔记完整内容 + N-hop 邻居的 frontmatter 摘要 + 内容摘要 + Tips + 错误记录 + concept.md frontmatter relationships[] 中的关系理由
   **And** 组装调用 WikilinkGraphService.get_neighbors()（Story 1.2）获取邻居

2. **Given** 上下文组装完成
   **When** 检查输出
   **Then** 压缩后总 token 数不超过预算（AR7，默认 4096 tokens）**User：请问你用什么压缩算法，建议去查看一下 claude code 前端所泄露的上下文压缩算法，，或者你启动并行 agent deep  explore 一下社区解决这一点的成熟的案例**  
   **User2：这里的 claude code 的开源算法，你完全可以在社区来 deep explore**
   **And** 公式块（`$$...$$` 和 `$...$`）整块保护不被切断
   **And** 代码块（```...```）整块保护不被切断

3. **Given** 当前笔记有 Tips callout（`[!tip]+`） **User：Tips callout 我是怎么进行触发的**
   **When** 组装上下文
   **Then** Tips 内容被提取并作为独立字段注入上下文
   **And** 邻居笔记的 Tips 也被包含（按 hop 距离排序，近优先）

4. **Given** 当前笔记的 frontmatter 中有 `errors: [...]`   **User：这里的`errors: [...]` 又是怎么进行触发的**
   **When** 组装上下文
   **Then** 错误记录被提取并注入上下文，AI 可用于历史误解提醒

5. **Given** 当前笔记或邻居笔记的 frontmatter 中有 `relationships: [...]`
   **When** 组装上下文     > **User：这里的Edge 文件我们又是该如何触发使用的**
   **Then** relationships[] 中的 `rationale` 和 `semantic_type` 字段被提取并注入上下文

6. **Given** 一个邻居笔记的 frontmatter 解析失败
   **When** 组装上下文
   **Then** 跳过该邻居的 frontmatter 字段，用空默认值替代，不中断整个组装流程

## Tasks / Subtasks

- [ ] Task 1: DialogContextService 核心实现 (AC: #1)
  - [ ] 1.1: 创建 `backend/app/services/dialog_context_service.py`
  - [ ] 1.2: 实现 `DialogContextService.__init__(wikilink_graph: WikilinkGraphService, vault_path: str)`
  - [ ] 1.3: 实现 `assemble_context(note_path: str, hop: int = 2, token_budget: int = 4096) -> DialogContext`
  - [ ] 1.4: `DialogContext` dataclass 包含：`current_note: NoteContent` · `neighbors: List[NeighborSummary]` · `tips: List[str]` · `errors: List[ErrorRecord]` · `relationship_rationales: List[str]` · `total_tokens: int`

- [ ] Task 2: 内容提取器 (AC: #1, #3, #4, #5)
  - [ ] 2.1: 实现 `_extract_tips(content: str) -> List[str]`：正则匹配 `[!tip]+` callout 块并提取内容
  - [ ] 2.2: 实现 `_extract_errors(frontmatter: Dict) -> List[ErrorRecord]`：从 frontmatter `errors` 字段读取
  - [ ] 2.3: 实现 `_extract_relationship_rationales(note_path: str) -> List[str]`：从当前笔记和邻居笔记的 frontmatter `relationships[]` 字段读取 `rationale` 和 `semantic_type`
  - [ ] 2.4: 实现 `_summarize_note(content: str, max_tokens: int) -> str`：生成内容摘要用于邻居注入

- [ ] Task 3: Token 压缩与保护 (AC: #2)
  - [ ] 3.1: 实现 `_compress_context(context: DialogContext, token_budget: int) -> DialogContext`
  - [ ] 3.2: 公式保护：识别 `$$...$$` 和 `$...$` 块，标记为不可切割
  - [ ] 3.3: 代码块保护：识别 ` ```...``` ` 块，标记为不可切割
  - [ ] 3.4: 压缩策略：优先截断远 hop 邻居摘要 → 截断非保护内容 → 保留当前笔记 + Tips + Errors 核心
  - [ ] 3.5: Token 计数使用 tiktoken 或简单字符估算（1 token ~= 4 chars 英文 / 2 chars 中文）

- [ ] Task 4: 集成 ContextEnrichmentService (AC: #1)
  - [ ] 4.1: 在 `backend/app/services/context_enrichment_service.py` 的 `enrich_context()` 中，当输入为 `.md` 路径时，委托到 `DialogContextService.assemble_context()`
  - [ ] 4.2: 保留原 `.canvas` JSON 分支作为 fallback

- [ ] Task 5: 错误容忍 (AC: #6)
  - [ ] 5.1: frontmatter 解析异常时 catch 并 structlog warning，返回空 dict
  - [ ] 5.2: relationships[] 字段解析异常时跳过，structlog warning
  - [ ] 5.3: 邻居 get_neighbors 返回空时，上下文仅含当前笔记

- [ ] Task 6: 测试 (AC: #1, #2, #3, #4, #5, #6)
  - [ ] 6.1: `backend/tests/unit/test_dialog_context_service.py` — 上下文组装、Tips 提取、Error 提取、Edge 理由提取
  - [ ] 6.2: `backend/tests/unit/test_context_compression.py` — 公式保护、代码块保护、token 预算遵守
  - [ ] 6.3: `backend/tests/unit/test_context_error_tolerance.py` — frontmatter 失败、Edge 缺失、空邻居

## Dev Notes

- **现有 context_enrichment**: `backend/app/services/context_enrichment_service.py` 是降级前遗留，读取 `.canvas` JSON。本 service 新建独立模块，通过 Task 4 桥接到现有接口
- **Service 风格**: 参考 `backend/app/services/rag_service.py` — structlog、类型标注、依赖注入
- **Token 计数**: 精确计数需要 tiktoken（依赖 OpenAI tokenizer），但项目用多种 LLM。建议 v1 用启发式估算（英文 1:4 / 中文 1:2），后续可替换
- **AR7 上下文压缩**: PRD 明确要求公式和代码块整块保护，这是学术内容（CS 61B）的硬需求
- **[DECISION-TECH-PENDING: context-assembly/compression-algorithm]** 压缩算法待 Deep Research 确定。候选：LangChain ContextualCompressionRetriever + LLMChainExtractor（句子级提取）。用户建议参考 Claude Code 前端压缩算法的社区分析。
- **Tips callout 格式**: Obsidian callout 语法 `> [!tip]+ 标题\n> 内容`，需要正则匹配多行
- **关系数据来源**: 关系信息存储在 concept.md frontmatter 的 `relationships[]` 字段中，每条包含 `target` / `semantic_type` / `rationale` / `ei_techniques` / `se_summary`（替代独立 edges/ 目录方案）
- **structlog**: `structlog.get_logger(__name__)` 统一

### 触发机制说明（用户批注回应）

| 元素 | 触发方式 | 写入目标 |
|------|---------|---------|
| Tips `[!tip]+` | 用户在 md 编辑器中手写 `> [!tip]+ 关键知识点` → 保存文件时系统解析 callout | frontmatter `tips[]` 数组更新 |
| Errors `errors[]` | AI 对话中检测到误解 → `record_error` MCP 工具自动触发 | frontmatter `errors[]` + Graphiti 双写 |
| Relationships `relationships[]` | `/edge_discuss` Skill 讨论结束 → 更新当前概念的 frontmatter | concept.md 的 `relationships[]` 字段 |
**User：关于 edge 关系的讨论 ，我觉得如果我在当前的文档拉出来新的节点的时候，就是自动触发讨论的情况；而且你这个 error 的检测确定是在 claudian 对话的流程中自动的触发是吧。**
**注意**: Tips 是用户主动标记，errors 是 AI 自动检测，relationships 是 Skill 讨论后自动记录。

### Project Structure Notes

- 新建文件：`backend/app/services/dialog_context_service.py`
- 修改文件：`backend/app/services/context_enrichment_service.py`（新增 DialogContextService 委托分支）
- 测试文件：`backend/tests/unit/test_dialog_context_service.py`
- 测试文件：`backend/tests/unit/test_context_compression.py`
- 测试文件：`backend/tests/unit/test_context_error_tolerance.py`

### References

- [Source: _bmad-output/planning-artifacts/prd.md#FR-ADAPT-02] — 双向链接图上下文组装
- [Source: _bmad-output/planning-artifacts/prd.md#AR7] — 上下文压缩（公式/代码整块保护）
- [Source: _bmad-output/planning-artifacts/epics.md#Story-1.3] — AC 原文
- [Source: backend/app/services/context_enrichment_service.py] — 现有 context_enrichment 模块
- [Source: backend/app/services/wikilink_graph_service.py] — Story 1.2 产出，本 service 依赖
- [Source: backend/app/services/rag_service.py] — Service 风格参考

## UAT Script

> 非技术用户验收脚本

1. **验证上下文组装** (AC: #1)
   - 在 vault 中找一篇有 `[[双链]]` 引用的笔记
   - 在浏览器访问 `http://localhost:8001/api/v1/context/assemble?note=笔记名.md`
   - 应该看到返回的上下文包含：当前笔记内容、邻居信息、Tips 列表、错误记录
   - 邻居信息应包含学习数据（mastery_score 等）

2. **验证公式保护** (AC: #2)
   - 找一篇包含数学公式（用 `$$` 包裹）的笔记
   - 查询该笔记的上下文
   - 公式应该完整显示，不会被截断到一半

3. **验证 Tips 提取** (AC: #3)
   - 找一篇包含 `[!tip]` 批注的笔记
   - 查询上下文，应该在 Tips 列表中看到批注内容

4. **验证错误容忍** (AC: #6)
   - 即使某些邻居笔记格式不标准，查询不应报错
   - 返回结果中格式有问题的邻居会被跳过，其他内容正常显示

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-1.3.1 | pytest | `.venv/bin/pytest backend/tests/unit/test_dialog_context_service.py -x -q` | 0 failed |
| CP-1.3.2 | pytest | `.venv/bin/pytest backend/tests/unit/test_context_compression.py -x -q` | 0 failed |
| CP-1.3.3 | pytest | `.venv/bin/pytest backend/tests/unit/test_context_error_tolerance.py -x -q` | 0 failed |
| CP-1.3.4 | ruff | `ruff check backend/app/services/dialog_context_service.py backend/app/services/context_enrichment_service.py` | exit 0 |

## User Feedback & Changes

### Feedback Log
<!-- Users write BMAD-ANNO callouts below -->

### Deviation Notes

**批注处理记录 (2026-04-13)**
1. **压缩算法** (User line 33, User2 line 34): 标记为 TECH 决策待定，社区调研 Claude Code 压缩方案。
2. **Tips 触发** (User line 38): 用户手写 [!tip]+ callout → 保存时解析。已补充触发机制说明。
3. **errors 触发** (User line 43): AI 对话自动检测 → record_error MCP。已补充。
4. **Edge 触发** (User line 48): 改为 /edge_discuss → frontmatter relationships[]。已更新。
5. **N3: 自动触发确认** (User line 108): ✅ 拉出新节点时，如果两端概念之间存在关系，可以自动触发 `/edge_discuss` 讨论（非强制，用户可跳过）。error 检测在 Claudian 对话流程中由 AI 自动检测并调用 `record_error` MCP，无需用户手动触发。

## Dev Agent Record

### Agent Model Used
(to be filled by Dev agent)

### Debug Log References

### Completion Notes List

### File List
