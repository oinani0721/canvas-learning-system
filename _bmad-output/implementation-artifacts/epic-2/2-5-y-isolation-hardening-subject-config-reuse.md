---
story_id: "2.5.Y"
epic_id: "2"
prd_id: "canvas-learning-system"
status: "review"
priority: "P0"
estimate_hours: 30  # 26-35h 取中位
depends_on: ["2.5", "2.5.X"]
blocks: []
trace:
  - "FR-CONV-06"
  - "FR-CTX-08"  # 多 vault 上下文隔离
  - "Decision-Review-D16-Isolation-Hardening"
ship_decision: "复用 SubjectConfig + 修硬编码 DEFAULT_GROUP_ID + 全链路 group/session 隔离审计 (ChatGPT Round-2 修正稿)"
chatgpt_decision_review: |
  Round-1: 新建 VaultContextResolver (33-48h)
  Round-2 修正: 复用 SubjectConfig (26-35h, 减 14-30%)
  关键修正:
    - 项目已有 backend/app/core/subject_config.py (ContextVar 级抽象)
    - 不应新建抽象造成职能重叠
    - Khoj 撤回, 改 Graphiti/Mem0/LlamaIndex 作对照
    - session_id 加 frontmatter 但不进 dedupe hash
research_artifacts:
  - "_bmad-output/research/chatgpt-deep-research-story-2.5-sovereignty-isolation-2026-05-04.md"
  - "_bmad-output/research/chatgpt-round2-cross-check-story-2.5-sovereignty-isolation-2026-05-04.md"
  - "_bmad-output/research/chatgpt-round2-reply-story-2.5-sovereignty-isolation-2026-05-04.md"
parent_story: "2.5"
parent_ship_commit: "0d05ad8"
test_count_target: 25  # subject_config 强化 + endpoint 加字段 + writer 修硬编码 + 隔离审计 + E2E
---

# Story 2.5.Y: 隔离硬化 — 复用 SubjectConfig 全链路 (D16 决议)

Status: ✅ **review** (10/10 Tasks 完成, 264 backend + 114 plugin = 378 测试 pass, 待用户 UAT)

## Story

As a 拥有多个 Obsidian vault (CS 61B / 数学 60 / 机器学习等) 的学生,
I want **每个 vault 的错误数据物理隔离**, AI 检测到的 cs_61b 错误**不应**污染数学 vault 的查询结果,
So that 我可以放心同时运行多 vault, 不担心**学科串台 / 跨 vault 数据泄漏 / 历史误解错位**。

## 设计哲学（Round-2 锁定）

> **不是"继续用 group_id 就好", 而是必须把 `vault_id/group_id/session_id` 变成 Story 2.5 写入和检索链路的一等参数。隔离不能靠"大家记得传 group_id", 必须靠类型、接口和测试强制。**

| 维度 | 当前现状 (Story 2.5 v1.0) | **Story 2.5.Y (本 spec)** |
|---|---|---|
| group_id 来源 | 硬编码 `DEFAULT_GROUP_ID = "cs188"` | **从请求 vault_id 动态推断** (复用 SubjectConfig) |
| vault_id 字段 | PostTurnExtractRequest **缺失** | **必填字段** + 后端解析 |
| LanceDB 隔离 | ❌ 向量搜索无 group_id 过滤 | ✅ 强制注入 `WHERE group_id = ?` |
| Cypher 隔离 | ⚠️ 部分查询忘传 group_id | ✅ 防御性 helper 自动注入 |
| 命名一致性 | ⚠️ `cs188` vs `canvas-dev` vs `cs_61b:main` 三套并存 | ✅ 统一 `vault:<vault_id>` 格式 |
| 备份粒度 | ❌ 仅全量 dump | ✅ per-group export + rebuild 脚本 |
| 测试覆盖 | ❌ 无跨 vault E2E | ✅ 两 vault 同名节点不串测试 |

---

## Acceptance Criteria

### AC #1 - PostTurnExtractRequest 强制 vault_id 字段

