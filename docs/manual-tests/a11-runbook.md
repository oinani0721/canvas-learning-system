# A11 修复验证手册

> **5 分钟自助验证**：考试节点选择算法是否真正从"schema drift civil war"中恢复。
> 用户抱怨过的 A11 原话 —— "节点选择算法是编的" —— 这份手册让你亲眼看见修复生效。

## 背景 — 你在验证的是什么

A11 的根因是 FR-KG-04 的 schema 内战：

| 写入方 (SyncService) | 查询方 (`question_generator._get_kg_relevance`) | 结果 |
| --- | --- | --- |
| `CanvasNode {id, canvasId, ...}` | `CanvasNode {uuid}` + `neighbor.canvas_id` | Cypher 永远查空 |
| 字段名都是 camelCase | 字段名混合 snake_case + 旧 `uuid` 残留 | 每个节点常量 `0.5` |

30% 的考试优先级权重（`W_KG_RELEVANCE=0.3`）彻底失效，但后端日志**没有任何告警** — silent degradation 的教科书案例。

修复后：
1. Cypher 用正确的 `{id}` + `canvasId`（Phase 1，commit `a6da4f7`）
2. 新增 `kg_relevance_degraded` 字段让 fallback 变可观测（Phase 6，commit `fcd0131`）
3. 所有 Neo4j 异常 fail-closed 到 `0.5 / "neo4j_unavailable"`（Phase 6，commit `5ecf834`）

本手册让你验证这 3 件事都还在。

## 前置条件

- Docker Desktop 运行中
- 已经 cd 到 `canvas-learning-system/`（repo 根目录）
- `backend/.venv` 已存在（如果没有：`cd backend && uv sync`）

## 步骤 1：启动测试 Neo4j（30 秒）

```bash
docker compose --profile test up -d neo4j-test
# 等 ~20 秒让 healthcheck 通过
```

验证容器运行中：

```bash
docker ps --filter "name=canvas-learning-system-neo4j-test" --format "{{.Names}} {{.Status}}"
# 期望看到: canvas-learning-system-neo4j-test Up X seconds (healthy)
```

## 步骤 2：跑 A11 端到端脚本（90 秒）

```bash
backend/.venv/bin/python scripts/test-a11-end-to-end.py
```

## 步骤 3：你应该看到什么

脚本会输出 5 段 Rich 格式的面板：

### 面板 1 — Test Setup
展示测试画布 ID、Neo4j URI、5 个 primary 节点名、以及"我把 mastery/retrievability 固定住了，让 kg_relevance 成为唯一变量"的声明。

### 面板 2 — Schema Verification
```
Canonical {id, canvasId} nodes  13
Legacy {uuid} nodes             0     ← 关键：必须是 0，不能有任何残留
CANVAS_EDGE relationships       18
Overall                         ✅ schema ok
```

这段是 **negative assertion**：如果 `Legacy {uuid} nodes` 不是 0，说明 schema drift 又回来了。

### 面板 3 — `_get_kg_relevance()` 直接计算表

```
┏━━━━━━━┳━━━━━━━┳━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Node  ┃ Edges ┃ Expected ┃ Actual ┃ Degraded reason ┃
┡━━━━━━━╇━━━━━━━╇━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ nodeE │     8 │    1.000 │  1.000 │ —               │
│ nodeD │     6 │    0.750 │  0.750 │ —               │
│ nodeA │     0 │    0.500 │  0.500 │ empty_graph     │ ← fallback
│ nodeB │     0 │    0.500 │  0.500 │ empty_graph     │ ← fallback
│ nodeC │     4 │    0.500 │  0.500 │ —               │ ← 同样是 0.5 但 NOT degraded
└───────┴───────┴──────────┴────────┴─────────────────┘
```

**这里的精妙之处**：`nodeC` 的 raw kg_relevance 也是 `0.5`（4/8 = 0.5），**和 `empty_graph` 的 fallback 值撞号**。
但 `degraded reason` 一列把它们区分开：`nodeC` 是真算出来的 0.5，`nodeA/nodeB` 是兜底。
这就是 Phase 6 `kg_relevance_degraded` 字段存在的理由。

### 面板 4 — `select_target_node()` 5 次连续调用

```
┏━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Pick ┃ Node  ┃ priority_score ┃ kg_relevance ┃ degraded    ┃
┡━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│    1 │ nodeE │         0.5000 │        1.000 │ —           │
│    2 │ nodeD │         0.4250 │        0.750 │ —           │
│    3 │ nodeC │         0.3500 │        0.500 │ —           │
│    4 │ nodeA │         0.3500 │        0.500 │ empty_graph │
│    5 │ nodeB │         0.3500 │        0.500 │ empty_graph │
└──────┴───────┴────────────────┴──────────────┴─────────────┘
```

选择序列 **E → D → C → A → B** 严格反映连接度。这 5 次调用模拟"用户考试 5 轮"，每轮都用 `examined_nodes` 排除已考察的节点，下一个挑剩下里优先级最高的。

### 面板 5 — Counterfactual BEFORE / AFTER

