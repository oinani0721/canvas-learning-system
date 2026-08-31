# CARD-OBS-nothrow-logging 验收单（BATCH-2026-09-01-第八批 / W8 车道第 ③ 卡）

> 车道：`card-w8-scope`（分支 `card/w8-scope`）。开工树：G4-4 收尾 commit（见 §一）。行号重锚历史见 §六。
> 移交来源：CARD-G4-3 Codex round-4 HIGH-1 + 第七批裁定 §三 A-1/A-3 登记。

## 一、概览与范围

**命题（唯一承诺）**：rag.py / memory.py 模块级 `logger.<level>(...)` 被包装后，其**方法调用期间**（含参数归一化）抛出的 `Exception` 不向调用方传播，因此不改变 HTTP 状态码与 detail。**不宣称防住"一切"**——Handler 层自吞、实参求值、未包装模块、BaseException（KeyboardInterrupt/SystemExit）均不在承诺内（§五 逐条）。

**范围声明（建议默认、待裁决）**：本卡接受第七批裁定 §三 A-1 的移交建议，并把范围收窄至**端点层两文件**（rag.py / memory.py 模块级 logger）。服务层站点（G4-3 验收单 :1046 点名 9 个锚定函数）**只登记不修改**——两者均为第七批的建议默认，非用户已裁定，待批。

**行号重锚**：卡文行号基于主干 `9af18b27`；G4-4 核心 commit `ca116f51` 使 rag.py 漂移 +26 行（:419→:445、:441→:467）；memory.py 零 G4-4 改动、行号不变。落地树终核行号见 §六 表。

**技术必然性说明（范围收窄的第二个理由）**：NoThrowLogger 往 kwargs 注入 `stacklevel`，而 structlog 的 `wrap_for_formatter` 渲染链（本仓最终 renderer，`app/core/logging.py:106`）不认识它，会把它渲染成 JSON 里的多余字段（A2 备料结论：只有 `render_to_log_kwargs` 族会按 `LOG_KWARG_NAMES` 提取 stacklevel，本仓没用）。所以本适配器**只能包 stdlib `logging.getLogger` 一族**——endpoints 下 8 个 `structlog.get_logger` 文件技术不可包，inventory 表一单列 NOT-WRAPPABLE。

## 二、完成条件对照（卡文 (a)-(f)）

| 条件 | 状态 | 证据 |
|---|---|---|
| (a) nothrow_logging.py | ✅ | NoThrowLogger 七方法全 try/except、二级降级 `_FALLBACK_LOGGER.warning`（模块级缓存，可 patch 的测试缝）、二级再失败静默、`.inner` 暴露、nothrow() 幂等；零依赖 structlog；ruff/mypy 干净（§三 裁判 5） |
| (b) rag/memory 包装 + 惰性参数 + 收敛 | ✅ | 模块级 `nothrow(...)` 各 1 行；19 处 f-string→%s（逐处前后表 §六）；rag.py:291-299 手写 try/except 收敛为直接调用；decision_tracker.py 未动；状态码/detail/schema 零变化（§三 裁判 6/7） |
| (c) 回归锁 ≥8 条 | ✅ | test_nothrow_logging_api.py **18 条**（13 基础门 + round-1 整改新增 5：stacklevel=None 防回归 / log() 帧透明 / 3 端点错误模板渲染门）；类级 patch + 调用方甄别 side_effect（httpx 请求日志实测误伤，§五 第 8 条）+ `_ours` needle 防假门 + 分层二级断言（⑥ 用模块属性 patch —— 类级 patch 会连二级一起打掉，探针实证） |
| (d) 负门 3 变异 | ✅ | §三 裁判 2 逐字 PASS 行；核 nodeid 整段匹配 **且**核失败原因关键字 |
| (e) inventory | ✅ | §三 裁判 3；只读 AST；篡改自检 4/4 + 结构验伪锚 2/2（防"恒 0 的坏门"） |
| (f) 裁判 7 条 | ✅ | §三 |

## 三、4-A 裁判 1-7（命令与逐字输出）

