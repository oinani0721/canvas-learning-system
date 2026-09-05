你是一位严格的代码审查者。请对下面这次改动做独立复核，并按 §五 的格式输出。

被审对象是一个 **Python 测试文件里的静态检查器**（用 `ast` 检查同仓另一个模块的源码结构）
和一段 **前端 JS 的状态结算逻辑**。请以「这段检查器/这段状态机是否正确、结论是否被证据
支撑」为准绳审阅。本次需要的是判断与理由，不需要示例代码。

---

## 一 只读文件与命令

工作树根目录（下称 `<树>`）：
`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-x2-g62b`

请只读以下内容（本次复核不需要读别的文件）：

1. `<树>/backend/tests/unit/test_review_app.py` —— 静态检查器本体在
   `_assert_module_closed()`（约 :298-520），白名单在 :239-277，`_root_name()` 在 :286-296，
   探针矩阵 `_AST_PROBES` / `_AST_ALLOWED_SHAPES` 在 :507 之后。
2. `<树>/backend/app/api/v1/endpoints/review_app.py` —— 被检查的模块；其中内联 JS 的
   状态结算在 `settlePendingSync()`（:388-410）、轮询在 `poll()`（:437-479）、
   手动刷新在 `onRefreshClick()`（:506-519）、可见性接线在 :481-485 与 :212-215。
3. 本次改动本身：
   `cd <树> && git -c core.quotepath=false diff HEAD -- backend/`
4. 上一批那次改动（本次复核的前置背景，代码面只有 2 个文件）：
   `cd <树> && git show 92734207 -- backend/app/api/v1/endpoints/review_app.py backend/tests/unit/test_review_app.py`
5. 本次产出的证据文件（结论与实测记录）：
   - `<树>/_bmad-output/审查/evidence-g62b/probe-r1.md`（新探针 + 定向变异承重矩阵）
   - `<树>/_bmad-output/审查/evidence-g62b/prem2-gen-semantics.md`（一个判别实验）
   - `<树>/_bmad-output/审查/evidence-g62b/negative-control-27e61454.md`（负控）
   - `<树>/_bmad-output/审查/evidence-g62b/probe-matrix.md`（上一批留下的红绿矩阵）
   生成这些结论的脚本：同目录 `probe_r1.py` / `probe_r1_gen.py` / `probe_matrix.py`。

复现命令（只读，不写生产文件；三个脚本都在内存里拼字符串，跑完对源文件做 sha256 自证）：

```
cd <树>/backend
PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q -p no:cacheprovider \
  tests/unit/test_review_app.py tests/unit/test_review_overview.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. .venv/bin/python ../_bmad-output/审查/evidence-g62b/probe_r1.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. .venv/bin/python ../_bmad-output/审查/evidence-g62b/probe_r1_gen.py
```

---

## 二 这次改了什么

本卡是**只读复核 + 取证卡**，代码树改动面只有 `backend/tests/unit/test_review_app.py`，
**+34 行 / 0 删除**，三处：

1. **`_flag_targets()` 里收紧了一个 fail-open 面**。原判据是：写位置（Store/Del）的
   `Attribute`/`Subscript`，沿 `.value` 下钻取「根名」，根名在受保护名单里才拒。
   `_root_name()` 在**根不是 `ast.Name`** 时返回空串，而空串永远不在名单里，于是形如
   `(json or list).dumps = …` / `_js_json(1).dumps = …` / `(json if c else list).dumps = …`
   的写路径被放行——它们改的是受保护对象**本体**。新增判据：根名取不到就直接拒。

   收紧刻意**没有**改 `_root_name()` 本体。同一个空串在另外两个消费点（无括号装饰器的
   接收者校验 :440-456、`request` 形参注解校验 :481-483）处于**白名单**语境，空串
   在那里已经是 fail-closed；改共用函数的返回语义会把那两处正确的行为一起改坏。

2. **`_AST_PROBES` 加了 3 条探针**（`根不可解析-*`），锁住上面这条收紧。

3. **`request` 形参注解豁免（:481-483 上方）补了一段适用面声明，判据一个字未改。**
   实测：豁免只认裸 `Name` 形态的 `Request`；`fastapi.Request`、
   `Annotated[Request, None]`、`Annotated[Request, Depends()]`、字符串注解 `"Request"`
   这四种在 FastAPI 里同样合法的写法当前一律判红。方向是误拒而非漏网，故只声明不改。

`review_app.py` **一个字节都没改**（三个证据脚本各自做了 sha256 前后比对）。

上一批 `92734207` 的两件事是本次复核的重点背景：
- 结算的因果锚从「毫秒时间戳比较」换成「轮询代际（严格递增整数）比较」；
- 静态检查器的写路径判定从「看有没有 Store 位置的 Name」换成「看写路径的根名是谁」。

---

## 三 请重点评估（按重要度排列）

