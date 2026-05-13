---
story_id: "2.2+2.9"
task_id: "wave-1-to-5 综合 UAT"
title: "Canvas Learning System 综合验收 — RAG 精度 + Multi-vault 隔离 + Skill native Grep"
ship_date: "2026-05-13"
status: "review"
phase: "B 综合 UAT"
trace:
  - "本 session 全部 commit (549d5f0 → 1d70c85, ~17 commits)"
  - "wave-1/2/3 hotfix + wave-4 rollback + wave-5 multi-vault 隔离全闭口"
  - "PLAN-ID: EPIC1-BMAD-DEV-ASSESS-2026-04-17"
deploy:
  backend: |
    71 endpoint vault_id 注入 + 共享 _vault_id_resolver.py helper
    rerank engine + chunk filter + metadata redaction
    multi-vault: per-vault wikilink graph + LanceDB ContextVar + ContextVar 继承
    integration test 12/12 pass (cross-vault isolation)
  frontend: |
    4 hotkey Notice [vault: <id>] 前缀 + buildBackendHeaders X-CLS-Internal-Key
    Status bar 常驻 🎓 vault_id · ✓/⚠/❌
    canvas:global-search 已 rollback (改 SKILL.md native Grep)
  skill: |
    study-question/SKILL.md v1.6 加 HARD-21 (native Grep 优先)
    chat-with-context/SKILL.md v2.1 修订 HARD-19 (Grep 优先 + MCP fallback)
  tests: |
    backend 262+ pass / frontend 193+ pass / integration test 12/12 / 0 wave-5 引入回归
---

# 📋 Canvas Learning System wave-1~5 综合验收单

5-10 分钟内验完全部 ship 内容 + 决定是否整体 ship。

---

## 1. 🎯 一句话目标(非技术)

按 Cmd+Shift+E 后看到的补充材料按"我问题相关性 + 课件优先 + 不被索引节点垄断"排序 + 切 vault 时邻居完全独立不串库 + Claudian 里用 `/study-question` 时 Claude 自己用 native Grep 搜全 vault → 不需要新建复杂功能。

---

## 2. 📖 你的视角

**作为** 一个用 Canvas Learning System 学多学科(每学科一个 Obsidian vault)的人,
**我想** 在每个 vault 都能用 plugin 调 backend RAG,且数据完全分隔(vault A 笔记不会进 vault B 的对话上下文);同时 skill 在解题时能自己 Grep 全 vault 教学笔记,
**以便** 我能跨 vault 学习不担心数据混乱 + 不依赖 plugin 加新命令包装层。

---

## 3. 🖥️ 交互流程

**Cmd+Shift+E 触发场景**:
```
你做: 打开 节点/admissibility.md → Cmd+Shift+E
↓
右上角 Notice: "[vault: cs_61b] 已组装 backend RAG 上下文 N KB / X 邻居 + Y 补充材料 ⭐ ..."
↓
切到 Claudian + Cmd+V 粘贴
↓
内容开头有 manifest 段, 第一行: Vault: cs_61b
↓
Claude 根据 vault: cs_61b 的邻居 + 补充材料回答
↓
对话历史里永久留下 vault_id 归属证据
```

**多 vault 切换场景**:
```
你做: 切换 Obsidian 到另一个 vault (例 数学) → 打开节点 → Cmd+Shift+E
↓
Status bar 立即从 "🎓 cs_61b · ✓" 变成 "🎓 数学 · ✓"
↓
Notice 显示 "[vault: 数学] ..." (不是 cs_61b 残留)
↓
邻居全是数学 vault 的节点 (0 cs_61b 残留)
```

**Claudian 内 /study-question 场景** (取代 wave-4 撤回的 canvas:global-search):
```
你做: 任意视图 (Dashboard 或非节点页) 切到 Claudian
↓
输入 /study-question 什么是 Bellman optimality
↓
Claude 主动 [4/5] Read 完整章节 + [5/5] Grep 三个关键术语跨 vault 分布
↓
4 段输出: 严格定义 / 直觉理解 / 反例 / 联系节点
↓
inline [[wikilink]] 引用 + Faithfulness 自检 (11/11 满分)
↓
末尾 dump 完整 supplementary 列表 + 矛盾点显式标
```

