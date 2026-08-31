# 第三轮终裁

**BLOCKER 0 / HIGH 2 / MEDIUM 3 / LOW 4**

**结论：需再一轮，不可验收。**

冻结首门通过，主要测试数字和 M7/M8/M9 都能独立重放；但 HIGH-1 的移交仍不完整，完整验收命令还实际连接并触碰了本机运行时数据。此外，变异裁判仍有假杀，且存在核心语义真存活变异。

## 冻结清单

HEAD 实测为 `9cf0fb85ed839bb7035d023534fca222a24d6968`。

[冻结清单](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/CARD-G4-3-证据冻结清单.txt:5) 的 7 项实际 SHA-256 全部逐字匹配：

```text
01  0a42b86a267ce8c0997b0ef08fc78add377099c78bd578db52a60a8c9b656254
02  b3bfe71e3f85161f9ee588064dbadeefbd7ef97f9bc9f437a8398d5a321ca4f3
03  6a109e8e32832cca9996686332eb5b8650dae13d15fa6681276dc6aefeb8c6b7
04  c8c623315211a9d7bac486f6109de1ee671c91f1a88ac467d9577dcb03b51779
05  6a109e8e32832cca9996686332eb5b8650dae13d15fa6681276dc6aefeb8c6b7
06  a9cc651ca5dadd29e889d34cfdc1b034e355b083757d71f3a37ea8ac44e4fdae
py  b2a3f99b2781399db6b46f49c0c8c25efb74f3e4d39587e8a4c7d61d5772a8e3
```

因此冻结清单本身不触发 BLOCKER。

## HIGH

### HIGH-1：端到端 fail-open 的“收窄+移交”仍是 PARTIAL / FAIL

局部 helper 已闭合：[decision_tracker.py:138](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/core/decision_tracker.py:138) 的两层兜底实跑 7/7 passed；[验收单:310](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/CARD-G4-3-验收单.md:310) 和 [memory 测试:650](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/tests/api/v1/endpoints/test_memory_four_state_api.py:650) 也明确说端到端未闭合。这部分确认无问题。

但以下宣称不成立：

- [验收单:447](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/CARD-G4-3-验收单.md:447)：称“全部绕过点都在硬边界外（服务层）”。
- [验收单:791](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/CARD-G4-3-验收单.md:791)：称列出了“全部绕过点”。

独立真实入口反例至少包括：

| 遗漏点 | 注入与观测 |
|---|---|
| [rag.py:274](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/api/v1/endpoints/rag.py:274) 主 `try` 前 `logger.info` | patch 后 HTTP 500，`service.await_count == 0`。这是已修改文件内的第六点，不是 service 硬边界外 |
| [rag_service.py:194](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/services/rag_service.py:194)、`:289-290` 初始化日志 | 真实路由返回 500，服务已完成初始化 |
| [memory_service.py:748](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/services/memory_service.py:748) → [2753](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/services/memory_service.py:2753) | Neo4j 已成功调用一次，failed-score warning 失败仍把响应升为 500 |
| [nodes.py:1873](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/lib/agentic_rag/nodes.py:1873) | 真实 compiled LangGraph、真实路由下，debug sink 抛错得到 500 |
| [vault_scope.py:133](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/core/vault_scope.py:133) | 基线 200，debug sink 抛错后 500 |
| [neo4j_client.py:746](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/clients/neo4j_client.py:746) | 健康 `ok/timeline=1` 被日志异常改写成 `unavailable/timeline=0` |

作者原列的五组绕过点均复现实锤，但清单远非完整；`CARD-OBS-nothrow-logging` 只写“允许触及 service 层”，也覆盖不了 endpoint、DI、vault resolver、client、LangGraph/lib。

**建议修法：** HIGH-1 保持 PARTIAL；删除“全部/全在 service 层”，把移交范围扩展为 endpoint、依赖初始化、service recovery、vault/client、LangGraph nodes/retrievers。至少先修本卡已改 `rag.py:274-276`，或取得明确的范围豁免。

### HIGH-2：完整验收命令不是只读测试，验收单声明失实

