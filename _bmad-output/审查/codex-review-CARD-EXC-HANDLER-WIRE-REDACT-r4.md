> 批次: BATCH-2026-09-18-第十五批 · 车道 P8 · 卡 CARD-EXC-HANDLER-WIRE-REDACT round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-EXC-HANDLER-WIRE-REDACT-r4.md)"`
> 审查绑定: `9e034d6072eccc890afd29a5c38221a4dab83b64`
> 会话头自证（抄 .stderr，括注行号；stderr 本身不入库）:
> `(2) OpenAI Codex v0.153.3` / `(5) model: gpt-6-astra` / `(9) reasoning effort: ultra`

---

复核绑定 **`9e034d6072eccc890afd29a5c38221a4dab83b64`**。限定读取面内结论：**0 BLOCKER / 0 HIGH / 3 MEDIUM / 5 LOW**。没有发现此前问题应升级为 BLOCKER/HIGH 的证据，但 round-4 仍留下一个 DI 注入是否命中的 LOW。

全程只读、未连接数据库、未启动生产 app 或运行 pytest。完成了提交差异核对、源码审查及纯内存 AST／状态映射验证；下面的负控除特别注明外，是根据代码和断言推导，未实际修改文件运行。

已确认三段增量均只改 `backend/tests/unit/test_exception_handlers_wire.py`，生产代码零改动；提交数量分别为一、一、二。`c2789bd2` 去除 docstring 后 AST 相同。六档状态门、处理器身份断言和异常消息全文落盘断言均已加入。

**BLOCKER / HIGH：无。**

**MEDIUM**

1. **另一套异常族的 500 仍原文直出。**  
   位置：[exception_handlers.py:78](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/core/exception_handlers.py:78)、同文件 `:464`。  
   未被拦下的输入：旧族 `CanvasException("server-secret", code=500, details={"path": "/srv/private"})`。`to_dict()` 会把消息和路径送入响应，绕过两条已脱敏的 500 路径。

   **登记不改可以接受，但理由只部分成立。** 保持注册，并不要求保持 500 原文；可以不改注册而修改处理器。全仓“生产 `raise` 为 0”超出本轮允许读取面，不能作为已独立验证的事实。当前没有确认生产可达触发点，因此不升 HIGH。

2. **响应头泄漏未被门覆盖。**  
   位置：[test_exception_handlers_wire.py:245](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/unit/test_exception_handlers_wire.py:245)、`:490`。  
   负控输入：在 core 500 响应增加 `X-Debug-Error: str(exc)`；正文、状态码、`bug_id` 和落盘断言仍可通过。中间件用例对 CORS 头也只检查存在，不检查值。

   当前源码中，`X-Request-ID` 来自 `request.state.request_id`，CORS 头来自允许列表或固定回退值，**未发现直接从异常原文赋值的路径**。这是覆盖缺口，不是已证实的当前头部泄漏。登记不改成立，但不能据此宣称“整个响应零泄漏”。

3. **core 4xx `details` 白名单没有被门锁住。**  
   位置：[exception_handlers.py:307](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/core/exception_handlers.py:307)、[test_exception_handlers_wire.py:467](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/unit/test_exception_handlers_wire.py:467)。  
   当前白名单实现正确。负控输入：把 helper 改为 `vars(exc)`；现有六档没有额外属性，也不检查 `details`，仍可通过。之后给异常增加 `internal_path="/srv/private"`，该属性就会直出。

   登记不改可作为测试债接受，不能表述为“白名单已通过行为门验证”。

**LOW**

1. **round-4 没有证明指定 DI 替身确实被调用。**  
   位置：[test_exception_handlers_wire.py:379](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/unit/test_exception_handlers_wire.py:379)、`:386`、`:401`。  
   取键来自模块中的 `CanvasServiceDep` 别名，并未核对实际路由保存的依赖对象，也没有替身命中断言。

   门未覆盖的路径：**保留 memory 兜底，仅让 canvas 覆盖键失配**；若真服务仍对这个不存在的名字抛相同 core 异常，响应依旧是 404，断言无法区分来源。作者同时撤掉两层的负控，不能排除此路径。

   `__metadata__[0]` 换成普通标记时通常会显式 `AttributeError`；若第一项仍有 `.dependency`，但指向错误对象，或别名与已绑定路由发生漂移，则可能静默取错。