---

## 🤖 Claude 已代验(你不用管)

| 维度 | 命令 / 证据 | 结果 |
|---|---|---|
| **Backend 测试** | `pytest tests/unit/ tests/security/ tests/integration/ --strict-markers` | ✅ 262+ pass / 0 wave 引入回归 |
| **Frontend 测试** | `npm test` | ✅ 193/193 pass + 22 new (vault-indicator) |
| **Integration test** | `pytest tests/integration/test_multi_vault_isolation.py` | ✅ 12/12 pass (mock-driven, 80s) |
| **wave-5 71 endpoint vault_id** | 文件清单 + `_vault_id_resolver.py` helper 9 file 复用 | ✅ target 50 endpoint 超额至 71 |
| **Q1 chunk filter** | `_is_link_list_chunk wikilink_density>0.6` 已 ship | ✅ 用户 wave-2 mini-UAT 实测见 0 MOC 污染 |
| **Q2 multi-vault 隔离** | `wikilink_graph_service.py` per-vault dict + `LanceDBClient.active_vault_id` ContextVar + 71 endpoint ContextVar 注入 | ✅ integration test 12/12 验证 |
| **Q3 rollback + SKILL.md** | wave-4 `46fc501` 删 `canvas:global-search` 全代码 + SKILL.md HARD-21/HARD-19 加 native Grep 优先 | ✅ 用户实测 Faithfulness 11/11 |
| **Frontend X-CLS-Internal-Key** | `buildBackendHeaders` 自动注入 + 5 fetch site 全覆盖 | ✅ DEBUG=False 生产环境 401 防御 |
| **Tauri 前端** | `frontend/DEPRECATED.md` + `@deprecated` marker | ✅ scope 收敛 |
| **Wave-5 Stage A UX** | Notice [vault:] 前缀 + manifest Vault: 行 + status bar 三态 | ✅ 3 路用户可见 |
| **业界 multi-tenancy 范式** | Shared-DB Row-per-Tenant + LanceDB 表前缀 (社区共识对齐) | ✅ Khoj / Smart Connections / Copilot 范式对照 |

**Claude 模拟验证**:
- 场景 A: 同节点查询 9 supplementary 中 0 MOC/Index 污染 ✅
- 场景 B: 切 vault A → B 后 Notice + status bar 立即换 ✅
- 场景 C: `/study-question` 触发 Claude 自己 Grep + Read 5+ file ✅
- 场景 D: vault A 和 vault B 并发 endpoint 调用 ContextVar 互不串 ✅
- 场景 E: vault_switch_coordinator 调用立即 log.warning DEPRECATED ✅
- 场景 F: LanceDB Tier-2 unprefixed fallback default 禁用 (env gate) ✅

---

## 👤 你来验(产品体验,5-10 分钟,全在 Obsidian)

### Step 1 — Q1 RAG 精度 + Notice [vault:] 前缀(必跑)

- [ ] 我做:Obsidian 内打开任意 `节点/<概念>.md`(例 `节点/admissibility.md`)
- [ ] 我做:Cmd+Shift+E
- [ ] 我看到:右上角 Notice 文案以 `[vault: <你的 vault 名>]` 开头(中文 vault 名也支持,例 `[vault: 数学]`)
- [ ] 我做:切到 Claudian + Cmd+V 粘贴
- [ ] 我看到:内容开头第二段是 `<manifest>` 段,**第一行是 `Vault: <vault_id>`**
- [ ] 我看到:9 条左右补充材料按"讲义类在前 / OCR 类在后",**0 个 MOC/Index 节点污染**
- [ ] 我感觉:每条材料都"有用",不需要翻 20 条找核心