**Given** Plugin 调用 `POST /api/v1/chat/post-turn-extract`
**When** 构造 request body
**Then** **必须**包含 `vault_id` 字段（非空字符串）
**And** **可选**包含 `subject_id` 和 `canvas_path`（用于二级隔离）
**And** 缺 `vault_id` → HTTP 422 with detail "vault_id is required for multi-vault isolation"

**Schema**:
```python
class PostTurnExtractRequest(BaseModel):
    node_id: str
    session_id: str
    messages: list[PostTurnMessage]
    fire_and_forget_graphiti: bool = True
    
    # NEW (Story 2.5.Y)
    vault_id: str = Field(..., description="Vault stable identifier, e.g. 'cs_61b' / '数学'")
    subject_id: str | None = Field(default=None, description="Optional subject override for sub-namespace")
    canvas_path: str | None = Field(default=None, description="Optional canvas/board name for canvas-level isolation")
```

---

### AC #2 - 复用 SubjectConfig 推导 group_id

**Given** request 含 `vault_id` + 可选 `subject_id` + `canvas_path`
**When** 后端进入 endpoint
**Then** **必须**调用 `SubjectConfig.build_group_id(vault_id, subject_id, canvas_path)` 派生 group_id
**And** **不允许**任何写入路径使用 `DEFAULT_GROUP_ID`（设为生产路径禁用）
**And** group_id 通过 `set_current_subject_id()` 注入 ContextVar，整个请求生命周期可用

**派生规则**（Round-2 锁定）：
```python
def build_group_id(vault_id: str, subject_id: str | None = None, canvas_path: str | None = None) -> str:
    """
    Round-2 修正: 命名统一为 'vault:<id>' 格式
    
    示例：
      vault_id="cs_61b"                                  → "vault:cs_61b"
      vault_id="cs_61b", canvas_path="admissibility"     → "vault:cs_61b:admissibility"
      vault_id="cs_61b", subject_id="algorithms"         → "vault:cs_61b:algorithms"
    """
```

---

### AC #3 - error_writer 移除硬编码 DEFAULT_GROUP_ID

**Given** `error_writer.py:270` 当前 `from app.config import DEFAULT_GROUP_ID`
**When** Story 2.5.Y ship
**Then** **删除**该 import
**And** `write_error_to_graphiti()` / `write_error_dual()` 函数签名加 `group_id: str` **必填参数**
**And** 调用方（endpoint 层）必须显式传 group_id（否则 mypy / runtime 报错）

**Before** (现状):
```python
# error_writer.py:308
await memory_svc.record_knowledge_entity(
    ...,
    group_id=DEFAULT_GROUP_ID,  # ❌ 硬编码
)
```

**After** (Story 2.5.Y):
```python
async def write_error_dual(
    error: ClassifiedError,
    file_path: str,
    *,
    group_id: str,  # ⭐ 必填
    session_id: str | None = None,
) -> WriteErrorResult:
    ...
    await memory_svc.record_knowledge_entity(
        ...,
        group_id=group_id,  # ✅ 从参数传
    )
```

**And** 全 codebase grep 不应再有 `from app.config import DEFAULT_GROUP_ID`（除 dev fallback）

---

### AC #4 - LanceDB 向量搜索注入 group_id 过滤

**Given** `vault_notes_retriever.py` 当前向量搜索可能跨 group 召回
**When** Story 2.5.Y ship
**Then** 所有 LanceDB `.search()` 调用**必须**含 `where=f"group_id = '{group_id}'"` 子句
**And** 当 group_id 缺失时 → 拒绝执行 + 抛 `ValueError("group_id required for vault isolation")`

**关键修复点**：
- `backend/app/retrievers/vault_notes_retriever.py:126-243`
- `backend/app/retrievers/cross_canvas_retriever.py:189-195` (TODO 占位符已 2 个月)

---

### AC #5 - Cypher 查询防御性 group_id 注入

