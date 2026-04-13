---
doc_type: story
story_id: "7.3"
aliases: ["7.3"]
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
# Story 7.3: 元认知 2x2 校准矩阵

## Story

As a 学习者,
I want 查看元认知 2x2 校准矩阵,
so that 我可以了解哪些概念我以为懂了但实际没懂（盲点），哪些概念我以为不懂但实际掌握了。

## Acceptance Criteria

1. **Given** 学习者有足够的校准数据（至少 5 次自评+实际评分记录）
   **When** 学习者查看 2x2 矩阵
   **Then** 展示四个象限，每个象限包含落入该区域的概念列表：
   - 象限 Q1：高自评 + 高实际（知道自己知道）— 绿色
   - 象限 Q2：低自评 + 高实际（不知道自己知道）— 蓝色
   - 象限 Q3：低自评 + 低实际（知道自己不知道）— 黄色
   - 象限 Q4：高自评 + 低实际（不知道自己不知道 / 盲点）— 红色高亮

2. **Given** 某个概念落入 Q4（高自评+低实际，盲点）
   **When** 矩阵渲染
   **Then** 该象限用红色背景高亮警告
   **And** Q4 象限内的概念名以警告样式标注（如加粗红字或⚠️前缀）

3. **Given** 学习者校准数据不足 5 条
   **When** 学习者查看矩阵
   **Then** 展示提示："校准数据不足——需要至少 5 次含自评的考察记录（当前：N 次）"
   **And** 不展示空矩阵（避免误导）

4. **Given** 概念有多条历史记录
   **When** 计算该概念的象限归属
   **Then** 使用最近 10 次考察的平均值（自评平均和实际得分平均）
   **And** 不使用单次记录（避免偶然误差）

5. **Given** 学习者点击矩阵中某个概念名
   **When** 点击发生
   **Then** 跳转到该概念的笔记（Obsidian 内部链接）
   **And** 不离开当前 Dashboard 视图（在新标签页或侧边栏打开）

## Tasks / Subtasks

