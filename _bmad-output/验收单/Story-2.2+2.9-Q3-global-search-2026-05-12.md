---
story_id: "2.2+2.9"
task_id: "Q3-global-search"
title: "Skill 解题全局搜索 plugin 入口 + multi-seed BFS + global-search endpoint"
ship_date: "2026-05-12"
status: "deprecated"
deprecated_reason: "Wave-4 (2026-05-12) — 用户澄清 skill 自带全局搜索 = Claude native Grep + Read,wave-1 plugin command + backend endpoint 是 scope 蔓延已 rollback。改 SKILL.md (study-question HARD-21 + chat-with-context HARD-19) 让 native Grep 优先。"
phase: "B (功能可用) — DEPRECATED"
trace:
  - "用户原话: 解题不懂时全局搜索教学笔记"
  - "Story-3.1/3.5 Skill 全局搜索补完"
  - "PLAN-ID: EPIC1-BMAD-DEV-ASSESS-2026-04-17"
  - "Wave-4 rollback: 改用 SKILL.md native Grep + Read 替代 plugin command + backend endpoint"
deploy:
  backend_files: |
    wikilink_context_service.py (multi-seed BFS + TraceItem.seed_origin) — ROLLED BACK
    chat.py (新 POST /api/v1/chat/global-search,在 enrich-context body 之外追加) — ROLLED BACK
  frontend_files: |
    src/global-search.ts (新增 helper) — ROLLED BACK
    src/main.ts (canvas:global-search 命令 + handleGlobalSearch) — ROLLED BACK
    tests/global-search.test.ts (新增 19 测试) — ROLLED BACK
  tests: backend 61/61 + frontend 173/173 (已删除)
---

> ⚠️ **DEPRECATED — Wave-4 (2026-05-12)**
>
> 此验收单对应的 wave-1 实现已 **整体 rollback**。用户原意是改 `SKILL.md` 让 Claude 用 **native Grep + Read** 全局搜 vault,而不是在 plugin / backend 加新命令 + endpoint。
>
> **替代方案**: 改 `study-question` SKILL.md HARD-21 + `chat-with-context` SKILL.md HARD-19,Claude 在 skill 内直接调 native Grep 工具搜 vault → Read 命中文件,无需 plugin 命令、无需 backend endpoint。
>
> **新验收路径**: 见 `Story-2.2+2.9-wave-3-mini-UAT-2026-05-12.md` 的 Step 1 (Skill native Grep 验证)。
>
> 本文档**保留**作为 audit trail (wave-1 scope 蔓延 → wave-4 收口的记录),内容不删,但**不再执行**。

# Story 2.2+2.9 Q3 — 全局搜索教学笔记验收单 (DEPRECATED)

## 1. 🎯 一句话目标

你**不打开任何节点页面**（比如在 Dashboard / 全局视图 / 空白笔记里）也能问 Claude "什么是 X 概念？"，让 Claude 自动从整个 vault 里找出最相关的教学笔记摘要给你。

## 2. 📖 你的视角

**作为** 一个学习者,
**我想** 当我解题时遇到一个"我都不知道该打开哪个节点"的概念（比如对手提的某个术语完全没概念），我想直接问 Claude 而不必先猜该开哪份笔记,
**以便** 我能用最少的步骤拿到 vault 里"和这个概念最相关"的资料，不用先靠记忆翻文件树。

## 3. 🖥️ 交互流程

**Dashboard 场景**:
```
你做: 在 Obsidian 任意视图（比如 dashboard.md）→ 按 Cmd+P → 输入 "全局搜索"
↓
看到候选命令: "全局搜索教学笔记 (Global Search,任意视图可触发)"
↓
回车 → 弹出问题输入框
↓
你输入: "Bellman optimality 是什么？" → 回车
↓
等 1-3 秒
↓
右上角 Notice: "⭐ 已组装全局搜索: N 补充材料 / XXXms — 切到 Claudian 粘贴"
↓
切到 Claudian 侧栏 → Cmd+V 粘贴 → 你看到一段"全局搜索 manifest"开头 + 自动从 vault 里召回的若干段相关笔记摘要
↓
继续问 Claude 跟进问题 → Claude 基于已注入的全局搜索结果回答
```

**节点内解题遇外来概念场景（multi-seed BFS）**:
```
你做: 在 节点/admissibility.md 解题 → 按 Cmd+P → 解题深度模式
↓
你输入: "Bellman optimality 是怎么和 admissibility 联系的？"
↓
后端识别 "Bellman optimality" 是外来概念 → 把它作为额外 seed 加入图遍历
↓
你看到 Claude 引用的资料里同时含 admissibility 的邻居 + Bellman optimality 的邻居
↓
我感觉: 不必先去单独打开 Bellman optimality 节点,一次提问就把两边都拉进来了
```

## 🤖 Claude 已代验

