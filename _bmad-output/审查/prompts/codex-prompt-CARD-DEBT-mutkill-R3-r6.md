# 独立复核请求 — CARD-DEBT-mutkill-R3（变异裁决共用判据收口）

## 一 背景与最小读取面

本卡在 git worktree `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools`
（分支 `card/t8-tools`）。被审的是一次对「变异负控 harness 共用裁决器」的收口。

**最小读取面（请只读这些，不要扩散到全仓）**：

1. `git diff dde52775 0e7d7ee7 -- . ':(exclude)_bmad-output'` —— 本卡的全部代码改动（审 SHA = `0e7d7ee7` = 当前 HEAD）；
   其中 `git diff 34473ebd 0e7d7ee7` 是**本轮针对 round-5 的整改**；
2. `backend/scripts/mutation_kill_identity.py` —— 重点看 `_nodeid_shaped` / `_split_unique`
   / `anchor_surface_broken` / `_loc_identity` / `kill_identity` / `RestoreGuard` 区段；
3. `backend/scripts/g33_mutation_gates.py` —— 重点看模块级 `restore_or_keep_exit_code`
   与 `main()` 里的两处调用点、`_verify_restore` 闭包、汇总段（`drift` / `ok_restore` /
   「还原逐字节相同」打印 / rc=3 分支 / `--json` 写块）；
4. `backend/scripts/mutation_verdict_reconcile.py` —— 全文（本卡新增）；
5. `backend/tests/unit/test_mutation_kill_identity_r3.py` —— 全文（本卡新增）；
6. `_bmad-output/审查/evidence-mutkill-r3/` 下：
   - `g32cb-run-*.txt` / `g32ccr1-run-*.txt` —— 两套全量真跑的 stdout（reconcile 的**真实**输入形态）；
   - `synthetic/` —— 合成样本两份（g33 `--json` 形态、g32b stdout 形态）+ 三份坏法样本；
   - `r3-red-*.txt` / `r3-green-*.txt` —— 先红后绿；
   - `r3-negctl-*.txt` —— 七层负控（每层各一个显形点，跑前跑后 shasum）；
   - `reconcile-*.txt` —— reconcile 真跑与五种合成情形。
7. 缺陷原文（本卡要收口的五条）：`_bmad-output/验收单/UAT-CARD-DEBT-mutkill-R2-*.md`
   的 §5.1（两条 HIGH）与 §第 30 条（三条 MEDIUM）。

## 一.5 前五轮的处置（⛔ **用户已明确解除 5 轮上限**，本轮 = r6，目标是 MEDIUM 也清零）

| 轮 | 绑定 | 结果 | 处置 |
|---|---|---|---|
| r1 | `223beed7` | B0 H0 M3 L2 | 五条全部接受并修 |
| r2 | `767f4b6a` | B0 **H1** M3 L0 | 四条全部接受并修（HIGH 是 r1 整改自己引入的回归） |
| r3 | `98edb541` | B0 H0 M2 L1 | 三条全部接受并修 |
| r4 | `991373e5` | B0 H0 M1 L1 | 两条全部接受并修（g32b 分母 6→138） |
| r5 | `34473ebd` | B0 H0 M3 L1 | 四条**全部接受并修**（其中「负控存档只有 17 层」已补跑 19 层） |

⛔ **十八条全部接受，无一条驳回。** 本轮（r6）的三条整改：

- **r5 M-1**：`ast_mutation_count` 的 fail-closed **覆盖到全树**。上一版只扫 `tree.body`，
  嵌套块里的写入（`if True:` / `for` / `try` / 函数内 `global`）既不计数**也不报错** ——
  又一次「少算而不出声」。现在两段判据：① 只在**模块级顶层**认 `= [字面量]` / `+= [字面量]`
  并计数；② **全树扫描**，任何 `MUTATIONS` 的 `Store`/`Del` 写入位不在 ① 之内、或出现
  `MUTATIONS.<就地改动方法>(...)`，一律**抛**。另拒 `*` 展开与链式赋值。
  作者已实测 8 种规避形态全部 fail-closed，四套真实源码仍返回 **138/9/11/18**。
- **r5 M-2**：新增 `_swallowed_cause()`。`RestoreGuard.critical()` 的 `finally` 在**本体已抛
  OSError** 时仍会重试 `restore()`，重试成功就抛**形态干净**的 130，把首次失败盖成
  `__context__` ⇒ 只看退出码分不出「干净信号退出」与「被盖住的失败」。判据：`SystemExit`
  底下压着非 `SystemExit` 异常即**不算**干净退出。⛔ `exc` 本身不是 `SystemExit` 时返回
  `None`（初版漏了这个前置，让普通 `OSError` 也被报成「被退出码盖住」—— 与本轮要修的 LOW
  同病，作者自己在跑测试时抓到并修了）。新增两条用**真实** `RestoreGuard` 复现该时序的单测。
