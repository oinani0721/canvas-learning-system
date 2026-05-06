---
story: "2.5.X"
title: "用户主权回归 — 渐进式确认 (D15 = C+)"
status: "review"
version: "v1.0"
date: "2026-05-05"
developer: "Claude Code (Opus 4.7)"
plan_id: "EPIC2-BMAD-DEV-D15-2026-05-05"
parent_story: "2.5"
parent_ship_commit: "0d05ad8"
this_story_ship_commit: "99a8586"
chatgpt_round2_commit_ready: "8.5/10"
test_summary: "Backend 167 + Plugin 104 = 271 全 pass, 0 regression"
---

# Story 2.5.X 验收单 v1.0 — 用户主权回归 C+ 方案

> [!info]+ 这是什么？给非技术你（PM）读的版本
> Story 2.5 v1.0 是 AI 自动判错（你的批注："违背双链/callout 哲学"）。
> Story 2.5.X 把它**降级为草稿**：AI 判错后**先放草稿区**，由你**主动确认**才进入正式 errors[]。
>
> 这次 ship：
> - **3 个 Obsidian 命令**（接受 / 异议 / 标记 AI 误判）让你直接 Cmd+P 操作
> - **Dashboard 加 "📋 待复盘错误候选"** 实时显示待处理数量
> - **后端 4 个新 endpoint**（accept / dismiss / dispute / rebuild-graphiti）
> - **30 天自动归档**（cron service 已写, lifespan 集成在 2.5.X.1）
> - **271 测试 pass**（Backend 167 + Plugin 104）
>
> 技术细节在 `_bmad-output/implementation-artifacts/epic-2/2-5-x-*.md`（Claude 读，你不用看）。

---

## 🎯 这个 Story 要做到什么（一句话）

**AI 判错后先写到笔记的"草稿区"（`error_candidates[]`），你 Cmd+P 主动确认才会移入正式"错题本"（`errors[]`）+ 同步知识图谱——AI 不再替你做最终决定，你才是数据主人。**

---

## 📖 用户故事（你的视角）

**作为** 用 AI 学习概念但又重视**数据主权**的 CS 61B 学生，
**我想** 让 AI 检测到的"可能误解"先进入**草稿区**等我审核（不直接污染我的正式错题本），
**以便** 我能像编辑双链/callout 一样**主动接受 / 编辑 / 否决**这些 AI 判断——保持双链/批注/AI 判错三套系统的**主动性一致**。

---

## ⚠️ 重要：本轮 UAT 是 "Phase B 局部 demo"

> [!warning]+ 必读 — 当前已通的 vs 还没接入的
>
> **✅ 已通的（本轮 UAT 验证）**：
> - 4 个 backend endpoint（accept/dismiss/dispute/rebuild-graphiti）
> - 3 个 Obsidian Cmd+P 命令（直接调上面 endpoint）
> - Dashboard "📋 待复盘错误候选" Dataview 渲染
> - 6 状态机校验（合法/非法转换 → 422）
> - 271 单元/集成测试
>
> **⏸️ 还没接入的**（Story 2.5.X.1 / 2.5.Y 做）：
> - `post-turn-extract` 仍是 v1.0 行为（写 errors[] 直接），**不**默认走 candidate 路径
>   → 这意味着**当前对话不会自动产生 candidate**，UAT 时需**手动准备** frontmatter 数据测
> - expired cron 是 service 函数，**没接 lifespan hook**（用户手动调测试）
> - vault_id / group_id 强化（Story 2.5.Y 做）
>
> **本轮 UAT 玩法**：
> 1. 你**手动构造**一个测试节点的 frontmatter `error_candidates[]` 数组（粘贴一段 yaml）
> 2. 在 Obsidian 用 **Cmd+P** 触发 3 个新命令测试 accept/dismiss/dispute
> 3. 看 Dashboard 列表 + frontmatter 字段变化
> 4. **本轮不验证**：post-turn-extract 自动写 candidate（Story 2.5.X.1 后才能验）

---

## 🖥️ 你会看到的交互（流程图）

```
准备阶段（5 分钟）
─────────────────────────────────────────────────────
1. 后端启动（一次, 跑完别关）
       ↓
2. Cmd+Q 关 Obsidian → 重开（让新 main.js 加载, 106348B）
       ↓
3. 创建测试节点 节点/UAT-2.5.X-test.md
   含手动准备的 error_candidates[] (1 条 pending)
       ↓

主流程 5 步（每步 ~1-2 分钟）
─────────────────────────────────────────────────────
4. 打开 Dashboard.md → 看到 "📋 待复盘错误候选 1 条"
       ↓
5. 切回 测试节点 → Cmd+P → "接受错误候选"
       ↓
6. 弹 SuggestModal 显示 "🟢 学生混淆 admissibility 与 consistency..."
       ↓
7. 选条 → 后台调 POST /accept-candidate
       ↓
8. Notice "✓ 已接受, 移入 errors[] (Graphiti: queued)"
       ↓
9. 重新打开节点 → frontmatter:
   - errors[] 多了 1 条 (含 source=user_confirmed_ai / from_candidate_id)
   - error_candidates[0].status = "accepted" (草稿区那条改状态)
       ↓
10. 切回 Dashboard → "待复盘 0 条"（accepted 不再 pending）

边界场景 4 步
─────────────────────────────────────────────────────
11. dispute 流程: Cmd+P → "异议候选" → 选条 → 输理由 → status=disputed
12. dismiss 流程: Cmd+P → "标记 AI 误判" → 选条 → status=dismissed
13. 双重 accept: 已 accepted 的再 accept → 422
14. rebuild-graphiti: curl dry_run=true 看 stats
```

