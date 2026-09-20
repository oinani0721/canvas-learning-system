> 批次: BATCH-2026-09-18-第十五批 · 车道 P8 · 卡 CARD-EXC-HANDLER-WIRE-REDACT round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-EXC-HANDLER-WIRE-REDACT-r3.md)"`
> 审查绑定: `8c4a66a8f247fb244031080f24464b764bd8163f`（= 最终代码 HEAD；此后只有一个纯 docstring commit，D-32 判等价）
> 会话头自证（抄 .stderr，括注行号；stderr 本身不入库）:
> `(2) OpenAI Codex v0.153.3` / `(5) model: gpt-6-astra` / `(9) reasoning effort: ultra`

---

绑定 **`8c4a66a8f247fb244031080f24464b764bd8163f`**：在指定读取面内，未发现可确认的 **BLOCKER / HIGH**。round-3 的依赖隔离修法成立；仍有 **3 项 MEDIUM、4 项 LOW**，主要是已登记残留与测试门未覆盖的路径。

两段提交链已独立确认：`0707be32→7d3bdc2b`、`7d3bdc2b→8c4a66a8` 各只有一个提交，均只改 `backend/tests/unit/test_exception_handlers_wire.py`，生产代码零改动。

本轮未修改文件、未导入生产 app、未运行 pytest／pyright／OpenAPI 导出，未连接数据库。执行验证仅限从获准源码抽出的纯函数和 `finally` 清理代码；下文其余负控结论来自源码推导。

**MEDIUM**

1. **另一套 `CanvasException` 的 500 仍能原文直出。**  
   位置：[exception_handlers.py:78](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/core/exception_handlers.py:78)、[注册处 :464](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/core/exception_handlers.py:464)。

   **未被拦下的输入**：路由或依赖抛出 `app.exceptions.CanvasException("secret /srv/private", code=500, details={"path": "/srv/private"})`。内层处理器直接返回 `to_dict()`，`message`、`details` 均未经脱敏。

   “卡文要求保留注册”可以支持范围豁免，但**保留注册不等于必须保留 500 原文**。“生产 raise 站点为 0”若成立，会降低当前可达性；本次读取范围不足以独立核实该数字。因此登记不改可以作为范围处置，不能作为已经封闭该通道的证明。

2. **响应头仍是脱敏门未覆盖的路径。**  
   位置：[exception_handlers.py:381](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/core/exception_handlers.py:381)、[test_exception_handlers_wire.py:466](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/unit/test_exception_handlers_wire.py:466)。

   **负控输入**：保持 JSON 不变，只把 core 500 的 `X-Request-ID` 改成 `str(exc)`。六档门仍无法拦住，因为零泄漏断言只检查 `resp.text`。中间件用例也只检查 CORS 头存在，没有检查头值是否含异常原文。

   当前代码没有显示异常文本流向 CORS 头：其值来自允许列表与固定 fallback。`X-Request-ID` 则原样来自 `request.state.request_id`，赋值源不在读取范围内。这里确认的是**测试缺口，不是已证实的当前生产头部泄漏**。登记“未证明”准确，但缺口仍在。

3. **core 4xx 的 `details` 白名单没有被六档门锁住。**  
   位置：[exception_handlers.py:307](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/core/exception_handlers.py:307)、[test_exception_handlers_wire.py:443](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/unit/test_exception_handlers_wire.py:443)。

   **负控输入**：把 `_core_exception_details()` 改为 `dict(exc.__dict__)`。现有用例既没有附加私密属性，也不比较 `details`，仍可全绿。

   **触发输入**：给 `CanvasNotFoundException("board")` 附加 `internal_path="/srv/private"`。当前白名单会排除它，负控实现会将它送入响应；纯函数验证确认了这个差别。登记不改成立，但“六档状态覆盖”不能扩展成“4xx 输出边界已覆盖”。

**LOW**

1. **动态类名仍可携带秘密，也能突破体积上界。**  
   位置：[main.py:809](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/main.py:809)、[review.py:1517](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/api/v1/endpoints/review.py:1517)。

   **对照输入**：抛出 `type("SECRET_/srv/private", (Exception,), {})("public")`，秘密进入 `error_type` 或 `reason`；超长类名也绕过固定 `RuntimeError` 样本证明的 `<512`。作为理论面登记不改合理；“生产无此形态”未在本次范围内独立证明。

2. **六档门只覆盖了一支已登记异常的子类。**  
   位置：[test_exception_handlers_wire.py:437](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/unit/test_exception_handlers_wire.py:437)。

   **负控输入**：仅对 `CanvasNotFoundException` 保留 `isinstance`，另外两类改为精确类型查表。内存验证结果：

   - 现有六档状态检查全部通过。
   - `NodeNotFoundException` 的子类从应有的 404 变成 500。
   - core `ValidationError` 的子类从应有的 400 变成 500。

   当前实现正确；缺的是另外两支继承映射的回归门。

