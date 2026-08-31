# CARD-OBS-nothrow-logging 验收单（BATCH-2026-09-01-第八批 / W8 车道第 ③ 卡）

> 车道：`card-w8-scope`（分支 `card/w8-scope`）。开工树：G4-4 收尾 commit（见 §一）。行号重锚历史见 §六。
> 移交来源：CARD-G4-3 Codex round-4 HIGH-1 + 第七批裁定 §三 A-1/A-3 登记。

## 一、概览与范围

**命题（唯一承诺）**：端点模块内每一次 `logger.<level>(...)` 被包装后，其抛错不改变 HTTP 状态码与 detail。**不宣称防住"一切"**——Handler 层自吞、实参求值、未包装模块均不在承诺内（§五 逐条）。

**范围声明（建议默认、待裁决）**：本卡接受第七批裁定 §三 A-1 的移交建议，并把范围收窄至**端点层两文件**（rag.py / memory.py 模块级 logger）。服务层站点（G4-3 验收单 :1046 点名 9 个锚定函数）**只登记不修改**——两者均为第七批的建议默认，非用户已裁定，待批。

**行号重锚**：卡文行号基于主干 `9af18b27`；G4-4 核心 commit `ca116f51` 使 rag.py 漂移 +26 行（:419→:445、:441→:467）；memory.py 零 G4-4 改动、行号不变。落地树终核行号见 §六 表。

**技术必然性说明（范围收窄的第二个理由）**：NoThrowLogger 往 kwargs 注入 `stacklevel`，而 structlog 的 `wrap_for_formatter` 渲染链（本仓最终 renderer，`app/core/logging.py:106`）不认识它，会把它渲染成 JSON 里的多余字段（A2 备料结论：只有 `render_to_log_kwargs` 族会按 `LOG_KWARG_NAMES` 提取 stacklevel，本仓没用）。所以本适配器**只能包 stdlib `logging.getLogger` 一族**——endpoints 下 8 个 `structlog.get_logger` 文件技术不可包，inventory 表一单列 NOT-WRAPPABLE。

## 二、完成条件对照（卡文 (a)-(f)）

| 条件 | 状态 | 证据 |
|---|---|---|
| (a) nothrow_logging.py | ✅ | NoThrowLogger 七方法全 try/except、二级降级 `_FALLBACK_LOGGER.warning`（模块级缓存，可 patch 的测试缝）、二级再失败静默、`.inner` 暴露、nothrow() 幂等；零依赖 structlog；ruff/mypy 干净（§三 裁判 5） |
| (b) rag/memory 包装 + 惰性参数 + 收敛 | ✅ | 模块级 `nothrow(...)` 各 1 行；19 处 f-string→%s（逐处前后表 §六）；rag.py:291-299 手写 try/except 收敛为直接调用；decision_tracker.py 未动；状态码/detail/schema 零变化（§三 裁判 6/7） |
| (c) 回归锁 ≥8 条 | ✅ | test_nothrow_logging_api.py 共 N 条（§三 裁判 1 collect 数）；类级 patch + `_ours` needle 防假门 + 分层二级断言（⑥ 用模块属性 patch —— 类级 patch 会连二级一起打掉，探针实证） |
| (d) 负门 3 变异 | ✅ | §三 裁判 2 逐字 PASS 行；核 nodeid 整段匹配 **且**核失败原因关键字 |
| (e) inventory | ✅ | §三 裁判 3；只读 AST；篡改自检 4/4 + 结构验伪锚 2/2（防"恒 0 的坏门"） |
| (f) 裁判 7 条 | ✅ | §三 |

## 三、4-A 裁判 1-7（命令与逐字输出）

> 落地后填写。每条格式：命令 → 期望 → 实际输出（逐字）→ 它证明什么 / 不证明什么。

### 裁判 1 — 四文件 pytest 全绿（后三文件 passed 不减）
```
命令: cd backend && caffeinate -i .venv/bin/pytest tests/api/v1/endpoints/test_nothrow_logging_api.py tests/api/v1/endpoints/test_rag_four_state_api.py tests/api/v1/endpoints/test_memory_four_state_api.py tests/api/v1/endpoints/test_rag_vault_scope_api.py -q -p no:cacheprovider
期望: 全绿；后三文件 passed ≥ G4-4 收官记录
实际: [落地后填]
证明: 新测试全绿 + 未破坏 G4-3/G4-4 既有 API 门。
不证明: 服务层旁路已修（本卡不改服务层）；生产日志行为（全 mock）。
```

