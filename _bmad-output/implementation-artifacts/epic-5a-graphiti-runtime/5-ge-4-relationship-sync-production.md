---
story_id: "5-ge-4-relationship-sync-production"
epic_id: "5a-graphiti-runtime"
prd_id: "canvas-learning-system"
status: "ready-for-dev"
priority: "P0"
estimate_hours: 2
depends_on: ["5-ge-1"]
blocks: []
sprint: "Sprint 2 v3 (Day 9 PM, Session C)"
plan_id: "EPIC1-BMAD-DEV-ASSESS-2026-04-17"
chatgpt_required: "#4 (后半) dry_run=False + 议题 6 group_id 隔离"
supersedes: ["关闭 relationship_sync_service.py dry_run=True default"]
decision_trace: "2026-05-26 ChatGPT Deep Research 缺口 4 + 议题 5 + 议题 6"
---

# Story 5-ge-4: relationship_sync_service 改 production + 移除 DEFAULT_GROUP_ID fallback

Status: ready-for-dev

## Story

As a **学习者**,
I want **当我用 Cmd+Shift+D 派生节点选了 "prerequisite" 关系后, Graphiti 真把这条关系写下来, 而不是停在 dry_run 仅扫描**,
So that 用户 line 47 痛点 "Claude 如何能正确识别 relationships" 直接解决 (frontmatter relationships → Graphiti edge 真同步).

## Acceptance Criteria

1. **Given** `backend/app/services/relationship_sync_service.py` **When** 改造 **Then**:
   - `sync_relationships_in_vault(vault_root, *, vault_id, subject_id=None, dry_run=False)` — **dry_run default 从 True 改 False**
   - 接口必须 keyword-only 强制 `vault_id` 参数 (不允许 fallback 到 DEFAULT_GROUP_ID)
   - group_id 用 `build_vault_group_id(vault_id, subject_id=subject_id)` 显式构造

2. **Given** 移除 fallback **When** 任何调用方传 None / missing vault_id **Then** raise `ValueError("vault_id is required, no DEFAULT_GROUP_ID fallback allowed")`

3. **Given** 名实一致 **When** 现状 (函数名 "Graphiti sync" 但用 Neo4jEdgeClient 写) **Then** **改造**:
   - **保留** Neo4j 显式结构层写入 (Neo4j 是 canonical topology)
   - **新增** Graphiti edge 镜像写入 (用 5-ge-1 unified schema 走 add_episode + 5-ge-2 belief_key)
   - 双层共享 `belief_key` (edge:{src}:{relation}:{tgt})

4. **Given** 单元测试 **Then** 覆盖:
   - dry_run=False 真写 Neo4j + Graphiti (2 层都验证)
   - missing vault_id → raise ValueError
   - 重复同步同一 relationship → 5-ge-2 belief_key 版本链生效 (不重复写)

5. **Given** ChatGPT 议题 5 "Neo4j vs Graphiti 分工" **When** 写入策略 **Then** 写进 `_bmad-output/.claude/CLAUDE.md` (架构契约 §)：
   - Neo4j = canonical topology (wikilink / frontmatter / review)
   - Graphiti = temporal memory (callout / error / calibration + 同时镜像 canonical relations)
   - 跨层共享 belief_key

## Tasks / Subtasks

- [ ] Task 1: 接口 keyword-only + 移除 fallback (AC: #1, #2)
  - [ ] 改 `backend/app/services/relationship_sync_service.py:189-205`
  - [ ] dry_run default False
  - [ ] vault_id 强制 + raise ValueError
- [ ] Task 2: Graphiti 镜像写入 (AC: #3)
  - [ ] 调 5-ge-1 unified writer 写 `relation_synced` event_type
  - [ ] 调 5-ge-2 update_belief_version_chain 维护 canonical edge
- [ ] Task 3: 名实一致重命名 (AC: #3)
  - [ ] 函数名保留 (`sync_relationships_in_vault`)
  - [ ] docstring 改 "writes both Neo4j topology + Graphiti temporal mirror" (反映真实行为)
- [ ] Task 4: 架构契约写 CLAUDE.md (AC: #5)
  - [ ] 改 `_bmad-output/.claude/CLAUDE.md` 加 "Neo4j 显式结构层 vs Graphiti 时序记忆层" §
- [ ] Task 5: 单元测试 (AC: #4)
  - [ ] `backend/tests/unit/test_relationship_sync_production.py`
  - [ ] missing vault_id 路径 / 重复同步 / 双层验证

## Dev Notes

### File Paths
- 改: `backend/app/services/relationship_sync_service.py` (line 189-205 + docstring)
- 改: `_bmad-output/.claude/CLAUDE.md` (加架构契约 §)

### Background Decision Trace
- 2026-05-26 ChatGPT 议题 5 "硬裁决: Neo4j 显式结构层 vs Graphiti 时序记忆层"
- 2026-05-26 ChatGPT 议题 6 "DEFAULT_GROUP_ID fallback 跨 vault 污染高风险"
- 用户 line 47 批注 "Claude 如何能正确识别 relationships" 直接解决

### References
- ChatGPT 报告 §Part 3 议题 5 + 议题 6
- 用户 line 47 批注 (主审计报告)

## Change Log

- 2026-05-26: spec 新建 (修关键命名错配 + 移除安全隐患)