> 每条格式：命令 → 期望 → 实际输出（逐字）→ 它证明什么 / 不证明什么。以下全部为本卡落地后的实测记录（2026-09-01）。

### 裁判 1 — 四文件 pytest 全绿（后三文件 passed 不减）
```
命令: cd backend && caffeinate -i .venv/bin/pytest tests/api/v1/endpoints/test_nothrow_logging_api.py tests/api/v1/endpoints/test_rag_four_state_api.py tests/api/v1/endpoints/test_memory_four_state_api.py tests/api/v1/endpoints/test_rag_vault_scope_api.py -q -p no:cacheprovider
期望: 全绿；后三文件 passed ≥ G4-4 收官记录
实际: 逐轮记录——首验 107 passed (13+30+49+15)；round-1 整改后 115 (18+30+49+18)；round-2 整改后 **118 passed** (21+30+49+18)，2026-09-01 终态
分文件（终态）: nothrow 21 | rag_four_state 30 | memory 49 | rag_vault_scope 18
证明: 新门全绿 + G4-3/G4-4 既有门零回归（memory 49 改写前后两次实测一致；rag_four_state 断言零改动仅 patch 目标下移）。
不证明: 服务层旁路已修（本卡不改服务层）；生产日志行为（全进程内 mock）。第 4 文件 test_rag_vault_scope_api.py 已由 G4-4 收尾 commit（aaecf696）入树（round-2 复核确认），纯净 checkout 可重放。
```

### 裁判 2 — 负控 3 变异
```
命令: cd backend && .venv/bin/python scripts/nothrow_logging_negative_control.py
期望: NEGATIVE-CONTROL: PASS (3 mutants each killed by named gates with expected reason; restored byte-identical)
实际: rc=0，逐字末行 NEGATIVE-CONTROL: PASS (3 mutants each killed by named gates with expected reason; restored byte-identical)。round-1 整改后为**逐门单跑 + 逐门原因匹配**版，三门各自独立验证（M1: "500" ✓；M2: "500"/"Internal Server Error" ✓；M3 三门各含 "500" ✓），逐字节还原全过。
证明: 三道行为门在对应变异下以预期原因变红；还原逐字节一致（filecmp shallow=False）。
不证明: 未变异的其它门会红；SIGKILL 强杀下还原仍发生（try/finally 不接 SIGKILL，§五 第 7 条）。
```

### 裁判 3 — inventory
```
命令: cd backend && .venv/bin/python scripts/nothrow_logging_inventory.py
期望: rag.py、memory.py 在「已包装」列 + 服务层登记条数
实际: 【已包装】2 个 —— memory.py :58（12 处调用，f-string 0）/ rag.py :35（11 处调用，f-string 0）；未包装 26（agents 50/review 50/metadata 14/websocket 13/health 28+EXTERNAL 4…）；structlog NOT-WRAPPABLE 8；死绑定 3；无绑定有调用 1（rollback.py 内联）；服务层移交 21 处跨 9 锚定函数。自检 7+2 通过（篡改 4 + 假包装 2 + 根模块 1；结构锚 2）。round-1 整改后实跑：端点层 287 处调用 / f-string 163 处。
证明: 两文件模块级绑定外层是 nothrow（alias 来源已验证必须 app.core.nothrow_logging）且 f-string 首参 0；存量面如实登记。
不证明: 函数内局部绑定、.inner 绕过、handler/装饰器方案（表尾"本表不证明什么"；round-1 LOW-8 的两类新盲区已补识别与自检）。
```

### 裁判 4 — 单行 f-string grep = 0
```
命令: grep -n 'logger\.\(info\|error\|warning\|debug\|exception\)(f"' backend/app/api/v1/endpoints/rag.py backend/app/api/v1/endpoints/memory.py
期望: 0 行
实际: 0 命中（rc=1）
证明: 两文件无**单行** f-string 日志。
不证明: 无跨行隐式拼接 f-string —— 单行 grep 天然看不见（本卡改写前 rag.py:292/566、memory.py:748 三处就是跨行的，grep 数不出来）。AST 级判据 = inventory 的 JoinedStr 判定（两文件 f-string 首参必须为 0，见裁判 3 输出行内"f-string 0 处"）。
```