---

## ✅ 验收清单（19 步 UAT，约 25 分钟）

> [!tip]+ 怎么用这份清单
> - 每跑完一步，**点击 `- [ ]`** → 切换为 `[x]`（Obsidian 原生）
> - 发现不对劲 → **选中那一行 → `Cmd+Shift+A` → 选 ❌ 错误**，写实际现象
> - 看不懂某步 → 用 `Cmd+Shift+A` 选 ❓ 提问，Claude 会回

### 第 0 步：前置（必须做，3 项）

#### P1 · 后端已启动

- [ ] 终端跑（**不要关此终端**）：
  ```bash
  cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend
  python start_server.py
  ```
- [ ] 看到 `Application startup complete` 或 `Uvicorn running on http://0.0.0.0:8001`
- [ ] **快速验证 4 endpoint 注册**（方法 A: OpenAPI URL 修正版）：
  ```bash
  # ⚠️ OpenAPI 实际路径是 /api/v1/openapi.json (main.py:379 openapi_url 配置)
  curl -s http://localhost:8001/api/v1/openapi.json | grep -o '"/api/v1/errors/[^"]*"' | sort -u
  ```
  应输出 4 行：
  ```
  "/api/v1/errors/accept-candidate"
  "/api/v1/errors/dismiss-candidate"
  "/api/v1/errors/dispute-candidate"
  "/api/v1/errors/rebuild-graphiti"
  ```

- [ ] **方法 B（备选, 不启动 backend 也能验证）**：
  ```bash
  cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend
  PYTHONPATH=. /Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/bin/python -c "
  from app.main import app
  required = {'/api/v1/errors/accept-candidate', '/api/v1/errors/dismiss-candidate',
              '/api/v1/errors/dispute-candidate', '/api/v1/errors/rebuild-graphiti'}
  registered = {r.path for r in app.routes if hasattr(r, 'path')}
  missing = required - registered
  print('✅ All 4 endpoints registered' if not missing else f'❌ Missing: {missing}')
  "
  ```
  预期输出: `✅ All 4 endpoints registered`

- [ ] **方法 C（最简单, 直接试 endpoint 是否响应）**：
  ```bash
  for ep in accept-candidate dismiss-candidate dispute-candidate rebuild-graphiti; do
    code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://localhost:8001/api/v1/errors/${ep}" -H 'Content-Type: application/json' -d '{}')
    echo "  /errors/${ep} → HTTP $code"
  done
  ```
  预期: 4 个 endpoint 都返回 422 (schema 校验) 或 404 (resource 缺失) 而非 405 (method) / 不存在

#### P2 · Obsidian 已重启 + main.js 是新版

- [ ] `Cmd+Q` 完全关 Obsidian → 重开
- [ ] 验证 main.js 是 Story 2.5.X 版本：
  ```bash
  stat -f "%z" /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/canvas-vault/.obsidian/plugins/canvas-learning-system/main.js
  ```
  应输出 **`106348`**（v1.0 是 88684）
- [ ] vault 是 `canvas-vault/`（左下角显示 vault 名）
- [ ] Settings → Community plugins → Canvas Learning System ✅ 已启用

#### P3 · 准备测试节点（含手动 error_candidates[]）

- [ ] 在 `节点/` 下新建 `UAT-2.5.X-test.md`
- [ ] **完整粘贴**以下内容（注意 yaml 缩进！）：