### Step 2 — Status bar 常驻 vault 指示器(必跑)

- [ ] 我做:看 Obsidian 底部 status bar
- [ ] 我看到:🎓 emoji + 当前 vault 名 + ✓/⚠/❌ 三态(✓ 绿 = backend OK / ⚠ 橙 = backend 在另一 vault / ❌ 红 = backend down)
- [ ] 我做:点击 status bar
- [ ] 我看到:打开 Canvas Learning System 的 Settings 页
- [ ] 我感觉:不进 Settings 也持续可见 vault 名 + 同步状态

### Step 3 — Multi-vault 切换隔离(强烈推荐,需 2 个 vault)

> 如你只有 1 个 vault,跳过本 step(integration test 12/12 已覆盖技术验证)

- [ ] 我做:在 vault A(例 cs_61b)打开节点 + Cmd+Shift+E + 切 Claudian + Cmd+V
- [ ] 我看到:邻居全是 vault A 的节点 + manifest 写 `Vault: cs_61b`
- [ ] 我做:Obsidian 切换到 vault B(例 数学)+ 同样按 Cmd+Shift+E + Cmd+V
- [ ] 我看到:Notice 显示 `[vault: 数学]`,status bar 立即变 `🎓 数学 · ✓`,邻居**全是数学 vault 节点**(0 cs_61b 残留)
- [ ] 我做:切回 vault A → 同样按 Cmd+Shift+E
- [ ] 我看到:邻居又是 cs_61b 的(切回不丢)
- [ ] 我感觉:跨 vault 学习不会串库,backend 永远跟着用户切换

### Step 4 — Claudian native Grep 全局搜索(必跑)

- [ ] 我做:任意视图(可以非节点页,如 dashboard.md / 空白文件)切到 Claudian
- [ ] 我做:输入 `/study-question 什么是 <你不熟的概念,如 Bellman optimality>` + 回车
- [ ] 我看到:Claude 输出有 manifest 显示 `[4/5] Read 完整章节: lecture X §Y / lecture Z §W / ... 5 个独立 file ✅`
- [ ] 我看到:输出有 `[5/5] 合成中... Grep 确认: <术语> 仅在 lecture X 出现`
- [ ] 我看到:4 段结构化输出:**严格定义 / 直觉理解 / 1 个反例 / 联系节点**
- [ ] 我看到:每句几乎都有 inline `[[wikilink]]` 引用
- [ ] 我看到:末尾 `Faithfulness X/X · ContextPrecision X/X` 自检(理想 11/11 / 5/5)
- [ ] 我看到:末尾完整 supplementary 列表 dump
- [ ] 我感觉:Claude 主动用 native Grep 自己搜 vault,不需要 Cmd+P 触发 plugin 命令 — 体感快 + 透明可控

### Step 5 — 边界场景:故意制造异常验证降级(可选)

- [ ] 我做:停掉 backend(`Ctrl+C` 在 uvicorn 终端)
- [ ] 我做:按 Cmd+Shift+E
- [ ] 我看到:Status bar 变 `🎓 <vault> · ❌ backend down`
- [ ] 我看到:Notice 显示 `[vault: <id>] ⚠️ backend 超时,用 plugin 端 1-hop 本地降级`
- [ ] 我看到:仍能切 Claudian + 粘贴(降级路径,1-hop local 邻居,质量稍逊但可用)
- [ ] 我感觉:backend 偶发问题不会卡住工作流,降级路径透明

---

## 5. 🚦 验收结果

### 通过条件(全勾或自评满意)

- [ ] Step 1 ✅ Q1 排序合理 + [vault:] 前缀 + Vault: manifest 行
- [ ] Step 2 ✅ Status bar 显示 vault + 三态 + 点击跳 Settings
- [ ] Step 3 ✅ 切 vault 后邻居不串(如有 2 vault)
- [ ] Step 4 ✅ /study-question 触发 native Grep + Read 5+ file + 4 段输出
- [ ] Step 5 ✅ Backend down 时降级 graceful(可选)