3. **core 500 门没有完整锁住“逐字同形”和长消息诊断。**  
   位置：[test_exception_handlers_wire.py:466](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/unit/test_exception_handlers_wire.py:466)。

   **负控输入一**：在 core 500 体中增加不含随机哨兵的额外字段。测试没有比较完整键集合，仍可通过，因此尚未严格证明与 generic 的三键体同形。

   **负控输入二**：在 [exception_handlers.py:358](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/app/core/exception_handlers.py:358) 把传给记录器的异常换成 `CoreCanvasException(str(exc)[:200])`。两条 core 样本都很短，不能暴露长消息被截断的问题。中间件的 6000 字符测试走另一处记录调用，不能补上这条路径。

4. **过期描述仍在，round-3 也漏同步了文件头。**  
   位置：[u9c 测试 :255](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/regression/test_u9c_startup_rejection_eval.py:255)、`:283`、`:315`；[新增测试 :36](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/unit/test_exception_handlers_wire.py:36)。

   **对照输入**就是当前实现：两种栈都脱敏，但旧文案仍说方向相反、当前 main 注释错误。u9c 登记移交可以接受。

   新测试文件头另称替换实现“如实全列”“除这两处外”，却未列 canvas／memory 两个 DI 覆盖；局部用例文档已经列明。u9c 的行区间限制不能解释新增文件自己的这处遗漏。

**round-3 修法与其余问题的裁定**

| 问题 | 独立结论 |
|---|---|
| memory 哑对象是否掩盖本应测试的行为？ | **没有掩盖指定异常的分派命题。** async canvas 替身仍抛 core 异常，生产 handler／中间件没有被替换。但此用例不再证明真实 MemoryService 初始化链，也不能单凭它认证目录级 W4 已恢复。 |
| 保存／恢复是否覆盖异常路径？ | **成立。** [测试 :363–375](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/unit/test_exception_handlers_wire.py:363) 的 `finally` 覆盖上下文进入、请求、退出。抽取源码的内存验证确认：缺键和已有 callable 覆盖都能在异常后还原。`None` 与缺键混同，但 `None` 不是合法 DI override，不列实质缺陷。 |
| core 4xx 继续回显是否可登记不改？ | **符合明确范围。** `message=str(exc)`、白名单属性值均未做值级脱敏。不过 core `ValidationError` 接受自由消息，处理器本身不能保证这些值必然来自调用方、必然没有服务端路径。 |
| 500→404 是否改变消费者语义？ | **会。** 缺失 canvas 且异常逸出端点时，只按 `>=500` 重试的消费者现在进入 404 分支；Node 和 ValidationError 也分别改变为 404／400。这是实际契约变化。前端／插件不在读取范围内，不能认证具体调用点兼容。 |
| 接上 `Exception` 是否新引入 TestClient 再抛？ | **再抛机制原本就存在。** 旧栈已有最外层 `ServerErrorMiddleware`；外三层抛异常前后都可能再抛。普通路由异常前后均先由 CORSException 接住。指定片段未发现因此新坏掉的既有测试，但没有全套运行证明。 |
| 两套同名异常是否有分派歧义？ | **没有。** 它们是两个不同类对象，分别作为键注册；名称相同不会造成冲突。 |
| OpenAPI 再生是否确实只变时间戳？ | **未独立证实。** diff 未改路由签名、响应模型或声明式 `responses`，与该说法相容；但未读取／运行导出器和前后产物。handler 注册不会自动补齐所有路由的错误响应声明，schema 无差异也不能证明 500→404 没有契约影响。 |
| `cast` 是否掩盖真实类型错误？ | **本次配对未见。** 各异常键与对应窄参数 handler 一致，core 没有被送进读取 `.code/.to_dict()` 的旧 handler。`cast` 不提供运行保证，也不能据此认证作者的 pyright 结果。 |
| u9c 是否保留中间件产出的排他判据？ | **保留。** [u9c :434](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p8-backend/backend/tests/regression/test_u9c_startup_rejection_eval.py:434) 锁 `error_type=="VaultScopeUnresolved"`，handler 对照在 `:380` 锁其缺席。 |
| generic 只有身份断言是否仍漏测？ | **新增单文件确实漏其行为，但整个已给验收组并非如此。** 保持函数身份、把 generic 的 `message` 改回 `str(exc)`，新增单文件挡不住；既有 u9c handler-only 的 `:377–383` 会挡住，故不重复列为全组缺口。 |

作者的两段负控——删除 Node→404、恢复 core 500 的 `str(exc)`——都对应明确断言，整改方向有效；它们不足以排除上述其他门未覆盖的路径。
