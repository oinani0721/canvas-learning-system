---
story_id: "2.2+2.9"
task_id: "Q1-hotfix"
title: "Rerank 5 P0 hotfix + chunk-type-aware filter"
ship_date: "2026-05-12"
status: "review"
phase: "B (功能可用)"
trace:
  - "Story-2.2+2.9 AC #4 真实可用 (T3 ship 后 P0-A/B/C/D/E 全 fix)"
  - "ChatGPT-Review 2026-05-11 P0-A/P0-B/P0-C 真实兑现"
  - "PLAN-ID: EPIC1-BMAD-DEV-ASSESS-2026-04-17"
deploy:
  backend_files: |
    supplementary_reranker.py (TYPE_WEIGHTS 加 note/video_transcript/image_ocr 过渡映射 + filter floor + min_keep)
    supplementary_search_service.py (tier-2 degraded 顶层传播 + chunk-link-list filter + guard fail-closed RuntimeError)
    chat.py (singleton 改 lazy await _get_supp_lancedb_client)
  tests: 104/104 (新增 27,baseline 77,零回归)
---

# Story 2.2+2.9 Q1 — Rerank 5 P0 Hotfix 验收单

## 1. 🎯 一句话目标

你按 Cmd+Shift+E 之后看到的"补充材料"不再被白板/索引节点污染、不再因评分错配被全部过滤、首次冷启 5 秒内也能加载，且**手动审计时能从 Claude 的回复里清楚看到每条材料的"评分线索"**。

## 2. 📖 你的视角

**作为** 一个学习者,
**我想** 当我开机后第一次按 Cmd+Shift+E、或在大量笔记的 vault 里提问时，补充材料不要"明明召回了却被丢光",而且我看 Claude 引用的材料能感觉到"这条比那条排前是有原因的",
**以便** 我能信任 RAG 而不是绕过它去手动 grep。

## 3. 🖥️ 交互流程

**冷启首问场景（P0-C fix）**:
```
你做: 早上刚开 Obsidian → 立刻按 Cmd+Shift+E
↓
等 1-5 秒（之前会立刻 fallback,补充材料为空,现在会真等模型起来）
↓
屏幕右上角 Notice: "已组装 backend RAG 上下文 ... + N 补充材料 ⭐"
```

**大量召回场景（P0-A + P0-B fix）**:
```
你做: 在一个写满 100+ 笔记的 vault 里按 Cmd+Shift+E 提问
↓
Claude 回复里引用的补充材料 ≥ 3 条（不再 0 条 / 1 条）
↓
材料按 "讲义/视频转录 > 一般笔记 > 截图 OCR" 的顺序排
```

**白板污染兜底（chunk filter bonus）**:
```
你做: 提问"这个领域的核心是？"（容易召回 MOC/Index）
↓
Claude 引用材料里没有"链接列表"型节点（即使被旧索引误标 type）
```

## 🤖 Claude 已代验（你不用管）

| Check | 命令 / 证据 | 结果 |
|---|---|---|
| P0-A TYPE_WEIGHTS 加过渡映射 | `grep "note.*0.7\|video_transcript\|image_ocr" backend/app/services/supplementary_reranker.py` | ✅ 3 个新条目 + PRD 6 档保留 |
| P0-A 单元测试 (TestTypeWeightsIndexerTransition) | `pytest tests/unit/test_supplementary_reranker.py -k Transition -q` | ✅ 5/5 pass |
| P0-B filter floor 机制 | code review rerank() 内 min_keep=3 + filter_floor_triggered 字段 | ✅ filter 后 < 3 条或砍 > 80% 时自动 fallback |
| P0-B 单元测试 (TestFilterFloor) | `pytest tests/unit/test_supplementary_reranker.py -k Floor -q` | ✅ 5/5 pass |
| P0-C singleton lazy init | `grep "await _get_supp_lancedb_client" backend/app/api/v1/endpoints/chat.py` | ✅ chat.py:332 改 lazy await |
| P0-C 集成测试 | `pytest tests/unit/test_chat_endpoint.py -k lazy_init -q` | ✅ 2/2 pass |
| P0-D tier-2 degraded 顶层传播 | `grep "tier2_legacy_unprefixed" backend/app/services/supplementary_search_service.py` | ✅ outer dict 写回 degraded=True + reason |
| P0-D 单元测试 (TestTopLevelDegradedFromLegacyFallback) | `pytest tests/unit/test_supplementary_search_service.py -k TopLevelDegraded -q` | ✅ 2/2 pass |
| P0-E guard fail-closed RuntimeError | code review _classify_snippet_taint 分支: ImportError→clean / RuntimeError→review | ✅ 异常路径 fail-closed |
| P0-E 单元测试 (TestClassifySnippetTaintFailClosed) | `pytest tests/unit/test_supplementary_search_service.py -k FailClosed -q` | ✅ 2/2 pass |
| Bonus chunk-link-list filter | code review _is_link_list_chunk + format_supplementary_xml 透出 is_link_list 属性 | ✅ wikilink_density > 0.6 标 link-list,XML attr 渲染 |
| Bonus 单元测试 | `pytest tests/unit/test_supplementary_search_service.py -k LinkList -q` | ✅ 8/8 pass |
| 全套件零回归 | `pytest tests/unit/test_supplementary_reranker.py tests/unit/test_supplementary_search_service.py tests/unit/test_chat_endpoint.py -q` | ✅ 104/104 pass (baseline 77,新增 27) |

