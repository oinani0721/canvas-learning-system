## 绑定与独立复算（先立证据面）

- HEAD = `581a8d0a`（父 `116f83c7`）；`git status` 仅两个未跟踪的 r4 复核/prompt 文件，树对 HEAD 干净。
- diff 面（22 文件）= 工具 + 该测试 + UAT §十 + evidence；**四份金集与 `gold_set_manifest.yaml` 零改动**（diff --stat 不含它们）✓。
- 我独立复算：`verify_all()` → rc=0；四 sha 逐字 = `r4-shas-*`（650c5d46…/d88d3a0a…/c7b25fcc…/582df3af…）✓。
- 全部探针**只读、纯内存**：`FakePath`（实现 `read_text/read_bytes/write_bytes`）驱动出厂函数；`git show 116f83c7:…` 取旧模块源码在内存 `exec` 做对照；未建/改任何文件，未连 7691/7687/8011，未跑 runner 非 shadow。

---

## ⓪ H-1 是否真关闭 —— **未完全关闭：HIGH**

**HIGH — 序列对账只比"值"不比"位置/对齐"，假 `- id:` 仍可配上有真实条目但**正则匹配不到的 id 行**，写入落在块 scalar 的 query 正文里，且 `problems=[]`、`changed` 谎报。**
- `backend/scripts/gold_set_manifest_tool.py:83`（`ITEM_ID_LINE_RE` 只认 `- id:` 未加引号形态）、`:618-630`（候选序列/ span 按**值序列**对账）、`:697-707`（全文档不变量）
- 复现（已在本机对出厂代码跑通，`changed=['q2'] problems=[]` 且确实 `write_bytes`）：
  1. 某条目的**第一个** `query: |` 块内写假行 `- id: q2` + 恰好一份 `user_verdict:` / `verdict_by:` / `verdict_at:` 行，同条目再用第二个 `query:` 键覆盖它（解析层**丢弃**该块 → 改写不被不变量看见）；
  2. 真实 `q2` 条目的 id 行写成 `- "id": q2`（或流式 `- {id: q2, …}`／别名）→ 文本层不产生候选，数量刚好补平；
  3. 真实条目的三字段已被同类正则匹配不到的写法（`user_verdict : x`）表达且**已等于本次目标值**（r3 那条"幂等重跑"前提；库调用显式传 `verdict_at` 即满足，CLI 需同一秒内第二次跑）。
  → 文本层 `["q1","q2"]` == 解析层 `["q1","q2"]` 通过；span 从块内假行到 EOF；found 恰一份；三键读回一致、全文档不变量也一致 → 工具报成功，**块内 query 正文三行被静默改写**。
- 与 r3 的差别（必须说清，便于定级）：r3 的"改写**活** query 正文"已被真关闭 —— 我用同一构造但把块放在**非丢弃**位置，出厂代码给出 `changed=[] problems=['预检：回写后除标注字段外还有其他解析差异…']`；把不变量整段换成 `pass` 后同一输入立刻变成 `changed=['q2'] problems=[]` 的静默改写 ⇒ **不变量承重**。残余危害面收窄（被改写的是 YAML 消费者看不见的丢弃区），但"工具自称成功 + 非标注字节被改"这一条成立，且整文件 sha 会变。
- 附带（同因，LOW 级）：对账是"逐值"不是"逐条目结构定位"，所以**合法但非规范写法**（`- "id": x`、流式条目、`- id: x  # 注`、id 用别名、`id: yes`→`str(True)`）会让**整个文件**拒绝回写；非字符串 id 还会让条目永远无法裁定（picks 键 `"5"` vs `ids_here={5}` → 每次报"找不到这个 id"）。当前四金集无此类行（我逐集合对账 75/28/2/0 全等），属潜在面。

---

## ① 新 parser：正常清单与边界