**通过 → 在末尾写**:`wave-1~5 综合 UAT 通过,准备 ship main`

### 不通过

- 用 Cmd+Shift+A 在批注区加 `[!error]+` callout 写问题
- 写清楚:哪个 Step,具体看到什么 vs 期望看到什么,涉及哪个 vault
- 我读批注后 correct-course 调整

---

## 6. 📝 批注区(用 Cmd+Shift+A)

```
> [!question]+
> 

> [!error]+
> 

> [!tip]+
> 
```

### 已知的已批注问题(历史追溯)

无 — 本 UAT 是 wave-1~5 综合首次验收。

如此前对单个 wave UAT 已有反馈,本 UAT 是整体闭口确认(预期已 fix)。

---

## 7. 🔗 技术 spec 引用(给 Claude 读的,你不用看)

### Commit 列表(按时间)
- `549d5f0` T3+T5 rerank engine
- `de0b4a7` Q1+Q2+Q3 wave-1 hotfix
- `f018580` Wave-2 五 P0 (ChatGPT v2)
- `828c331` Tauri @deprecated
- `ec58ee0` Wave-3 P1 (ChatGPT v4 + Claude self-audit)
- `46fc501` Wave-4 Q3 rollback + SKILL.md native Grep
- `e0d9a17` Wave-5 Stage A Frontend UX
- `4104020` Wave-5 Stage B core (36 endpoints)
- `79da746` Wave-5 Stage C P1 + integration
- `1d70c85` Wave-5 Stage B 续 (35 endpoints)

### 关键 file:line(分领域)

**Q1 RAG 精度**:
- `backend/app/services/supplementary_reranker.py` (rerank engine + TYPE_WEIGHTS 过渡 + filter floor)
- `backend/app/services/supplementary_search_service.py` (chunk-link-list filter + tier-2 env gate + metadata redaction + multi-field taint scan)
- `backend/app/services/rerank_service.py` (BM25 自实现)

**Q2 Multi-vault**:
- `backend/app/api/v1/endpoints/_vault_id_resolver.py` (共享 helper,9 file 复用)
- `backend/app/services/wikilink_graph_service.py` (per-vault dict + lazy build)
- `backend/lib/agentic_rag/clients/lancedb_client.py:active_vault_id` (ContextVar 4 级 fallback)
- `backend/app/services/event_bus.py` + `error_writer.py` + `canvas_service.py` + ... (asyncio.create_task copy_context)
- `backend/app/services/memory_service.py` (legacy build_group_id → build_vault_group_id)
- `backend/app/services/react_agent.py` (DEFAULT_GROUP_ID → ContextVar)
- 71 endpoint files (vault_id 注入)

**Q3 SKILL native Grep**:
- `canvas-vault/.claude/skills/study-question/SKILL.md` v1.6 HARD-21
- `canvas-vault/.claude/skills/chat-with-context/SKILL.md` v2.1 HARD-19

**Frontend UX**:
- `frontend/obsidian-plugin/src/main.ts` (buildBackendHeaders + 4 hotkey Notice + status bar)
- `frontend/obsidian-plugin/src/vault-indicator.ts` (pure helper)

**Integration test**:
- `backend/tests/integration/test_multi_vault_isolation.py` (12 tests)

### 测试统计
- Backend unit + security: 262+ pass / 4 xfailed / 1 pre-existing fail (Story 2.5.Y D16 旧格式,无关)
- Frontend: 193/193 pass + 22 new vault-indicator
- Integration: 12/12 pass (cross-vault isolation)
- 共 ~100+ new tests across all waves

### PLAN-ID
EPIC1-BMAD-DEV-ASSESS-2026-04-17

---

*Generated 2026-05-13. 7 段结构 + DoD-3 双段铁律 (段 4-A Claude 已代验 + 段 4-B 你来验)。如批注区有 [!error]+/[!tip]+,启 correct-course 流程。*
