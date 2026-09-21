# CARD-G4-13 r6 独立复核（开发/证据面 · 只读）

## 绑定与独立复算

- HEAD = `cb0997ff`（父 `691b1d3e`）✓；进场与收尾 `git status` 相同：仅 2 个**未跟踪**的 r6 复核/prompt 文件，`git diff HEAD` 为空（我未改任何仓库文件）。
- `git diff --stat 691b1d3e cb0997ff` = 工具 + 测试 + 证据/UAT/r5 存档；`git diff … -- backend/tests/regression/` 只剩测试文件（31+/16-）⇒ **四金集与 manifest 零改动**；我独立跑 `gold_set_manifest_tool.py verify`：**rc=0**，四 sha（`650c5d46…/d88d3a0a…/c7b25fcc…/582df3af…`）与 manifest、与 `r6-shas` 逐字同；manifest `revision: 2 / frozen: true / adjudication.status: pending`。
- 探针只读：`FakePath`（内存 read/write）驱动出厂 `_apply_verdict_edits`；`git show 691b1d3e:` 源码内存 `exec` 做 r5 对照；`verify_gold_set_file` 用桩（stub `load_yaml`/`sha256_of`/`Path.exists`）在内存驱动**真函数**；未连 7691/7687/8011，未跑两 runner 非 shadow。
- 沙箱外只跑了两条只读 pytest：**46 passed**（独立复现）＋ `--collect-only`（46 个 id 全列出，见 ③）。
- 数字：gate 44→46 ✓、目录级 1957→1959 ✓，二者 **+2 全部来自 `test_verify_gold_set_file_content_shape_fail_closed` 的 1→3 参数化**，与 UAT 点名的「三个新测试」无关。

## ⓪ 节点树定位是否真关闭 H 类 —— 未发现 BLOCKER/HIGH/MEDIUM；LOW×1

r5 点名构造**确已关闭**（实跑复算）：真条目 id/标注键引号化 + 被覆盖同级 `dead: |` 伪条目 ⇒ r6 `changed=[]`、problem=「user_verdict 行不是规范形态」、**0 字节变化**；真条目 canonical（伪条目只在死区）⇒ 只改真条目 3 行、死区 0 字节。逐项排除（全部实跑）：顶层重复 `queries` ⇒ 整文件拒；条目 merge `<<` 提供标注键 ⇒ 该条不动；标注键重复（canonical+canonical、canonical+quoted 混合）⇒ 该条不动；flow 单行/引号键/`? key` 显式键 ⇒ 该条不动；alias 作**键**（`? *vk`）走不通（锚只能落在 mapping 上→unhashable key；或 `&vk key:` 同行→被规范形态正则挡）；`yaml.compose` 与 `safe_load` 的差异面（未定义别名/多文档/NUL/深嵌套）全为 `YAMLError` 或两版同炸。**未能构造出「写入落语义无效区域且自报成功」的输入**——r5 的 H 危害模型未复现。

**LOW — 条目 alias 时写入落在锚定义区（可在 `queries:` 块之外的另一个顶层键文本里），自报成功、无问题、无测试。**
- `backend/scripts/gold_set_manifest_tool.py:676-678`（末条目 `end=len(lines)`；条目起点取 alias 解出的 `item.start_mark.line`）
- 复现：`base_item: &bi`（id/query/三标注）+ `queries:\n  - *bi` ⇒ `changed=['q1'] problems=[]`，3 行改在 `base_item:` 块，解析后 `queries[0]` 值**正确**（同一对象）。属「位置在条目自身文本之外」，非语义污染；同锚被别的顶层键引用时那个键也会同步变（YAML 别名固有）。UAT/自述未提 alias 面。

## ① 内容守卫「sha 相符但不可跑」残余 —— **MEDIUM×1**（LOW 见下）

