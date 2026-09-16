# 独立复核请求 — CARD-DEBT-mutkill-R3（变异裁决共用判据收口）

## 一 背景与最小读取面

本卡在 git worktree `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-t8-tools`
（分支 `card/t8-tools`）。被审的是一次对「变异负控 harness 共用裁决器」的收口。

**最小读取面（请只读这些，不要扩散到全仓）**：

1. `git diff dde52775 371e89a2 -- . ':(exclude)_bmad-output'` —— 本卡的全部代码改动（审 SHA = `371e89a2` = 当前 HEAD）；
   其中 `git diff dd49dff0 371e89a2` 是**本轮针对 round-16 的整改**；
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

## 一.5 前十六轮的处置（本轮 = r17）

累计 **73 条**：**71 条接受并修，2 条驳回**（round-10 的回滚你在 r9 已认可；round-17 对 r14
HIGH 的驳回**你在 r15 已认可**）。你连着两轮 **B0 H0**（r15、r16）。

**r16 三条全修**：

- **MEDIUM**：推导式白名单要分**急/惰**。`[x for x in MUTATIONS]`/`{…}`/`{k: v …}` 当场
  求值，求完没有活着的帧；**生成器表达式**把 `iter(MUTATIONS)` 存进自己的帧，
  `it.gi_frame.f_locals[".0"].__reduce__()[1][0].append(4)` 拿得回原列表（实测运行时 4 条）。
  ⇒ 生成器表达式只在**没被绑走**（父节点是 `Call`）时才认。⚠️ 四套实测三处生成器表达式
  全是直接实参（`sorted` / `next` / `collections.Counter`），不挡现有写法；⚠️ 故意**不**要求
  「被调用者是消耗型内建」—— `collections.Counter` 是 `Attribute`，那样写会把 g32b 打死。
- **LOW-1**：「字符串字段 ⇒ 不是读取位」的**措辞**比判据宽。该规则**故意**连 `obj.MUTATIONS`
  与 `f(MUTATIONS=7)` 一起拒（你说得对，两者并不重绑）。保持这么宽是有意的（四套命中 0 处，
  收紧只会重开面），但错误消息已改成「一律不认：可能是重绑定，也可能只是同名的属性/关键字名，
  本函数不去分辨」。
- **LOW-2**：H1 残留的错误陈述「pytest 在断言没有消息时只打 `FAILED <nodeid>`」—— 实测是错的，
  消息为空仍补异常类名；真正产出「无 reason 整行」的是**行宽**。:195 与 :307 两处一并更正。

**你上一轮的两条证据限制都已闭合**：
① **「未附替换正文，不能独立确认每层只拆一层」** —— 负控存档现在**先逐层打印 old→new
   的 unified diff 与锚点命中数**，再跑；谁都能自己核每层到底拆了什么。
② **「全扫绑旧 SHA」** —— 上一 SHA 的 25 层全扫已落档
   （`r3-negctl-sweep25-20260916T191230.txt`：25/25 层各有独立显形点、0 层无声、
   跑前跑后 6 文件逐字同）；本 SHA 的 **26 层**版正在跑。

⛔ **另外补了一条 `ast_mutation_count` 的「威胁模型」声明，请你评价它是否诚实**：
该函数承诺的是**跨源一致性**（部分表冒充全量 / `MUTATIONS` 漂移 / 存档被改），
**不**承诺抵抗一个**蓄意改写自己源码**的 harness 作者 —— 理由是能改源码的人同样能改它
印出来的六档与自称分母，多这一维不会更强。⇒ 白名单的作用是「静态数不出来就抛」，
不是「证明这份源码在运行期改不了表」（后者在 Python 里静态不可判定）。历轮被换入口
打穿**八次**的清单已写进 docstring。**如果你认为这条边界声明本身写得不对或仍过宽，请直说**；
如果你同意，请不要再用「又找到第九个入口」这一形态报 MEDIUM —— 那一维已按上述边界收口。

现状：单测 **84 passed**；四套真实分母 138/9/11/18；26 层负控锚点全部命中 1 次。

**请重点核**：① 上面那条威胁模型边界声明是否诚实、有没有借它掩盖真问题；
② 急/惰分流会不会**过度收紧**（四套必须仍 138/9/11/18）；③ 两处 LOW 的更正是否与代码逐字相符；
④ 73 条处置里有没有哪一条只是把问题挪了个地方；⑤ 还有没有**任何一处**说得比代码宽。

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
