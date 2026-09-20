> 批次: BATCH-2026-09-18-第十五批 · 车道 P8 · 卡 CARD-EXC-HANDLER-WIRE-REDACT round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-EXC-HANDLER-WIRE-REDACT.md)"`
> 审查绑定: `0707be325932974e979e07e042021f0be9712152`（= 送审时 HEAD）
> 会话头自证（抄 .stderr，括注行号；stderr 本身不入库）:
> `(4) OpenAI Codex v0.153.3` / `(7) model: gpt-6-astra` / `(11) reasoning effort: ultra`

---

三处主改动及生产接线在 `0707be325932974e979e07e042021f0be9712152` 上成立，但不能据此认定所有响应通道都已脱敏、行为门已覆盖完整。**未确认 BLOCKER / HIGH；发现以下 MEDIUM / LOW。**

本轮仅做只读源码核对和纯内存负控；未导入生产 app、未运行会落盘的 pytest、未连接数据库。以下“门仍可通过”是对指定测试的静态反事实分析。

1. **MEDIUM — core 4xx 仍可直接输出内部异常文本。**  
   位置：[exception_handlers.py:394](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/core/exception_handlers.py:394)、[exception_handlers.py:315](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/core/exception_handlers.py:315)。

   **未被拦下的输入**：`ValidationError("SERVER_SECRET_/private/deploy/vault", field="SERVER_SECRET_/private/deploy/vault")`。原类及 helper 的纯内存负控确认：状态为 400，`message`、`details.field` 均保留原文。属性白名单只约束键，不约束值。

   `CanvasNotFoundException`、`NodeNotFoundException` 同样回显参数。**回显调用方已知输入本身不等于泄密**；缺口是处理器无法区分公共输入与服务端诊断。限定读取面没有生产抛出点，因此不能断言某个真实端点已经泄漏。

2. **MEDIUM — 新接通的另一套 CanvasException 仍存在 500 原文直出路径。**  
   位置：[exception_handlers.py:78](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/core/exception_handlers.py:78)、[exception_handlers.py:464](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/core/exception_handlers.py:464)。

   **负控输入**：`app.exceptions.CanvasException(secret, code=500, details={"path": secret})`。其处理器直接返回 `to_dict()`，先于 CORS 异常中间件处理，因此 `message`、`details` 原文进入响应，绕过 generic 500 脱敏。

   这条注册及输出路径已证实；作者所谓“生产从不 raise 此族”在限定读取面内**无法独立确认**。新增门也没有该族输入。

3. **MEDIUM — core 500 脱敏及其余状态映射没有行为门覆盖。**  
   位置：[test_exception_handlers_wire.py:263](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/unit/test_exception_handlers_wire.py:263)、[exception_handlers.py:375](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/core/exception_handlers.py:375)。

   新门对 core 族只制造了 `CanvasNotFoundException`。以下**负控回退**均未被覆盖：

   - 将 core 500 的 `message` 改回 `str(exc)`。
   - 删除 `NodeNotFoundException → 404` 或 `ValidationError → 400` 映射。
   - 破坏已映射异常子类继承状态码的行为。

   对照输入应包含 core 基类、未登记子类、Node、Validation，以及已登记类型的子类。当前实现这些映射正确，但门没有锁住。

4. **MEDIUM — 生产 generic handler 只锁“键存在”，未锁绑定身份或实际行为。**  
   位置：[test_exception_handlers_wire.py:142](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/unit/test_exception_handlers_wire.py:142)。

   **负控回退**：生产接线后，把 `app.exception_handlers[Exception]` 错绑为 `canvas_exception_handler`。键仍存在；真实 app 的两条行为用例分别落 core 404、端点自捕获的 FSRS 200，均不到 generic handler。u9c 则另建 app，不能验证生产实例的绑定。

   **未被拦下的输入**是外三层中间件自身抛出的 `RuntimeError`：错误处理器读取不存在的 `exc.code`，再次失败。当前生产绑定正确，这是门的缺口。

