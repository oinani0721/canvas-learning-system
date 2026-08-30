总裁定：**NOT-CLOSED（需整改）**。运行态与 exact-byte 证据全部通过，但契约仍存在可复现的接受绕过，不能以 `116 passed` 或 live `0 finding` 代替收口。

### 运行证据

| 项目 | 结果 |
|---|---|
| 冻结对象 | **CLOSED**。开跑、收尾三项 SHA-256 均与给定值完全一致 |
| 指定测试 | **CLOSED**。`116 passed, 10 warnings in 89.18s`，exit 0 |
| live checker | **CLOSED**。完整 probe 档，`probe_skipped=false`，G1–G11 全跑；exit 0、0 finding、175 目录 / 324 文件、1 条已登记分歧 |
| live vault 完整性 | **CLOSED**。324 行全量文件 SHA-256 清单首尾逐字相同；清单摘要均为 `aeeb946e…a6408e7c` |
| 工作树 | 无 tracked diff；仅保留开跑前已有的 untracked 对象 |

### 逐条裁定

| 项目 | 裁定 | 复核结果 |
|---|---|---|
| HIGH-1(a) note 严格字符串 | **NOT-CLOSED** | 三个 ledger 节中 `null/[]/{}/123` 均被 [`_nonempty_str`](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:606>) 拒绝；但 `repo_docs` 改成 `conditional` 后四种坏 note 全部 **ACCEPTED**，[其校验缺少 conditional-note 规则](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:505>)。 |
| HIGH-1(b) 无 type + indexed 必须 conditional | **CLOSED** | 指定五条均已改为 conditional 并带非空 note；逐条翻回 `included`，5/5 均抛 ConfigError。[规则入口](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:611>)。 |
| HIGH-1(c) 补 `dir-jiedian` / 不限目录 | **CLOSED（字面整改）** | [`registered_by`](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:1197>) 已含 `dir-jiedian`，write_path 已写“不限目录”；生产推断也确实没有目录条件。[代码](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/lib/agentic_rag/clients/lancedb_client.py:2740>)。但登记仍不完整，见下方新 HIGH。 |
| HIGH-2(a) id 全局命名空间 | **CLOSED** | ledger/repo 同节及跨节重复均被 ConfigError 拒绝。[实现](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:468>)。 |
| HIGH-2(b) 严格 kebab | **CLOSED** | ledger/repo 带点 id 均被拒；生产正则为 `[a-z0-9]+(-[a-z0-9]+)*`。[实现](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:483>)。 |
| HIGH-2(c) glob 非空字符串列表 | **NOT-CLOSED** | 标量与 `[null]` 均被 ConfigError 拒绝；但 ledger 中一个 glob 显式为 `[]`、另一个 sibling glob 非空时仍 **ACCEPTED**。[空列表经 `raw_pats or []` 放行](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:641>)。 |
| HIGH-2(d) 普通行禁止 `surface` | **NOT-CLOSED** | 直接自报会被拒；但普通行同时自报 `_section: derived_artifacts` 后，`surface: store` + 空 match 被 **ACCEPTED**，因为 [`setdefault` 信任输入的 `_section`](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:687>)。`repo_docs` 自报 surface 也被接受。 |
| 新 HIGH：resolution rationale=null | **CLOSED** | `requires_resolution_stable=false` + `resolution_unstable_rationale=null` 实跑抛 ConfigError。[实现](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:539>)。 |
| MEDIUM：root scope 枚举 | **CLOSED** | `scope=rootish` 实跑抛 ConfigError。[实现](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:438>)。 |
| MEDIUM：契约总函数化 | **NOT-CLOSED** | `_verify_contract` 内部异常已统一包装；但 invalid UTF-8 在 [`raw.decode`](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:395>) 处仍抛 `UnicodeDecodeError`，越过 CLI 的 ConfigError-only 捕获，结果是 traceback/exit 1。 |

### 仍存在的问题分级

**HIGH**

- `exam_board` 声称推断不限目录，五条 conditional note 也承认可产生该类型，但 `registered_by` 仍遗漏 `dir-raw`、`dir-root-course-cs188`、`dir-multimodal`、`dir-wiki`、`root-loose-md`；因此 `roles: ["wiki"]` 也遗漏 `raw`。checker 目前只验证已列引用的角色，不验证引用完整性。
- `repo_docs` conditional-note 绕过。
- 普通行伪造 `_section` 或 `repo_docs.surface` 的绕过。

**MEDIUM**

- `by_design_divergences.rag_reason`、`memory_reason`、`rationale` 仍用 `str(...).strip()`；三字段的 `null/[]/{}/123` 共 12 个变异全部被接受。[代码](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:561>)。
- YAML 将 `exam_board` 第一条 write path 写成“检验白板目录形态”；代码实际是显式 `type: exam_board` 直通，目录本身不是派生条件。
- YAML 把 memory_service 的 A7 outbox 写成 `backend/data/outbox/`；实际写入 `backend/data/failed_writes.jsonl`，[memory_service](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/app/services/memory_service.py:442>)；`data/outbox/events.jsonl` 属另一套 event bus。

**LOW**

- no-probe help/JSON 已正确，但人读输出仍称“只覆盖 G1/G2/G3/G4”，遗漏实际执行的 G8–G11。[输出文案](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:1224>)。
- YAML `survey_method=os.walk` 已闭合；checker 的 G8 注释/finding 仍以 `rglob` 描述当前实现。
- YAML/常量已是 retrieval 四值；checker 注释仍写“三值”。[注释](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:142>)。
- 测试头的 49 函数 / 31 组 / 116 passed 已闭合；但旧测试仍使用允许点号且不含 repo_docs 的宽松正则。[测试](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/tests/unit/test_vault_doc_roles.py:1212>)。
- launchd 陈述已闭合：仓库及已安装 plist 均为 09:05–20:05 共 12 档并启用 `RunAtLoad`。

本轮仅核对指定单测、生产 checker 与列出的收口面，不代表全量后端测试或 CI。`graphiti-canvas` 本会话未暴露，不影响上述本地 exact-byte、生产入口及内存变异结果。