### 裁判 5 — ruff
```
命令: ruff check 四文件 + ruff format --check 新文件 + 存量两文件 HEAD 基线法（reference_ruff_format_gate_check_baseline_first）
期望: 0 error；新文件 rc=0；存量两文件按 HEAD 基线判定
实际: ruff check 六文件 All checks passed (rc=0)；format 新文件 4 个 rc=0；format 存量两文件 rc=1 —— HEAD 基线法（git show a3c41075:<p> | ruff format --check --stdin-filename <p>，同配置）同为 rc=1 → 存量漂移非本卡引入；format --diff 想改的行（memory :170 Query 参数、rag :570 pyyaml warning）与本卡 diff 零交集。
证明: 新文件零 lint/format 问题；存量两文件未新增格式漂移。
不证明: 存量两文件整体 format 合规（存量债，本卡不扩范围）。
```

### 裁判 6 — 契约不变（W4② 门下）
```
命令: cd backend && caffeinate -i .venv/bin/pytest tests/api -q -p no:cacheprovider，且 stdout 含 NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0
期望: passed ≥ ② 收官记录；attempts = 0
实际: 6a. openapi 归一化 diff = 空 ✓（before = 落地前 a3c41075 树全量 app.openapi()，after = 本卡落地后；sort_keys + 剔 x-generated-at；192 paths，含 G4-4 vault_id required）。Codex round-1 独立复算受影响 router 固定 blob 归一化 SHA-256 f62f4ee196a7dc69fd2a651fe3d1655242bb5f39fa5d6e40025574a1f1bc319e 双端一致（交叉证据）。
6b. tests/api 全量 + NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0：未跑（W4② 未合主干，主干 HEAD 928010b9；该计数器由 ② 交付，本树 grep=0）→ 按卡文降级路径待 ② 合入后主 session 补跑。隔离替代证据：裁判 1 四文件 + 新测试全为裸 FastAPI + 进程内 mock，无 lifespan；tests/api/ 无 conftest。
证明 (6a): 零契约变化的外部证据。
不证明 (6b 未跑): 全量回归与 7691 隔离（待 ②）；6a 是全量 schema 快照，不含 middleware/lifespan 运行时行为。
```

### 裁判 7 — 禁改门
```
命令: git log --format= --name-only $(git merge-base HEAD worktree-feature-obsidian-hybrid-dev)..HEAD -- backend/app/services/rag_service.py backend/app/services/memory_service.py backend/app/services/exam_service.py backend/app/services/verification_service.py backend/app/core/decision_tracker.py backend/app/core/logging.py backend/app/api/v1/endpoints/chat.py | sort -u
期望: 空
实际: 空（rc=0）。同分支 DEBT-8/G4-4 合法改动面（review_service/agents/rag/nodes/fsrs_manager）均不在禁改清单；49 的"log_decision 诚实化"改 review_service.py 调用侧，decision_tracker.py 本体未动。
证明: 本卡及同车道各卡均未触碰七个禁改文件。
不证明: 禁改清单之外的文件状态（那些由各自卡的验收单负责）。
```

## 四、4-B 用户可见变化（零技术词）

查询功能本身没有变化（本卡覆盖的两个模块里，负责记录的环节出问题时，不会再把正常的查询变成报错）。以前如果那部分坏了，查一个东西可能莫名其妙收到一条错误；现在坏了也只是"少记一条记录"，查询结果照常回来。界面上看不到任何不同。范围之外的其它环节（如检索服务内部）的同类问题不在本卡处理范围，已另行登记。

（D3-A grep 自检：对上段 grep 禁词表 → **0 命中**，2026-09-01 实测。）

## 五、本卡不防什么（诚实边界，必读）

