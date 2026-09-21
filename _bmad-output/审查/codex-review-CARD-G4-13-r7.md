# CARD-G4-13 r7 独立复核（只读）

**绑定**：HEAD = `22c1603a203852ec3dbfb2bbec60ef2e9056a849`，父 `cb0997ff`；仓库无改动（仅原有未跟踪的 r7 review/prompt）。我独立重跑了行为门 `51 passed`、`gold_set_manifest_tool.py verify` rc=0，并逐字复算四份金集 sha 与 manifest 一致。未连 7691/7687/8011，未跑两个 runner 的非 shadow 模式。

---

## ⓪ 守卫是否覆盖两个 runner 的取值面

**结论：不覆盖。r6 的「sha 相符但 runner 会崩」类残留仍在；以下输入都能通过当前 vgsf。**

- **MEDIUM（M1）— 期望键与标量类型只查容器，memory runner 仍 exit 1。**
  - `backend/scripts/gold_set_manifest_tool.py:476-490` 只要求四个期望键中至少一个 truthy，且只检查 `expect_hit/not_hit/any` 是 list。
  - `backend/scripts/run_memory_retrieval_regression.py:199` 对非 `expect_empty` 条目硬取 `q["expect_any"]`。
  - 复现 1：条目写成 `{id: q1, query: abc, expect_hit: [{"file": x}]}`（或只给 `expect_not_hit`）⇒ vgsf 返回 True；只要该条有任一返回结果，真 `main()` 就未捕获 `KeyError: expect_any` → exit 1（我用假 `httpx.Client` 走真 `main()` 已复现）。
  - 复现 2：`expect_any: [1]` 或 `leak_markers: [1]` 只过 list 检查；有返回结果时 `norm_text()` 在 `run_memory_retrieval_regression.py:91-93/110-115` 抛 `TypeError` → exit 1。
  - 复现 3：`group_id: 2020-01-01`（YAML date）或 `version: !!binary aGk=`（YAML bytes）过 vgsf；`run_memory_retrieval_regression.py:153-160` 只捕获 `HTTPError/ValueError`，`httpx` JSON 编码抛的 `TypeError` 未捕获 → exit 1；`version` 为 bytes/date 时还会在 `:390` 的 `json.dumps(report)` 处抛 `TypeError` → exit 1（已复现）。

- **MEDIUM（M2）— config 数值只查类型，不查有限性/范围；有 exit 1，也有 fail-open。**
  - `backend/scripts/gold_set_manifest_tool.py:491-494` 只做 `isinstance(int/float)`，`bool` 被排除，但 `.nan/.inf` 通过。
  - `backend/scripts/run_memory_retrieval_regression.py:136`：`max_results: .nan` ⇒ `int(nan)` `ValueError`；`.inf` ⇒ `OverflowError`；二者均在 `main()` 的未保护路径上 → exit 1（已复现）。
  - `run_memory_retrieval_regression.py:374` / `run_vault_retrieval_regression.py:497`：`tolerance: .inf/.nan` 通过 vgsf；我直接调用真 `compare_with_baseline()`，所有指标从 1.0 掉到 0.0 时 regressions 仍为 `[]` ⇒ **门禁 fail-open**。
  - 同类：`top_k` 非有限值在 vault 侧会抛异常，但被 `main():502-506` 兜成 rc=2；`duplicate_ratio: .nan` 不崩，但会使近重复比较恒假。

- **LOW（L2）— vault 侧内部键未守卫；会抛但被 main 兜成 rc=2。**
  - `expect_hit` 项缺 `file`、`expect_not_hit` 项非映射/`max_in_top_k` 非数值、`contamination.path_globs/doc_types` 为 null、`forbidden.path_globs/doc_types/markers` 为 null、`delivery.hard_cap/min_relevance/elbow_drop_threshold` 为字符串等，vgsf 仍返回 True；对应取值/转换在 `run_vault_retrieval_regression.py:122-157/191-195/303/331-345` 抛异常。因为 `main():502-506` 包了 `run_tiers`，最终 rc=2，不是 M1 那种 exit 1；但守卫覆盖声明不成立。

- **LOW（L3）— 非崩溃型类型缺口。**
  - `group_id` 为 int、且未来接口回传 `group_id` 时，`run_memory_retrieval_regression.py:119` 的 `group_id.replace()` 会 `AttributeError`（当前接口注释称不回传 group_id，故为条件性）；`vault_id` 在 `run_vault_retrieval_regression.py:197` 被 `str()` 吞掉类型错误，可能静默落到错误 vault；`version` 为 list/dict 不崩，但 vgsf 未校验。

- **LOW（L4）— r6 的 id/空串/空集形状仍未关闭。**
  - `tool.py:470-472` 通过 `id: null`、`id: 5`、`query: ""`、主集 `queries: []`；memory 空主集在 `run_memory_retrieval_regression.py:379` 得到全 0 指标（有 baseline 时 rc=1；无 baseline 时可能写零基线），vault 空集则走 `:510-516` rc=2 哨兵。