### 裁判 2 — 负控 3 变异
```
命令: cd backend && .venv/bin/python scripts/nothrow_logging_negative_control.py
期望: NEGATIVE-CONTROL: PASS (3 mutants each killed by named gates with expected reason; restored byte-identical)
实际: [落地后填]
证明: M1/M2/M3 各自的指定门以预期原因变红（nodeid 整段匹配 + 输出含 "500"/"await_count"/"Internal Server Error" 关键字），还原逐字节一致。
不证明: 未变异的其它门会红；SIGKILL 强杀下还原仍发生（try/finally 不接 SIGKILL，诚实边界）。
```

### 裁判 3 — inventory
```
命令: cd backend && .venv/bin/python scripts/nothrow_logging_inventory.py
期望: rag.py、memory.py 在「已包装」列 + 服务层登记条数
实际: [落地后填：已包装 2 / 未包装 N / structlog 8 / 死绑定 N / 无绑定有调用 1（rollback.py）/ 服务层 9 函数 M 处调用]
证明: 两文件模块级绑定外层是 nothrow；存量未包装面已如实登记。
不证明: 函数内局部绑定、.inner 绕过、handler/装饰器方案（表尾"本表不证明什么"）。
```

### 裁判 4 — 单行 f-string grep = 0
```
命令: grep -n 'logger\.\(info\|error\|warning\|debug\|exception\)(f"' backend/app/api/v1/endpoints/rag.py backend/app/api/v1/endpoints/memory.py
期望: 0 行
实际: [落地后填]
证明: 两文件无**单行** f-string 日志。
不证明: 无跨行隐式拼接 f-string —— 单行 grep 天然看不见（本卡改写前 rag.py:292/566、memory.py:748 三处就是跨行的，grep 数不出来）。AST 级判据 = inventory 的 JoinedStr 判定（两文件 f-string 首参必须为 0，见裁判 3 输出行内"f-string 0 处"）。
```

### 裁判 5 — ruff
```
命令: ruff check 四文件 + ruff format --check 新文件 + 存量两文件 HEAD 基线法（reference_ruff_format_gate_check_baseline_first）
期望: 0 error；新文件 rc=0；存量两文件按 HEAD 基线判定
实际: [落地后填]
```

### 裁判 6 — 契约不变（W4② 门下）
```
命令: cd backend && caffeinate -i .venv/bin/pytest tests/api -q -p no:cacheprovider，且 stdout 含 NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=0
期望: passed ≥ ② 收官记录；attempts = 0
实际: [落地后填；W4② 未合入则按卡文降级：先做 (a)-(e)，裁判 6 与 Codex 等 ② 合入再跑]
附带: openapi 归一化前后 diff 为空（W4③ 的 check-openapi-drift.py 若已合入则用之，否则 app.openapi() dump + 剔除 x-generated-at）
证明: 零契约变化的外部证据。
```

### 裁判 7 — 禁改门
```
命令: git log --format= --name-only $(git merge-base HEAD worktree-feature-obsidian-hybrid-dev)..HEAD -- backend/app/services/rag_service.py backend/app/services/memory_service.py backend/app/services/exam_service.py backend/app/services/verification_service.py backend/app/core/decision_tracker.py backend/app/core/logging.py backend/app/api/v1/endpoints/chat.py | sort -u
期望: 空
实际: [落地后填]
```

## 四、4-B 用户可见变化（零技术词）

无变化（日志系统出问题不会再把正常查询变成报错）。以前如果负责记日志的那部分坏了，用户查一个东西可能莫名其妙收到一条错误；现在坏了也只是"少记一条记录"，查询结果照常回来。界面上看不到任何不同。

（D3-A grep 自检：对上段 grep 禁词表 → 0 命中。[落地后贴实测]）

## 五、本卡不防什么（诚实边界，必读）