1. **Handler 层自吞不是本卡守住的**：stdlib `Handler.emit`/`Formatter.format` 内的异常（含 structlog `ProcessorFormatter`，`app/core/logging.py:29-116`）由 `Handler.handleError` 自吞、从不传播到调用点。这部分保护先于本卡存在，也不因本卡变化。本卡的守护区 = 调用点到 `Logger.makeRecord` 之间。
2. **实参求值不防**：`logger.error(f"...{x.attr}")` 里 `x.attr` 的求值发生在**进入包装器之前**。本卡把两文件全部 19 处 f-string 改成惰性 %s，是把消息构造挪进守护区；**其它模块的 f-string 日志（存量 163 处，inventory 实跑数）不享受这条**。
   **渲染等价的边界（Codex round-1 MEDIUM-2）**：`f"{e}"` 走 `__format__`、`%s` 走 `__str__`——覆写 `__format__` 的异常类在 13 个异常插值点上渲染会不同。当前生产异常类型未覆写 `__format__`，渲染实际逐字等价；任意对象的严格等价需惰性适配对象调用 `format(value, "")`，本卡不做（复杂度不值），如实登记为已知边界。
3. **未包装模块不防**：inventory 表一「未包装」列全部（agents.py 50 处、review.py 50 处、metadata.py 14 处……移交登记，待用户裁决是否立后续卡）。
4. **`.inner` 绕过不防**：经 `.inner` 拿到原始 Logger 的调用在保护外（逃生舱的代价，docstring 已声明）。
5. **structlog 一族技术不可包**：stacklevel kwarg 会泄进 JSON event_dict（§一）。8 个 structlog 文件 + `memory_system_logger` 第三条链（health.py 的 memory_logger，自带 handler 不走 root）不在覆盖面。
6. **`exception()` 一级失败丢 traceback**：一级抛错后二级降级行只带异常 `repr`，原始 traceback 不重放（刻意不重放原始消息——它可能正是失败源）。
7. **编程错误被降级为一条 fallback WARNING**：如 `logger.log("INFO", ...)`（level 传成字符串）原本当场 TypeError，现在变成 fallback 行 + 继续跑。fallback 行带 logger 名/方法名/异常 repr，可定位但比"当场炸"容易被忽略——"观测面不得成为业务失败源"的必然代价。占位符/实参不匹配类错误 stdlib 本来就在 handleError 自吞，不是本卡新引入的遮蔽。
8. **负控的还原在 SIGKILL 下失效**：`try/finally` 不接 SIGKILL；被强杀时工作树留在变异态。逐字节比对保证的是"正常退出时还原 = 开跑时字节"，不是"任意退出都还原"。
9. **帧透明在被测路径上证明**：帧透明门断言 `info` 路径（/weak-concepts 入口日志）+ `log()` 路径（round-1 LOW-5 整改新增单测）；`exception()` 的 offset 一致性由实现同构保证（同一 `_guarded`），未单独立门。Logger **子类**覆写 `info()` 再调 super() 的场景会改变帧数——本适配器承诺限定于 plain `logging.Logger`（Codex round-1 LOW-5 讨论，如实声明）。

## 六、逐处改写「前 / 后」表

**改写规则**：① `f"...{v}..."` → `"...%s...", v`；② 一律 `%s` 不用 `%d`（`%d` 遇 None 在格式化阶段抛 TypeError → handleError 吞掉 → 日志彻底消失；`%s` 对 int 渲染逐字相同）；③ 消息渲染对当前生产异常类型逐字等价（`__format__` 边界见 §五 第 2 条）；④ `str(e)` 只从日志实参挪走，`detail=str(e)` 业务处原样。

### rag.py（9 处改写 + 1 处收敛 + 2 处不动；行号 = a3c41075）

