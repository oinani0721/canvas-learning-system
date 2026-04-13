---
story_id: "3.2"
epic_id: "3"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P1"
estimate_hours: 10
depends_on: ["3.1"]
blocks: ["3.5"]
trace:
  - "FR-KG-03"
  - "FR-KG-05"
---

# Story 3.2: Graphify 关系提取 + 置信度

Status: ready-for-dev

## Story

As a 系统,
I want 通过 Graphify 从笔记中自动提取概念关系并生成独立的 AI 检索索引,
So that AI 有 71x token 压缩的知识图谱检索索引，且不修改用户的双向链接。

## Acceptance Criteria

1. **Given** 学习者触发 Graphify 索引（`/graphify ./wiki`）
   **When** Graphify 7 层管道处理 wiki/ 目录
   **Then** 生成独立的 `outputs/graphify-out/graph.json`（包含 nodes / edges / clusters）
   **And** 生成 `outputs/graphify-out/GRAPH_REPORT.md` 可读报告
   **And** 不修改用户的任何 wikilink 文件

2. **Given** Graphify 处理完成
   **When** 检查 graph.json 中的每个概念
   **Then** 每个概念标注三级置信度：EXTRACTED（明确出现在原文）/ INFERRED（LLM 推断但无原文）/ AMBIGUOUS（多义或不确定）
   **And** 置信度直接映射到 `wiki/concepts/*.md` 的 frontmatter `confidence` 字段

3. **Given** vault 中约有 100 个 wiki 文件
   **When** 执行全量索引
   **Then** 索引完成时间 < 30s（NFR-PERF）
   **And** 增量索引（仅处理变更文件）时间按比例缩短

4. **Given** graph.json 已生成
   **When** 其他系统组件查询图谱
   **Then** 可通过 graph.json 的 edges 数组获取任意概念的关系列表
   **And** 可通过 clusters 数组获取 Leiden 社区检测的聚类结果
   **And** 查询响应 < 100ms（内存中 JSON 解析）

5. **Given** Graphify 处理过程中 LLM 服务中断
   **When** 7 层管道某一层失败
   **Then** 已完成层的结果保留，失败层记录错误日志
   **And** 系统通知学习者"Graphify 索引部分完成，N 个文件未处理"
   **And** 下次运行时自动补充未处理的文件

## Tasks / Subtasks

