你是独立复核者。请只读、不改任何文件、不连任何数据库或网络端口。

仓库树根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t5-bugs`
分支 `card/t5-bugs`，审查绑定 SHA = `27021e85f1d5548a47b8a2e5126be152fe9eac40`（HEAD），
地盘基线 PREV = `6d7eb683f126ec4ae142426ad7be34d33cad0e27`。

---

## ① 背景与最小读取面（请逐个读完再下结论）

本卡 `CARD-T-SWITCHVAULT`（BATCH-2026-09-11-第十四批）修一个真缺陷：MCP 工具
`switch_vault` 直接读 `result.vault_name` / `result.vault_id`，而被调用的端点注解并
实际返回 `JSONResponse`，它没有这两个属性 ⇒ 运行期 `AttributeError` 被本函数的
`except Exception` 吞成
`{'success': False, 'error': "'JSONResponse' object has no attribute 'vault_name'"}`。
调用方看到的是一句与真实原因无关的内部类型错误；真实原因是该端点被 P0-3 写侧隔离、
恒返回 410，改 vault 要在部署配置里改。

请读以下内容（写死的最小读取面）：

1. `git --no-pager diff --no-color 6d7eb683f126ec4ae142426ad7be34d33cad0e27 27021e85f1d5548a47b8a2e5126be152fe9eac40 -- . ':(exclude)_bmad-output'`
   —— 本卡全部代码改动（应恰两个文件）。
2. `backend/app/mcp/tools/infra_tools.py` **全文**（含未改动的 `check_backend_health`，
   它是本卡参照的同型先例，本卡不改它）。
3. `backend/app/api/v1/endpoints/vault.py` 第 30–108 行 —— `VaultSwitchRequest` 模型
   与 P0-3 隔离端点本体（恒 410）。
4. `backend/app/mcp/server.py` 第 277–297 行（`check_backend_health` 的 live 路由注册面）
   与第 353–405 行（`QUARANTINED_MCP_TOOLS` 清单 + 410 stub 注册循环）。
5. `backend/tests/unit/test_mcp_switch_vault_tool.py` **全文** —— 本卡新增的两条测试。

---

## ② 作者自述（请独立核对，不要采信）

作者声称：

- (a) `switch_vault` 现在解析 `JSONResponse.body`，与同文件 `check_backend_health` 同型；
- (b) `bytes(result.body)` 是为静态类型准备的：`body` 的静态类型是 `bytes | memoryview[int]`，
  而 `json.loads` 不接受 `memoryview`；
- (c) 对 `payload` 加了 `isinstance(payload, dict)` 守卫，且**非 dict 一律判失败**，
  不落进 `success=True` 分支；
- (d) 410 / `error` 分支把端点 body 里的 `detail` 透传为 `error`；`detail` 缺失时不落成
  字符串 `"None"`；
- (e) 原先 `:63` / `:64` 两处 `# pyright: ignore[reportAttributeAccessIssue]` 已随缺陷访问删除，
  `switch_vault` 函数体内现在零 pyright ignore（`check_backend_health` 的那条保留、非本卡地盘）；
- (f) 两条新测试**直接 await 真协程**、不 mock、不 monkeypatch，打的是真实隔离端点；
  第二条测试是第一条的自证锚，断言 `status_code == 410` 且 body 里没有 `vault_name` / `vault_id`；
- (g) 实测：`pyright app` = `0 errors, 81 warnings`（与本卡开工基线逐字相同）；
  `ruff check` / `ruff format --check` 两文件 rc=0；两条测试 2 passed；
  `tests/unit` 目录级红集与批基线 64 条逐条相同（零新增、零减少）。

---

## ③ 请按重要性排序回答这些问题

⓪ **payload 非 dict 的路径**：`json.loads` 可能返回数字 / 字符串 / 列表 / null。
   现在的分支排列下，是否存在**未被拦下的输入**能触达某个未加守卫的 `.get(...)`，
   或者能让调用方拿到 `success=True`？请逐条走分支，不要只看 `isinstance` 那一行。

① `bytes(result.body)` 在 `body` 为 `memoryview` 时是否恒成功？若 `body` 是别的类型
   （例如被中间件替换），会落到哪个 `except`、调用方看到的文案是否仍有信息量？