```markdown
---
type: concept
board_name: UAT-2.5.X
mastery_score: 0.30
errors: []
error_candidates:
  - id: "uat-cand-001"
    status: pending
    source: ai_suggested
    node_id: "节点/UAT-2.5.X-test.md"
    session_id: "s-uat-2026-05-05-001"
    group_id: "cs_61b:main"
    candidate_dedupe_hash: "uat001hash000abc"
    pedagogy_type: conceptual_confusion
    legacy_type: knowledge_gap
    legacy_remedy: backtrack_definition
    description: "学生混淆了 admissibility 和 consistency, 认为它们等价"
    context: "对话第 3 轮"
    ai_reason: null
    evidence_turns: []
    raw_dialog_excerpt: null
    confidence: 0.85
    confidence_source: llm
    sub_tags: [synonym_confusion]
    suggested_remedy_strategies: [discrimination_comparison]
    created_at: "2026-05-05T08:00:00+00:00"
    last_seen_at: "2026-05-05T08:00:00+00:00"
    seen_count: 1
    seen_sessions: [s-uat-2026-05-05-001]
    status_changed_at: null
    status_changed_by: null
  - id: "uat-cand-002"
    status: pending
    source: ai_suggested
    node_id: "节点/UAT-2.5.X-test.md"
    session_id: "s-uat-2026-05-05-001"
    group_id: "cs_61b:main"
    candidate_dedupe_hash: "uat002hash000def"
    pedagogy_type: procedural_error
    legacy_type: reasoning_fallacy
    legacy_remedy: counterexample_construction
    description: "因果倒置: 把 'h ≤ optimal cost' 推成 admissibility 的因"
    context: "对话第 5 轮"
    confidence: 0.55
    confidence_source: llm
    sub_tags: []
    suggested_remedy_strategies: [error_finding]
    created_at: "2026-05-05T08:01:00+00:00"
    last_seen_at: "2026-05-05T08:01:00+00:00"
    seen_count: 1
    seen_sessions: [s-uat-2026-05-05-001]
    status_changed_at: null
    status_changed_by: null
---

# UAT-2.5.X-test

这是 Story 2.5.X 用户主权 C+ 测试节点。frontmatter 已手动准备 2 条 pending candidates。
```

- [ ] **保存**（Cmd+S）→ 保持文件打开
- [ ] 切到 **Reading view** (Cmd+E) → frontmatter 应显示为 Properties panel（如果没显示就保持 Edit view 也行）

---

### 主流程 5 步（覆盖 5 endpoint + 6 状态机 + 7 个 AC）

#### V1 · Dashboard Dataview 保活渲染（AC #4）

**你做的事**：
- [ ] 打开 vault 根的 `Dashboard.md`
- [ ] 滚到 "📋 待复盘错误候选" section（在 "⏰ 待复习 (FSRS 到期)" 上方）

**你应该看到**：

- [ ] **总览表**显示 6 状态机各状态数：
  - `⏳ pending`：**2** ✅
  - `✅ accepted`：0
  - `✗ dismissed`：0
  - `⚠️ disputed`：0
  - `🗄️ expired`：0
- [ ] **"⏳ 待复盘 2 条 (按节点分组)"** 标题
- [ ] 节点链接 `[[UAT-2.5.X-test]]` (2 条)
- [ ] 每条候选显示：
  - 🟢 (uat-cand-001 confidence=0.85, 高置信)
  - 🔴 (uat-cand-002 confidence=0.55, 低置信)
  - description 截断 + pedagogy_type + confidence + seen_count + last_seen 时间
- [ ] 引导文本："`Cmd+P` 搜 \"接受错误候选\" / \"异议错误候选\" → 选条处理"

**你不应该看到**：
- [ ] ❌ "暂无待复盘的错误候选"（说明 Dataview 没读到 frontmatter，可能 yaml 格式错）
- [ ] ❌ JS 报错红字（按 F12 看 Console）

---

#### V2 · 接受错误候选（AC #5）

**你做的事**：
- [ ] 切回 `节点/UAT-2.5.X-test.md`（让它 active file）
- [ ] **Cmd+P** → 输入 "接受错误候选" → Enter

**你应该看到**：

- [ ] 弹 **CandidateSuggestModal** placeholder："选择要接受的错误候选"
- [ ] 列表 2 条：
  - `🟢 学生混淆了 admissibility 和 consistency... (conceptual_confusion, conf=0.85, seen=1)`
  - `🔴 因果倒置: 把 'h ≤ optimal cost' 推成... (procedural_error, conf=0.55, seen=1)`
- [ ] 选第 1 条（uat-cand-001）→ Enter
- [ ] 几秒钟后右下角弹 Notice：
  - ✅ **`✓ 已接受 → errors[] (Graphiti: queued)`**

**回 Obsidian 验证 frontmatter**：

- [ ] **关闭再重新打开** `UAT-2.5.X-test.md`（让 Obsidian 重新读 frontmatter）
- [ ] **errors[]** 数组应**多 1 条**：
  ```yaml
  errors:
    - id: uat-cand-001          # 复用 candidate_id
      type: conceptual_confusion
      legacy_type: knowledge_gap
      description: "学生混淆了 admissibility..."
      source: user_confirmed_ai  # ⭐ 主权字段
      user_confirmed: true       # ⭐ 主权字段
      user_confirmed_at: "2026-05-05T..."
      from_candidate_id: uat-cand-001  # ⭐ 追溯字段
      seen_count: 1
      ...
  ```
- [ ] **error_candidates[0]**（即 uat-cand-001）应：
  - `status: accepted` （从 pending 改）
  - `status_changed_at: "2026-05-05T..."` （ISO 8601）
  - `status_changed_by: user`
- [ ] error_candidates[1]（uat-cand-002）保持 **pending**（没动）

**你不应该看到**：
- [ ] ❌ Notice "❌ 失败" 或后端 4xx/5xx
- [ ] ❌ errors[] 没新增（说明 endpoint 没写入）
- [ ] ❌ candidate.status 还是 pending（说明状态机没改）

---