- **r5 L-1**：`_report_final_restore_failure` → `_report_restore_concern(headline, detail_of, verify)`
  —— headline 由**调用方**给，函数不替调用方断言发生了什么。末次还原**成功**、只是本轮早些
  时候有失败被吞时，现在印「末次还原成功, 但本轮早些时候有还原失败被吞」。

现状：单测 **35 passed**；负控 19 层（本轮新增两处修复的负控层待补，见下）；reconcile 坏法 14 种。

**请重点核**：① `ast_mutation_count` 的全树 fail-closed 有没有**反向**问题（把某种合法且可数
的写法误判成不可数）—— 对四套真实源码必须仍是 138/9/11/18；② `_swallowed_cause` 的链遍历：
`raise ... from None`（`__suppress_context__`）、`__cause__` 与 `__context__` 同时存在、
`SystemExit` 套 `SystemExit`、`exc.code` 是 `None`/字符串、`KeyboardInterrupt`（**不是**
`SystemExit` 子类）这些情形下判得对不对；③ `_report_restore_concern` 的两个调用点 headline
是否都与事实一致；④ 十八条整改里有没有哪一条其实只是把问题挪了个地方；⑤ 本卡的三个脚本里
还有没有**任何一处** docstring/注释说得比代码宽（这是本卡的主题）。

## 二 作者自述（请独立核对，不要采信本节）

- **H1**：`_split_unique` 让「整行就是一个无 reason 的 nodeid」这一读法也进同一个候选集，
  于是「截断+reason」与「整行无 reason」两种合法读法并存时 `len(cands) > 1` ⇒ 判不唯一
  ⇒ 调用方判 `HARNESS-ERROR`。读法空间（完整 reason / 参数化 / 无 reason / 括号闭合的
  二义形态）已穷举进 docstring。⚠️ **作者的一条自我更正，请独立核**：初稿写「候选集只增不减 ⇒
  返回值只会 True→False」，实测**推翻** —— 「有 ` - ` 切点」那一族确实只增（方括号成对 ∪ nodeid 形），
  但「无 ` - ` 切点」那一族的判据由「整行方括号成对」换成「整行是 nodeid 形」，两者**互不包含**，
  两个方向都会翻（`a::b[c - d]` True→False 收紧；`a::b[[c]` False→True 放宽，后者由并联的
  `_boundary_ok` 在端到端路径上兜住）。请核这条声明本身是否准确、以及那条放宽有没有真的被兜住。
- **H2**：`kill_identity` 的弱位置分支（`require_gate_file` 且**无** `expect_loc`）新增
  「所有失败 nodeid 都属于目标门」核 —— 该核原先只在 `_loc_identity()` 里、只有传
  `expect_loc` 才跑。边界：只封**弱位置判据自己的承诺**，不触碰 D-28 延期的「具体断言绑定」。
- **M①**：新增 `anchor_surface_broken()`，在 `rc==0 ⇒ SURVIVED` 与「红在门文件之外 ⇒
  SURVIVED」两条早退**之前**判 `HARNESS-ERROR`；`_loc_identity` 的 `stmt:` 指纹除「在不在」
  外**复核命中数恰为 1**（与跑门前的 `check_expect_loc_unique` 同口径）。rc 契约不变：
  锚完好时 `rc==0` 仍是 SURVIVED。
- **M②**：`g33` 的 `restore_or_keep_exit_code` 提为模块级并接受注入回调；末次还原（外层
  `finally`）若新失败，不再被 `_was_exiting` 静默吞掉 —— 先跑还原逐字节自检并打印，再把
  退出码升到 3；非末次失败仍吞异常保号但返回 `False` 记账，汇总段的 `ok_restore` 把它算进去。
  「首次信号 130 保号」约定不变（还原成功时控制流一动不动）。
- **M③**：新增 `mutation_verdict_reconcile.py`，按**各套实际输出形态**取六档（g33 读
  `--json` 的 `verdict_counts`；g32b/g32cb/g32ccr1 三套实测**无** `--json`/`verdict_counts`，
  只能解析其 stdout 汇总段，三套形态互异故正则按套写）。分母由本工具**自己用 AST 从该套
  源码现算** `len(MUTATIONS)`（g32b 6 / g32cb 9 / g32ccr1 11 / g33 18），不采信存档自称的
  `total`。逐档硬比四个数：逐档相加 / 该套印出来的六档之和 / 该套自称分母 / AST 现算条数。
  缺档键、声明了却缺输入、文件不存在、解析不到六档 ⇒ `SystemExit`（非零 rc）。

## 三 按重要性排序的问题