- **未发现 fail-open；发现 1 条新"误伤"面（LOW）。**
- 正常清单我实跑复算：`_parse_checklist_picks(UAT-…-裁定清单.md)` → `picks={} / problems=0`（103 条、0 勾、含 `---`+`## 补审` 段）✓；r4 dry-run 显示勾 2 条 → 每文件恰 3 行变化 ✓。
- 边界逐条（旧 → 新，均已复算）：标题内嵌锚 旧 `{'B':'irrelevant'}`（夺权）→ 新归 A 且无 problem ✓；补审段勾选 旧记到最后一条 → 新拒绝+problem ✓；标题在锚前 旧写 A+噪声 → 新拒绝+problem（更 fail-closed）✓；重复标题同 id → 正常归属 ✓；`#`/`---` 结束条目 ✓。
- **LOW — 条目内任何以 `#` 开头的行会把该条勾选整体丢弃。**
  `tool:551-554`（`stripped.startswith("#")`）。复现：锚+标题后插一行 `# note`，再放真勾选 → 该条 `picks` 为空 + "不在任何条目标题之下"。当前清单/金集无此类行（我扫过 4 集合 0 条多行或 `#`/`---`/`**` 开头 query），仅潜在误伤；`---` 同理（只按整行相等 ⚠️ 比 `#` 窄）。

---

## ② `verify_gold_set_file` / `verify_all` / `build_manifest`

- **MEDIUM — `verify_all` 仍会在"已登记金集的 `queries` 里含非映射条目"上崩，runner 也会走 exit 1（不是 rc=2）。**
  `tool:311-330`（只守卫到 `queries` 是列表）、`:373-387`（`_field_problems` 里 `q.get` 直接吃条目）、`run_vault_retrieval_regression.py:217-218`、`run_memory_retrieval_regression.py:148-149`（`q["id"]/q["query"]` 在各自 try 之外）。
  复现（我实跑，sha 与 manifest 一致，即 `build` 后的状态）：`queries: ["str", …]` → `verify_all` 抛 `AttributeError: 'str' object has no attribute 'get'`（CLI `verify` = 未捕获异常 exit 1）；同一文档 `verify_gold_set_file` 仍返回 `True`（只核 sha/query_count）；两个 runner 随即在取 `q["query"]` 时 `TypeError` → exit 1，正是其 docstring 承诺要避免的"指标回退"语义污染。r4 新增的 4 个 verify_all case 只覆盖顶层/`queries`/`config` **文档级**形状，**条目级**没覆盖（这也让 r3 的 M-"verify_all 形状崩"只算部分关闭）。
- 其余 r4 守卫我逐条实跑对照（旧 → 新）：顶层 list `AttributeError`→rc=2；`queries:5` `TypeError`→rc=2；`config:5`（count 对齐时）`AttributeError`→rc=2；`files:[]`+totals 全 0 `rc=0`→rc=2（代码两函数都有，但 **verify_all 侧无测试**）；`vgsf` 非目标坏条目 `True`→`False`；`query_count` 缺失 `True`→`False`；入参 5/None/bytes/NUL → `(False, 文案)` ✓。
- `build_manifest`：top-list / `revision: None` / `1.9` / `True` / `history: dict|int` 全部 rc=1 且**未写**（我用 FakePath 实跑，无真实落盘）✓；`revision_history` **falsy 非 list**（`{}`、`0`、`""`、`false`）因 `tool:191` 的 `or []` 绕过守卫 → rc=0 照写（静默归一化）——与自述"history 必须 list…全部拒绝"不符（无数据丢失）。`manifest` 不存在时 `--bump-revision` 仍被静默忽略（r3 已登记的非缺陷项）。
- bool / rc 语义**仍可区分** ✓：sha 不符 = `sha256 期望…实测…`（vgsf 压成 False、verify_all rc=1，docstring 已明确不承诺一一对应）；环境/输入错 = `解析失败/不可读/条目非法/未登记任何文件`（rc=2/False）。
- **LOW — `apply-verdicts`（CLI）对非映射文档仍崩**：`tool:714-731` 的 try 只收 `YAMLError/OSError/UnicodeDecodeError`，顶层 list/标量 → `AttributeError`、`queries: 5` → `TypeError`（我实跑）；`verify_all(非 Path)` 同类（`tool:242-249`，`5/'str'/b'x'` 均 `AttributeError`）。

---

## ③ 新测试是否真覆盖 / 会否误绿

