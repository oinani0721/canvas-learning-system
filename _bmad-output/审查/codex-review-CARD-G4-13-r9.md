复核完成。以下为 r9 独立复核报告（只读；未改任何文件；未连 7691/7687/8011；未跑非 shadow runner）。

---

# CARD-G4-13 r9 独立复核（Codex × DeepSeek V4.1 Flash · 开发/证据面）

**绑定**：HEAD = `908d459ff2aea8cf5c0e2b8894272b9d440beb9f`（= `908d459f`），父 `c773e36b`。仓库工作树除任务开始前已存在的两个未跟踪 r9 review/prompt 文件外干净。独立复算方式：从 `22c1603a`（r7）/`c773e36b`（r8）/`908d459f`（r9）各取 `gold_set_manifest_tool.py` 源码，同一 fixture 矩阵直调 `verify_gold_set_file()` 逐版本对照；重跑行为门；算术核对；sha/verify 逐字比对；未跑目录级 1969（验证其收集数算术与既有 artifact）。

---

## ⓪ H1 是否真关闭 —— **（未发现 blocker）** 显式 null 族已修回；附一条测试钉死缺口（见 ②）

逐 case 复算（`T`=放行、`F`=拒绝；vault 侧与 memory 侧各自独立 manifest）：

| 输入（显式 `key:` 空值 ⇒ YAML null） | r7 `22c1603a` | r8 `c773e36b` | r9 `908d459f` | r9 拒绝文案锚 |
|---|---|---|---|---|
| `tolerance:` (memory) | F | **T** | **F** | `config.tolerance 不是有限数值: None` |
| `duplicate_ratio:` (memory) | F | **T** | **F** | `config.duplicate_ratio 不是有限数值` |
| `max_results:` (memory) | F | **T** | **F** | `config.max_results 不是有限数值: None` |
| `top_k:` (memory) | F | **T** | **F** | `config.top_k 不是有限数值: None` |
| `leak_markers:` (memory) | F | **T** | **F** | `config.leak_markers 不是字符串列表（…）: None` |
| `tolerance:` (vault) | F | **T** | **F** | 同 memory 文案 |
| `duplicate_ratio:` / `max_results:` (vault) | F | **T** | **F** | 同上 |
| `top_k:` (vault) | F | **T** | **F** | 同上 |
| `leak_markers:` (vault) | F | **T** | **F** | 同上 |
| `expect_hit:` = null | F（文案为「缺期望键」） | F（同族误报，但**是拒**） | **F** | `expect_hit missing`/缺期望键；r9 下 `expect_not_hit` 存在时走 `expect_not_hit 形态不对` |
| `expect_not_hit:` = null（条目另有合法 `expect_hit`） | F（旧判定 `nots is not None`，null ⇒ 拒） | **T**（`nots is not None`＝False ⇒ 跳过） | **F** | `vault 条目 'q1' 的 expect_not_hit 形态不对` |

结论：**H1 的五类面（数值键、`leak_markers`、`expect_hit`、`expect_not_hit`）在 r9 全部「键存在即须合法类型」——显式 null 一律拒**，与作者自述一致。`group_id:`/`vault_id:` = null 复算仍放行（合法语义，未回归）。**未发现漏网的显式 null 面**：逐键扫过 `version`/`contamination`/`forbidden`/`delivery`（null ⇒ 拒）、`expect_empty`（null ⇒ 拒）、`id`/`query`（null 在 r7/r8/r9 三个版本均放行，属已登记长尾，不是本族回归）。修复锚点：

- `backend/scripts/gold_set_manifest_tool.py:487-499`（`"expect_hit" in q` / `"expect_not_hit" in q` / `isinstance(max_in_top_k, bool)`）
- `backend/scripts/gold_set_manifest_tool.py:518-536`（`num_key not in cfg` / `id_key in cfg` / `"leak_markers" in cfg`）

