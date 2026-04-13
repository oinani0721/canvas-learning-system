---
story_id: "2.2"
epic_id: "2"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 6
depends_on: ["2.1"]
blocks: []
trace:
  - "FR-CONV-03"
---

# Story 2.2: 补充学习材料搜索

Status: ready-for-dev

## Story

As a 学习者,
I want 对话回答中看到可点击的补充学习材料列表,
So that 我可以深入探索相关内容，找到课堂笔记和其他学习资源。

## Acceptance Criteria

1. **Given** AI 对话回答已生成
   **When** 系统调用 `search_vault_notes` MCP 工具执行语义搜索
   **Then** 返回最多 5 条相关学习材料
   **And** 每条结果包含标题、内容片段摘要（< 100 字）、来源文件路径、相关度分数

2. **Given** 语义搜索返回结果
   **When** 结果在 Claudian sidebar 显示
   **Then** 每条材料以可点击的 wikilink 形式呈现（支持文件级 / 段落级 / block 级三种精度）
   **And** 按精排后的最终分数降序排列
   **And** 相关度 < 0.70 的结果不显示

3. **Given** 搜索返回多种类型的学习材料
   **When** 系统执行精排
   **Then** 按类型权重调整最终分数：lecture_notes (1.0) > discussion (0.9) > exam_review (0.85) > wiki_concepts (0.8) > chat_session (0.7) > raw_notes (0.6)
   **And** 最终分数 = relevance_score * type_weight

4. **Given** LanceDB 索引文件变更
   **When** 单文件保存触发增量索引
   **Then** 增量索引耗时 < 500ms/file（NFR-PERF）

5. **Given** LanceDB 服务不可用或索引为空
   **When** 学习者启动对话
   **Then** AI 正常回答，补充材料区域显示"暂无补充材料"
   **And** 不影响主对话流程

## Tasks / Subtasks

- [ ] Task 1: `search_vault_notes` MCP 集成到 `/chat_with_context` workflow (AC: #1)
  - [ ] 1.1: 在 Story 2.1 的 skill workflow 中新增 Step 5（PRD §4.1.1 的扩展 9 步 workflow），在 context_enrichment 和 search_memories 之后调用 `search_vault_notes`
  - [ ] 1.2: 搜索 query 取自用户问题 + 当前笔记标题的组合
  - [ ] 1.3: 传递 `pipeline_token` 保持链路追踪（token_B → token_C）
  - [ ] 1.4: 设置 `search_mode: "hybrid"`（bge-m3 语义 + jieba 关键词）和 `min_relevance: 0.70`

- [ ] Task 2: 精排服务实现 (AC: #3)
  - [ ] 2.1: 在 `backend/app/services/` 下创建 `supplementary_reranker.py`
  - [ ] 2.2: 实现 `rerank_supplementary_materials(raw_results: list) -> list` 函数，按 PRD §4.1.1 的精排优先级权重计算最终分数
  - [ ] 2.3: 过滤掉 `final_score < 0.70 * min_type_weight` 的结果
  - [ ] 2.4: 返回排序后 Top 5 结果

- [ ] Task 3: wikilink 格式化输出 (AC: #2)
  - [ ] 3.1: 在 skill workflow Step 7 中将搜索结果格式化为 Obsidian wikilink
  - [ ] 3.2: 根据 LanceDB 返回的 `block_id` 选择精度：有 heading → `[[file#heading]]`；有 block_id → `[[file#^block_id]]`；无 → `[[file]]`
  - [ ] 3.3: 输出格式：`1. 《标题》\n   "摘要片段..."\n   📄 source_file (相关度 X.XX)\n   🔗 [[wikilink]]`
  - [ ] 3.4: 主 LLM 回答与补充材料之间用 `---` 分隔

- [ ] Task 4: 降级处理 (AC: #5)
  - [ ] 4.1: 在 `search_vault_notes` 调用处捕获连接异常和空结果
  - [ ] 4.2: 异常时跳过补充材料展示，主对话正常继续
  - [ ] 4.3: 索引为空时显示"暂无补充材料"提示

- [ ] Task 5: 测试 (AC: #1~#5)
  - [ ] 5.1: 单元测试 `rerank_supplementary_materials`：权重计算、过滤、排序
  - [ ] 5.2: 单元测试 wikilink 格式化：三种精度级别
  - [ ] 5.3: 集成测试：完整搜索→精排→显示流程
  - [ ] 5.4: 性能测试：单文件增量索引 < 500ms

## Dev Notes

- **已有实现**: `backend/app/services/lancedb_index_service.py` 提供增量索引；`backend/app/services/react_agent.py` (line 55-137) 提供 `search_vault_notes` MCP 工具；`backend/app/services/tool_executor.py` (line 60-124) 提供 LanceDB hybrid 搜索
- **bge-m3 模型**: 需要 Ollama 已安装且 `ollama pull bge-m3` 完成
- **Anchor PRD 引用**: §4.1.1 补充学习材料显示 (line 3707-3877)，含精排权重定义和 wikilink 三级精度
- **学习科学依据**: Elaborative Interrogation (Pressley 1987, d=0.80) + Interleaving (Rohrer 2015, d=0.40) + Spaced Retrieval (Karpicke 2012)

### Project Structure Notes

```
backend/app/services/
  supplementary_reranker.py       # 新增：精排服务
  lancedb_index_service.py        # 已有：增量索引（无需修改）
  react_agent.py                  # 已有：search_vault_notes MCP（无需修改）
  tool_executor.py                # 已有：LanceDB hybrid 搜索（无需修改）
backend/tests/unit/
  test_supplementary_reranker.py  # 新增
```

### References

- PRD §4.1.1 补充学习材料: `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md` (line 3707-3877)
- LanceDB 已有实现: `backend/app/services/lancedb_index_service.py`
- search_vault_notes MCP: `backend/app/services/react_agent.py` (line 55-137)

## UAT Script

> 1. 确保 Ollama 运行中，bge-m3 模型已加载
> 2. 确保后端已完成 vault 初次索引（`POST /api/v1/metadata/index/vault`）
> 3. 打开 `wiki/concepts/admissibility.md`，启动 AI 对话
> 4. 提问："admissibility 的证明是怎么做的？"
> 5. 验证 AI 回答下方出现 `---` 分隔线和补充材料列表
> 6. 验证每条材料有标题、摘要、相关度分数和可点击 wikilink
> 7. 点击其中一个 wikilink，验证跳转到对应笔记的正确位置

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 精排权重计算 | unit | `pytest tests/unit/test_supplementary_reranker.py -x` | 全部通过 |
| wikilink 格式化 | unit | `pytest tests/unit/test_supplementary_reranker.py::test_wikilink_format -x` | 三种精度正确 |
| 增量索引性能 | perf | `pytest tests/perf/test_lancedb_index.py --timeout=5` | < 500ms/file |
| 端到端搜索 | integration | `pytest tests/integration/test_supplementary_search.py -x` | Top 5 结果正确排序 |

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
