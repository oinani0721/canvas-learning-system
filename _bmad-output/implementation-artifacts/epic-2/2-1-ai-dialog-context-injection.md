---
story_id: "2.1"
epic_id: "2"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 10
depends_on: ["1.3"]
blocks: ["2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8"]
trace:
  - "FR-CONV-01"
  - "FR-CONV-04"
---

# Story 2.1: AI 对话 + 邻居上下文注入

Status: ready-for-dev

## Story

As a 学习者,
I want 启动 AI 对话时系统自动注入相邻概念和掌握度信息,
So that AI 的回答基于我笔记的实际结构和我的学习状态。

## Acceptance Criteria

1. **Given** 学习者在某笔记页面启动 AI 对话（`/chat_with_context`）
   **When** 对话启动
   **Then** 系统调用 `context_enrichment` MCP 工具，通过 wikilink 图遍历获取当前笔记的 2-hop 邻居
   **And** 返回的邻居列表包含每个邻居的 slug、关系类型、hop 距离

2. **Given** 2-hop 邻居已获取
   **When** 系统组装 LLM 上下文
   **Then** 注入当前笔记完整内容 + 每个邻居的 frontmatter（mastery_score / bkt_params / tips[] / errors[]）+ 内容摘要
   **And** 注入 Edge 文件中的 rationale 和 relationship_type
   **And** 公式块（`$$...$$` / `$...$`）和代码块（` ```...``` `）在压缩过程中保持完整不被截断

3. **Given** 注入的上下文超过 token 预算
   **When** 系统执行上下文压缩
   **Then** 按优先级保留：当前笔记全文 > 1-hop 邻居 frontmatter+Tips+errors > 1-hop 内容摘要 > 2-hop frontmatter > 2-hop 内容
   **And** 压缩后总 token 不超过预算阈值（可配置，默认 8192 tokens）
   **And** 压缩过程不破坏 LaTeX 公式和代码块的完整性

4. **Given** 上下文组装完成
   **When** LLM 生成响应
   **Then** LLM 首 token 延迟 < 5s P95（NFR-PERF）
   **And** 响应内容正确引用了邻居概念的相关信息

5. **Given** wikilink 图服务不可用（Epic 1 降级场景）
   **When** 学习者启动对话
   **Then** 系统仅注入当前笔记内容，跳过邻居发现
   **And** 在响应末尾通知学习者："邻居上下文暂时不可用，仅基于当前笔记回答"

## Tasks / Subtasks