| # | 行(新/旧) | 前 | 后 |
|---|---|---|---|
| R0 | 291-299 / 274-283 | G4-3 手写兜底 `try: logger.info(f"RAG query: …") except: pass`（跨行 f-string） | **收敛为直接调用** `logger.info("RAG query: %s... subject=%s cross=%s", request.query[:50], request.subject_id, request.cross_subject)` |
| R1 | 408 / 382 | `logger.error(f"RAG service unavailable: {e}")`（query 503 分支） | `logger.error("RAG service unavailable: %s", e)` |
| R2 | 412 / 386 | `logger.error(f"RAG query failed: {e}")`（query 500 分支） | `logger.error("RAG query failed: %s", e)` |
| R3 | 445 / 419 | `logger.info(f"Getting weak concepts for: {canvas_file}")` ← **HIGH-1 主犯** | `logger.info("Getting weak concepts for: %s", canvas_file)` |
| R4 | 467 / 441 | `logger.error(f"RAG service unavailable: {e}")` ← **HIGH-1 第二处** | `logger.error("RAG service unavailable: %s", e)` |
| R5 | 523 / 497 | `logger.error(f"Failed to load RAG config: {e}")` | `logger.error("Failed to load RAG config: %s", e)` |
| R6 | 566-568 / 540-542 | `logger.info(f"[CONFIG] Updated {len(updates)} params, persisted to {config_path}")`（跨行） | `logger.info("[CONFIG] Updated %s params, persisted to %s", len(updates), config_path)` |
| R7 | 577 / 551 | `logger.info(f"[CONFIG] Updated {param}: {old_val} -> {value}")` | `logger.info("[CONFIG] Updated %s: %s -> %s", param, old_val, value)` |
| R8 | 586 / 560 | `logger.error(f"Failed to update RAG config: {e}")` | `logger.error("Failed to update RAG config: %s", e)` |

**不动**：:309（G4-4 新增 scope resolved，已惰性 + a3c41075 加的 call-site 兜底保留，§五 第 10 条）；:570（pyyaml warning 纯字面量）。**模块级** :35 = `nothrow(...)` + import。

### memory.py（10 处改写 + 2 处不动；行号不变）

| # | 行 | 前 | 后 |
|---|---|---|---|
| M1 | 138 | `logger.info(f"Created learning episode: {episode_id}")` | `logger.info("Created learning episode: %s", episode_id)` |
| M2 | 142 | `logger.error(f"Failed to create learning episode: {e}")` | `logger.error("Failed to create learning episode: %s", e)` |
| M3 | 268 | `logger.error(f"Failed to get learning history: {e}")` ← 主端点 1 | `logger.error("Failed to get learning history: %s", e)` |
| M4 | 347 | `logger.error(f"Failed to get concept history: {e}")` ← 主端点 2 | `logger.error("Failed to get concept history: %s", e)` |
| M5 | 460 | `logger.error(f"Failed to get review suggestions: {e}")` ← 主端点 3 | `logger.error("Failed to get review suggestions: %s", e)` |
| M6 | 497 | `logger.error(f"Failed to get memory health status: {e}")` | `logger.error("Failed to get memory health status: %s", e)` |
| M7 | 561 | `logger.error(f"Failed to process batch episodes: {e}")` | `logger.error("Failed to process batch episodes: %s", e)` |
| M8 | 748-751 | `logger.info(f"[Observer-Fallback] Extracted {extracted_count} items " f"for node {request.node_id} into group {resolved_group_id}")`（跨行拼接） | `logger.info("[Observer-Fallback] Extracted %s items for node %s into group %s", extracted_count, request.node_id, resolved_group_id)` |
| M9 | 762 | `logger.error(f"[Observer-Fallback] extract-conversation error: {e}")` | `logger.error("[Observer-Fallback] extract-conversation error: %s", e)` |
| M10 | 905 | `logger.error(f"[M3] archive-session error: {e}")` | `logger.error("[M3] archive-session error: %s", e)` |

**不动**：:624 / :872（已是惰性参数）。**模块级** :58 = `nothrow(...)` + import。

### 附属表：既有测试连带改动（1 处）

test_rag_four_state_api.py 入口日志注入用例（原 :188-200）：patch 目标 `"app.api.v1.endpoints.rag.logger.info"` → `"…rag.logger.inner.info"`，docstring 追加说明，**断言零改动**。理由：patch 包装器方法本身 = 绕过其内部保护，R0 收敛 call-site 兜底后注入必传播 → 门假红；下移后异常产生于守护区内由 `_guarded` 吞掉——门从"测 call-site try/except"（双层兜底假绿面）变成真正测 NoThrowLogger。passed 不减（30）。