#### V3 · 异议候选（AC #7 dispute path）

**你做的事**：
- [ ] **Cmd+P** → "异议错误候选" → Enter
- [ ] SuggestModal 显示 1 条（仅 uat-cand-002 还 pending）
- [ ] 选 uat-cand-002 → Enter
- [ ] 弹 **DisputeReasonModal**：
  - 标题 "异议错误候选 — 写下你的理由"
  - 提示 "请说明为何认为 AI 误判..."
  - textarea placeholder "例如: 我没把 X 当成 Y..."
- [ ] 输入理由："我不是因果倒置, 只是问 admissibility 和 optimal cost 的关系"
- [ ] 点 **✅ 提交异议**（蓝色 mod-cta 按钮）

**你应该看到**：

- [ ] Notice：**`⚠ 已标记 disputed + 写入理由`**
- [ ] 重新打开节点 → frontmatter:
  ```yaml
  error_candidates:
    - id: uat-cand-001
      status: accepted          # V2 已改
    - id: uat-cand-002
      status: disputed          # ⭐ 改为 disputed
      dispute_reason: "我不是因果倒置, 只是问 admissibility 和 optimal cost 的关系"  # ⭐ 写入
      status_changed_at: "..."
      status_changed_by: user
  ```
- [ ] **errors[]** 仍只有 1 条（V2 的）— **不应**为 disputed 写入

**你不应该看到**：
- [ ] ❌ errors[] 多了 1 条（dispute 不应写正式错题本）
- [ ] ❌ dispute_reason 字段缺失

---

#### V4 · 标记 AI 误判（AC #7 dismiss path）

**你做的事**：
- [ ] 在 frontmatter 手动加一条新 candidate（因为已用完 2 条）：

  ```yaml
  - id: "uat-cand-003"
    status: pending
    source: ai_suggested
    node_id: "节点/UAT-2.5.X-test.md"
    session_id: "s-uat-2026-05-05-002"
    group_id: "cs_61b:main"
    candidate_dedupe_hash: "uat003hash000ghi"
    pedagogy_type: careless_slip
    legacy_type: problem_framing
    legacy_remedy: backtrack_definition
    description: "粗心遗漏 base case 条件"
    context: "对话第 7 轮"
    confidence: 0.40
    confidence_source: llm
    sub_tags: []
    suggested_remedy_strategies: [isomorphic_practice]
    created_at: "2026-05-05T08:02:00+00:00"
    last_seen_at: "2026-05-05T08:02:00+00:00"
    seen_count: 1
    seen_sessions: [s-uat-2026-05-05-002]
    status_changed_at: null
    status_changed_by: null
  ```

- [ ] 保存 → **Cmd+P** → "标记错误候选为 AI 误判（dismiss）" → Enter
- [ ] 选 uat-cand-003 → Enter

**你应该看到**：

- [ ] Notice：**`✗ 已标记为 AI 误判 (dismissed)`**
- [ ] 重新打开节点 → uat-cand-003 `status: dismissed`
- [ ] **errors[]** 仍只有 1 条（dismiss 不应写正式错题本）

---

#### V5 · rebuild-graphiti 兜底（AC #6）

**你做的事**：

- [ ] 在另一个终端跑：

  ```bash
  curl -X POST 'http://localhost:8001/api/v1/errors/rebuild-graphiti?group_id=vault:cs_61b&dry_run=true' | python -m json.tool
  ```

**你应该看到**（dry_run=true 仅扫描计数）：

```json
{
  "group_id": "vault:cs_61b",
  "dry_run": true,
  "total_files_scanned": <N>,        // 节点/ 下 .md 数量
  "total_errors_scanned": 1,          // 至少 1 (V2 accept 的那条)
  "newly_written": 0,                 // dry_run 不写
  "failed": 0,
  "failures": [],
  "elapsed_ms": <数字>
}
```

- [ ] `total_errors_scanned >= 1` ✅
- [ ] `newly_written = 0` ✅（dry_run）
- [ ] 改 `dry_run=false` 实际写：

  ```bash
  curl -X POST 'http://localhost:8001/api/v1/errors/rebuild-graphiti?group_id=vault:cs_61b&dry_run=false' | python -m json.tool
  ```

- [ ] `newly_written >= 1` ✅（实际写入）
- [ ] `failed: 0` （或如果 Graphiti 没启 → failures[] 含错误信息但**不阻塞**）

> ⚠️ 如果 Graphiti / Neo4j 没启 → `failed > 0`，**这是预期的**（rebuild 设计为单条失败不中断）

---

### 边界场景 9 步（每步 < 1 分钟）

#### V6 · 双重 accept 拒绝（状态机反向不可逆）

- [ ] **Cmd+P** → "接受错误候选"
- [ ] **预期**：Modal 弹但**只显示 0 条**（uat-cand-001 已 accepted, 002 disputed, 003 dismissed → 全是终态 → 没 pending）
- [ ] 或显示 Notice "当前节点无待复盘错误候选" ✅

> 📌 这验证 `filterPendingCandidates` 只显示 pending 的实现正确。

