---
story_id: "1.9"
epic_id: "1"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 6
depends_on: ["1.8"]
blocks: []
trace:
  - "FR-SYS-01"
  - "FR-DATA-01"
---

# Story 1.9: LanceDB vault_id 命名空间隔离

Status: ready-for-dev

## Story

As a 学习者,
I want 每个 vault 的向量索引数据完全隔离（CS188 的笔记不会混入 CS61B 的搜索结果）,
So that 我在 CS61B 里搜"链表"只会出 CS61B 的笔记，不会冒出 CS188 AI 课的内容。

## 通俗化解释（给学习者）

> **一句话说**: 每门课的笔记各存各的，搜索时不会串门。

**你会遇到的场景**:
- 你在 CS61B vault 里搜"树"，结果出来了 CS188 的"决策树"和"博弈树"，把你搞混了
- 你删了 CS188 vault 想清理空间，结果 CS61B 的搜索也坏了，因为底层索引混在一起
- 你想看某门课一共索引了多少笔记，但计数把所有课的都加在一起了

**这个功能帮你**:
- 每个 vault 有自己独立的"搜索数据库"（用 vault_id 命名空间隔离）
- 切换 vault 后，搜索自动只查当前 vault 的数据
- 删除某个 vault 的索引不影响其他 vault

**用个比喻**: 就像图书馆每层楼放不同科目的书 — 你在 CS61B 楼层搜书，不会搜出 CS188 楼层的。

## Acceptance Criteria

1. **Given** LanceDB 初始化
   **When** 创建表或索引
   **Then** 表名包含 vault_id 前缀：`{vault_id}_concept_embeddings`、`{vault_id}_note_chunks`
   **And** vault_id 从当前活跃 vault 的目录名派生（如 `CS188`、`CS61B`）

2. **Given** 两个 vault（CS188、CS61B）都已索引
   **When** 当前 vault = CS61B 时执行搜索
   **Then** 只搜索 `CS61B_*` 前缀的 LanceDB 表
   **And** 搜索结果不包含 CS188 的任何内容

3. **Given** vault 切换完成（Story 1.8）
   **When** LanceDB 客户端接收新请求
   **Then** 自动切换到新 vault_id 的表空间
   **And** 无需重建索引（已有的表保留）

4. **Given** 某 vault 的索引损坏或需要重建
   **When** 执行 `DELETE /api/v1/index/{vault_id}`
   **Then** 只删除该 vault_id 前缀的 LanceDB 表
   **And** 其他 vault 的索引不受影响

5. **Given** vault_id 命名空间
   **When** 查询索引统计
   **Then** `GET /api/v1/index/stats` 返回按 vault_id 分组的统计：`{"CS188": {"tables": 6, "rows": 1234}, "CS61B": {"tables": 6, "rows": 567}}`

6. **Given** `group_id` 占位符代码
   **When** 审查现有代码
   **Then** `vault_notes_retriever.py` 中的 `group_id` placeholder 被替换为真实的 `vault_id` 参数
   **And** `subject_resolver.py` 中的隔离逻辑使用 `vault_id` 过滤

## Tasks / Subtasks

