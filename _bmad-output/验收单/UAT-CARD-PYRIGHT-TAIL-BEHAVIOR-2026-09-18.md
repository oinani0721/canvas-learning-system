# UAT — CARD-PYRIGHT-TAIL-BEHAVIOR

> 批次 `[BATCH-2026-09-18-第十五批 / CARD-PYRIGHT-TAIL-BEHAVIOR]` · 车道 `card-p8-backend`（P8 第 2/3 张）
> 卡文：`_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P8-B.md`（主干树只读副本）
> 协议：`.claude/rules/card-batch-protocol.md`（主干树只读副本）§1 / §2.1 / §2.2 / §2.3 / §3 / §5

## 〇 终态字段（收工重算）

| 字段 | 值 |
|---|---|
| `PREV`（开工 HEAD = P8-A 末 commit） | `2038278a` |
| 本卡代码 commit 数 | **5**（`b8500c6e` 纯格式 / `2617a930` 语义+新测试 / `b46a280f` r1 整改 / `3596e98b` 对抗复核整改 / `5e8a76fd` 纯 docstring）+ 1 个 evidence commit `ec4c6697` |
| 最终代码 SHA | `5e8a76fd`（末位为纯 docstring commit，D-32 等价自证；Codex r2 绑的是其前一个 `3596e98b`） |
| Codex 轮次 | 2（另有 1 次 0 字节配额耗尽，不计配额）+ 1 次内部多 agent 对抗复核（96 agents，另存档） |
| evidence 档数 | 55（`find -size 0` = 0，带验伪锚：故意造一个 0 字节文件检查必须报它） |
| 地盘文件数 | 7（6 个 `backend/app/services/*.py` + 1 个 NEW 测试） |

## 一 (a) 第 0 分钟

| 项 | 实测 |
|---|---|
| `pwd` | `…/worktrees/card-p8-backend` ✓ |
| `git branch --show-current` | `card/p8-backend` ✓ |
| `git rev-parse --short=8 HEAD` | `2038278a` ✓ |
| subject 含 `CARD-EXC-HANDLER-WIRE-REDACT` | `grep -cF` → 1 ✓ |
| `git status --porcelain \| wc -l` | 0 ✓ |
| `test -e backend/.venv/bin/pytest` / `backend/.env` | 均存在 ✓ |
| pyright 自证 `( test -x "$P" \|\| { echo 缺席; exit 1; } )` | OK（绝对路径，含 `exit` 的块已包进子 shell） ✓ |
| `grep -vc '^#' "$BASE"` | **33** ✓（`evidence-b15/unit-red-baseline-9c4e7e82.txt`） |
| 开工 `tests/unit` 目录级（跑法与基线头第 3 行逐字同，不带 `--ignore`） | `33 failed, 5738 passed, 44 skipped, 13 xfailed`，nodeid 集与批次基线 **diff 为空** |
| §〇 八项 file:line 逐字核 | 全部命中，**零漂移**（见下「卡文实测更正」第 2/3 条例外——那两处是卡文对行号**语义描述**的偏差，不是锚点漂移） |
| 手册 §一.1 P8 地盘行 | 已抄（下方 §六），⛔ 未改手册 |

## 二 卡文事实的实测更正（逐条如实，供主 session 与下一张卡复用）

1. **`md_file_index` 的键不是「文件名」，是动态的**。卡文 §〇 写「键 = 文件名、值 = vault 内相对路径」。
   实测（obsidiantools 随包）：**无重名时键是裸文件名**（`note` → `sub/note.md`），
   **出现同名不同目录时自动改用去扩展名的相对路径**（`sub/note` / `sub2/note`），
   且 `Vault.graph` 的节点名**同步跟随**同一套键。
   ⚠️ **本条的初版结论「两者恒同域、不存在歧义」是错的，已被 Codex r1 LOW-2 推翻并由主 session 复跑确认。**
   实况：**图节点是索引键的真超集** —— 图节点 = 索引键 ∪ 正文 wikilink 的目标文本。
   反例实测（重名 `sub/note.md` + `sub2/note.md`，另有笔记写裸名 `[[note]]` 与 `[[data.txt]]`）：
   索引键 = `{hub, sub/note, sub2/note}`，图节点额外多出 `{note, data.txt}`。
   我的初版边界探针只测了「重名」与「嵌套目录」两个维度、**没测它们与裸名链接的组合**就下了结论——
   典型的「判据面比主张面窄」。多出来的键查不到索引 ⇒ 走兜底 `f"{key}.md"`，行为与旧实现一致（**代码没错，是说明错**）。
   现已把该反例做成常驻门 `test_resolve_path_falls_back_for_unresolved_link_targets`，
   并在 `_resolve_path` 的 docstring 里改成如实表述。
2. **`intelligent_parallel_service.py:628` 的语义描述偏差**。卡文 (d) 写「:626 日志之后、取 canvas 内容 :628 之前」。
   实测 :628 是 `if self._agent_service is None:`（依赖检查），:636 才是 `await self._get_node_content(...)`。
   本卡按卡文**字面位置**（:626 日志之后）插入 `AgentType(agent_type)` 校验，即落在依赖检查**之前**——
   这正是 (g)⑤ 的门能用真默认实例（未注入 `agent_service`）跑通的原因；顺序含义见代码注释与 Codex 问题②。
3. **`exam_service.py` 的 `limit: int = 20` 在 :115 不是 :112**（卡文 (k)② 写 :112）。负控段②按实测 :115 做。
4. **卡文判据 4 与卡文实现规格 (c) 自相矛盾**：(c) 要求抽 `_build_misconception(*, …, created_at: str)`，
   调用它必然写 `created_at=`；而判据要求 `grep -cE '^\s*created_at=' error_classifier.py` 1 → **0**。
   实测改后仍为 **1**（那是新纯函数自己的 kwarg 名，不是 `Misconception` 的字段名）。
   真正锁住缺陷的判据已补为 **AST 口径**：`Misconception(...)` 调用点的 kwarg 集合
   **不含** `created_at`、**含** `misconception_created_at`（实测 call_sites=1，kwargs 见下方 DoD-3）。
5. **三条文本判据被本卡自己的说明性注释/docstring 命中**（判据数的是文本、不是代码）：
   卡文要求 `get_litellm_config` 3→0、`agentic_rag.embedding` 1→0、`get_source_path` 2→0，
   实测改后分别是 **1 / 1 / 1**——全部来自本卡**故意保留**的「改前是什么、为什么改」注释与 docstring。
   已补 **AST 口径判据**（`ast.unparse` + 递归剥 docstring 后再数），三项实测 **0 / 0 / 0**，
   并配三条验伪锚（`get_runtime_model_config`=2、`md_file_index`=1、`降级为文本搜索`=2，均非零命中）。
   ⚠️ 验伪锚期望值本身一度写错（`降级为文本搜索` 我先写成 1，实测 2）——**判据写错会伪装成代码错**，
   已在真文件上实测后改正，原始 BAD 输出保留在 `struct-ast-after-20260918T200234.txt`。
