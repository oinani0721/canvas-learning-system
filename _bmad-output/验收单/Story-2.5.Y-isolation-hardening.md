---
story: "2.5.Y"
title: "多 Vault 隔离硬化 — D16 复用 SubjectConfig"
status: "review"
version: "v1.0"
date: "2026-05-05"
developer: "Claude Code (Opus 4.7)"
plan_id: "EPIC2-BMAD-DEV-D16-2026-05-05"
parent_story: "2.5"
parent_ship_commit: "0d05ad8"
sibling_story: "2.5.X (D15 用户主权 C+)"
this_story_ship_commit: "fc7b9dd"
chatgpt_round2_commit_ready: "8.5/10"
test_summary: "Backend 264 + Plugin 124 = 388 全 pass, 0 regression"
---

# Story 2.5.Y 验收单 v1.0 — 多 Vault 隔离硬化

> [!info]+ 这是什么？给非技术你（PM）读的版本
>
> Story 2.5.Y 解决了 ChatGPT Round-2 cross-check 揭露的 **3 个真实漏洞**：
> 1. ⚠️ `error_writer.py:270` 把 `DEFAULT_GROUP_ID="cs188"` 硬编码进 Graphiti 写入 → **任何 vault 数据都被打包到 cs188 命名空间**
> 2. ⚠️ `PostTurnExtractRequest` 没 `vault_id` 字段 → **后端不知道写到哪个 vault**
> 3. ⚠️ `group_id` 命名 3 套并存（`cs188` / `canvas-dev` / `cs_61b:main`）→ 数据混乱
>
> 这次 ship 修了：
> - **统一命名规约 `vault:<vault_id>[:<sub>]`**（如 `vault:cs_61b` / `vault:数学:离散`）
> - **Plugin 自动传 `vault_id`**（从 Obsidian `app.vault.getName()` 推断）
> - **后端 ContextVar 透传 `group_id`** 到所有写入路径（不再硬编码）
> - **Cypher 防御性 helper** 强制 `WHERE n.group_id = $group_id`（防忘传跨 vault 泄漏）
> - **迁移脚本** dry_run 模式（旧 `cs188/canvas-dev` → `vault:default`）
> - **388 测试 pass**（Backend 264 + Plugin 124）
>
> 技术细节在 `_bmad-output/implementation-artifacts/epic-2/2-5-y-*.md`（Claude 读，你不用看）。

---

## 🎯 这个 Story 要做到什么（一句话）

**未来你有多个 vault（CS 61B / 数学 / 机器学习）时，每个 vault 的错误数据物理隔离——AI 检测到的 cs_61b 错误绝不污染数学 vault 的查询结果，靠"vault: 前缀"统一命名 + 类型强制 + 防御性 Cypher 校验。**

---

## 📖 用户故事（你的视角）

**作为** 未来可能开多个 vault 的 CS 61B 学生，
**我想** 让每个 vault 的学习数据（错误 / 节点 / 关系）**物理隔离**到独立 namespace，
**以便** 我能放心同时学多门课，**不担心**：
- AI 把 cs_61b 错误推荐到数学 vault
- Graphiti 检索跨学科污染
- 切 vault 时数据"串台"

---

## ⚠️ 重要：本轮 UAT 是 "Backend-heavy 验证"

> [!warning]+ 必读 — 用户感知 vs 后端变化
>
> Story 2.5.Y **绝大部分改动在后端**，用户在 Obsidian 里**看不到大变化**。验证主要靠：
> - **curl 后端 endpoint** 看响应（vault_id 必填 / Cypher 防御）
> - **Neo4j Browser**（http://localhost:7478）看 group_id 字段
> - **后端日志**（structlog JSON 输出）看 ContextVar 注入
> - **Plugin 命令** 用 Cmd+P 触发，但后端会自动收到 vault_id（无 UI 变化）
>
> **本轮验证**（19 步）：
> - 后端 schema vault_id 必填校验（V1）
> - Plugin 端自动注入 vault_id（V2）
> - error_writer ContextVar 优先链路（V3）
> - cypher_helpers 防御性（V4）
> - 迁移脚本 dry_run（V5）
> - LanceDB Story 1.9 隔离仍 work（V6）
> - 两 vault 同名节点不串（V7）
> - 边界场景（V8-V13）
> - 测试快验（V14-V15）
>
> **本轮不验证**：
> - per-group physical export 实际跑（Task 7 用 2.5.X rebuild_graphiti 替代）
> - Neo4j 全 codebase Cypher 调用替换（Task 5.3 留待后续）