2. **另外两支已登记异常的继承行为未被门覆盖。**  
   位置：[test_exception_handlers_wire.py:461](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/unit/test_exception_handlers_wire.py:461)。  
   负控输入：仅把 Node／Validation 两支改为精确类型匹配，保留 Canvas 分支的 `isinstance`。纯内存验证中，现有六档结果不变，但 Node 子类和 Validation 子类由 404／400 错落 500。当前实现正确，登记不改成立。

3. **core 500 的完整键集未被门锁住。**  
   位置：[test_exception_handlers_wire.py:490](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/unit/test_exception_handlers_wire.py:490)。  
   负控输入：增加 `"details": {"server_path": __file__}`。它不含随机 `secret`，也不是 `error_type`，当前断言仍可通过。因此门不足以证明“与 generic 逐字同形”。当前实际响应只有预期三键，登记不改成立。

4. **动态类名可以通过 `error_type`／`reason` 输出。**  
   位置：[main.py:809](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/main.py:809)、[review.py:1517](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/api/v1/endpoints/review.py:1517)。  
   对照输入：`type("SECRET_PATH", (RuntimeError,), {})("ordinary")`。`SECRET_PATH` 会出现在响应里；超长类名也能突破当前样本验证的体积上限。未发现获准读取代码中存在这种生产来源，维持 LOW、登记不改合理。

5. **说明文字仍有残留矛盾。**  
   位置：[test_u9c_startup_rejection_eval.py:283](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/regression/test_u9c_startup_rejection_eval.py:283)、`:315`、`:338`；另见 `main.py:835`、`test_exception_handlers_wire.py:344`。  
   对照输入是维护者按这些文字判断当前行为：会得到“两个方向相反”“生产未接 handler”“两项 DI override”等过期结论。文件头补充已完成，但函数内部说明尚未全部同步。越界部分登记移交合理，不影响当前运行行为。

**对重点问题的判断：**

- **两层修法仍保留 core → 404 的窄命题。** 替换 MemoryService 没有替换生产 app、处理器或中间件；隔离无关初始化合理。但测试不能证明真实服务初始化链，也缺少“声明的替身确实命中”的证据，见 LOW-1。
- **异常路径下恢复成立。** `:394` 的 `finally` 覆盖请求及上下文进入／退出异常；模块属性由 pytest `monkeypatch` 清理。原 override 为合法 callable 时会恢复。`.get()` 无法区分缺失与原值 `None`，但 `None` 不是正常有效的依赖覆盖，不另计缺陷。
- **core 4xx 确实继续回显消息和白名单属性值。** “本卡不脱敏 4xx”作为明确范围成立；但“回显的一定只是调用方输入、不含服务端路径”不是构造器保证。`CoreValidationError("/srv/private", field="/srv/private")` 就会原样返回。
- **消费者语义确有变化。** 对逸出端点自身 `except` 的 core not-found，500 → 404 会改变仅按状态码重试、提示或分支的消费者行为。这是本卡有意改变的结果；未读取插件／前端调用点，不能认证全部兼容。
- **没有识别出由接线本身新增的 TestClient 再抛回归。** 最外层 `ServerErrorMiddleware` 原先就存在；逃到它的异常原先也有再抛行为。CORS 已接住的路由异常仍返回响应，core 异常则更早被处理。u9c 的 handler-only 用例已使用 `raise_server_exceptions=False`。这不等于全仓测试已验证通过。
- **两套同名类没有当前分派歧义。** 它们是不同类对象、互不继承；分派不依据类名。当前 `cast(...)` 的类键和处理器参数匹配，未发现掩盖错绑；但本轮未运行 pyright，不能认证“0 errors”的执行报告。
- **OpenAPI“再生仅差时间戳”未独立证实。** diff 没有改变路由声明或响应模型，因此该结果合理；异常处理器的运行行为变化通常不会自动补入 schema。未读取生成器及 schema、未执行再生，不能确认既有 schema 是否完整描述新增的 404 行为。
- **u9c 的产出方区分仍在。** handler-only 的 `:380` 要求没有 `error_type`；中间件用例的 `:434` 要求它等于 `VaultScopeUnresolved`。翻转没有删掉这组当前实现下的排他判据。

另一个覆盖边界：只运行新增单文件时，把 generic 的消息改回 `str(exc)` 不会被其身份断言拦住；但 **u9c `:377` 已锁定 generic 固定消息**，所以不能把它算成“本卡全部相关门仍全绿”的新增 MEDIUM。

“MEDIUM／LOW 登记不阻断”可以决定处置；“超出允许改动范围”可以决定移交。两者都不能消除问题或自动降低严重性。本轮证据支持维持这些等级。


