总裁定：**需整改**。运行证据均通过，但原 HIGH-1、HIGH-2 及两项 LOW 尚未闭合，另发现 1 项新 HIGH。

## 运行证据

| 项目 | 结果 |
|---|---|
| 三份冻结对象 | 开跑、收尾 SHA-256 均与给定值完全一致 |
| 指定测试 | `109 passed, 10 warnings in 89.62s`，exit 0，无 skip/xfailed |
| 测试实际计数 | **42 个 test 函数 / 30 个编号组 / 109 items**，不是 39 函数 |
| live `--enforce` | exit 0；0 finding；175 目录 / 324 文件；1 个已登记分歧 |
| vault 前后清单 | 324 行逐字节相同；清单 SHA-256 均为 `f49145f869e08eda35cb880ef4f3ff77ce92778b557bdf05184e3fa29ad2f4ea` |
| 工作树 | 未修改；三份冻结对象保持原有 untracked 状态 |

vault 清单采用证据包相同口径：排除 `.git/*`。

## 逐项裁定

| 整改项 | 裁定 | 复核结果 |
|---|---|---|
| HIGH-1 conditional retrieval | **NOT-CLOSED** | `dir-jiedian` 内容已修正，删除 note 会触发 ConfigError；但契约及真相源仍有多处缺口，见下文 |
| HIGH-2 id/match 契约 | **NOT-CLOSED** | 典型重复 id、坏 id、空 match 会被拒；但“全局唯一、kebab-case、glob 结构”仍可绕过 |
| HIGH-3 divergence scope | **CLOSED** | `scope=typo_scope` 实测 ConfigError；枚举门位于 [checker:538](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:538) |
| MEDIUM-1 JSON checks | **CLOSED** | no-probe 实测 `checks_run=G1-G4,G8-G11`，`checks_skipped=G5-G7` |
| MEDIUM-2 no-probe import | **CLOSED** | 将写侧 parser 替换为“调用即抛错”后，`with_probe=False` 仍完成 175/324 扫描，证明未调用 |
| MEDIUM-3 derived 粒度 | **CLOSED** | [YAML:113](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:113) 已区分产物族角色与实例 retention，并写明反向不成立 |
| MEDIUM-4 type 优先级 | **CLOSED** | [YAML:1131](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:1131) 与批量、单文件生产条件一致 |
| LOW 十一类 finding | **CLOSED** | checker 已写 G1–G11 |
| LOW `rglob → os.walk` | **NOT-CLOSED** | checker 已改，但 [YAML:73](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:73) 仍称 survey 使用 `rglob` |
| LOW DIV-2 文档 | **CLOSED** | 两个窄 pattern 正确排除全小写 `.md` |
| LOW 测试计数 | **NOT-CLOSED** | [tests:4](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/tests/unit/test_vault_doc_roles.py:4) 仍写 38/27；实际 42/30 |

## 关键未闭合证据

HIGH-1：

- [YAML:336](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:336) 的 `dir-jiedian` 已正确写为 conditional。
- 但 `rag_retrieval_note: null`、`[]`、`{}`、`123` 均被接受；[checker:588](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:588) 使用了 `str(value).strip()`。
- `repo_docs` 可声明 conditional 且不带 note，仍被接受。
- 生产推断 [lancedb_client.py:2740](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/lib/agentic_rag/clients/lancedb_client.py:2740) 不限制目录。当前另有五个允许 `(none)`、`rag_index=true`、却声明 `included` 的条目：`dir-raw`、`dir-root-course-cs188`、`dir-multimodal`、`dir-wiki`、`root-loose-md`。
- [YAML:1161](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:1161) 的 `exam_board.registered_by/write_path` 仍漏掉 `dir-jiedian` 的真实推断路径。

HIGH-2：

- 唯一性/格式仅覆盖三个 ledger 节；`repo_docs` 内重复、跨节重复及 `Repo_BAD` 均被接受，[checker:639](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:639)。
- kebab 正则允许 `foo-bar.baz`、连续点及尾点，[checker:466](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:466)。
- `dir_glob: "节点"` 标量会被接受；`dir_glob: [null]` 抛 TypeError，而非 ConfigError。
- 普通 vault 行注入 `surface: store` 后可用空 match 且无 identifier 通过；“identifier 兜底”可被自报 surface 绕过。

## 新发现

- **HIGH**：`requires_resolution_stable: false` 加 `resolution_unstable_rationale: null` 被接受；运行时确实关闭稳定性绑定，使解析不稳定路径可被既有 divergence 覆盖。[checker:530](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:530)

- **MEDIUM**：`root_files.scope` 无枚举校验，拼错后静默按 root 处理。[checker:655](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/check_vault_doc_roles.py:655)

- **MEDIUM**：契约校验不是总函数；畸形 glob/pattern 成员可产生未捕获 TypeError/AttributeError，而 CLI 只捕获 ConfigError。

- **LOW 文案差异**：
  - YAML、checker、测试头仍称 retrieval“三值”，实际为四值。
  - checker 的 no-probe 说明仍称只跑 G1–G4，实际还跑 G8–G11。
  - 测试头仍称九个必填字段，实际为十个。
  - [YAML:840](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t4-roles/backend/scripts/vault_doc_roles.yaml:840) 称 launchd“每日 09:05”；tracked plist 实际为 09:05–20:05 每小时一次并启用 RunAtLoad。

本轮只验证了指定单测与生产 checker，不代表全量后端测试或 CI。`graphiti-canvas` 工具在本会话未暴露，因此未执行 AGENTS 要求的 Graphiti memory 查询；该限制不影响上述本地冻结对象和生产入口证据。


