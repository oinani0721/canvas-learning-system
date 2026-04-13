---
story_id: "3.5"
epic_id: "3"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P2"
estimate_hours: 4
depends_on: ["3.2"]
blocks: []
trace:
  - "FR-KG-08"
  - "FR-KG-09"
---

# Story 3.5: KG 健康检查 + 图片入图

Status: ready-for-dev

## Story

As a 学习者,
I want 定期检查知识图谱健康状况并将图片内容纳入图谱上下文,
So that 图谱结构健康且多模态内容可被 AI 检索使用。

## Acceptance Criteria

1. **Given** 学习者触发健康检查（`/graphify ./wiki --health-check`）
   **When** 系统扫描 Graphify 索引（graph.json）
   **Then** 报告包含以下检查项：
   - 孤立节点列表（无 Edge 的 wiki/concepts/*.md 文件）
   - 矛盾关系列表（如 A depends_on B 且 B depends_on A 形成循环依赖）
   - 置信度分布（EXTRACTED / INFERRED / AMBIGUOUS 各占百分比）
   **And** 生成 `outputs/graphify-out/health-report-<date>.md` 可读报告

2. **Given** 健康检查完成
   **When** AMBIGUOUS 比例 > 20%
   **Then** 系统发出警告"wiki 质量下降，建议审查 AMBIGUOUS 节点"
   **And** 列出 AMBIGUOUS 节点的文件路径供学习者逐个审查

3. **Given** 健康检查发现孤立节点
   **When** 报告生成
   **Then** 对每个孤立节点建议操作：
   - "建议为 [[<slug>]] 添加关系（`/edge_discuss`）"
   - "或考虑合并到相近概念"
   **And** 按创建时间排序（最旧的孤立节点优先处理）

4. **Given** 笔记中嵌入了图片（`![[image.png]]` 或 `![alt](image.png)`）
   **When** AI 识别图片内容（通过 Claudian 的 Vision API）
   **Then** 识别出的概念信息存储为 `image_context` 字段附加到所在笔记的 frontmatter
   **And** 图片中的概念可作为知识图谱上下文被后续对话和出题使用
   **And** 图片识别结果不替代手写内容，仅作为补充上下文

5. **Given** 图片识别过程
   **When** Vision API 不可用或图片无法解析
   **Then** 系统跳过该图片，记录警告日志
   **And** 不影响其他图片和文本内容的正常处理

## Tasks / Subtasks

- [ ] Task 1: 健康检查命令实现 (AC: #1, #2, #3)
  - [ ] 1.1: 实现 `/graphify --health-check` 命令扩展（或独立 skill），读取 `outputs/graphify-out/graph.json`
  - [ ] 1.2: 实现孤立节点检测：遍历 graph.json nodes，找出不在任何 edge 中出现的节点
  - [ ] 1.3: 实现矛盾关系检测：遍历 graph.json edges，找出 A→B 和 B→A 都存在且关系类型相同的循环
  - [ ] 1.4: 实现置信度分布统计：计算 EXTRACTED / INFERRED / AMBIGUOUS 三类占比
  - [ ] 1.5: 生成 `outputs/graphify-out/health-report-<YYYY-MM-DD>.md` 报告，包含三项检查结果 + 建议操作
  - [ ] 1.6: AMBIGUOUS > 20% 时在报告头部插入警告 callout

- [ ] Task 2: 孤立节点建议操作 (AC: #3)
  - [ ] 2.1: 对每个孤立节点生成建议文本："建议为 [[<slug>]] 添加关系（`/edge_discuss`）"
  - [ ] 2.2: 孤立节点按创建时间排序（从 frontmatter created_at 或文件 mtime 读取）
  - [ ] 2.3: 在报告中分组展示：`## 孤立节点（需要关系）` 段落

- [ ] Task 3: 图片内容识别与入图 (AC: #4, #5)
  - [ ] 3.1: 实现图片嵌入检测：正则匹配 `![[*.png]]` / `![[*.jpg]]` / `![alt](path)` 语法
  - [ ] 3.2: 对检测到的图片调用 Claudian Vision API（Claude 3.5 multimodal），提取图片中的概念关键词和描述
  - [ ] 3.3: 将识别结果存储到所在笔记 frontmatter 的 `image_context` 字段（列表格式，每项含 image_file / concepts / description）
  - [ ] 3.4: 识别结果标记为 `confidence: INFERRED`（图片识别非原文提取）
  - [ ] 3.5: Vision API 不可用或图片解析失败时跳过并记录 structlog 警告

- [ ] Task 4: 测试 (AC: #1~#5)
  - [ ] 4.1: 单元测试孤立节点检测：有 Edge 和无 Edge 节点正确分类
  - [ ] 4.2: 单元测试矛盾关系检测：循环依赖正确识别
  - [ ] 4.3: 单元测试置信度分布：百分比计算正确、AMBIGUOUS > 20% 触发警告
  - [ ] 4.4: 单元测试图片识别：正则匹配、Vision API 调用、frontmatter 存储
  - [ ] 4.5: 降级测试：Vision API 不可用时跳过不崩溃

## Dev Notes

- **核心依赖**: Story 3.2（Graphify）提供 `outputs/graphify-out/graph.json` 作为健康检查的输入
- **Anchor PRD 引用**: §6.7 定期健康检查 (line 6147-6158) 定义了三项检查内容和 AMBIGUOUS 20% 阈值
- **Karpathy 方法论**: 定期用 LLM 扫描 vault 检测不一致是 Karpathy LLM Wiki 的核心实践
- **图片识别**: 使用 Claudian 的 Vision API（Claude 3.5 multimodal），不引入额外的图片处理依赖
- **频率**: 健康检查是手动触发（非自动定时），建议每周一次
- **structlog 日志**: 所有检查步骤使用 `structlog.get_logger(__name__)` 记录

### Project Structure Notes

```
outputs/graphify-out/
  health-report-<date>.md            # 新增：健康检查报告
  graph.json                         # 读取：Graphify 生成的图谱（Story 3.2）
wiki/concepts/
  *.md                               # 修改：追加 image_context frontmatter 字段
```

### References

- Anchor PRD §6.7 健康检查: `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md` (line 6147-6158)
- BMAD PRD FR-KG-08, FR-KG-09: `_bmad-output/planning-artifacts/prd.md` (line 418-419)
- Story 3.2 Graphify: `_bmad-output/implementation-artifacts/epic-3/3-2-graphify-relation-extraction.md`
- Karpathy LLM Wiki 方法论: vault 定期一致性检查

## UAT Script

> 1. 确保已运行过 `/graphify ./wiki` 生成 graph.json
> 2. 运行 `/graphify ./wiki --health-check`
> 3. 验证 `outputs/graphify-out/health-report-<today>.md` 已生成
> 4. 验证报告包含：孤立节点列表 + 矛盾关系列表 + 置信度分布
> 5. 如有孤立节点，验证建议操作文本正确（含 `[[slug]]` wikilink）
> 6. 在某个笔记中嵌入一张图片（`![[test-diagram.png]]`），重新运行健康检查
> 7. 验证该笔记 frontmatter 中出现 `image_context` 字段，包含图片中识别的概念

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| 孤立节点检测 | unit | `pytest tests/unit/test_kg_health.py::test_orphan_detection -x` | 正确分类有/无 Edge |
| 矛盾关系检测 | unit | `pytest tests/unit/test_kg_health.py::test_contradiction_detection -x` | 循环依赖被识别 |
| 置信度分布 | unit | `pytest tests/unit/test_kg_health.py::test_confidence_distribution -x` | 百分比正确 |
| AMBIGUOUS 警告 | unit | `pytest tests/unit/test_kg_health.py::test_ambiguous_warning -x` | > 20% 触发警告 |
| 图片识别 | integration | `pytest tests/integration/test_image_recognition.py -x` | image_context 字段正确 |
| Vision API 降级 | integration | `pytest tests/integration/test_image_recognition.py::test_api_unavailable -x` | 跳过不崩溃 |

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