- [ ] Task 1: `context_enrichment` MCP 工具扩展 — 支持 2-hop wikilink 图遍历 (AC: #1)
  - [ ] 1.1: 在 `backend/app/services/context_enrichment_service.py` 中新增 `enrich_from_wikilink_graph(node_id: str, max_hops: int = 2)` 方法，调用 Story 1.3 的 wikilink 图服务获取邻居
  - [ ] 1.2: 返回结构化邻居列表 `List[NeighborContext]`，每项含 `slug` / `hop_distance` / `relationship_type` / `frontmatter` / `content_summary`
  - [ ] 1.3: 实现 1-hop 优先、2-hop 补充的遍历策略；遍历深度由参数 `max_hops` 控制
  - [ ] 1.4: 遍历超时保护：单次图遍历 < 200ms（NFR-PERF：图遍历查询 < 200ms），超时返回已获取的部分结果

- [ ] Task 2: LLM 上下文组装与 token 预算压缩 (AC: #2, #3)
  - [ ] 2.1: 在 `backend/app/services/` 下创建 `chat_context_assembler.py`，实现 `ChatContextAssembler` 类
  - [ ] 2.2: 实现 `assemble_context(current_note, neighbors, token_budget)` 方法，按优先级填充 token 预算
  - [ ] 2.3: 实现 `compress_content(text, max_tokens)` 方法，在句子边界截断，保护 LaTeX 公式（`$$...$$` / `$...$`）和代码块（` ```...``` `）完整性
  - [ ] 2.4: token 计数使用 tiktoken（cl100k_base 编码），预算默认 8192 可通过环境变量 `CHAT_CONTEXT_TOKEN_BUDGET` 配置
  - [ ] 2.5: 优先级排序：当前笔记全文 → 1-hop frontmatter+Tips+errors → 1-hop 内容摘要 → 2-hop frontmatter → 2-hop 内容

- [ ] Task 3: `/chat_with_context` Skill workflow 实现 (AC: #4)
  - [ ] 3.1: 创建 Claudian skill 定义文件，按 PRD §4.1 的 7 步 workflow 实现（Step 1 注入 current_note → Step 3 调 context_enrichment → Step 5 构造 prompt → Step 6 LLM 返回）
  - [ ] 3.2: Step 5 构造 system prompt 模板，包含 `{context}` 占位符和正面措辞规范
  - [ ] 3.3: 实现 `pipeline_token` 传递机制（Step 3 返回 token_A，传给后续 Step 4/7）
  - [ ] 3.4: 添加延迟监控日志：记录 context_enrichment 耗时、LLM 首 token 耗时

- [ ] Task 4: 降级处理与错误恢复 (AC: #5)
  - [ ] 4.1: 在 `enrich_from_wikilink_graph` 中捕获图服务异常（连接超时 / 服务不可用），返回空邻居列表 + 降级标记
  - [ ] 4.2: 在 skill workflow 中检测降级标记，仅注入当前笔记内容
  - [ ] 4.3: 降级时在 LLM system prompt 末尾追加通知文本

- [ ] Task 5: 单元测试与集成测试 (AC: #1~#5)
  - [ ] 5.1: 单元测试 `enrich_from_wikilink_graph`：正常 2-hop 遍历、超时降级、空图场景
  - [ ] 5.2: 单元测试 `ChatContextAssembler`：token 预算压缩、公式保护、优先级排序
  - [ ] 5.3: 集成测试：完整 workflow 从 skill 触发到 LLM 响应，验证上下文正确注入
  - [ ] 5.4: 性能测试：100 文件 vault 下首 token < 5s P95

## Dev Notes

- **核心依赖**: Story 1.3（wikilink 图构建与遍历服务）提供 `get_neighbors(node_id, max_hops)` 接口
- **已有代码参考**: `backend/app/services/context_enrichment_service.py` 已有 1-hop 邻居发现逻辑（基于旧 Canvas JSON），需重构为 wikilink 图遍历
- **Anchor PRD 引用**: §4.1 `/chat_with_context` (line 3647-3705) 定义了完整 7 步 workflow
- **token 计数**: 使用 tiktoken `cl100k_base` 编码器（Claude 3.5 兼容），不引入新依赖（tiktoken 已在 requirements）
- **公式保护策略**: 正则匹配 `\$\$[\s\S]*?\$\$` 和 `` ```[\s\S]*?``` `` 标记为不可分割块，压缩时整块保留或整块丢弃
- **structlog 日志**: 所有 service 使用 `structlog.get_logger(__name__)` 记录，遵循项目日志规范

### Project Structure Notes

```
backend/app/services/
  context_enrichment_service.py   # 扩展：新增 enrich_from_wikilink_graph()
  chat_context_assembler.py       # 新增：token 预算压缩与上下文组装
backend/tests/unit/
  test_chat_context_assembler.py  # 新增：压缩与优先级测试
  test_context_enrichment_wikilink.py  # 新增：图遍历测试
```

### References

- PRD §4.1 `/chat_with_context` workflow: `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md` (line 3647-3705)
- 已有 context_enrichment_service.py: `backend/app/services/context_enrichment_service.py`
- NFR 性能指标: BMAD PRD `_bmad-output/planning-artifacts/prd.md` (line 526-537)
- Story 1.3 wikilink 图遍历: `_bmad-output/implementation-artifacts/epic-1/`

## UAT Script

> 1. 打开 Obsidian vault，导航到 `wiki/concepts/admissibility.md`
> 2. 使用 Cmd+Option+C 启动 AI 对话
> 3. 输入问题："admissibility 和 consistent 有什么区别？"
> 4. 验证 AI 回答中引用了邻居概念（如 a-star、consistent）的信息
> 5. 验证首次回答出现时间 < 5 秒
> 6. 停止后端服务，再次启动对话，验证系统提示"邻居上下文暂时不可用"但仍能回答

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| context_enrichment 2-hop | unit | `pytest tests/unit/test_context_enrichment_wikilink.py -x` | 全部通过 |
| token 预算压缩 | unit | `pytest tests/unit/test_chat_context_assembler.py -x` | 全部通过 |
| 公式保护 | unit | `pytest tests/unit/test_chat_context_assembler.py::test_formula_protection -x` | LaTeX 块完整 |
| 首 token 延迟 | perf | `pytest tests/perf/test_chat_latency.py --timeout=10` | P95 < 5s |
| 降级场景 | integration | `pytest tests/integration/test_chat_degradation.py -x` | 降级提示出现 |

## User Feedback & Changes

### Feedback Log

(empty)

### Deviation Notes

(empty)

## Dev Agent Record

### Agent Model Used

(to be filled by Dev agent)

### Debug Log References

(to be filled by Dev agent)

### Completion Notes List

(to be filled by Dev agent)

### File List

(to be filled by Dev agent)
