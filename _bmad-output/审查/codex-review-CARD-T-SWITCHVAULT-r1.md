> 批次: BATCH-2026-09-11-第十四批 · 车道 T5-C (card-t5-bugs) · 卡 CARD-T-SWITCHVAULT round-1
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-T-SWITCHVAULT.md)"`
> 审查绑定: `ab99f1303745633875111bc8ef303d52143b4bb0`（该轮送审时的 HEAD）
> 会话头自证（抄 .stderr，stderr 本身不入库 —— .gitignore:264 覆盖 `_bmad-output/审查/**/*.stderr*`）:
> - codex 版本行 = .stderr:2 `OpenAI Codex v0.153.3`
> - model 行 = .stderr:5 `model: gpt-6-astra`
> - reasoning 行 = .stderr:9 `reasoning effort: ultra`

---

**结论：当前恒 410 路径上的原缺陷已修复；未发现本卡阻断项。**

已读完全部指定内容。分支、HEAD 均符合绑定，PREV→HEAD 排除 `_bmad-output` 后恰改两个文件；所读代码与 HEAD 一致。本次未修改文件、未运行项目测试、未连接数据库或端口。

**BLOCKER: 0**  
**HIGH: 0**  
**MEDIUM: 0**  
**LOW: 4**——见②③⑤⑥，均注明触发条件及当前限制。

### ⓪ 非 dict 路径：没有漏网输入

依据 [infra_tools.py:65](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/mcp/tools/infra_tools.py:65)，逐分支如下：

| 输入或状态 | 实际路径 |
|---|---|
| 转 bytes／解 JSON 抛 `TypeError`、`ValueError` | 67–69 行返回失败 |
| 抛其他普通异常 | 88–89 行返回失败 |
| JSON 数字、字符串、列表、null、布尔值 | 73–75 行全部提前返回失败 |
| dict，HTTP ≥400 或存在 `"error"` 键 | 77–81 行返回失败 |
| dict，HTTP <400 且没有 `"error"` 键 | 才能进入 83–87 行成功分支 |

因此，**题设中的非 dict 输入既不能触达后面的 `.get()`，也不能得到 `success=True`**。即使错误文案构造时再抛普通异常，也会进入外层失败返回。

失败分支取非空 `detail`，否则取 `error`，再否则使用 HTTP 状态文案；缺失 `detail` 不会生成字符串 `"None"`。

### ① `bytes(result.body)`：不是无条件恒成功

位置：[infra_tools.py:66](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/mcp/tools/infra_tools.py:66)。

- 有效、未释放的 `memoryview` 可以转换；**已释放的 memoryview 会抛 `ValueError`**，进入内层异常处理。
- `str`、`None` 等会抛 `TypeError`，同样进入内层。文案包含 HTTP 状态和具体异常，仍有信息量，但“不是有效 JSON”把转换失败也归入了这一类。
- `bytearray` 等可以转换，随后正常判断 JSON。
- 缺少 `.body`、转换抛 `OverflowError`／`MemoryError` 或其他异常，则进入外层，只保留原异常字符串，信息量没有保证。
- 如果连 `status_code` 都不可读取，内层构造文案时的异常也会落入外层。

已用不导入项目的标准库演算核验上述常见转换。另需澄清：这里直接调用端点协程，**普通 HTTP 中间件不经过这条调用链**。

### ② LOW-1：成功分支未覆盖，而且缺少成功结构校验

**位置：**[infra_tools.py:77](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/mcp/tools/infra_tools.py:77)、83–86 行。

**显形条件：**将来返回 HTTP 200、body 为 `{}` 或 `{"success": false}`，且没有 `"error"` 键时，代码仍返回 `success=True`，两个 vault 字段均为空。

当前 [vault.py:97](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/api/v1/endpoints/vault.py:97) 恒返回 410，因此这是当前不可达的潜在路径。**它属于门未覆盖的路径；两条测试对成功分支没有任何约束力。**这不构成要求本卡恢复切换能力的理由。

