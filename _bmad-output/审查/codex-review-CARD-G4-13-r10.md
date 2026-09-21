复核完成。只读；未改任何文件；未连 7691/7687/8011；未跑非 shadow runner；未评 G4-14/R-SLO/L-5/103 条语义。绑定：HEAD=`0b0fc8ac8dcdfeff81bbef3352ebbe0538055e8d`（父 `908d459f`）；工作树除任务前已存在的两个未跟踪 r10 review/prompt 文件外干净；金集/清单 blob 与 `908d459f` 逐字相同（4 sha 独立重算 = `650c5d46…`/`d88d3a0a…`/`c7b25fcc…`/`582df3af…`）。复算方式：`git show 908d459f:` 取 r9 源码副本，与 r10 源码同进程加载，同一 fixture 矩阵直调 `verify_gold_set_file()` 逐版本对照；独立重跑行为门与目录收集数；对 runner 内部行做微复算（未实跑 runner）。

---

# CARD-G4-13 r10 独立复核（开发/证据面）

## ① r9 M×5 逐类复算（r9 源码 vs r10 源码，同 fixture）

| r9 复核 M 项 | fixture | r9 | r10 | 结论 |
|---|---|---|---|---|
| **M1** 非 JSON 标量 | `id/category/query_type: 2020-01-01`、`origin: !!binary`、`tags: !!set`（6 例） | 全 T | 全 F（`含不可 JSON 序列化的标量`） | **已拦** |
| **M2** 超大整数 OverflowError 逃逸 | `tolerance/version/max_results/duplicate_ratio/top_k = 10**400`（5 例） | 全 **EXC** | 全 **EXC**（`OverflowError: int too large to convert to float`） | **未拦（MEDIUM）** |
| **M3** 范围/空集 | `tolerance: 2`、`duplicate_ratio: 2` | T | F | 已拦 |
| | `leak_markers: []` | T | **T** | **未拦（MEDIUM）** |
| **M4** 空串期望值 | `expect_any: [""]`、`expect_hit: [{file: ""}]` | T | **T** | **未拦（MEDIUM）** |
| **M5** 内部键 | `delivery.min_relevance: null`、`hard_cap: "x"` | T | F | 已拦 |
| | `contamination/forbidden` 内部键（str/int） | T | **T** | 未拦（§17.1 已登记） |
| | **`delivery.hard_cap: null`** | T | **T** | **新口子（MEDIUM）** |

**MEDIUM-1（M2 未收口 + §17.1 overclaim）** — `backend/scripts/gold_set_manifest_tool.py:538-543`（`math.isfinite(v)` 在范围检查之前，巨整数直接抛 `OverflowError`）、`:555-557`（version）、`:566-575`（`delivery.min_relevance: <巨整数>` 同样 EXC）；契约见 `:402-404`「环境/输入错一律走 (False, 文案)、**不以异常逃逸**」。两个 runner 的调用点无 try/except（`run_vault_retrieval_regression.py:490`、`run_memory_retrieval_regression.py:359`）⇒ 异常冒泡为未捕获 traceback = **exit 1**，正是 M2 点名的 rc=1 污染。复现：`config.tolerance: <400 位 9>` → r9=EXC / r10=EXC。UAT §17.1 第 3 行把「超大整数」写成已收（`_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19.md:539`）与实测不符。

**MEDIUM-2（新口子：`delivery.hard_cap: null`）** — `gold_set_manifest_tool.py:561-565`（`hc is not None` 把显式 null 当「未设置」跳过；同一区块的 `min_relevance/elbow_drop_threshold` null 却拒 ⇒ 自相矛盾）。runner：`run_vault_retrieval_regression.py:331` `int(None)` 被内层 try 吞掉（Tier-D 全空 ⇒ rc=1），`:345` `int(None)` 在 try 外（对 `expect_empty` 条目）⇒ 未捕获 TypeError **exit 1**；真 vault 集有 22 处 `expect_empty` 命中行。复现：fixture `delivery: {hard_cap: null}` → 守卫 T（已复算）+ 微复算 `int({"hard_cap": None}.get("hard_cap", 10))` → TypeError。

**MEDIUM-3（r9 M4 未收口、且 §17.1 未登记）** — `gold_set_manifest_tool.py:530-532`（`expect_any` 元素只查 str）、`:504-508`（`file` 只查 str）。`expect_any: [""]`/`expect_hit: [{file: ""}]` 守卫 T（r9=r10）；`norm_text("")==""`、`"" in text` 恒真 ⇒ memory hit@5 / vault hit@10 **恒 100%**（fail-open）。复现：把任一 memory 条目 `expect_any` 换成 `[""]`，守卫 rc=0。