6. **`ruff format --check` 是硬门，而本卡六个文件属主干既有漂移集**（`backend/app` 实测 141 文件 would reformat；
   `backend/ruff.toml` `line-length=120` 而代码按 88 列写）。P8-A 改的 6 个文件全是 `already formatted`，
   所以上一张卡没遇到这道门。处置见 §三 (o)。

## 三 完成条件逐条

### (b) 先红（改代码前落档）

- **结构基线**：`struct-before-20260918T192029.txt` → ignore 计数 `1/1/1/3/2/1/1/1/0`（合计 **11**）·
  `litellm=3 · runtime_cfg=0 · created_at=1 · mc_created=0 · cancelled=0 · agenttype=0 ·
  deadimport=1 · srcpath=2 · mdindex=0 · tnew7=1 · query_eq=2` —— 与卡文预期逐字相符。
- **行为红**：`tail-red-replay-20260918T200104.txt`（⚠️ 这份是**与最终测试文件严格同源**的重放：
  先把六个文件 `cp` 备份、`git show HEAD:<path> > <path>` 还原成改前态跑一次，跑后从备份恢复，
  跑前/跑后 `shasum -a 256` 六行逐字同、`git status --porcelain` 只列本卡地盘文件。
  此前两份 `tail-red-*` 对应的测试文件有一处枚举名差异，作为过程档保留、不作承重）。
  **9 failed / 6 passed**，红因分两类，逐条如实：
  - 红在**行为断言**（4 条）：`assert 'note.md' == 'sub/note.md'`、`assert 'unique.md' == 'sub/unique.md'`、
    `RuntimeError: agent_service not injected …`（T-new-6：改前校验在依赖检查之后 ⇒ 先抛 RuntimeError）、
    `AssertionError: 已无死 import ⇒ 不得再把原因写成 ImportError`
  - 红在**符号缺席**（5 条，非行为断言，如实标注）：`_resolve_intent_model` / `_INTENT_FALLBACK_MODEL` /
    `_build_misconception` / `_classify_gather_result`（×2）`ImportError`
  - 新符号一律在**用例函数体内** import，避免模块级 collect error 把「红在断言」的证据一并吞掉。
- **TYPE_CHECKING AST 门改前即绿**：`typecheck-ast-20260918T194246.txt` → `declared 11 mismatch []`
  （符合卡文 (b) 预期；其「红」由 (k)② 负控给出）。

### (c) 组 1 — 静默降级改真接线

| 项 | 改动 | 去掉的 ignore |
|---|---|---|
| **T-new-3** `agent_routing_engine.py` | `get_litellm_config`（**不存在的名字**）→ `get_runtime_model_config`；抽模块级 `_resolve_intent_model(config=None) -> str` + 常量 `_INTENT_FALLBACK_MODEL`；`except Exception` 收窄为 `except (ImportError, AttributeError, RuntimeError)` 且 `logger.warning` 一次；无配置回落走 `logger.debug`（正常路径不刷 warning）。⛔ 未改 `litellm.acompletion` 调用与 prompt、未改 `litellm_config.py`（只在 `TYPE_CHECKING` 块加了一行类型 import） | `reportAttributeAccessIssue` ×1 |
| **T-new-1** `wikilink_graph_service.py` | `self._vault.get_source_path(note_key)` → `self._vault.md_file_index.get(note_key)`；`Path(source).as_posix()`；None 回落 `f"{note_key}.md"`；`except Exception` 收窄为 `except (AttributeError, KeyError, TypeError)`。⛔ 未动 `_get_frontmatter`、未做 D-G 键归一化、未改 `:213` 调用形态 | `reportAttributeAccessIssue` ×1 |
| **T-new-2** `error_classifier.py` | kwarg `created_at=` → `misconception_created_at=`；建实体逻辑抽成模块级纯函数 `_build_misconception(*, error_type, description, context, remedy, node_id, session_id, created_at)`；`classify()` 改调它，LLM 调用原样。⛔ 未改 `entity_types.py`、未动 `classify_with_pedagogy` | `reportCallIssue` ×1 |

### (d) 组 2 — 异常 / 类型语义

| 项 | 改动 | 去掉的 ignore |
|---|---|---|
| **T-new-5** `batch_orchestrator.py` | 新增模块级 `_classify_gather_result(result) -> Literal["ok","failed","cancelled"]`；`_execute_all_groups` 与 `_execute_group` 两处 `isinstance(result, Exception)` → `isinstance(result, BaseException)`（取消才筛得掉），取消记 `status="failed"`、`failed_count += 1`、**不 append 原异常对象**（⚠️ `error_type="CancelledError"` 只在 **node 级**的 `NodeExecutionResult` 上成立——group 级的 `GroupExecutionResult` **没有** `error_type` 字段，Codex r1 LOW-1b 指出；代码未给它传该字段，是初版文档措辞把 node 级说成了两级通用），并各记一条区分取消的日志；`error_message` 用 `str(result) or type(result).__name__`（`str(CancelledError())` 是空串）。⛔ 未改两处 `gather(..., return_exceptions=True)`、未改结果模型字段、未改并发上限 | `reportArgumentType` ×2 + `reportAttributeAccessIssue` ×1 |
| **T-new-6** `intelligent_parallel_service.py` | 入口（`logger.info` 之后）加 `AgentType(agent_type)`，`ValueError` → 立即返回 `SingleAgentResponse(node_id=…, status=SingleAgentStatus.failed, error_message=f"unknown agent_type: {agent_type}")`（⛔ 未加字段——该模型**没有** `success` 字段，卡文 (g)⑤ 的「`success is False`」按实际字段落成 `status == SingleAgentStatus.failed`）；`call_agent` 改传枚举值。`:659` 的 `hasattr` 守卫与其 ignore **保留**（零行为）。⛔ 未改端点、未改 `AgentType` 枚举 | `reportArgumentType` ×1（保留 `reportAttributeAccessIssue` ×1） |

### (e) 组 3 — 退役 + 一致性门 + T-new-7 不动

- **T-new-8** `multimodal_service.py`：删死 import 与其后**不可达**的重试循环（被调对象从不存在）；
  函数体改为「`logger.warning`（文案仍含 **`降级为文本搜索`**，原因如实写「未接入 embedding 服务」、不再写 ImportError）→ `return None`」。
  随之退役 `import asyncio`、`EMBEDDING_MAX_RETRIES`、`EMBEDDING_RETRY_DELAY`。
  ⚠️ 引用面如实（初版写「全仓再无引用」，判据面其实只有 `backend/**/*.py`，Codex r1 LOW-3 指出）：
  全仓**可执行代码**（`*.py` / `*.sh` / `*.js` / `*.ts`）对这三个名字 **0 命中**；
  文档里仍有历史提及（`docs/stories/36.13.story.md` 把 `EMBEDDING_RETRY_DELAY` 登记为「✅ 常量」），
  该登记在退役后已失实，归第十六批一并更正。
  `search()` 侧两处不动 ⇒ **用户可见行为不变**（文本搜索、`search_mode="text"`）。补实现 = 第十六批。