---

## 🖥️ 你会看到的交互（流程图）

```
Story 2.5.Y 隔离链路（用户透明）
─────────────────────────────────────────────────────
Obsidian Cmd+P "接受错误候选"
       ↓
Plugin handler 调 inferVaultId(app.vault.getName())  ← 自动推断
       ↓
buildAcceptPayload(cand.id, node, { vaultId: "cs_61b" })  ← 注入 payload
       ↓
POST /api/v1/errors/accept-candidate { vault_id: "cs_61b", ... }
       ↓
Backend Pydantic vault_id 校验  ← 缺则 422
       ↓
build_vault_group_id("cs_61b") → "vault:cs_61b"  ← 统一前缀
       ↓
set_current_subject_id("vault:cs_61b") → ContextVar  ← 注入请求级
       ↓
write_error_to_graphiti() 优先 ContextVar  ← Task 3 不再硬编码
       ↓
memory_service.record_knowledge_entity(group_id="vault:cs_61b")
       ↓
Neo4j Misconception node.group_id = "vault:cs_61b"  ← 隔离落地

UAT 主流程 (15-20 分钟)
─────────────────────────────────────────────────────
1. curl post-turn-extract 不传 vault_id → 422
2. 用 Cmd+P "接受错误候选" 触发, 看后端日志 vault_id 透传
3. Neo4j Browser 看 group_id 是否 vault: 前缀
4. curl cypher 测试空 group_id 抛错
5. Python REPL 跑迁移 dry_run
6. 准备 2 个 vault 测同名节点不串
```

---

## ✅ 验收清单（15 步 UAT，约 30 分钟）

> [!tip]+ 怎么用这份清单
> - 每跑完一步，**点击 `- [ ]`** → 切换为 `[x]`（Obsidian 原生）
> - 发现不对劲 → **选中那一行 → `Cmd+Shift+A` → 选 ❌ 错误**
> - 看不懂某步 → 用 `Cmd+Shift+A` 选 ❓ 提问，Claude 会回

### 第 0 步：前置（必须做，3 项）

#### P1 · 后端已启动 + Story 2.5.Y endpoint 就绪

- [ ] 终端跑（**不要关此终端**）：
  ```bash
  cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend
  python start_server.py
  ```
- [ ] 看到 `Application startup complete`
- [x] **快速验证 Story 2.5.Y schema 已生效**（方法 A: OpenAPI URL 修正版）：
  ```bash
  # ⚠️ OpenAPI 实际路径是 /api/v1/openapi.json (main.py:379 openapi_url 配置)
  curl -s http://localhost:8001/api/v1/openapi.json | python3 -c "
  import json, sys
  spec = json.load(sys.stdin)
  comps = spec.get('components', {}).get('schemas', {})
  req = comps.get('PostTurnExtractRequest', {})
  print('vault_id in props:', 'vault_id' in req.get('properties', {}))
  print('vault_id required:', 'vault_id' in req.get('required', []))
  "
  ```
  应输出：
  ```
  vault_id in props: True
  vault_id required: True
  ```

- [x] **方法 B（备选, 直接 curl 触发 422 验证）**：
  ```bash
  curl -s -o /dev/null -w "缺 vault_id → HTTP %{http_code}\n" \
    -X POST 'http://localhost:8001/api/v1/chat/post-turn-extract' \
    -H 'Content-Type: application/json' \
    -d '{"node_id":"x","session_id":"s","messages":[{"role":"user","content":"a"}]}'
  ```
  应输出: `缺 vault_id → HTTP 422` ✅

- [x] **方法 C（不启动 backend 静态验证）**：
  ```bash
  cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend
  PYTHONPATH=. /Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/bin/python -c "
  from app.api.v1.endpoints.chat import PostTurnExtractRequest
  fields = PostTurnExtractRequest.model_fields
  required = [name for name, f in fields.items() if f.is_required()]
  print(f'vault_id in fields: {\"vault_id\" in fields}')
  print(f'vault_id required: {\"vault_id\" in required}')
  print(f'subject_id in fields: {\"subject_id\" in fields}')
  print(f'canvas_path in fields: {\"canvas_path\" in fields}')
  "
  ```
  应输出 4 行 True/False, 其中 vault_id 两行均 True

#### P2 · Plugin main.js 是 2.5.Y 版本

