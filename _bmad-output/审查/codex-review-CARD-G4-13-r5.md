## 绑定与独立复算（先立证据面）

- HEAD = `691b1d3e`（父 `581a8d0a`）；`git status` 仅 2 个未跟踪 r5 复核/prompt 文件；`git diff --stat 581a8d0a 691b1d3e` 只含 `backend/scripts/gold_set_manifest_tool.py` + `backend/tests/regression/test_gold_set_manifest_g413.py`（四金集与 manifest 零改动）。
- 我独立重算：四 sha `650c5d46…/d88d3a0a…/c7b25fcc…/582df3af…` 与 manifest、与 `r4-shas-…txt` 逐字同；`verify_all` rc=0（4 条 OK）；真 103 条清单 `_parse_checklist_picks` → `picks={} / problems=0`；四文件 `blocks==n_q` 75/28/2/0。
- 全部探针**只读、纯内存**：`FakePath`（`read_bytes/write_bytes/read_text`）驱动出厂函数；`git show 581a8d0a:…` 源码内存 `exec` 做对照；未建/改任何文件，未跑 runner、未连端口；**未实跑 pytest**（只读沙箱），测试面靠源码内存复算 + 证据文本核对。

---

## ⓪ 残余 H 是否真关闭 —— **HIGH（未完全关闭）**

**HIGH — 结构对账只把「候选 span」与「同序解析条目」比对，从不把 span 绑定到解析条目**真正所在**的位置；另起一个被覆盖的同级 block scalar 放伪条目即可让对账全绿、写入落进死区。**
- `backend/scripts/gold_set_manifest_tool.py:647-657`（span 单独解析 `"queries:\n"+span`，只取 `probe["queries"][0]` 比对 ⇒ span 之后的顶层多余键被静默吸收/忽略）、`:83`（`ITEM_ID_LINE_RE` 只认未加引号 `- id:`）、`:641-646`（id 值序列对账）。
- 复现（已在本机对出厂代码跑通，`changed=['q2'] writes=1 problems=[] bytes_changed=True`，解析层文档**完全不变**）：真条目 id 行写 `- "id": q2`（正则看不见）→ 候选全来自一个**被覆盖**的同级死 scalar：
  `dead: |` 里放与真条目**逐键相同**的 `- id: q1 … - id: q2 …`，文件尾再写一行 `dead: placeholder` 覆盖它。
  → 每个候选 span 各自恰好解析成同序条目（k=0/k=1 均 `ok=True`）；写入把死 scalar 里的 `user_verdict:  "irrelevant"`、`verdict_at: "…"` 改写成规范化字节；预检（`:719-724`）、全文档不变量（`:728-740`）都看不见（死区被覆盖）⇒ 工具自报成功。前提同 r4：目标值 = 现有生效值（幂等重跑/显式 `--at`）。**该构造在 r4 源码上同样落写**（我实跑 `OLD changed=['q2'] writes=1`）⇒ 属「r5 未关闭该类」，不是新回归。
- 同根、更轻的一例：同一 via 条目里**重复键**（先未引号可见、后引号不可见，值相同）⇒ 写入落在**不生效的那一行**，`changed=['q1'] problems=[]`、生效值不变（我实跑）。
- **已按 ⓪ 逐项排除的等价性面**（我逐条内存复算）：① r4 受害构造（committed fixture）在 r5 下**确实被拒**（`changed=[] / 0 字节`，红→绿成立）；② 交换两个条目位置 ⇒ 索引对齐比较，**不漏**，回写落对条目（实跑正确）；③ 同名重复 id ⇒ `spans` 恰 1 次检查照旧拒绝；④ 同时可见的重复键 ⇒ `:677-680` found=2，该条不动；⑤ 跨条目别名 `query: *a` ⇒ span 单独解析抛 `undefined alias` ⇒ 整文件拒绝（fail-closed）；⑥ 行内 flow 条目 ⇒ 候选数不符 ⇒ 整文件拒绝（fail-closed）；⑦ `queries:` 后出现 `---`/ `...` 多文档标记 ⇒ `load_yaml` 与 probe 双双 `YAMLError: expected a single document in the stream` ⇒ fail-closed（我实跑）。

## ① 内容形状守卫是否完整 —— **MEDIUM（部分）**