- [ ] Task 1: vault_id 生成逻辑 (AC: #1)
  - [ ] 1.1: 在 `config.py` 或 `vault_switch_coordinator.py` 中新增 `get_current_vault_id() -> str`
  - [ ] 1.2: vault_id = vault 目录名的 sanitized 版本（去特殊字符，全小写，如 `cs188`）
  - [ ] 1.3: 确保 vault_id 是合法的 LanceDB 表名前缀（字母数字下划线）

- [ ] Task 2: LanceDB 表命名改造 (AC: #1, #2)
  - [ ] 2.1: 修改 `lancedb_client.py:329-349` 的 `__init__`，接受 `vault_id` 参数
  - [ ] 2.2: 所有表创建/查询操作加 `{vault_id}_` 前缀
  - [ ] 2.3: 提供 `switch_vault(new_vault_id)` 方法更新内部前缀
  - [ ] 2.4: 现有无前缀的表视为 `default` vault_id（向后兼容）

- [ ] Task 3: 检索层 vault_id 过滤 (AC: #2, #6)
  - [ ] 3.1: 修改 `vault_notes_retriever.py:126-231`，将 `group_id` placeholder 替换为 `vault_id`
  - [ ] 3.2: 修改 `subject_resolver.py:159-241`，查询时带 `vault_id` 过滤条件
  - [ ] 3.3: RAG pipeline 入口注入当前 `vault_id`

- [ ] Task 4: 索引管理 API (AC: #4, #5)
  - [ ] 4.1: `DELETE /api/v1/index/{vault_id}` — 删除指定 vault 的索引
  - [ ] 4.2: `GET /api/v1/index/stats` — 按 vault_id 分组统计
  - [ ] 4.3: 在 `vault.py` router 中注册

- [ ] Task 5: 测试 (AC: #1, #2, #4)
  - [ ] 5.1: `backend/tests/unit/test_lancedb_vault_isolation.py` — 两个 vault_id 的表互不干扰
  - [ ] 5.2: 切换 vault 后搜索只返回当前 vault 数据
  - [ ] 5.3: 删除单 vault 索引不影响其他 vault

## Dev Notes

- **LanceDB 表结构**: `lancedb_client.py:329-349` 初始化 6 张表（concept_embeddings / note_chunks / qa_pairs / exam_questions / canvas_metadata / relationship_edges），每张都需要加 vault_id 前缀
- **group_id placeholder**: `vault_notes_retriever.py:126-231` 有 `group_id` 参数但未真正实现隔离（placeholder 代码），需要用 vault_id 替换
- **subject_resolver.py:159-241**: 当前按 subject 过滤但不按 vault 隔离，需要增加 vault_id 维度
- **LanceDB 表名限制**: 表名只能用字母、数字、下划线，vault_id 必须 sanitize（如 "CS 61B" → "cs_61b"）
- **向后兼容**: 现有无前缀的表应被识别为 `default` vault，避免数据丢失
- **性能**: 表前缀方案比 WHERE 过滤更高效（LanceDB 按表物理隔离，不需要全表扫描）
- **QA 来源**: R12 [C4]（跨 vault 数据污染）+ R12 [N1]（vault_id 一等命名空间）

### Project Structure Notes

- 修改文件: `backend/lib/agentic_rag/clients/lancedb_client.py`（vault_id 前缀改造）
- 修改文件: `backend/app/services/lancedb_index_service.py`（传递 vault_id）
- 修改文件: 检索层 retriever / resolver 文件（vault_id 过滤）
- 新建文件: `backend/app/api/v1/endpoints/index.py`（索引管理 API）
- 测试文件: `backend/tests/unit/test_lancedb_vault_isolation.py`

### References

- [Source: backend/lib/agentic_rag/clients/lancedb_client.py:329-349] — LanceDB 初始化
- [Source: _bmad-output/research/obsidian-qa-round13-claude-answers-2026-04-16.md] — R12 [C4][N1]
- [Source: docs/architecture.md] — 数据层架构

## UAT Script

> 非技术用户验收脚本

1. **验证数据隔离** (AC: #1, #2)
   - 在 CS188 vault 下，在 Claudian 中搜索"决策树"，应有结果
   - 在 Claudian 中切换到 CS61B vault，再搜索"决策树"，应无结果（除非 CS61B 也有这个概念）
   - 在 CS61B 下搜索"链表"应有结果

2. **验证切换自动切表** (AC: #3)
   - 在 Claudian 中切换 vault 后立即搜索，不需要手动"重建索引"
   - 搜索结果只包含当前 vault 的笔记

3. **验证独立删除** (AC: #4)
   - 在 Claudian 中说"帮我清除 CS188 的索引数据"
   - 切换到 CS61B，搜索仍正常
   - 切回 CS188，搜索应提示"需要重建索引"

4. **验证统计信息** (AC: #5)
   - 在 Claudian 中说"帮我看看各个课程索引了多少笔记"，应看到每个 vault 各自的数量

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| CP-1.9.1 | pytest | `.venv/bin/pytest backend/tests/unit/test_lancedb_vault_isolation.py -x -q` | 0 failed |
| CP-1.9.2 | ruff | `ruff check backend/lib/agentic_rag/clients/lancedb_client.py` | exit 0 |
| CP-1.9.3 | grep | `! grep -n 'group_id.*placeholder\|group_id.*TODO' backend/` | exit 0（无 placeholder 残留）|

## User Feedback & Changes

### Feedback Log
<!-- Users write BMAD-ANNO callouts below -->

### Deviation Notes

**QA 来源追溯**:
1. **R12 [C4]**: 承认跨 vault 数据污染问题 — 当前 LanceDB 无 vault 隔离，CS188 和 CS61B 的笔记混在一起
2. **R12 [N1]**: 采纳 vault_id 一等命名空间建议 — vault_id 作为所有数据层的第一维度过滤
3. **R7 IQ-Q2**: LanceDB 索引粒度 — 等本 Story 实现后评估

## Dev Agent Record

### Agent Model Used
(to be filled by Dev agent)

### Debug Log References

### Completion Notes List

### File List