- [ ] `Cmd+Q` 完全关 Obsidian → 重开
- [x] 验证 main.js 是 Story 2.5.Y 版本：
  ```bash
  stat -f "%z" /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/canvas-vault/.obsidian/plugins/canvas-learning-system/main.js
  ```
  应输出 **`107299`** 或更大（2.5.X 是 106348B，2.5.Y +951B）
- [ ] vault 是 `canvas-vault/`

#### P3 · Neo4j Browser 可访问（可选，V3/V7 需要）

- [ ] 浏览器打开 `http://localhost:7478`
- [ ] 登录（用户名 `neo4j`，密码见 `.env` 的 `NEO4J_PASSWORD`）
- [ ] 看到 Neo4j Browser 主界面（如果失败 → docker 没启 → 跳过 V3/V7）

---

### 主流程 7 步（覆盖 8 个 AC）

#### V1 · vault_id 必填校验（AC #1）

**你做的事**：

- [x] 用 curl 调 post-turn-extract，**不**传 vault_id：
  ```bash
  curl -i -X POST 'http://localhost:8001/api/v1/chat/post-turn-extract' \
    -H 'Content-Type: application/json' \
    -d '{
      "node_id": "节点/UAT-2.5.Y.md",
      "session_id": "s-uat-Y",
      "messages": [{"role": "user", "content": "test"}]
    }'
  ```

**你应该看到**：

- [x] **HTTP `422 Unprocessable Entity`** ✅
- [ ] response body 含 `"loc": ["body", "vault_id"]` 和 `"type": "missing"`

**加上 vault_id 重试**：

- [x] ```bash
  curl -i -X POST 'http://localhost:8001/api/v1/chat/post-turn-extract' \
    -H 'Content-Type: application/json' \
    -d '{
      "node_id": "节点/UAT-2.5.Y.md",
      "session_id": "s-uat-Y",
      "vault_id": "cs_61b",
      "messages": [{"role": "user", "content": "test"}]
    }'
  ```
- [x] **HTTP 200** ✅（即使返回 `extracted_count: 0`，schema 校验已通过）

**你不应该看到**：

- [ ] ❌ 不传 vault_id 时仍 200（schema 校验失效）
- [ ] ❌ vault_id="" 空字符串通过（`min_length=1` 失效）

---

#### V2 · Plugin 自动注入 vault_id（AC #1 + Task 9）

**你做的事**：

- [ ] 准备测试节点（参考 Story 2.5.X UAT P3，加几条 pending candidate）
- [ ] 切到 `节点/UAT-2.5.X-test.md`（重用 2.5.X 的测试节点）
- [ ] **打开后端日志终端**（运行 `python start_server.py` 那个）
- [ ] **Cmd+P** → "接受错误候选" → 选条 → Enter

**你应该在后端日志看到**：

- [ ] 一条 structlog JSON log，含字段类似：
  ```json
  {
    "event": "candidate_service.accepted",
    "candidate_id": "uat-cand-XXX",
    "error_id": "uat-cand-XXX",
    ...
  }
  ```
- [ ] `accept-candidate` 请求体（如启用 access log）含 `"vault_id":"canvas-vault"`（plugin 推断的）或 `"cs_61b"`（如 Settings 配置）

> 💡 **如果后端没 access log** → 直接看 Plugin 端 Console（Cmd+Opt+I）→ Network tab → POST /accept-candidate → request payload 里应有 `vault_id` 字段。

**你不应该看到**：

- [ ] ❌ accept-candidate 返回 422（说明 plugin 没传 vault_id）
- [ ] ❌ Plugin 控制台报错 "vault_id required"

---

#### V3 · group_id 用 vault: 前缀写入 Neo4j（AC #2 + Task 1）

**你做的事**：

- [ ] 在 V2 之后（已 accept 一个 candidate, Graphiti 异步写入）
- [ ] 等 5-10 秒（fire-and-forget Graphiti 队列处理）
- [ ] 浏览器开 Neo4j Browser `http://localhost:7478`
- [ ] 跑 Cypher：
  ```cypher
  MATCH (m)
  WHERE m.group_id IS NOT NULL
  RETURN DISTINCT m.group_id, count(*) AS cnt
  ORDER BY cnt DESC
  LIMIT 20
  ```

**你应该看到**：

- [ ] 至少一行 group_id 以 **`vault:`** 前缀开头（如 `vault:canvas-vault` 或 `vault:cs_61b`）
- [ ] 同时可能有**老格式**（`cs188` / `canvas-dev`）— 这是 Story 2.5.Y 之前的历史数据，正常

**你不应该看到**：

