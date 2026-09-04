# UAT · CARD-CX-G6-2b-R1 — X2 `92734207` 补审（代际因果锚 + AST 门根名/豁免判定）

> 批次标记 `[BATCH-2026-09-05-第十一批 / CARD-CX-G6-2b-R1]`
> 车道 `card-x2-g62b`（分支 `card/x2-g62b`，开工 HEAD `59286a0a`，已预合主干 `304f03ca`）
> 日期 2026-09-05

---

## 1. 🎯 一句话目标

上一批有一处改动**没有经过任何第三方检查就合进去了**，这张卡专门回头把它查一遍——
查完发现的问题当场补上，查不动的地方如实写下来。

---

## 2. 📖 你的视角

作为项目负责人，我想知道「那处没人复查过的改动到底靠不靠谱」，
以便决定它能不能继续留在主干上、后面几张卡能不能放心接着改它。

---

## 3. 🖥️ 交互流程

本卡**不改变任何界面行为**。复习总览页该怎么用还怎么用：
打开页面 → 看到各科目的待复习数字 → 点「刷新」→ 先显示"正在同步最新数字"→
数字真的更新后才显示"已重建 · 数字已更新"。

这条流程本身是上一批做的；本卡只是核对它在各种时机下都说真话，没有动它。

---

## 4-A. 🤖 Claude 已代验（技术断言全在这段）

### 裁判命令

| # | 命令 | 结果 |
|---|---|---|
| 1 | `pytest -q tests/unit/test_review_app.py tests/unit/test_review_overview.py` | **146 passed**（开工基线 143，+3 新探针，只增不减）✅ |
| 2 | 三条点名门（`module_imports_are_closed` / `stale_get_cannot_settle` / `causal_anchor_survives_same_millisecond`） | **3 passed** ✅ |
| 3 | 负控（换入 `27e61454` → 同毫秒门红 → 还原） | 三段 sha 齐全，还原逐字节相同 ✅ |
| 4 | `grep -c 'with TestClient'` 三文件 | `0 / 0 / 0` ✅（不起 lifespan） |
| 5 | `pytest -q tests/api` | 1 failed / 267 passed；该红**在 HEAD 版上同样复现**（实测，非推断）→ 主干既有 ✅ |
| — | `NEO4J_LIVE_PORT_CONNECT_ATTEMPTS` | 每次跑都是 `0 (blocked=0, advisory=0, unaccounted=0)` ✅ 未连 7691 |
| — | `ruff check` / `ruff format --diff` | `All checks passed` / `1 file already formatted` ✅ |

### (a) 代际判据三前提 — 逐条落 file:line

判据行 **`review_app.py:402`**：
`if (startGen !== undefined && n.gen !== undefined && startGen <= n.gen) continue;`
（台账原记 `:397`，实测那是注释行 → **锚点需更正**，见 §台账待登记条目）

| 前提 | 结论 | 证据 |
|---|---|---|
| ① `state.pollGen` 严格递增、无其他写点 | **成立** | 全文 `pollGen` 仅 6 处（`:345 :397 :442 :449 :472 :508`），其中**赋值形态只有 2 处**：`:345` 初始化 `pollGen: 0`、`:442` `const gen = ++state.pollGen`（前缀自增）。`state` 在 `:345` 是 `const`，全文无 `= state` 别名、无 `Object.assign`。→ 唯一写点 `:442`，步长 +1 |
| ② `:508` 的 `n.gen` 是「已启动的最新 GET 代际」 | **成立，但比卡文表述更强** | `:508` 位于 `await fetch(URLS.refresh…)`（`:499`）**之后**，读到的是 **POST 响应返回那一刻**的 `state.pollGen`，不是「发 POST 那一刻」。两说在「POST 在飞期间又启动一轮 GET」时预测**相反**，跑了判别实验：`evidence-g62b/prem2-gen-semantics.md`（node 退出码 0，TAP `pass=2 fail=0 skipped=0`）。**代码这一侧是对的**；`:507` 的注释措辞（「发 POST 这一刻」）描述的是有缺陷的那一说 → 登记，见 §本卡未证明什么 |
| ③ `document.hidden` 时 pending 不永久饿死 | **成立，且有行为门守** | 链路：`:511` 隐藏时不发 GET → `:434` `schedule()` 隐藏时不排程 → `:481-485` `visibilitychange` → `:212-215` `visibilityAction(false)` 返回 `{cancelTimer:true, pollNow:true}` → `:484` `poll()` → `:442` 新代际必 > `n.gen`（由前提①）→ 结算。行为门：`test_js_hidden_rebuilt_defers_get_and_own_key_status_meta` 第一 case 实测「回前台后的 poll 完成结算」；失败分支同样过判据（`:473` 传 `gen`），结算为"同步失败"而非饿死 |

