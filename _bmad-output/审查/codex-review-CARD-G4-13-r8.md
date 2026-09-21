# CARD-G4-13 r8 独立复核报告（Codex × DeepSeek V4.1 Flash，只读）

**绑定**：HEAD = `c773e36b2c5501b76371ef05d40012904e1165db`，父 `22c1603a`；仓库未改动（`git status` 仅任务开始前已存在的两个未跟踪 r8 review/prompt 文件）。独立复算：行为门 **54 passed**（2.11s，重跑）、`tests/regression` **1974 collected**、四金集 sha 与 manifest/`r8-shas-*` 逐字一致、`ruff check/format` 双 rc=0、`verify_gold_set_file()` 直调四份真实金集全部 `True`。目录级 `1967 passed` 未重跑（仅收集数 + 证据算术核对）；未连 7691/7687/8011，未跑两个 runner 非 shadow 模式。

---

## ⓪ 守卫残余：sha 相符但 runner exit 1 / 门禁 fail-open

**结论：有残余；其中 H1 是相对 r7 的守卫回退。** 按严重度：

### HIGH H1 — 显式 YAML null 被当成“缺键”，r7 拦过、r8 重新放行 ⇒ 未捕获 exit 1

- `backend/scripts/gold_set_manifest_tool.py:517-521` 用 `v = cfg.get(num_key); if v is None: continue`。
- `backend/scripts/gold_set_manifest_tool.py:533-535` 对 `leak_markers` 用 `lm is not None and (...)`。
- 与 r7 源码对照实跑（in-memory 同一 fixture、同一 manifest）：`tolerance:` / `duplicate_ratio:` / `max_results:` / `top_k:` / `leak_markers:` 显式 null 在 r7 返回 **False（拒）**，在 `c773e36b` 返回 **True（放行）**；`expect_not_hit:` 显式 null 同样从 r7 的拒变为 r8 的放行（`tool.py:492-500` 的 `nots is not None` 跳过）。

复现输入（memory / category；manifest 同步更新 sha/query_count/class_key）：

```yaml
config:
  version: 1
  tolerance:          # 或 max_results: / duplicate_ratio: / leak_markers:
queries:
  - id: q1
    query: body
    expect_any: [x]
```

- guard 返回 `(True, "OK …")`；
- `backend/scripts/run_memory_retrieval_regression.py:374` `float(None)`（vault 侧 `run_vault_retrieval_regression.py:497` 同）在 `main()` 无 try 包裹路径上抛 `TypeError` → **exit 1**；`max_results`/`duplicate_ratio` 在 `run_queries:136/138`、`leak_markers` 在 `is_leaked:114-115` 经 `:170` 调用，均在 `main():379` 的无保护路径 → **exit 1**。
- 边界说明：vault 的 `top_k:` null 在 `run_tiers:191` 抛，最终被 `main():500-505` 兜成 rc=2；但 memory 的四个 null 全部落在 exit 1 档。

### MEDIUM M1 — `id` / `query_type` / `category` 的非 JSON YAML 类型仍可 exit 1

- `tool.py:471-473` 只查 `id` 是否**存在**、`query` 是否 str，不查 `id` 类型；`query_type`/`category` 完全未查。
- `run_memory_retrieval_regression.py:185` 把 `category` 原样写进 `entry`；`run_vault_retrieval_regression.py:245` 把 `query_type` 原样写进 `entry`；`id` 在 `:185`/`:245` 前已进入 `entry`。
- 复现：`id: 2020-01-01` / `category: 2020-01-01`（vault 为 `query_type: 2020-01-01`）→ guard True；`json.dumps(report)`（memory:390 / vault:541，非 shadow 主门路径）抛 `TypeError: Object of type date is not JSON serializable` → **exit 1**。`!!binary` 同理。这与 r8 自述要关闭的「非 JSON 类型 ⇒ exit 1」是同一族，r8 只关了 `group_id`/`version`。

### MEDIUM M2 — 守卫自身对超大整数溢出逃逸，违反其 fail-closed 契约

- `tool.py:521` / `:528` 直接调用 `math.isfinite(v)`；YAML 400 位整数字面量 load 为 Python `int`，`math.isfinite(10**400)` 抛 `OverflowError: int too large to convert to float`。
- 与 r7 对照：r7 返回 True（随后 runner `float()` 溢出 exit 1）；r8 在 **guard 内**抛异常，`ok, detail = verify_gold_set_file(...)` 处未捕获 → exit 1。`tool.py:402` 明言「环境/输入错一律走 `(False, 文案)`、不以异常逃逸」，此路径直接违反该承诺。
- 输入：`config.tolerance: <309 位以上整数>`（`version`、`max_results`、`top_k` 同）。