- [ ] ❌ 全部 group_id 仍是 `cs188`（说明 ContextVar 注入失败）
- [ ] ❌ Story 2.5.Y 之后**新写入**仍走 cs188（看 created_at 字段：新条 group_id 应是 vault: 前缀）

> ⚠️ **如果 Neo4j 没启** → 跳过 V3，看 backend log 找 `error_writer.graphiti_written` 事件确认 group_id 字段。

---

#### V4 · cypher_helpers 防御性（AC #5 + Task 5）

**你做的事**：

- [x] 跑 Python REPL 测试 `cypher_with_group_filter` 校验逻辑：
  ```bash
  cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend
  PYTHONPATH=. /Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/bin/python -c "
  from app.utils.cypher_helpers import cypher_with_group_filter, assert_group_id_required

  # 1. 空 group_id → ValueError
  try:
      cypher_with_group_filter('MATCH (n) RETURN n', '')
      print('FAIL: should have raised')
  except ValueError as e:
      print('PASS: empty group_id rejected:', e)

  # 2. 注入 WHERE 子句
  q, p = cypher_with_group_filter('MATCH (n:Concept) RETURN n', 'vault:cs_61b')
  print('PASS: query includes filter:', 'WHERE n.group_id = \$group_id' in q)
  print('PASS: params:', p)

  # 3. 已有 WHERE 用 AND
  q2, _ = cypher_with_group_filter(
      'MATCH (n) WHERE n.x > 1 RETURN n', 'vault:cs_61b', where_keyword='AND'
  )
  print('PASS: AND injected:', 'AND n.group_id' in q2)

  # 4. assert_group_id_required 防御
  try:
      assert_group_id_required(None, context='UAT V4')
      print('FAIL')
  except ValueError as e:
      print('PASS: assert helper rejects None:', 'UAT V4' in str(e))
  "
  ```

**你应该看到**：

```
PASS: empty group_id rejected: ...
PASS: query includes filter: True
PASS: params: {'group_id': 'vault:cs_61b'}
PASS: AND injected: True
PASS: assert helper rejects None: True
```

**你不应该看到**：

- [ ] ❌ "FAIL: should have raised"（说明防御失效）

---

#### V5 · group_id 迁移脚本 dry_run（AC #6 + Task 6）

**你做的事**：

- [x] 测试 `map_legacy_group_id` 映射规则：
  ```bash
  PYTHONPATH=. /Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/bin/python -c "
  from app.services.group_id_migration_service import map_legacy_group_id, LEGACY_TO_VAULT_MAPPING

  cases = [
      ('cs188', 'vault:default'),
      ('canvas-dev', 'vault:default'),
      ('general', 'vault:default'),
      ('vault:cs_61b', 'vault:cs_61b'),  # 已新格式幂等
      ('cs_61b:main', 'vault:cs_61b:main'),
      ('数学', 'vault:数学'),
      ('CS 61B!', 'vault:cs_61b'),  # sanitize
      ('', 'vault:default'),
  ]
  print('LEGACY_TO_VAULT_MAPPING:', dict(LEGACY_TO_VAULT_MAPPING))
  for old, expected in cases:
      actual = map_legacy_group_id(old)
      status = 'PASS' if actual == expected else 'FAIL'
      print(f'{status}: {old!r:<20} → {actual!r:<25} (expected {expected!r})')
  "
  ```

**你应该看到**（全 PASS）：

```
PASS: 'cs188'              → 'vault:default'
PASS: 'canvas-dev'         → 'vault:default'
PASS: 'general'            → 'vault:default'
PASS: 'vault:cs_61b'       → 'vault:cs_61b'  (幂等)
PASS: 'cs_61b:main'        → 'vault:cs_61b:main'
PASS: '数学'               → 'vault:数学'
PASS: 'CS 61B!'            → 'vault:cs_61b'  (sanitize)
PASS: ''                   → 'vault:default'
```

**你不应该看到**：
- [ ] ❌ 任何 FAIL（映射规则有 bug）

---

#### V6 · LanceDB Story 1.9 isolation 仍工作（AC #4 修正版）

> ⭐ **重要**：ChatGPT Round-1 描述"LanceDB 没传 group_id"是过时论断 — Story 1.9 已通过 **table-name vault_id prefix** 解决。本步骤验证该机制仍生效。

**你做的事**：

- [x] 跑防御性测试：
  ```bash
  PYTHONPATH=. /Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/bin/pytest tests/unit/test_lancedb_isolation_assertions.py -q 2>&1 | tail -3
  ```

**你应该看到**：

- [x] `13 passed, 0 failed` ✅