| Check | 命令 / 证据 | 结果 |
|---|---|---|
| Backend 新增 multi-seed BFS | code review `wikilink_context_service.py:~371-615` enrich_from_wikilink_graph 加 additional_seeds 参数 | ✅ multi-seed merge + slug 去重 + 保留 min(hop) |
| TraceItem 加 seed_origin 字段 | code review `wikilink_context_service.py:~99` | ✅ 多 seed 场景诊断字段就绪 |
| Backend 新增 global-search endpoint | code review `chat.py:~828-1020` POST /api/v1/chat/global-search | ✅ GlobalSearchRequest + GlobalSearchResponse + manifest |
| Backend 测试 (multi-seed + endpoint) | `pytest tests/unit/test_wikilink_context_service.py tests/unit/test_chat_endpoint.py -q` | ✅ 61/61 pass (含 6 新增) |
| Frontend 新增 canvas:global-search 命令 | code review `frontend/obsidian-plugin/src/main.ts:~515-534` 无 isNodePath 守门 | ✅ 命令注册,任意视图可触发 |
| Frontend handleGlobalSearch 实现 | code review `frontend/obsidian-plugin/src/main.ts:~919-1027` AbortController 8s timeout + 错误分类 + Notice | ✅ 失败路径 graceful（backend_timeout/backend_unreachable/backend_error/non_json_response） |
| Frontend helper (pure functions) | code review `frontend/obsidian-plugin/src/global-search.ts` 新文件 100 行 | ✅ 模式与 node-chat-context.ts 一致（pure + orchestrator） |
| Frontend 测试 | `npm test` | ✅ 173/173 pass (含 19 新增 across 5 describe blocks) |
| Build OK | `npm run build` | ✅ 152KB main.js,0 type error (我加的代码) |

**模拟验证场景**（Claude 自测）:
- 场景 A: POST /api/v1/chat/global-search 空 user_question → 422 ✅
- 场景 B: POST 正常 → 200 + supplementary XML + manifest ✅
- 场景 C: lancedb 不可用 → degraded=True + reason="lancedb_unavailable" ✅
- 场景 D: 两 seed BFS,seed_A 返 [X,Y] / seed_B 返 [Y,Z] → merge 后 [X,Y,Z] 不重复,Y 标 seed_origin=seed_A（先到） ✅
- 场景 E: frontend backend 未起 → handleGlobalSearch catch TypeError → Notice "⚠️ 全局搜索失败 (backend_unreachable)" 不 crash ✅

## 👤 你来验

> 第一次用前在 Obsidian Settings → Hotkeys 找 "全局搜索教学笔记 (Global Search,任意视图可触发)" 自绑你喜欢的快捷键。或直接 Cmd+P 模糊搜命令名。

### Step 1 — Dashboard / 空白笔记触发全局搜索

- [ ] 我做：打开 Obsidian 的 dashboard.md（或任意一个**不是** `节点/` 下的文件,或空白页）
- [ ] 我做：按 Cmd+P → 输入 "全局" → 选择"全局搜索教学笔记 (Global Search...)"
- [ ] 我做：在弹出的问题框里输入任一你正在学但不太懂的概念,比如 "什么是 X-Y-Z 定理？"
- [ ] 我看到：等 1-3 秒后右上角弹 Notice "⭐ 已组装全局搜索: N 补充材料 ..."
- [ ] 我感觉：从来没需要先去找"该打开哪个节点",直接问就拿到资料

### Step 2 — 粘到 Claudian 看到全局搜索结果

- [ ] 我做：切到 Claudian 侧栏 + Cmd+V 粘贴
- [ ] 我看到：内容开头是 "/chat-with-context" 加上一段 "Global Search Manifest" 说明（含你的问题 / vault 名 / 召回数量）
- [ ] 我看到：下面跟着若干段从 vault 各处召回的笔记摘要
- [ ] 我感觉：Claude 已经看到了相关资料,我直接问追问题就能拿到回答

### Step 3 — 节点内"解题遇外来概念"两边都拉进来

- [ ] 我做：在一个具体节点（比如 `节点/admissibility.md`）按 Cmd+P → "解题深度模式"
- [ ] 我做：输入一个故意包含外来概念的问题,比如 "admissibility 跟 Bellman optimality 怎么联系？"
- [ ] 我做：切 Claudian + Cmd+V 粘贴
- [ ] 我看到：粘贴出来的"邻居"段里同时含 admissibility 的相关节点 + Bellman optimality 的相关节点
- [ ] 我感觉：一次提问把两个概念的"周边知识"都拉进对话,不必先单独打开 Bellman 节点

### Step 4 — backend 没起来时友好降级

- [ ] 我做：故意先停掉 backend（或拔网络 / 切到没起 backend 的环境）
- [ ] 我做：按 Cmd+P → "全局搜索教学笔记" → 输入任意问题
- [ ] 我看到：等 8 秒以内弹 Notice "⚠️ 全局搜索失败 (backend 未连接/超时)" 提示
- [ ] 我感觉：不会卡死、不会弹红色 error 框,告诉我清楚发生了什么

## 5. 🚦 验收结果

通过条件:
- [ ] Step 1 ✅ Dashboard 也能触发
- [ ] Step 2 ✅ 粘贴出来有 manifest + 召回结果
- [ ] Step 3 ✅ 外来概念两边都拉进来
- [ ] Step 4 ✅ backend 没起时友好降级

通过 → 末尾写 "Q3 global-search 通过"

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
  - `backend/app/services/wikilink_context_service.py:371-615` (multi-seed BFS + seed_origin)
  - `backend/app/api/v1/endpoints/chat.py:828-1020` (global-search endpoint + manifest)
  - `frontend/obsidian-plugin/src/global-search.ts` (pure helpers)
  - `frontend/obsidian-plugin/src/main.ts:515-534` (canvas:global-search command)
  - `frontend/obsidian-plugin/src/main.ts:919-1027` (handleGlobalSearch)
- 测试: backend 61/61 + frontend 173/173
- PLAN-ID: EPIC1-BMAD-DEV-ASSESS-2026-04-17
