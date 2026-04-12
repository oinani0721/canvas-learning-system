---
doc_type: story
story_id: "7.5"
epic_id: "EPIC-7"
prd_id: "PRD14"
status: ready-for-dev
priority: "P1"
estimate_hours: 4
depends_on: ["7.1"]
blocks: []
trace:
  decisions: []
  bugs: []
---

# Story 7.5: 单概念详细档案

## Story

As a 学习者,
I want 查看单个概念的详细档案,
so that 我可以深入了解某个概念的学习历程和掌握度变化。

## Acceptance Criteria

1. **Given** 学习者在 Dashboard 或任意笔记中点击某个概念名
   **When** 档案页面加载
   **Then** 展示概念基础信息：概念名、创建日期（created_at）、所属领域（domain/tags）

2. **Given** 档案页面加载
   **When** 掌握度曲线区域渲染
   **Then** 展示 BKT mastery_score 随时间的变化折线图（时间轴 x，mastery_score y）
   **And** 折线图包含所有历史复习记录的数据点（不限条数）
   **And** 当历史记录 < 2 条时，显示提示"数据点不足，需要更多考察记录"而非空图

3. **Given** 档案页面加载
   **When** 复习记录区域渲染
   **Then** 展示历次考察记录表格：日期、题目简述（或题目 ID）、得分（0–100）、使用提示数
   **And** 表格按日期倒序排列（最新记录在最上方）
   **And** 最多展示最近 20 条，超出部分提供"查看更多"展开选项

4. **Given** 档案页面加载
   **When** 误解记录区域渲染
   **Then** 展示历史错误分类列表：错误类型（来自 error_history）、首次出现日期、是否已修正（corrected: bool）
   **And** 未修正的错误（corrected: false）用红色标注
   **And** 已修正的错误用删除线或灰色标注

5. **Given** 档案页面加载
   **When** 关联概念区域渲染
   **Then** 展示来自 Graphify 知识图谱的关系：前置概念（prerequisite）、关联概念（related）、对比概念（contrasts_with）
   **And** 每个关联概念名可点击跳转到对应笔记
   **And** 若 Graphify 未建立任何关系（新概念），显示"暂无关联概念"

6. **Given** 档案页面加载
   **When** FSRS 参数区域渲染
   **Then** 展示当前 FSRS 参数：difficulty（难度系数）、stability（记忆稳定性，单位天）、due_date（下次复习日期）
   **And** 以用户友好格式展示：difficulty 显示为百分比，stability 显示为"约 N 天"，due_date 显示为"N 天后"或"已过期 N 天"

## Tasks / Subtasks

