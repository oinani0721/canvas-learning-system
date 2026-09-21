## 复核完成（只读）

**绑定**：HEAD=`191de457`（父 `0b0fc8ac`）；工作树除任务前已存在的 2 个未跟踪文件（`codex-review-CARD-G4-13-r11.md` / `codex-prompt-CARD-G4-13-r11.md`）外干净——**我未改任何文件**（含未向该空文件写入，如需落盘请明示）。未连 7691/7687/8011、未跑非 shadow runner、未评 G4-14/R-SLO/L-5/103 条语义。
**复算方式**：`git show 0b0fc8ac:` 取 r10 源码，与 r11 源码同进程加载，同一 fixture 直调 `verify_gold_set_file()`；runner 侧直调真模块 `main()`（只 monkeypatch 出口函数，零 HTTP、零落盘）；残余面用**真函数**（`forbidden_violations`/`is_contaminated`）微复算；沙箱无临时目录 ⇒ pytest 无法启动，门数用 AST 独立重算 + artifact 核对。

---

## ① M1–M5 逐条复算（r10 源码 → r11 源码，同 fixture）

| r10 复核项 | fixture | r10 | r11 | 判定 |
|---|---|---|---|---|
| **M1** 守卫自身 OverflowError | `tolerance`/`duplicate_ratio`/`delivery.min_relevance`/`elbow_drop_threshold = 10**400` | **EXC:OverflowError** | **F**（`超出 [0,1]` / `不是 [0,1] 有限数值`）⇒ rc=2 | **真关闭** |
| M1 同族（同上） | `max_results`/`top_k`/`version = 10**400` | **EXC** | **T（被接受，不崩）** | 崩已关；**放行**（见 LOW-1） |
| **M2** `delivery.hard_cap` 显式 null | `delivery: {hard_cap: null}`（vault+memory 两面） | T | **F**（`不是 ≥0 的整数`）⇒ rc=2 | **真关闭** |
| **M3** 空串恒真 fail-open | `expect_any: [""]`（单条/混合）、`expect_hit: [{file: ""}]`、`expect_not_hit: [{path_glob: ""}]` | T | **F**（`非空字符串列表` / `file 须非空 str` / `path_glob`）⇒ rc=2 | **真关闭**（path_glob 为 r11 额外收口） |
| **M4** 空 `leak_markers` | `leak_markers: []`、`[""]` | T | **F**（`非空字符串列表（空表会让泄漏指标恒 0）`）⇒ rc=2 | **真关闭** |
| **M5** `expect_hit.grade` 类型 | `grade: null / "x" / 1.0 / -1 / true` | T（r10 不查 grade） | **F**（`grade 须 ≥0 int`）⇒ rc=2 | **真关闭** |
| 对照（对照面） | `grade: 3`、`hard_cap: "x"`、`hard_cap: 3.5`、`tolerance: 2`、`.inf`、`leak_markers: [x]`、合法基线 | T 或 F | **同上**（结论逐条一致） | 无回归/无误拒 |

独立全键扫描（900 样本 × 两版本）：**r10 守卫内异常 14 行（7 键 × 2 面）→ r11 = 0 行**；四真金集直调真 manifest 全 `T`（sha `650c5d46…`/`d88d3a0a…`/`c7b25fcc…`/`582df3af…` 与我重算一致），且四份内容**逐条不违反任何新规**（grade ∈{1,2,3} 全 int、无空 file/expect_any/path_glob、无空 leak_markers、无 hard_cap null）⇒ **无误拒面**。

## ② rc 契约兜底：逐输入落档（含 r10 记录方向修正）