---

## ① 节点树定位

- **LOW（L1）— alias 条目的写入位置仍有缺陷；「已知语义」登记不完整。**
  - `backend/scripts/gold_set_manifest_tool.py:683-705` 用 `item.start_mark.line` 定 span，`:715-740` 只按 node 里的键行写。
  - 复现 A（单 alias）：`base: &bi` 定义 q1 三标注行，`queries:\n  - *bi` ⇒ `changed=['q1']`、`problems=[]`，三行实际改在 `base:` 锚定义区，而不是 `queries` 文本内。
  - 复现 B（alias 跟在普通条目后）：`queries:` 先有普通 q1，再有 `- *bi`（q2）⇒ 选中 q1 报 `q1: user_verdict 的键行不在条目行区间内`，零写；选中 q2 则改锚定义区。语义上 q2 的解析值正确，但这已不只是「写锚=写该条目」：span 计算会把普通条目误拒，UAT `:399` 的「已知语义、不作缺陷」措辞过宽。

- **其余点名形态：未发现新增的写坏路径。**
  - 顶层重复 `queries`：`:683-685` 整文件拒绝。
  - merge key `<<`：标注键不在直接 node.value ⇒ 该条报「缺失/重复」且零写；属 fail-closed，不是写错区。
  - flow 形态/引号键/显式键：`:737-739` 以 `VERDICT_LINE_RE` 拒绝，零写。
  - BOM、CRLF、无尾换行：实测均只改目标 3 行；BOM/CRLF/无尾换行保持原字节特征。单独的 lone-CR 会在预检阶段解析失败并零写（unreachable 的写坏，但会误拒）。

---

## ② 三个补齐测试是否真实、是否空转

- **未发现（无 BLOCKER/HIGH/MEDIUM）— 三个测试确实存在且可判别。**
  - `backend/tests/regression/test_gold_set_manifest_g413.py:1136`（decoy）、`:1192`（precheck）、`:1219`（duplicate）。
  - 我用 `git show 691b1d3e:` 的 r5 源码 + 与 committed test 相同的 fixture 复算：r5 在 decoy 下 `changed=['q2'] / bytes_changed=True / problems=[]`；HEAD 为 `changed=[] / 零写 / 「规范形态」problem`。测试选的是 `verdict:irrelevant`（恰为 true q2 的当前值），这是 r5 能绕过 precheck 的幂等构造；因此该测试在 r5 上确红、在 HEAD 上绿。
  - precheck 测试 monkeypatch `_yaml_scalar` 后触发「预检读回不一致」并零写；duplicate 测试触发 node-tree 的 found=2 分支并零写。`51 passed` 已独立复跑。
  - 行为门计数 `46 + 3 新测试 + 2 新参数化 case = 51` 自洽。

- **LOW（L5）— 仍有重要分支没有 committed 测试。**
  - `tool.py:785-796` 的全文档不变量（`expected != doc`）没有任何测试到达；precheck 测试只覆盖 `:779` 的读回不一致，decoy 测试在 HEAD 上于 `:737-739` 早退。
  - 新增 guard 的 `bad_expect` 项类型、`config.{contamination,forbidden,delivery}` 内部键、`leak_markers` 项类型、非有限数值均无专属 case；当前 `1090-1133` 只新增 `no-expectation-key` 与 `config-numeric-type` 两 case。

---

## ③ 证据链

- **数字自洽且可复算部分成立。**
  - `r7-gate-green-*.txt` 的 51 passed 我独立复跑一致；`r7-verify-*.txt` rc=0 我独立复跑一致；四份金集完整 sha 与 manifest 逐字一致：`650c5d46…` / `d88d3a0a…` / `c7b25fcc…` / `582df3af…`。
  - `r7-decoy-red-r5-green-head-*.txt:1-5` 的 fixture sha256、r5 落写、HEAD 拒绝零写三组结论均与我的独立复算一致。
  - `r7-regression-outside-sandbox-*.txt` 的 `1964 + 6 + 1 = 1971` 与收集数自洽，但我没有重跑完整目录级 1964（只重跑 51 门），这一点应标为未独立复算。

- **LOW（L6）— decoy 证据仍不是严格自包含，UAT「自包含」措辞过宽。**
  - `_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19.md:397` 称其为「自包含版」；但 `r7-decoy-red-r5-green-head-*.txt` 只有 sha、字节数和输出，没有 fixture 正文、运行命令、更新目标值。把 committed test 里的 fixture 拿来做二次复算可行，证据文件本身单独不可复算。