- [ ] Task 1: 设计档案页面结构 (AC: #1, #2, #3, #4, #5, #6)
  - [ ] 1.1 确定档案页面的实现方式：Dataview JS 内嵌于概念笔记（preferred）或独立档案笔记
  - [ ] 1.2 若内嵌于概念笔记：在笔记底部添加 ````dataviewjs` 块渲染所有档案区域
  - [ ] 1.3 定义档案页面六个区域的渲染顺序：基础信息 → 掌握度曲线 → 复习记录 → 误解记录 → 关联概念 → FSRS 参数

- [ ] Task 2: 实现基础信息区域 (AC: #1)
  - [ ] 2.1 从 frontmatter 读取：file.name（概念名）、created_at、domain/tags
  - [ ] 2.2 用 `dv.header(2, "概念档案")` 和 `dv.paragraph` 渲染基础信息

- [ ] Task 3: 实现掌握度曲线 (AC: #2)
  - [ ] 3.1 在 `backend/app/api/v1/endpoints/dashboard.py` 添加 `GET /api/v1/concepts/{concept_name}/history` 端点
  - [ ] 3.2 端点返回：`{data_points: [{date, mastery_score, quiz_result}], insufficient: bool}`
  - [ ] 3.3 在档案页面 Dataview JS 中调用端点，使用 Chart.js（或 Obsidian Charts 插件）渲染折线图
  - [ ] 3.4 历史记录 < 2 条时，渲染提示文字而非空图表

- [ ] Task 4: 实现复习记录表格 (AC: #3)
  - [ ] 4.1 从 frontmatter `error_history` 和考察记录中提取历次复习数据
  - [ ] 4.2 用 Dataview JS `dv.table` 渲染：日期 | 得分 | 使用提示数
  - [ ] 4.3 默认展示最近 20 条，用 `dv.el("details")` 包裹展开部分

- [ ] Task 5: 实现误解记录区域 (AC: #4)
  - [ ] 5.1 从 frontmatter `error_history` 提取错误分类列表
  - [ ] 5.2 未修正错误（corrected: false）渲染为红色文字
  - [ ] 5.3 已修正错误渲染为灰色 + 删除线（CSS: `text-decoration: line-through; color: gray`）
  - [ ] 5.4 `error_history` 为空时显示"暂无误解记录 — 继续保持！"

- [ ] Task 6: 实现关联概念区域 (AC: #5)
  - [ ] 6.1 在 `backend/app/api/v1/endpoints/dashboard.py` 添加 `GET /api/v1/concepts/{concept_name}/relations` 端点
  - [ ] 6.2 端点查询 Neo4j Graphify 图，返回：`{prerequisite: [...], related: [...], contrasts_with: [...]}`
  - [ ] 6.3 档案页面调用端点，用 `dv.fileLink(name)` 渲染可点击的关联概念列表
  - [ ] 6.4 三类关系分别用不同标签前缀标注（"前置:"/"关联:"/"对比:"）
  - [ ] 6.5 接口返回空数组时显示"暂无关联概念"

- [ ] Task 7: 实现 FSRS 参数区域 (AC: #6)
  - [ ] 7.1 从 frontmatter `fsrs_params` 读取：difficulty、stability、due_date
  - [ ] 7.2 difficulty 转换为百分比显示（×100 保留一位小数）
  - [ ] 7.3 stability 显示为"约 N 天"（Math.round）
  - [ ] 7.4 due_date 计算与今天的差值：正数显示"N 天后"，负数显示"已过期 N 天"，0 显示"今天"

- [ ] Task 8: 编写测试 (AC: #2, #3, #4, #5, #6)
  - [ ] 8.1 后端测试：`/api/v1/concepts/{name}/history` 返回正确数据点（按日期升序）
  - [ ] 8.2 后端测试：历史 < 2 条时返回 `insufficient: true`
  - [ ] 8.3 后端测试：`/api/v1/concepts/{name}/relations` 正确查询 Neo4j 并分类返回
  - [ ] 8.4 后端测试：概念无 Neo4j 节点时返回空数组（不报 404）
  - [ ] 8.5 单元测试：due_date 已过期时显示"已过期 N 天"（负差值处理正确）

## Dev Notes

- **FR32**：档案包含"5 信号 + Tips + 待纠正 + 相关 Edges"。5 信号即 mastery_score/BKT/FSRS/error_history/confidence_level；Tips 对应 FSRS 参数；待纠正对应 corrected:false 的 error_history；相关 Edges 对应 Graphify 关系
- **折线图方案**：
  - 首选：Obsidian Charts 插件（已在多 vault 验证），支持 `chart` 代码块语法
  - 备选：Dataview JS 动态生成 Chart.js canvas（需要额外插件 CustomJS 或 Dataview JS 直接 import）
  - 最简降级：Dataview table 列出时间序列（放弃图形化）
- **历史数据存储位置**：`error_history` 存在 frontmatter，但复习记录（date/score/hints）可能分散在多处。需在 Task 1.1 中明确数据来源，统一到 frontmatter 某个字段或外部 JSON
- **关联概念 API 依赖 Neo4j**：若 Graphify 未建立该节点关系，正常返回空数组；不应因为 Neo4j 查询失败而让整个档案页面崩溃（try/catch 降级）
- **FSRS difficulty 范围**：FSRS v5 中 difficulty ∈ [1, 10]，非 [0, 1]。转换为百分比时需除以 10（不是乘以 100）。实现前确认 `FRONTMATTER-SPEC.md` 中的存储格式

### Project Structure Notes

- 概念历史 API：`backend/app/api/v1/endpoints/dashboard.py`（追加端点）
- 概念关系 API：`backend/app/api/v1/endpoints/dashboard.py`（追加端点）或 `backend/app/api/v1/endpoints/graph.py`（如已存在）
- 档案内嵌模板：`vault/_templates/concept-profile-section.md`（可选，作为复用模板）

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-7.5] — AC 原始定义
- [Source: _bmad-output/planning-artifacts/prd.md#FR32] — FR32：单概念档案（5 信号 + Tips + 待纠正 + 相关 Edges）
- [Source: _bmad-output/implementation-artifacts/7-1-global-dashboard-dataview.md] — 三层布局（depends_on）
- [Source: docs/_meta/FRONTMATTER-SPEC.md] — fsrs_params/error_history/confidence_level 字段定义
- [Source: backend/app/services/rag_service.py] — 后端 service 风格参考

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证基础信息** (AC: #1)
   - 打开任意一个概念笔记（如"递归"）
   - 滚动到页面底部，应看到"概念档案"标题
   - 标题下方应显示：概念名、创建日期、所属领域
   - 如果底部没有档案区域，记录 Story 7.5

2. **验证掌握度曲线** (AC: #2)
   - 在档案区域找到"掌握度变化"图表
   - 如果你有超过 2 次考察记录，应看到折线图，x 轴是日期，y 轴是掌握度（0–1）
   - 如果只有 0–1 次考察，应看到提示文字而非空图
   - 如果有足够记录但只看到提示文字，记录 Story 7.5

3. **验证复习记录表格** (AC: #3)
   - 在档案区域找到"复习记录"表格
   - 表格应按日期倒序排列（最新记录在最上方）
   - 每行包含：日期、得分、使用提示次数
   - 如果顺序相反（最旧记录在上方），记录 Story 7.5

4. **验证误解记录** (AC: #4)
   - 在档案区域找到"误解记录"列表
   - 未修正的错误应以红色显示
   - 已修正的错误应以灰色显示（带删除线）
   - 没有任何错误记录时应显示"暂无误解记录"
   - 如果红色和灰色显示相反，记录 Story 7.5

5. **验证关联概念链接** (AC: #5)
   - 在档案区域找到"关联概念"区域
   - 应看到分类（前置/关联/对比）的概念列表，每个概念名可点击
   - 点击一个概念名，应跳转到对应笔记
   - 若无关联概念，显示"暂无关联概念"而非报错
   - 如果点击无反应或页面报错，记录 Story 7.5

6. **验证 FSRS 参数** (AC: #6)
   - 在档案区域找到"复习参数"区域
   - 应看到三个数据：难度（百分比形式）、记忆稳定性（X 天）、下次复习（X 天后或已过期）
   - 如果显示的是原始数字（如"difficulty: 0.32"）而非友好格式，记录 Story 7.5

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-7.5.1 | pytest | `.venv/bin/pytest tests/unit/test_concept_history_api.py -x -q` | 0 failed |
| CP-7.5.2 | pytest | `.venv/bin/pytest tests/unit/test_concept_relations_api.py -x -q` | 0 failed |
| CP-7.5.3 | pytest | `.venv/bin/pytest tests/unit/test_fsrs_display_format.py -x -q` | 0 failed |
| CP-7.5.4 | pytest | `.venv/bin/pytest tests/unit/test_due_date_relative.py -x -q` | 0 failed |

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

- EPIC: [[EPIC-7]]
- PRD: [[PRD14]]
- Depends on: [[7.1]]