[验收单:730](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/CARD-G4-3-验收单.md:730) 声称“全部进程内 mock，不连任何数据库、零数据库写”。按 [验收命令:595](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/CARD-G4-3-验收单.md:595) 实跑时实际出现：

```text
Neo4j driver initialized: bolt://localhost:7691
MemoryService: recovered 1 episodes from Neo4j
CREATE FULLTEXT INDEX episode_content IF NOT EXISTS ...
already exists ... has no effect
```

触发链为：

- [test_metadata_subject_mapping.py:54](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/tests/api/v1/endpoints/test_metadata_subject_mapping.py:54) 启动未隔离的 app lifespan；
- [main.py:159](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/main.py:159) 预热真实 MemoryService；
- [memory_service.py:287](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/services/memory_service.py:287) 执行真实 DDL。

本次 DDL 因索引已存在而没有 schema 效果，但审计实跑已触碰工作树内两个 ignored 运行时文件：

```text
backend/app/data/vault_index_pending.jsonl  新建，14,449 bytes
backend/data/bug_log.jsonl                  原文件被追加/改写
```

这是本次审计必须披露的只读违规。我没有删除 pending 文件，也没有在缺少前像的情况下回滚 `bug_log.jsonl`。此前误生的一枚 `evidence-g43/__pycache__/*.pyc` 已精确移除，并重新核过冻结 SHA。

**建议修法：** 禁用 live Neo4j/LanceDB lifespan，所有运行时路径指向 `tmp_path`，并在验收前后比较数据库及 ignored 文件副作用；隔离后重新生成完整证据。

## MEDIUM

### MEDIUM-1：`judge_kill` 仍能被无关失败骗过

[judge_kill:266](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/evidence-g43/mutation_gate_check_g43.py:266) 只检查收集非空、数量等于 75、存在任意 `FAILED`。

分支实测：

- collection 非零退出 → `None` → 非 kill：正确。
- 成功但解析到 0 → `_collected_count()` 返回 `None` → 非 kill：正确。
- 人工 `collected=0` 或 74 → 数量不等 → 非 kill：正确。
- `collected=75`、无 FAILED → 非 kill：正确。
- **仅改一条测试断言制造无关红灯，生产代码完全不变**：`1 failed / 74 passed / collected=75`，仍判 `✓ 被抓住`。
- 构造 `rc=0 + collected=75 + 任意 failed 字符串` 也返回 True。

另有 exact nodeid 被空格截断、只比数量不比集合、测试与 collection 两个 subprocess 的 TOCTOU、无 timeout 等脆弱点。

**建议修法：** 每个 mutant 登记预期失败 nodeid；要求 `rc==1`、exact collection 集合不变、执行总数为 75，并在恢复生产代码后重跑这些 nodeid 验证转绿。用 pytest hook/JUnit XML，不要解析字符串。

### MEDIUM-2：核心 `empty` 语义存在真存活变异

把 [decision_tracker.py:82](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/core/decision_tracker.py:82) 改为包含 `ServiceStatus.EMPTY.value`：

```text
py_compile=0
collected=75
75 passed
```

原因是 [memory 测试:332](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/tests/api/v1/endpoints/test_memory_four_state_api.py:332) 虽写“ok/empty”，实际只注入 `ok`；[RAG 测试:179](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/tests/api/v1/endpoints/test_rag_four_state_api.py:179) 也只测 `ok`。

**建议修法：** 两侧参数化 `ok/empty`，补 M10=加入 EMPTY；再补加入 OK、删 DEGRADED、删 UNAVAILABLE 的独立 mutant。

其它缺口中：

- `items` 协同改名：普通门已抓到 7 failed，但 M1–M9 没有该 mutant。
- `retrieval_status: Optional[ServiceStatus]` 改回 `Optional[str]`：普通门抓到 2 failed，但 mutation 集合没覆盖。
- 仍应补单端点 trace 删除、reason 删除/交换、function 标签错误等 mutant。

### MEDIUM-3：消费方证据仍自相矛盾

[证据 01:15](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/evidence-g43/01-review-suggestions-消费方证据.txt:15) 的 C 组明确有一条 schema docstring 命中，但 [结论:58](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/evidence-g43/01-review-suggestions-消费方证据.txt:58) 写“A/B/C 三组零命中”。