**1（最重要）· 代际因果锚的三个前提是否真的成立。**
   结算判据是 `review_app.py:402` 的
   `if (startGen !== undefined && n.gen !== undefined && startGen <= n.gen) continue;`。
   本卡声称：
   - 前提①：`state.pollGen` 只有两个写点——`:345` 初始化 0、`:442` 前缀自增，`state` 是
     `const` 且无别名，因此严格递增；
   - 前提②：`:508` 写入的 `n.gen` 取自 `await fetch(POST)` **之后**的 `state.pollGen`，
     即「POST 响应返回那一刻已启动的最新 GET 代际」。注意 `:507` 的注释写的是「发 POST
     这一刻」——本卡认为**注释描述的语义有缺陷、代码实现的语义才是对的**，并用
     `prem2-gen-semantics.md` 的判别实验支持该结论（实验布置为「POST 在飞期间又启动一轮
     GET」，两种语义在这一情形下预测相反）。请评估该实验设计是否真的能区分两说、
     有没有别的解释；
   - 前提③：页面隐藏时不发 GET，pending 不会永久饿死（回前台 `visibilitychange` 触发的
     poll 代际必然更大）。
   请独立判断这三条，尤其是**有没有第四个前提被漏掉**，以及在乱序响应、并发 POST、
   多 vault 同时 pending、`document.hidden` 中途翻转等情形下判据是否仍然正确。

**2 · 第 1 项那条收紧是否引入了误判（误拒）。**
   反向探针集 `_AST_ALLOWED_SHAPES`（6 条）与「未注入的真实源码必须放行」这条验伪锚
   都在。请判断这 6 条 + 验伪锚是否足以覆盖误拒风险；本模块将来正常演进时，有没有
   合理的写法会被这条新判据挡住。

**3 · 承重结论的方法论是否站得住。**
   `probe-r1.md` 第二段用「定向变异」证明某几行**独家承重**：把被点名的那几行换成
   `pass` / 恒假条件，再看指定探针是否由红转绿，同时要求同批**对照探针**仍然红。
   请评估：这个方法能否被「变异其实把检查器整个弄坏了」蒙混过去；对照探针的选取是否
   恰当；`E-dupes收口`、`C1b-根不可解析收紧`、`C2-match三类绑定`、`C4-装饰器接收者`
   这四组的结论是否都成立。

**4 · 负控的有效性。**
   `negative-control-27e61454.md`：把**真实的上一版实现**（时间戳锚）换回生产文件，
   验证「同毫秒」那道门变红、另外两道门仍绿，再逐字节还原（三段 sha256 都在文档里）。
   请评估这个负控能否支撑「该门有独有承重」这一结论。

**5 · 本卡如实登记的两处，登记得对不对。**
   - 无括号装饰器走 `Attribute` 分支时只校验**尾部方法名 + 根名**，中间层不校验，
     于是 `@request.app.router.get` 通过；而同一串表达式**作为调用**时走的是
     `ast.unparse` 全路径比对，会被拒。两条分支口径不一致——本卡把它记为登记项而非
     修复项，请判断这个定级是否恰当。
   - `request` 注解豁免面窄于合法集（上面 §二 第 3 条），同样只登记不改。

**6 · 其余你认为重要的问题。** 包括但不限于：证据文件里有没有「结论比证据宽」的表述、
   哪条断言其实没有被任何门守住、脚本自身的判据有没有可能假绿。

---

## 四 已裁决，不必再计入

以下几项已由项目负责人裁定，请**不要**作为 BLOCKER/HIGH 重复提出（如发现新的事实性
错误仍请指出）：

- **D-4**（X5-C：M4 orphan 权威口径）——维持登记，留待下一批处理。
- **D-5**（X7-B：D1-D7，含「深层值不再是合法值」的契约变更与 SKILL.md 零改动口径）
  ——全部按验收单默认裁定。
- **`request` 注解豁免面窄于合法集**（§三 第 5 条后半）——本卡已裁定为「只声明适用面、
  不动判据」，理由是方向为误拒而非漏网，且收宽豁免面需要它自己的一套反向探针，归后续卡。
- **`review_app.py:507` 的注释措辞**与代码实际不一致——本卡已裁定「只登记、不改」，
  理由是本卡为只读复核卡且同车道后续卡就要改这个文件。
- 本卡**不改**因果锚的语义（不许改回时间戳、不许引入第二套锚），这是卡的硬边界。
- 三张调用白名单与接收者白名单（`_ALLOWED_CALL_NAMES` / `_ALLOWED_CALL_ATTRS` /
  `_ALLOWED_RECEIVERS` / `_ALLOWED_IMPORTS`）**不得放宽**，也是硬边界。

---

## 五 输出格式

请用中文，按下面的结构输出：

```
## 结论摘要
（3-5 句）

## 逐条发现
### [BLOCKER|HIGH|MEDIUM|LOW] <一句话标题>
- 位置: <file:line>
- 事实: <你实际读到/跑到的证据，不要复述本 prompt 的说法>
- 影响: <会导致什么后果>
- 建议: <怎么改；若认为不必改请说明理由>

## §三 六个问题的逐项答复
（每项一段，明确给出「成立 / 不成立 / 部分成立」的判断）

## 我没有验证的部分
（如实列出你没跑、没读、或无法判断的内容）

BLOCKER/HIGH 清零：是/否
```

最后一行必须**逐字**是 `BLOCKER/HIGH 清零：是` 或 `BLOCKER/HIGH 清零：否`。