### (b) 负控 — 用真实上一版而非手工变异体

`evidence-g62b/negative-control-27e61454.md`。`27e61454 → HEAD` 的 `review_app.py`
差异**只有代际锚这一件事**（5 个耦合点全覆盖、无夹带）→ 红绿变化可唯一归因。

| 阶段 | sha256（前 16） | 校验 |
|---|---|---|
| 换入前（当前版） | `b7e4a8d94f82b1a6…` | — |
| 换入后（`27e61454` 版） | `4ff348f19d608290…` | 与 `git show` 的 sha **相同** ✅（确实换成了那一版）；与换入前**不同** ✅（换入真的生效） |
| 还原后 | `b7e4a8d94f82b1a6…` | 与换入前**逐字节相同** ✅ |

红绿：换入后 `module_imports_are_closed` **绿**、`stale_get_cannot_settle` **绿**、
`causal_anchor_survives_same_millisecond` **红** → 同毫秒门有**独有承重**（不被既有两门覆盖）。
拒因身份精确到断言原文：`同毫秒不是「更晚」— pending 必须留着`。
还原用 `trap … EXIT INT TERM`（只挂 EXIT 挡不住 SIGTERM）。

### (c) AST 门四条新补面 — 各一探针

`evidence-g62b/probe-r1.md`（16 条新探针 + 5 组定向变异，脚本自检 rc=0）。

**方法说明**：既有 `probe-matrix.md` 用**基线 commit** 的门做「改前」对照，只能回答
「这条面是不是新补的」；一条探针可被两条规则同时拦下，那样分辨不出**假承重**。
本卡补的是**定向变异**：拆掉被点名的那几行，看指定探针是否由红转绿，同批**对照探针**
必须仍红（否则说明变异把门整个弄坏了，「承重」成了平凡真命题），另有变异体自身的
验伪锚（拆一条规则不该让真实源码变红）。变异全程只在**内存字符串**上做，跑完对两个
源文件做 sha256 前后比对自证——磁盘一个字节没碰。

| # | 面 | 实测 | 处置 |
|---|---|---|---|
| ① | **洞①** `_root_name` 根非 `Name` 返回空串 → 写路径 fail-open | `_js_json(1).dumps = f` / `(json or list).dumps = f` / `(json if _PAGE_TEMPLATE else list).dumps = f` **三条全部放行**；对照「根是 Name」(`_STATUS_META.dumps = f`) 被拒 → 放行确实来自"取不到根"而非"整条规则不存在" | **收紧**（理由见下） |
| ② | `MatchAs` / `MatchStar` / `MatchMapping.rest` 绑定名不产生 Store 位置 Name | 变异 `C2` 拆掉这三条 → 三条 match 探针**全部由红转绿**；对照 `for-目标` / `海象` 仍红 | 独家承重 ✅ 无需改 |
| ③ | `global` / `nonlocal` 声明 + 赋值 | 四种形态实测：`global`+赋值 / `global`+`for` 绑定 / `global`+`del` / `nonlocal`+赋值 **全部被拒**（拒因均为「受保护名」）；`global` 纯声明不赋值**放行** | **无独立漏洞面**。`ast.Global`/`ast.Nonlocal` 没有专门检查是**正确**的：声明本身不改变任何绑定，真正改绑定的赋值/for/del 各自已被抓 |
| ④ | 装饰器穷举漏 `ast.Attribute` 链式 | `@request.app.router.get` **放行**（尾 attr `get` ∈ `_ALLOWED_CALL_ATTRS`、根名 `request` ∈ `_ALLOWED_RECEIVERS`，**中间层 `.app.router` 无人校验**）；同一串表达式**作为调用** `request.app.router.get()` 被拒（Call 分支用 `ast.unparse` 全路径比对）→ 两条分支**口径不一致** | **登记**（理由见下） |