## 七、存量登记表

完整输出可随时重跑 `backend/scripts/nothrow_logging_inventory.py`（只读）复现。要点（round-1 整改后实跑）：

- **已包装 2**：memory.py :58（12 处调用，f-string 0）、rag.py :35（11 处，f-string 0）——本卡覆盖面
- **未包装 26**（stdlib，如实登记不修改）：agents.py 50 处（f-string 47）、review.py 50（31）、metadata.py 14（11）、websocket.py 13（11）、health.py 28（11）+ EXTERNAL memory_logger 4 处、multimodal 9（9）、mastery_ws 8（5）、edges 8、tips 10（10）、exam_quick 5（5）、其余 ≤3 处若干
- **NOT-WRAPPABLE（structlog）8**：chat.py 17 处（V5 未合面禁改）、errors / index / kg_health / monitoring / review_overview / vault / wikilink
- **EXTERNAL**：health.py 函数内 import 的 memory_logger（独立 handler 链，4 处调用）
- **死绑定 3**：context / exam / skills（绑了 0 调用，零风险面）
- **匿名内联 1**：rollback.py:41（`logging.getLogger(__name__).warning(...)`，模块级包装罩不住）
- **根模块便捷调用**：inventory 已识别 `logging.<level>()` 形态（round-1 LOW-8 新增，当前 endpoints 计数见实跑输出）
- **服务层移交 21 处 / 9 锚定函数**（G4-3 验收单 :1046 点名，函数名锚定 + 当前树行号）：rag_service.initialize 3 / _get_fallback_result 1 / query 2；vault_scope.active_vault_aliases 1 / resolve_vault_scope 2；memory_service.get_learning_history 2 / get_concept_score_history 5；neo4j_client._handle_merge_learning 1；nodes.multi_query_rewrite_node 1

## 八、本卡未证明什么

- 裁判 6（tests/api 全量 + attempts=0）在 W4② 合入主干前不可跑（依赖 root conftest 的 7691 守卫 fixture——A5 备料证实该计数器由 W4② 交付，本卡树上尚不存在）；按卡文降级路径执行并在 §三 裁判 6 登记（已按此执行：6b 未跑、6a openapi diff 实测为空）。
- 未在真实 Neo4j / live vault 上做端到端观测故障注入（本卡全进程内 mock + 裸 FastAPI——隔离纪律要求，不是疏忽）。
- 「19 处消息渲染不变」精确边界：对当前生产异常类型（未覆写 `__format__`）逐字等价；任意对象严格等价需 `format(value, "")` 适配，不做（§五 第 2 条）。既有 0 测试断言 record.msg（勘探实证）；整改后新增 3 条端点错误模板渲染门（`record.msg` 惰性形态 + args 数量 + `getMessage()` 结果）。

## 九、待你裁决（均为建议默认、非已批）

| # | 事项 | 建议默认 | 影响 |
|---|---|---|---|
| A-1 | 接受第七批 §三 A-1 的移交 + **范围收窄至端点层两文件**（服务层只登记） | 接受收窄；服务层另立卡 | 不接受则需扩本卡或新卡覆盖 rag_service/memory_service/vault_scope/neo4j_client/nodes 的 21 处服务层调用 |
| A-2 | 未包装存量（28 文件 178 处调用 + 8 个 structlog 文件技术不可包 + rollback 内联 1 处）是否立后续卡 | 立卡，优先 agents.py/review.py（各 50 处） | 不立则这些端点的观测旁路维持现状 |
| A-3 | rag.py:291-299 手写 try/except 收敛为直接调用（连带 test_rag_four_state_api.py:188 patch 目标下移） | 按卡文默认收敛 | 若倾向保守可保留双层兜底，但该门退化为"测 call-site try/except"而非测包装器（假绿面） |

## 十、Codex 审查轮次记录