**你不应该看到**：

- [ ] ❌ regression（说明 Story 1.9 isolation 被破坏）

---

#### V7 · 两 vault 同名节点不串（AC #8）

> 这是核心隔离测试。如果用户实际只有 1 个 vault，可用以下"模拟"方式验证。

**你做的事**：

- [x] 跑 Python REPL 模拟两 vault 同名节点：
  ```bash
  PYTHONPATH=. /Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/bin/python -c "
  from app.core.subject_config import build_vault_group_id

  # vault A: cs_61b 含 admissibility
  group_a = build_vault_group_id('cs_61b', canvas_path='admissibility.md')
  # vault B: 数学 含同名 admissibility
  group_b = build_vault_group_id('数学', canvas_path='admissibility.md')

  print(f'vault A group_id: {group_a!r}')
  print(f'vault B group_id: {group_b!r}')
  print(f'isolated: {group_a != group_b}')
  assert group_a == 'vault:cs_61b:admissibility'
  assert group_b == 'vault:数学:admissibility'
  assert group_a != group_b
  print('PASS: 两 vault 同名节点 group_id 独立')
  "
  ```

**你应该看到**：

```
vault A group_id: 'vault:cs_61b:admissibility'
vault B group_id: 'vault:数学:admissibility'
isolated: True
PASS: 两 vault 同名节点 group_id 独立
```

**你不应该看到**：

- [ ] ❌ 两 group_id 相同（命名冲突 → 跨 vault 数据污染）

---

### 边界场景 6 步

#### V8 · vault_id 空字符串被拒（AC #1）

- [x] curl 测试空字符串：
  ```bash
  curl -i -X POST 'http://localhost:8001/api/v1/chat/post-turn-extract' \
    -H 'Content-Type: application/json' \
    -d '{"node_id":"x","session_id":"s","vault_id":"","messages":[{"role":"user","content":"a"}]}'
  ```
- [x] **预期 HTTP 422**（min_length=1 校验）

---

#### V9 · vault_id 中文通过（AC #2 sanitize）

- [x] curl 测试中文 vault_id：
  ```bash
  curl -i -X POST 'http://localhost:8001/api/v1/chat/post-turn-extract' \
    -H 'Content-Type: application/json' \
    -d '{"node_id":"x","session_id":"s","vault_id":"数学","messages":[{"role":"user","content":"a"}]}'
  ```
- [x] **预期 HTTP 200**（中文 vault_id 通过）
- [ ] 后端日志的 group_id 应是 **`vault:数学`**（保留 unicode）

---

#### V10 · subject_id 优先于 canvas_path（AC #2 互斥）

- [x] Python REPL：
  ```bash
  PYTHONPATH=. /Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/bin/python -c "
  from app.core.subject_config import build_vault_group_id

  result = build_vault_group_id(
      'cs_61b', subject_id='algorithms', canvas_path='admissibility.md'
  )
  print(result)
  assert result == 'vault:cs_61b:algorithms'  # subject 赢
  print('PASS')
  "
  ```
- [x] **预期**：`vault:cs_61b:algorithms`（subject 优先，canvas_path 被忽略）

---

#### V11 · DEFAULT_GROUP_ID 兜底 + warning（AC #3）

- [ ] 跑代码看是否触发 deprecated warning：
  ```bash
  PYTHONPATH=. /Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/bin/python -c "
  import asyncio, structlog
  from app.services.error_writer import write_error_to_graphiti
  from app.services.error_classifier import ClassifiedError
  from app.graphiti.entity_types import ErrorType, PedagogyErrorType, RemedyStrategy

  err = ClassifiedError(
      legacy_type=ErrorType.KNOWLEDGE_GAP,
      pedagogy_type=PedagogyErrorType.CONCEPTUAL_CONFUSION,
      description='V11 测试: 不注入 ContextVar',
      confidence=0.85,
      legacy_remedy=RemedyStrategy.BACKTRACK_DEFINITION,
      pedagogy_remedies=[],
      sub_tags=[],
  )

  # 不调 set_current_subject_id, 不传 group_id 参数
  # → 应触发 group_id_fallback_to_default warning
  asyncio.run(write_error_to_graphiti(err, node_id='UAT-V11', error_id='v11-test'))
  print('Done — 检查日志应有 group_id_fallback_to_default warning')
  "
  ```

**你应该在日志看到**：