- **TYPE_CHECKING 门**：门内两条用例——签名逐条比对（`(name, is_async, unparse(args), unparse(returns))`）+
  声明名集合 == `attach_to_exam_service()` 内 11 条赋值目标名集合。**实测 11/11 一致 ⇒ 两文件零改动**。
- **T-new-7 ⛔ 未做**：`learning_context_service.py` **零改动**（`git diff --name-only` 该文件为空），
  `:205` 的 ignore 与 census 注释原样；`query_eq` 改前=改后=2。用户在本卡期间未裁「接通」⇒ **SKIP 登记**（见 §五/§六）。

### (f) 结构判据（改前 X / 改后 Y 成对 + 验伪锚）

`struct-before-20260918T192029.txt` ↔ `struct-after-20260918T195759.txt`（同一条命令）：

| 项 | 改前 | 改后 | 结论 |
|---|---|---|---|
| ignore 计数（九文件） | `1/1/1/3/2/1/1/1/0`（11） | **`1/0/0/0/1/0/0/1/0`（4）** | ✓ 保留 `learning_context:205` / `intelligent_parallel:659` / `exam_service:559` |
| `runtime_cfg`（非注释） | 0 | **2** | ✓ ≥2 |
| `mc_created` | 0 | **1** | ✓ |
| `cancelled`（非注释） | 0 | **3** | ✓ ≥1 |
| `agenttype`（非注释） | 0 | **1** | ✓ ≥1 |
| `mdindex` | 0 | **2** | ✓ ≥1 |
| `tnew7`（T-new-7 不动锚） | 1 | **1** | ✓ 相等 |
| `query_eq`（T-new-7 零改动锚） | 2 | **2** | ✓ 相等 |
| **验伪锚** `exam_service` 项 | 1 | **1** | ✓ 恒 1（未触该文件，证 grep 真在数） |
| `litellm` / `created_at` / `deadimport` / `srcpath` | 3 / 1 / 1 / 2 | 1 / 1 / 1 / 1 | ⚠️ 未达卡文预期，根因见 §二.4 / §二.5，已补 AST 口径判据 |

**AST 口径补充判据**（`struct-ast-after-20260918T200305.txt`，脚本全文内联在档内以便复核）：

```
OK  agent_routing_engine.py    get_litellm_config        got=0 expected=0
OK  agent_routing_engine.py    get_runtime_model_config  got=2 expected=2   ← 验伪锚
OK  multimodal_service.py      agentic_rag.embedding     got=0 expected=0
OK  multimodal_service.py      降级为文本搜索              got=2 expected=2   ← 验伪锚
OK  wikilink_graph_service.py  get_source_path           got=0 expected=0
OK  wikilink_graph_service.py  md_file_index             got=1 expected=1   ← 验伪锚
OK  multimodal_service.py      EMBEDDING_MAX_RETRIES     got=0 expected=0
OK  multimodal_service.py      asyncio                   got=0 expected=0
call_sites=1
  kwargs=['context','description','error_type','misconception_created_at','misconception_id','node_id','remedy_strategy','session_id']
FAILURES=0
```

### (g) 承重行为门（终态 24 条）

`backend/tests/unit/test_pyright_tail_behavior.py` — 收集 **24** 条（≥9；15 条初版 + 9 条按两轮复核补的门），
`tail-green-r3-*.txt` → **24 passed**、rc=0。
**零 mock / 零 monkeypatch / 零替身 / 零连库**（W4 哨兵 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0 (blocked=0, advisory=0, unaccounted=0)`），
文件头写有替身清单。既有 `test_multimodal_fixes.py` 的两条相关用例收工仍 passed（见 (i)）。

判别力如实标注（哪些门测得出改动、哪些测不出）：

| 用例 | 判别力 |
|---|---|
| `test_resolve_path_falls_back_for_unknown_key` | ⚠️ **无判别力**（改前异常后也回落同一个值）。锁的是「修复没把兜底顺手弄丢」 |
| `test_resolve_path_disambiguates_duplicate_basenames` 里重名那两键 | ⚠️ **无判别力**（旧回落 `f"{key}.md"` 恰等于真值）。判别力来自同 vault 内不重名的 `sub/unique.md` 那条断言 |
| `test_legacy_created_at_kwarg_is_silently_dropped_by_model` | ⚠️ 改前/改后**都绿**。它是**缺陷机理门**，锁「为什么必须改 kwarg 名」（pydantic `extra='ignore'` 静默丢值） |
| `test_gather_return_exceptions_surfaces_cancellation_as_non_exception` | 不依赖本卡任何新符号，证明**缺陷输入面真实存在**（真 cancel 后 `isinstance(result, Exception)` 为 False） |
| 其余 | 有判别力（见 (b) 先红红因） |

### (h) pyright 保持 0（三次实测同数）

`pyright-before-20260918T192214.txt` → `0 errors, 80 warnings, 0 informations`
`pyright-after-*.txt`（初版 / r1 整改后 / r2 定稿后共三次）→ 每次都是 `0 errors, 80 warnings, 0 informations`
⛔ 未用 `LEFTHOOK_EXCLUDE=python-typecheck`（两次 commit 的 lefthook `python-typecheck` 均 `exit: 0`）；
本卡**未新增**任何 `# pyright: ignore`；新增的 `# type: ignore[call-arg]` 只有测试文件里故意传旧 kwarg 那一处。
⛔ 未用 `| tail -1` 取汇总行（改用 `grep -E '^[0-9]+ errors?, '`）。

### (i) 既有套件不回退

| 套件 | 开工 | 收工 | 结论 |
|---|---|---|---|
| 19 个点名 `tests/unit` 文件 | `3 failed, 393 passed` | `3 failed, 393 passed` | ✓ 同 3 个 nodeid（`test_intelligent_parallel_endpoints.py` 的 404 三条，既有红） |
| `tests/api` 目录级 | `269 passed` | `269 passed` | ✓ |
| `tests/regression` 目录级 | `1913 passed, 6 skipped, 1 xfailed` | `1913 passed, 6 skipped, 1 xfailed` | ✓ 逐项一致 |
| `tests/unit` 目录级 | `33 failed, 5738 passed`（nodeid 集 == 批次基线） | `32 failed, 5763 passed`（`unit-close-final-*.txt`） | ✓ diff **只有一行 `<`**，`comm -13` 空 ⇒ 本卡引入 0 |

⛔ 未碰任何 `conftest.py`。

