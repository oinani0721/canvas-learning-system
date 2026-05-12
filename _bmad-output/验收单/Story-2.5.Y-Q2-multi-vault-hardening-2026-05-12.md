---
story_id: "2.5.Y"
task_id: "Q2-multi-vault-hardening"
title: "WikilinkGraphService per-vault dict + BackgroundTaskManager copy_context"
ship_date: "2026-05-12"
status: "review"
phase: "B (功能可用)"
trace:
  - "Story-2.5.Y AC#10 真实落地 (单例 → per-vault dict)"
  - "ChatGPT P0-A Multi-Vault 全链路真实兑现"
  - "PLAN-ID: EPIC1-BMAD-DEV-ASSESS-2026-04-17"
deploy:
  backend_files: |
    wikilink_graph_service.py (单例 → dict[str, WikilinkGraphService] 按 vault key 分桶)
    background_task_manager.py (asyncio.create_task 加 context=contextvars.copy_context())
  tests: 96/96 (新增 6 + 既有 90 零回归)
---

# Story 2.5.Y Q2 — Multi-Vault 隔离硬化验收单

## 1. 🎯 一句话目标

你在两个不同的 vault 之间来回切（比如 cs_61b 和 数学），按 Cmd+Shift+E 时不会把另一个 vault 的笔记错误注入到当前对话；后台任务（自动错误抽取等）也不会把数据写错地方。

## 2. 📖 你的视角

**作为** 一个学多个学科的人,
**我想** 在 vault A 学完切到 vault B 时，AI 看到的邻居/笔记完全来自 vault B 而不是 A 的残留,
**以便** 我能放心地一个 Obsidian session 里跨 vault 学习，不必担心"上一个 vault 的内容"污染我的学习记录。

## 3. 🖥️ 交互流程

**切 vault 前后场景**:
```
你做: 在 vault cs_61b 打开 节点/admissibility.md → 按 Cmd+Shift+E
↓
屏幕弹: "...邻居 N1: BFS-1hop / DFS-1hop / ..."  ← cs_61b 邻居
↓
你做: Obsidian 切到 vault 数学 → 打开 节点/eigenvalues.md → 按 Cmd+Shift+E
↓
屏幕弹: "...邻居 N2: 特征值定义 / 谱定理 / ..."  ← 必须是数学 vault 邻居
↓
我感觉: 没看到任何 cs_61b 的节点（如 BFS / Pacman / A*）出现在数学的上下文里
```

**后台任务场景**:
```
你做: 在 vault cs_61b 完成一次 Claude 对话 → Claudian 自动 fire 错误抽取后台任务
↓
等几秒（后台跑）
↓
我感觉（隐形,但可信）: 后台任务把错误记录写到 vault cs_61b 的学习档案,不写到 vault 数学
```

## 🤖 Claude 已代验

| Check | 命令 / 证据 | 结果 |
|---|---|---|
| WikilinkGraphService 改 per-vault dict | code review `wikilink_graph_service.py:~317` `_wikilink_graph_services: dict[str, ...]` | ✅ singleton → dict,按 vault key 分桶 |
| `_resolve_vault_key()` 从 ContextVar 派生 | code review get_current_subject_id() 派生 + sanitize_subject_name 归一化 | ✅ 异常/空值落 `__default__` 桶（向后兼容） |
| Per-vault isolation 测试 | `pytest tests/unit/test_wikilink_graph_service.py::TestMultiVaultIsolation -q` | ✅ 3/3 pass (test_per_vault_isolation + test_no_contextvar_uses_default_key + test_clear_cache_for_vault) |
| BackgroundTaskManager copy_context | code review `background_task_manager.py:~200` `asyncio.create_task(..., context=contextvars.copy_context())` | ✅ Python 3.11+ 原生支持,当前 venv 3.14 |
| ContextVar inheritance 测试 | `pytest tests/unit/test_background_task_manager.py -q` | ✅ 3/3 pass (test_create_task_inherits_contextvar + test_create_task_with_different_contextvars + test_default_contextvar_propagates) |
| wikilink 套件零回归 | `pytest tests/unit/test_wikilink_graph_service.py tests/unit/test_wikilink_context_service.py tests/unit/test_wikilink_parser.py -q` | ✅ 96/96 (90 baseline + 6 新增) |
| 跨 vault 隔离 helper | code review `clear_cache_for_vault / clear_all_caches / get_cache_stats` 已加 | ✅ 测试 + 运营脚手架就绪 |

**模拟验证场景**（Claude 自测,你不用做）:
- 场景 A: ContextVar set vault_cs_61b → get_wikilink_graph_service() 返回 instance_A → build graph;切到 vault 数学 → 返回 instance_B → build graph_B;切回 cs_61b → instance_A 仍是 cs_61b graph ✅
- 场景 B: ContextVar None → 落 `__default__` 桶 → 正常工作（向后兼容） ✅
- 场景 C: 主任务 set vault_C → fire-and-forget 后台 task → task 内 get_current_subject_id() == vault_C ✅

## 👤 你来验

> 你需要至少 2 个 vault 才能完整验证。如只有 1 个 vault,只跑 Step 3。

### Step 1 — 切 vault 前后邻居完全不同

- [ ] 我做：打开第一个 vault（比如 cs_61b）→ 打开 `节点/某概念.md`
- [ ] 我做：按 Cmd+Shift+E → 切到 Claudian → Cmd+V 粘贴
- [ ] 我看到：粘贴出来的内容里"邻居"段列出的节点名字全部能在 cs_61b 里找到
- [ ] 我做：Obsidian 切到另一个 vault（比如 数学）→ 打开 `节点/另一概念.md`
- [ ] 我做：按 Cmd+Shift+E → 切 Claudian → Cmd+V
- [ ] 我看到：这次"邻居"段全是数学的节点名字
- [ ] 我感觉：没有任何 cs_61b 的节点（BFS / Pacman / 之类）混进数学的对话上下文

### Step 2 — 切回原 vault 数据不丢

- [ ] 我做：从数学切回 cs_61b → 打开同一个 Step 1 里用过的节点
- [ ] 我做：按 Cmd+Shift+E + Cmd+V
- [ ] 我看到："邻居"段又回到 cs_61b 的节点
- [ ] 我感觉：来回切不丢数据，每个 vault 独立保持自己的图

### Step 3 — 后台任务不串库（隐形,主要看"日后没出怪事"）

- [ ] 我做：在你常用 vault 里跟 Claude 完成一轮完整对话（用 study-question 或 chat-with-context）
- [ ] 我做：等 10 秒（让后台抽取错误的任务跑完）
- [ ] 我看到：dashboard.md 或学习记录里如有新增,标的是**当前 vault** 的学习记录,不是另一个 vault
- [ ] 我感觉：后台默默做事但写对地方,我不需要操心数据归属

## 5. 🚦 验收结果

通过条件:
- [ ] Step 1 ✅ 切 vault 后邻居全换
- [ ] Step 2 ✅ 切回原 vault 数据保留
- [ ] Step 3 ✅ 后台任务归属正确

通过 → 末尾写 "Q2 multi-vault hardening 通过"

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

- Story: `_bmad-output/implementation-artifacts/epic-2/2-5-y-isolation-hardening-subject-config-reuse.md` (AC#10 现真实落地)
- 关键代码:
  - `backend/app/services/wikilink_graph_service.py:~317-411` (per-vault dict)
  - `backend/app/services/background_task_manager.py:~200` (copy_context)
- 测试: 96/96 pass (新增 6)
- PLAN-ID: EPIC1-BMAD-DEV-ASSESS-2026-04-17