- [ ] structlog warning：`error_writer.group_id_fallback_to_default`
- [ ] 含 `fallback: cs188` 字段（deprecated 兜底）
- [ ] 含 `hint: Story 2.5.Y AC #3: 调用方应通过 ContextVar 或参数传入 group_id`

> 📌 这个 warning 说明 fallback 仍工作（向后兼容），但鼓励调用方迁移到 ContextVar。

---

#### V12 · cypher_helpers Cypher injection 防御（AC #5）

- [x] Python REPL：
  ```bash
  PYTHONPATH=. /Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/bin/python -c "
  from app.utils.cypher_helpers import cypher_with_group_filter

  # 模拟 injection attempt
  malicious = \"vault:x'; DROP DATABASE neo4j; --\"
  q, p = cypher_with_group_filter('MATCH (n) RETURN n', malicious)

  # 1. injection 字符串作为参数, 不出现在 query 文本
  print('Query:', q)
  print('Param:', p)
  assert 'DROP' not in q  # query 不含 DROP (参数化绑定)
  assert p['group_id'] == malicious  # 但参数仍是原值
  print('PASS: 参数化绑定防 injection')
  "
  ```

**你应该看到**：

- [x] `PASS: 参数化绑定防 injection`
- [x] Query 文本无 `DROP DATABASE`（仅 `\$group_id` 占位）
- [x] 参数 dict 含原始字符串（driver 层会安全 escape）

---

#### V13 · Plugin inferVaultId fallback（Task 9）

- [ ] Plugin tests:
  ```bash
  cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/frontend/obsidian-plugin
  npm test 2>&1 | tail -5
  ```

**你应该看到**：

- [x] `# tests ≥ 124, # pass = tests, # fail 0` (Story 2.5.Y 后实际 ≥ 133, package.json test script 已加 error-candidate-helpers.test.ts)

---

### 测试快速验证（V14-V15）

#### V14 · backend Story 2.5.Y 全栈 75 测试 pass

- [x] 跑 Story 2.5.Y 全部测试：
  ```bash
  cd /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/backend
  PYTHONPATH=. /Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/bin/pytest tests/unit/test_subject_config_vault.py tests/unit/test_post_turn_request_vault_id.py tests/unit/test_cypher_helpers.py tests/unit/test_lancedb_isolation_assertions.py tests/unit/test_group_id_migration.py -q 2>&1 | tail -3
  ```

- [x] **预期**：`75 passed, 0 failed`（21 + 7 + 18 + 13 + 16）

---

#### V15 · 全栈 264 测试无 regression

- [x] 跑 Story 2.5 全家桶（v1.0 + 2.5.X + 2.5.Y）：
  ```bash
  PYTHONPATH=. /Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/bin/pytest tests/unit/test_subject_config_vault.py tests/unit/test_post_turn_request_vault_id.py tests/unit/test_cypher_helpers.py tests/unit/test_lancedb_isolation_assertions.py tests/unit/test_group_id_migration.py tests/unit/test_candidate_writer.py tests/unit/test_candidate_state_machine.py tests/unit/test_candidate_service.py tests/unit/test_error_rebuild_service.py tests/unit/test_candidate_expiry_service.py tests/unit/test_error_writer.py tests/unit/test_error_extractor.py tests/unit/test_error_classification_mapping.py tests/integration/test_2_5_x_e2e.py tests/integration/test_story_2_5_chatgpt_round2_p0.py tests/integration/test_error_extraction_e2e.py -q 2>&1 | tail -3
  ```

- [x] **预期**：`264 passed, 0 failed`

---

## 🚦 验收结果

### 全 15 步 ✅

→ 告诉 Claude **"Story 2.5.Y v1.0 通过"**
→ Claude mark `done` + sprint-status 升级
→ 启动 **Story 2.5.X.1**（chat.py 切默认 candidate_only + cron lifespan，8-12h）
→ 或并行 **Epic 2 后续 Story**（2.6 dialog archive / 2.7 concept extraction）

### 主流程部分失败（V1-V7 任一 ❌）

→ 在批注区写**哪一步 + 实际现象**（最好截图）
→ Claude 跑 `bmad-bmm-correct-course` 修
→ 重出 v1.1 验收单

### 边界失败（V8-V13 任一 ❌）

→ 阻断分级：
- **V8（vault_id 空通过）= 阻断 ship**（schema 校验失效，多 vault 隔离失败）
- **V12（Cypher injection 不防）= 阻断 ship**（安全问题）
- **V11（DEFAULT_GROUP_ID warning 缺失）= 不阻断**（仅提醒，fallback 仍 work）
- V9 (中文 vault_id) / V10 (subject 优先) 失败 = 不阻断（属于 nice-to-have）