### MEDIUM M3 — 只查有限性、不查范围/空集：若干 fail-open 退化值

- `tool.py:517-521` 只要求有限数值。`tolerance: 2`（或任何 ≥1 的值）通过；`run_vault_retrieval_regression.py:427-439` / `run_memory_retrieval_regression.py:297-310` 的判定 `delta < -tolerance` / `delta > tolerance` 对 [0,1] 指标**永不触发**，全部回退可 rc=0。
- `duplicate_ratio: 2` 通过，`SequenceMatcher.ratio() <= 1` 使近重复检测恒空 → `duplicate_rate=0`（越低越好，反而“改善”）。
- memory `leak_markers: []` 通过（`:533-535`），`is_leaked` 对 `[]` 恒 False → `leak_rate=0`，泄漏检测被静默关闭。
- r7 M2 原文即写「不查有限性/**范围**」；r8 只补了有限性，范围/空集残留。

### MEDIUM M4 — 期望元素只查 str、不查非空：空串使主指标恒满分

- `tool.py:509-511` 只要求 `expect_any` 是非空 **list**、元素是 str；`expect_any: [""]` 或 `["  "]` 通过。
- `run_memory_retrieval_regression.py:110` `norm_text("")==""`，`:199` `is_relevant` 对任意返回文本恒 True → hit@5=100%、MRR=1.0，门禁可绿。
- vault 侧 `tool.py:487-490` 只要求 `h["file"]` 是 str；`expect_hit: [{file: ""}]` 通过，`run_vault_retrieval_regression.py:127-131` `"" in path_n` 对任意结果恒真 → hit@10=100%。
- `leak_markers` 元素的大小写由两侧 `casefold` 归一（安全）；空串元素会使全部结果判泄漏 → leak_rate=100%（红，不是 fail-open）；但**空列表**见 M3。

### MEDIUM M5 — `contamination/forbidden/delivery` 内部键：登记理由“rc=2”不成立，且含 fail-open

- `tool.py:530-532` 只查顶层是否 dict。内部键为 str/int/float 时 runner 不一定抛：
  - `forbidden: {path_globs: "secret/**"}` 通过；`run_vault_retrieval_regression.py:149` `for g in "secret/**"` 逐字符迭代，几乎不匹配真实路径 → `hard_violations` 空 → `main():523-527` 的「信息隔离铁律」硬门可 rc=0（**fail-open**）。
  - `contamination.path_globs: "raw/*"` 通过；`:138-143` 同样逐字符 → `delivered_contamination_rate` 被静默算成 0。
  - `delivery.min_relevance: null` 通过；`:332-335` 的 `float(None)` 被每 query 的 `except Exception`（`:336-338`）吞掉 → Tier D 全空、指标回退 → **rc=1**，不是 UAT §14.1 `:437-438` 声称的 rc=2。只有 `hard_cap` 坏值在 `:345` 的空 query 分支才会 rc=2。
- null 型内部值多会 rc=2（正确），但 str 型内部值会静默改变语义或绕过硬门，登记文字过窄且定性错误。

### LOW（未达 HIGH/MEDIUM 的边界项）

- **L-a `max_in_top_k` 边界**：`tool.py:497` `isinstance(..., int)` 放行 `true`（bool 是 int 子类），runner `:303` `int(True)=1`，语义偏移 1；放行 `-1`，`:307-310` `over = n_hit - (-1)` 可使 `contamination_at_10 > 1.0`。二者不 exit 1。
- **L-b `grade` 类型**：`tool.py:487-490` 不查 `grade`；`grade: high` / `[1]` 通过 guard，`run_vault_retrieval_regression.py:122-135/277` `int()` 在 `run_tiers` 内抛，被 `main():500-505` 兜成 **rc=2**（不是 exit 1）；`"1"`/`1.9`/`true` 会被静默强转。
- **L-c `cfg["version"]` 为 int**：int 有限值本身安全（仅写入 `report["gold_set_version"]`，shadow 模式在写盘前 early return）。真正的问题是**缺失/null**：guard `:527-529` 拒，但 runner 默认 0（memory:380、vault:517），且 `build` 会写 `config_version: None`（`tool.py:150`），`verify_all` 的 None==None 又放行 → build/verify 能过、runner guard 拒（见 ①）。
- **L-d `group_id` 为空**：`group_id: ""` 通过 `:523-526`；runner `if group_id`（`:148-151`）/ `group_id or ""`（`:117-119`）把空串当 null/server default，行为上等价 null，不崩但无法表达“空 vault 过滤”的显式错误。`vault_id: null` 通过后在 `run_vault_retrieval_regression.py:197` 变成 `str(None)="None"`，**不是**默认 `canvas_vault`（默认只在缺键时生效）→ 静默指向错误 vault。
- **L-e vault `expect_empty` + `expect_not_hit` 并存**：guard 放行；runner 的假阳性分支（`:343-345`）与配额污染分支（`:300-320`）**都会执行**，不崩、不 fail-open（双重从严）。`expect_empty: true` + `expect_hit` 并存时 runner 在 `:250` 按 empty 分支走，`expect_hit` 被静默忽略（返回全记假阳性，红，不是 fail-open），但矛盾声明未被拒。
- **L-f memory `expect_empty` 真值非 bool**：`tool.py:507-508` 先 `continue`，`:512` 的 bool 检查不可达；`expect_empty: "yes"`/`1` 被 r8 放行（r7 拒）。runner 按真值处理，不崩，但类型契约回退。

**逐 runner 取值行对照结论**：memory 的 `max_results/leak_markers/duplicate_ratio/tolerance`（H1）仍有 exit 1；`category/id`（M1）非 JSON 标量 exit 1；`expect_any` 空串（M4）fail-open；`leak_markers=[]`（M3）fail-open。vault 的 `tolerance` null（H1）exit 1；`query_type/id`（M1）exit 1；`forbidden/contamination` str（M5）fail-open；`delivery.min_relevance` null 为 rc=1 而非 rc=2；`top_k` null → rc=2；`grade` 坏值 → rc=2。

---

## ① 是否误拒真实四金集 / 未来合法扩展

- **真实四金集：未误拒。** 我直调 `verify_gold_set_file()`（不是只跑 CLI）对四份真实文件：全部 `True`/`OK`；CLI `verify` rc=0；四 sha 与 manifest 逐字一致（`650c5d46…` / `d88d3a0a…` / `c7b25fcc…` / `582df3af…`）。`22c1603a→c773e36b` 对金集与 manifest 的 diff 为空。
- **自查修正的数字可验。** 真实 vault 集 75 条中恰 **41 条**是 `expect_hit`-only（无 `expect_not_hit`、无 `expect_empty`）；当前 guard 的「expect_empty 存在才查类型」写法让这 41 条全过（直调 guard True），数字与自述吻合。
- **新键/未知键被忽略：未发现误拒。** 我在合法条目上加 `source`（dict/list）、`user_verdict: 2020-01-01`、`language: !!binary`、`query_type/category` 任意值及未知 config 键，guard 仍 True；runner 不读 `source/user_verdict/language`，不会因它们崩。
- **但有两处对 runner 合法形态的误拒（LOW）**：
  - `config.version` 缺失：guard `tool.py:527-529` 直接拒；runner 默认 0（memory:380 / vault:517）；`build` 会写 `config_version: None`（`tool.py:150`），`verify_all` 又认为 None==None 合法 → **build/verify/runner 三方不对称**。删除一个合法文件的 `version` 再 build 即可复现“工具自己生成、守卫却拒”。
  - `expect_not_hit` 项缺 `max_in_top_k`：guard `tool.py:494-500` 拒；runner 默认 0（vault:303），本可跑。输入 `expect_not_hit: [{path_glob: x}]`。
- **`language/query_type/category` 类型**：`language` 完全忽略（任意形态安全）；`query_type/category` 被原样回写报告，JSON-safe 形态安全，YAML date/bytes 形态 → M1 的 exit 1（不是误拒，是未拦下的崩）。

---

## ② 三个新 case 是否真在目标分支上判别

我把 `test_gold_set_manifest_g413.py:1114-1132` 的三组 fixture 原样输入 r7（`22c1603a`）与 HEAD 的 guard：

| case | class_key | r7 | r8 | 判别性 |
|---|---|---|---|---|
| `memory-expect-any-missing` | category | `False`，文案「一个期望键都没有」 | `False`，文案含 `expect_any` | **仅文案级判别**：`ok is False` 在 r7 也成立，只有 fragment 断言 `"expect_any" in detail` 在 r7 红 |
| `non-finite-number`（tolerance .nan） | query_type | `True` | `False`，文案含 `tolerance` | **真判别**：r7 放行 → 测试红；r8 拒 → 绿 |
| `expect-any-non-str`（`[1]`） | category | `True` | `False`，文案含 `expect_any` | **真判别**：r7 的 `bad_expect` 只查 list，放行 → 红；r8 拒 → 绿 |

无空转测试：三 case 都实际执行到目标分支；但 UAT §14.1 `:434` 把三 case 统一当作“关闭 M1 的锚”略强——其中 `memory-expect-any-missing` 的行为面 r7 本就拒绝（r7 的 `no_expect` 兜住），新增的是 kind-aware 文案与分支归属。既有 `config-numeric-type` case 在 r7/r8 都绿，不是 r8 的判别器。

---

## ③ 证据链数字自洽 / UAT §十四 overclaim

**自洽部分（独立复算）**：
- `51→54`：diff 精确新增 3 个 parametrize case；我重跑 `test_gold_set_manifest_g413.py` 得 **54 passed**（证据 2.06s，我的 2.11s），一致。
- `1964→1967`：r7 证据 `1971 collected / 1964 passed + 6 skipped + 1 xfailed`；r8 证据 `1974 / 1967 + 6 + 1`；我在 HEAD 独立 `--collect-only` 得 **1974 collected**，差值恰 +3，算术自洽。目录级 1967 **未重跑**（6 分钟级），仅确认收集数。
- 四 sha/verify/gold-manifest 零改动：全部独立复算成立；`r8-shas-*` 与实算逐字同；`ruff` 双 rc=0 也独立复算。
- 行为门 54 绿、`memory-expect-any-missing` 等 3 case 确实被收集执行（diff + 重跑）。

**UAT §十四 overclaim（LOW）**：
- `UAT:435` 称首版「41 条误拒」是「被门＠54 前一轮的 `verify` 自检暴露」。但 `r8-verify-*` 的输出格式来自 `verify_all()`（`tool.py:245-350`），该函数**不调用** `verify_gold_set_file()`；`r8-verify` 与 `r7-verify` 还逐字节相同（`1ea8be…`）。这条证据链无法触发/暴露 kind-aware guard 的 41 条问题。真正能证明的是我这次直调 `verify_gold_set_file()` 对四真实文件全 True，以及 shadow-only 的正向 gate 调用（`test:432-434` 只对两份 shadow 调正向 guard）。
- `UAT:447` 写「83 条×10 键 diffs=0；12 判分函数 AST same=True」，但 `r8-immutability-*` 只写 `AST diffs = 0`，**没有 checked=12**（r7 版才有 `AST checked=12`）；12 这个数在 r8 artifact 中不可见。
- `UAT:448` 的 `r8-dryrun-fullflow` 与 r7 版**逐字节相同**（`4d9bc5…`），尾行仍是 `DRY-RUN r4 OK`——不是 r8 可区分产物（同 r7 L7 形态）。
- `UAT:437-438` 内部键「坏值在 run_tiers 内抛，最终 rc=2」与 M5 实测不符（str 型静默 fail-open；`delivery.min_relevance` null → rc=1）。
- `UAT:434` 三 case 表述见 ②：两个真判别、一个仅文案判别。

---

## ④ r7 清单（M×2 / L×8）逐条点名

| r7 项 | c773e36b 状态 | 依据 |
|---|---|---|
| **M1** vgsf 残余 ⇒ exit 1 / fail-open | **未关闭**：H1（null 回退，r7 拦过 r8 放行）、M1（id/query_type/category 非 JSON）、M3/M4（范围/空串 fail-open）、M5（内部键登记错误） | 上表 |
| **M2** §十二三个测试不存在 | **关闭**（r7 已关，r8 保持）：gate 54 独立重跑绿；3 测试仍在 | `test:1136/1192/1219`（HEAD 行号沿 r7），重跑 54 |
| **L1** alias 写锚定义区/多条目 span | 未处理，仍仅登记 | UAT `:439`；r8 diff 未触 `:683-740` |
| **L2** vault 内部键未守卫 | **未关闭**，且登记理由错 | M5；`tool.py:530-532`；UAT `:437-438` |
| **L3** 非崩溃型类型缺口（group_id int / vault_id int / version list） | 大部分关闭：`tool.py:523-529` 已查 str/null 与有限数值；但 `group_id:""`、`vault_id:null` 语义残留（L-d） | 直调 probe：group_id:int r7 T → r8 F |
| **L4** id null/5、query ""、空主集 | **未关闭**；且 id 的 YAML date/bytes 已从“无害”升级为 M1 exit 1 | `tool.py:471-473`；memory:185/390、vault:245/541 |
| **L5** 重要分支无 committed 测试 | 部分改善：+3 case 覆盖 memory expect_any 缺失/非 str、非有限 tolerance；仍无 null 回退、范围 fail-open、内部键、非 JSON 标注、id/空集 case | `test:1090-1133`；M1-H1 均无专属 case |
| **L6** decoy 证据不严格自包含 + UAT「自包含」措辞 | 未处理（r8 无新 decoy 证据；UAT `:397` 旧措辞仍在） | `UAT:397` |
| **L7** immutability/dryrun 与上轮逐字节同 + 文案 r4 | **未关闭**：dryrun 仍与 r7 逐字节同、仍写 r4；immutability 改了但丢掉 checked=12 | hash 对照；UAT `:447-448` |
| **L8** 事故因果叙述不可验 | 未处理（历史叙述仍在，无新增可验证材料） | UAT `:379-387` |

---

## 未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径

**未被拦下的输入（guard True → runner 崩/放水）**：
- `config.tolerance:` / `max_results:` / `duplicate_ratio:` / `leak_markers:` 显式 null ⇒ memory exit 1；vault `tolerance:` null ⇒ exit 1。
- `config.tolerance: <309+ 位整数>` / `version:` 同类 ⇒ guard 内 `OverflowError` 逃逸 ⇒ exit 1。
- `id: 2020-01-01` / `category: 2020-01-01`（vault `query_type:`）⇒ `json.dumps` TypeError ⇒ exit 1。
- `expect_any: [""]` / `expect_hit: [{file: ""}]` ⇒ 命中率恒 100%，门禁可绿。
- `tolerance: 2` / `duplicate_ratio: 2` / `leak_markers: []` ⇒ 对应门禁维度被静默关闭。
- `forbidden: {path_globs: "secret/**"}`（str）⇒ 硬禁违规检测被逐字符迭代绕过，`hard_violations=[]`，主门可 rc=0。
- `expect_not_hit: [{path_glob: x, max_in_top_k: true/-1}]` ⇒ bool/负值语义偏移；`grade: high/[1]` ⇒ rc=2；`expect_empty: "yes"` ⇒ 类型契约放宽。

**对照输入**：
- r7 `22c1603a` guard vs r8 `c773e36b` guard 的同 fixture 矩阵：r7 **F→r8 T** 的回归集合 = `tolerance:null`、`top_k:null`、`duplicate_ratio:null`、`max_results:null`、`leak_markers:null`、`expect_not_hit:null`、`expect_empty:"yes"`；r7 **T→r8 F** 的改善 = `expect_any:[1]`、`group_id:int`、`version:null/缺失`。两者都 T 的残余 = 空串期望、`grade` 坏值、bool/负 `max_in_top_k`、内部键 str、`tolerance:2`、id date、`leak_markers:[]`。
- 四真实金集：r7 与 r8 guard 直调均 True；sha/verify rc=0；CLI verify 输出与证据一致。

**负控输入**：
- 三个新 case 在 r7 源码上的复算：`non-finite-number`、`expect-any-non-str` **行为红**；`memory-expect-any-missing` 仅文案红。
- gate 54 在 HEAD 绿（含这三 case），说明测试本身可判别；但没有任何 committed case 覆盖 H1/M1-M5 的残余输入（负控缺席）。

**门未覆盖的路径**：
- 显式 null 回退、超大整数溢出、`expect_any/file` 空串、`tolerance/duplicate_ratio` 范围、`leak_markers=[]`、`forbidden/contamination/delivery` 内部 str/null、`id/query_type/category` 非 JSON、`expect_empty` 真值非 bool、`max_in_top_k` bool/负数、`version`/`max_in_top_k` 缺失误拒、`query:""`、主集 `queries: []`。
- 正向 guard 只在 gate 中对 vault shadow（2 条）调过；真实 vault 主集 41 条 hit-only 未被 committed 测试钉住（本次以直调 guard 补证）。
- 两个 runner 的真网络/非 shadow 路径、完整 1967 目录级执行未按边界重跑；7691/7687/8011 未连。

---

## 本轮总评：B=0 / H=1 / M=5 / L=8

`c773e36b` **部分达成**自述目标：kind-aware 分流、memory `expect_any` 缺失/非 str、非有限 tolerance、`group_id/version` 的类型面确实被收紧，三个新 case 有两个是 r7 上真红、gate 54 与 sha/verify 冻结可复算；但守卫把显式 YAML null 重新放回 exit 1 档（相对 r7 的**回退**），且非 JSON 标注、内部键 fail-open、范围/空串退化值、大整数溢出等仍未被拦下，UAT §十四 对 verify 证据与 AST 数字的引用也超出 artifact 支撑，因此不能判定为完整达成。


