> 批次: BATCH-2026-09-18-第十五批 · 车道 P8 · 卡 CARD-EXC-HANDLER-WIRE-REDACT round-5（末轮）
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-EXC-HANDLER-WIRE-REDACT-r5.md)"`
> 审查绑定: `6d8e4ee056c0538c81a4e028b866453f9bde7ac7`（= 最终 HEAD，代码树自此零改动）
> 会话头自证（抄 .stderr，括注行号；stderr 本身不入库）:
> `(2) OpenAI Codex v0.153.3` / `(5) model: gpt-6-astra` / `(9) reasoning effort: ultra`

---

**BLOCKER：0；HIGH：0。在限定读取面内，没有证据需要把此前 MEDIUM/LOW 升级。`6d8e4ee0` 的命中断言未发现新的正确性问题，也未见正常路径下自行偶发失败的机制。**

复核绑定 `6d8e4ee056c0538c81a4e028b866453f9bde7ac7`，所审文件与该提交一致。全程只读、未连接数据库；未启动应用或运行 pytest、pyright、OpenAPI 生成器。

已独立确认：

- 四段后续 diff 均只涉及 `backend/tests/unit/test_exception_handlers_wire.py`，生产代码零改动。
- `c2789bd2` 剥除全部 docstring 后，AST 完全相同。
- `6d8e4ee0` 仅新增 12 行调用记录与断言。
- 作者所述负控执行结果、W4 `blocked=0`、B15 目录级比较，本轮没有独立复跑。

**保留的问题如下。**

1. **MEDIUM：旧异常族 500 仍有条件性原文直出路径。**  
   位置：[exception_handlers.py:78](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/core/exception_handlers.py:78)、`:464`；[canvas_exceptions.py:68](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/exceptions/canvas_exceptions.py:68)。  
   **对照输入**：旧族 `CanvasException("secret-path", code=500, details={"path": "secret-path"})`。一旦该异常逸出路由，已注册处理器会原样输出 `message/details`。  
   保留注册是明确的范围决策，可以解释登记不改；但不能据此称路径不存在。“生产 raise 站点为 0”超出允许读取面，本轮未确认。没有已证生产触发链，维持 MEDIUM，不升 HIGH。

2. **MEDIUM：响应头泄漏的门未覆盖。**  
   位置：[test_exception_handlers_wire.py:245](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/unit/test_exception_handlers_wire.py:245)、`:502`。  
   **负控输入**：保持当前 JSON 体，在响应头增加 `X-Error: str(exc)`；现有正文断言和 CORS 头存在性断言仍可通过。  
   当前代码未发现该数据流：CORS 值来自允许列表匹配或固定 fallback；`X-Request-ID` 来自 `request.state.request_id`。后者的上游赋值不在读取面，不能声明全链已证明安全。这是覆盖缺口，不是已证当前头部泄漏。

3. **MEDIUM：core 4xx 的 `details` 白名单未被门锁住。**  
   位置：[exception_handlers.py:307](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/core/exception_handlers.py:307)、`:392`；测试 `:479–509`。  
   **负控输入**：把白名单改为 `exc.__dict__` 全量导出；现有门没有额外敏感属性样本，也不检查 `details`，仍可全绿。  
   当前实现确实只取 `canvas_name/node_id/field`，但**只限制键，不脱敏值**；`message` 同样保留原文。调用方输入回显符合本卡明确保留的 4xx 口径。若生产将内部秘密作为 `ValidationError` 的消息或 `field`，仍会输出；本轮没有取得这种生产输入证据，不升 HIGH。

4. **LOW：另外两支子类继承路径未覆盖。**  
   位置：[test_exception_handlers_wire.py:473](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/unit/test_exception_handlers_wire.py:473)。  
   **负控输入**：仅让 `NodeNotFoundException`、core `ValidationError` 按精确类型匹配，保留 Canvas 分支的 `isinstance`；六档门仍可绿，另外两支子类却落 500。当前实现三支统一使用 `isinstance`，静态抽取的纯函数核验也得到子类分别为 404、400。

5. **LOW：core 500 完整键集未锁。**  
   位置：[test_exception_handlers_wire.py:502](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/unit/test_exception_handlers_wire.py:502)。  
   **负控输入**：增加一个不含现有 marker 的 `debug_path` 字段，现有门仍可通过。当前 `exception_handlers.py:373` 的实际响应仍只有正确的三键，属于门未覆盖的路径。