- **LOW（L7）— r7-immutability / r7-dryrun 仍与 r5/r6 逐字节相同，且 dryrun 文案仍写 r4。**
  - `r7-immutability-*.txt` 与 r5/r6 sha256 均为 `901fff…`；`r7-dryrun-fullflow-*.txt` 与 r5/r6 均为 `4d9bc5…`，尾行仍是 `DRY-RUN r4 OK`（证据文件第 10 行）。
  - 底层事实（金集/manifest 未改、verify rc=0）我已独立验证；但「本轮重跑并保留」不能仅凭该产物证明，r6 的这条 LOW 只被解释、未被证据面真正关闭。

- **LOW（L8）— 「如实登记事故」的效果可验，因果叙述不可验。**
  - UAT `:381-387` 称 r6 编辑脚本「把追加在文件尾的三个新测试整段截掉」；可验证的是 `cb0997ff` 中三个测试名不存在、`22c1603a` 中补齐（grep/collect 均成立）。至于“脚本截尾”这一因果机制，commit 和内附证据没有脚本、日志或执行记录；应标注为作者说明而非独立证据。

---

## ④ r6 清单（M×2 / L×7）逐条闭合

| r6 项 | r7 状态 | 依据 |
|---|---|---|
| M1 vgsf 守卫残余 → runner exit 1 | **未关闭**（残 M1/M2） | `expect_hit`-only、`expect_any/leak_markers` 项非 str、`group_id/version` 非 JSON 类型、非有限数值仍穿透 |
| M2 §十二点名的三个测试不存在 | **基本关闭**：三个测试已补齐且在 r5 上判别 | `test…:1136/1192/1219`；`51 passed`；decoy 负控已复现；但不变量/新 guard 分支仍无测试（L5） |
| L1 alias 写锚定义区 | **部分关闭/登记不完整** | 单 alias 语义正确但多条目 span 会误拒，见 L1 |
| L2 `id: null/5`、`query: ""`、空主集 | **未关闭** | vgsf 仍放行，见 L4 |
| L3 参数化断言 `"query"` 弱 | **关闭** | 已收窄为「缺 id 或 query」，测试通过 |
| L4 decoy 证据仅 2 行断言 | **部分关闭** | 内容准确性提高，但仍非严格自包含，见 L6 |
| L5 r6 immutability/dryrun 与 r5 逐字节同 | **未真正关闭** | r7 版本仍逐字节同且无 r7/HEAD 专属信号，见 L7 |
| L6 `ITEM_ID_LINE_RE` 死代码及措辞 | **关闭** | `.py` 源码全仓无引用；`VERDICT_LINE_RE` 注释已改为只校验形态 |
| L7 非规范写法 fail-closed 误伤面 | **已登记接受，无新增实害** | UAT `:400`；当前四份金集均规范形态，verify rc=0 |

---

## 未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径

- **未被拦下的输入**：
  - `expect_hit`-only / `expect_not_hit`-only → memory `q["expect_any"]` KeyError exit 1。
  - `expect_any: [1]`、`leak_markers: [1]` → `norm_text` TypeError exit 1。
  - `max_results: .nan/.inf` → memory `int()` ValueError/OverflowError exit 1。
  - `tolerance: .inf/.nan` → `compare_with_baseline` 全部回归被吞，门禁可 rc=0。
  - `group_id: 2020-01-01` / `!!binary`、`version: 2020-01-01` / `!!binary` → JSON 编码/落盘 TypeError exit 1。
  - vault 侧 `expect_hit` 项缺 `file`、`contamination/forbidden/delivery` 内部键为 null/字符串 → 在 `run_tiers` 内抛，最终 rc=2（未污染 exit 1 档，但 guard 未覆盖）。

- **对照输入**：当前四份真实金集 + manifest ⇒ vgsf 全 True、verify rc=0、四 sha 逐字一致；BOM/CRLF/无尾换行各只改目标 3 行；顶层重复 `queries`、merge key、flow 形态、引号键均 fail-closed 零写。

- **负控输入**：r5 源码 + committed decoy fixture ⇒ `changed=['q2'] / bytes_changed=True / problems=[]`；HEAD ⇒ `changed=[] / 零写 / 规范形态 problem`。precheck monkeypatch ⇒ 零写 + 「预检」；duplicate 标注键 ⇒ 零写 + 「缺失/重复」。

- **门未覆盖的路径**：全文档不变量分支 `tool.py:785-796`；新增 guard 的内部项/映射/非有限数值分支；alias 多条目 span；lone-CR；`group_id` 为 int 且未来接口回传 `group_id` 的条件分支；完整 1964 目录级回归我未重跑；两个 runner 的真网络/非 shadow 路径按边界未运行。

---

**本轮总评：B=0 / H=0 / M=2 / L=8**

`22c1603a` **部分达成**自述目标：三个测试补齐且可判别、死代码删除、弱断言收窄、verify/51 门与四 sha 冻结均已独立复算成立；但 vgsf 仍有多类 sha 相符输入会让 memory runner 以 exit 1 收场（且 `tolerance` 非有限值可让门禁 fail-open），decoy/immutability/dryrun 证据也没有达到严格自包含或可区分重跑，因此不能判定为完整达成。