E 组 `:35-44` 实际为 10 条，表格 `:50-55` 也合计 10，却写成 9。原命令复跑仍为 10。

所有十条均已定性为非消费方，所以“活跃生产源码消费方为 0”没有被推翻；但 round-2 MEDIUM-3 没有完整闭合。

## LOW

1. [04 证据:84](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/evidence-g43/04-变异门验证-输出.txt:84) 的 M9 总数写 12，但只保存了后 7 个 nodeid；原因是 [脚本:258](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/evidence-g43/mutation_gate_check_g43.py:258) 使用 `tail[-8:]`。应输出完整 `r.failed`。

2. [验收单:471](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/CARD-G4-3-验收单.md:471) 的当前 `git status` 实数不是 14，而是 15。额外项是 0-byte `codex-review-CARD-G4-3-round3.md`；只有明确排除 reviewer 占位后才是 14。

3. 冻结清单只绑定 evidence 7 文件，没有绑定生产代码、测试、验收单及登记文档；它不能单独证明“代码—测试—证据—声明”为同一快照。本轮独立重跑补上了关键数字，但冻结设计仍不完整。

4. 文档/名称仍有陈旧语义：
   - [memory_schemas.py:563](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/app/models/memory_schemas.py:563) 仍称 `LearningMemoryClient` 走 Neo4j 直连，实际是本地 JSON；
   - [RAG 测试:370](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/backend/tests/api/v1/endpoints/test_rag_four_state_api.py:370) 函数名仍称 `keeps_none_quality_grade`，但 `:393-398` 已刻意允许多种值，名称/docstring 与门的实际语义不一致。

## 确认无问题

### M7/M8/M9 是真杀

在独立 `/tmp` 副本施加 [脚本:125-201](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v4-apistatus/_bmad-output/审查/evidence-g43/mutation_gate_check_g43.py:125) 的三项变异：

| 变异 | 语法 | collected | 实跑 |
|---|---:|---:|---:|
| M7 | 合法，完整 `if True` 且无悬空 `except` | 75 | 7 failed / 68 passed |
| M8 | 合法 | 75 | 3 failed / 72 passed |
| M9 | 合法 | 75 | 12 failed / 63 passed |

M7 的 7 个、M8 的 3 个与存档逐项一致；M9 总数 12 一致，但存档只列了 7 个。另制造真实 SyntaxError 后得到 `rc=4 / collected=None / failed=[] / judge=False`，旧语法错误假杀已修。

### 数字对账

| 宣称 | 独立结果 |
|---|---|
| 73 = 46 + 27 | 两个新测试文件分别 collect 46 / 27 |
| 裁判 75 passed | `75 passed / 148 deselected / 11 warnings` |
| 9 mutants、collected 75 | 九项均收集 75 |
| 先红 45 / 30 | HEAD 生产代码 × 定稿测试实跑一致 |
| 302 → 375 | HEAD / current collect-only 一致 |
| 243 → 316 | 完整实跑 `59 failed/243 passed` → `59 failed/316 passed` |
| AST 19 / 2 / 17 | 独立 AST 遍历一致 |
| evidence 6+1 | 6 个 txt + 1 个 py，一致 |
| 改动清单 14 | 严格当前状态为 15，不一致 |

`03` 与 `05` 各有 59 个唯一 FAILED nodeid，内容和 SHA 完全一致。

LOW-3 的 status/reason/call_count/双 patch 门、LOW-4 的“字段契约语义等价副本”改词均确认落实。

### 硬边界

以 `git rev-parse HEAD:<path>` 对比 `git hash-object <path>`，以下文件均与 HEAD 逐字节相同：

- `rag_service.py`、`memory_service.py`、`chat.py`、`agents.py`
- `lib/agentic_rag/nodes.py`
- `backend/openapi.json`
- `test_agents_dedup.py`
- `test_agents_encoding.py`
- `test_agents_learning_event.py`
- `test_fsrs_state_api.py`
- `test_metadata_subject_mapping.py`

最终终裁：**需再一轮**。至少要闭合两个 HIGH、修正 `judge_kill` 和 EMPTY 真存活门，并在完全隔离数据库和运行时文件后重新生成、完整冻结证据。