**MEDIUM-4（r9 M3 剩余项：`leak_markers: []`）** — `gold_set_manifest_tool.py:576-579`（只查「是字符串列表」）；`run_memory_retrieval_regression.py:114-115/137/170` 的 `any(... for m in [])` 恒 False ⇒ `leak_rate` 恒 0 ⇒ 泄漏类指标回退在门里不可见（rc=0）。UAT §17.1「其余 M/L」枚举（`:545-546`）未点名此项。

**MEDIUM-5（新点名：`expect_hit[i].grade`）** — 同族 `sha 相符但 runner exit 1`：`gold_set_manifest_tool.py:504-508` 不查 grade；`expect_hit: [{file: f, grade: null}]` 或 `grade: "x"` → 守卫 T（已复算）→ `run_vault_retrieval_regression.py:131/163` 的 `int(...)` 在无 try 路径（`:349`）⇒ ValueError/TypeError exit 1。r9 的 M1–M5 未列此项（新点名），严重度按 exit-1 档记 M。

**M1（对照）**：`id: ""`/`id: 123`/`query: 123`/`language: 0`、`tolerance: .inf` → 全 F（`tool.py:477-488`、`:542`），无空转。

## ② 误拒复算（四真集 + 未来合法扩展）

- **四份真金集**：r9/r10 双双 T、rc=0（我显式指真 manifest 直调）；`r10-verify`/`r10-shas` 与我的独立重算逐字一致 ⇒ **无误拒**。
- **合法扩展全 T**：新键/unknown 键、`source` 任意形态（含 str）、`user_verdict` 映射、`verdict_by/verdict_at: null`、**缺 `language`**、`expect_empty` 与 `expect_not_hit` 并存、`expect_empty: true + expect_hit: []`、`version: 0`（shadow 合法）、`version: -1` ⇒ 全 T。`expect_hit: []` **单独**出现 → F（`缺期望键`，r9 起既有、非 r10 新增；对照项，不算误拒）。
- **LOW（唯一误伤面）** — 全文档 `json.dumps`（`tool.py:471-476`）会把 **runner 根本不读**的标注字段里的非 JSON 标量整类拒掉：手写未加引号的 `verdict_at: 2026-09-20T00:00:00Z`（datetime）或 `origin: 2020-01-01`（date）→ r9=T / r10=F；而 runner 只把显式键写进 report（memory:182-190/390，vault:243-247/541），不 dump 整份 gold ⇒ 守卫严格强于实际失败面。方向 fail-closed、`apply-verdicts` 自写值恒带引号（管线内不自伤），故记 LOW。

## ③ 新残余（守卫 T → exit 1 / fail-open）

- **contamination/forbidden 内部键（登记项，非新）**：`:558-560` 只查顶层 dict。`forbidden.path_globs: "secret/**"`（str）在 `run_vault_retrieval_regression.py:148` 逐字符迭代 ⇒ 硬禁门静默失效（可 rc=0）；`contamination.path_globs: 5` 在 `:140/318` 迭代 int ⇒ 未捕获 TypeError exit 1；`forbidden.doc_types: 5`（`:151/241`）同理。均为守卫 T（已复算）。
- **`cfg["version"]` 边界**：0/-1 放行（shadow 用 0 属合法，无门禁语义）；巨整数 → 归入 MEDIUM-1 的 EXC。
- **`group_id: ""` / `vault_id: ""`**：守卫 T；memory runner `:150 if group_id:` 把 "" 当未设置（**benign**）；vault runner `:197 str(cfg.get("vault_id","canvas_vault"))` 对 "" 会让上下文指向退化 vault（L-d 遗留，未变）。
- **LOW-4（定性不准）**：§17.1 把 contamination/forbidden 内部键标成「rc=2 档」（`:546`），实测是 **exit 1（未捕获）或 fail-open（rc=0）**两种更差结局。
- 新增/遗留：主集 `queries: []` 仍 T（§16.2 M3 项未动）；`unquoted ts` 见 ②。

## ④ 6 新 case 判别性 / gate 62 / 目录级 1975

- 6 例原样喂 r9 源码 = **全 T**，喂 r10 = **全 F 且断言 fragment 命中**（`non-json-scalar`/`empty-query-string`/`negative-max-in-top-k`/`range-tolerance`/`expect-empty-with-expect-hit`/`delivery-hard-cap-type`）⇒ **真判别、无空转**（负控成立）。
- 形状 parametrize 16 条（10 旧 + 6 新，`test_gold_set_manifest_g413.py:1090-1189`）；独立重跑 **62 passed（2.10s）**；`--collect-only` 目录级 **1982 collected** = 1975 passed + 6 skipped + 1 xfailed（artifact `r10-regression-outside-sandbox…153105.txt` 353.53s 同数）⇒ 1975 = r9 的 1969 + 6，**数字自洽**。目录级 1975 本体未重跑（6 分钟级，只做 collect-only + 算术 + artifact 核对）。

