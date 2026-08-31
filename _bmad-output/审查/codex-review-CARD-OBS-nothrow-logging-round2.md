终裁：Round 1 的两个 HIGH 已消除；本轮未找到 BLOCKER/HIGH，但仍有文证、测试门和 inventory 的中低风险残余。

### 1. [MEDIUM] 吞错边界仍写错，核心守护代码已修复

证据：[nothrow_logging.py:46](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/app/core/nothrow_logging.py:46) 称 `RecursionError` 重抛后包装器“看不见”，但真正的 `except Exception` 位于 [nothrow_logging.py:120](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/app/core/nothrow_logging.py:120)，会捕获它。CPython 的 `StreamHandler.emit` 确实在 [logging/__init__.py:1150](/opt/homebrew/Cellar/python@3.14/3.14.4_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/logging/__init__.py:1150) 重抛 `RecursionError`，但它随后仍处于 `_guarded` 调用内。

反例：stream `write()` 抛 `RecursionError` → 裸 Logger 传播；包装后返回并调用 fallback。`MemoryError`、自定义 Handler 的 `AttributeError` 也会被吞。占位符不匹配“stdlib 本来自吞”只对 `StreamHandler` 等自行调用 `handleError` 的实现成立；`Handler.handle` 和 `Logger.callHandlers` 没有统一 catch。

另有字面承诺缺口：`wrapped.log()` 缺 `level`、`wrapped.info(self=...)` 会在进入守护区前由 Python 参数绑定抛 `TypeError`。

建议：边界改成“进入 `_guarded` 后至 inner 返回前同步冒出的所有 `Exception`”；明确 `RecursionError`/`MemoryError`，并把承诺限定为签名合法的调用，或将 `log` 改成全 `*args/**kwargs` 转发。`stacklevel=None` 补偿已完整移入 try，本轮未再击穿。

### 2. [MEDIUM] 19 处参数无漏，但“逐字相同”仅对普通生产值成立

独立 AST 复算为 rag 9 处、memory 10 处：

- rag：`:307,429,433,466,488,544,587,600,609`
- memory：`:142,146,272,351,464,501,565,752,768,911`

代表性 `str/None/bool/int/普通异常` 重放为 `19/19` 相同，R0/R6/M8 数值改用 `%s` 没有精度或参数丢失；既有 [memory.py:878](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/app/api/v1/endpoints/memory.py:878) 仍是 3 个 `%s`、2 个 `%d`、5 个实参。三处单行 grep 看不见的是 R0/R6/M8；严格说只有 M8 是相邻 f-string 隐式拼接。

反例：

```text
Exception.__format__ -> FORMAT
Exception.__str__    -> STR
旧 f-string          -> RAG query failed: FORMAT
新 getMessage()      -> RAG query failed: STR
```

该反例覆盖 13 个异常插值点。验收单已在 `:106/:173` 披露，故整改诚实性成立；但裸 `except Exception` 可接到任意自定义异常，不能再无条件称“当前生产异常逐字等价”。

建议：若要严格保真，用惰性适配对象在 `__str__` 内执行 `format(value, "")`；否则维持当前实现并保持范围限定。

### 3. [LOW] 二级 patch 确实命中，诊断门仅缺泛化样本

[nothrow_logging.py:124](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/app/core/nothrow_logging.py:124) 在 except 中运行时读取模块全局 `_FALLBACK_LOGGER`，模块属性 patch 确实能命中；[test_nothrow_logging_api.py:384](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/tests/api/v1/endpoints/test_nothrow_logging_api.py:384) 没有再依赖类级 `Logger.warning` 证明二级路径。

`:410-417` 已要求同一 rendered line 同时包含 logger、method、异常，能抓“缺少诊断信息”的普通实现。

残余反例：实现若只硬编码本测试的 `rag/info/log sink dead` 整行，当前门仍绿，而 memory/error 的动态上下文可完全错误。

建议：参数化至少两组 logger/method/exception，并直接核对 fallback 的三个动态实参。

### 4. [MEDIUM] `_ours` 仍可在模板被调用但日志无法渲染时假绿

[_ours:205-215](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/tests/api/v1/endpoints/test_nothrow_logging_api.py:205) 的 4 个源码断言，经参数化实际覆盖 7 个调用场景、6 个 distinct needles。新增渲染门只覆盖其中 4 个；未覆盖：

- `/rag/query` 的 503 模板 `rag.py:429`
- `/rag/query` 的 500 模板 `rag.py:433`
- memory concept-history 模板 `memory.py:351`

反例：`logger.error("RAG query failed: %s", exc, "extra")` → `_ours=True`；但 `record.getMessage()` 抛 `TypeError: not all arguments converted`，标准 Handler 自吞且没有日志输出。完全删除调用时 `_ours` 会红；假绿发生在“模板调用存在、实参数量错误”的情况。

建议：补齐上述三条正常渲染门。

### 5. [LOW] plain Logger 的 info/log/exception 帧偏移未找到反例

证据：offset 为 2，三条路径都经过一个公开包装方法和 `_guarded`；CPython `findCaller` 会跳过 logging 自身的 `Logger.exception → Logger.error` 帧。实测：

```text
info      -> caller_info
log       -> caller_log
exception -> caller_exception, exc_info=True
```

新增 `log()` 门位于 [test_nothrow_logging_api.py:483](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/tests/api/v1/endpoints/test_nothrow_logging_api.py:483)。未单测 `exception()` 是覆盖缺口，不是当前实现错误。Logger 子类覆写方法会增加非 logging 帧并漂移；验收单 `:113` 已排除该范围。

建议：把 info/log/exception 做成同一个参数化帧门，并同步模块 docstring 的 plain Logger 限定。