5. **LOW — “日志全文保留”门实际只检查两个前缀片段。**  
   位置：[test_exception_handlers_wire.py:238](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/unit/test_exception_handlers_wire.py:238)、[main.py:791](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/main.py:791)。

   **负控回退**：把 `error=e` 改为 `error=RuntimeError(safe_message[:500])`。只要 marker、路径均在前 500 字符，现有断言仍通过，6000 字符尾部已经丢失；栈完整性也没有断言。

   当前代码确实传入原异常并使用 `exc_info=True`；但限定读取面不足以独立认证 `bug_log.jsonl` 保存全文及栈。

6. **LOW — 类型名不是无条件安全、定长的输出。**  
   位置：[main.py:809](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/main.py:809)、[review.py:1517](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/api/v1/endpoints/review.py:1517)。

   **负控输入**：`type(secret + "x"*6000, (RuntimeError,), {})("safe")`。秘密及长字符串将通过 `error_type` 或 `reason` 输出，固定 `RuntimeError` 样本无法覆盖。

   普通 `RuntimeError(secret)` 不存在这一问题；没有证据表明生产动态构造这类名称，因此这里只认定边界及测试覆盖限制，**不认定现实远程泄漏**。

其余问题的核对结果：

| 问题 | 结论 |
|---|---|
| **Q0：X-Request-ID、CORS 头** | 指定代码中没有异常原文到这些头的数据流。`X-Request-ID` 来自 `request.state.request_id`，其上游来源未获准读取；CORS 值来自请求 Origin、允许列表及固定值。见 [exception_handlers.py:347](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/core/exception_handlers.py:347)、[main.py:765](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/main.py:765)。现有门没有检查响应头是否包含秘密。 |
| **Q1：500 → 404 的消费者语义** | **确定改变 HTTP 行为。** 同一未被端点捕获的缺失异常，状态从 500 变 404，按状态决定重试或“资源不存在”提示的消费者会进入不同分支。具体插件是否受损，消费者代码不在允许读取面，不能认证兼容。 |
| **Q2：TestClient 重抛** | **未发现本卡新增此类回归的证据。** 指定 Starlette `applications.py:68` 表明外层 `ServerErrorMiddleware` 原本就存在；注册 `Exception` 改变其处理器，不是新增重抛机制。普通路由异常仍被 CORSException 接住；外层中间件异常原本也会逸出。u9c handler-only 用例已经显式使用 `raise_server_exceptions=False`。 |
| **Q3：两套同名异常** | **无现有分派歧义。** 两者是不同类对象，互不继承；注册键不按类名字符串匹配。 |
| **Q4：OpenAPI 只有时间戳变化** | **未独立证实。** diff 未改请求签名、响应模型或路由响应声明，因此生成结果不变有合理依据；但异常处理器映射不会自动变成 OpenAPI 响应声明。即便只差时间戳，也不能证明新增运行语义已完整记入 schema。生成器、schema 和其他路由声明不在读取面，无法确认具体漏项。 |
| **Q5：cast 是否掩盖实际错配** | [exception_handlers.py:464](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/core/exception_handlers.py:464) 的类与 handler 参数目前配对正确。`cast` 绕过了通用回调签名检查，但未发现实际类型错配；本轮没有重跑 pyright，不能独立背书“0 errors”。 |
| **Q6：u9c 排他判据** | **仍保留。** 中间件用例要求 [`error_type == "VaultScopeUnresolved"`](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/regression/test_u9c_startup_rejection_eval.py:434)，handler-only 用例要求[该键缺席](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/regression/test_u9c_startup_rejection_eval.py:380)。结合当前实现，仍能区分这两个产出方。 |

另需纠正作者自述：函数默认值实际是 **`True`**（[exception_handlers.py:407](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/core/exception_handlers.py:407)），生产在 [main.py:823](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/main.py:823) 显式传 `False`。这保留了既有裸调用套件的兼容性；不能把摘要中的默认 `False` 当作代码事实。