## ⑤ UAT §十七 overclaim / §十六.2 诚实性

- **MEDIUM-2/3 同因**：§17.1 两行（`:539` 超大整数、`:540` delivery 内部键）**overclaim**——M2 仍 EXC、`hard_cap: null` 仍放行；§16.2 却仍把 M2 列在册（自我矛盾）。
- **LOW-5（登记枚举不完整）**：§17.1「其余 M/L（…）维持登记」（`:545-546`）只点名 contamination/forbidden + alias + L-5，漏掉 r9 M3 的 `leak_markers: []`、r9 M4 的空期望值、§16.2 M3 的主集 `queries: []`；且 §16.2 的 M1–M5 与 r9 复核的 M1–M5 并非同一套（M3/M4 换项）。§16.2 末有「见 r9 全文」指针，信息未丢失 ⇒ LOW。§16.2「触发前提：需先手改冻结金集」（`:518`）仍是 r9 复核①判定「不成立」的因果叙述，r10 未修正。
- **LOW-6（证据判别力/引用缺口）**：`r10-verify`（sha `1ea8be28`）、`r10-shas`（`aafefff3`）、`r10-dryrun`（`4d9bc5d2`，末行仍写「DRY-RUN r4 OK」）、`r10-immutability`（`ddd921c6`）与 r7–r9 **逐字节相同**（确定性重放，对 r10 零判别力）；§17.2 声称的「83 条×10 键」「12 判分函数 AST same=True」在 3 行 artifact 里不可见（只显示 `unchanged=58/25`、`AST diffs = 0`）。无数字级 overclaim：62/37/1975/rc=0 均可独立复算；§17.3 三条未证明声明诚实。

---

**未被拦下的输入**（守卫 T，或异常逃逸）：`tolerance/version/max_results/duplicate_ratio/top_k/delivery.min_relevance = <400 位整数>`（EXC ⇒ exit 1）；`leak_markers: []`；`expect_any: [""]`；`expect_hit: [{file: ""}]`；`expect_hit[i].grade: null|"x"`；`forbidden.path_globs: "secret/**"|5`；`contamination.path_globs: 5`；`delivery.hard_cap: null`；主集 `queries: []`；`vault_id: ""`/`group_id: ""`；`verdict_at: <未加引号 ISO 时间戳>`（后者是过度拒绝而非放行）。
**对照输入**：M1 六例 + `tolerance:2`/`duplicate_ratio:2`/`max_in_top_k:-1`/`min_relevance:null`/`hard_cap:"x"`/`language:0`/`query:""`/`id:""` → 全 T→F；四真金集 T→T、sha/manifest 零漂移。
**负控输入**：6 个 committed case 在 r9 源码上全 T（红）、r10 全 F（绿）且 fragment 命中；`expect_hit: []` 单独出现两版均 F（非本段引入）；`expect_empty×expect_not_hit`、`version: 0` 两版均 T（防误伤反证）。
**门未覆盖的路径**：目录级 1975 本体、两个 runner 的 shadow 路径（边界禁止）未跑；`hard_cap: null`/`grade: null` 的 runner 结局由调用点代码位置 + 微复算推定（未实跑 runner）；`contamination/forbidden` 的 fail-open 只做静态 + 微复算，未连 LanceDB/后端。

**本轮总评：B=0 / H=0 / M=5 / L=6**

- r10 达成其自述的**部分**核心目标：M1 类（非 JSON 标量）整类真关闭、6 个新 case 真判别且 gate 62 绿、金集/manifest/runner 零改动、四真金集不误拒、数字全自洽；矛盾组合两条新规（vault/memory）实测有效。
- 但「r9 复核 M×5 的边界收敛」只关闭约 1.5/5 类：**M2 完全未拦**（仍是守卫内异常逃逸 + runner exit 1，且是最该按 rc=1 档处理的一条），**M4 完全未拦**，M3 剩 `leak_markers: []`，M5 剩 contamination/forbidden 内部键并**新开 `hard_cap: null` 口子**；另新点名 `expect_hit.grade`（exit-1 档）。§17.1 两行 overclaim、§16.2 枚举与 r9 复核不同套（有全文指针兜底）；证据面沿用 r7–r9 的逐字节旧档，无 r10 判别力。