6. **LOW：动态异常类名可以携带信息。**  
   位置：[main.py:809](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/main.py:809)、[review.py:1517](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/api/v1/endpoints/review.py:1517)。  
   **对照输入**：`type("SECRET", (RuntimeError,), {})("irrelevant")`，`SECRET` 会进入 `error_type` 或 `reason`；超长类名也不受当前消息长度门约束。需要代码动态构造这种类型，未见生产可达证据，维持 LOW。

7. **LOW：部分说明仍与现实现冲突。**  
   位置：[test_u9c_startup_rejection_eval.py:283](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/regression/test_u9c_startup_rejection_eval.py:283)、`:315`、`:338`；另有 `:255` 的旧中间件注释。  
   **对照输入**是当前接线，以及两条测试都断言泛化文案；旧描述仍称方向相反或生产未接线。新增测试 `:344–354` 也仍称“两次 DI override”，实际已是一项 override 加一项模块属性 patch。执行断言不受影响，可以登记移交。

**关于最终命中断言及两层覆盖：**

- [测试 :370–375、:408](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/unit/test_exception_handlers_wire.py:370) 的列表是用例局部变量，替身先同步 `append`，随后立即抛异常，中间没有 `await`；请求结束后才检查。没有随机值、等待时限或共享列表导致的可见偶发源。零次、重复调用或参数改变导致失败，是对路径变化的有效报警。
- 它仍能证明**注入的 core `CanvasNotFoundException` 在生产 app 上得到 404**：替换的是异常来源，生产 app、路由、中间件和处理器没有替换。它不能证明真实 CanvasService 或 MemoryService 初始化链正确。
- `__metadata__[0].dependency` 依赖当前结构，但 r5 已阻止相关静默假绿：首项没有 `dependency` 会直接报错；取到未被路由消费的键，调用记录为空，命中断言失败。它不是适应任意 `Annotated` 变形的取键方法。
- `:396–404` 的 `finally` 覆盖客户端进入、请求和退出异常，后置断言失败前已恢复 override；模块属性由 `monkeypatch` teardown 恢复。已有合法 callable override 能恢复。显式 `None` 与缺键会被混同，但 `None` 本来不是合法 callable override。

**其余问题的回答：**

| 问题 | 判断 |
|---|---|
| 500→404 是否改变消费者语义？ | **会。** 未被端点自行捕获的 core 异常，现在可能让“5xx 重试”进入“404 不存在”分支。具体插件/前端调用点不在读取面，不能确认实际回归，也不能宣称消费者完全无影响。 |
| 新接 `Exception` 是否引入 TestClient 再抛回归？ | 没有证据支持。给定 Starlette 源码显示 `ServerErrorMiddleware` 原本就存在；新增 handler 不创造再抛机制。路由普通异常仍先由 CORSException 接住；u9c handler-only 已明确使用 `raise_server_exceptions=False`。 |
| 两套同名类是否分派歧义？ | 没有。它们是不同类型对象，分别直接继承 `Exception`；同名不影响分派。人为跨族多重继承仍按明确 MRO 选择，当前未见此输入。 |
| OpenAPI 是否确实仅差时间戳？ | **未独立验证。** diff 没改参数、响应模型或装饰器声明，与该说法相容；但异常处理器通常不会自动补全路由的 404/500 schema。即使再生只差时间戳，也不能证明运行期响应已被完整描述。 |
| `cast` 是否掩盖真实类型错误？ | 注册键与处理器参数逐项匹配，未见真实错配。`cast` 不做运行期转换；不能仅凭 pyright 通过证明分派正确。本轮没有复跑 pyright。 |
| u9c 是否保留中间件排他判据？ | **保留。** `:380` 要求 handler-only 无 `error_type`，`:434` 要求中间件形态为 `"VaultScopeUnresolved"`。删除中间件、改由 generic 产出响应的负控会被拦住。 |
| generic 是否完全没有行为门？ | 新 wire 文件主要锁函数身份，但 u9c handler-only 已检查其泛化消息与原文缺席，不能把“新文件缺行为请求”说成“整卡没有覆盖”。 |

“协议允许 MEDIUM/LOW 登记不阻断”和“部分行段越界”作为**延期处置理由成立**，不能作为严重性判断依据。本轮维持等级，是因为没有发现足以支持升级的实际输入链与影响证据。

需要纠正作者最后一句的范围：**旧异常族确有现存条件性原文直出路径**；准确表述应是“未证明其当前生产可达”，而不是“全部都只是门缺口”。