② `success=True` 分支在当前隔离态**永不执行**（端点恒 410）。这是否属于
   **门未覆盖的路径**？若是，本卡的两条测试对它有无任何约束力？请直说没有。

③ 外层 `except Exception as e` 是否仍会吞掉本该显形的错误？特别是：端点若抛异常
   而不是返回 `JSONResponse` 时，调用方拿到的文案是否又变回一句与真实原因无关的内部错误？

④ 修好之后，这个函数在运行期是否仍然是**无人可达的死代码**？请以
   `server.py` 的注册面为准给出判断（`switch_vault` 是否在 `QUARANTINED_MCP_TOOLS` 内、
   是否有任何 live 路由指向 `infra_tools.switch_vault` 本体）。

⑤ 同文件 `check_backend_health` 是否有同型隐患？**本卡不改它**，只问是否需要另立卡。

⑥ 两条测试是否存在**假绿面**：有没有哪条断言在修复被退回后仍然会通过？
   （作者做过两组负控：退回 `result.vault_name` 时红在「has no attribute」那条；
   删掉 410 透传分支时红在 success 那条。请判断这两组是否足以支撑「测试锁住了修复」。）

---

## ④ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给出：
- 一句问题陈述；
- `file:line`（用你实际读到的行号）；
- 一句说明「在什么输入或什么状态下会显形」。

若某级别没有问题，请显式写 `BLOCKER: 0` / `HIGH: 0` 等，不要省略。

---

## ⑤ 边界

- 只读。不要修改文件，不要运行会写盘的命令，不要连接任何数据库或端口。
- **不要评价 P0-3 隔离决策本身**——是否该解除隔离是产品裁定，不在本卡范围；
  本卡只把误导性的错误文案改成透传真实原因。
- **不要评价 `check_backend_health` 既有的那条 pyright ignore**（`:47` 附近），
  它不在本卡地盘；如认为需要处理，只在 ⑤ 里说「建议另立卡」即可。
- 不要要求本卡恢复 runtime vault 切换能力。
- 不要要求扩大本卡地盘：本卡只允许改
  `backend/app/mcp/tools/infra_tools.py` 与 `backend/tests/unit/test_mcp_switch_vault_tool.py`
  两个文件。若你的建议需要改别的文件，请标注「需另立卡」。

---

## ⑥ round-4 增量：round-3 四条 LOW 的处置 + 一次独立多视角审计

round-3 你给出 BLOCKER 0 / HIGH 0 / MEDIUM 0 / LOW 4，四条全部是**文档表述强于证据**。
本轮除按你的意见整改外，还另跑了一次**独立多视角审计**（5 个不同 lens 各自逐句审查 +
每条 finding 由 3 个 refuter 对抗验证），共收 35 条，去重后逐条整改。

增量 diff：
`git --no-pager diff --no-color 3ecf2c5e9e163a3daecc14797a28cdab80d82380 27021e85f1d5548a47b8a2e5126be152fe9eac40 -- . ':(exclude)_bmad-output'`
**本轮只改测试文件的 docstring 与注释**，生产文件零 diff。

### (1) 为回应「证据不足」，补跑了负控 I–N 六组，把四条推导升为实测

| 组 | 变异 | 实测 | 对应 |
|---|---|---|---|
| I | 删失败判据的 `"error" in payload` 一侧 | 2 passed | 补齐你 r2 LOW-2 指出「只测了一侧」 |
| J | 删 `str(detail)` 类型转换 | 2 passed | 你 r3 LOW-4 的漏列项 |
| K | 照原设计稿改回去（删失败分支 + 直接索引 `payload["vault_name"]`） | 1 failed，**红在 token 断言** | 厘清「防后人改回去」归①不归② |
| L | 删失败分支的 `reason[:200]` 截断 | 1 failed，**红在逐字比对断言** | 确认截断**被**①锁住（detail 实测 216 > 200） |
| M | 删 `bytes()` 后跑 **pyright** | `0 errors` → **`1 error`**，报在 `infra_tools.py:66` 的 `json.loads` 实参（`bytes \| memoryview[int]` 不能赋给 `str \| bytes \| bytearray`） | **你 r2 LOW-3 末段点名的缺口**：此前「由 pyright 门守」只有推导，现已实测 |
| N | 五种 mock 形状探针（进程内 monkeypatch，不改仓库文件） | 缺 `.body` 或缺 `.status_code` 的三种 ⇒ ①**红**；带 `.body`+`.status_code` 的两种 ⇒ ①绿 | 证伪 `:20` 的「任何假返回值上都恒真」 |

