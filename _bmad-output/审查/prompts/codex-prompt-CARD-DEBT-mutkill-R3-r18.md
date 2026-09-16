# 独立复核请求 — CARD-DEBT-mutkill-R3（变异裁决共用判据收口）

## 一 背景与最小读取面

本卡在 git worktree `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools`
（分支 `card/t8-tools`）。被审的是一次对「变异负控 harness 共用裁决器」的收口。

**最小读取面（请只读这些，不要扩散到全仓）**：

1. `git diff dde52775 e7862c4d -- . ':(exclude)_bmad-output'` —— 本卡的全部代码改动（审 SHA = `e7862c4d` = 当前 HEAD）；
   其中 `git diff 371e89a2 e7862c4d` 是**本轮针对 round-17 的整改**；
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

## 一.5 前十七轮的处置（本轮 = r18）

累计 **76 条**：**74 条接受并修，2 条驳回**（round-10 的回滚你在 r9 已认可；round-17 对 r14
HIGH 的驳回你在 r15 已认可）。你已连着三轮 **B0 H0**（r15/r16/r17），r17 还是首轮 **M0**。

**r17 三条 LOW 全修** —— 三条**都是「说得比事实宽」**，正是本卡存在的理由，不因是 LOW 就留：

- **LOW-1**：生成器那条注释写「当实参传出去、调用返回后那个生成器对象再也够不着」——
  你说得对，`it = iter(x for x in MUTATIONS)` 里生成器就是直接实参，而 `iter()` 把它**原样
  返回**，`it.gi_frame` 照样够得着。⇒ 注释改成「只保证**没被直接绑给名字**，不保证调用方
  不会把它还回来（那要知道被调用者干了什么，静态判不出来）」，并指回威胁模型边界。
- **LOW-2**：那条测试**自称**「两族两向各钉一条」，实际只有三条，且把 `FAILED a::b[c - d]`
  标成了「无切点族」（body 里明明有 ` - `）。缺的是**无切点·收紧**（`FAILED a[b]`）。
  ⇒ 不再用注释宣称方向：**把 H1 收口前的判据重新实现一份**，2×2 四格逐格断言「旧 → 新」
  （实测：有切点·收紧 True→False / 有切点·放宽 False→True / 无切点·收紧 True→False /
  无切点·放宽 False→True），并加一条「四格必须各一条」的集合断言。
- **LOW-3**：文件头两处失实 —— 称覆盖**两个**模块（漏了 reconcile 整块）、称「全部 I/O 落
  `tmp_path`」（实际还读四套真实源码、读门文件、起真 pytest 子进程）。⇒ 改成三个模块 +
  按「写 / 读 / 子进程」三类如实列出，保留「不连库、不碰 live vault」的硬声明。

⚠️ **D-32：本轮生产代码是纯注释尾巴** —— `mutation_verdict_reconcile.py` 去 docstring 后
AST 与上一 SHA **完全相同**；`mutation_kill_identity.py` / `g33_mutation_gates.py` **逐字未改**。
实质改动只在单测（补上缺的那一格 + 旧判据重实现 + 文件头更正）。

**你上一轮的证据限制现已闭合**：`evidence-mutkill-r3/r3-negctl-sweep26-20260916T193718.txt`
（绑 `371e89a2`）里 **26/26 层各有独立显形点、0 层无声**，跑前跑后 6 文件 `shasum -a 256`
逐字同，并且**开头就逐层打印了每一层的 `old → new` unified diff 与锚点命中数** ——
「每层只拆一层」现在是你能自己核的事实。两套承重全量在该 SHA 上 rc=0、目标文件 sha 逐字同。

现状：单测 **84 passed**；四套真实分母 138/9/11/18。

**请重点核**：① 三条 LOW 的更正是否与代码逐字相符、有没有改出新的过宽说法；
② 2×2 那张表的「旧判据等价实现」是否真的等价于 H1 收口前的形态；
③ 76 条处置里有没有哪一条只是把问题挪了个地方；④ 还有没有**任何一处**说得比代码宽。

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
  源码现算** `len(MUTATIONS)`（g32b 138 / g32cb 9 / g32ccr1 11 / g33 18），不采信存档自称的
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
