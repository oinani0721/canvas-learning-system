> 批次: BATCH-2026-09-18-第十五批 · 车道 P8 · 卡 CARD-EXC-HANDLER-WIRE-REDACT round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-EXC-HANDLER-WIRE-REDACT-r2.md)"`
> 审查绑定: `7d3bdc2b36a30d4ff00fb4d33bb9e2bf30c07895`（= 最终 HEAD，代码树自此零改动）
> 会话头自证（抄 .stderr，括注行号；stderr 本身不入库）:
> `(2) OpenAI Codex v0.153.3` / `(5) model: gpt-6-astra` / `(9) reasoning effort: ultra`

---

绑定 **`7d3bdc2b36a30d4ff00fb4d33bb9e2bf30c07895`**，本轮结论：**0 BLOCKER / 0 HIGH / 3 MEDIUM / 2 LOW**。其中两项 MEDIUM 是回归门缺口，不是当前源码已发生的泄漏。

已独立确认：round-1→round-2 只有一个提交，仅测试文件 **+106/-2**，生产代码零改动。全程未写文件、未连接数据库、未导入生产 app；验证采用源码检查和提取真实纯函数的内存执行，**未重跑 pytest、pyright 或 OpenAPI 再生**。

1. **MEDIUM：另一套异常族仍有原文直出 500 的路径，“既有套件要求如此”的理由不成立。**

   位置：[exception_handlers.py:464](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/core/exception_handlers.py:464)、[exception_handlers.py:78](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/core/exception_handlers.py:78)。

   **未被拦下的输入**：另一套 `CanvasException("SECRET", code=500, details={"path": "/srv/private"})`。只要它到达异常分派，`to_dict()` 就会把 message、details 原样送出；内存执行确认了该载荷。

   [test_middleware.py:47](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/test_middleware.py:47) 使用裸调用，约束的是默认 **True** 分支，不能证明生产 **False** 分支必须保持原文 500；保留注册也不必等于保留原文输出。

   “生产 raise 站点为 0”不在本轮允许读取面内，**未独立证实**。可以作为有条件延期的依据，不能据此认定该路径已封闭。

2. **MEDIUM：响应头携带异常原文的负控，现有门拦不住。**

   位置：[exception_handlers.py:381](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/core/exception_handlers.py:381)、[test_exception_handlers_wire.py:444](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/unit/test_exception_handlers_wire.py:444)。

   **负控输入**：仅把 core 500 的头改为：

   ```python
   headers={"X-Request-ID": str(exc)[:100]}
   ```

   两个 500 测例的哨兵会进入响应头，但状态、JSON、日志均不变，`resp.text` 检查仍通过。指定 U9C 用例也不走这条 core 路径。

   当前生产代码没有这样写；这是**门未覆盖的路径**。新增文件唯一的响应头断言只检查 CORS 键存在，无法证明完整响应零泄漏。

3. **MEDIUM：core 4xx 的 `details` 属性白名单没有被门锁住。**

   位置：[exception_handlers.py:307](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/core/exception_handlers.py:307)、[test_exception_handlers_wire.py:421](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/unit/test_exception_handlers_wire.py:421)。

   **负控输入**：将 `_core_exception_details()` 改为 `return vars(exc)`。现有六档用例不检查 `details`，按断言与路径推演仍全绿。

   **未被拦下的输入**：

   ```python
   exc = CanvasNotFoundException("public")
   exc.server_path = "/srv/private/secret"
   ```

   当前实现只导出 `canvas_name`；负控实现会额外导出 `server_path`。内存对照确认这一差异。该缺口不同于明确保留的 4xx 业务文案回显。

4. **LOW：动态类名仍是内容输出通道，且未受现有长度门约束。**

   位置：[main.py:809](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/main.py:809)、[review.py:1517](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/api/v1/endpoints/review.py:1517)。

   **负控输入**：`type("SECRET_/srv/private", (RuntimeError,), {})("普通消息")`。类名会进入 `error_type` 或 `reason`；超长类名同理。现门使用固定类名，未覆盖该输入。

   原 LOW-6 可以按理论边界延期；“生产无此形态”本轮未独立证明。

5. **LOW：U9C 测试说明仍残留相反的当前态描述。**

   位置：[test_u9c_startup_rejection_eval.py:338](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/regression/test_u9c_startup_rejection_eval.py:338)，另见 `:283–284、:315–317`。

   仍写着“生产当前没接它”“结论相反”，与新口径冲突。**未被拦下的输入**是把这些说明当作当前证据引用；行为门不会发现文档退化。运行期排他断言本身仍有效。

其余问题的核对结果：

- **原 MEDIUM-1：范围理由成立，安全性理由不能扩大。** [exception_handlers.py:394](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/core/exception_handlers.py:394) 仍输出 `str(exc)`，白名单也只限制属性名。对照输入 `ValidationError("SECRET /srv/private", field="/srv/private")` 会原样进入 message/details。可以明确排除整改，但不能保证这些值“全来自调用方”或“不含服务端路径”。

- **当前头部通道：未发现异常原文串入。** `X-Request-ID` 来自 `request.state.request_id`，其上游赋值不在读取面内；CORS 头来自允许的 Origin 或固定回退，当前代码没有从异常文本取值。

- **消费者语义确实改变。** 未被端点自行捕获的 core “不存在”异常由 500 变 404，原先按状态码分支的消费者会进入不同分支；响应体也改变。本轮未获准读取插件/前端调用点，因此不能认定消费者已兼容。

- **没有证据表明接线新增了默认 TestClient 再抛回归。** 所列 Starlette 源码显示，接线前后都有外层 `ServerErrorMiddleware`，改变的是它使用的 handler。普通路由异常仍先被 CORSException 接住；外层异常此前也会再抛。U9C 两例均显式使用 `False`。这不是全套测试无回归的实测结论。

- **两套同名类没有分派歧义。** 键是不同类对象，不是类名；当前两套继承链相互独立。`cast(...)` 确实放宽静态检查，但所见注册键与处理器参数相配，未发现借此掩盖实际错绑。

- **OpenAPI“只有时间戳一行”未获独立验证。** 本次 diff 没改路由签名、响应模型或声明，因此该说法与改动形态相容；但运行期新增 404 行为，并不等于相应 schema 声明已经完整。缺少生成结果及相关契约文件，不能认证没有遗漏。

- **U9C 排他判据保留。** [test_u9c_startup_rejection_eval.py:434](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/regression/test_u9c_startup_rejection_eval.py:434) 要求 `error_type == "VaultScopeUnresolved"`，handler-only 的 `:380` 要求该键缺席。移除中间件这一负控会变红。

- **round-2 三项整改成立。** 六档映射内存执行结果为 `404/404/400/404/500/500`；绑定身份断言和日志消息全文断言均存在。作者所述两段负控会被相应断言拦下。全文断言仍不能证明对应 `bug_id` 的记录及异常栈正确。另须区分：新增单文件不执行 generic 本体路径，但把 generic 文案改回 `str(exc)`，**既有 U9C 门会拦下**，不能报成组合套件仍全绿。
