> 批次: BATCH-2026-09-11-第十四批 · 车道 T5-C (card-t5-bugs) · 卡 CARD-T-SWITCHVAULT round-4
> 模型: `gpt-6-astra` · reasoning_effort: `ultra` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --sandbox read-only -m gpt-6-astra -c model_reasoning_effort="ultra" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-T-SWITCHVAULT-r4.md)"`
> 审查绑定: `27021e85f1d5548a47b8a2e5126be152fe9eac40`（该轮送审时的 HEAD）
> 会话头自证（抄 .stderr，stderr 本身不入库 —— .gitignore:264 覆盖 `_bmad-output/审查/**/*.stderr*`）:
> - codex 版本行 = .stderr:2 `OpenAI Codex v0.153.3`
> - model 行 = .stderr:5 `model: gpt-6-astra`
> - reasoning 行 = .stderr:9 `reasoning effort: ultra`

---

结论：**当前隔离路径的修复成立，但 round-4 的证据表述仍未全部成立。**

已核对分支、HEAD 和指定读取面；本次只读，未运行项目测试、导入项目代码或连接端口。以下绑定 `27021e85f1d5548a47b8a2e5126be152fe9eac40`，证据以本次读取快照为准。

**BLOCKER: 0**  
**HIGH: 0**  
**MEDIUM: 2**

1. **最终 SHA 的目录级结果实际为 65 条红项，不能声称“64 条逐条相同、diff 空”。**  
   位置：[unit-close-r4-20260916T132148.txt:1215](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/_bmad-output/审查/evidence-switchvault/unit-close-r4-20260916T132148.txt:1215)。  
   我独立提取 FAILED/ERROR 清单，与基线比较得到 **base=64、close=65、新增1、减少0**。新增的是 `test_accept_candidate_already_accepted_returns_422`；同日志 `:601–605`、`:1148` 显示一次 Neo4j 连接尝试被阻断。**这不证明本卡引入回归，也不表示实际连接成功**；但确实反证本次目录级“零新增”。后来单独重跑通过不能改写该次结果。若处理该测试，**需另立卡**。

2. **“全部裁判已在最终 SHA 重跑”缺乏对应记录。**  
   位置：[allgates-selfbound-final-20260916T124527.txt:2](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/_bmad-output/审查/evidence-switchvault/allgates-selfbound-final-20260916T124527.txt:2)。  
   该记录绑定的是 **`3ecf2c5e`**，测试文件摘要也属于旧版本；`:31–34` 的 ruff check/format 成功不能改称对 `27021e85` 的实测。UAT `:6、:50、:59` 同样仍绑定旧 SHA。**当它们被引用为最终 SHA 验收依据时显形**；AST 等价不能替代新版文档的格式检查。

**LOW: 3**

1. **N 探针把单条断言通过扩大成完整测试①通过。**  
   位置：[test_mcp_switch_vault_tool.py:54](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/unit/test_mcp_switch_vault_tool.py:54)。  
   [N 记录:6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/_bmad-output/审查/evidence-switchvault/negctl-r4-mockshapes-20260916T132000.txt:6) 明说只检查 `"has no attribute" not in error`。M4 的 `fake detail`、M5 的 JSON 解析错误都会在完整测试的 `:149` **token 断言失败**。因此 `:55–56` 的“①绿、门形同虚设”不成立；“②也在测 mock”亦无对应执行记录。

2. **负控 A 的“杀伤力依赖 handler 仍在”不成立，依赖它的只是失败位置。**  
   位置：[test_mcp_switch_vault_tool.py:91](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/unit/test_mcp_switch_vault_tool.py:91)。  
   **恢复 `result.vault_name` 并删除外层 handler 时**，`AttributeError` 会直接使 `:135` 的 `asyncio.run` 失败，测试仍红。只有“红在属性错误文案断言”依赖 handler。

3. **216 字符及截断尾巴被标为实测，但未找到对应探针存档。**  
   位置：[test_mcp_switch_vault_tool.py:38](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs/backend/tests/unit/test_mcp_switch_vault_tool.py:38)。  
   L 记录只保存了变异生效和逐字断言失败；body 类型探针未打印长度或尾巴。**将这句话作为实测证据引用时显形**。我从端点源码常量独立计算，确实得到 `216` 和 `"to change vault."`，但这支持源码计算结论，不能补成作者此前已有的运行期探针记录。

逐项回答原问题：

- **⓪ 非 dict 路径安全。** `infra_tools.py:66–69` 先处理转换、解析异常；解析成功的数字、字符串、列表、null、bool 均在 `:73–75` 返回失败；只有 dict 才能到 `:78、:85–86` 的 `.get()`。若读取 `status_code` 出错，则进入外层失败处理。**不存在非 dict 穿透到 `.get()` 或得到 `success=True` 的路径。**
- **① `bytes(memoryview)` 并非恒成功。** 已释放的 memoryview 会抛 `ValueError`，进入 `:67` 内层处理；str、None 等通常产生 `TypeError`，也在这里处理。其他异常可能进入 `:88` 外层。内层通常保留 HTTP 状态及异常消息；但若 `status_code` 同样缺失，最终可能只剩该属性错误，覆盖最初转换失败的信息。
- **② 是未覆盖路径。** 端点正常返回恒为 410，`:83–87` 的成功分支不执行；两条测试对它的成功契约、字段映射**没有任何约束力**。负控 B 只证明当前 410 不能被误报成功。
- **③ 外层仍会吞掉异常传播。** `:88–92` 返回“异常类型＋原消息”，不保留堆栈和异常链。端点抛异常时，信息是否充分取决于原异常；不能一概说与真实原因无关。空 `RuntimeError()` 只能得到 `"RuntimeError"`。
- **④ 当前 MCP 路由不可达。** `server.py:367` 包含 `switch_vault`，`:399–403` 注册的是 410 stub，没有 live 路由指向工具本体。测试及显式 Python 调用仍可执行它，因此不能扩大成“任何运行期均无人可达”。
- **⑤ health 有条件性同型隐患，建议另立卡。** `infra_tools.py:44–47` 对 memoryview、坏 JSON、非对象及缺 `data` 没有防御，且 `server.py:283–297` 是 live 注册面。UAT `:191–194` 的移交条目已实际存在。
- **⑥ 存在改前改后都绿的断言。** 测试①的 `success is False`、测试②全部断言均不能单独识别原缺陷。A/B 足以证明拦住那两个具体回退；**不足以证明整个修复被完整锁住**。C/K/L 增加了具体约束，H 则已证明调用链仍不受测试保证。

round-4 其余重点：

- A–M 的其余对应结果与存档相符，M 确有 `0 errors → 1 error`。但 UAT `:165–166` 仍把 `str(detail)` 写成“源码推导、未跑变异”，与 J 记录矛盾，说明证据标签尚未全部同步。
- 11 条覆盖了主要未覆盖分支，但不是穷尽清单。例如 `infra_tools.py:57` 把输入路径替换成固定合法字符串，仍真实调用端点并得到相同 410，两条测试不会发现；可归入第 7 条的参数传递边界。
- **本轮没有改变执行逻辑：确认。** 生产文件逐字相同；测试文件剥除 docstring 后 AST 指纹相同。我在内存中改变真实断言后，比较结果确实变为不同，验伪锚为 `True`。
- `(g)` 中旧记录的 pyright 汇总逐字相同成立；最终 SHA 的目录级记录也显示本卡两条测试通过。不能据此确认全部最终 SHA 裁判通过或红集不变。