- **MEDIUM — 关键新机制无测试钉住，且 H-1 回归测试不是受害构造。**
  `test_gold_set_manifest_g413.py:829-866` 的 fixture 用 `user_verdict: pending`（旧代码在该 fixture 上会把三行写到**真字段**上，属"旧版也 changed=['q1']"的分支差异测试，不是"预检误判通过→改坏正文"构造）；**全文档不变量（`tool:697-707`）在测试文件里 0 命中**（grep"还有其他解析差异"无结果）。我把不变量整段 `pass` 化后同一输入立即变静默改写 ⇒ 承重却无门。
- 先红证据（我用 `116f83c7` 源码内存复算）：假 id 行 → 旧 `changed=['q1']/problems=[]`（新测试红）；重复 id → 旧 `changed=['q1']`；CRLF → 旧 0 个 CRLF、全 LF；`verdict_by="a\nb"` → 旧确实写入且**多 2 行**（守卫只查字面 `\n`）；内嵌锚/补审段 → 旧 `{'B':…}`/末条误归属；`vgsf` 坏条目/缺 count → 旧 True；`files:[]`+totals0 → 旧 rc=0；三形状 → 旧崩 ⇒ 上述新断言在旧代码上确实会红 ✓（14 条中 ⑩`non-utf8` 旧代码已被 `(OSError, UnicodeDecodeError)` 接住，属"补覆盖"非行为变更）。
- **门未覆盖**：verify_all 的 `files:[]`→rc=2、条目级非映射（②的 MEDIUM）；无尾换行（我实跑 OK：不加 `\n`、6 行不变）、CR-only/`U+2028`/`U+0085` 行尾（我实跑：LS/NEL 被 `safe_load` 当换行、写前预检拦下 → fail-closed ✓，无测试）；预检失败/字段行重复分支仍无测试。
- 反空转锚的收缩（只在有 query 的文件上要求块数）**可接受** ✓：0 条文件本来无键可重复；有 query 的四个集合 `blocks==n_q` 成立（75/28/2）✓。

---

## ④ 证据链

- `r4-m3-probe-assets/`（README + 两变异体 + `mutants.diff` + `probe.py`）**自包含** ✓：我核对变异体调用顺序确与 diff 一致（memory 变异体 `alive`@355 先于 `verify`@367；真 runner verify@359 先于 alive@365；vault 变异体 verify@503 在环境检查@497 之后），第三方可按 README 复算。限制：`probe.py` 要建临时目录，我在只读沙箱内**未实跑**，只复算了源码/顺序。归档中 `…134720.txt`（"不可区分=False"）与 `…134729.txt`（"两条都成立"）是两次矛盾输出，**前者未标作废**，读者可能误读为先失败后通过（r4 最终结论取 134729）。
- 目录级口径**可比** ✓：collected 1945→1959（+14 = 5 fail-closed case + 4 verify_all case + 5 新测试；gate 文件 25→39），passed 1938→1952，skipped 6、xfailed 1 不变 ⇒ 1938+14=1952 自洽，且 diff 内只动了这一个测试文件。
- UAT §十：`39 passed` ✓（`r4-gate-green-…134736` collected 39/39 passed；同目录另有 37 项的同名中间产物，无作废标记）；`1952/6/1 红 0` ✓；83 条×10 键 diffs=0 ✓（58+25）；四 sha、verify rc=0 ✓ 我已独立重算。**overclaim 两处**：① 整改表把 H-1 的行为锚写成"不再写坏"，但该测试既不构成受害构造、也未覆盖不变量（见③）；② "history 必须 list…拒绝覆盖"对 falsy 非 list 不成立（L4）。§10.3 的"只把回写工具修到『任何已列输入不写坏』"措辞本身是诚实的 ✓。

---

## ⑤ r3 清单逐条点名（H-1 / M×8 / L×8）