**洞① 选「收紧」的理由**：它是**可绕过白名单**的实证通道——`(json or list).dumps = …`
不留别名、不产生任何保护名的 Store 位置，改掉的却是 `json.dumps` 本体（`json` 为真值）；
严重度高于只会误拒的洞②。收紧**刻意落在黑名单那个消费点**（`_flag_targets` 的
`elif` 支）而**不改 `_root_name` 本体**：同一个空串在装饰器接收者、`request` 注解
那两个**白名单**语境里已经是 fail-closed，改共用函数会把两处正确行为一起改坏。
配套变异 `C1b` 证明收紧那几行**独家承重**（拆掉 → 三条探针放行 = 复现收紧前行为；
对照「根可解析」两条仍红）。

**洞④ 选「登记」的理由**：方向上它**不放宽已有防线**（收紧前后都放行），是一处
**口径不一致**而非新引入的洞；改它等于统一装饰器分支与 Call 分支的接收者判定口径，
需要它自己的一组正反探针（哪些链式接收者算合法），超出只读复核卡范围。

### (d) 洞② request 豁免适用面 — 只改声明不改判据

四种在 FastAPI 里同样合法的写法**全部判红**（拒因均为「受保护名 `request` 被参数遮蔽」）：

| 写法 | `_root_name` 取到 | 结果 |
|---|---|---|
| `request: fastapi.Request` | `"fastapi"` | 🔴 误拒 |
| `request: Annotated[Request, None]` | `"Annotated"` | 🔴 误拒 |
| `request: Annotated[Request, Depends()]` | `"Annotated"` | 🔴 误拒 |
| `request: "Request"` | `""`（Constant） | 🔴 误拒 |
| `request: Request`（对照，唯一被豁免的写法） | `"Request"` | ✅ 放行 |

方向是**误拒不是漏网** → 不阻断。结论写进 `:481` 上方注释，**判据一个字未改**。

> 附带更正一条我自己的预期：写探针前我以为 `Annotated[Request, Depends()]` 会先撞
> 「白名单外调用」（`Depends` 不在白名单），实测拒因**就是**参数遮蔽——`ast.walk` 是
> BFS，`FunctionDef` 先于其子节点 `Call` 出队。卡文点名的原样写法因此**直接**落在洞②上。

### (e) `:503` 重复定义收口真承重

变异 `E-dupes收口`（拆掉 `dupes = sorted(...)` + `assert not dupes` 两行）：

| 探针 | 角色 | 变异前 | 变异后 |
|---|---|---|---|
| `重复定义-def`（模块级第二次 `def _js_json`） | 被测 | 🔴 `受保护名有多个模块级定义点: ['_js_json']` | ✅ 放行 |
| `重复定义-模板`（第二次 `_PAGE_TEMPLATE = "..."`） | 被测 | 🔴 `…: ['_PAGE_TEMPLATE']` | ✅ 放行 |
| `重复定义-class` | 对照 | 🔴 def/class 名遮蔽 | 🔴 仍红 |
| `模块级覆盖-import名` | 对照 | 🔴 受保护名被重绑定 | 🔴 仍红 |

→ 这两行**独家承重**，且变异没把门整个弄坏 ✅

### (f)(g) 外部复核 — **未达成，阻断在环境**

⛔ **`gpt-6-astra` 在本机跑不起来**，两轮均 0 字节：

```
ERROR: {"type":"error","status":400,"error":{"type":"invalid_request_error",
"message":"The 'gpt-6-astra' model requires a newer version of Codex.
Please upgrade to the latest app or CLI and try again."}}
```

本机 `codex-cli 0.147.0`（`/opt/homebrew/bin/codex`）。这是**第四种 0 字节成因**——
既不是 stdin 挂起、不是内容被拦、也不是网络，而是**CLI 版本旧于服务端要求的模型**。
两轮同样 400 = 确定性错误，不是抖动（协议要求的"重发一次"已执行）。

**我没有擅自升级 codex CLI**：它是 homebrew 全局二进制，第十一批还有 6 个车道在并行
使用，升级属于跨 session 影响的环境变更，需要你点头。→ 见 §待你裁决。

prompt 已按五分节写好并通过 cyber 触发词自检（`构造/可复现/打穿/绕过/规避/攻击` 计数
全 0，被弃用的旧模型名计数 0），存 `_bmad-output/审查/prompts/codex-prompt-CARD-CX-G6-2b-R1.md`
（5383 字符），环境修好后可直接重跑。

### (h) 不改代际语义