---

#### V7 · 终态间转换被拒（直接 curl）

- [ ] 直接调 endpoint 试图把已 accepted 的 cand-001 再 accept：

  ```bash
  curl -X POST 'http://localhost:8001/api/v1/errors/accept-candidate' \
    -H 'Content-Type: application/json' \
    -d '{
      "candidate_id": "uat-cand-001",
      "node_id": "节点/UAT-2.5.X-test.md"
    }' | python -m json.tool
  ```

**预期**：
- [ ] HTTP **422**
- [ ] response 含 `"detail": "Illegal status transition: 'accepted' is a terminal state..."`

---

#### V8 · dispute 空理由被拒

- [ ] 直接 curl 测试空 dispute_reason：

  ```bash
  curl -X POST 'http://localhost:8001/api/v1/errors/dispute-candidate' \
    -H 'Content-Type: application/json' \
    -d '{
      "candidate_id": "uat-cand-002",
      "node_id": "节点/UAT-2.5.X-test.md",
      "dispute_reason": ""
    }' | python -m json.tool
  ```

**预期**：
- [ ] HTTP **422**（Pydantic min_length=1 校验）

---

#### V9 · 不存在 candidate 返回 404

- [ ] 直接 curl 测试不存在 candidate_id：

  ```bash
  curl -X POST 'http://localhost:8001/api/v1/errors/accept-candidate' \
    -H 'Content-Type: application/json' \
    -d '{
      "candidate_id": "fake-id-doesnt-exist",
      "node_id": "节点/UAT-2.5.X-test.md"
    }' | python -m json.tool
  ```

**预期**：
- [ ] HTTP **404**
- [ ] detail 含 "not found"

---

#### V10 · expire cron service（手动调用）

> 当前 expire cron 还没接 lifespan hook（Story 2.5.X.1 做），但 service 函数可手动调测。

- [ ] 准备测试 frontmatter，手动加一条**老 created_at**（< 30 天前）的 pending candidate：

  ```yaml
  - id: "uat-cand-old-001"
    status: pending
    created_at: "2026-04-01T00:00:00+00:00"   # 30+ 天前
    # ... 其他字段同上 ...
  ```

- [ ] 在 backend 跑 Python REPL（在 backend 目录）：

  ```bash
  PYTHONPATH=. /Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/bin/python -c "
  import asyncio
  from app.services.candidate_expiry_service import expire_pending_candidates
  result = asyncio.run(expire_pending_candidates(
      '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/canvas-vault',
      expiry_days=30,
  ))
  print(result.model_dump_json(indent=2))
  "
  ```

**预期**：
- [ ] `total_expired >= 1`（uat-cand-old-001 被 expire）
- [ ] 重新打开节点 → uat-cand-old-001 `status: expired` + `status_changed_by: system`
- [ ] Dashboard 总览表 `🗄️ expired` 计数 +1

---

### Esc 取消（V11-V12）

#### V11 · CandidateSuggestModal Esc 取消

- [ ] 准备一个新 pending candidate（手动加 frontmatter）
- [ ] **Cmd+P** → "接受错误候选" → Modal 弹出
- [ ] 按 **Esc**

**预期**：
- [ ] Modal 关闭 ✅
- [ ] **不**调 backend ✅
- [ ] **不**改 frontmatter ✅

---

#### V12 · DisputeReasonModal Esc 取消

- [ ] 准备一个新 pending candidate
- [ ] **Cmd+P** → "异议错误候选" → 选条 → DisputeReasonModal 弹出
- [ ] 在 textarea 输点字（如 "test"）
- [ ] 按 **Esc**

**预期**：
- [ ] Modal 关闭 ✅
- [ ] candidate.status 仍是 **pending**（没改）✅
- [ ] **不**写 dispute_reason 到 frontmatter ✅

---

### 跨 Session dedupe（V13-V14）

> 验证 Task 8 — session_id 累加但不进 dedupe hash

#### V13 · 跨 session 同错误 → 1 candidate + seen_sessions 累加

> 因 chat.py 没切默认 candidate_only，本场景**模拟测试**（用 curl 触发 backend service）

- [ ] 在 Python REPL 跑（模拟 3 个 session 写同一错误）：

  ```bash
  PYTHONPATH=. /Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/bin/python -c "
  import asyncio
  from app.services.error_writer import write_error_dual
  from app.services.error_classifier import ClassifiedError
  from app.graphiti.entity_types import ErrorType, PedagogyErrorType, RemedyStrategy

  err = ClassifiedError(
      legacy_type=ErrorType.KNOWLEDGE_GAP,
      pedagogy_type=PedagogyErrorType.CONCEPTUAL_CONFUSION,
      description='V13 测试: 跨 session dedupe',
      context='UAT V13',
      confidence=0.85,
      legacy_remedy=RemedyStrategy.BACKTRACK_DEFINITION,
      pedagogy_remedies=[RemedyStrategy.DISCRIMINATION_COMPARISON],
      sub_tags=[],
  )

  fp = '/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/canvas-vault/节点/UAT-2.5.X-test.md'

  async def run():
      r1 = await write_error_dual(fp, err, node_id='节点/UAT-2.5.X-test.md', session_id='s-A')
      r2 = await write_error_dual(fp, err, node_id='节点/UAT-2.5.X-test.md', session_id='s-B')
      r3 = await write_error_dual(fp, err, node_id='节点/UAT-2.5.X-test.md', session_id='s-C')
      print(f'r1: {r1[\"candidate_id\"]}')
      print(f'r2: {r2[\"candidate_id\"]}')
      print(f'r3: {r3[\"candidate_id\"]}')
      print(f'同一 candidate_id: {r1[\"candidate_id\"] == r2[\"candidate_id\"] == r3[\"candidate_id\"]}')

  asyncio.run(run())
  "
  ```