**但有一条与 H1 直接相关的测试钉死缺口（LOW，见 ②）**：committed 的 `explicit-null-not-hit` fixture 是 `expect_hit: [{file: f, grade: 1}] + expect_not_hit: null`——我把它原样喂 r8 源码：r8 **放行（T）**，r9 拒（F），所以判别性成立。但该 fixture **没有**覆盖 r8 真正漏放的形态「`expect_not_hit:` null 且**没有其它期望键**」与 r8 的 `expect_hit: []` 分支组合；r8 报告的 H1 原形之一（无其它键的 not_hit null）无 committed 负控。不是功能回归，是「r8 漏放族未被 committed 测试逐一钉死」。

---

## ① §十五「长尾登记」口径 —— **MEDIUM（登记口径部分不成立）**

§十五.1 写：长尾「在冻结的四份金集里不存在，**需先手改金集并重建 manifest 才能出现**」。逐条复算后，**该句的前提对、推论不成立**：

- 这些形态确实不在当前四份金集（四 sha 逐字复核：`650c5d46…`/`d88d3a0a…`/`c7b25fcc…`/`582df3af…` 与 r9 artifact 相同，且 `c773e36b→908d459f` 对金集/manifest 的 blob 哈希完全相同）。
- 但触发它们**不需要「手改金集」这一特殊动作**：
  - **fail-open 族**（`tolerance: 2`、`duplicate_ratio: 2`、`leak_markers: []`、`expect_any: [""]`、`expect_hit: [{file: ""}]`）只需一次**普通内容扩充/编辑**（新增字段或改一个值）＋ 正常跑 `build --bump-revision`（`gold_set_manifest_tool.py:196-215`）重算 sha/count 即可；`frozen: true` 只挡无理由重建（`:34-37` 的设计注释），**不挡带 `--reason` 的常规重建**。守卫对这批输入**全放行**（我逐条复算：r7/r8/r9 三版全 T）。
  - **M1 族**（`id`/`category`/`query_type` 的 YAML 非 JSON 标量，如 `id: 2020-01-01` 被 PyYAML 解析成 `datetime.date`）同样可由**不带引号的日期风格标注**自然引入，然后 build 重算 manifest 即可进冻结态；三个版本守卫全放行 ⇒ 两个 runner 的 `json.dumps(report)` 抛 `TypeError` ⇒ exit 1（`run_memory_retrieval_regression.py:185/390`、`run_vault_retrieval_regression.py:245/541`）。
- 唯一「需手改」的是**不重建 manifest 就想让守卫看到坏内容**——但那样 sha 会先不符、在守卫更早处被拒（`tool.py:452-453`）；所以「需手改+重建」实际读作「需一次正常内容改动+一次带理由的 build」，而不是「要绕过冻结」。长尾**登记**本身（移交主 session / 终轮）是诚实的范围裁量；**不成立的是「冻结态下触发不了 / 要手改」的因果叙述**，且 M1/M2 两条（exit 1 档）在「防御性加固」措辞下被弱化描述。

一句话可复现：把 `vault_gold_set.yaml` 任一条的 `query_type: x` 改成 `query_type: 2020-01-01`（或把某条 `expect_any` 改成 `[""]`），`build --bump-revision --reason test` 后用本工具 `verify` → rc=0；再按 runner 取值行跑（或直调 `run_queries`/`run_tiers`）→ 前者 `json.dumps` TypeError exit 1，后者指标恒 100%。**长尾里 M1（非 JSON id/category/query_type）与 M2（超大整数）是唯一可确定污染 rc=1 档的项，登记为「防御性」比实际严重度低一档。**

附：**M3/M4/M5 的 fail-open 全部仍在**（逐版本复算见 ④ 表），与 r8 报告一致，未因 r9 修复而变化。`delivery.min_relevance: null` 的 `float(None)` 在 `try/except Exception`（`run_vault_retrieval_regression.py:330-338`）内被吞成 Tier-D 空结果 ⇒ **rc=1 路径**（r8 报告 M5 的定性仍成立）；`forbidden.path_globs` 为 str 时 `for g in "secret/**"`（`:148`）逐字符迭代 ⇒ 硬禁检测静默为空 ⇒ 主门可 rc=0，**fail-open 仍在**。

