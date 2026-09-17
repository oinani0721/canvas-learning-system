> 批次: BATCH-2026-09-11-第十四批 · 车道 T5-C (card-t5-bugs) · 卡 CARD-T-SWITCHVAULT round-3
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-T-SWITCHVAULT-r3.md)"`
> 审查绑定: `3ecf2c5e9e163a3daecc14797a28cdab80d82380`（该轮送审时的 HEAD）
> 会话头自证（抄 .stderr，stderr 本身不入库 —— .gitignore:264 覆盖 `_bmad-output/审查/**/*.stderr*`）:
> - codex 版本行 = .stderr:2 `OpenAI Codex v0.153.3`
> - model 行 = .stderr:5 `model: gpt-6-astra`
> - reasoning 行 = .stderr:9 `reasoning effort: ultra`

---

**结论：当前 410 隔离响应的错误透传修复成立；round-3 的文档整改仍未完全闭合。**

已读完全部指定读取面，确认分支及 HEAD 为指定值。全过程未改文件、未运行项目测试、未连接数据库或端口。

## 分级问题

**BLOCKER: 0**  
**HIGH: 0**  
**MEDIUM: 0**  
**LOW: 4**

### LOW-1：仍残留“②证明①调用链”的过强表述

- 位置：[test_mcp_switch_vault_tool.py:21](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/unit/test_mcp_switch_vault_tool.py:21)、同文件 **:118**。
- 显形条件：负控 H 跳过端点、直接返回完整固定文案时，两条测试仍绿；②只能证明它自己调用的端点契约，不能证明①调用了该端点。
- 新增第 7 条已正确承认这一边界，但上述两处仍与它矛盾。另外 **:20** 的“任何假返回值上都恒真”也不成立：返回缺少 `body` 的对象即可产生属性错误，使①变红。

### LOW-2：“九条均有逐项负控实测”的前言超过现存证据

- 位置：[test_mcp_switch_vault_tool.py:31](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/unit/test_mcp_switch_vault_tool.py:31)。
- 显形条件：读者按“每条都标注是哪组变异实测出来的”理解全部九条时，会把源码推导误认成逐项实测；实际第 1–4、9 条没有对应组号，A–H 也未逐项验证这些内容。
- 应区分“负控摘要支持”与“源码分支推导”。

### LOW-3：外层异常分支的触发条件仍写得过窄

- 位置：[test_mcp_switch_vault_tool.py:48](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/unit/test_mcp_switch_vault_tool.py:48)；实际路径为 `infra_tools.py:66`、`:77`、`:88`。
- 显形条件：端点正常返回，但对象缺少 `body`，或 `status_code` 无法与整数比较，同样进入外层 `except`；“要靠端点抛异常”不是必要条件。
- 同文件 **:56–57** 对内层异常不可达的归因也应明确：依据是当前返回合法 JSON 字节；仅有“非空 detail”不足以说明解析阶段不会异常。

### LOW-4：九条仍遗漏非字符串 `detail` 的转换未覆盖

- 位置：[infra_tools.py:80](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/app/mcp/tools/infra_tools.py:80)；清单位置 `test_mcp_switch_vault_tool.py:56`。
- 显形条件：当前 `detail` 恒为字符串，删除 `str(detail)` 对这两条测试的固定输入没有影响；若将来返回 `detail=7`，删除转换后会在截断操作处报错。
- 第 9 条只登记了缺失时的回退链，没有明确登记这一类型转换。**这是源码推导，本轮没有运行该变异。**

## ⓪–⑥ 逐项回答

### ⓪ 非 dict 是否可能漏过守卫或返回成功？

**没有。**按 `infra_tools.py:65` 起的顺序：

1. 解析抛 `TypeError`／`ValueError`：进入 **:67–69**，失败返回；其他普通异常进入外层捕获。
2. 解析得到数字、字符串、列表、`null`、布尔值：在 **:73–75** 立即失败返回。
3. 只有字典才能到 **:77**；HTTP ≥400 **或**存在 `error` 键，均失败。
4. 只有未满足上述失败判据的字典才能进入 **:83–87**。