⚠️ **那条 flaky 的三次观测如实记录**（不靠「基线头说它 flaky」一句话背书）：
`test_candidate_service::test_accept_candidate_already_accepted_returns_422`
在批次基线里**红**、在本卡 `unit-close-final` 里**绿**、在 19 文件套件 `suite-close-r3` 里又**红**
——同一代码状态下三次观测两红一绿，与基线头第 4 行「flaky … 已在集内」的标注一致。
本卡改动面（六个 services 文件）与 `candidate_service` 无任何调用关系。

### (j) openapi

不改端点（只改 `backend/app/services/**` + 新 unit 测试）；lefthook `spec-sync-flat`（`backend/app/{api,models,schemas,mcp}/*.py`）
与 `spec-sync-root`（`backend/app/{main.py,config.py}`）两 glob 均**不命中** ⇒ **不适用**。
两次 commit 后 `git --no-pager show --stat --no-color HEAD | grep -c openapi` 均为 **0**，hook 未塞入 `openapi.json`。
⛔ 零 `LEFTHOOK_EXCLUDE`、零 `--no-verify`。

### (k) 负控三段

每段：备份 → `trap 'git show HEAD:<path> > <path>' EXIT` → 只拆一层 → 跑门 → 还原 → `shasum` 前后比对。
⚠️ 顺序按协议教训「改完 → commit → 跑负控」（`git show HEAD:` 还原会吞掉未提交改动），故三段均在语义 commit 之后跑。

| 段 | 拆的那一层 | 实际红在 | shasum 前后 | porcelain |
|---|---|---|---|---|
| ① `batch_orchestrator.py` | 删 `_classify_gather_result` 的 `CancelledError` 分支（:153–154） | `test_classify_gather_result_separates_cancellation_from_failure` — `AssertionError: assert 'failed' == 'cancelled'` ✓ | 逐字同 | 0 |
| ② `exam_service.py` | `:115` `limit: int = 20` → `21` | `test_type_checking_declarations_match_ext_signatures` — `声明与真实签名不一致: {'get_exam_records': ((…limit: int=21…), (…limit: int=20…))}` ✓ 证门**看得见默认值** | 逐字同 | 0 |
| ③ `wikilink_graph_service.py` | `:331` `md_file_index.get` 改回 `get_source_path` | `test_resolve_path_returns_vault_relative_path_for_nested_note` — `assert 'note.md' == 'sub/note.md'`；并连带 `test_resolve_path_disambiguates_duplicate_basenames` — `assert 'unique.md' == 'sub/unique.md'` ✓ | 逐字同 | 0 |

三段都是「红在**指定断言**」，不是「某处有失败」。

### (l) 地盘核

`territory-*.txt`：`git --no-pager diff --stat --no-color 2038278a HEAD -- . ':(exclude)_bmad-output'` 恰 **7** 个文件：

```
backend/app/services/agent_routing_engine.py
backend/app/services/batch_orchestrator.py
backend/app/services/error_classifier.py
backend/app/services/intelligent_parallel_service.py
backend/app/services/multimodal_service.py
backend/app/services/wikilink_graph_service.py
backend/tests/unit/test_pyright_tail_behavior.py          (NEW)
```

⊆ 卡文 (l) 白名单 ✓。禁改面 `learning_context_service.py` / `exam_service_ext.py` / `exam_service.py` /
`main.py` / `api/**` / `models/**` / `graphiti/**` / `clients/**` / `core/**` 的 `--name-only` **为空** ✓。
（另用 `--name-only` 复核了一遍，防 `--stat` 把长路径首段缩写成 `.../`；并带 `-c core.quotepath=false`。）

**验伪锚**（`territory-final-*.txt`，evidence commit `ec4c6697` **之后**重跑才生效）：
不带 `':(exclude)_bmad-output'` 时 `_bmad-output/` 条目 = **57**；带 exclude 时 = **0**
⇒ exclude 真的在起作用，判据**非空洞**。
（⚠️ 首次跑时该锚为 0 —— evidence 尚未 commit，`git diff` 不显示未跟踪文件，
带不带 `':(exclude)_bmad-output'` 输出相同，锚在 commit 前恒空洞；已在 evidence commit 后重跑。）

### (m) 现网只读

本卡零连库、零 vault 读写（新测试只用 `tmp_path`）。
`git diff --name-only $PREV HEAD -- . ':(exclude)_bmad-output' | xargs grep -n -e fsrs_bridge -e decay_beta -e 7691 -e 7687`
→ **无输出、`grep_rc=1`**（`live-readonly-*.txt`）。⚠️ 首次跑命中 1 条，来自新测试文件头部**说明性注释**里写的端口字面量（「零连库(7691/7687/7692 均不触)」）
——又一次「判据数的是文本、不是代码」。已改写该注释措辞使判据真正无命中。
未设任何指向现网的环境变量；W4 哨兵在每次 pytest 收尾都打印 `blocked=0, advisory=0, unaccounted=0`。

### (n) Codex

见 §四。

### (o) 提交

本卡 **4 个代码 commit + 1 个 evidence commit**（均未 push）：

| SHA | header | 说明 |
|---|---|---|
| `b8500c6e` | `chore(format): ruff format 六个 services 文件 [BATCH-…]`（94 字符） | **纯格式**。见下 |
| `2617a930` | `fix(services): 七项 pyright ignore 掩盖的真缺陷改成真行为 [BATCH-…]`（97 字符） | 语义 + 新测试 |
| `b46a280f` | `fix(services): 按 Codex r1 + 内部对抗复核整改说明与门 [BATCH-…]` | 四处说明改到如实 + 补 8 条门 |
| `3596e98b` | `fix(services): 补下游端到端门 + 三处如实标注 [BATCH-…]` | 端到端门 + 三处标注；**最终代码 SHA** |
| （末位） | `docs(uat): …` | evidence + 验收单 + prompt + Codex 存档 |

**为什么拆出一个纯格式 commit**：本卡六个文件属主干既有 ruff 漂移集，而 lefthook 的
`ruff format --check {staged_files}` 是**整文件**判定、无法只对本卡改动行放行；D-40 的整仓 format
要到第十五批末位才由主 session 做。为了让语义 commit 的审查面**不含格式噪音**，
先把六个文件 `git show HEAD:<path>` 还原成 `PREV` 态、只跑 `ruff format` 单独提一个 commit。
**纯格式自证**：逐文件 `ast.dump(ast.parse(PREV版)) == ast.dump(ast.parse(format后))` → 六个全部 `True`。
⛔ 全程零 `LEFTHOOK_EXCLUDE`、零 `--no-verify`；`ruff check` rc=0；`ruff format --check` 7 文件 all formatted。
`*.stderr*` 未入库；0 字节存档 —— `find … -size 0` 为空。

**ruff 验伪锚**（F821；`backend/ruff.toml` 的 `select` 只有 `E9/F63/F7/F82`，**无 F401** ⇒ 锚必须选 F821）：
`ruff-*.txt` → 本卡 7 个改动文件 `All checks passed!` `ruff_rc=0`；探针 `def f(): return undefined_name_x`
→ `F821 Undefined name` + `probe_rc=1`（证 ruff 真在检查），探针随后移出工作树、未入 commit。