**MEDIUM — 守卫仍放行两类「映射但不可跑」形状，runner 在无 try 的取值行上 exit 1（r5 M 同类残余）。**
- `backend/scripts/run_memory_retrieval_regression.py:199`（`q["expect_any"]` 硬下标；`:192` 只判 `q.get("expect_empty")`）：条目 `{id: q1, query: abc}` + manifest 同 sha/同 count ⇒ vgsf 实测 `True`（桩驱动真函数 PASS-THROUGH）⇒ `run_queries`（`:379` 无 try）KeyError → traceback → exit 1。
- `backend/scripts/run_memory_retrieval_regression.py:136-137`（`int(max_results)`/`float(duplicate_ratio)`）与 `backend/scripts/run_vault_retrieval_regression.py:497`（`float(tolerance)`，try 从 `:502` 才开始）：`config: {tolerance: "xyz"}` / `{max_results: "abc"}` ⇒ vgsf `True` ⇒ ValueError → exit 1。
- 对照（实测 rejected ✓）：`config` 非映射/缺失、条目缺 `id`、`query` 非字符串、`len(qs)≠query_count`、非映射条目 —— r6 真拦下。
- LOW（信息面、非崩点）：`id: null` / `id: 5` / `query: ""` 均 PASS-THROUGH（读取面内 `q["id"]` 只做 f-string/字典键，未构崩点）；主集 `queries: []` PASS-THROUGH（vault 被 `:508-517` 空哨兵兜成 rc=2，memory 侧全 0 指标有 rc=1 风险）。

## ② 新崩点 / 误伤 —— 未发现 BLOCKER/HIGH/MEDIUM；LOW×2

- **未发现新崩点**：`yaml.compose` 异常面（ReaderError/ParserError/ComposerError）全为 `YAMLError` 子类 → `:649-652` 已接；`root=None`、顶层非映射、非唯一 `queries`、非映射条目、id 键缺失/重复、id 值非标量 → 全部 fail-closed（逐分支实跑）。深嵌套 `RecursionError`（depth≈1200）两版同炸且 CLI 路径 safe_load 先行 ⇒ 非 r6 新面。`found[key]` 只在三字段内取值；`updates` 传第四字段会 KeyError，但 `:814` 只造三字段，CLI 不可达。真 103 条逐条复算 **75/28/2/0 全可写、problems=[]** ✓。
- **LOW（措辞/死代码）** `backend/scripts/gold_set_manifest_tool.py:83`：`ITEM_ID_LINE_RE` 全仓零引用（唯一定义），注释仍写「query 条目起始行」⇒「文本启发式零残留 / 唯一正则」表述不精确（残留定义、无残留行为）。
- **LOW（误伤面，r5 已登记并扩大）** 合法非规范写法 fail-closed 不写：`"user_verdict": x`、`- "id": x`、`? key`、flow 单行、条目 merge/alias；四金集无此类行，当前无实害。

## ③ 测试真实性 —— **MEDIUM×1**（LOW×1）

**MEDIUM — UAT §12.1 点名的三个测试在本 commit 不存在，r5 的 M（关键机制无判别测试）未关。**
- `_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19.md:352`（`test_apply_verdicts_decoy_scalars_do_not_hijack_writes`、`test_apply_verdicts_rejects_duplicate_annotation_key_lines`）、`:354`（`test_apply_verdicts_precheck_blocks_corrupt_write`，连 monkeypatch 细节都写了）。
- 复现：全仓 grep 只命中 UAT 自身；`pytest --collect-only` 的 46 个 id 里无这三个名字。⇒ 预检分支、全文档不变量分支、重复标注键分支仍**无 committed 判别测试**（重复键**行为**我手工实测为拒绝：两种混合都 `changed=[]`+problem）。
- 正面（不空转）：`backend/tests/regression/test_gold_set_manifest_g413.py:829-869` 在 r5 源码上**确先红**——`git show 691b1d3e:` 实跑同 fixture ⇒ r5 整文件拒绝（`changed=[]`）⇒ 断言 `changed==['q1']` 必失败；r6 下恰 3 行、正文零改动。
- **LOW** `:1093-1095,1121-1122`：case «item-missing-query» 的 fragment `"query"` 是 `"queries"` 的子串 ⇒ 任何 queries 类拒绝文案都能过，非判别（case 3 的 `"config"` 有判别性）。

## ④ 证据链 —— **MEDIUM×1**（LOW×2）

- 自洽 ✓：44→46、1957→1959、+2=参数化；`r6-verify/r6-shas` 与我自跑一致；ruff 双 rc=0；`r5-gate-red-…140423` 已补作废注记 ✓。
- **MEDIUM（overclaim，与 ③ 同根）**：§12.1/§12.2 用三个不存在的测试当 H/M 整改的锚；自述 ④「decoy + 预检分支 + 重复标注键 + 3 形状 case」与 commit 内容不符（实际只新增 3 个形状 case + 改写 1 个 fake-id 判据）。
- **LOW** `evidence-g413/r6-decoy-red-on-r5-20260920T142551.txt` 全文 **2 行断言**（无命令/fixture/输出/哈希）。我按「幂等值前置 + 死区值引号化」复算 r5 源码确得 `changed=['q2'] bytes_changed=True`（结论真），但该构造不对应任何 committed 测试，只能支撑「该构造在 r5 是受害者」。
- **LOW** `r6-immutability-…142623.txt` 与 `r6-dryrun-fullflow-…142617.txt` 与 r5 版**逐字节相同**（后者尾行仍「DRY-RUN r4 OK」）⇒ 不含 r6 专属信号（immutability 结论我已用 git diff 独立证实；dryrun 仅兼容性快照）。