| r8/r9/r10 点名的 exit-1 输入 | r10 实际落档（我复算） | r11 落档 |
|---|---|---|
| 守卫内巨整数 | **exit 1**（EXC 在 `:490` 之前，无任何 try） | 数值键 ⇒ rc=2；`max_results`/`top_k`/`version` ⇒ 接受（后续 ≤2） |
| vault `tolerance: null`（`:497 float(None)`）、`query_type: 2020-01-01`（`:541 json.dumps`） | **exit 1** | **rc=2**（外层兜底 + r10 的 json 全量检查） |
| memory `max_results/duplicate_ratio/leak_markers/tolerance: null`（`:136/:138/:137/:374` 无 try 的 `run_queries`/`_main` 路径）、memory `category` 非 JSON（`:390`） | **exit 1** | **rc=2** |
| vault `hard_cap: null`（`:331/:334` 内层 try 吞 → `:345` 外层） / `grade` 坏值（`:131/:163/:280`） | **rc=2 或 rc=1（run_tiers 外层 try `:502-505` 已兜住）——r10 记为 exit 1 是误记** | 守卫直接拒 ⇒ rc=2 |
| `contamination.path_globs: 5` / `forbidden.doc_types: 5` / `markers: 5`（未修） | vault：**rc=2**（同上误记为 exit 1）；memory 不消费 | 不变（异常类现在也兜底） |
| `forbidden.path_globs: "…"`（未修） | r10 记「fail-open（可 rc=0）」——**方向只对一半** | 含 `*` ⇒ 全部结果判硬禁 ⇒ **rc=1**；不含通配符 ⇒ 恒空 ⇒ **fail-open（可 rc=0）** |
| 主集 `queries: []` / `vault_id: ""` / `group_id: ""` | 空哨兵 rc=2 / 退化 vault / benign | 不变 |

**兜底是否吞掉不该吞的**（进程内实测真 `main()`）：真回退 **rc=1 保留**（vault/memory 双面）、`KeyboardInterrupt` **透传**、argparse `SystemExit(2)` **透传**、`--update-baseline` 无 `--reason` 仍 **rc=2** ✅。可接受但应登记的两处见 **LOW-4**（报告阶段异常替换真结论；baseline 写非原子）。

## ③ 零语义改动（除 rename）

把 r11 归一化（`def _main()` → `def main()` + 剥离新 wrapper）后与 r10 **逐字节相同**：vault **True**、memory **True**。⇒ 判分函数与 `_main` 主体确为零改动，§18.1 该条**不 overclaim**。

## ④ 新增 8 个门 + 数字自洽

- 6 个 guard case：**逐条真判别**——r10 源码上 `huge-int-tolerance` = **EXC**，其余 5 条 = **T（红）**；r11 = **全 F 且断言 fragment 命中**（`tolerance`/`hard_cap`/`expect_any`/`leak_markers`/`expect_hit`/`grade`）。旧 10 条两版全 F（对照，无空转）。
- 2 个兜底测试：r10 源码上 `main()` **抛异常**（红），r11 返回 **rc=2 + 文案**（绿）⇒ 真判别。
- gate **70** = 62 + 8：我以 AST 独立重算该文件用例数 **= 70**（其中形状 parametrize 22 = 16 + 6），与 `r11-gate-green`（`70 passed`，2.19s，hash 与 r10 不同 = 真重跑）一致；目录级 **1983 = 1975 + 8**（r11 artifact 为 330s 真跑，末行 `1983 passed, 6 skipped, 1 xfailed`）；`r11-named` 47 passed 含 metric-guard 10 条（rename 未破坏 G4-12 度量守卫）。**数字全自洽。**

## ⑤ UAT §十八 / §十六.2

- §18.1 六行整改对照 **逐条为真**（我按源码+行为双重复算）；「判分函数与 `_main` 零改动」为真；「未证明」3 条诚实。
- §18.2 数字级无 overclaim（70/47/83/1983/rc=0 均可复算）；但 `r11-verify/shas/immutability/dryrun-fullflow` 与 r10 **逐字节相同**（确定性重放，对 r11 **零判别力**），「12 个判分函数 AST same=True」在 3 行 artifact 里**不可见**（只见 `AST diffs = 0`）——见 LOW-5。
- §16.2 **仍未更新**：其 M1–M5 是 r9 那一套（多数已被 r10/r11 关闭），「M4 内部键（rc=2 档）」实测不准，「触发前提：需先手改冻结金集」仍是 r9 判定不成立的因果叙述 — 见 LOW-6。

---

## 逐条判定