- **H-1 = 部分关闭**（活体 query 正文已被不变量挡住 ✓；对齐维度 + 丢弃区仍可静默改写 → 本轮 H）。
- M-1 同 id 重复 = 关闭 ✓（旧 last-wins 只改一块，新"恰 1 次"拒绝，0 字节写）。
- M-2 CRLF 全文件行尾重写 = 关闭 ✓（旧 0 CRLF → 新 6 CRLF、恰 3 行差；CR-only/异种行尾无测试）。
- M-3 内嵌锚夺权 / 补审段误归属 = 关闭 ✓（旧 `{'B':…}`、末条误归属 → 新忽略/拒绝+problem）。
- M-4 `verify_gold_set_file` 跳过坏条目 / 缺 count = 关闭 ✓（旧 True/True → 新 False/False）；但**目标文档内容**仍不校验（见② MEDIUM）。
- M-5 `verify_all` 形状崩 = **部分关闭**（顶层/`queries`/`config` 三类已 rc=2；**条目级仍崩**）。
- M-6 `build_manifest` revision/history = 关闭（除 falsy 非 list 一处，L4）；revision None/1.9/True/list 全拒绝 ✓。
- M-7 重复键判据空转 = 关闭 ✓（反空转锚生效，四集合块数=条数）。
- M-8 缺 UnicodeDecodeError case / verify_all 新分支无测试 = **部分关闭**（⑩⑫ 已补，4 case 已补；`files:[]`(verify_all) 与条目级无测试）。
- L①`_yaml_scalar` 真换行 = 关闭 ✓（旧多写 2 行 → 新"多行"拒绝）。L②memory pin 不可区分 = 关闭 ✓（`_pin_env_after_verify:345-371` 记录调用；失败场景 `calls==[]`（:429/:770）、对照 `calls==["alive"]`（:790））。L③锚在标题后噪声 = 关闭到 fail-closed ✓。L④roundtrip 弱断言 = 部分（CRLF 3 行差已钉 ✓；无尾换行/预检失败/重复字段行仍无测试）。L⑤`files:[]` rc=0 = 关闭 ✓（代码两函数，verify_all 侧无测试）。L⑥入参非路径 = 关闭 ✓（vgsf：5/None/bytes/NUL 全部 `(False,文案)`）；L⑦"6 红=/bin/ps"措辞、L⑧build 首生成路径 = 前者属证据叙事（未评）、后者非缺陷（仍静默忽略 `--bump-revision`）。
- 不评项已守约：G4-14 七指标 / R-SLO / L-5（Tier-R top10）未触碰；103 条语义未评。

---

## 未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径

- **未被拦下的输入**：对齐变体（丢弃区块内假行 + `- "id": x`/流式/别名隐藏真条目 + 已等于目标值的三字段）→ `changed=['q2'] problems=[]` 且改写了 query 正文；`queries: [非映射]`（sha 一致）→ `verify_all` 崩 / runner exit 1；`vgsf` 对同一文档返回 True；`apply-verdicts` 顶层非映射或 `queries` 非 list → 未捕获 AttributeError/TypeError；`verify_all(非 Path)` → AttributeError；`revision_history: {}`/`0` → 绕过守卫 rc=0 重写。
- **对照输入**：四金集文本层==解析层（75/28/2/0）；真清单 0 problems；CRLF 恰 3 行；无尾换行不新增 `\n`；LS/NEL 行尾 fail-closed；干净 manifest `verify_all` rc=0、四 sha 与 manifest 逐字同。
- **负控输入（先红复算）**：`116f83c7` 源码对 11 条新 case 会红（假 id→`['q1']`；重复 id→`['q1']`；CRLF→全 LF；多行→多 2 行；内嵌/补审段→误归属；vgsf 坏条目/缺 count→True；`files:[]`+totals0→rc=0；三形状→崩；入参→TypeError）；**不变量关掉后同一输入从"拒绝"变"静默改写"**（证明它承重）。
- **门未覆盖的路径**：全文档不变量本身（0 测试）；verify_all 条目级/`files:[]`；H-1 的真实受害构造；无尾换行与 CR-only/异种行尾；`probe.py` 未在本轮实跑（只读沙箱）；r4 无 gate-red 存档。

---

**本轮总评：B=0 / H=1 / M=2 / L=4**

`581a8d0a` **部分达成**自述目标：r3 的 1H/8M/8L 中 11 条完全关闭、3 条部分关闭（H-1 的活体改写已由不变量真关闭，但"序列对账"仍缺**结构对齐**维度；verify_all 形状崩差条目级；测试面缺不变量/verify_all-空注册钉子）；CRLF/字节级、重复 id、锚边界、vsf/verify_all/build 的已列输入、M-3 pin 承重与证据链均经我独立复算成立 —— 因此不宜按"H-1 已关闭、全绿"收口，建议把候选对账升级为按 YAML 结构逐条目定位（或对每个候选做解析层归属校验）后重跑一轮。