所有 `.get()` 都在字典守卫之后。缺失或假值 `detail` 会继续回退到 `error`／HTTP 文案，不会仅因缺失而变成字符串 `"None"`。

### ① `bytes(memoryview)` 是否恒成功？

**不是。**有效、未释放的普通 memoryview 可以转换；已释放的 memoryview 会抛 `ValueError`，进入 **:67–69**，文案包含 HTTP 状态和异常消息。

- `body` 为 `str`／`None`：通常抛 `TypeError`，进入内层。
- 缺少 `body`，或自定义转换抛其他普通异常：进入 **:88–92**，返回异常类型及消息。
- 若连 `status_code` 都异常，内层构造文案也可能失败，再进入外层，原始解析原因可能被后续异常遮住。

本地 Starlette 源码支持更正后的类型归因和正常路径返回 bytes 的说明；**Pyright 的类型检查不证明所有运行期转换都成功。**

### ② 成功分支是否没有测试约束？

**是，两条测试对成功分支没有任何约束力。**

`vault.py:97–108` 当前正常返回恒为 410，因此 `infra_tools.py:83–87` 永不执行；成功字段映射同样未覆盖。

### ③ 外层是否仍吞异常？

**仍会。**`infra_tools.py:88–92` 把普通异常转成失败结果，没有重新抛出或记录 traceback。

但端点直接抛异常时，现在保留实际异常类型和消息；空消息 `RuntimeError()` 返回 `"RuntimeError"`。它不能保证解释完整业务原因，也不能保证揭示根因；**不能据此说它必然恢复成原来的无关属性错误。**

### ④ 当前 MCP 运行入口能否到达本体？

**不能。**

`server.py:367` 将 `switch_vault` 列入隔离清单，**:399–405** 注册的是 410 stub；生产代码搜索未发现 live 路由指向 `infra_tools.switch_vault`。

准确表述是：**当前 MCP 路由不可达，显式 Python 调用和测试仍可执行本体。**

### ⑤ health 是否有同型隐患？

**有，建议另立卡。**

`infra_tools.py:44–47` 直接解析 `body` 并索引 `"data"`；memoryview、坏 JSON、非对象 JSON、缺失 `data` 都可能使其抛异常。它通过 `server.py:283–297` 的 live 路由可达。

当前正常返回包含 `data`，所以这是条件性防御缺口。本卡无需处理；本轮未取得可定位的验收单移交条目，不能确认“已登记”。

### ⑥ 两组负控是否足以证明“测试锁住了修复”？

**只能支持有限结论。**

- 修复退回后，第二条测试仍全部通过；第一条的 `success is False` 断言也仍通过。
- A/B 证明测试能识别这两个具体回退。
- 加上 C，可以支持当前隔离文案的逐字一致性约束。
- H 明确证明：这些测试不能锁住调用链；D–G 也证明不能覆盖全部新增防御行为。

因此，“锁住原属性访问回退和当前隔离输出”成立；“锁住整个修复及其调用链”不成立。

## round-3 改动与证据核对

- **范围确认**：PREV → HEAD 恰两个文件。
- **执行代码确认**：`b355f7b7 → 3ecf2c5e` 只有测试模块 docstring 和行内注释变化，生产文件逐字相同。独立剥除 docstring 后 AST 相同；内存中修改真实断言值后比较变为 False。准确说是“仅改文档文字”，包括 comments。
- **负控记录确认**：[八组摘要](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/_bmad-output/审查/evidence-switchvault/negctl-r3-8mutants-20260916T021643.txt:1)记录 A/B/C 为 `1 failed, 1 passed`，D–H 为 `2 passed`，与作者表格一致。但它没有完整变异 diff、执行命令及 pytest 输出，不能视为本轮独立复现。
- **(g) 的证据边界**：保存的 Pyright 单行摘要逐字相同；Ruff 和两测试的保存结果吻合。独立从目录测试日志提取的 64 项失败／错误记录与基线清单一致。相关执行证据绑定 `b355f7b7`，不是最终 SHA 的重跑；AST 同一性支持执行代码未变，不能替代本轮 Ruff 格式检查。