- [ ] Task 1: Graphify 安装与配置 (AC: #1)
  - [ ] 1.1: 安装 `graphifyy` PyPI 包（`pip install graphifyy`）并验证版本 >= 0.3.17
  - [ ] 1.2: 运行 `graphify install` 在 vault 中安装 `.claude/skills/graphify/SKILL.md`
  - [ ] 1.3: 运行 `graphify claude install` 注入 CLAUDE.md 规范
  - [ ] 1.4: 验证安装完整性：skill 文件存在 + CLAUDE.md 末尾有 Graphify 区块

- [ ] Task 2: `/graphify` 命令集成与 7 层管道配置 (AC: #1, #3)
  - [ ] 2.1: 配置 `/graphify ./wiki` 命令，指定输出目录为 `outputs/graphify-out/`
  - [ ] 2.2: 验证 7 层管道完整执行：File Discovery → Content Extraction → Entity Detection → Relation Extraction → Leiden Clustering → Confidence Scoring → Graph Output
  - [ ] 2.3: 配置只读约束：Graphify 输出到 `outputs/graphify-out/` 目录，禁止修改 `wiki/` 下的任何文件
  - [ ] 2.4: 添加性能计时日志，记录每层管道耗时

- [ ] Task 3: 三级置信度映射与 frontmatter 同步 (AC: #2)
  - [ ] 3.1: 实现置信度映射逻辑：读取 `graph.json` 中每个节点的 confidence 字段
  - [ ] 3.2: 同步到 `wiki/concepts/*.md` 的 frontmatter `confidence` 字段（EXTRACTED / INFERRED / AMBIGUOUS）
  - [ ] 3.3: 同步时仅更新 confidence 字段，不修改其他 frontmatter 或 body 内容
  - [ ] 3.4: 对于 graph.json 中 INFERRED 的新概念，记录日志但不自动创建 wiki 文件（需用户通过 `/extract_node` 确认）

- [ ] Task 4: 性能优化与增量索引 (AC: #3, #4)
  - [ ] 4.1: 实现增量索引检测：比对文件 mtime 与上次索引时间戳，仅处理变更文件
  - [ ] 4.2: 性能基准测试：100 文件 vault 全量索引 < 30s
  - [ ] 4.3: 实现 graph.json 内存缓存：首次加载后缓存在内存中，查询响应 < 100ms
  - [ ] 4.4: 配置 Graphify 的 LLM 并发参数（如果支持），优化索引速度

- [ ] Task 5: 降级处理与错误恢复 (AC: #5)
  - [ ] 5.1: 实现管道层级错误隔离：每层 try-catch，失败层记录到 `outputs/graphify-out/errors.log`
  - [ ] 5.2: 保留已完成层的部分结果（如 File Discovery + Content Extraction 完成但 Entity Detection 失败，保留前两层数据）
  - [ ] 5.3: 实现未处理文件列表持久化（`outputs/graphify-out/pending.json`），下次运行时自动补充
  - [ ] 5.4: 降级通知：在 GRAPH_REPORT.md 中标注失败层和未处理文件数量

- [ ] Task 6: 测试 (AC: #1~#5)
  - [ ] 6.1: 单元测试置信度映射：EXTRACTED / INFERRED / AMBIGUOUS 正确同步到 frontmatter
  - [ ] 6.2: 集成测试：完整 `/graphify ./wiki` 生成 graph.json + GRAPH_REPORT.md
  - [ ] 6.3: 性能测试：100 文件全量索引 < 30s、graph.json 查询 < 100ms
  - [ ] 6.4: 降级测试：模拟 LLM 中断后部分结果保留和增量补充

## Dev Notes

- **核心依赖**: Story 3.1（概念提取）提供 `wiki/concepts/*.md` 文件作为 Graphify 的输入
- **Anchor PRD 引用**: §6 Graphify 集成 (line 5815-6158) 定义了安装步骤、7 层管道、三级置信度、71x token 减少和健康检查
- **Graphify 是外部工具**: PyPI `graphifyy` v0.3.17，13.7k stars，7 层管道，三级置信度（EXTRACTED/INFERRED/AMBIGUOUS），71x token 减少，Leiden 聚类
- **只读约束**: Graphify 生成 `outputs/graphify-out/graph.json`，不修改 `wiki/` 下的文件。置信度同步是本 Story 额外实现的逻辑
- **graph.json 结构**: `{ nodes: [{id, type, confidence}], edges: [{from, to, relation, confidence}], clusters: [{id, nodes, label}] }`
- **LanceDB 互补**: Graphify 负责关系图谱（71x token 压缩），LanceDB + bge-m3 负责向量检索（句子级精确）。两者完全互补，不替代

### Project Structure Notes

```
outputs/graphify-out/
  graph.json                         # 新增：Graphify 生成的知识图谱
  GRAPH_REPORT.md                    # 新增：可读报告
  errors.log                         # 新增：错误日志
  pending.json                       # 新增：待处理文件列表
.claude/skills/graphify/
  SKILL.md                           # 新增：Graphify skill 定义（由 graphify install 创建）
```

### References

- Anchor PRD §6 Graphify 集成: `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md` (line 5815-6158)
- BMAD PRD FR-KG-03, FR-KG-05: `_bmad-output/planning-artifacts/prd.md` (line 413, 415)
- Graphify GitHub: https://github.com/safishamsi/graphify
- NFR-PERF 性能指标: BMAD PRD `_bmad-output/planning-artifacts/prd.md` (line 526-537)
- Story 3.1 概念提取: `_bmad-output/implementation-artifacts/epic-3/3-1-concept-extraction-wikilink.md`

## UAT Script

> 1. 确保 vault 中 `wiki/concepts/` 下有至少 5 个概念文件
> 2. 在终端运行 `/graphify ./wiki`
> 3. 验证 `outputs/graphify-out/graph.json` 已生成，包含 nodes / edges / clusters 三个数组
> 4. 验证每个 node 都有 confidence 字段（EXTRACTED / INFERRED / AMBIGUOUS 之一）
> 5. 验证 `outputs/graphify-out/GRAPH_REPORT.md` 已生成，可读
> 6. 验证 `wiki/concepts/*.md` 的 frontmatter confidence 字段已同步更新
> 7. 验证 wiki/ 下的文件内容（除 confidence 字段外）未被修改
> 8. 记录全量索引耗时，确认 < 30s

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| Graphify 安装 | smoke | `python -c "import graphifyy; print(graphifyy.__version__)"` | 版本 >= 0.3.17 |
| graph.json 生成 | integration | `pytest tests/integration/test_graphify_pipeline.py::test_full_pipeline -x` | graph.json 包含 nodes + edges + clusters |
| 置信度映射 | unit | `pytest tests/unit/test_graphify_confidence.py -x` | 三级置信度正确映射 |
| 只读约束 | integration | `pytest tests/integration/test_graphify_pipeline.py::test_no_wiki_modification -x` | wiki/ 文件 hash 不变 |
| 全量索引性能 | perf | `pytest tests/perf/test_graphify_perf.py --timeout=60` | < 30s for 100 files |
| 降级恢复 | integration | `pytest tests/integration/test_graphify_degradation.py -x` | 部分结果保留 + pending.json 生成 |

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