### (p) 见 §五「本卡未证明什么」与 §六「台账待登记条目」

## 四 Codex 复核

命令（协议 §2 固定形态，模型 `gpt-6-astra` + `ultra`）：

```
codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" \
  "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-PYRIGHT-TAIL-BEHAVIOR.md)" \
  > _bmad-output/审查/codex-review-CARD-PYRIGHT-TAIL-BEHAVIOR[-rN].md \
  2> _bmad-output/审查/codex-review-CARD-PYRIGHT-TAIL-BEHAVIOR[-rN].stderr </dev/null
```

prompt 五分节齐（①背景 + 最小读取面写死 15 项 / ②作者自述请独立核对 6 条 / ③按重要性排序的 8 个问题 /
④输出格式 BLOCKER-HIGH-MEDIUM-LOW + `file:line` + 一句复现思路 / ⑤边界）；
措辞已核：协议 §2 的四个禁用词计数 = **0**（起草时「首次构造时」已改为「首次实例化时」）。
问题③里明确要求用 **负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径** 四类措辞。
prompt 第 15 项（手册 §零.16）**不在本 worktree**，已改成绝对路径并标注「读不到就跳过，结论已在 ②.2 与 ⑤ 复述」，
避免复核方落到空读取面。三个短 SHA 均经 `git cat-file -t` 验证为真 commit（⛔ 不手工补全短 SHA）。

### r1（绑 `2617a930`）—— **0 字节，配额耗尽，不计入轮次配额**

- 存档 `codex-review-CARD-PYRIGHT-TAIL-BEHAVIOR-r1.md` 实测 **0 字节**，`codex_rc=1`；
  按协议「0 字节存档不入 commit」已移出仓库（留在 session scratchpad）。
- `.stderr` 末两行：`ERROR: You've hit your usage limit. Visit … or try again at Sep 24th, 2026 2:05 AM.`
  `.stderr` 被 `.gitignore:264`（`_bmad-output/审查/**/*.stderr*`）覆盖，**不入库**。
- 会话头自证（抄自 `.stderr`，括注行号；协议 §2.1）：
  `4:OpenAI Codex v0.153.3` / `7:model: gpt-6-astra` / `11:reasoning effort: ultra`
  ⚠️ 协议 §2.1 举例说 codex 0.153.3 把 `model:` 排在会话头第 5 行；本次实测在**第 7 行**
  （会话头前多了两条 `codex_models_manager` 的 refresh 超时 ERROR）。这印证协议那句「行号不限、括注行号」——
  按固定行号字面抄会漏自证字段。
- ⚠️ **不继承那个「9 月 24 日」**：既有教训「外部服务的重置时间是一次观测不是不变量」
  （`dcaaaef9` 的批级通告曾被 24 分钟后的实测推翻）。重发时按协议实际复测，不按该日期停工。

### r1（重发，绑 `2617a930`）—— **BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 4**

存档 `codex-review-CARD-PYRIGHT-TAIL-BEHAVIOR-r1.md`（6702 字节，含协议 §2.1 首部），
`codex_rc=0`。自证三行同上（`4:` / `7:` / `11:`）。首句自述绑定
`2617a930fdc62fc487c0bd5c26423ac992a5af07` == 送审时 HEAD。

**按合并门（协议 §1）：阻断级 = 0，BLOCKER = 0、HIGH = 0 ⇒ 该轮通过。**
但 4 条 LOW 全部是**「我写的说明比事实更强」**，按 DD-13 名实一致逐条改到如实（不是改行为——行为都对）：

| # | Codex 指出 | 我的独立复核 | 处置 |
|---|---|---|---|
| LOW-1a | `_classify_gather_result` docstring 称「`KeyboardInterrupt`/`SystemExit` 会成为 gather 结果项，归 failed 比改前收紧」——**不成立**。实测 Python 3.14.4：子协程真正 `raise KeyboardInterrupt()` 时 gather **不返回结果列表**，原异常在 `asyncio.run()` 边界抛出，改前改后都到不了那两个循环 | 接受。这是我凭 `BaseException` 的类型关系**推演**出来的行为，没有实测过 | 改写 docstring 为如实表述 |
| LOW-1b | 外层 `GroupExecutionResult` **没有** `error_type` 字段，注释/commit body 称「取消记 status=failed / error_type=CancelledError」对 group 级不成立 | 核实：`GroupExecutionResult` 字段为 `group_id/agent_type/status/node_results/completed_count/failed_count`，确无 `error_type`。**代码没错**（我并未给它传该字段），是文档措辞把 node 级说成了两级通用 | 验收单 §三(d) 更正；新 commit body 写明 |
| LOW-2 | `_resolve_path` docstring 称「两者恒同域、不存在歧义」**过强**。反例：重名 `sub/note.md` + `sub2/note.md`，另有文件写裸名 `[[note]]` ⇒ 图多出索引里没有的 `note` 节点；`.txt/.pdf` 等非 md 链接目标同理 | 接受。我的边界探针**没测这个组合**（重名 ∧ 裸名链接）——「关于证据的断言必须先数一遍再写」 | 改写 docstring；并把该反例**做成常驻门**（说明失实 → 行为已锁） |
| LOW-3 | 常量退役注释称「全仓再无引用」不准确：`.gdr/prd-backend-pack.md:29616–29617`、`docs/stories/36.13.story.md:46` 仍有文字提及 | 接受。我的 grep 面是 `backend --include='*.py'`，写结论时却说了「全仓」——判据面 ≠ 主张面 | 改为「全仓**可执行代码**再无引用；文档中仍有历史提及」 |
| LOW-4 | 测试文件头称「零网络」不成立：import 服务链会触发 LiteLLM 拉远端价格表 | 接受。我自己在边界探针里**亲眼看到过**这条 `Failed to fetch remote model cost map` 警告，却仍在文件头写了「零网络」 | 改为「零主动网络调用；import 链会触发 LiteLLM 价格表拉取尝试（既有行为，非本卡引入）」 |

**另一条独立复核出的数字更正（Codex 问题 6 附带指出）**：

> **ignore 计数是 `11 → 3`，不是 `11 → 4`。**

自己逐文件数并求和：改前 11、改后 `1+0+0+0+1+0+0+1+0` = **3**。
卡文 §一(f) 写「合计 **4**：保留 learning_context :205、intelligent_parallel :659、exam_service :559」——
**列了 3 条却写 4**，是卡文自身的算术错误；卡文给的向量 `1/0/0/0/1/0/0/1/0` 本身正确。
我此前在语义 commit body 与本验收单初稿里沿用了「4」。commit `2617a930` 的 body **不 amend**
（amend 会改 SHA、破坏 r1 的审查绑定），更正写在本验收单与后续 commit body 里。
保留的三条实测位置：`learning_context_service.py:205` / `intelligent_parallel_service.py:629`
（卡文写 :659，纯格式 commit 后行号变）/ `exam_service.py:559`。