---

## ② 新 case 判别性 / gate 56 / 目录级 1969 —— **LOW（判别性成立，但有一处 fixture 弱化 + 一处证据瑕疵）**

- **判别性（独立复算，把 5 个 shape case 的 fixture 原样喂三版源码）**：

| case | r7 assert | r8 assert | r9 assert |
|---|---|---|---|
| `memory-expect-any-missing` | FAIL（文案不同） | PASS | PASS |
| `non-finite-number`（`.nan`） | FAIL（放行） | PASS | PASS |
| `expect-any-non-str`（`[1]`） | FAIL（放行） | PASS | PASS |
| `explicit-null-numeric`（tolerance null） | FAIL（拒但文案不同…实为 r7 拒、断言 fragment 命中） | **FAIL（放行 = H1 回归）** | PASS |
| `explicit-null-not-hit` | FAIL（拒，但文案不含 fragment） | PASS | PASS |

  即：**两个新 case 在 r8 源码上都会红（真判别）**，在 r9 上绿；无空转，目标分支真实执行（我按 committed fixture 复算，非仅凭 artifact）。

- **gate 56**：独立重跑 `test_gold_set_manifest_g413.py` = **56 passed（2.04s）**，与 `r9-gate-green-…151702` 的 `56 passed (2.07s)` 一致。
- **目录级 1969**：独立 `--collect-only` = **1976 collected**（r8 时我上一轮的收集数为 1974），差 +2 恰为两个新 case；1976 = 1969 passed + 6 skipped + 1 xfailed，**算术自洽**；1969 = r8 的 1967 + 2。1969 本体未重跑（6 分钟级，边界允许），但收集数、skip/xfail 结构与 artifact 均对得上。
- **LOW（证据瑕疵）**：`r9-gate-green-*.txt` 有 **3 份**，其中 `…151618` / `…151643` 两份是 **`1 failed / 55 passed`**（失败 case id 含 `expect_hit: []` 的旧 fixture），只有 `…151702` 是 56 passed；三份都进了本 commit。UAT §十五.2 只写「行为门 56 passed」没有提这两份红档，且失败 artifact 里 **没有**中间态说明（红档对应的 fixture 已被最终 commit 替换，无法从 commit 内重建）。这**不构成对 r9 功能的 overclaim**（最终树独立复跑 56 绿），但**审计轨迹不诚实**：读者在 evidence 目录里会同时看到 2 红 1 绿、而 UAT 只呈现绿。

---

## ③ 证据链 / UAT §十五 overclaim —— **LOW（两处 citation 级问题；无数字级 overclaim）**

逐条核对后，**数字全部自洽、无 overclaim**；两处是「引用不够紧」：

- `r9-verify-*` **与 `r8-verify-*`、`r7-verify-*` 逐字节相同**（sha256 `1ea8be28…`），`r9-dryrun-fullflow-*` 与 `r7/r8` 同（`4d9bc5d2…`），`r9-immutability-*` 与 `r8-immutability-*` 同（`ddd921c6…`）。前两者正确（金集/清单未变、verify 文本确定）；但**这三份 artifact 对 r9 的 null 修复没有判别力**，作为「r9 干过什么」的证据价值≈0，只证明「r9 没有把已绿的东西弄红」。`r9-immutability` 里 `AST diffs = 0` 与 UAT 写的 `12 判分函数 AST same=True` 的「12」在 artifact 里仍不可见（r8 报告的 L7 延续）。
- 其余：`r9-named` 37 passed（点名两文件 2+35=37，我核对过 artifact 的 collected=37 与文件构成）；`r9-regression-outside-sandbox` 1969/6/1 与收集数算术一致；`r9-ruff` 双 rc=0；`r9-shas` 四 sha 与我独立复算逐字相同。§十五.3 的「未证明」四条是诚实的自我限制。