- 已关闭：顶层非映射 / `queries` 非列表 / **条目非映射** ⇒ `(False, 文案)`（`:455-466`）、`verify_all` 条目级 ⇒ rc=2（`:320-323`）✓，两条新 case 在 r4 源码上确先红（rc=1 / True）。
- **仍未拦下（vgsf 形状守卫实测返回 True，我逐个猴子补丁复算）**：`queries: [{}]`、`- id: q1`（缺 `query`）、`id: 5`、`queries: []`、缺 `config` / `config: 7`、`query: [a,b]`。
  复现思路：把上述任一形状写成 sha 与 manifest 一致（= build 后冻结态）⇒ `verify_gold_set_file` 仍 `True` ⇒ 按 r4 复核引用的 runner 行（`run_vault_retrieval_regression.py:217-218` / `run_memory_retrieval_regression.py:148-149`，本轮最小读取面不含 runner，未直接复核）`q["query"]/q["id"]` KeyError → **exit 1**，正是 r5 承诺关掉的那类语义污染。
- 附带（LOW，先于 r5 存在）：vgsf 不比对 `len(qs)` 与 manifest `query_count`（manifest 写 7、实际 1 条仍 `True`，`:466` 只把 want_count 印在文案里）；`verify_all` 侧会 rc=1，但 runner 只调 vgsf。

## ② 新代码新崩点 / 误伤 —— **未发现 BLOCKER/HIGH；2 条 LOW**

- 崩点：未发现。`:641-646` 先比长度/值 ⇒ 结构循环不会 IndexError；probe 只可能抛 `yaml.YAMLError`（`:651-654` 已接）。`_load_queries_strict`（`:746-757`）实测把 r4 会崩的三类输入（顶层 list / `queries: 5` / 条目 `not-a-map`）变成 problem + 0 字节（旧：AttributeError/TypeError）✓。`verify_all` 入参 5 / `b"x"` ⇒ rc=2，`"\x00"` ⇒ rc=2（`Path.exists()` 未抛），旧版 AttributeError ✓。
- `build_manifest`：`revision_history` 为 `{}`/`0`/`""`/`false` ⇒ rc=1 且**不写**；`[]` 仍合法（实跑）✓（`:191-195`）。
- **LOW（新增误伤面）** 跨条目锚/别名：r4 会正常回写，r5 因 span 单独解析解析不到 `*a` ⇒ **整文件拒绝**（我实跑：`OLD changed=['q2']` → `NEW 解析失败 拒绝`）。合法非规范写法（flow 条目、`- "id": x`、`id: yes`）整文件拒绝是 r4 已登记的潜在面；当前四金集无此类行（blocks==n_q、verify rc=0），仅潜在。
- **LOW（新修无钉子）** 标题边界收窄到 `^#{1,6}\s`（`:582`）后正常清单仍逐条归属 ✓（真 103 条清单 `picks={}/problems=0`；dry-run 每文件恰 3 行）；但「条目内 `# note` 不再误伤」这条 r4-L 行为**无测试**（gate-red 只 3 红，说明 r4 上没有对应红项）。

## ③ 测试真实性 —— **MEDIUM（部分）**

- 受害构造**真会红在旧代码**：我用 committed fixture 对 `git show 581a8d0a:` 源码内存复算 ⇒ `changed=['q2'] writes=1 problems=[]`；对 r5 ⇒ `0 写 + 「结构对账失败」problem` ✓；断言 `:1050` 确实为目标分支（红证据 140537 行号 1001/1050/1106 与 committed 文件一致 ✓）。
- **LOW** 该测试只断言 `problems` 非空，不钉消息 ⇒ 「任何更弱的拒绝（例如任何 YAML 错）」也能绿；同理 content-shape case 只查 `"queries" in detail`。
- **MEDIUM（r4 的 M 只部分关闭）** 关键机制仍无判别性测试：全文档不变量（`:728-740`）在测试文件里 0 命中（我 grep `预检/解析差异` 仅命中两处 docstring）；我实跑证明它**仍承重且无人钉**——同类 decoy 换成**活** scalar（`notes: | …`）时 r5 拒于不变量，把 `if expected != doc:` 抹成 `if False:` 即变 `changed=['q2'] writes=1` 静默落写，而 committed 任何测试都不覆盖该输入。预检分支（`:719-724` 读回不一致）与字段行缺失/重复分支（`:677-680`）同样 0 测试命中。
- 反空转锚仍有效 ✓（`:198-203` 判据未改；四文件 blocks==n_q 75/28/2/0 我独立复算）。

## ④ 证据链 —— **LOW（叙述/命名瑕疵，数字自洽）**