## 👤 你来验（产品体验,3-5 分钟）

### Step 1 — 冷启首问不再"空材料"

- [ ] 我做：完全退出 Obsidian → 重启 → 等 5 秒别动 → 立刻打开一个学过的概念页面（比如 `节点/admissibility.md` 或常用任一节点）
- [ ] 我做：按 Cmd+Shift+E
- [ ] 我看到：右上角 Notice 显示 "...N 补充材料 ⭐"，N ≥ 1（之前冷启 N 经常是 0）
- [ ] 我感觉：开机第一问就能用，不必等"系统暖机"那种焦虑

### Step 2 — 大 vault 提问材料数明显多了

- [ ] 我做：在你笔记多的 vault 里打开一个常用节点
- [ ] 我做：按 Cmd+Shift+E + 切到 Claudian 侧栏 + Cmd+V 粘贴 + 输入问题（比如 "怎么证明？"）回车
- [ ] 我看到：Claude 引用的补充材料数 ≥ 3 条（不再是"召回了一堆但 Claude 只引 1 条"）
- [ ] 我感觉：信任感提升，不再怀疑"是不是检索出问题"

### Step 3 — 排序优先级清晰

- [ ] 我做：复看 Step 2 Claude 给的材料列表
- [ ] 我看到：讲义类 / 视频转录类的标题排在普通笔记前面
- [ ] 我感觉：Claude 优先用了"权威源"，而不是随便引用一段散记

### Step 4 — 索引/链接列表节点不再霸屏

- [ ] 我做：换一个有"目录/索引"节点的视图，提问 "这个领域核心概念是什么"
- [ ] 我看到：Claude 引用里**没有**那种纯链接列表的节点
- [ ] 我感觉：检索看到的是"知识颗粒",不是"目录的目录"

## 5. 🚦 验收结果

通过条件:
- [ ] Step 1 ✅ 冷启首问 N ≥ 1
- [ ] Step 2 ✅ 大 vault 引用 ≥ 3 条
- [ ] Step 3 ✅ 排序优先级清晰
- [ ] Step 4 ✅ 链接列表节点过滤

通过 → 在末尾写 "Q1 hotfix 通过"

## 6. 📝 批注区

```
> [!question]+
> 

> [!error]+
> 

> [!tip]+
> 
```

## 7. 🔗 技术 spec 引用

- Spec: `_bmad-output/implementation-artifacts/epic-2/2-2-and-2-9-merged-rerank-evidence.md`
- 关键代码:
  - `backend/app/services/supplementary_reranker.py` (TYPE_WEIGHTS 过渡映射 + filter floor)
  - `backend/app/services/supplementary_search_service.py` (tier-2 degraded + chunk-link-list filter + guard fail-closed)
  - `backend/app/api/v1/endpoints/chat.py:~332` (singleton lazy init)
- 测试: 104/104 pass (新增 27)
- PLAN-ID: EPIC1-BMAD-DEV-ASSESS-2026-04-17