**第 0 次发出（作废，施工方事故）**：prompt 文件被误落到 `backend/_bmad-output/`，Codex `$(cat)` 读根路径得到空任务（回复"请告诉我具体任务"），stdout 166 字节即止。未进入审查，不计轮次，登记以备复核。

**Round 1（锚定 `78c9e6e7`）**：终裁 **FAIL — 0 BLOCKER / 2 HIGH / 3 MEDIUM / 5 LOW**。存档：`_bmad-output/审查/codex-review-CARD-OBS-nothrow-logging.md`。整改对照：

| # | 严重级 | Codex 发现 | 判定 | 整改 |
|---|---|---|---|---|
| 1 | HIGH | `stacklevel` 补偿在 try **外**，`stacklevel=None` 的 TypeError 直接传播击穿承诺；docstring 吞错范围声明与 stdlib 实况不符（handle/callHandlers 无 catch、RecursionError 重抛、BaseException 不接） | **成立，全盘接受** | 补偿移入 try；docstring 按"包装器新增吞掉 / stdlib 本来自吞 / 不接的 BaseException"三层重写；新增回归锁 `test_stacklevel_none_does_not_propagate` |
| 9 | HIGH | commit `78c9e6e7` 里的验收单是**骨架版**（4-A 全是"落地后填"）却把 (a)-(f) 标 ✅；多处全称措辞（"每一次""逐字不变"）被其反例推翻；裁判 5/6/7 缺"证明/不证明"；f-string 存量 173 应为 163 | **成立，全盘接受** | 根因 = 终版写完后未重新 add（commit 带的是骨架）；本终版即整改后的完整版，全称措辞全部收窄（见 §一/§五/§六/§八），173→163（inventory 实跑数）；整改随本 commit 提交后再送 round 2 |
| 2 | MEDIUM | `f"{e}"` 用 `__format__`、`%s` 用 `__str__` —— 覆写 `__format__` 的异常类 13 个插值点渲染会不同 | **成立（影响面收窄）** | 当前生产异常未覆写 `__format__`，渲染实际等价；不改代码（惰性适配对象复杂度不值），§六 措辞收窄 + §五 登记边界 |
| 4 | MEDIUM | `_ours` 只证明"调用发生"，不证明"渲染成功"——错误参数让 getMessage 在 Handler 内静默炸时门假绿 | **成立** | 新增 `test_error_templates_render_completely`（3 端点参数化）：正常错误路径下断言 `record.msg` 是惰性模板、args 数量、`getMessage()` 渲染结果 |
| 6 | MEDIUM | `test_rag_vault_scope_api.py` 在本卡 commit 里不存在（G4-4 的 untracked 文件），纯净 checkout 无法重放四文件裁判 | **成立（G4-4 交付物归属）** | 该文件是 G4-4 session 的交付物（其收尾 commit 待发）。登记：主 session 复核须在 G4-4 收尾 commit 后重放裁判 1；本卡整改后实测 115 passed（18+30+49+18） |
| 3 | LOW | fallback 诊断门 join 后分别搜三项，三条残缺日志可拼接假绿 | **成立** | 断言改为**单条** rendered line 同时含 logger 名 + 方法名 + 原始异常 |
| 5 | LOW | 帧透明门只锁 info 路径；Logger 子类覆写 info 的场景 offset 会漂 | **部分成立** | 新增 `test_frame_transparent_for_log_level_path`（log() 路径）；exception() 路径同构性由实现保证、子类覆写场景 §五 第 9 条如实声明不承诺 |
| 7 | LOW | 负控原因验证对整份输出一次 any()，M3 多门时别的门"别的失败"可搭车 | **成立** | 负控改造为**逐门单跑 + 逐门原因匹配**（M3 三门各自独立验证）；整改后重跑 PASS（rc=0） |
| 8 | LOW | inventory 漏 `logging.error()` 根模块便捷调用；名字叫 nothrow 的本地假包装可骗过判定 | **成立** | 新增 `<root-logging>` 接收者识别 + `_local_nothrow_shadows`（SUSPECT 标注）+ alias 来源必须 `app.core.nothrow_logging` + 自检扩至 7 条（篡改 4 + 假包装 2 + 根模块 1）；实现期自检还抓出本分支初版条件写错对象层级（`func.value` 是 Name 不是 Attribute）——自检价值的现场证明 |
| 10 | LOW | openapi 证据未落档 | **成立** | 本卡实测：before/after 全量 `app.openapi()` 归一化（sort_keys + 剔 x-generated-at）diff **空**；Codex 独立复算受影响 router 固定 blob 归一化 SHA-256 `f62f4ee196a7dc69fd2a651fe3d1655242bb5f39fa5d6e40025574a1f1bc319e`（双端一致）登记为交叉证据 |