---

## ④ 未关闭的 B/H/M/L 清单（继承自 r8，逐条给 `file:line` + 复现思路）

### MEDIUM（未关闭，均为 r8 已报、r9 登记未修；逐版本复算仍可复现）

- **M1 非 JSON 标量 `id`/`category`/`query_type` ⇒ exit 1（未关闭）** — `gold_set_manifest_tool.py:471-473`（只查 `"id" in q`、`query` 为 str，不查 id 类型、完全不查 `category`/`query_type`）；`run_memory_retrieval_regression.py:185/390`、`run_vault_retrieval_regression.py:245/541`。复现：任一金集条目的 `id: 2020-01-01`（或 `category`/`query_type` 同）→ 守卫三版全 T → runner `json.dumps` TypeError → exit 1。
- **M2 超大整数在守卫内 `OverflowError` 逃逸（未关闭）** — `gold_set_manifest_tool.py:522/528`（`math.isfinite(v)` 无 `OverflowError` 保护），与 `:402` 的「不以异常逃逸」契约冲突。复现：`config.tolerance: <400 位 9>` → r8/r9 守卫均 **EXC（OverflowError）**（r7 反而 T），runner 侧为 `float()` 溢出 ⇒ exit 1。
- **M3 范围/空集 fail-open（未关闭）** — `gold_set_manifest_tool.py:518-522`（只查有限性）；`tolerance: 2`、`duplicate_ratio: 2`、`leak_markers: []` 三版全 T。`tolerance` 使 `delta < -tolerance` 恒假（`run_memory_retrieval_regression.py:307-310`、`run_vault_retrieval_regression.py:436-439`）；`duplicate_ratio: 2` 使近重复恒 0；`leak_markers: []` 使 `is_leaked` 恒假（`run_memory_retrieval_regression.py:114-115`）。
- **M4 空串期望值 fail-open（未关闭）** — `gold_set_manifest_tool.py:487-490`（`file` 只查 str）、`:506-513`（`expect_any` 元素只查 str）；`expect_any: [""]`、`expect_hit: [{file: ""}]` 三版全 T，runner `norm_text("")==""` ⇒ hit@5=100%。复现：把任一 memory 条目的 `expect_any` 换成 `[""]`，跑 shadow runner 看 hit 恒 1.0（无需真改动金集也能在副本上复现）。
- **M5 `contamination`/`forbidden`/`delivery` 内部键（未关闭）** — `gold_set_manifest_tool.py:530-532` 只查顶层 dict；`forbidden: {path_globs: "secret/**"}`（str）在 `run_vault_retrieval_regression.py:148` 逐字符迭代 ⇒ `hard_violations` 空 ⇒ 硬禁门 rc=0（fail-open）；`delivery.min_relevance: null` 在 `:331-338` 被 `except Exception` 吞 ⇒ Tier-D 全空 ⇒ rc=1（与 §14 旧文案不符）。

### LOW（未关闭/新发现）