**预期**：
- [ ] 3 次返回同一 `candidate_id`（dedupe hash 不含 session_id）
- [ ] 重新打开节点 → frontmatter:
  - 仅多 **1 条** candidate（不是 3 条）
  - `seen_count: 3`
  - `seen_sessions: [s-A, s-B, s-C]` ✅（去重累加）

---

#### V14 · 不同 description → 不同 hash → 独立 candidate

- [ ] 在同一 REPL session 改 description 后再写：

  ```python
  err2 = ClassifiedError(...同上, description='V14 不同错误内容')
  await write_error_dual(fp, err2, node_id='节点/UAT-2.5.X-test.md', session_id='s-D')
  ```

**预期**：
- [ ] frontmatter `error_candidates[]` 多 **1 条新** candidate（独立 dedupe_hash）

---

### 主权字段验证（V15）

#### V15 · errors[] 含完整主权字段

- [ ] 重新打开节点查看 V2 accept 那条 errors[]
- [ ] 应**精确**含以下字段：
  ```yaml
  errors:
    - id: uat-cand-001
      source: user_confirmed_ai      # ⭐ 主权 (区别于 v1.0 的 ai_auto_extracted)
      user_confirmed: true            # ⭐ 主权
      user_confirmed_at: "..."        # ⭐ 主权时间戳
      from_candidate_id: uat-cand-001 # ⭐ 追溯到原 candidate
      type: conceptual_confusion
      legacy_type: knowledge_gap
      description: "..."
      dedupe_hash: "..."
      ...
  ```

> 📌 这是 Story 2.5.X 与 v1.0 的核心差别：v1.0 errors[] 没有 `user_confirmed` / `from_candidate_id` 字段。

---

### Dashboard 实时刷新（V16）

#### V16 · Dashboard 数字与 frontmatter 同步

- [ ] 切回 `Dashboard.md`
- [ ] 滚到 "📋 待复盘错误候选" section
- [ ] **预期**总览表显示（基于 V2-V14 累计）：
  - `⏳ pending`：约 0-1（除非又加新的）
  - `✅ accepted`：1（V2 那条）
  - `✗ dismissed`：1（V4 那条）
  - `⚠️ disputed`：1（V3 那条）
  - `🗄️ expired`：1（V10 那条 if applicable）

> ⚠️ 如果 Dashboard 没自动刷新，**点 main.js 注册的 "🔄 强制刷新缓存" 按钮**（Story 1.18 v1.1 加的）。

---

### 性能预算（V17）

#### V17 · accept_candidate 响应 < 1 秒

- [ ] 准备一条新 pending candidate
- [ ] 触发 Cmd+P "接受错误候选" → 选条
- [ ] **预期**：从点选 → Notice 出现 < **1 秒**（实际应 100-500ms）
- [ ] curl 直接测响应时间：

  ```bash
  time curl -X POST 'http://localhost:8001/api/v1/errors/accept-candidate' \
    -H 'Content-Type: application/json' \
    -d '{"candidate_id":"<new-id>","node_id":"节点/UAT-2.5.X-test.md"}' > /dev/null
  ```

- [ ] `real` 时间 < 1 秒 ✅

---

### 单元测试快速验证（V18）

#### V18 · backend 167 测试全 pass

- [ ] 跑全套 backend 测试：

  ```bash
  cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend
  PYTHONPATH=. /Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/bin/pytest tests/unit/test_candidate_writer.py tests/unit/test_candidate_state_machine.py tests/unit/test_candidate_service.py tests/unit/test_error_rebuild_service.py tests/unit/test_candidate_expiry_service.py tests/integration/test_2_5_x_e2e.py -q 2>&1 | tail -3
  ```

- [ ] **预期**：`X passed, 0 failed`（应 ≥ 113，含 16+41+14+13+20+10）

---

### Plugin 测试快速验证（V19）

#### V19 · plugin 19+85 测试全 pass

- [ ] 跑 plugin 测试：

  ```bash
  cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/frontend/obsidian-plugin
  npm test 2>&1 | tail -5
  ```

- [ ] **预期**：`# tests 104, # pass 104, # fail 0`

---

## 🚦 验收结果