`review_app.py` **一个字节未改**——三个证据脚本各自做了 sha256 前后比对，
`git diff --stat HEAD -- backend/` 显示代码树改动面**只有** `test_review_app.py`
**+34 行 / 0 删除**。

---

## 4-B. 👤 你来验

**这一轮对你来说没有变化。**

我没有改任何你看得见的东西——复习页面的样子、按钮、数字、提示文字，全都和昨天一样。
这一轮做的是「把上次自己改的东西请第三方看一遍」，属于回头检查，不是新功能。

如果你想花一分钟确认它确实没坏：

- [ ] 我打开复习总览页 → 我看到各科目的待复习数字照常显示 → 我感觉和以前一样，没有异样
- [ ] 我点某一科的「刷新」→ 我看到先出现"正在同步最新数字"，过一会儿变成"已重建 · 数字已更新"
      → 我感觉它是等真的弄完了才报喜，不是嘴上说说
- [ ] 我在刷新过程中切到别的窗口再切回来 → 我看到那条提示最终仍然变成了"已更新"
      → 我感觉它没有把我晾在"正在同步"上不管

三条都对上 = 没坏。有任何一条不对，在下面批注区写一句就行。

---

## 5. 🚦 验收结果

| 完成条件 | 状态 |
|---|---|
| (a) 三前提逐条证明落 file:line | ✅ 达成（前提② 附带查出注释与代码的语义分歧，代码正确） |
| (b) 负控用真实上一版 + 三段 sha | ✅ 达成 |
| (c) 四条新补面各一探针 + 洞① 二选一 | ✅ 达成（洞① 选**收紧**并落地 +3 探针；②③④ 结论见上表） |
| (d) 洞② 三种合法写法探针 + 只改声明 | ✅ 达成（做了四种，判据未动） |
| (e) `:503` 重复定义收口真承重 | ✅ 达成（定向变异，改前红改后绿 + 对照仍红） |
| (f) 一轮 Codex（gpt-6-astra ultra） | ⛔ **未达成** — 本机 CLI 版本不支持该模型，两轮均 400 |
| (g) Codex 每条先实测再采信 | ⛔ **不适用** — 无报告可采信 |
| (h) 不改代际语义 | ✅ 达成（`review_app.py` 零字节改动） |

**结论：6/8 达成，(f)(g) 阻断在环境而非工作面。**
卡的其余部分可独立成立（收紧、探针、负控、三前提证明都不依赖外审），
但**卡的核心目的「补上零外审」没有达成**——这一点不能含糊过去。

---

## 6. 📝 批注区

> [!question]+ 待你裁决
>
> **D-1｜codex CLI 升级（批级问题，不只本卡）** — 本机 `codex-cli 0.147.0` 跑
> `gpt-6-astra` 被服务端 400 拒。**且本机 codex 的默认模型就是 `gpt-6-astra`**
> （探测所见：`model: gpt-6-astra / reasoning effort: ultra`）——所以「不指定 `-m`
> 用默认模型」这条退路**不存在**，默认走的正是那个跑不起来的模型。三个选项，我倾向 **甲**：
> - **甲**：由你升级 homebrew 的 codex（`brew upgrade codex`），我随后重跑本卡
>   prompt 补上外审。它是全局二进制、第十一批 6 个车道在并行用，升级属跨 session
>   环境变更，所以我没自己动手。
> - **乙**：显式指定一个旧模型跑一次。但你 2026-09-05 刚裁定统一 `gpt-6-astra`
>   并要求新卡文里那个旧模型名的计数为 0——乙等于显式退回你已弃用的那个，我不推荐。
> - **丙**：本卡按人审替代收工，X2 的代码面**继续挂着"零外审"**，等环境修好再补。
>
> ⚠ 无论选哪个：**其余车道的 Codex 复核会撞同一个 400**，这是批级问题。
>
> **D-2｜洞④ 装饰器口径不一致的定级** — 无括号装饰器 `@a.b.c.get` 只校验尾部方法名 +
> 根名，而同一表达式作调用会被全路径比对拒。我定为**登记不修**（不放宽已有防线、
> 修它需要另一组正反探针）。若你认为该在本批修掉，请改判。
>
> **D-3｜`review_app.py:507` 注释措辞** — 注释说「发 POST 这一刻」，代码实际取
> 「POST 返回那一刻」，实验证明代码那一侧才对。我**没改注释**（本卡硬边界是
> `review_app.py` 零改动，且 Z1-B/C/D 就要改这个文件）。建议由 Z1-B 顺手改正。

