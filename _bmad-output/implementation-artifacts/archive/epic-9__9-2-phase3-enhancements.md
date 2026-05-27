---
story_id: "9.2"
epic_id: "9"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P2"
estimate_hours: 8
depends_on: ["5.2", "5.6"]
blocks: []
trace:
  - "FR-MAST-02"
  - "FR-EXAM-15"
  - "FR-KG-03"
---

# Story 9.2: Phase 3 持续改进

Status: ready-for-dev

## Story
As a 学习者,
I want FSRS 插件升级、校准投票改进和图谱聚类发现,
So that 学习系统随着使用越来越精确，推荐越来越准。

## Acceptance Criteria

### Enhancement A: SM-2 → FSRS 插件升级路径

1. **Given** Phase 2 中间隔复习使用 frontmatter FSRS 字段（手动计算）**When** Obsidian FSRS 社区插件稳定（>1000 下载 + 无 critical issue）**Then** 提供迁移路径：自动将现有 frontmatter fsrs_* 字段映射到插件原生格式 **And** 迁移脚本支持回滚（备份原 frontmatter）

2. **Given** FSRS 插件迁移完成 **When** 学习者使用间隔复习 **Then** 复习调度由插件原生管理（替代 Story 7.2 的手动计算）**And** Story 7.1 复习队列从插件 API 获取数据（替代 Dataview 查询 frontmatter）**And** 掌握度更新仍通过后端 mastery_service 统一管理

3. **Given** FSRS 社区插件尚未稳定 **When** 学习者继续使用系统 **Then** Phase 2 的 frontmatter 方案继续工作 **And** 不强制要求迁移 **And** 迁移脚本提供 dry-run 模式预览变更

### Enhancement B: 校准投票 few-shot 样本积累

4. **Given** 学习者在每次考察后进行校准投票（Story 5.6 "AI 评分合理/偏高/偏低"）**When** 投票数据积累超过 20 次 **Then** 系统从投票数据中提取 few-shot 样本：选取最近 5 次"AI 评分合理"的题目-回答-评分三元组 **And** 在后续评分 prompt 中注入这些 few-shot 样本以校准评分标准

5. **Given** few-shot 样本注入评分 prompt **When** AI 对新回答评分 **Then** 评分精度提升（投票中"合理"占比从初始 ~60% 提升到目标 ~80%）**And** few-shot 样本按 FIFO 更新（新投票替换最旧样本）

6. **Given** 投票数据不足 20 次 **When** 系统评分 **Then** 不注入 few-shot 样本（回退到 Story 4.6 的基线评分）**And** 不因数据不足导致评分质量下降

### Enhancement C: Graphify 聚类发现

7. **Given** 知识图谱中概念数量 > 50 **When** 学习者触发图谱分析（手动或每周自动）**Then** 使用 Graphify v0.3.17 的 community detection 算法识别概念聚类 **And** 每个聚类标注主题标签（基于聚类内概念名称的 LLM 摘要）

8. **Given** 聚类分析完成 **When** 结果展示在 Dashboard **Then** 新增一个"知识聚类"区域，显示发现的 N 个主题聚类 **And** 每个聚类显示概念数量、平均掌握度（处方性措辞）、建议行动 **And** 聚类内的概念间 Edge 密度作为"关联强度"指标

9. **Given** 概念数量 < 50 **When** 系统尝试聚类分析 **Then** 跳过分析并提示"概念数量不足，建议积累更多知识后再分析" **And** 不生成低质量的聚类结果

## Tasks / Subtasks

### Enhancement A Tasks