**Codex 对我 8 个问题的回答里，另外几条如实记录（不改代码）**：

- 问题 1：`model = _resolve_intent_model()` 位于 `_llm_classify_intent` 后半段 `try` 之**外**，
  非 `(ImportError, AttributeError, RuntimeError)` 的异常（如 pydantic `ValidationError`）可以外溢。
  Codex 实测「当前空配置不是触发条件」⇒ 无实际缺陷。卡文 (c) 明确规定了这个 except 元组，
  **本卡不扩大它**；改为在 docstring 里如实写明这条边界。
- 问题 2：空串 / `None` / `"FOUR-LEVEL"` 大小写变体**都被拦下**，返回 `failed` + `unknown agent_type`；
  合法取值 + 未注入依赖仍抛 `RuntimeError`。⚠️ 「无效参数会遮住同时存在的依赖缺失」——这是**新增的校验优先级**，
  如实登记。端点 404/422 语义**未确认**（端点文件不在允许读取面内）。
- 问题 5：两种 AST 负控**都会通过**（门静默跳过）——即门对「`TYPE_CHECKING` 块内新增非 def 语句」
  与「ext 新增未挂载的模块级 def」都不报错。这从「本卡未证伪」升级为 **Codex 已证实的盲区**，§六.6 更新。
  另：删掉自动挂载调用、改赋值右侧，门仍可能通过 ⇒ 门不证明运行期挂载（与 §六.6 原有结论一致）。
- 问题 7：三个被删名称在本文件内无残留引用，也无具名/星号 import 从该模块取它们（文档提及见 LOW-3）。

### r2（绑 `3596e98b`）—— **BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 2**

存档 `codex-review-CARD-PYRIGHT-TAIL-BEHAVIOR-r2.md`（7935 字节，含协议 §2.1 首部），`codex_rc=0`。
自证三行同 r1。首句自述绑定 `3596e98b0042c34acdf03ea90be2e8886d6f57f3` == 送审时 HEAD。

**按合并门（协议 §1）+ D-15：BLOCKER = 0、HIGH = 0 ⇒ 该轮通过。**

两条 LOW **又**是「我新写的说明比事实强」，已逐条复核并改到如实（详见末位 docstring commit）：

| # | Codex 指出 | 我的独立复核 | 处置 |
|---|---|---|---|
| LOW-1 | 新门与 `_resolve_path` docstring 把旧行为写成「**任何**不在 vault 根目录的笔记…目录信息全部丢失 / 正文**恒空**」——不成立。对照输入：重名时键已是 `sub/note`，旧兜底 `f"{key}.md"` 恰好等于真实路径。同文件 `:203` 残留的「两者同域」也未同步收窄 | 属实。兜底是否等于真实路径**取决于键形态**，我把「无重名」这一种情形说成了全部 | 三处逐一收窄；并注明图节点还含未解析 wikilink 目标、`_resolve_path` 不校验入参来源 |
| LOW-2 | `_classify_gather_result` 的可达性说明**方法名写错**：超时入口是 `start_batch_session`，不是 `execute_batch`；「本仓唯一的取消源」超出已核范围 | 属实。`grep asyncio.wait_for` → `:370`，而 `async def execute_batch` 在本文件**不存在** | 改为 `start_batch_session:370`；「本仓唯一」收窄为「本文件内已知的取消路径」并注明未穷举文件外调用方 |

**Codex r2 对新增 9 条门的判别力评估（如实转录，已并入 §六「本卡未证明什么」）**：

| 门 | 能抓住 | Codex 指出仍未覆盖 |
|---|---|---|
| gather AST 门 | `BaseException → Exception` | **负控输入**：内存中对调两个分支体，门仍通过；不验证分支动作或真正所属循环 |
| attach RHS 门 | `generate_hint = skip_question` | **负控输入**：删顶层挂载调用、删副作用 import、或赋值前加 `return`，**四条 exam 门仍全部通过** |
| TYPE_CHECKING 非 def 门 | 块内新增变量注解等 | 新增未挂载的模块级 helper 仍通过（这本身合理，ext 原就有未挂载 helper） |
| resolver → 下游读取门 | 嵌套路径可交给真实读取器 | **门未覆盖的路径**：`get_neighbors → NeighborNote.path` 这段生产接线被绕过 |
| 无参模型解析门 | 生产形态的配置 import / 单例读取 | `_llm_classify_intent` 是否使用解析结果、凭据是否传递 |

**Codex r2 独立确认的事实**：六个纯格式文件 AST 全等；测试数 **15 → 24**；三个声明零改动的文件确实零 diff；
九文件保留 `pyright: ignore` **合计 3**；新增有效 `type: ignore` 只有测试里故意传旧 kwarg 那一处；
`manager._config = object()` 是对真实管理器做非法状态注入、**不是 mock 被测方法**，`finally` 恢复、串行 pytest 无持续污染；
`search()` / `get_health_status()` 的 PREV↔HEAD AST 一致，健康显示与搜索降级的矛盾属**既有行为**。

**Codex r2 明确不背书的部分（如实保留）**：未复跑 pytest 与 pyright，
故「24 passed / 0 errors, 80 warnings / 五段负控还原」**不作为本轮实测**；
`retry_single_node` 相邻注释里「没有任何写方 / hasattr 恒 False / 改前成功恒不可达」这三条更强主张本轮不背书。

### 末位：纯 docstring commit `5e8a76fd`（D-32，不计轮次）

按 D-32「审后只改注释 / docstring 的 commit 由主 session 逐行等价核并写明『判等价』，
不计入 D-15 轮次、不触发再审」。本卡按该条处置，并自带 AST 等价自证
（`d32-docstring-equivalence-*.txt`）：

```
backend/app/services/batch_orchestrator.py        剥 docstring 后 AST 相同 = True   (未剥时 False)
backend/app/services/wikilink_graph_service.py    剥 docstring 后 AST 相同 = True   (未剥时 False)
backend/tests/unit/test_pyright_tail_behavior.py  剥 docstring 后 AST 相同 = True   (未剥时 False)
ALL_STRIPPED_AST_IDENTICAL = True
```

「未剥时 = False」是**必须**的一半：它证明这次 commit 确实改了文案，不是一个空 commit。
该 commit 后行为门重跑 **24 passed**。⚠️ 请主 session 复核时逐行核该 commit 并在台账写明「判等价」。

## 五 DoD-3

### 4-A Claude 已代验（技术证据）