> [!tip]+ 你可以只回一句
> 「D-1 选甲/乙/丙，D-2 D-3 按默认」就够了。

---

## 7. 🔗 技术 spec 引用

- 卡文：`_bmad-output/implementation-artifacts/goal-cards/第十一批-goals/Z1-A.md`
- 协议：`.claude/rules/card-batch-protocol.md`
- 被审对象：`git show 92734207 -- backend/app/api/v1/endpoints/review_app.py backend/tests/unit/test_review_app.py`
- 本卡改动：`git -c core.quotepath=false diff <本卡 commit>^ <本卡 commit> -- backend/`
- 证据：
  - `_bmad-output/审查/evidence-g62b/probe-r1.md` + `probe_r1.py`（新探针 + 定向变异）
  - `_bmad-output/审查/evidence-g62b/prem2-gen-semantics.md` + `probe_r1_gen.py`（前提② 判别实验）
  - `_bmad-output/审查/evidence-g62b/negative-control-27e61454.md`（负控三段 sha）
  - `_bmad-output/审查/evidence-g62b/probe-matrix.md`（上一批矩阵，本卡重跑后 42 条负向全绿）
- Codex prompt（待环境修复后可直接重跑）：
  `_bmad-output/审查/prompts/codex-prompt-CARD-CX-G6-2b-R1.md`
- 失败证据（摘录入库；`*.stderr` 按协议不入库，原件留在工作树）：
  `_bmad-output/审查/codex-review-CARD-CX-G6-2b-R1-FAILED.md`

---

## ⛔ 本卡未证明什么

1. **`92734207` 的代码面仍然零外部复审。** 这是本卡存在的理由，也是本卡**没做到**的
   那一条。下面所有结论都出自我自己的实测，没有第三方对抗过。
2. **洞④（装饰器链式接收者口径不一致）只登记未修**——`@request.app.router.get` 形态
   当前仍放行。我没有证明"它不会被用到"，只证明了"它不是本批新引入的"。
3. **洞②（request 注解豁免面窄）只声明未改**——四种合法 FastAPI 写法当前会被误拒。
   我没有验证"收宽之后不会引入漏网"，那需要它自己的反向探针集。
4. **`:507` 注释与代码的语义分歧未修**——我证明了代码那一侧正确，但注释仍留在文件里，
   后人若把它当规格照改会引入缺陷（本卡的判别实验会在那时变红，算是留了个哨兵）。
5. **前提① 是源码事实，不是行为门。** `pollGen` 只有两个写点靠 grep + `const` 论证，
   没有一道门会在将来有人加第三个写点时变红。
6. **代际锚在真实浏览器里没跑过。** 全部 JS 断言都在 node 沙箱（stub document/fetch/
   timer）里，不是 Chrome/Safari 的真实事件循环与网络栈。
7. **`tests/api` 那条红只证明了"HEAD 版也红"**，没有追它的根因，也没有证明它与
   review 链路无关（只证明了它不是本卡引入）。

---

## 📒 台账待登记条目（本卡不改台账，仅登记）

> 台账 = `_bmad-output/implementation-artifacts/goal-cards/未合卡追踪台账.md`，
> 按协议只有主 session 能改。

1. **X2 行锚点更正**：代际因果锚的判据行是 `review_app.py:402`，
   台账原记的 `:397` 是**注释行**（实测 `sed -n '397,402p'`）。
2. **X2 补审状态**：`CARD-CX-G6-2b-R1` 已完成 (a)(b)(c)(d)(e)(h)，
   **(f)(g) 未达成**——`gpt-6-astra` 在 `codex-cli 0.147.0` 上返回 400，
   两轮均 0 字节。X2 代码面**仍属零外审**，请勿据本卡销掉该标记。
3. **新增待裁决 D-1/D-2/D-3**（见 §6 批注区）。
4. **环境项**：本机 codex CLI 需升级才能执行 2026-09-05 的「统一 `gpt-6-astra` ultra」
   裁定；在升级前，第十一批**其余车道的 Codex 复核会遇到同样的 400**——
   这是批级而非卡级问题，建议主 session 优先处置。
5. **本卡代码树改动面**：`backend/tests/unit/test_review_app.py` **+34 / -0**，
   裁判 1 由 143 → **146 passed**。`review_app.py` 零改动。