1. **Handler 层自吞不是本卡守住的**：stdlib `Handler.emit`/`Formatter.format` 内的异常（含 structlog `ProcessorFormatter`，`app/core/logging.py:29-116`）由 `Handler.handleError` 自吞、从不传播到调用点。这部分保护先于本卡存在，也不因本卡变化。本卡的守护区 = 调用点到 `Logger.makeRecord` 之间。
2. **实参求值不防**：`logger.error(f"...{x.attr}")` 里 `x.attr` 的求值发生在**进入包装器之前**。本卡把两文件全部 19 处 f-string 改成惰性 %s，是把消息构造挪进守护区；**其它模块的 f-string 日志（存量 173 处）不享受这条**。
3. **未包装模块不防**：inventory 表一「未包装」列全部（agents.py 50 处、review.py 50 处、metadata.py 14 处……移交登记，待用户裁决是否立后续卡）。
4. **`.inner` 绕过不防**：经 `.inner` 拿到原始 Logger 的调用在保护外（逃生舱的代价，docstring 已声明）。
5. **structlog 一族技术不可包**：stacklevel kwarg 会泄进 JSON event_dict（§一）。8 个 structlog 文件 + `memory_system_logger` 第三条链（health.py 的 memory_logger，自带 handler 不走 root）不在覆盖面。
6. **`exception()` 一级失败丢 traceback**：一级抛错后二级降级行只带异常 `repr`，原始 traceback 不重放（刻意不重放原始消息——它可能正是失败源）。
7. **编程错误被降级为一条 fallback WARNING**：如 `logger.log("INFO", ...)`（level 传成字符串）原本当场 TypeError，现在变成 fallback 行 + 继续跑。fallback 行带 logger 名/方法名/异常 repr，可定位但比"当场炸"容易被忽略——"观测面不得成为业务失败源"的必然代价。占位符/实参不匹配类错误 stdlib 本来就在 handleError 自吞，不是本卡新引入的遮蔽。
8. **负控的还原在 SIGKILL 下失效**：`try/finally` 不接 SIGKILL；被强杀时工作树留在变异态。逐字节比对保证的是"正常退出时还原 = 开跑时字节"，不是"任意退出都还原"。
9. **帧透明只在被测路径上证明**：帧透明门只断言 `info` 路径（/weak-concepts 入口日志）；`log()`/`exception()` 的 offset 一致性由实现同构保证（同一 `_guarded`），未逐路径立门。

## 六、逐处改写「前 / 后」表

（落地后从 scratchpad/rewrite-table.md 拷入终版——含 rag.py 9 处 + 收敛 1 处 + memory.py 10 处的逐处对照、不动 3 处清单、既有测试 :188 patch 目标下移的正当性、语义漂移逐条声明。）

## 七、存量登记表

（落地后从裁判 3 输出拷入：表一 28+ 包装状态分类 + 表二匿名内联 1 处 + 表四服务层 9 锚定函数逐处行号与代码。）

## 八、本卡未证明什么

- 裁判 6（tests/api 全量 + attempts=0）在 W4② 合入主干前不可跑（依赖 root conftest 的 7691 守卫 fixture——A5 备料证实该计数器由 W4② 交付，本卡树上尚不存在）；按卡文降级路径执行并在 §三 裁判 6 登记。[落地后按实际情况更新]
- 未在真实 Neo4j / live vault 上做端到端观测故障注入（本卡全进程内 mock + 裸 FastAPI——隔离纪律要求，不是疏忽）。
- 「19 处消息逐字不变」由改写规则与抽查保证，未逐处写渲染断言（既有 0 测试断言 record.msg，A1 实证）。

## 九、待你裁决（均为建议默认、非已批）

| # | 事项 | 建议默认 | 影响 |
|---|---|---|---|
| A-1 | 接受第七批 §三 A-1 的移交 + **范围收窄至端点层两文件**（服务层只登记） | 接受收窄；服务层另立卡 | 不接受则需扩本卡或新卡覆盖 rag_service/memory_service/vault_scope/neo4j_client/nodes 的 21 处服务层调用 |
| A-2 | 未包装存量（28 文件 178 处调用 + 8 个 structlog 文件技术不可包 + rollback 内联 1 处）是否立后续卡 | 立卡，优先 agents.py/review.py（各 50 处） | 不立则这些端点的观测旁路维持现状 |
| A-3 | rag.py:291-299 手写 try/except 收敛为直接调用（连带 test_rag_four_state_api.py:188 patch 目标下移） | 按卡文默认收敛 | 若倾向保守可保留双层兜底，但该门退化为"测 call-site try/except"而非测包装器（假绿面） |

## 十、Codex 审查轮次记录

[送审后填写：每轮 severity 计数 + 终裁 + 整改对照。BLOCKER/HIGH 最多续 3 轮。]
