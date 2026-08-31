# 对抗性审查请求：CARD-OBS-nothrow-logging（BATCH-2026-09-01-第八批 / W8 车道第 ③ 卡）

你是独立对抗性审查者。施工方已完成本卡全部工作，你的职责是**证伪**：默认立场是"这套实现/测试/文证有问题"，逐条找实证，找不到就明说找不到。禁止照抄施工方验收单的措辞当结论。

仓库根（worktree）：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w8-scope`（分支 `card/w8-scope`，只读，禁止任何写操作）。

## 本卡命题（唯一承诺）

端点层日志调用不得成为业务失败源。移交来源：CARD-G4-3 Codex round-4 HIGH-1（`_bmad-output/审查/codex-review-CARD-G4-3-round4.md`：patch rag.py `/weak-concepts` 入口 `logger.info` 抛错 → HTTP 500 且 service await_count=0；patch :441 `logger.error` 抛错 → 结构化 503 变裸 500）。

落地物：
- `backend/app/core/nothrow_logging.py`（NoThrowLogger 两级降级 + nothrow() 幂等包装）
- `backend/app/api/v1/endpoints/rag.py` / `memory.py`（模块级 nothrow 包装 + f-string 全改惰性 %s 参数 + rag.py 原手写 try/except 收敛为直接调用）
- `backend/tests/api/v1/endpoints/test_nothrow_logging_api.py`（注入式回归锁）
- `backend/scripts/nothrow_logging_negative_control.py`（负控 3 变异）
- `backend/scripts/nothrow_logging_inventory.py`（只读 AST 存量登记）
- `test_rag_four_state_api.py` 一处 patch 目标下移（`...rag.logger.info` → `...rag.logger.inner.info`，施工方声称是 call-site 收敛的直接后果）

## 必审清单（每条给 file:line 证据 + severity）

1. **吞编程错误**：NoThrowLogger 把日志调用的 TypeError/AttributeError 等编程错误也吞掉。施工方在模块 docstring 声明这是"已知代价"并辩称占位符不匹配类错误 stdlib 本来就在 handleError 自吞。核实：这个辩解对不对（读 CPython logging 源码或本仓 .venv 里的实现）？声明的边界和实际吞掉的范围是否一致？有没有**本该炸出来**的错误类别被 docstring 漏掉？
2. **惰性改写的语义**：抽验 rag.py / memory.py 全部 19 处 f-string→%s 改写（含 3 处跨行隐式拼接），逐处核对 `record.getMessage()` 渲染结果与改写前**逐字相同**（特别核对 `%d`→`%s` 的三处：memory.py :872 已有 `%d` 未动、新改写里有没有丢精度或丢参数）。施工方声称"消息文本逐字不变"——找出任何一处不成立的反例。
3. **⑥ 是不是测到假东西**：施工方自认"类级 patch `logging.Logger.warning` 会连二级降级 `_FALLBACK_LOGGER` 一起打掉"（称有探针实证），因此二级测试用 `patch.object(nothrow_logging, "_FALLBACK_LOGGER", ...)` 模块属性 patch。攻击这个分层：(a) 模块属性 patch 后，`_guarded` 的 except 块里读的是模块全局还是局部绑定？真的会被 patch 到吗（读 nothrow_logging.py 实码）？(b) 有没有测试仍然依赖类级 patch 证明二级路径？(c) `test_fallback_line_carries_diagnostic_context` 对 fallback 行内容的断言是否真的能抓"降级行不带诊断信息"的实现？
4. **spy 假门**：`_ours(spy, needle)` 靠首参子串匹配指认"我们那一行"。找反例：改写后哪条日志的首参是模板串（含 %s），needle 匹配的是**模板**而不是渲染文本——这会不会让某条 `_ours` 断言在"日志根本没发出"时假绿？逐条核 6 处 `_ours` 调用的 needle 与对应改写后模板串。
5. **帧透明门**：`_STACKLEVEL_OFFSET = 2` 与 `_guarded` 调用深度强耦合。核对：`log()` 方法经 `_guarded("log", level, ...)` 转调，帧数与 `info()` 一致吗？`exception()` 在 stdlib 里是 `error(msg, exc_info=True)` 的别名——包装层帧数一致吗？施工方的帧透明门只测了 `info` 一条路径——`log()`/`exception()` 的 offset 会不会不同（用 .venv/bin/python 实测或读 CPython 源码论证）？
6. **既有测试 :188 patch 目标下移**：核实改动后该测试仍锁同一回归（入口日志失败不破坏 /rag/query 响应），且 passed 总数不减。施工方声称这是 R0 收敛的直接后果——反驳它：有没有不改测试的替代方案（如保留 call-site try/except）而施工方没考虑？
7. **负控 M3 的配料完整性**：`nothrow_logging_negative_control.py` 的 `_M3_OLD` 配料必须与 nothrow_logging.py 的 `_guarded` 实体逐字一致。核对一致性与 count==1。M3 变异（删 except 变透明转发）下，施工方指定的三道门（①200 门/②503 门/④ detail 门）是不是**最先且必然**红的？有没有更早崩的（如 collect error / fixture error）让"指定门红了"的判定失真？
8. **inventory 验伪锚**：`nothrow_logging_inventory.py` 的自检（4 条合成语料）与结构锚（rollback.py 内联 / health.py EXTERNAL）是否足以防"判定恒 False 的坏门"？找出它仍会漏判的第三种形态（提示：函数内局部 `logger = logging.getLogger(...)` 绑定、`.inner` 绕过、装饰器方案——施工方在"本表不证明什么"里声明了哪几种？声明清单有没有漏？）。
9. **验收单诚实性**：读 `_bmad-output/审查/CARD-OBS-nothrow-logging-验收单.md`。(a) 有没有出现"全部/一切/所有绕过点"这类全称断言（G4-3 round-4 的 HIGH-1 教训就是验收单写"全部"）；(b)「本卡不防什么」是否覆盖：Handler 层自吞、实参求值、`.inner` 绕过、未包装模块、exception() 一级失败丢 traceback、SIGKILL 强杀时负控还原失效、health.py memory_logger 第三条链；(c) 「待你裁决」是否把第七批 §三 的**建议**写成了"用户已裁定"（本批纪律明令禁止）；(d) 每道门是否写了"它证明什么、不证明什么"。
10. **禁改面**：`git log --format= --name-only $(git merge-base HEAD worktree-feature-obsidian-hybrid-dev)..HEAD -- backend/app/services/rag_service.py backend/app/services/memory_service.py backend/app/services/exam_service.py backend/app/services/verification_service.py backend/app/core/decision_tracker.py backend/app/core/logging.py backend/app/api/v1/endpoints/chat.py | sort -u` 应为空。核对 HTTP 状态码/detail 文案/openapi schema 零变化（施工方声称有 openapi 前后归一化 diff 空的证据，抽验）。

## 输出格式

逐条：`[BLOCKER|HIGH|MEDIUM|LOW] <一句话标题>` + file:line 证据 + 具体反例场景（输入→错误结果）+ 建议修法。没有问题的条目明确写"未找到反例，理由：…"。最后一行给终裁：`BLOCKER/HIGH 清零：是|否`。