### 6. [LOW] patch 目标下移仍锁同一回归，替代方案并未遗漏

[test_rag_four_state_api.py:197-217](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/tests/api/v1/endpoints/test_rag_four_state_api.py:197) patch `.inner.info` 后仍断言 HTTP 200 和 `query.await_count == 1`，确实把异常放在 `_guarded` 内，而不是绕过包装器。

独立重放四文件为 `115 passed`，分解 `18+30+49+18`；four-state 仍为 30。`c9d8c0f6` 已是 `HEAD^`，vault-scope 文件已由 `aaecf696` 入树。

保留 call-site `try/except` 并维持旧 patch 确实是替代方案，但验收单 `:181` 已明确考虑；不是施工方遗漏。无需代码修复。

### 7. [LOW] M3 配料和三门真实有效，但 memory 原因词不够鉴别

[_M3_OLD:62-75](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/scripts/nothrow_logging_negative_control.py:62) 与 `_guarded` 当前实体逐字一致，`count == 1`。

只读内存变异下，三门分别最先红于：

- 200 → 500，service 未执行；
- 503 → 500；
- 结构化 500 → `text/plain Internal Server Error`。

精确 `FAILED nodeid` 要求可排除 collect/fixture `ERROR`。

反例：M3 三门共用 `reason_keywords=["500"]`（`:109-114`）。memory 门本来就期望 500；若无关回归返回 503，它会先在 `assert status_code == 500` 失败，输出仍含“500”，脚本会误称原因匹配，detail 断言根本没执行。

建议：memory 门必须匹配 `text/plain` 和 `Internal Server Error`，各门分别配置原因。因只读纪律，我未执行会原地改文件的脚本；采用了等价的进程内透明转发变异。

### 8. [MEDIUM] inventory 自检通过，但报告层仍有假阳和漏报

[inventory.py:312-319](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/scripts/nothrow_logging_inventory.py:312) 能识别合成 `logging.error()`；但 [inventory.py:439-450](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/scripts/nothrow_logging_inventory.py:439) 的 `total_calls`、`has_calls` 都没纳入 `root_calls`：

```text
root_calls=1 / has_calls=False / total_increment=0 / bucket=nolog
```

另外：

- `:77` 的 `endswith(".nothrow_logging")` 会把 `evil.nothrow_logging` 判成真包装；
- 真 import 后本地重定义 `nothrow`，仍进入【已包装】，只额外打印 SUSPECT，与 `:87-89` 的“不判已包装”矛盾；
- `import app.core.nothrow_logging as obs; obs.nothrow(...)` 反被漏判；
- health 锚只核 imported name 数量，没有核真实 `external_calls`。

提示中的函数局部 logger、`.inner`、handler/装饰器三类已在 `:559-560` 全部声明。漏声明的是模块别名、方法别名及 root-call 从原语到报告的传播缺口。

建议：严格匹配完整模块来源；shadow 文件禁止进入 wrapped；追踪模块别名；将 `root_calls` 纳入总数、`has_calls` 和分类；health 锚核实际调用数。

### 9. [MEDIUM] 验收单主体完整，但用户可见段仍有全称越界

七项要求的边界均在 [验收单:104-113](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/_bmad-output/审查/CARD-OBS-nothrow-logging-验收单.md:104) 出现；“待裁决”在 `:10/:175-181` 明确写成建议、非已批；七道裁判各有“证明/不证明”。

但 [验收单:98](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/_bmad-output/审查/CARD-OBS-nothrow-logging-验收单.md:98) 声称“日志系统出问题也只是少记一条，查询结果照常”，超出两端点模块范围。

真实入口反例：`POST /rag/query`，`ainvoke=None` 的控制组为 `200/unavailable`；让未包装的 [rag_service.py:328](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope/backend/app/services/rag_service.py:328) `logger.warning` 抛错，同输入变成 HTTP 500，detail 为 `RAG query execution failed: service log dead`。

另有陈旧状态：`:35` 混写旧 107 与当前 115；`:38/:195` 仍称 vault-scope 文件 untracked、收尾 commit 待发，实际均已入树。Handler 边界在 `:104/:111` 仍继承第 1 项的错误表述。

建议：把 `:98` 限定为“rag.py/memory.py 已包装模块级调用”，并更新当前提交和 115 passed 记录。

### 10. [LOW] 禁改面与卡内 HTTP/OpenAPI 契约未找到反例

用户给定禁改命令独立运行 rc=0、输出为空。

从固定 Git 对象分别导入 `a3c41075` 与 `6b995031`：

- 全量 OpenAPI 都是 192 paths、503672 bytes；
- 归一化 SHA-256 同为 `982eda0e2351117d75b6bb5a5b2dfb81bab6f86d8b29985656c9c8a7484180f6`；
- 受影响两 router 的归一化 SHA 同为验收单所列 `f62f4ee1…319e`；
- CARD-OBS 前后 13 个 `HTTPException` 调用、13 个 route decorator 和 BaseModel 结构一致。

未找到本卡引入的状态码/detail/schema 变化。HEAD 中空白 `vault_id` 的 422 validator 属于并行 G4-4，不应把“零变化”扩写成整个分支行为零变化。

执行限制：未跑全量 `tests/api` 或 CI；Graphiti MCP 本轮未暴露，无法执行规定的 memory-facts 搜索。共享树审查期间出现外部并发改动；终态仍有非本卡的 `M backend/tests/unit/test_agentic_rag_vault_scope.py` 及既有审查产物，我未修改或清理。本结论全部锚定 `HEAD=6b995031`。

BLOCKER/HIGH 清零：是