### 全 19 步 ✅
→ 告诉 Claude **"Story 2.5.X v1.0 通过"**
→ Claude mark `done` + sprint-status 升级
→ 启动 **Story 2.5.X.1**（chat.py 切默认 candidate_only + lifespan cron 集成）
→ 或并行启动 **Story 2.5.Y**（隔离硬化 SubjectConfig 复用 + LanceDB 修漏洞）

### 主流程部分失败（V1-V5 任一 ❌）
→ 在批注区写**哪一步 + 实际现象**（最好截图）
→ Claude 跑 `bmad-bmm-correct-course` 修
→ 重出 v1.1 验收单

### 边界失败（V6-V10 任一 ❌）
→ 阻断分级：
- **V8 dispute_reason 校验失败 = 阻断 ship**（数据完整性）
- **V7 终态转换不被拒 = 阻断 ship**（状态机失效，错题本可能腐败）
- **V11/V12 Esc 取消有副作用 = 阻断 ship**（用户体验破坏）
- V9 404 错误信息不友好 = 不阻断（仅提醒）

### Dashboard 不渲染（V1 失败）
→ 检查 vault 是否装 Dataview plugin（Story 1.18 已要求）
→ Console (Cmd+Opt+I) 看 dataview 报错
→ 检查 frontmatter yaml 缩进（最常见错误）

### 后端起不来（P1 失败）
→ 不算验收失败，先解决环境问题
→ 告诉 Claude："后端 start_server.py 报 [粘贴错误]"

---

## 📝 你的批注区

> [!question]+ Story 2.5.X v1.0 实测批注（2026-05-05 起）
>
> 跑完 19 步任意写下：
> - **Phase B 局部 demo 体验**：手动准备 frontmatter 是否太繁琐？要不要 Story 2.5.X.1 切默认 candidate_only 才能真正端到端？
> - **3 个命令的命名**："接受错误候选" / "标记 AI 误判" / "异议错误候选" — 是否好懂？要不要换成更口语化（如"这个错对" / "AI 判错了" / "我有不同看法"）？
> - **CandidateSuggestModal 显示格式**：`🟢 描述 (pedagogy_type, conf=0.85, seen=2)` — confidence 数字是否有用？还是改成"我很确定 / 我有点不确定 / 我可能错了"更好？
> - **DisputeReasonModal**：textarea 4 行高度够吗？要不要先弹一个常见理由列表（"我没误解" / "AI 上下文不全" / "概念定义有歧义"）让你点选？
> - **Dashboard 总览**：6 状态机 (pending/accepted/edited/dismissed/disputed/expired) 是否信息过载？要不要折叠成"待复盘 / 已处理"两栏？
> - **30 天 expired**：阈值合理吗？要不要 14 天？或者按 mastery_score 调整（弱节点放宽）？
> - **关键质疑**：Story 2.5.X 让 AI 不再替你判错，但**你有真的去复盘吗**？如果你不打开 Dashboard，candidate 仍堆积——是不是该加 Notification（Obsidian 启动时弹"你有 N 条待复盘"）？
>
> （空）

### 已知的已批注问题（历史追溯）

无（v1.0 首次 ship，Story 2.5.X 派生）

<!--
correct-course 后追加 [!error]+ callout 例：
> [!error]+ 2026-05-XX — v1.0 → v1.1 修复
> 你的原批注：[verbatim]
> 根因：[plain]
> 已修复：[summary]
-->

---

## 🔗 技术 spec 参考（给 Claude 读的，不是给你读的）

### Story 2.5.X spec
- **主 spec**：`_bmad-output/implementation-artifacts/epic-2/2-5-x-error-candidate-progressive-confirmation.md`（v1.0 已 ship review）
- **D15 决议**：`_bmad-output/决策批注/D15-D16-用户主权与隔离方案-2026-05-04.md`
- **ChatGPT Round-2 reply**：`_bmad-output/research/chatgpt-round2-reply-story-2.5-sovereignty-isolation-2026-05-04.md`（C+ 8.5/10 commit-ready）

### PRD 锚定
- `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md`
  - §FR-CONV-06 错误自动提取（Story 2.5 v1.0 trace）
  - §3.2 frontmatter `errors[]` schema
  - §12 决策点清单 — 待用户追加 D15 / D16

### 后端代码（Story 2.5.X 新增）
- `backend/app/services/candidate_state_machine.py` — 6 状态机 + apply_status_change
- `backend/app/services/candidate_service.py` — accept/dismiss/dispute service
- `backend/app/services/candidate_expiry_service.py` — expire cron service
- `backend/app/services/error_rebuild_service.py` — rebuild from frontmatter
- `backend/app/api/v1/endpoints/errors.py` — 4 endpoint 注册
- `backend/app/api/v1/router.py` — errors_router prefix=/errors

### 后端代码（Story 2.5.X 改动复用）
- `backend/app/services/error_writer.py` — 加 `write_candidate_to_frontmatter` + `write_error_dual` 双 mode
- `backend/app/api/v1/endpoints/chat.py` — `post-turn-extract` 显式 `mode="write_confirmed"` 兼容 v1.0
- `backend/app/mcp/tools/error_tools.py` — `record_error` MCP 显式 `mode="write_confirmed"`