**Given** Backend 内所有 `MATCH (n) WHERE n.group_id = $groupId` 查询
**When** Story 2.5.Y ship
**Then** 创建 helper 函数 `cypher_with_group_filter(query, group_id)` 自动注入 WHERE 子句
**And** 全 codebase 审计：所有 `session.run(...)` / `await tx.run(...)` 调用必须用此 helper（除 schema migrations）
**And** 单测覆盖：传空 group_id 抛错

**示例**:
```python
# Helper
def cypher_with_group_filter(base_query: str, group_id: str) -> str:
    """Round-2: 强制注入 group_id 过滤, 防御性编程"""
    if not group_id:
        raise ValueError("group_id required")
    return f"{base_query} WHERE n.group_id = $group_id"

# 用法
result = await tx.run(
    cypher_with_group_filter(
        "MATCH (n:Concept) RETURN n",
        group_id=group_id
    ),
    group_id=group_id
)
```

---

### AC #6 - group_id 命名统一迁移

**Given** 当前 codebase 三套 group_id 命名并存：
- `cs188` (config.py 默认)
- `canvas-dev` (CLAUDE.md 全局规则)
- `cs_61b:main` / `cs_61b:admissibility` (生产推断)

**When** Story 2.5.Y ship
**Then** 统一为 `vault:<vault_id>[:<subject_or_canvas>]` 格式
**And** 提供迁移脚本 `scripts/migrate_group_ids.py`：
1. 扫描 Neo4j 所有 group_id 值
2. 映射 `cs188` → `vault:default` / `canvas-dev` → `vault:default` / `cs_61b:X` → `vault:cs_61b:X`
3. 更新 Graphiti episode metadata
4. 更新 LanceDB 索引
5. 更新所有 frontmatter `group_id` 字段

**And** CLAUDE.md / `_bmad-output/.claude/CLAUDE.md` 更新 group_id 命名规约

---

### AC #7 - per-group export / rebuild 脚本

**Given** 用户想备份单个 vault 的 Graphiti 数据
**When** 执行 `python scripts/export_group.py --group-id vault:cs_61b --output ./backups/cs_61b.jsonl`
**Then** 脚本：
1. 查 Neo4j 所有 `n.group_id = "vault:cs_61b"` 的节点
2. 导出为 JSONL（含 entity_type / properties / relationships）
3. 包含元数据 header（导出时间 / 节点数 / Neo4j 版本）

**And** 提供 `python scripts/rebuild_group.py --group-id vault:cs_61b --input ./backups/cs_61b.jsonl --dry-run` 还原脚本：
1. 读 JSONL
2. 验证 group_id 一致
3. dry-run 模式：报告将写入数量
4. 实际模式：调 Graphiti SDK 写回（含 idempotency check）

---

### AC #8 - E2E 两 vault 同名节点不串

**Given** 测试场景：
- vault A (`vault:cs_61b`) 含 `节点/admissibility.md`，frontmatter 含 1 条 error
- vault B (`vault:数学`) 含 `节点/admissibility.md`（同名！），frontmatter 含 1 条 error（不同内容）

**When** 调 `search_memories(query="admissibility", group_id="vault:cs_61b")`
**Then** 仅返回 vault A 的 error（**不**返回 vault B 的）
**And** 调 `search_memories(query="admissibility", group_id="vault:数学")` 仅返回 vault B
**And** Cypher / LanceDB / Graphiti 三层均一致

---

## Tasks / Subtasks