- [ ] Task 1: 定义校准数据结构 (AC: #1, #4)
  - [ ] 1.1 确认 frontmatter 中 `confidence_level` 字段格式（自评：0.0–1.0 或 low/medium/high 枚举）
  - [ ] 1.2 确认 `error_history` 中包含自评记录（或新增 `self_assessment_history` 字段）
  - [ ] 1.3 在 `backend/app/services/dashboard_service.py` 实现 `classify_calibration(concept_pages)` 函数
  - [ ] 1.4 分类逻辑：自评阈值 0.5（低/高分界），实际 mastery_score 阈值 0.6（低/高分界）
  - [ ] 1.5 取最近 10 次记录的平均值，不足 10 条时取全部

- [ ] Task 2: 后端 API 端点 (AC: #1, #3)
  - [ ] 2.1 在 `backend/app/api/v1/endpoints/dashboard.py` 添加 `GET /api/v1/dashboard/calibration-matrix` 端点
  - [ ] 2.2 返回结构：`{total_records, q1: [...], q2: [...], q3: [...], q4: [...], insufficient_data: bool}`
  - [ ] 2.3 当 total_records < 5 时，设置 `insufficient_data: true`，四个象限返回空数组
  - [ ] 2.4 概念对象结构：`{name, file_path, self_assessment_avg, mastery_score_avg, record_count}`

- [ ] Task 3: 在 Dashboard 笔记中渲染 2x2 矩阵 (AC: #1, #2, #4, #5)
  - [ ] 3.1 在 `vault/wiki/dashboard.md` 的 Dataview JS 中调用校准矩阵 API 或本地计算
  - [ ] 3.2 用 Dataview JS `dv.el` 渲染 2x2 HTML 表格：2 列（自评高/低）× 2 行（实际高/低）
  - [ ] 3.3 Q4（高自评+低实际）单元格设置红色背景：`style="background: #ffd5d5"`
  - [ ] 3.4 Q4 内概念名前添加 ⚠️ 前缀
  - [ ] 3.5 概念名渲染为 Obsidian 内部链接格式 `[[概念名]]`（Dataview 会自动转为可点击链接）

- [ ] Task 4: 处理数据不足情况 (AC: #3)
  - [ ] 4.1 当 API 返回 `insufficient_data: true` 时，渲染提示文字而非矩阵
  - [ ] 4.2 提示中显示当前记录数 N（"当前：N 次"）
  - [ ] 4.3 提示中包含操作引导："完成含自评的考察以积累数据"

- [ ] Task 5: 编写测试 (AC: #1, #2, #3, #4)
  - [ ] 5.1 单元测试：高自评+低实际 → 归类 Q4（盲点检测正确）
  - [ ] 5.2 单元测试：低自评+高实际 → 归类 Q2
  - [ ] 5.3 单元测试：多条记录取平均值（测试 10 条 vs 3 条边界）
  - [ ] 5.4 API 测试：records < 5 时返回 `insufficient_data: true`
  - [ ] 5.5 API 测试：records >= 5 时四象限均有数据（使用测试 fixture）

## Dev Notes

- **FR30**：2x2 矩阵是 Dunning-Kruger 元认知可视化的经典形式。核心价值是暴露盲点（Q4），学习者通常对此区域最缺乏意识
- **自评字段映射**：
  - 若 `confidence_level` 为枚举（low/medium/high），映射为 0.2/0.5/0.8 数值
  - 若为 0.0–1.0 浮点，直接使用
  - 若字段缺失，该概念不计入矩阵计算（不强行分类）
- **阈值说明**：自评 ≥ 0.5 = "高自评"，mastery_score ≥ 0.6 = "高实际"。这两个阈值与 Story 7.1/7.2 的红/绿区阈值不同（有意为之：校准矩阵使用中性分界线，不叠加主观判断）
- **Dataview HTML 渲染**：Obsidian Dataview JS 支持 `dv.el("div", content, {attr: {style: "..."}})` 注入 HTML，可实现红色背景
- **`[[wikilink]]` 限制**：Dataview JS 中直接嵌入 wikilink 格式在 table 里有效，但需用 `dv.fileLink(name)` 而非字符串拼接

### Project Structure Notes

- 校准矩阵服务：`backend/app/services/dashboard_service.py`（追加到 Story 7.2 的同一文件）
- 校准矩阵 API：`backend/app/api/v1/endpoints/dashboard.py`（追加端点）
- Dashboard 笔记：`vault/wiki/dashboard.md`（追加矩阵区块）

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-7.3] — AC 原始定义
- [Source: _bmad-output/planning-artifacts/prd.md#FR30] — FR30：2x2 校准矩阵
- [Source: _bmad-output/implementation-artifacts/7-1-global-dashboard-dataview.md] — 三层布局（depends_on）
- [Source: docs/_meta/FRONTMATTER-SPEC.md] — confidence_level 和 error_history 字段定义

## UAT Script

> Non-technical user validation: no code terminology, only describe what to click and what to see.

1. **验证矩阵四象限** (AC: #1)
   - 打开 Dashboard（`wiki/dashboard.md`），向下滚动找到"元认知校准矩阵"区域
   - 应看到一个 2×2 的表格，包含四个区域：
     - 左上：绿色（你自评高，实际也高）
     - 右上：蓝色（你自评低，但实际掌握好）
     - 左下：黄色（你自评低，实际也低，你清楚自己不会）
     - 右下：红色（你自评高，但实际掌握差——这是盲点！）
   - 如果表格只有两列而不是 2×2 格，记录 Story 7.3

2. **验证盲点高亮** (AC: #2)
   - 找到右下角的红色区域（盲点）
   - 这个区域应有明显的红色背景
   - 区域内的概念名前面应有 ⚠️ 符号
   - 如果红色区域没有突出显示，记录 Story 7.3

3. **验证概念链接** (AC: #5)
   - 点击矩阵中任意一个概念名
   - 应在侧边栏或新标签页打开对应的概念笔记
   - 当前 Dashboard 页面应保持可见（不跳转离开）
   - 如果 Dashboard 被关闭或概念名不可点击，记录 Story 7.3

4. **验证数据不足提示** (AC: #3)
   - 仅限新安装或考察记录极少的情况
   - 矩阵区域应显示提示文字，包含"当前：N 次"
   - 不应显示空的 2×2 表格
   - 如果显示空表格而没有提示，记录 Story 7.3

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-7.3.1 | pytest | `.venv/bin/pytest tests/unit/test_calibration_classify.py -x -q` | 0 failed |
| CP-7.3.2 | pytest | `.venv/bin/pytest tests/unit/test_calibration_average.py -x -q` | 0 failed |
| CP-7.3.3 | pytest | `.venv/bin/pytest tests/unit/test_calibration_api_insufficient.py -x -q` | 0 failed |

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