**Round 2**（锚定 `6b995031`）：终裁 **`BLOCKER/HIGH 清零：是`** —— round-1 两个 HIGH 均确认消除。存档：`_bmad-output/审查/codex-review-CARD-OBS-nothrow-logging-round2.md`。按卡文纪律（BLOCKER/HIGH 续轮、MEDIUM/LOW 登记结案）：

| # | 严重级 | round-2 发现 | 处置 |
|---|---|---|---|
| 1 | MEDIUM | docstring"RecursionError 包装器看不见"表述**错误**（重抛后仍在 `_guarded` 调用窗口内会被接住）；`wrapped.log()` 缺 level 的绑定错发生在守护区前 | **已修**（本 commit）：守护区定义改写为"进入 `_guarded` 后至 inner 返回前"；log() 绑定错明确划出承诺外；MemoryError/RecursionError 如实归入接住清单 |
| 4 | MEDIUM | `_ours` 渲染门缺 3 模板（/rag/query 503/500、concept-history） | **已修**（本 commit）：渲染门扩为 6 模板全覆盖 |
| 8 | MEDIUM | inventory 报告层：root_calls 未入 has_calls/总数；`evil.nothrow_logging` 尾段匹配假阳；本地重定义 nothrow 仍判已包装；`obs.nothrow` 模块别名漏判；health 锚未核实际调用 | **已修**（本 commit）：完整模块名严格匹配；模块别名收集 + `obs.nothrow` 识别（实现期自检当场抓出 Attribute 分支错用名字表后修正）；shadow 文件强制降级未包装；root_calls 纳入 has_calls/总数；health 锚强化 |
| 2 | MEDIUM | `__format__` 边界下"当前生产异常逐字等价"不能再无条件成立 | **措辞已收窄**（§五 第 2 条 round-1 已披露；再删"无条件"限定），维持现实现（惰性适配对象复杂度不值） |
| 9 | MEDIUM | 4-B"日志系统出问题也只是少记一条"超出两模块范围；107/115 混写；vault-scope untracked 表述过时 | **已修**（本 commit）：4-B 限定"本卡覆盖的两个模块"；终态 118 passed 统一；入树状态更新 |
| 3/5 | LOW | 诊断门泛化样本、exception() 帧门未参数化 | L-3 诊断门第二组样本与 exception 参数化登记为后续增强（现有门已证真实有效）；§五 第 9 条声明保留 |
| 6 | LOW | patch 下移仍锁同一回归，无需修复 | Codex 自判无需修复 |
| 7 | LOW | M3 memory 门原因词不鉴别（共用 "500"） | **已修**（本 commit）：`reason_by_gate` 按门配置，memory 门须含 "Internal Server Error"/"text/plain" |
| 10 | LOW | openapi 证据落档 | round-1 已落（§三 裁判 6），round-2 复算全量归一化 SHA-256 `982eda0e2351117d75b6bb5a5b2dfb81bab6f86d8b29985656c9c8a7484180f6` 双端一致，登记交叉证据 |

**终态复核（整改 commit 后）**：四文件 **118 passed**（21+30+49+18）/ 负控逐门 PASS rc=0 / ruff check+format 全绿 / inventory 自检 7+2 + 结构锚 2 全过。Codex round-2 已确认 BLOCKER/HIGH 清零；MEDIUM/LOW 按卡文纪律登记结案（上表）。