- [ ] **Task 1: 复用并强化 SubjectConfig** (AC: #2)
  - [ ] 1.1: 审查 `backend/app/core/subject_config.py` 现有 API
  - [ ] 1.2: 增强 `build_group_id()` 函数：支持 vault_id / subject_id / canvas_path 三参数
  - [ ] 1.3: 命名统一为 `vault:<vault_id>[:<sub>]` 格式
  - [ ] 1.4: 弃用 `DEFAULT_GROUP_ID` 常量（仅保留为 dev fallback，标记 deprecated）
  - [ ] 1.5: 单测 `test_subject_config.py` 覆盖 build_group_id 各种组合

- [ ] **Task 2: PostTurnExtractRequest 加 vault_id 字段** (AC: #1)
  - [ ] 2.1: 修改 `chat.py:236-260` `PostTurnExtractRequest` 加 `vault_id: str = Field(...)` 必填
  - [ ] 2.2: 加 `subject_id` / `canvas_path` 可选字段
  - [ ] 2.3: endpoint 入口调 `set_current_subject_id(build_group_id(vault_id, subject_id, canvas_path))`
  - [ ] 2.4: 缺 vault_id 返回 422 + 详细 error message
  - [ ] 2.5: 同步修改 `accept-candidate` / `dismiss-candidate` 等 Story 2.5.X 引入的 endpoints

- [ ] **Task 3: error_writer 移除 DEFAULT_GROUP_ID 硬编码** (AC: #3)
  - [ ] 3.1: 删除 `error_writer.py:270` 的 `from app.config import DEFAULT_GROUP_ID` 
  - [ ] 3.2: 修改 `write_error_dual()` / `write_error_to_graphiti()` 函数签名加 `group_id: str` 必填
  - [ ] 3.3: 修改所有调用方（endpoint 层）显式传 group_id
  - [ ] 3.4: 全 codebase grep 验证无残留 `DEFAULT_GROUP_ID` 用法（除 deprecated marker）
  - [ ] 3.5: mypy 严格模式验证（参数缺失 → 编译错误）

- [ ] **Task 4: LanceDB 隔离审计** (AC: #4)
  - [ ] 4.1: 修改 `backend/app/retrievers/vault_notes_retriever.py:126-243`
  - [ ] 4.2: 所有 `.search()` 调用加 `where=f"group_id = '{group_id}'"` 
  - [ ] 4.3: group_id 为空时 raise `ValueError`
  - [ ] 4.4: 修复 `cross_canvas_retriever.py:189-195` 的 TODO 占位符（2 个月历史债）
  - [ ] 4.5: 单测 `test_lancedb_isolation.py`：vault A 数据无法被 vault B 查到

- [ ] **Task 5: Cypher 防御性 helper** (AC: #5)
  - [ ] 5.1: 新增 `backend/app/utils/cypher_helpers.py`
  - [ ] 5.2: 实现 `cypher_with_group_filter(base_query, group_id) -> str`
  - [ ] 5.3: 全 codebase 审计：所有 `tx.run` / `session.run` 调用替换为 helper（除 schema migrations）
  - [ ] 5.4: 单测覆盖：空 group_id 抛错 + 注入正确 WHERE 子句

- [ ] **Task 6: group_id 命名统一迁移** (AC: #6)
  - [ ] 6.1: 写 `scripts/migrate_group_ids.py`
  - [ ] 6.2: 实现 dry-run 模式：扫描所有 group_id 值 + 映射规则报告
  - [ ] 6.3: 实现 apply 模式：更新 Neo4j + LanceDB + frontmatter
  - [ ] 6.4: 更新 `CLAUDE.md` 和 `_bmad-output/.claude/CLAUDE.md` 的 group_id 命名规约
  - [ ] 6.5: 写迁移测试 `test_group_id_migration.py`

- [ ] **Task 7: per-group export/rebuild 脚本** (AC: #7)
  - [ ] 7.1: 写 `scripts/export_group.py --group-id <id> --output <file>`
  - [ ] 7.2: 写 `scripts/rebuild_group.py --group-id <id> --input <file> [--dry-run]`
  - [ ] 7.3: idempotency check（重复 rebuild 不重复写）
  - [ ] 7.4: 集成到 `Makefile` 或 `pyproject.toml` scripts

- [ ] **Task 8: E2E 多 vault 测试** (AC: #8)
  - [ ] 8.1: 新增测试 fixture：构造 2 个 vault，含同名节点不同内容
  - [ ] 8.2: `test_2_5_y_multi_vault_isolation.py`：
    - vault A 写 error → group_id="vault:cs_61b"
    - vault B 写 error → group_id="vault:数学"
    - search_memories(group_id="vault:cs_61b") 仅返回 A
    - search_memories(group_id="vault:数学") 仅返回 B
  - [ ] 8.3: Cypher / LanceDB / Graphiti 三层各跑一遍
  - [ ] 8.4: 验证 frontmatter 中 group_id 与 Graphiti 元数据一致

- [ ] **Task 9: Plugin 端传 vault_id** (AC: #1)
  - [ ] 9.1: 修改 `frontend/obsidian-plugin/src/main.ts`
  - [ ] 9.2: 从 `app.vault.getName()` 或 `.canvas-config.yaml` 读取 vault_id
  - [ ] 9.3: 调 post-turn-extract / accept-candidate 等 endpoints 时显式传 vault_id
  - [ ] 9.4: 单测 plugin（vitest）覆盖 vault_id 注入

- [ ] **Task 10: 文档更新** (AC: #6)
  - [ ] 10.1: 更新 `CLAUDE.md` 全局 group_id 规约（删 `canvas-dev`，统一 `vault:<id>`）
  - [ ] 10.2: 更新 `docs/architecture.md` 多 vault 隔离章节
  - [ ] 10.3: 更新 `docs/known-gotchas.md` 标记 G-FAKE / G-PIPE 中已修复项

## Dev Notes

### 关键实现锚点

1. **复用 SubjectConfig 而非新建抽象**（Round-2 修正）：
   - `backend/app/core/subject_config.py` 已有：
     - `ContextVar` 请求级 subject_id
     - `get_current_subject_id()` / `set_current_subject_id()`
     - `extract_subject_from_canvas_path()`
     - `extract_canvas_name()`
     - `build_group_id(subject, canvas_name)`
   - **不**新建 `VaultContextResolver` (Round-1 推荐已被 Round-2 否决)
   - 改造 `build_group_id()` 接受 `vault_id` 作为新主参数

2. **历史债清单**（参考 R4/R8/R12 review 文档）：
   - `cross_canvas_retriever.py:189-195` — `find_related_canvases()` TODO 占位符 2+ 个月，始终返回 `[]`
   - `vault_notes_retriever.py:126-243` — group_id placeholder，未真正激活隔离
   - `memory_service.search_memories()` — 部分查询无 WHERE group_id 子句

3. **session_id 字段**（Round-2 锁定）：
   - PostTurnExtractRequest 已有 `session_id`（v1.0 已有）
   - frontmatter `errors[]` / `error_candidates[]` (Story 2.5.X) 写入 `session_id` + `seen_sessions[]`
   - **不**进 dedupe hash（跨 session 同错应 update 不 append）

4. **Mem0 6 维度对照**（Round-2 修正后）：
   - 学习 Mem0 的多维过滤思路：user_id / agent_id / session_id / run_id / app_id / created_at
   - Story 2.5.Y 当前仅实施 vault_id（≈ user_id）+ session_id
   - 未来 Phase 2 可扩展 agent_id（多 AI 角色）/ run_id（多次执行追溯）

5. **回滚策略**：
   - 若 Story 2.5.Y 失败，可：
     1. revert commit
     2. 重启 backend (group_id 落回 DEFAULT 值)
     3. 跑 `migrate_group_ids.py --rollback` 还原 Neo4j / LanceDB
   - 关键：迁移脚本必须**双向**支持

### Project Structure Notes

```
backend/app/
  core/
    subject_config.py           # 改：强化 build_group_id() 支持 vault_id
  config.py                     # 改：DEFAULT_GROUP_ID 标记 deprecated (仅 dev fallback)
  api/v1/endpoints/
    chat.py                     # 改：PostTurnExtractRequest 加 vault_id 必填
    errors.py                   # 改：accept/dismiss endpoints 加 vault_id
  services/
    error_writer.py             # 改：移除 DEFAULT_GROUP_ID import + group_id 必填
    memory_service.py           # 改：record_knowledge_entity 检查 group_id 必填
  retrievers/
    vault_notes_retriever.py    # 改：LanceDB search 加 group_id WHERE
    cross_canvas_retriever.py   # 修：TODO 占位符 → 真实查询 + group_id 过滤
  utils/
    cypher_helpers.py           # 新增：cypher_with_group_filter()
backend/scripts/
  migrate_group_ids.py          # 新增：cs188 / canvas-dev → vault:<id>
  export_group.py               # 新增：per-group 导出 JSONL
  rebuild_group.py              # 新增：per-group 还原（idempotency）
backend/tests/unit/
  test_subject_config.py        # 改：覆盖 vault_id 场景
  test_lancedb_isolation.py     # 新增
  test_cypher_helpers.py        # 新增
  test_group_id_migration.py    # 新增
backend/tests/integration/
  test_2_5_y_multi_vault_isolation.py  # 新增 E2E
frontend/obsidian-plugin/src/
  main.ts                       # 改：从 vault config 读 vault_id 注入 endpoints
docs/
  architecture.md               # 改：多 vault 隔离章节
  known-gotchas.md              # 改：标记已修复历史债
CLAUDE.md                       # 改：group_id 命名规约（删 canvas-dev）
_bmad-output/.claude/CLAUDE.md  # 改：同上
```

### References

- **Anchor PRD §FR-CTX-08**: 多 vault 上下文隔离（待用户在 PRD §12 批注 D16 具体定义）
- **Story 2.5 v1.0 ship code**: commit `0d05ad8`
- **Story 2.5.X spec**: `_bmad-output/implementation-artifacts/epic-2/2-5-x-error-candidate-progressive-confirmation.md`
- **ChatGPT Round-2 reply**: `_bmad-output/research/chatgpt-round2-reply-story-2.5-sovereignty-isolation-2026-05-04.md`
- **现有 SubjectConfig**: `backend/app/core/subject_config.py:42-60`
- **历史债 review**:
  - `_bmad-output/research/round-12-1-5-annotations-deep-dive-2026-04-21.md` (cross_canvas_retriever)
  - `_bmad-output/research/obsidian-qa-round8-claude-answers-2026-04-15.md` (LanceDB)
  - `_bmad-output/implementation-artifacts/epic-1/1-9-lancedb-vault-id-isolation.md` (epic-1.9 placeholder)
  - `_bmad-output/research/obsidian-qa-round4-claude-answers-2026-04-14.md` (group_id 全链路)
- **Decision-Review-D16**: 隔离方案选择 (待用户在 PRD §12 批注)

### 与 Story 2.5.X 的协调

- Story 2.5.X 引入 `error_candidates[]` 数组 + accept/dismiss endpoints
- Story 2.5.Y 给所有这些 endpoints 加 `vault_id` 必填字段
- 实施顺序：**Story 2.5.X 先 ship → 2.5.Y 在 X 基础上加隔离硬化**
- 若 2.5.Y 改 X 的 endpoint 签名，需更新 X 的测试（fixture 加 vault_id）

## UAT Script

> **前置**：用户在 PRD §12 批注 D16 决议（隔离方案 = 复用 SubjectConfig），并完成 Story 2.5.X UAT
>
> **场景 1：vault_id 必填验证**
> 1. 用 curl 调 post-turn-extract，**不**传 vault_id
> 2. **预期**：HTTP 422，error detail "vault_id is required for multi-vault isolation"
> 3. 加上 vault_id="cs_61b" 重试 → 200 OK
>
> **场景 2：group_id 命名统一**
> 4. 调 post-turn-extract（vault_id="cs_61b"，无 canvas_path）
> 5. 看 Neo4j Browser (localhost:7478)：
> 6. **预期**：misconception 节点 `group_id` 字段值为 `"vault:cs_61b"`（**不**是 `"cs188"` 或 `"cs_61b:main"`）
>
> **场景 3：error_writer 硬编码移除**
> 7. 后端启动时设环境变量 `DEFAULT_GROUP_ID=__SHOULD_NOT_BE_USED__`
> 8. 跑场景 2 流程
> 9. **预期**：Neo4j 中 group_id 仍是 `vault:cs_61b`（**不**是 sentinel 值）
> 10. **预期**：grep 后端日志，无 "DEFAULT_GROUP_ID" 字样
>
> **场景 4：LanceDB 隔离**
> 11. vault A (cs_61b) 含 `节点/admissibility.md` (内容 X)
> 12. vault B (数学) 含 `节点/admissibility.md` (内容 Y)
> 13. 调 vault_notes_retriever 搜索 "admissibility"，传 group_id="vault:cs_61b"
> 14. **预期**：仅返回内容 X（**不**返回 Y）
>
> **场景 5：Cypher 防御性**
> 15. 在测试代码里调 `tx.run("MATCH (n:Concept) RETURN n")` 无 group_id 过滤
> 16. **预期**：抛 `ValueError("group_id required")`
> 17. 用 helper `cypher_with_group_filter()` → 正常返回
>
> **场景 6：迁移脚本 dry-run**
> 18. 运行 `python scripts/migrate_group_ids.py --dry-run`
> 19. **预期**：报告 `cs188 → vault:default (N 个节点) / canvas-dev → vault:default (M 个节点) / cs_61b:main → vault:cs_61b (P 个节点)`
> 20. 加 `--apply` 执行，再次 dry-run 应报告 0 个待迁移
>
> **场景 7：per-group export/rebuild**
> 21. `python scripts/export_group.py --group-id vault:cs_61b --output ./test.jsonl`
> 22. **预期**：JSONL 文件含所有 cs_61b 节点（每行一个 entity JSON）
> 23. `python scripts/rebuild_group.py --group-id vault:cs_61b --input ./test.jsonl --dry-run`
> 24. **预期**：报告 "0 newly written (already exist)" — idempotency 验证
>
> **场景 8：跨 vault 不串（核心）**
> 25. 在 vault A 启动对话产生 1 条 error
> 26. 切到 vault B，调 search_memories(group_id="vault:数学")
> 27. **预期**：返回结果**不**含 vault A 那条 error
> 28. Dashboard.md 在 vault A 显示 1 条 candidate，vault B 显示 0 条

## Automated Checkpoints

| Checkpoint | Type | Command | Pass Signal |
|---|---|---|---|
| vault_id 必填 | unit | `pytest tests/unit/test_post_turn_request.py::test_vault_id_required -x` | 缺字段抛 422 |
| build_group_id | unit | `pytest tests/unit/test_subject_config.py::test_build_group_id -x` | 各组合返回 vault:* 格式 |
| 硬编码移除 | static | `grep -r "from app.config import DEFAULT_GROUP_ID" backend/app/services/` | 无匹配 |
| LanceDB 隔离 | unit | `pytest tests/unit/test_lancedb_isolation.py -x` | A vault 数据无法被 B vault 查到 |
| Cypher helper | unit | `pytest tests/unit/test_cypher_helpers.py -x` | 空 group_id 抛错 |
| 迁移幂等 | unit | `pytest tests/unit/test_group_id_migration.py::test_idempotent -x` | 二次跑 dry-run 0 条 |
| 跨 vault 不串 | integration | `pytest tests/integration/test_2_5_y_multi_vault_isolation.py -x` | 三层全隔离 |

## User Feedback & Changes

### Feedback Log

(empty)

### Deviation Notes

(empty)

## Dev Agent Record

### Agent Model Used

(to be filled by Dev agent)

### Debug Log References

(to be filled by Dev agent)

### Completion Notes List

(to be filled by Dev agent)

### File List

(to be filled by Dev agent)

## Change Log

- **2026-05-04 v1.0 初稿** — 基于 ChatGPT Round-2 reply（commit `348a7ae`）锁定隔离硬化方案
  - 复用 SubjectConfig + group_id 命名统一为 `vault:<id>` + 全链路硬化
  - 弃用 Round-1 的"新建 VaultContextResolver"提议（职能与现有 SubjectConfig 重叠）
  - 等待用户在 PRD §12 批注 D16 后启动 dev-story