脚本会把 "修复前 kg ≡ 0.5 导致所有节点 priority=0.35 的 tie" 和 "修复后 3 个不同的 priority 值" 并排展示。这是给你看"如果 A11 没修，你会看到什么"的反事实。

### 最终裁决

```
╭──────────────────────────────────────────────────────────────────╮
│ ✅ A11 FIX VERIFIED                                              │
│                                                                  │
│   ✓ kg_relevance is NOT constant — 3 distinct values observed    │
│   ✓ Selection sequence reflects connectivity ranking (E→D→C→A→B) │
│   ✓ degraded markers correctly distinguish empty_graph from 0.5  │
│   ✓ Schema drift eliminated (0 legacy {uuid} nodes)              │
╰──────────────────────────────────────────────────────────────────╯
```

Exit code `0` = 修复工作正常；exit code `1` = 至少一项断言失败（终端会高亮红色单元格）。

## 步骤 4（可选）：Neo4j Browser 二次验证

直接在浏览器里查 schema，不依赖脚本：

1. 打开 <http://localhost:7479>
2. 登录 `neo4j` / `testpassword`
3. 执行：

```cypher
MATCH (n:CanvasNode)
WHERE n.canvasId = 'a11-test-canvas'
RETURN n.id, n.canvasId, n.title
LIMIT 5
```

**期望**：看到 5 个节点，`id` 和 `canvasId` 都是字符串，**没有 `uuid` 字段**（Browser 的属性面板不应显示 `uuid`）。

**注意**：脚本跑完会自动 DETACH DELETE 测试数据，所以上面的查询要在脚本还没跑完时执行，或者重新跑脚本但加 `--keep-data` 参数（当前版本不支持；如需保留数据，可以把 `_clear_canvas` 的 finally 块注释掉）。

## 步骤 5（可选）：让 Claude Code 跑 pytest 回归

在 Claude Code desktop 里说：

> 跑一下 A11 端到端测试: pytest backend/tests/e2e/test_a11_kg_relevance_e2e.py -v

Claude Code 会执行：

```bash
NEO4J_TEST_URI=bolt://localhost:7692 \
  backend/.venv/bin/python -m pytest \
  backend/tests/e2e/test_a11_kg_relevance_e2e.py -v
```

**期望**：`11 passed in ~1.1s`

pytest 变体和 CLI 脚本共享同一套 fixture 设计，但断言更细粒度 —— 覆盖 schema、每个节点的 kg 值、nodeC 的 NOT-degraded 特殊情况、首次选择、完整序列、distinct kg 值数量 6 个维度。

## 故障排查

| 症状 | 可能原因 | 修复 |
| --- | --- | --- |
| `kg=0.5 (5/5 nodes)` | Phase 1 没部署 | `git log --oneline \| grep a6da4f7` 应该能找到；没有就 `git pull` |
| `kg_relevance_degraded` 字段不存在 | Phase 6 没部署 | `git log --oneline \| grep fcd0131` |
| `Legacy {uuid} nodes > 0` | 测试 Neo4j 里残留了旧 schema 的数据 | `docker compose --profile test down -v && docker compose --profile test up -d neo4j-test` |
| 脚本报 "cannot reach test Neo4j" | neo4j-test 容器没启动 | `docker compose --profile test up -d neo4j-test` + 等 20 秒 |
| pytest 报 "Future attached to a different loop" | 不小心用了 `real_neo4j_client` module-scoped fixture | 本测试的 fixture 是 function-scoped，不应该出现；如果出现，重启 worker |

## 这份手册覆盖了什么、没覆盖什么

**覆盖**：
- A11 本身（kg_relevance 从常量 0.5 变成真实 weighted degree）
- Phase 1 Cypher schema 修复
- Phase 6 degraded marker + fail-closed 异常处理
- 和 SyncService 的 schema 一致性（raw Cypher 用的是同一套 `{id}, canvasId` 键）

**不覆盖**：
- Phase 11 Segment Commit（板→节点→边顺序），需要跑 `test_segment_commit_*.py`
- Phase 12 `SyncErrorClass` 前端路由，需要 Playwright
- Phase 17 Fail-Closed Degraded Scoring 在 verification_service 层的完整集成，需要另起 e2e
- UI 层面的可见性（exam API 不 expose kg_relevance 字段，所以 UI 看不见）

A11 是一个**不可见修复** —— 这份手册和脚本的存在就是为了把不可见变可见。

## 相关文件

| 文件 | 用途 |
| --- | --- |
| `scripts/test-a11-end-to-end.py` | 这份手册驱动的主脚本 |
| `backend/tests/e2e/test_a11_kg_relevance_e2e.py` | 同逻辑的 pytest 回归 |
| `backend/app/services/question_generator.py:_get_kg_relevance` (L700+) | 被测对象 |
| `backend/tests/unit/test_kg_relevance_weighted.py` | 数学预期的单元测试参考 |
| `openspec/changes/fix-fr-kg-04-schema-drift-and-sync-hardening/` | 完整的 OpenSpec change（design/specs/tasks） |
