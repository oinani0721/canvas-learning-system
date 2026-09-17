> 批次: BATCH-2026-09-11-第十四批 · 车道 T5-C (card-t5-bugs) · 卡 CARD-T-SWITCHVAULT round-5
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-T-SWITCHVAULT-r5.md)"`
> 审查绑定: `59e0d7661f94ece7f217a82fbb675ec3025c6b3c`（该轮送审时的 HEAD）
> 会话头自证（抄 .stderr，stderr 本身不入库 —— .gitignore:264 覆盖 `_bmad-output/审查/**/*.stderr*`）:
> - codex 版本行 = .stderr:2 `OpenAI Codex v0.153.3`
> - model 行 = .stderr:5 `model: gpt-6-astra`
> - reasoning 行 = .stderr:9 `reasoning effort: ultra`

---

审查绑定 `59e0d7661f94ece7f217a82fbb675ec3025c6b3c`。指定读取面已全部读完；未修改文件、未运行项目测试、未连接数据库或端口。

收尾时外部提交将 HEAD 推进至 `a557cb7e50e2fa8c5cb2e64cae022cdc3cdc20be`；新增内容全部位于 `_bmad-output`，代码差异为空，以下源码结论仍绑定送审版本。

**BLOCKER: 0**

**HIGH: 0**

**MEDIUM: 1**

- **M1：相同代码两次结果不同，不能推出“逻辑上排除代码引起”。**  
  位置：[验收单:160](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/_bmad-output/验收单/UAT-CARD-T-SWITCHVAULT-2026-09-16.md:160)，同类表述见 `:161`、`:166`、`:310–312`。  
  **显形条件：**代码存在竞态、后台任务或共享状态时，同一份代码本来就可能间歇失败。AST 等价只能排除**两轮之间的可执行语句差异**；`candidate` 零文本命中不能证明零关联，有限次单跑通过也不能证明“只在目录级发生”。

  但“既有偷连”的分类另有可靠支持：第十四批基线第 3 行确实标注该用例为 flaky；[卡前原始日志:597](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/_bmad-output/审查/evidence-b13-integ/unit-integ5-20260911T010612.txt:597)已经记录同一用例、同一 `7691` 地址及同型 W4 拦截。**分类有依据，当前因果论证仍须收窄。**处理 candidate 测试需另立卡。

**LOW: 2（其中一项为既有、需另立卡的问题）**

- **L1：五种样本全红，不能推出 mock 必须复制“逐字相同的 410 body”才能全绿。**  
  位置：[测试文件:62](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/unit/test_mcp_switch_vault_tool.py:62)，另见 `:119`。  
  **显形条件：**仅工具侧返回 HTTP 400、body 为 `{"detail": D[:200]}`，其中 `D` 是真实端点 detail，①四条断言仍成立；无需 HTTP 410 或完整相同 body。此为**源码推导，未执行变异**。另外，`:119` 的“任何不改变该响应的改动都不显形”也过强：已有负控 B 不改变端点响应，却让①的 success 断言变红。

- **L2／⑤：`check_backend_health` 的响应解析仍有条件性防御缺口，建议另立卡。**  
  位置：[infra_tools.py:47](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/mcp/tools/infra_tools.py:47)。  
  **显形条件：**响应 body 变成 memoryview、坏 JSON、非对象 JSON，或对象缺少 `data` 时，直接解析、索引会抛异常；[server.py:297](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/mcp/server.py:297)确有 live 调用入口。这里评价的是运行行为，不评价其既有 ignore。

其余问题逐项回答：

- **⓪ 非 dict 路径：没有漏网输入。**  
  [infra_tools.py:66](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/mcp/tools/infra_tools.py:66)解析失败先返回失败；解析为数字、字符串、列表、布尔值或 `null` 后，`:73–75` 均返回失败。只有 dict 才到 `:77`，随后才可能执行 `.get()`。即使生成错误文案时又抛异常，也进入外层失败处理，不会取得 `success=True`。

- **① `bytes(memoryview)` 不恒成功。**  
  有效 memoryview 通常能转换；已释放的 memoryview 会抛 `ValueError`。本次仅用无应用导入的 Python 内存探针确认了这一点。该错误以及字符串 body 的 `TypeError` 均由 `:67` 捕获，返回包含 HTTP 状态及异常说明的文案。缺少 `.body`、其他异常则进入 `:88`；如果 `.status_code` 也缺失，内层错误报告可能被新的 `AttributeError` 覆盖。当前是直接协程调用，不经过 HTTP 中间件。

- **② success 分支属于门未覆盖路径，两条测试对它没有任何约束力。**  
  [vault.py:98](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/api/v1/endpoints/vault.py:98)恒返回 410，故 `infra_tools.py:83–87` 不执行。未来若返回 HTTP 200、body `{}`，当前代码会报成功并给出两个空字段；这也未被测试约束。

- **③ 外层仍会把异常转成普通失败结果。**  
  `infra_tools.py:88–92` 保留异常类型和消息，但不向调用方传播异常或 traceback。端点抛 `RuntimeError("具体原因")` 时，消息仍携带具体原因；空消息异常只剩 `RuntimeError`。所以它**不必然再次生成无关错误，也不保证提供业务上有用的解释**。两条测试不约束这条异常路径。

- **④ 当前 MCP 路由仍不能到达本体。**  
  [server.py:367](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/mcp/server.py:367)包含 `switch_vault`，`:399–405` 注册的是 410 stub；没有 live 路由指向 `infra_tools.switch_vault`。准确说法是“当前 MCP 路由不可达”，测试及显式 Python 调用仍能执行它。

- **⑥ 存在有意保留的非鉴别断言。**  
  修复退回后，①的 `success is False` 仍通过，②整条测试也仍通过。A、B 足以证明**这两个具体回归会被杀掉**，不足以证明整个实现被锁住。已有负控 H“跳过端点、硬编码完整 `detail[:200]`”仍然两条全绿，明确说明调用链未被测试锁住。

round-5 其余更正已核实：

- **代码未变：成立。** `27021e85..59e0d766` 只改测试模块 docstring；生产文件逐字相同，剥除模块 docstring 后测试 AST 相同。`PREV..59e0d766` 恰为指定两个文件。
- **最终五道门证据：成立，限于核读存档。** 两文件工作树／Git blob 哈希与[最终门日志:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/_bmad-output/审查/evidence-switchvault/allgates-selfbound-59e0d766-20260916T145021.txt:5)吻合；日志支持 2 passed、pyright 汇总 `0 errors, 81 warnings`、ruff 两项通过及无 mock 判据通过。不能扩大为“81 条警告逐项相同”。
- **目录级结果：独立重算后，round-4 为 65，唯一新增所述 candidate 用例；最终 SHA 新一次为 64，与原始批基线差集为空。** 后者不改写前者。`blocked=1` 确实表示那条记录中的连接尝试被拦下。
- **证据标签：J、L、216 字符探针、A 删除 handler 的源码推导均与记录相符；参数传递未覆盖及清单非穷尽也成立。** 剩余越界主要就是 M1 的因果推论和 L1 的全称结论。