### 后端 / Neo4j 起不来

→ 不算验收失败，先解决环境问题
→ 告诉 Claude："V3/V7 跑不了，Neo4j 没启"

### 与 Story 2.5.X UAT 关系

→ 推荐**先跑 Story 2.5.X UAT**（19 步），再跑 2.5.Y UAT（15 步）
→ 2.5.Y UAT V2/V3 复用 2.5.X 的测试节点（无需重新准备）

---

## 📝 你的批注区

> [!question]+ Story 2.5.Y v1.0 实测批注（2026-05-05 起）
>
> 跑完 15 步任意写下：
> - **vault_id 推断逻辑**：Plugin 默认从 `app.vault.getName()` 取 vault_id（即 vault 文件夹名 "canvas-vault"）。要不要让用户在 Settings 显式配置 vault_id（如 "cs_61b" 比 "canvas-vault" 更语义化）？
> - **`vault:` 前缀必要性**：你觉得"vault:cs_61b"比 "cs_61b" 更清晰吗？还是太冗长？
> - **DEFAULT_GROUP_ID deprecated 兜底**：留着 fallback 是否会让用户漏掉真问题（应该硬 fail）？还是 fallback 保护更安全？
> - **subject_id 设计**：`vault:cs_61b:algorithms` 三级嵌套用过吗？还是 vault 已经够用？
> - **迁移脚本风险**：dry_run 模式默认 True，但 `--apply` 后无法回滚（Neo4j 不支持）。要不要加 `--backup-first` 选项强制先备份？
> - **多 vault 切换 UX**：未来如果你有 3 个 vault（CS 61B / 数学 / 机器学习），你期望怎么切？Obsidian 自带切换 + plugin 自动适配吗？还是要 Settings 显式配置？
> - **Neo4j Browser 看 group_id 体验**：V3 跑 Cypher 看 group_id 是否直观？要不要 Dashboard 加"当前 vault group_id"显示（用 plugin API 查 backend）？
>
> （空）

### 已知的已批注问题（历史追溯）

无（v1.0 首次 ship）

<!--
correct-course 后追加 [!error]+ callout 例:
> [!error]+ 2026-05-XX — v1.0 → v1.1 修复
> 你的原批注：[verbatim]
> 根因：[plain]
> 已修复：[summary]
-->

---

## 🔗 技术 spec 参考（给 Claude 读的，不是给你读的）

### Story 2.5.Y spec
- **主 spec**：`_bmad-output/implementation-artifacts/epic-2/2-5-y-isolation-hardening-subject-config-reuse.md`（v1.0 已 ship review）
- **D16 决议**：`_bmad-output/决策批注/D15-D16-用户主权与隔离方案-2026-05-04.md`
- **ChatGPT Round-2 reply**：`_bmad-output/research/chatgpt-round2-reply-story-2.5-sovereignty-isolation-2026-05-04.md`（C+ 8.5/10 commit-ready）

### PRD 锚定
- `/Users/Heishing/Desktop/spring course 2026/CS 61B/14-scheme-a-implementation-prd.md`
  - §FR-CTX-08 多 vault 上下文隔离（Story 2.5.Y trace）
  - §12 决策点清单 — 待用户追加 D15 / D16

### 后端代码（Story 2.5.Y 新增）
- `backend/app/utils/cypher_helpers.py` — `cypher_with_group_filter` + `assert_group_id_required`
- `backend/app/services/group_id_migration_service.py` — `map_legacy_group_id` + `migrate_legacy_group_ids` (mock-friendly)

### 后端代码（Story 2.5.Y 改动）
- `backend/app/core/subject_config.py` — 新增 `build_vault_group_id` + `is_vault_group_id`
- `backend/app/api/v1/endpoints/chat.py` — `PostTurnExtractRequest` 加 `vault_id` 必填 + 入口 ContextVar 注入
- `backend/app/services/error_writer.py` — `write_error_to_graphiti` group_id 优先级（ContextVar > 参数 > deprecated fallback）

### Plugin 代码（Story 2.5.Y 新增）
- `frontend/obsidian-plugin/src/error-candidate-helpers.ts` — `inferVaultId` + `build*Payload` 加 `vault_id` 字段
- `frontend/obsidian-plugin/src/main.ts` — 3 handler 调 `inferVaultId(app.vault.getName())` 注入

### Vault 改动
- `canvas-vault/.obsidian/plugins/canvas-learning-system/main.js` — 106348B → **107299B**（+951B vault_id 注入逻辑）