### Plugin 代码（Story 2.5.X 新增）
- `frontend/obsidian-plugin/src/error-candidate-helpers.ts` — 纯 logic 模块
- `frontend/obsidian-plugin/src/main.ts` — 加 3 命令 + 3 handler + 2 Modal class

### Vault 改动
- `canvas-vault/Dashboard.md` — 加 "📋 待复盘错误候选" Dataview section
- `canvas-vault/.obsidian/plugins/canvas-learning-system/main.js` — 88684B → **106348B**（+17.7KB）

### 测试覆盖
- **Backend 167 passed**:
  - `test_candidate_writer.py` (16) — Task 1
  - `test_candidate_state_machine.py` (41) — Task 2
  - `test_candidate_service.py` (14) — Task 3+4
  - `test_error_rebuild_service.py` (13) — Task 5
  - `test_candidate_expiry_service.py` (20) — Task 9
  - `test_2_5_x_e2e.py` (10) — Task 8+10
  - 53 v1.0 回归（error_writer + extractor + classifier + ChatGPT regression）
- **Plugin 104 passed**:
  - `error-candidate-helpers.test.ts` (19) — Task 7
  - 85 v1.0 回归

### Git commit chain
- `322abf5` — Task 1: candidate writer + dual mode routing
- `d97cfbb` — Task 2: 6 状态机校验 + 状态变更 helper
- `d8eea9a` — Task 3+4: accept/dismiss/dispute endpoints + service 层
- `6aab383` — Task 5: rebuild_graphiti_from_frontmatter 兜底
- `fdb3d8a` — Task 6: Dashboard Dataview 待复盘错误候选保活
- `b2451e5` — Task 7: plugin 命令 + Modal + helpers
- `99a8586` — Tasks 8+9+10: session_id E2E + expired cron + 集成测试 + → review

### AC → 代码 trace 表

| AC # | 验收点 | 代码定位 |
|---|---|---|
| AC #1 | candidate 写 frontmatter 不写 errors[] | `error_writer.write_candidate_to_frontmatter` + `write_error_dual` mode 路由 |
| AC #2 | 6 状态机 + 反向不可逆 | `candidate_state_machine.ALLOWED_TRANSITIONS` + `validate_status_transition` |
| AC #3 | dedupe 不含 session_id | `error_writer._make_dedupe_hash` (复用 v1.0) + `seen_sessions` 累加 |
| AC #4 | Dashboard Dataview 保活 | `canvas-vault/Dashboard.md` "📋 待复盘错误候选" section |
| AC #5 | accept_candidate endpoint | `candidate_service.accept_candidate` + `errors.py::accept_candidate_endpoint` |
| AC #6 | rebuild_graphiti 兜底 | `error_rebuild_service.rebuild_graphiti_from_frontmatter` + endpoint |
| AC #7 | dismiss/dispute 不写 errors[] | `candidate_service.dismiss/dispute_candidate` + `_change_candidate_status_only` |

---

## 📅 下一步（你批完这份单后）

1. **全部 ✅** → 说 **"Story 2.5.X 通过"** → Claude mark done → 启动：
   - **Story 2.5.X.1**（chat.py 切默认 candidate_only + expire cron lifespan 集成 + 8-12h）
   - 或并行 **Story 2.5.Y**（隔离硬化 SubjectConfig 复用 + LanceDB 修漏洞 + 26-35h）
2. **主流程部分 ❌** → 在批注区写清楚 + 截图 → Claude 跑 `bmad-bmm-correct-course` → 重出 v1.1
3. **V8 dispute 校验 / V7 状态机 / V11-V12 Esc 任一失败** → 阻断 ship → 立即停 → 整个 Story 回炉
4. **暂停** → 告诉 Claude "暂停 Story 2.5.X"，状态保持 `review`，可随时回来

---

> [!success]+ Phase B 局部 demo 设计理由（2026-05-05）
>
> Story 2.5.X 选择"先 ship backend infra + plugin 命令 + Dashboard，等 Story 2.5.X.1 切 chat.py 默认"而不是一次性切默认的理由：
>
> 1. **风险隔离**：chat.py 切默认 = breaking change（影响 v1.0 已 ship 行为），单独 ship 让回滚更容易
> 2. **小步快跑**：本轮 ship 5 个 feature（4 endpoint + 3 命令 + Dashboard + cron + E2E），下轮只切默认 + lifespan 集成 → ship 周期可控
> 3. **用户参与早**：你现在就能批注 candidate UX（modal 文案 / 总览表格式 / dispute 流程），Story 2.5.X.1 会基于反馈调整
> 4. **测试覆盖完整**：271 测试已覆盖所有路径（含 chat.py 切默认后的 candidate flow），切默认时仅是 spec change 不是新逻辑
>
> **代价**：本轮 UAT 需要手动准备 frontmatter `error_candidates[]` 数据（V13/V14 用 Python REPL 模拟）。Story 2.5.X.1 后这个代价消失。