## ⑤ r5 清单逐条点名闭合

| r5 项 | r6 状态 | 证据 |
|---|---|---|
| **H** 被覆盖同级 scalar/文本启发式 | **named 构造关闭 ✓**（写准真条目、死区 0 字节） | 我实跑；`tool.py:624-720` |
| H 同类「写入落非目标区域」 | 仅剩 alias 变体（LOW，语义正确） | ⓪ LOW；`:676-678` |
| **M** vgsf「映射但不可跑」→ runner exit 1 | **部分关闭**：点名 3 形状 ✓；`expect_any`、config 数值类型仍穿透 | ① MEDIUM |
| **M** 关键机制无判别测试 | **未关闭**：预检/不变量/重复标注键 0 committed 测试 | ③ MEDIUM |
| **L①** `#` 行过宽 | 代码关闭（r5）✓，仍无测试钉子 | `:589` |
| **L②** apply-verdicts 非映射文档崩 | 关闭 ✓ | — |
| **L③** verify_all 非 Path 崩 | 关闭 ✓ | — |
| **L④** `revision_history` falsy | 关闭 ✓ | — |
| L（r5 新增）证据命名 / 140423 | 关闭 ✓（r6-verify/r6-shas 已补；已注记） | ④ |

## 未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径

- **未被拦下的输入**：① memory `{id, query}`（无 `expect_empty`/`expect_any`）⇒ vgsf True ⇒ `:199` KeyError → exit 1；② `config.tolerance/max_results/duplicate_ratio` 非数值 ⇒ vgsf True ⇒ vault `:497` / memory `:136-137` ValueError → exit 1；③ `id: null`/`id: 5`/`query: ""`/主集空 `queries` ⇒ vgsf True（未找到崩点，除 memory 空集 rc=1 风险）；④ 条目 alias ⇒ 3 行写进锚定义区（可位于另一个顶层键文本内）、`problems=[]`。
- **对照输入**（r6 正确/拒绝）：r5 H 构造 ⇒ 0 写+problem；canonical 真条目+尾部死区伪 `- id:` ⇒ 只写真条目 3 行；重复顶层 `queries`/重复标注键（含混合）/条目 merge/flow/引号键/显式键 ⇒ fail-closed；真 103 条全可写；`verify` rc=0、四 sha 逐字同。
- **负控输入**（r5 源码内存复算）：decoy（幂等值前置+死区引号值）⇒ `changed=['q2'] bytes_changed=True`（复现 r6-decoy-red 声明）；committed 新测试同 fixture ⇒ r5 整文件拒绝 ⇒ 该测试在 r5 上确红；r6 源码对 `queries:[{}]`/缺 `query`/缺 `config` 全部 rejected。
- **门未覆盖的路径**：预检读回分支 / 全文档不变量分支 / 重复标注键分支（无 committed 测试，且我构造的输入里不变量一次也没被触发）；alias&merge 定位；`#` 行收窄的误伤修复；两个 runner 本体（只读实际取值行，未运行非 shadow）。

---

**本轮总评：B=0 / H=0 / M=2 / L=7**
（M1=① 守卫残余致 runner exit 1；M2=③/④ UAT 点名 3 个测试不存在 ⇒ 关键分支无判别测试 + 证据 overclaim；L=alias 写入位置 / id·空串·空集形状 / 参数化弱断言 / decoy 证据仅 2 行断言 / 两份 r6 证据与 r5 逐字节同 / `ITEM_ID_LINE_RE` 死代码与「零残留」措辞 / 非规范写法 fail-closed 误伤面。）

**`cb0997ff` 部分达成自述目标**：机制面（节点树定位关掉 r5 点名的 H 构造、五类形状守卫、重复键/跨行/非规范拒绝、金集与 manifest 冻结零改动）经我独立复算**成立**；但测试与证据面不达标——UAT §12.1 点名的 3 个「新测试」在该 commit 里不存在（gate 的 +2 来自参数化 case），r5 的「关键机制无判别测试」与「runner exit-1 残余」均未关闭，故自述第 4 条与 §十二的测试锚不能成立。