- **BLOCKER**：未发现。
- **HIGH**：未发现。
- **MEDIUM-1** — `forbidden`/`contamination` 内部键未修，且**登记描述与实测不符**（`gold_set_manifest_tool.py:578-581` 只查顶层 dict；`run_vault_retrieval_regression.py:145-151` 逐字符迭代 str）。三种落档：str 含 `*` ⇒ **rc=1 假硬禁**；str 无通配符 ⇒ **fail-open（可 rc=0）**；int 诸键 ⇒ **rc=2**。一句话复现：`forbidden_violations({"source_path":"notes/x.md"}, {"path_globs":"secret/**"})` → 返回 2 条硬禁；换 `"qqq"` → 返回 `[]`。（r10 记该例为「fail-open」只对一半；§16.2 记「rc=2 档」两版都测不准 —— 因含 rc=1 假硬禁 / 硬禁门 fail-open 两面，按 M 记。）
- **LOW-1** — `_is_finite_number` 对 int 无上界（`gold_set_manifest_tool.py:398-402`；`run_vault_retrieval_regression.py:191,229-232`）：400 位 `top_k`/`max_results`/`version` 由 EXC 变「接受」。复现：`config.top_k: <400 位 9>` → r10=EXC / r11=T。
- **LOW-2** — grade 收口严于 runner 真实失败面（`:512-526`）：`grade: 2.0` / `"2"` 被拒，而 `int(2.0)`/`int("2")` 本可消费。复现：加 `grade: 2.0` → r11=F（方向 fail-closed，属过度拒绝）。
- **LOW-3** — 兜底测试只钉 rc=2（`test_gold_set_manifest_g413.py:1380-1417`）：无门钉住「rc=1 不被吞」「KeyboardInterrupt/SystemExit 透传」；我手工实测三项均符合 docstring，但非门禁。
- **LOW-4** — 报告阶段异常会替换真结论：vault `print_report` 在硬禁判定之前（`:521` vs `:523`），BrokenPipeError ⇒ 真硬禁被判成 rc=2；`--update-baseline` 非原子（`:549` 先 append history、`:563` 后 write baseline）⇒ 可留半态。
- **LOW-5** — 证据显示层（UAT `:592-593`）：4 件 artifact 与 r10 逐字节相同、零判别力；「12 判分函数 AST same=True」不可见（claim 本身为真，我已逐字节证明）。
- **LOW-6** — §16.2 未随 r11 更新、§18.1 只写「照 §十六.2」未逐条点名剩余项（UAT `:496-546`、`:588`）。
- **LOW-7** — rc 语义名实不一致：vault docstring `:36`、memory docstring `:28` 只写「2 = 环境不可用」，与正式契约「环境**或输入错**」不符（对照 `:490-494`/`:359-363`）。

---

**未被拦下的输入**（守卫 T / fail-open / 误档）：`forbidden.path_globs` 为 str（含 `*` ⇒ rc=1；无通配符 ⇒ fail-open）；`contamination.path_globs/doc_types`、`forbidden.doc_types/markers` = int（TypeError ⇒ rc=2）；`config.top_k/max_results/version` = 400 位整数；主集 `queries: []`；`vault_id: ""`；`expect_hit[i].contains` 任意形态（`str()` 强转/短路）；`verdict_at: <未加引号 ISO 时间戳>`（过度拒绝，非放行）。
**对照输入**：16 条 committed 形状 case 中旧 10 条两版双 F；`grade: 3`、`hard_cap: "x"|3.5`、`tolerance: 2|.inf`、`leak_markers: [x]`、合法基线两版同结论；四真金集 T→T、sha/manifest 零漂移。
**负控输入**：6 个新 case 在 r10 源码上 EXC/T（红）→ r11 F（绿）且 fragment 命中；2 个兜底测试在 r10 上抛异常（红）→ r11 rc=2（绿）；`_import_runner` 载入的是磁盘真文件（我独立 exec 真源码复核 `_main`/`main` 存在与行为）。
**门未覆盖的路径**：目录级 1983 本体（沙箱无临时目录，pytest 起不来 ⇒ 只做 AST 计数 70 + artifact 核对 + 算术）；两 runner 的真 shadow/main 全流程与残余键的 runner 实跑（边界禁止 ⇒ 只用真函数微复算 + 调用点代码位置推定）；「rc=1 保留 / 中断透传」无门；`--update-baseline` 半态的实测未做。

**本轮总评：B=0 / H=0 / M=1 / L=7**

r11 达成自述目标：M1–M5 **逐条真关闭**（含 r10 引入的守卫自崩）、6 个新 guard case 与 2 个兜底测试**真判别**、judging/`_main` **逐字节零改动**、70/1983 自洽、四真金集无误拒；rc 契约兜底使「异常冒充 exit 1」在实际入口关闭（真回退 1 档与中断语义未被吞）。剩余面集中在**未修的 contamination/forbidden 内部键**（rc=1 假硬禁 / 单字符串 fail-open，且登记描述不准）与 7 条 LOW（int 无上界、grade 过度拒绝、兜底测试盲区、报告阶段 rc=2 语义、证据零判别力、§16.2 未更新、docstring 名实不符）。