- [ ] Task 1: 编写 FSRS 插件兼容性评估文档 (AC: #1, #3)
  - [ ] 调研当前 Obsidian FSRS 插件状态（下载量、issue 数、API 稳定性）
  - [ ] 编写 frontmatter → 插件格式映射规则
  - [ ] 定义迁移触发条件（>1000 下载 + 无 critical issue）

- [ ] Task 2: 实现迁移脚本 (AC: #1, #2)
  - [ ] 脚本：遍历 wiki/concepts/ 的 frontmatter fsrs_* 字段
  - [ ] 映射到插件原生格式
  - [ ] 备份原 frontmatter（在 `outputs/fsrs-migration-backup/` 目录）
  - [ ] dry-run 模式：只报告变更不实际修改
  - [ ] 回滚功能：从备份恢复原 frontmatter

### Enhancement B Tasks

- [ ] Task 3: 实现 few-shot 样本提取 (AC: #4, #5, #6)
  - [ ] 从 frontmatter calibration_votes 数组过滤 vote="agree" 的记录
  - [ ] 选取最近 5 条作为 few-shot 样本
  - [ ] 样本格式：{question, answer, score, rubric_summary}
  - [ ] FIFO 更新逻辑

- [ ] Task 4: 实现 few-shot 注入评分 prompt (AC: #4, #5)
  - [ ] 在 `backend/app/services/scoring_service.py` 中扩展评分 prompt
  - [ ] 注入位置：system prompt 的 `[CALIBRATION_EXAMPLES]` 占位符
  - [ ] 阈值检查：< 20 次投票时跳过注入

### Enhancement C Tasks

- [ ] Task 5: 实现 Graphify 聚类调用 (AC: #7, #9)
  - [ ] 集成 Graphify v0.3.17 的 community detection API
  - [ ] 输入：知识图谱的节点和边（从 wiki/concepts/ 和 edges/ 构建）
  - [ ] 输出：聚类分配 + 聚类内密度
  - [ ] < 50 节点时跳过分析

- [ ] Task 6: 实现聚类主题标注 (AC: #7)
  - [ ] 用 LLM 对每个聚类内的概念名称做主题摘要
  - [ ] 结果存入 `outputs/cluster-analysis.json`

- [ ] Task 7: 实现 Dashboard 聚类展示 (AC: #8)
  - [ ] 在 wiki/dashboard.md 新增"知识聚类"区域
  - [ ] dataviewjs 读取 cluster-analysis.json
  - [ ] 每个聚类显示概念数 + 平均掌握度（处方性措辞）+ 建议行动

## Dev Notes

### Architecture
- 这是 Phase 3 的增强型 Story，三个 Enhancement 相互独立可并行实施
- Enhancement A 是纯迁移工作，不改变核心逻辑
- Enhancement B 是 scoring pipeline 的精度优化，基于真实用户反馈数据
- Enhancement C 是知识图谱的高级分析，依赖 Graphify 社区插件

### Enhancement Priority

| Enhancement | 价值 | 风险 | 建议顺序 |
|---|---|---|---|
| B: 校准投票 few-shot | 高（直接提升评分精度）| 低（纯 prompt 优化）| 第 1 |
| A: FSRS 插件迁移 | 中（依赖社区插件稳定性）| 中（迁移可能有边界情况）| 第 2 |
| C: 聚类发现 | 中（增值分析）| 中（Graphify API 集成）| 第 3 |

### File Paths
- FSRS 迁移脚本：`scripts/fsrs_migration.py`（新建）
- 迁移备份：`outputs/fsrs-migration-backup/`
- 评分服务扩展：`backend/app/services/scoring_service.py`（few-shot 注入）
- 校准投票数据：`wiki/concepts/*.md`（frontmatter calibration_votes）
- Graphify 集成：`backend/app/services/graphify_service.py`（聚类分析）
- 聚类分析结果：`outputs/cluster-analysis.json`
- Dashboard 扩展：`wiki/dashboard.md`（知识聚类区域）

### Testing
- Enhancement A: 迁移脚本的 dry-run 正确性 + 回滚正确性
- Enhancement B: few-shot 样本提取 + prompt 注入 + 阈值检查
- Enhancement C: 聚类结果的合理性（已知图结构的预期聚类）

### References
- **From PRD**: §1.8 间隔复习 — FSRS 升级路径
- **From PRD**: §2.7 校准投票 (line 2440-2530)
- FR-MAST-02: FSRS 最优复习间隔
- FR-EXAM-15: 考后校准投票
- FR-KG-03: Graphify 概念关系提取
- FSRS 算法：open-spaced-repetition/fsrs4anki
- Graphify v0.3.17：https://github.com/HEmile/juggl / Graphify plugin
- Story 5.2: 掌握度更新服务（FSRS 依赖）
- Story 5.6: 校准投票记录（数据来源）

## UAT Script

### Enhancement A
> 1. 确保至少 5 个概念有 fsrs_* frontmatter 字段
> 2. 运行迁移脚本 dry-run 模式：`python scripts/fsrs_migration.py --dry-run`
> 3. 确认输出的变更预览合理
> 4. 运行实际迁移：`python scripts/fsrs_migration.py --migrate`
> 5. 确认 frontmatter 已更新
> 6. 运行回滚：`python scripts/fsrs_migration.py --rollback`
> 7. 确认 frontmatter 恢复原样

### Enhancement B
> 1. 在 5+ 次考察中投票"AI 评分合理"
> 2. 积累到 20 次后，开始新一次考察
> 3. 确认评分 prompt 中包含 few-shot 样本
> 4. 投票"AI 评分合理"的占比应趋向 ~80%

### Enhancement C
> 1. 确保 vault 中有 50+ 概念节点
> 2. 触发聚类分析
> 3. 在 Dashboard 看到"知识聚类"区域，显示 N 个主题聚类
> 4. 每个聚类有主题标签、概念数、平均掌握度（处方性措辞）
> 5. 概念 < 50 时触发分析，看到"概念数量不足"提示

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| FSRS 迁移 dry-run | unit | `pytest tests/unit/test_fsrs_migration.py -x` | 0 failures |
| FSRS 回滚 | unit | `pytest tests/unit/test_fsrs_rollback.py -x` | 0 failures |
| Few-shot 提取 | unit | `pytest tests/unit/test_calibration_fewshot.py -x` | 0 failures |
| Few-shot 阈值 | unit | `pytest tests/unit/test_fewshot_threshold.py -x` | 0 failures |
| 聚类分析 | unit | `pytest tests/unit/test_graphify_cluster.py -x` | 0 failures |
| 聚类阈值 | unit | `pytest tests/unit/test_cluster_min_nodes.py -x` | 0 failures |

## User Feedback & Changes

### Feedback Log
(to be filled during/after implementation)

### Deviation Notes
(to be filled if implementation deviates from spec)

## Dev Agent Record

### Agent Model Used
(to be filled by Dev agent)

### Debug Log References
(to be filled by Dev agent)

### Completion Notes List
(to be filled by Dev agent)

### File List
(to be filled by Dev agent)