### (2) 文档整改：引入三级证据标注

每条声明现在都标注了【实测-负控 X】/【实测-探针】/【源码推导】，并在开头声明
「没有标注的句子不得被当作实测结论引用」。逐条处置：

- **你 r3 LOW-1**：`:21-22`、`:118` 两处「②证明①调用链」已改；另外审计发现**第三处**
  `:15` 的「**被调**端点」（这个词同样预设「②验的就是①调用过的那个端点」），三轮均未点名，一并改。
  `:20` 的「任何假返回值恒真」按负控 N 的五形状实测改写。
- **你 r3 LOW-2**：清单前言改为明确区分——第 5/6/7/8/11 条有负控组号，第 1/2/3/4/9/10 条
  是源码推导。⚠️ 并按审计意见把**第 1 条的依据单列**（它依据 MCP 注册面，
  与第 2-4、9-10 条依据的「端点恒 410」是两回事，原建议把它们并为一句会引入新的归因不实）。
- **你 r3 LOW-3**：`:47-48` 外层 except 触发条件已改为「不只由端点抛异常触发」，并按
  审计意见把登记面**扩大一层**——不被锁的不只是文案形态，而是该 `except` 的**存在与捕获宽度**
  （删掉整个 try/except 两条测试同样不红）；同时注明**负控 A 的杀伤力依赖该 handler 仍在**。
  `:56-57` 的归因已拆成两条（内层兜底依据「body 恒为合法 JSON 字节」；回退链依据「detail 恒非空」）。
- **你 r3 LOW-4**：新增第 11 条登记 `str(detail)`，并标【实测-负控 J】。
- **你 r3 ⑤**：`check_backend_health` 的移交条目已写进验收单
  `_bmad-output/验收单/UAT-CARD-T-SWITCHVAULT-2026-09-16.md` §五.6（你上轮说「本轮未取得
  可定位的验收单移交条目，不能确认『已登记』」——现在它可定位了）。
- **你 r3「(g) 证据边界」**：全部裁判已在**最终 SHA** 上重跑并落档（此前绑 `b355f7b7`），
  含你点名的 ruff 格式检查；`tests/unit` 目录级也在最终 SHA 重跑（base=64 / close=64 / diff 空）。

### (3) 审计另外发现、你三轮未点名的几处（已改）

- `:26-27`「硬编码成 `quarantined` **也能全绿**（负控 C 实测）」—— C 组日志实为
  `1 failed / 1 passed`；「全绿」是「若门只剩 token 匹配」的**反事实推论**，从未单独跑过。
  （这与我在 `:61-62` 刚承认过的同一类错误。）
- `:23-24`「**实测** body 只有 `{error, detail}`」—— evidence 目录没有任何存档打印过 body 键集，
  那是**源码事实**；且②断言的是两个具名键**缺席**，不是键集排他。
- `:64-65`「不连……**任何端口**」—— 判据只有 `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS` 一项，
  已收窄为「实测未连现网 Neo4j；其余端口无对应计数器，按源码推导」，并注明该计数只覆盖测试体、
  不覆盖 import 期副作用。
- 第 5 条的「**实测** body 恒为 bytes」—— 负控 D 只证明「`json.loads` 接受了 `result.body`」
  （`str`/`bytearray` 同样通过），推不出类型断言；已拆成「一次探针观测 + 源码推导」。

### 请重点核

1. 上述每一处改写，是否**仍有**比证据更强的地方？（这是本卡连续三轮的失分点）
2. 三级证据标注是否被**如实**使用——有没有哪条标了【实测】却找不到对应记录，
   或标了【源码推导】其实有实测？
3. 「本文件不证明什么」11 条是否仍有遗漏的未覆盖改动？
4. 本轮是否真的没有改动可执行代码？（AST 剥 docstring 后指纹相同，验伪锚为 True）