### 文档改动
- `CLAUDE.md` — §Graphiti 协议加 §Story 2.5.Y group_id 命名规约（vault: 前缀 + 已弃用格式列表）

### 测试覆盖
- **Backend Story 2.5.Y 75 passed**:
  - `test_subject_config_vault.py` (21) — Task 1
  - `test_post_turn_request_vault_id.py` (7) — Task 2
  - `test_cypher_helpers.py` (18) — Task 5
  - `test_lancedb_isolation_assertions.py` (13) — Task 4 修正版
  - `test_group_id_migration.py` (16) — Task 6
- **Plugin Story 2.5.Y 10 passed**:
  - `error-candidate-helpers.test.ts` 中新增 `inferVaultId` + vault_id payload 测试

### Git commit chain (Story 2.5.Y)
- `def3a27` — Tasks 1+2+3: SubjectConfig + vault_id 必填 + 移硬编码 (456 行)
- `24a2493` — Task 5: Cypher 防御性 helpers (316 行)
- `f987f0b` — Task 4: LanceDB 隔离防御性测试 (175 行)
- `fc7b9dd` — Tasks 6+9+10 ship: 迁移脚本 + Plugin vault_id + CLAUDE.md (618 行)

### AC → 代码 trace 表

| AC # | 验收点 | 代码定位 | UAT 步骤 |
|---|---|---|---|
| AC #1 | PostTurnExtractRequest vault_id 必填 | `chat.py::PostTurnExtractRequest` | V1, V8 |
| AC #2 | 复用 SubjectConfig 推导 group_id | `subject_config.py::build_vault_group_id` | V3, V9, V10 |
| AC #3 | error_writer 移除硬编码 | `error_writer.py::write_error_to_graphiti` ContextVar 优先 | V11 |
| AC #4 | LanceDB 隔离（Story 1.9 已修） | `vault_notes_retriever.py` table prefix | V6 |
| AC #5 | Cypher 防御性 helper | `cypher_helpers.py` | V4, V12 |
| AC #6 | group_id 命名迁移 | `group_id_migration_service.py` | V5 |
| AC #7 | per-group export/rebuild | 用 Story 2.5.X rebuild_graphiti endpoint 替代 | (Story 2.5.X UAT V5) |
| AC #8 | 两 vault 同名节点不串 | `build_vault_group_id` 两 vault 输出独立 | V7 |

---

## 📅 下一步（你批完这份单后）

1. **全部 ✅** → 说 **"Story 2.5.Y 通过"** → Claude mark done → 启动：
   - **Story 2.5.X.1**（chat.py 切默认 candidate_only + cron lifespan，8-12h）— **关键** ship 后用户对话才真正端到端
   - 或 **Story 2.6**（dialog archive 三层消息管理）
2. **主流程部分 ❌** → 在批注区写清楚 + 截图 → Claude 跑 `bmad-bmm-correct-course` → 重出 v1.1
3. **V8 vault_id 空通过 / V12 Cypher injection 不防 → 阻断 ship**
4. **暂停** → 告诉 Claude "暂停 Story 2.5.Y"，状态保持 `review`，可随时回来

---

> [!success]+ Story 2.5.Y 设计核心（2026-05-05 锁定）
>
> Story 2.5.Y 解决的不是"功能新增"，而是 **隔离质量回归**：
>
> 1. **类型强制**：vault_id 从 Optional 升 Required（schema 层 fail-fast）
> 2. **统一命名**：vault: 前缀让旧/新数据可视化区分（迁移脚本可识别）
> 3. **请求级注入**：ContextVar 替代硬编码，所有 service 透明拿 group_id
> 4. **防御性编程**：cypher_helpers 强制 WHERE 子句，防忘传跨 vault 泄漏
> 5. **向后兼容**：DEFAULT_GROUP_ID 保留为 deprecated fallback + warning（不破坏 v1.0 已 ship 行为）
> 6. **修正 spec**：ChatGPT Round-1 关于 LanceDB 的判断过时——Story 1.9 已通过 table prefix 隔离
>
> **代价**：Plugin 需要传 vault_id（已自动注入，用户无感）。Backend code 显式调 build_vault_group_id（开发者负担）。但**用户主权**仍由 Story 2.5.X 守护——Story 2.5.Y 仅解决"AI 决定写到哪里"的隔离层。
>
> 双 Story 协作：**2.5.X 是用户主权（who decides）**，**2.5.Y 是隔离质量（where it lands）**。