| 门 | 证据档 | 结论 |
|---|---|---|
| 结构 ignore 11 → 4（成对同命令） | `struct-before-20260918T192029.txt` / `struct-after-20260918T195759.txt` | ✓ |
| AST 口径符号判据 + 3 条验伪锚 | `struct-ast-after-20260918T200305.txt` | `FAILURES=0` |
| 行为门 红 → 绿 | `tail-red-replay-20260918T200104.txt` / `tail-green-r3-*.txt` | 9 红（15 条时）→ **24 passed**（补门后） |
| 负控三段各红在指定断言 | `negctl-1/2/3-*.txt` | ✓ shasum 前后逐字同、porcelain 0 |
| pyright 两次 0 errors | `pyright-before-*.txt` / `pyright-after-*.txt` | `0 errors, 80 warnings` ×2 |
| TYPE_CHECKING AST 一致性 | `typecheck-ast-20260918T194246.txt` / `typecheck-ast-after-*.txt` | `declared 11 mismatch []` ×2 |
| 既有 19 文件 + regression + api 目录级 | `suite-open/close(-r3)`、`regression-open/close-final`、`api-open/close(-r3)` | 19 文件 3 failed（既有，+1 已知 flaky）；regression `1913 passed` 两次一致；api `269 passed` 两次一致 |
| `tests/unit` 目录级 nodeid diff | `base.nodeids` / `close-final.nodeids` | 唯一差异 = `< test_candidate_service::test_accept_candidate_already_accepted_returns_422`（批次基线头注明的已知 flaky）；`comm -13` 为空 |
| 地盘门 + 禁改面 | `territory-*.txt` | 恰 7 文件、禁改面空 |
| 纯格式 commit 的 AST 等价 | commit `b8500c6e` body | 六文件 `ast_identical=True` |

### 4-B 用户体验（零技术词）

- 批量跑智能体时被中途取消的那一份，不再被当成「做完了」混进结果里。
- 单个重跑时如果我把智能体名字打错了，它当场就告诉我这个名字不存在，而不是跑一半默默失败。
- 系统挑分类模型时会真的按我设置面板里填的走，而不是不管我怎么填都用同一个写死的。
- **白板旁边那些相关笔记，现在能真正被读进来了。** 以前放在子文件夹里的笔记，系统找不到它的真实位置，
  于是那些笔记的正文和重点标注**从来没进过对话**——看起来一切正常，只是内容悄悄少了一块。
  现在它能对上真正的文件，那些笔记的内容第一次真的参与进来。
- 多模态搜索还是按关键字匹配（和以前一样），但它现在会老实说「没有接向量服务」，
  而不是报一个看不懂的英文错误名。

**felt-sense**：以前是「它没报错，所以大概没事」；现在是「它要么真做了，要么直接告诉我哪里不对」。
最后那条尤其明显——不是它变快了，是我终于知道**以前少了什么**。

## 六 本卡未证明什么（≥4；两轮 Codex + 一轮内部对抗复核后重写）

1. **两处 `isinstance(result, BaseException)` 的取消分支，未在真实并发路径上触发过。**
   新增的 AST 门锁住了「两个循环筛的是 `BaseException`」这件事本身，另有一条门证明
   「真 `gather(return_exceptions=True)` 确实会把 `CancelledError` 放进结果列表」，
   但两者之间的运行期接线（那两个循环真的执行了、真的没 append 原异常对象）仍无运行期门。
   Codex r2 也明确指出：AST 门「不验证分支动作或真正所属循环」——**把两个分支体在内存里对调，门仍通过**。
2. **该取消分支在生产中是否可达，未证明。** 本文件内 `start_batch_session` 的
   `asyncio.wait_for` 取消的是外层协程（那时 gather 直接重抛、不返回结果列表），
   文件内也无处持有子任务句柄 `.cancel()`（用户取消走 `_cancel_requested` 协作式布尔）。
   所以 `"cancelled"` 要被命中，需要**子任务自己**以 `CancelledError` 收尾。
   本卡**未穷举本文件之外的调用方**是否另有取消源。
3. **`KeyboardInterrupt` / `SystemExit` 的归类选择未经运行期验证。** 实测它们根本到不了这两个循环
   （`asyncio.run()` 边界即重抛）。自定义 `BaseException` 子类确实会进结果列表并被归成 `"failed"`；
   「是否应重新抛出」属错误处理策略，Codex r2 判「当前没有必须改为重抛的生产证据」，本卡未改。
4. **T-new-3 未证明配置生效后 LLM 真能调通。** 本卡零连网，只证模型串**解析**正确。
   ⚠️ 更重要的是：`litellm.acompletion` **只传 model 不传 api_key**，而面板配的 key 只活在
   `RuntimeModelConfigManager` 内存里 ⇒ 模型一旦切到环境变量里没有 key 的 provider，
   调用会抛 `AuthenticationError` 并被外层 `except Exception` 吞成「分类失败」。
   改 `acompletion` 调用不在本卡范围（卡文 ⛔），**已登记移交**。
5. **T-new-6 未证明端点 HTTP 语义未变。** 参数校验被放在依赖检查之前，确实改变了错误优先级
   ——无效 `agent_type` 与「依赖未注入」同时存在时，前者会遮住后者。
   Codex 两轮都明确：**404/422 的最终映射未核实**（端点文件不在允许读取面内）。
6. **`retry_single_node` 成功分支首次在生产可达，且它返回的 `file_path` 是推导出来的名字。**
   本卡把 `agent_type` 类型修对之前，裸字符串会让下游 `agent_type.value` 抛 AttributeError 被吞成
   `success=False` ⇒ 成功分支恒不可达。现在可达了，而 `AgentResult` 不含 `file_path` 字段、
   `call_agent` 也不落盘 ⇒ 响应里的路径**不保证对应真实文件**，agent 的回答被整个丢弃。
   重新设计成功语义超出本卡授权，本卡只加了一条 warning 让它不再静默。
   ⚠️ Codex r2 声明：「没有任何写方／hasattr 恒 False／改前成功恒不可达」这三条**它不背书**
   （仅凭允许读取的枚举与签名不足以完全证明）——本卡如实保留该边界。
7. **T-new-8 退役后向量搜索仍关闭**，未证明补实现可行（旧 `len(vector) == 768` 与
   `multimodal_store` 默认 1024 维、`embedder_factory.build_embedder(embedding_dim=1024)` 都对不上）。
   附带一条既有不一致（本卡未引入、未修）：`get_health_status` 的
   `vector_search_available = has_store and lancedb_connected` 与 `_generate_embedding` 完全解耦，
   本卡把后者固化成恒 None 后，该字段从「运行期才知道」变成**静态可证的假**。
8. **T-new-7 未接通**：`learning_context_service.py` 的「学习记忆第二数据源」仍零供数，
   `exam_quick` 出题输入不变。产品裁定前是 **SKIP**，不是隐含前提。
9. **AST 一致性门不证明运行期挂载成功。** Codex r2 给出的负控：删掉顶层 `attach_to_exam_service()`
   调用、删掉 `exam_service.py` 末尾的副作用 import、或在赋值前加 `return`，**四条 exam 门仍全部通过**。
   本卡新增的「挂载右侧必须是同名 def」只堵住了「挂错函数」，堵不住「根本没挂」。