### ③ LOW-2：既有外层异常处理仍可能隐藏诊断信息

**位置：**[infra_tools.py:88](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/mcp/tools/infra_tools.py:88)。

**显形条件：**端点自身、请求模型构造或响应处理抛普通异常时，只返回 `str(e)[:200]`，没有异常类型、发生阶段或堆栈。

例如空消息的 `RuntimeError()` 会得到空错误；`AttributeError` 仍可能变成裸内部错误。因此**仍可能吞掉本该显形的错误**。但不能说所有端点异常都“与真实原因无关”：异常本身若写明原因，该原因仍会保留。

补充边界：54 行导入在 `try` 外，导入错误不会被此外层捕获。

### ④ 当前 MCP 注册面：本体确实不可达

依据 [server.py:367](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/mcp/server.py:367)，`switch_vault` 在隔离清单内；[server.py:399](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/mcp/server.py:399) 将对应 URL 绑定到 `_make_handler` 生成的 410 stub。

静态搜索未发现生产代码中其他指向 `infra_tools.switch_vault` 的调用。

所以，**它是当前生产 MCP 注册面上的不可达代码，本次修复没有改变该路由的运行行为**。测试和显式 Python 调用仍能执行本体，不能扩大表述为“任何运行期都不可达”。

### ⑤ LOW-3：health 存在同型防御缺口，需另立卡

**位置：**[infra_tools.py:47](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/mcp/tools/infra_tools.py:47)。

**显形条件：**body 为 memoryview、非法 JSON、非对象 JSON 或对象缺少 `data` 时，直接解析并索引会抛类型、解码或键错误，没有相应守卫。

它有真实 live 调用：[server.py:297](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/mcp/server.py:297)。此外，[system.py:430](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/api/v1/system.py:430) 当前实际返回的已经是 JSONResponse，因此解析分支当前就会执行；正常返回包含合法 `data`，未发现正常响应必然失败。

**建议另立卡。**本项不评价既有 pyright ignore。

### ⑥ LOW-4：测试锁住两种具体回退，未锁住完整透传契约

**位置：**[test_mcp_switch_vault_tool.py:55](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/unit/test_mcp_switch_vault_tool.py:55)、58、65、72–86 行。

**显形条件：**实现发生以下回退或错误修改时：

| 变化 | 测试结果推导 |
|---|---|
| 退回旧属性访问 | 第一条的 `success=False` 仍绿，58 行属性错误断言红；第二条全部仍绿 |
| 删除 410/error 分支 | 第一条在55行成功状态断言红 |
| 错误地硬编码 `success=False, error="quarantined"` | 两条仍可全绿 |
| 删除非 dict 守卫、删除 `bytes()`、改坏成功字段映射 | 当前常量响应下，两条仍可全绿 |

因此，两组负控**足以证明能捕获题述两种回归，不足以证明完整透传和所有新增分支都被锁住**。

两条测试源码确实用 `asyncio.run` 执行真协程，没有替换 `_switch`。但第二条独立调用端点，只证明端点契约；**它本身不能证明第一条调用了该端点**。本次实际调用关系由54、57行源码独立确认。

### 作者声明的其余核对

- **(a)(b)(c)(e)：成立。**解析 body 的模式与 health 相同；本地 Starlette 的 body 类型来源包含 `bytes | memoryview`；`switch_vault` 函数体内零 pyright ignore。
- **(d)：是截断透传。**真实 `detail` 长216字符，81行只返回前200字符，截掉末尾 `to change vault.`；隔离原因及完整部署命令保留。
- **(g)：留存证据相符，未独立重跑。**两份 pyright 摘要逐字相同；两份失败清单均64条、顺序和内容完全相同；日志记载 Ruff 两项 rc=0、两测试通过及两组负控失败。这些是日志复核，不是本次执行结果，也不证明81条 warning 的身份逐条相同。


