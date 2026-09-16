# 复核任务：CARD-RED-HYGIENE（BATCH-2026-09-11-第十四批 · 车道 T10 第 5/5）

你是独立复核者。只读审查，不要修改任何文件。

工作树：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t10-red`
分支：`card/t10-red`
本卡最终 HEAD：**以 `git rev-parse HEAD` 实取为准**（本 prompt 写不进自己之后的 SHA）。
⚠️ **本 prompt 文件所在的 commit 不是 HEAD**：它最后一次改动在 `6d337e96`，其后还有纯 `_bmad-output`
的 commit。所以**不要**把「含本 prompt 的那个 commit」当作最终 HEAD，一律以你自己 `rev-parse` 实取的为准。
本卡 commit 链：`8bfcdfce`（主体）→ `b38e1d04`（只读自审整改）→ `2c740216`（按你 r1 整改）
→ `f28c0f4a`（**零代码**）→ `69c99d1a`（按你 r2 整改）→ `ef21be2c`（按你 r3 整改）
→ `0bc3baef`（按你 r4 整改，**纯 docstring + 文档**）→ `6d337e96`（**纯文档，零代码**）
→ `8ac84933`（**纯文档，零代码**）→ 可能还有一个纯文档 commit（本段更正本身）

⚠️ **轮次账（请以此为准，仓里的存档文件名会让你误判）**：
本轮是 **r6**，但它是**计入 D-15 配额的第 5 轮** —— 因为 **r5 落 0 字节、没有产出任何结论**
（账户级用量配额在报告生成阶段耗尽，进程 `exit=0` 而 stdout 为空）。
`_bmad-output/审查/codex-review-CARD-RED-HYGIENE-r5.md` 这份存档**记录的是「送了、跑了、被打断」
这件事本身，不含任何 findings**，它自己首部也写明「不得被当作 r5 通过或未通过引用」。
⇒ 你在仓里看到 r1..r5 五份存档，但**有结论的只有 r1..r4 四轮**。
⇒ **本轮仍是 D-15 上限那一轮。仍有 HIGH ⇒ 停下交主 session 人审，车道不会再改代码。**

⚠️ **本轮的定位与前四轮不同，请先读这一段再决定怎么分配力气：**
你的 r4（绑 `ef21be2c`）已给出 **BLOCKER 0 / HIGH 0**，并明写「不要求继续改代码送第 5 轮」。
**自 `ef21be2c` 起，本卡的代码行为零改动** —— 之后只动了两样东西：
1. `0bc3baef` 改了 `test_agents_health.py` 的**两个 docstring 块**（按你 r4 MEDIUM-1 撤回
   那句「按其形式即穷尽」的过强声明）。去 docstring 后 `ast.dump` 逐字相同、长度同为 43367
   （证据 `FINAL-d32-equivalence-*.txt`；主 session 已带验伪锚独立复算：不去 docstring 时两侧 AST
   **必须不同**，实测确为不同 ⇒ 该判据没有空转）。按批级裁定 D-32，纯注释/docstring 尾巴不占轮次。
2. 本 commit 只动 `_bmad-output`（文档与存档），**一行代码都没改**。

所以本轮**不是**为了再改代码，而是为了让终审在字面上也绑最终 HEAD，并复核一件
**前四轮都没看过的事**：⓪ 段列的那些「撤回过强声明之后新写下的替代声明」本身成不成立。
若你仍报 MEDIUM/LOW，车道会如实登记移交而不再整改（轮次已到上限）。
`$PREV`（= 同车道上一张卡 CARD-EPW-COVERAGE 的 commit）：`f294878bb677ae54dcbf17277004efa2fa1ef97b`

看改动（对 `$PREV` 的累计代码面 —— 本卡代码改动的全部）：

```
git --no-pager diff --no-color f294878b HEAD -- . ':(exclude)_bmad-output'
```

**本轮相对你 r4 的代码增量（应当只有两个 docstring 块）**：

```
git --no-pager diff --no-color ef21be2c HEAD -- . ':(exclude)_bmad-output'
```

**终审绑定自核（本轮请你自己跑并把结果写进报告）**：

```
git --no-pager diff --no-color <你实际审的 SHA> HEAD -- . ':(exclude)_bmad-output' ; echo "rc=$?"
```

（`':(exclude)…'` 的写法是必需的，本机 git 不认 `':!…'`；`--no-color` 也是必需的 ——
本机多个 worktree 共用同一份 `.git/config`，作业期内 `color.ui` 会被并发改写，
带 ANSI 前缀的输出会让 `grep '^@@'` 之类的判据静默归零。）

---

## ⓪ 你的 r4 已被逐条处置 —— 本轮重点（**请优先看这一节**）

r4（绑 `ef21be2c`）：**BLOCKER 0 / HIGH 0 / MEDIUM 1 / LOW 2**，你明写「不要求继续改代码送第 5 轮」。
逐条处置见 `_bmad-output/审查/evidence-red-hygiene/RESPONSE-codex-r4-20260916.md`。

- **MEDIUM-1（`ctx` 判定并非穷尽）**：**接受，不改代码，改为撤回声明 + 登记移交**。
  `_collect_writes` 的 docstring 里那句穷尽性声明已删，替换为**逐条列出的已知漏面**
  （`match` 捕获的 `MatchStar.name` 是字符串、类体在定义时当场执行而 `_own_nodes` 跳过 `ClassDef` 体、
  `import`/`def`/`except … as` 的名字绑定不经 `ctx`）。
- **LOW-1（新判定新增两种误报）**：接受，同样**登记移交**并写进 docstring，
  且从两种扩写为三种（推导式局部同名变量、无右值的纯注解、切片副本写下标）。
- **LOW-2（回应声称已收窄、原件却还留着旧论证）**：已修（纯文档）。

### ⚠️ 本轮真正要你看的是：**那些「撤回」本身带来的新声明，前四轮谁都没审过**

这是本轮与前四轮唯一的实质差别，也是车道请你重点判的地方：
r4 让车道撤回一句过强声明，车道照做了 —— 但**撤回时顺手写下的替代声明有 6 条可验证的技术主张**
（上面 MEDIUM-1 的 3 类漏面 + LOW-1 的 3 类误报），它们写在 `ef21be2c → 0bc3baef` 的 docstring 里，
**在 r4 之后产生，因此没有任何一轮看过**。按批级口径「不入库的复核不作依据」，
它们在补证之前只是未经检验的自述 —— 把一个未证主张换成另一个未证主张，并不是整改。

主 session 已就此补做三件事，**请逐件独立复核，不要采信车道的转述**：

1. **6 条主张的实测补证** — `_bmad-output/审查/evidence-red-hygiene/FINAL-R5-docstring-claims-*.txt`
   做法：import 入库真 helper（非逻辑副本），复刻 `_production_expected_templates()` 的完整取值三步，
   逐格喂对照输入看 guard 实际裁决，与 docstring 声称的结果对照。实测 **`MISMATCH_COUNT = 0`**
   （8 格：L1/L2/L3a/L3b/L3c 称不红→实测不红；F1/F2/F3 称红→实测红）。
   存档带**同次执行的验伪锚**（已知必红的 `.append()` 实测确为红 ⇒ 那 5 个「不红」不是判据空转），
   并打了 HEAD + 被测文件 HEAD 侧/工作树侧双 `sha256`（两侧相同 ⇒ 跑的是已提交内容）。
   **请判**：(a) 这 8 格喂的对照输入是否真能落到它声称的那条路径上？
   (b) `MISMATCH_COUNT = 0` 有没有可能是探针复刻取值三步时与真实调用点产生了偏差而得来的？
   (c) 这 3 类漏面是否**确实**是门未覆盖的路径（而不是其实会红、docstring 自谦写错了）？

2. **两份 guard 探针存档的版本对应关系被理清** — 验收单 §四-A.13 改写。
   此前验收单只引 `FINAL-R3-guard-shapes-*.txt`（19 格），而那份绑的是 `69c99d1a` 的**旧实现**
   （`_own_statements` / `_iter_write_targets` / `_assert_not_mutated_after_binding`，枚举语句类型），
   在当前 HEAD 上那段代码**已不存在**。绑当前实现的是 `FINAL-R4-guard-shapes-*.txt`（26 格）。
   两版行为确有分叉，实测一例：「纯注解无右值」在旧实现下 `binds=0`（红在「找到 0 处绑定」），
   在当前实现下 `binds=1`（红在「那处绑定不是普通赋值」）—— 都红但红的身份不同。
   §四-A.12 引用的 `guard-ast-shapes-*.txt` 更早，且测的是**逻辑副本**而非入库代码，已降级为过程记录。
   **请判**：这三份存档的版本归属写对了吗？还有没有别处仍在拿绑旧实现的证据说当前行为？

3. **一处过强措辞被撤回** — 验收单 §六.11 原写「使门通过时两者**必然一致**」，
   与同节第 16 条（你 r4 MEDIUM-1 的结论）和代码 docstring 的最终口径直接冲突：
   r4 整改时改了代码 docstring 却漏改验收单。已撤回并写明成因。
   另 `FINAL-R4-guard-shapes-*.txt` 抬头第 2 行仍留着那句已撤回的穷尽性声明，
   已在该文件开头**追加**撤回批注（原文一字未改，正文 26 格逐格自断言，不受该措辞影响）。
   **请判**：仓内还有没有**别的**地方仍在主张那句已撤回的穷尽性声明？
   （这是本卡反复出现的老问题：同一结论抄在多处，改一处漏多处。车道已登记为 §七.16。）

---

## ⓪-bis（背景，r3 的处置摘要，已在 r4 核过，保留供索引）

r3（绑 `69c99d1a`）：**BLOCKER 0 / HIGH 0 / MEDIUM 2 / LOW 3**，维持撤销 r1 HIGH-1。
逐条处置见 `_bmad-output/审查/evidence-red-hygiene/RESPONSE-codex-r3-20260916.md`。

- **MEDIUM-1（第四类漏面 + 你 LOW-1 的切片误报）**：**已修，而且换了方法**。
  前三轮每轮都被你找出没列到的语句形态（下标 `AugAssign` → 多 target → 解包绑定 →
  `with as` 下标 → 推导式 target → 默认参数里的 `.pop()`）—— 车道认为**枚举语句类型追不完**，
  改为**按 Python AST 自带的 `ctx=Store/Del` 判定**：
  `Name`+`Store` 记为绑定；`Subscript`/`Attribute`+`Store/Del` 且根名匹配记为其它写入；
  就地变更方法调用记为其它写入；断言「绑定恰好 1 处且其它写入为空」。
  `_own_nodes()` 跳过嵌套 def/lambda/class 的**函数体**但**仍下钻**其默认参数 / 装饰器 / 基类
  （那是你那条 `def helper(unused=x.pop())` 的落点）。
  你 LOW-1 的误报也一并修了：就地变更方法**只认裸 `Name` 作接收者** ——
  `x[:].reverse()` 改切片副本、`x[0].append()` 改元素，都不算写本体。
  **请重点核这个新判定方式**：(a) 你之前点名的全部形态现在是否都红？
  (b) 有没有**新的误报**（本该通过却红）？(c) `ctx` 这条路本身有没有你能想到的绕不过去的洞？
  车道复验在 `FINAL-R4-guard-shapes-*.txt`：**26 格逐格写死预期并自断言，预期不符 = 0**。
- **MEDIUM-2（自审汇总在 RH-1 改判后仍未重算）**：已修，**第三次**。
  车道复算确认你的 19 / 2 行 / 16 / 15 / 3，并查清自己先前与你差 1 的原因
  （把「未验证」的 RG-3 也算进了翻转；采纳你的严格口径）。
  这次**连计数规则一起写进 §一**并留了历次错值档。「15 + 3 ≠ 18」那句错表述已删。
- **LOW-1**：见 MEDIUM-1 同段。
- **LOW-2（两份红集混写）**：已修。车道独立复算确认你的实数 ——
  integ5 = 65（36 FAILED + 29 ERROR）、EPW = 34、本卡 34；本卡 vs EPW 差集 **0**、
  vs integ5 差集 **31**。已按你的建议拆开引用（EPW 证「红集没变」，integ5 证「现象早于本卡」）。
- **LOW-3（末次地盘证据不在被审 SHA）**：该存档本轮已入库。
  ⚠️ 车道另登记了它的**结构性成因**：收工判据必然晚于最后一个 commit，
  所以「末次判据存档 ∉ 被审 SHA」会反复出现，属批级流程口径问题，建议统一处置。

⚠️ **你 r3 自述未完成独立目录级重跑**（收集前被只读环境的临时目录限制挡住），
车道已在回应里如实转述，**没有**把它当作独立验证。本轮若你的环境仍跑不了目录级，
照实说即可，车道不会把存档复核写成独立运行。

---

## ⓪-bis（背景，r1/r2 的处置摘要，已在后续轮次核过，保留供索引）

你 r2（绑 `2c740216`）给出 **BLOCKER 0 / HIGH 0 / MEDIUM 6 / LOW 3**，并撤销了 r1 的 HIGH-1
（依据是 `$PREV` 已入库的 `evidence-b13-integ/unit-integ5-20260911T010612.txt` 第 597-606 / 1143 行
已有同一条 candidate422、同一指纹、同样 `blocked=1` ⇒ 该现象早于本卡）。
车道接受你对其论证形式的批评，五跑存档结论已收窄。

逐条处置见 `_bmad-output/审查/evidence-red-hygiene/RESPONSE-codex-r2-20260916.md`：

- **MEDIUM-1（guard 仍漏三种写法）**：**已修**（本卡选择修而非登记 —— 那是本卡自己写进去的
  「多 target 被覆盖」逻辑错误，且它让 docstring 里「门通过时声明与运行时必然一致」成了假话）。
  新增 `_root_name()` 把写目标剥到根 `Name`；新增 `_iter_write_targets()` **逐个产出**所有写目标
  并展开元组解包，覆盖 `AugAssign`/`Assign`/`AnnAssign`/`Delete`/`For`/`AsyncFor`/`NamedExpr`
  与八个 list 变更方法。
  **请用你 r2 那套方法复验你点名的三种**（`a[0] += "-x"`、`del a[0], b[0]`、`a[0] = b[0] = "x"`），
  并看看还有没有第四种。车道自己的复验在 `FINAL-R3-guard-shapes-*.txt`：**19 格逐格写死预期、
  由探针自己断言**，退出码反映预期是否兑现（修了你 LOW-1 点的「rc=0 掩盖期望文本错误」）。
  覆盖边界已写进 docstring：别名写入 / 传进函数由被调方改 / `setattr` 等动态手段**看不见**。
- **MEDIUM-2（协议用 `grep -c` 数拦截次数，对 0/1/9 恒得 1）**：车道复核属实，
  **登记移交协议卡**（协议是批级资产、非本卡地盘）。并已注明这条削弱了车道先前引用该判据的力度。
- **MEDIUM-3（自审汇总五项全错）**：**已修**，改为脚本解析实数（18 / 2 行 3 条 / 15 / 15 / 3），
  并写明差异来源；**RH-1 的主 session 自核也被你证伪**，表格改判为成立，
  §四 加了「主 session 逐条自核不是可靠兜底」。你指出的「验证者判不成立的原因只有摘要、
  无 verifier 正文因而未被独立确认」也已如实写入。
- **MEDIUM-4（R2 证据未入库）**：已随 `f28c0f4a` 入库，本轮被审 SHA 包含它们。
- **MEDIUM-5 / MEDIUM-6**：接受，按**不可追认**保留 PARTIAL（第 0 分钟工作树干净 /
  commit1 的 typecheck 执行历史），并在 `minute0-*.txt` 加了撤回指针。
- **LOW-1**：已修，见上（新探针自校验预期）。
- **LOW-2（四处更正没同步到原件）**：四处逐条已同步 ——
  docstring 里那句「增/删/改名/换序任一发生都会红」已撤回并改写为逐条覆盖声明；
  `attribution-*.txt` 撤回「测试文件不在基线即贡献为零」的不足推理、改引你给的 `$PREV` 红集对照；
  `minute0-*.txt` 加 PARTIAL 指针；五跑存档收窄结论（并写明它没有复现协议所述的 nodeid 翻转）。
- **LOW-3（territory 绑旧 SHA、`≤1` 条件与输出不符）**：已修，
  `FINAL-R3-territory-*.txt` 绑本卡最终 SHA，工作树判据改为逐项列出 + 归属说明。

**本轮请特别核**：(a) MEDIUM-1 的修法是否真的闭合（有没有第四种写法漏掉）；
(b) 这次的修改有没有引入新问题；(c) 其余各条的处置是否到位。

---

## ⓪-bis（背景，r1 的处置摘要，已在 r2 核过，此处保留供索引）

你上一轮（绑 `8bfcdfce`）给出 **BLOCKER 0 / HIGH 1 / MEDIUM 3 / LOW 4**。
逐条处置写在 `_bmad-output/审查/evidence-red-hygiene/RESPONSE-codex-r1-20260916.md`。摘要：

- **HIGH-1（目录级不增）**：车道**不自判通过**（D-15 规定车道对 HIGH 只能写理由、由主 session 裁定）。
  车道给的三条理由：① 你第一跑的 33 条 `>` 是你环境 Node 缺 `libllhttp.9.3.dylib`，你已自行归因；
  ② 你第二跑唯一那条 `>` 是 `candidate422`，而协议 `.claude/rules/card-batch-protocol.md` §3 第 79 行
  明确记载这条与 `mock_warning` 是 W4 哨兵红的载体、会在彼此之间翻转，并规定判据
  「绑 `blocked=` 次数 + 失败正文，**不绑 nodeid**」，且你那跑 `blocked=1` 而车道两跑 `blocked=0`；
  ③ 归属侧你自己给了更强证据（`$PREV` 已入库的 `epw-unit-close7.nodeids` 与本卡存档同为 34 条红）。
  **请复核这三条理由是否站得住**，并给出你对该 HIGH 的最终意见。
- **MEDIUM-1（guard 漏「绑定后就地改表」）**：已修。作用域改为只看 `health_check` 自己的语句
  （不下钻嵌套函数）；绑定后的就地修改（`AugAssign` / 下标赋值 / `Delete` / 八个 list 变更方法）
  一律报红；顶层必须是单个函数定义；覆盖声明收窄为「钉住生产在**绑定处声明**的名单」。
  **请用你 r1 那套方法复验**（抽真实 helper、内存替换 `inspect.getsource` 输入），
  尤其确认你演示的 `+= ["new"]` 与 `[0]="renamed"` 现在确实红。
  车道自己的复验落在 `FINAL3-guard-shapes-*.txt`（11 种形态）。
- **MEDIUM-2（第 0 分钟工作树干净证据不足）**：接受，记为**未证实 PARTIAL**，不追认。
- **MEDIUM-3（最终 commit 的 python-typecheck 未被独立证明）**：接受。本轮落盘
  `FINAL-precommit-hooks-*.txt`，并区分该 hook 的两种 skip（glob 不匹配 vs pyright 缺席）：
  实测本卡只有 commit1 暂存了 `backend/app/*.py`，commit2/3 是 glob 型 skip；
  commit1 成功那次的 hook 原始输出没留下，标记**历史 PARTIAL 不追认**。
- **LOW-1**：`_handler_was_not_reached` 的措辞已收窄（零 await 只证明没走到那一次 LLM 调用）。
- **LOW-2**：三处计数/索引/行号已修，含把格式豁免存档的 hunk 跨度收紧为实际被改行
  （`$PREV` 284-286 / `8bfcdfce` 247-249 / 当前 HEAD 250-252）。
- **LOW-3 / LOW-4**：已修（送 r1 之前的自审已同批处理；地盘证据已入库）。

### ⚠️ 本轮的新事实：最终 HEAD 上车道自己也跑出了 `>` = 1，与你 r1 第二跑同形

绑最终 HEAD `2c740216` 的目录级跑（`FINAL-R2-unit-close-*.txt`）实测：

    35 failed / 5165 passed / 35 skipped / 19 xfailed
    '<' = 30，**'>' = 1**
    NEO4J_LIVE_PORT_CONNECT_ATTEMPTS=1 (blocked=1, advisory=0, unaccounted=0)

那条 `>` 是 `tests/unit/test_candidate_service.py::test_accept_candidate_already_accepted_returns_422`，
失败正文首行逐字为

    - ('::1', 7691, 0, 0) on thread MainThread (owner=…test_accept_candidate_already_accepted_returns_422)

即协议 §3 指定的 W4 哨兵指纹（唯一指纹数实测 = 1）。连接**被拦下**（blocked，非 connected），
随后走 JSON 降级。三跑对照：`8bfcdfce` 34/`>`=0/blocked=0；`b38e1d04` 34/`>`=0/blocked=0；
`2c740216` 35/`>`=1/blocked=1。

⇒ 车道**没有**把 `>` = 0 写进验收单，如实记的是「最终 HEAD 这一跑 `>` = 1，该条是哨兵载体」。
**请你判**：这是否就是你 r1 HIGH-1 说的那件事？按协议 §3「绑 blocked= 次数 + 失败正文、
不绑 nodeid」的口径，本卡该不该被这一条拦住？还是说这条口径本身有问题、该另立卡修哨兵归属？
（车道三个 commit 都没碰任何与端口 / Neo4j / conftest 相关的文件，diff 面见上方命令。）

另：送你 r1 之前，本卡先跑过一轮只读多维对抗自审（记录入库
`SELF-REVIEW-adversarial-20260916.md`，23 条 findings，主 session 自核后判 17 条成立）。
**该记录里对自审流程本身的批评（反驳式验证偏松、把严重度混进成立性）也请你核一核是否属实。**

---

## ① 任务与地盘边界

本卡是 RED 卫生收尾卡，做了七件事：

- **(b)** `backend/tests/api/v1/endpoints/test_agents_health.py`：mock 的模板期望表由 12 项对齐到生产的 13 项（生产真相源 = `backend/app/services/agent_service.py` 的 `AgentService.health_check` 内局部变量 `expected_templates`），并把该列表提为类属性 `MockAgentService.EXPECTED_TEMPLATES`；新增一条防漂 guard `test_mock_expected_templates_match_production_truth_source`，用 AST 从生产源码取该字面量与 mock 逐元素比对。
- **(c)** `backend/tests/unit/test_sync_batch_auth.py` 与 `backend/tests/unit/test_system_endpoint_auth.py`：文件头鉴权矩阵中「DEBUG=True + 空 key」那一档由 200 改写为 503（P0-2 加固后的实际行为），并注明例外条件。纯文案改动。
- **(d)** `test_system_endpoint_auth.py`：新增 `TestSystemTestLLMAuthPrecedesHandler` 两条用例，把文件头声称的「dependency runs BEFORE the body handler」变成断言。新增 fixture `auth_client_with_llm_spy` 外露业务替身 `litellm.acompletion` 的句柄；承重用例与对照用例共用谓词 `_handler_was_not_reached`。对照用例只用 `app.dependency_overrides` 摘掉鉴权依赖这一个变量。**不改任何生产源码**。
- **(e)** 两条已知 flaky（`test_candidate_service.py::test_accept_candidate_already_accepted_returns_422`、`test_mock_degradation_transparency.py::TestMockScoringWarningLogs::test_mock_mode_logs_warning`）只定性、未改。
- **(f)** 退役死配置 `MEMORY_RETRY_BASE_DELAY` / `MEMORY_RETRY_MAX_DELAY`：删 `backend/app/config.py` 两个 Field 与其段注释、删 `backend/.env.example` 对应注释段，同批改 `backend/tests/unit/test_cache_configuration.py`（删整个 `TestMemoryRetryDelayFromSettings` 类、去掉两条真 `Settings` 默认值断言、从 `required_keys` 去掉两键、清掉两行 MagicMock 赋值），另把该文件里 4 处 `config.py:678` 的行号引用改成符号名（因为本卡删了 16 行，该行号已漂到 `:662`）。
- **(g)** `tests/contract/test_node_id_patterns.py::TestNodeIdPatternConsistency::test_pattern_matches_json_schema` 只定性、未改。
- **(h)** 地盘硬约束：**只允许改这 6 个文件**

  ```
  backend/.env.example
  backend/app/config.py
  backend/tests/api/v1/endpoints/test_agents_health.py
  backend/tests/unit/test_cache_configuration.py
  backend/tests/unit/test_sync_batch_auth.py
  backend/tests/unit/test_system_endpoint_auth.py
  ```

  `backend/app/config.py` 与同批另一条车道（T5）有声明交集：T5 只在该文件**新增** `TASK_CLEANUP_INTERVAL_SECONDS` 且避开 `MEMORY_RETRY` 段，本卡只**删除** `MEMORY_RETRY` 两字段，两侧 hunk 不重叠。

  明确禁改：`agent_service.py` / `agents.py` / `security.py` / `system.py` / `main.py` / `backend/app/models/**` / `specs/**` / 任何 `conftest.py` / `backend/requirements.txt` / 上面两条 flaky 的文件。

---

## ② 要核的判据

证据目录（已入库，可直接读）：`_bmad-output/审查/evidence-red-hygiene/`

1. **第 0 分钟自证**（`minute0-*.txt`）：pwd / 分支 / `$PREV` / 工作树干净 / venv+env / `pyright app` = 0 errors / 红基线 64。
   ⚠️ 该存档「工作树干净」一项卡方已按你 r1 MEDIUM-2 记为**未证实 PARTIAL**、不追认
   （存档只留计数不留 porcelain 原始路径，而空目录本身不计脏项）。请核这个处置是否到位，
   以及是否有别的办法能事后证明或证伪它。

2. **(b) 先红后绿 + 防漂负控**：
   - `agents-health-RED-*.txt` 应显示 2 failed，失败身份为 `assert 12 == 13` 与 `assert 10 == 11`；
   - `agents-health-GREEN-*.txt` 应显示 12 passed；
   - `agents-health-GUARD-GREEN-*.txt` 应显示 13 passed；
   - `agents-health-NEGCTL-rename-*.txt` 是负控输入：把 mock 里一个模板名改名（长度仍 13），期望**只有** guard 那条红、其余 12 条数量判据全绿，跑前跑后 `shasum -a 256` 逐字节相同。
     请判断这个负控是否真的证明了它声称的那件事。

3. **(c)** 两文件里陈述性的旧口径字面量应已清零；请自己 grep 核实，并判断替换后的文案是否与 `backend/app/security.py` 的实际分支行为一致。

4. **(d) 承重断言与对照输入**：
   - `auth-GREEN-*.txt`：两文件合计 19 passed；
   - `auth-NEGCTL-3mutants-*.txt` 是三段负控输入，逐段期望：
     M1 把对照用例的断言方向翻成与承重同向 → **对照**那条红；
     M2 把共用谓词改恒真 → **对照**那条红、承重仍绿；
     M3 把共用谓词改恒假 → **承重**那条红。
     三段跑完还原，跑前跑后 `shasum -a 256` 逐字节相同。
   - 请重点判断：承重那条断言是否可能恒真（即它是否能区分「鉴权确实前置」与「这个替身根本不在被测请求的路径上」）；对照用例只摘掉鉴权依赖是否真的是单变量。

5. **(f) 退役**：
   - census：`git grep` 证 `backend/app` 下生产消费方为 0（卡方的 census 排除了 `_bmad-output` / `.gdr` / `_bmad-archive` / `docs` 四个面——请核这个排除是否掩盖了真消费方）；
   - `cachecfg-RED-*.txt`：删字段后未改测试时应 3 failed（两条真 `Settings` 默认值断言 + 一条 `.env.example` 文档断言）；
   - `cachecfg-GREEN-*.txt`：同批改测试后 9 passed / 4 xfailed；
   - `pyright-after-retire-*.txt`：`pyright app` 仍 `0 errors`。
   - 请核前后测试计数的算术是否与「删了哪几条、修了哪几条」严格对得上，尤其：删掉一条 `xfail(strict=True)` 用例会让 xfailed 计数减一，卡方是否把「删掉」记成了「转绿」。

6. **(h)(i) 地盘与目录级**（⚠️ 以 `FINAL-*` 系列为准；无前缀的旧存档已被取代，多数带自查更正段）：
   - `FINAL-territory-*.txt`：代码面恰好 6 文件；`backend/openapi.json` 与 `$PREV` blob 逐字节相同；
     exclude 验伪锚 36 vs 0；本卡 commit 面含 `stderr` 的 = 0（取名面已按你 r1 的同类批评修正）。
   - `FINAL-R2-unit-close-*.txt` / `FINAL-R2-unit-comm-*.txt`：绑最终 HEAD `2c740216` 的目录级与 comm。
   - `attribution-*.txt`：卡方原先只用「本卡 4 个测试文件不在 BASE 红集」论证归属，
     **你 r1 指出那不充分，卡方已接受**并在存档加了更正段；归属现以你给的对照
     （`$PREV` 已入库的 `epw-unit-close7.nodeids` 与本卡存档同为 34 条红）为准。请复核。

7. **本卡 commit 用了 `LEFTHOOK_EXCLUDE=python-lint,spec-sync-root`**，依据写在 `lefthook-exclude-justification-*.txt`：
   - `python-lint` 依协议 §2.3 的 `ruff format --check` 主干既有漂移过渡条款，卡方声称剩余漂移只在 `test_cache_configuration.py` 且不在本卡改动行上，并已自清了本卡引入的那一处（`test_agents_health.py`）；
   - `spec-sync-root` 的跳过依据是「本卡不改变 OpenAPI 面」；
   - `python-typecheck` **未**放进 `LEFTHOOK_EXCLUDE`；按你 r1 MEDIUM-3，卡方已落盘
     `FINAL-precommit-hooks-*.txt` 并区分该 hook 的两种 skip（glob 不匹配 vs pyright 缺席），
     且把 commit1 成功那次标记为历史 PARTIAL 不追认。
   请独立复核这三条，尤其自己重算一遍格式漂移的**实际被改行**（不是 hunk 跨度），不要采信卡方结论。

8. **证据自身的诚实性**：evidence 目录里有两份文件名带 `SUPERSEDED`，是卡方自查后标注作废的（一份是关于证据的陈述与实际输出矛盾，一份是验伪锚跑挂了却当成锚）。请核它们的作废说明是否诚实、取代它们的文件是否真的修好了那个问题。另请自行检查其余存档里有没有类似的「硬编码结论句与紧邻输出矛盾」。

---

## ③ 最小读取面

- 上述 6 个地盘文件
- `backend/app/services/agent_service.py` 的 `AgentService.health_check`（生产真相源，只读）
- `backend/app/security.py` 的 `require_internal_api_key`（只读）
- `backend/app/api/v1/system.py` 的 `/system/test-llm` handler（只读）
- `backend/tests/contract/test_node_id_patterns.py`（只读）
- `lefthook.yml`（`python-lint` 与 `spec-sync-root` 两节）
- 红基线：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/evidence-b14/unit-red-baseline-08100483.txt`
- `_bmad-output/审查/evidence-red-hygiene/` 全部存档，本轮新增/改动的三份请务必看：
  - `FINAL-R5-docstring-claims-*.txt`（6 条主张的实测补证，本轮新增）
  - `FINAL-R5-unit-close-*.txt`（当前 HEAD 的目录级重跑，本轮新增）
  - `FINAL-R4-guard-shapes-*.txt`（**开头被追加了撤回批注**，原文一字未改）
- 验收单 `_bmad-output/验收单/UAT-CARD-RED-HYGIENE-2026-09-16.md`
  本轮改动的四处：§四-A.12（降级）、§四-A.13（版本对应改写）、§四-A.14（新增）、§六.11（撤回过强措辞）

跑测试用：

```
cd <树>/backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q -p no:cacheprovider <target>
```

⛔ 禁止连 7691 / 7687，禁止写 live vault，禁止修改任何文件。

---

## ④ 反面问题（请逐条正面回答）

1. **(f) 的退役是否漏改了连带消费方？** 除静态引用外，有没有 `getattr` / `model_dump()` / 环境变量注入之类的动态访问路径会在运行期读这两个键？`Settings` 的 `extra` 策略是什么，若某个部署的 `.env` 仍设了这两个键会发生什么？

2. **(d) 的「拒绝时业务替身未被调用」断言是否恒真？** 也就是：如果有人把 patch 目标写错、把端点写错、或让请求在 body 校验阶段就被挡下，这条断言会不会照样绿？对照用例是否足以排除这些情形？对照用例结束时只 `pop` 掉鉴权依赖、保留 `get_settings` 覆盖，会不会污染同文件后续用例？

3. **(b) 的防漂 guard 是否存在门未覆盖的路径？** `_production_expected_templates()` 用 AST 解析生产源码。在什么形态下它会静默取到空表或错的赋值？它的两条断言（`len(...) == 13` 与 `== production`）是否有一条恒真？生产若把该列表改成从常量或文件读取，这条 guard 是会红，还是会以别的异常掩盖过去？

4. **目录级是否真的没有 `>`？** 请自己重跑一次目录级并对基线做差集，不要采信 `unit-comm-*.txt` 的结论。跑法（R-B14-3：`cd backend` 之后 `--ignore` 必须用相对路径）：

   ```
   cd <树>/backend && PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest tests/unit \
     --ignore tests/unit/test_deploy_vault_sh.py -q -p no:cacheprovider
   ```

   基线自证口径：`grep -vc '^#' <基线文件>` 应为 64。

5. **`pyright` 是否被跳过了？** 请核 commit 时 `python-typecheck` 确实实跑并通过，且 `pyright app` 在当前 HEAD 上仍是 `0 errors`。跑法（cwd 必须是 `backend/`，禁止 `| tail -1` 取汇总行）：

   ```
   P=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-v5-lance/backend/.venv/bin/pyright
   ( test -x "$P" || { echo 缺席; exit 1; }; cd <树>/backend && "$P" app 2>&1 | grep -E '^[0-9]+ errors?, ' )
   ```

6. **(e)(g) 的「只定性不改」是否掩盖了本该在本卡处理的事？** 还是说它们确实越出了本卡地盘、登记移交是正确处置？

7. **【本轮新增】撤回一句过强声明之后，新写下的替代声明站得住吗？** 见 ⓪ 段第 1 项。
   具体：docstring 现在列的 3 类漏面（`match` 捕获 / 类体当场执行 / `import`·`def`·`except as` 的名字绑定）
   是否**确实**是门未覆盖的路径？3 类误报（推导式局部同名变量 / 无右值纯注解 / 切片副本写下标）
   是否**确实**会红？主 session 的补证 `FINAL-R5-docstring-claims-*.txt` 报 `MISMATCH_COUNT = 0`，
   但那份探针是**复刻**取值三步而非直接调用 `_production_expected_templates()`
   （后者写死了从 `AgentService.health_check` 取源码，喂不进对照输入）——
   **这个复刻本身有没有与真实调用点产生偏差**，以致 8 格全对是复刻误差而非真实行为？

8. **【本轮新增】仓内还有没有别处仍在主张那句已撤回的穷尽性声明？** 见 ⓪ 段第 3 项。
   本卡已知它至少出现在三处（代码 docstring、`FINAL-R4-guard-shapes-*.txt` 抬头、验收单 §六.11），
   前者已改、后两者已加撤回批注 / 已撤回。**请你独立搜一遍**，看还有没有第四处。
   这是本卡反复栽的同一个坑（同一结论抄在多处、改一处漏多处），车道登记在 §七.16。

9. **【本轮新增】绑旧实现的证据有没有别处仍被当成当前行为引用？** 见 ⓪ 段第 2 项。
   `FINAL-R3-guard-shapes-*.txt`（19 格）绑 `69c99d1a` 的旧实现，当前 HEAD 上那段代码已不存在；
   `guard-ast-shapes-*.txt` 更早且测的是逻辑副本。验收单 §四-A.12 / §四-A.13 已分别降级与改写。
   **请核**：这两份的版本归属现在写对了吗？验收单别处（含 §五 各轮小结、§六、§七）还有没有
   仍拿它们当当前行为的依据？

---

## ⑤ 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 四级分组逐条列出，每条写明：

- 文件与符号名（有行号请一并给，但以符号名为准）
- 你实际跑了什么命令、看到什么输出
- 具体的失败场景：怎样的输入或怎样的后续改动会让它出错
- 建议处置（修 / 登记移交 / 不成立）

最后请单独给一行绑定声明：你本次审查绑定的 SHA，以及
`git --no-pager diff --stat --no-color <你审的SHA> HEAD -- . ':(exclude)_bmad-output'` 是否为空。

⚠️ 上一版 prompt 此处写的是「本轮的目标是绑最终 HEAD `2c740216`」——
那个 SHA 停留在 r2 时期，之后四轮都没更新，**已失实，现更正**：
本轮的目标是**绑 `git rev-parse HEAD` 实取到的那个 SHA**（就是含本 prompt 的这个 commit），
且 BLOCKER = 0、HIGH = 0。**请不要照抄 prompt 里的任何 SHA 当作最终 HEAD，以你实取的为准。**
若你仍判有 HIGH，请写清它是本卡引入的缺陷，还是环境 / 既有 flaky / 协议口径问题
（本轮是第 5 轮 = 上限，仍有 HIGH 将停下交主 session 人审，车道不会再改代码）。

若某一级为 0 条，请显式写「BLOCKER: 0」「HIGH: 0」，不要省略。
