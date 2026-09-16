> 批次: BATCH-2026-09-11-第十四批 · 车道 T5-C (card-t5-bugs) · 卡 CARD-T-SWITCHVAULT round-2
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-T-SWITCHVAULT-r2.md)"`
> 审查绑定: `b355f7b7ce039ff5fad04ced64b901661828a038`（该轮送审时的 HEAD）
> 会话头自证（抄 .stderr，stderr 本身不入库 —— .gitignore:264 覆盖 `_bmad-output/审查/**/*.stderr*`）:
> - codex 版本行 = .stderr:2 `OpenAI Codex v0.153.3`
> - model 行 = .stderr:5 `model: gpt-6-astra`
> - reasoning 行 = .stderr:9 `reasoning effort: ultra`

---

**当前隔离响应的核心缺陷已修复；round-2 仍有测试证明范围与证据口径问题。**

已逐项读完指定读取面及两组 diff。分支、HEAD 均匹配 `b355f7b7ce039ff5fad04ced64b901661828a038`，PREV→HEAD 的代码改动恰好两个文件。全程只读，未运行测试、连接数据库或端口。

## 分级发现

**BLOCKER: 0**  
**HIGH: 0**  
**MEDIUM: 0**  
**LOW: 4**（含一项既有隐患，需另立卡）

### LOW-1：逐字比对仍不能证明调用链，也没有建立两条测试之间的数据依赖

位置：[test_mcp_switch_vault_tool.py:21](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/unit/test_mcp_switch_vault_tool.py:21)、`:27`、`:88`。

测试①内部另调端点取得期望值；测试②的结果没有被①消费。**若工具跳过端点，直接硬编码当前完整 `detail[:200]`，两条测试仍可通过。** 新断言确实挡住了短常量 `"quarantined"`，但注释所称“证明调用该端点”仍不成立。

### LOW-2：“本文件不证明什么”仍漏列新增分支

位置：[test_mcp_switch_vault_tool.py:30](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/unit/test_mcp_switch_vault_tool.py:30)；[infra_tools.py:65](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/mcp/tools/infra_tools.py:65)、`:77`、`:78`、`:80`。

当前测试只遇到“合法对象、HTTP 410、`error="gone"`、非空字符串 `detail`”，因此还没有约束：

- 转换／JSON 解析失败后的内层异常兜底；
- `detail` 缺失或假值时，回退到 `error`、再回退到 HTTP 文案；
- HTTP 状态与 `error` 键两个失败判据各自的作用。

**删除任一个失败判据，或把 `or` 改成 `and`，当前两条测试仍能通过。** 负控 B 删除整个失败分支，并没有覆盖这些变异。

### LOW-3：现有负控日志没有证明“五组均实跑两条测试”

位置：[test_mcp_switch_vault_tool.py:39](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/unit/test_mcp_switch_vault_tool.py:39)、`:45`；[负控日志:35](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/_bmad-output/审查/evidence-switchvault/negctl-r2-5mutants-20260916T020013.txt:35)、`:43`。

日志中 A/B/C 各为 `1 failed`，D/E 各为 `1 passed`。**将它表述为“两条测试仍全绿实测”时，证据口径超过了日志。** 测试②不执行工具本体，故这些变异不影响②，可以静态判断；应与实际运行记录分开。

同样，现有材料支持 `bytes()` 的静态类型理由，但没有提供“删除 `bytes()` 后 pyright 报错”的负控记录。

### LOW-4：`check_backend_health` 的响应解析仍有同型防御缺口——建议另立卡

位置：[infra_tools.py:44](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/mcp/tools/infra_tools.py:44)，实际解析在 `:47`；live 调用见 [server.py:297](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/mcp/server.py:297)。

**当响应 body 为 `memoryview`、非法 JSON，或解析结果缺少 `"data"`／类型不符时**，这里可能直接抛出 `TypeError`、解析异常或 `KeyError`。当前健康端点正常返回带 `"data"` 的 JSONResponse，未发现该正常响应必然失败；这项需另立卡，本卡不处理。

## 逐项结论

### ⓪ 非 dict 能否漏过守卫？

**不能。** 按实际执行顺序：

| 输入／状态 | 分支结果 |
|---|---|
| 转换或解析抛 `TypeError`／`ValueError` | `:67–69` 返回失败 |
| JSON 数字，包括浮点数 | `:73–75` 返回失败 |
| JSON 字符串 | 同上 |
| JSON 列表 | 同上 |
| JSON `null` → `None` | 同上 |
| JSON 布尔值 | 同上 |
| dict，HTTP ≥400 | `:77–81` 返回失败 |
| dict，HTTP <400，但存在 `"error"` 键 | 同上，即使其值为空 |
| dict，HTTP <400，且没有 `"error"` 键 | `:83–87` 返回成功 |

所有 `.get()` 都位于非 dict 早返回之后，没有非 dict 输入能抵达它们。