- 红证据：140537（3 failed/41 passed）是合法旧源码基线（红在指定断言）；**140423（2 failed）是中间开发态**（其 content-shape 断言在 1105 行，committed 文件是 1106 ⇒ 两次跑的测试文件不同版本），且时间戳**早于** 3-failed 那次 ⇒ 「先红→后绿」在目录顺序上倒置，该文件未标作废、又被 `r5-gate-red-*.txt` 通配覆盖。
- 计数自洽 ✓：gate 39→44（+5）；目录级 `collected 1959→1964`、`1952→1957 passed`、6 skipped / 1 xfailed 不变、0 failed（我核对 r4/r5 两份文本）；ruff 通过。
- **LOW** UAT §11.2 引 `r5-verify` / shas 作为证据，但 evidence-g413 里**没有 r5-verify/r5-shas 文件**（只有 `r4-verify-…134627.txt` / `r4-shas-…`；内容仍与现状一致）⇒ 结论真、引用名不真。
- §十 两处 overclaim 已按承诺改词（`:265` 「仅部分关闭」、`:271` 「当时仍绕过」）✓；r4 探针中间版已补「已作废」注记（`r4-m3-mutation-probe-…134720.txt` 文末）✓。

## ⑤ r4 清单逐条点名（H×1 / M×2 / L×4）

- **H（残余·结构对齐）= 未关闭** → 本轮 HIGH（⓪ 的 decoy 构造；r4 受害形状本身已关，但同类仍可构造）。
- **M（verify_all 条目级崩 / runner exit 1）= 部分关闭**：崩溃面关（rc=2 红→绿）；「映射但缺键」条目仍能过 vgsf → runner exit-1 面残留（① MEDIUM）。
- **M（关键机制无测试 / H-1 非受害构造）= 部分关闭**：受害构造**真关闭** ✓；不变量/预检/重复字段行仍无判别测试（③ MEDIUM）。
- **L①`#` 行过宽** = 代码关闭 ✓（无测试钉子 → LOW）；**L②apply-verdicts 非映射文档崩** = 关闭 ✓（实跑旧崩→新 problem）；**L③verify_all 非 Path 崩** = 关闭 ✓（实跑 5/bytes/`\x00` 全 rc=2）；**L④`revision_history` falsy 非 list** = 关闭 ✓（实跑 4 种 falsy 全 rc=1 且 0 写，`[]` 仍允许）。

---

## 未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径

- **未被拦下的输入**：① decoy 死 scalar 变体（真条目 id 引号化 + 被覆盖同级 scalar 放同名伪条目）→ 结构对账全绿、`changed=['q2'] problems=[]`、死区字节被改、解析层文档不变、文件 sha 变；② 同条目「未引号可见 + 引号不可见」重复标注键 → 写不生效行、自报成功；③ `queries:[{}]` / 缺 `query` / `id: 5` → vgsf `True`（runner exit-1 类）；④ manifest `query_count` 与实际不符 → vgsf `True`。
- **对照输入**：四金集 sha/计数未动（650c5d46…/d88d3a0a…/c7b25fcc…/582df3af…，revision 2）、verify rc=0；真 103 条清单 0 problems、103 个锚；blocks==n_q 75/28/2/0；交换条目位置回写落对条目；跨条目别名/flow 条目 fail-closed。
- **负控输入（先红复算）**：r4 源码对 committed 受害构造 `changed=['q2'] writes=1 problems=[]`；r4 的 `apply_verdicts` 对三类坏文档抛 AttributeError/TypeError；r4 `build_manifest` 对 falsy 非 list history `rc=0 + 写`；r4 `verify_all(5/b"x")` 抛 AttributeError；**不变量抹除后**活区 decoy 由「拒绝」变「静默落写」（承重证据，且 committed 无测试钉它）。
- **门未覆盖的路径**：全文档不变量 / 预检失败 / 字段行重复三分支；`#` 行收窄后的误伤修复；vgsf 对「映射形状内部」缺失键与非空性；结构对账「span 外多余顶层键被忽略」这一语义（decoy 无负控）；两个 runner 本体（本轮最小读取面不含，未直接复核）。

**本轮总评：B=0 / H=1 / M=2 / L=3**

`691b1d3e` **部分达成**本次自述目标：r4 点名的 M 崩溃面、L×4、以及 r4 受害构造的形状本身（红→绿我已独立复算）都真关闭，`_load_queries_strict`/入参守卫/`revision_history` 判空经实跑成立，冻结面零改动；但「结构对账关闭 H 残余」不成立——候选 span 与解析条目**从未做位置绑定**，被覆盖的同级 scalar 放同名伪条目仍可让对账全绿、写入落进非条目区域并自报成功（r4 源码同构造亦落写），且内容形状守卫对「映射但不可跑」的条目、全文档不变量/预检分支仍留缺口。