0. **H1 是否真的覆盖了「读法空间」这个性质，而不是换个方向又漏一类读法？**
   `_nodeid_shaped` 的两条结构约束（参数段之前不含空白；有参数段时以 `]` 收尾）是否有
   反例：某个 pytest 真能产出的 nodeid 被它判成「不是 nodeid 形」，或某个非法 nodeid 被判成是？
   候选判据取并集是否真的做到了「只增不减」（有没有哪条输入在改动后从 False 翻成 True）？
1. **H2 的「所有失败属目标门」核是否在无 `expect_loc` 的弱位置路径上真的生效**？它与
   D-28 延期的「具体断言绑定」的边界是否清晰、有没有实际上越过 D-28 去动了 `expect_loc` 语义？
   这条收紧会不会把**本来正当**的 KILLED（例如参数化门产生多条同门失败）误判成 HARNESS-ERROR？
2. **M① 的改动是否误伤了 rc=0 的正常 SURVIVED 结论**？`anchor_surface_broken` 只在
   `expect_loc` 以 `stmt:` 开头时才动作，这个前置条件是否足够（`require_gate_file` 但
   `expect_loc is None` 的三套会不会被波及）？`stmt_fingerprints` 的缓存（`_FP_CACHE`）
   在锚检查里被提前触发，是否改变了后续 `_loc_identity` 看到的指纹表？
3. **M② 是否仍保住「首次信号 130 保号」同时让末次新失败浮出**？把退出码从 130 升到 3
   是否恰当（还是应当保 130 并另行标记）？`_verify_restore` 在末次失败路径里被调用时，
   `baseline` / `_TARGET_FILES` 是否一定已经绑定好？SHA 检查的早退次序有没有被破坏？
   `restore_failures` 进入 `ok_restore` 后，会不会让**正常**跑法出现新的 rc=3 假红？
4. **reconcile 是否真做到「不统计自己重解析的裁决结果」（避免自证恒真）**？尤其：
   - 「三套只有 stdout、只有 g33 有 `--json`/`verdict_counts`」这一实况是否被如实处理；
   - AST 现算的独立分母是否**真的参与了比较**而非装饰（`synthetic/g32b-stdout-bad-denominator.txt`
     是一份内部完全自洽 5/5/5 的样本，只有 AST=6 这一维能抓到它）；
   - `--expect` 声明了却缺输入时是否确实非零 rc；
   - 三套的 KILLED 行形态互异，正则有没有把 g32b 的「KILLED 合计」那一行误吃成一档或多算；
   - `_one()` 要求每种形态恰好命中 1 次，对真实 tee（可能含逐条进度行）是否会误报。
5. **负控是否每段只拆一层防线**？对照输入是否落在门**未覆盖**的路径上，而不是门的已覆盖面？
   特别请核：作者在首轮负控里发现 `m1b`（拆掉 `_loc_identity` 的命中数核）**没有让任何
   测试变红**，因而补了两条直接打在 `_loc_identity` / `anchor_surface_broken` 本体上的
   用例。这个处置是否恰当，还有没有别的「两层冗余、拆一层不红」的面没被发现？

## 四 输出格式

按 `BLOCKER` / `HIGH` / `MEDIUM` / `LOW` 分级，每条给：
`<级别> <一句话结论> — <file:line> — <一句复现思路>`。
末尾给一行计数：`BLOCKER=n HIGH=n MEDIUM=n LOW=n`。

## 五 边界

- **只读**：不要修改任何文件，不要跑 pytest，不要连数据库（Neo4j 7691/7687 / LanceDB）。
- 不评 D-28 延期的 `expect_loc` 具体断言绑定（那是下一张卡 T8-C 的面）。
- 不评 `g32cb` / `g32ccr1` / `g32b` 三套里同型「末次还原吞没」的四套统一（本卡只修 g33 +
  census，四套统一已移交台账）。
- ⚠️ **本卡按主 session 裁定 R-B14-9 有意不跑两套全量**：`g33` 本卡只跑 `--selfcheck-syntax`，
  `g32b` 最多只可能有排除 M5 的部分跑（预期 rc=4；任一 HARNESS-ERROR 时 rc=2；且部分跑
  **不产出六档聚合表**）。原因是这两套的 `MUTATIONS` 都含**就地变异** `canvas-vault/.claude/
  scripts/fsrs_bridge.py` 的条目，而该文件受「零写者铁律」保护（它是 live 复习链的部署对账
  文件，被改一个字节整条复习链 exit 78 停摆）。**因此本卡没有这两套的全量存档，reconcile
  对其形态只有合成样本覆盖 —— 请按此前提评判覆盖面，不要把「缺这两份存档」当成本卡的疏漏。**
- 承重的全量真跑只有 `g32cb` + `g32ccr1` 两套（这两套实测不含 `fsrs_bridge` / `decay_beta`）。