10. **新增的端到端门仍未覆盖真正的生产接线。** Codex r2 指出：
    `get_neighbors → NeighborNote.path` 这一段被绕过了——门直接调 `_resolve_path` 再喂给下游读取器，
    没有走 `get_neighbors` 真路径。
11. **未跑 `pyright tests`**（沿用 U2 口径，只跑 `pyright app`）。
12. **`wikilink_graph_service.py` 的 `get_front_matter` 返回 `list[dict]` 与 `isinstance(fm, dict)` 的错配未修**
    （同文件相邻缺陷，只登记）。
13. **Codex 两轮都未复跑我的测试与 pyright**：r2 明确写「不将作者的『24 passed／0 errors／五段负控还原』当成本轮实测」。
    那些数字是本 session 自己跑的，证据在 evidence 档里，但**没有第二方复跑**。

## 七 台账待登记条目（≥4）

1. **七项修复 + 结构 `11 → 3` + 行为门 15 → 24**。代码 commit 链：
   `b8500c6e`（纯格式，AST 等价自证）→ `2617a930`（语义 + 新测试，Codex r1 绑定）
   → `b46a280f`（r1 四条 LOW + 内部对抗复核整改）→ `3596e98b`（端到端门 + 三处标注，Codex r2 绑定）
   → 末位纯 docstring commit（D-32 等价自证，不计轮次）。地盘恒 7 文件，禁改面恒空。
2. **⚠️ 卡文 §一(f) 的「合计 4」是算术错误**——它列了 3 条保留项却写 4；实测 `11 → 3`
   （`learning_context_service.py:205` / `intelligent_parallel_service.py:629` / `exam_service.py:559`）。
   `2617a930` 的 body 沿用了错数字，**未 amend**（会破坏 r1 审查绑定），更正在 `b46a280f` 的 body 与本验收单。
3. **⚠️ 卡文判据本身的三处问题**（建议回写卡文模板，否则下一张卡照抄照错）：
   ① 判据 4 的 `created_at=` 1→0 与实现规格 (c) 的 `_build_misconception(created_at: str)` **自相矛盾**；
   ② `get_litellm_config` / `agentic_rag.embedding` / `get_source_path` 三条用**全文件文本** grep，
   会被「解释改前是什么」的注释与 docstring 命中 ⇒ 结构门应走 **AST 口径**（剥注释 + 剥 docstring）；
   ③ (m) 的现网只读 grep 同理会被说明性注释里的端口字面量命中。
4. **T-new-7 产品裁定挂起**（`learning_context_service.py:205` 补 `query=`）——默认**不接通**，本卡零改动。
   用户裁「接通」后须另立卡，并覆盖 G4-5 读组对称。
5. **T-new-3 的 api_key 未传，移交**：`litellm.acompletion` 只传 model 不传 api_key，
   面板配的 key 只活在 `RuntimeModelConfigManager` 内存里 ⇒ 切到 env 无 key 的 provider 时
   必抛 `AuthenticationError` 并被吞成「分类失败」。改 acompletion 调用不在本卡范围（卡文 ⛔）。
6. **T-new-6 打通了一片没人走过的分支，移交**：`retry_single_node` 成功分支首次在生产可达，
   返回的 `file_path` 是推导名、无写方，agent 回答被丢弃。本卡只加 warning，未重新设计成功语义。
   端点 404/422 映射两轮 Codex 都未核实（端点不在允许读取面）。
7. **T-new-8 补实现移交第十六批**：`embedder_factory.build_embedder(embedding_dim=1024)` 接线 +
   旧 `len(vector) == 768` 断言对齐；**并带一条**：`get_health_status` 的
   `vector_search_available` 与 `_generate_embedding` 解耦，现已成静态可证的假，一并处置。
   另：`docs/stories/36.13.story.md` 把 `EMBEDDING_RETRY_DELAY` 登记为「✅ 常量」，退役后该登记失实。
8. **D-G WLGRAPH-KEY-NORM 撞 `wikilink_graph_service.py`**——本卡改了 `_resolve_path`，
   若 D-G 排入必须**串本车道之后**。本卡实测对该卡直接相关：
   `md_file_index` 键无重名时是裸文件名、重名时用去扩展名相对路径；
   **图节点是索引键的超集**（含未解析的 wikilink 目标与非 .md 目标）；
   `[[with%20space]]` 不会自动解码。
9. **`wikilink_graph_service.py` 的 `get_front_matter` 返回类型错配**（`list[dict]` vs `isinstance(fm, dict)`）新登记。
10. **T1 / T3 / T14 / T-new-9 / T-new-10 仍挂 census**，本卡未动。
11. **清单编号更正**：手册 §一.1 P8 第 2 条写「census **§六** 8 项」，实测 §六 是 T-new-9/T-new-10；
    本卡八项实来自 **§四**（T-new-1/2/3/5/6/7/8，共 7 项）+ **§九.4**；
    另 `batch_orchestrator.py` 的 ignore 是**三处**（:506/:569/:570）不是两处。
12. **`ruff format --check` 硬门 × 主干既有漂移（对后续卡有复用价值）**：`backend/app` 实测 **141** 文件
    would reformat（`line-length=120` 而代码按 88 列写）。第十五批凡改到这 141 个文件之一的卡都会撞上
    这道整文件判定的门。本卡处置 = **拆一个纯格式 commit + 逐文件 AST 等价自证**，
    让语义 commit 的审查面不含格式噪音，供后续卡复用，直到 D-40 主 session 整仓 format 落地。
13. **Codex 轮次与绑定**：
    - 0 字节一次（`You've hit your usage limit`，**不计配额**，已移出仓库）；配额随后恢复。
    - r1 绑 `2617a930` → BLOCKER 0 / HIGH 0 / MEDIUM 0 / **LOW 4**（全部是「说明比事实强」）。
    - r2 绑 `3596e98b` → BLOCKER 0 / HIGH 0 / MEDIUM 0 / **LOW 2**（同类：方法名写错 + 影响面过强）。
    - 末位为纯 docstring commit，按 **D-32** 做「剥 docstring 后 AST 逐字相同」自证，
      不计入 D-15 轮次、不触发再审；请主 session 复核时逐行核该 commit 并在台账写明「判等价」。
14. **内部对抗复核（非 Codex，另记）**：`Workflow` 96 agents / 8 维 find → 每条发现 3 视角对抗 verify
    → 完整性批评者。29 条发现 → 存活 15 / 被反驳 14。存档
    `evidence-pyright-tail-behavior/internal-adversarial-review-wf_59b05a99-45a.md`（含逐条三视角裁决全文）。
    ⚠️ 按协议 §1「不入库的复核不作依据」，本条以**存档**形态入库，且在验收单中与 Codex 轮次**分列**，
    不混记为 Codex 轮次。它的完整性批评者是本卡「邻居正文从恒空变成有内容」这一最大用户可见收益的**唯一发现者**。