- **L-d（2 条，未关闭）** — `vault_id: null` 通过 `tool.py:525`，但 runner 只在缺键时用默认值：`run_vault_retrieval_regression.py:197` 的 `group_id` 取 `str(None)` ⇒ 静默指向 `"None"` 而非 `canvas_vault`（可复现）；`group_id: ""` 放行但语义等价 null（`:524-525` 只排除非 str 非 null）。
- **L-e/L-f（未关闭）** — `expect_empty` 与 `expect_hit` 并存、`expect_empty` 非 bool 的 memory 真值路径（`tool.py:506-513` 的 `continue` 在前）三版行为一致放行；r9 的 `expect_hit:` null 在**无** `expect_not_hit` 时只报「缺期望键」，不是类型错（信息量低但方向安全）。
- **L-新增：新 case 的 fixture 弱化（LOW）** — `test_gold_set_manifest_g413.py:1141-1146`：最终版 `expect_not_hit` fixture 带 `expect_hit: [{file: f, grade: 1}]`，避开了 r8 的 `expect_hit: []` 分支，导致「r8 的 `expect_not_hit: null` 漏放」只被间接钉住；建议补一条 `expect_hit` 缺失 + `expect_not_hit: null` 的负控（r8 源码上应为 T，r9 应为 F）。
- **L-新增：`r9-gate-green` 红档未披露（LOW）** — 见 ②；`_bmad-output/审查/evidence-g413/r9-gate-green-20260920T151618.txt`、`…151643.txt` 与 `UAT §十五.2` 的呈现缺口。
- **L-遗留：`verify`/`dryrun`/`immutability` artifact 逐字节与 r7/r8 同（LOW）** — 见 ③；`r9-immutability` 的 `AST checked=12` 无 artifact 支撑。

---

## 未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径

**未被拦下的输入（守卫 T → runner 崩/放水；均为 r8 遗留、r9 未修）**：`id/category/query_type: 2020-01-01`（exit 1）；`tolerance/version: <309+ 位整数>`（守卫内 OverflowError ⇒ exit 1）；`tolerance: 2`、`duplicate_ratio: 2`、`leak_markers: []`（fail-open）；`expect_any: [""]`、`expect_hit: [{file: ""}]`（hit 恒 100%）；`forbidden.path_globs: "secret/**"`（硬禁 fail-open）；`delivery.min_relevance: null`（rc=1）；`vault_id: null`（静默错 vault）；`queries: []` 主集（memory shadow 早退 rc=0 / vault 空哨兵 rc=2，均非 2 档语义统一）。

**对照输入**：r7→r8 的回归集合 = 上表 12 条显式 null + `expect_empty:"yes"`；r8→r9 的恢复集合 = 同一 12 条（我按「键存在」判定逐条复算，全部 F）。四份真金集在 r7/r8/r9 三版守卫下均 T（`c773e36b→908d459f` 对金集/manifest 零改动，blob 哈希相同）。

**负控输入**：两个新 case 在 r8 源码上均红（独立复算），r9 上均绿；`r9-gate-green-…151618/151643` 两份红档本身即「fixture 首版未判别目标分支」的负控痕迹，但未被 UAT 收录说明。M1/M2/M3/M4/M5 与 L-d 均**无 committed 负控**（与 r8 结论一致）。

**门未覆盖的路径**：两个 runner 的 shadow 路径仅在 r8/r9 证据中未重跑（我未跑，边界允许）；非 shadow、网络、8011 均未触碰；「目录级 1969」本体未重跑（仅收集数 + 算术核对）；`queries: []`、`expect_empty` 并存矛盾、internal-key 类型等仍无 case。

---

## 本轮总评

**B=0 / H=0 / M=5 / L=9**

- **B**：无 blocker。
- **H**：H1 **真关闭**（5 类显式 null 在 r9 全部拒；我以 r7/r8/r9 三版源码同 fixture 逐条复算，全部由 r8 的 T 回到 F；未发现漏网 null 面）。
- **M**：5 条均为 r8 已报、r9 明确登记移交的长尾（非 JSON 标量、超大整数溢出、范围/空集、空串、内部键），逐条复算仍可复现；**H 类（exit 1 / 硬门 fail-open）虽已登记，但其中 M1/M2 会污染 rc=1 档，严重度不宜按「防御性」处理**。
- **L**：新增 2 条（fixture 弱化、gate 红档未披露）+ 7 条遗留。
- `908d459f` **达成作者自述的核心目标**（显式 null 族修回、+2 判别性 case、gate 56 绿、金集/manifest 零改动、sha/verify 不变），且其修复可被独立复算；不达成的是 §十五.1「长尾需手改金集才能出现」的因果叙述与 §十五.2 证据呈现的完整性。