**但 dict 的成功判定很宽：HTTP 200 加 `{}` 就会返回成功和两个空字段。** 当前恒 410，不会执行这条路径。

### ① `bytes(memoryview)` 是否恒成功？D 的更正是否准确？

**不能无条件说恒成功。** 有效的 `memoryview` 通常可以转换；已经释放的 view 会抛 `ValueError`，进入内层兜底。

其他典型情况：

- `body` 为 `str`、`None`：转换抛 `TypeError`，返回带 HTTP 状态及异常消息的“body is not valid JSON”文案。
- `body` 为 `bytearray`：可以转换，再解析。
- 响应缺少 `body`，或转换过程抛其他普通异常：进入外层 `except Exception`，返回异常类型和消息。
- 若连 `status_code` 也不符合响应契约，构造内层错误文案时可能再次异常，最后返回外层捕获的错误。

这通常保留了诊断线索，但“不是合法 JSON”也包含了**尚未开始解析就转换失败**的情况。

**作者撤回 D 的原声称是正确的。** 本地依赖源码中，[JSONResponse.render:194](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/.venv/lib/python3.14/site-packages/starlette/responses.py:194) 返回编码后的 `bytes`；当前端点正常返回路径删除 `bytes()`，行为不变。

文档还需精确两点：

- “运行期恒为 bytes”应限定于**当前端点正常返回、body 未被替换**的路径。
- 联合类型来自 **Starlette `Response.render` 及 `body` 的类型推导**；typeshed 提供的是 `json.loads` 接受 `str | bytes | bytearray` 的签名。“typeshed 把 Response.body 标成……”归因不准确。

### ② 成功分支有没有门？

**是未覆盖路径；两条测试对该分支及字段映射没有任何约束力。** 测试①约束的是当前 410 响应必须失败，不能据此证明未来成功响应处理正确。

### ③ 外层异常是否仍被吞掉？空消息整改是否有效？

[infra_tools.py:88](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/mcp/tools/infra_tools.py:88) 仍把普通异常转换为失败字典，异常不会继续传播，traceback 和异常链也没有保留。

不过，端点若抛 `RuntimeError("具体原因")`，现在会返回 `"RuntimeError: 具体原因"`；**它保留的是原异常，不会必然重新制造原来的无关属性错误。** 原异常本身若缺少业务说明，包装器仍无法补出真实业务原因。

round-2 对普通空消息异常的整改有效：`RuntimeError()` 返回 `"RuntimeError"`，不再是空字符串。新增类型名前缀会占用 200 字符额度，使原消息末尾更早被截断；没有证据表明单独增加类型名构成新的实质泄漏问题。D/E 中的 E 确实没有行为门。

### ④ live MCP 是否能调用修复后的本体？

**按所查注册面，不能。**

`switch_vault` 位于 [server.py:367](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/mcp/server.py:367) 的隔离清单；`:399–405` 注册的是 `_make_handler(...)` 生成的 410 stub，没有 live 路由指向 `infra_tools.switch_vault`。

测试和显式 Python 调用仍能执行本体；此次修改不会改变 live MCP stub 的响应。

### ⑤ 同文件健康工具

见 **LOW-4：建议另立卡**。

### ⑥ 两条测试及五组负控究竟锁住什么？

| 负控 | 当前 SHA 对应断言 | 能支持的结论 |
|---|---|---|
| A：退回属性访问 | 测试 `:74` | 能发现原属性错误回归 |
| B：删除整个失败分支 | 测试 `:71` | 能发现当前隔离响应被报成功 |
| C：硬编码 `"quarantined"` | 测试 `:92` | 能发现该短文案未逐字透传 |
| D：删除 `bytes()` | 未发现变异 | 本测试不守此转换 |
| E：恢复旧异常格式 | 未发现变异 | 本测试不守外层异常文案 |

日志中的 `:58`／`:55` 是旧行号；当前 SHA 分别为 `:74`／`:71`。

测试②全部断言、测试①的 `success is False` 在原缺陷下仍会通过，这是其作为契约锚／前置断言的边界。**A/B/C 足以支持当前固定隔离响应的核心修复，不能支持“所有新增改动都有门”。**

新增逐字断言会随端点的固定文案一起更新期望值，正常改文案通常不会因此噪音红；已有 `:81` 的 token 断言仍限制措辞。若未来 `detail` 含每次调用变化的内容，两次独立调用的逐字比较才会产生不稳定性。

## 作者自述的验证边界

代码层面，解析 body、非 dict 失败、缺失 `detail` 不产生 `"None"`、函数体零 pyright ignore，以及两测试直接执行真实协程，均与源码一致。

现有日志记录了 `2 passed`、ruff 两门 rc=0；pyright 前后**摘要**逐字相同，为 `0 errors, 81 warnings, 0 informations`。我另从目录级日志重提了 **35 FAILED + 29 ERROR**，与关闭清单一致；关闭清单与提供的 64 条基线清单也逐字一致。以上是本轮只读核对已有证据，未重跑这些检查。
