# CARD-G4-13 r7 独立复核任务书（Codex × DeepSeek V4.1 Flash · 开发/证据面）

> 批次 `[BATCH-2026-09-18-第十五批 / CARD-G4-13]`；车道 `card-p9-testinfra`；复核对象 = commit
> `22c1603a`（父 `cb0997ff`）。只读复核，**不改任何文件**。

## ① 背景与最小读取面

背景：r6 复核（`codex-review-CARD-G4-13-r6.md`）对 `cb0997ff` 给出 **B=0 / H=0 / M=2 / L=7**：
M1 = vgsf 内容守卫残余（memory 期望键缺失 / config 数值类型 ⇒ runner exit 1）；M2 = UAT §十二 点名的
三个测试**在 commit 里不存在**（r6 的测试编辑脚本截尾事故）+ 关键分支无 committed 测试；L×7。
`22c1603a` 补齐三个测试、加严守卫、删死代码、收窄弱断言、重生成自包含 decoy 证据（见 UAT §十三）。
裁定窗口仍未开（103 条 pending）；金集与 manifest 零改动（verify rc=0、四 sha 逐字同）。

最小读取面（只读这些）：
- `git --no-pager diff cb0997ff 22c1603a -- backend/scripts/gold_set_manifest_tool.py backend/tests/regression/test_gold_set_manifest_g413.py`
- `backend/scripts/gold_set_manifest_tool.py` 第 397-580（vgsf 内容守卫）/ 617-820（节点树版 _apply_verdict_edits）
- `backend/tests/regression/test_gold_set_manifest_g413.py`（重点 1090-1260 = 形状 case + 三个补齐的测试）
- 两个 runner 的实际取值行：`run_vault_retrieval_regression.py:190-197,214-220,331-345,497` /
  `run_memory_retrieval_regression.py:134-138,148-149,192-199,374`（只读，用于核对守卫覆盖）
- `_bmad-output/审查/codex-review-CARD-G4-13-r6.md`（上一轮全文 = 问题清单）
- `_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19.md` §十三
- 证据：`_bmad-output/审查/evidence-g413/r7-*`

## ② 作者自述（逐条独立核对）

1. 三个测试已补齐且在目标分支上判别（decoy 引号键 ⇒ 「规范形态」problem；预检 monkeypatch ⇒ 零写+
   「预检」problem；重复标注键 ⇒ 「缺失/重复」problem）；gate 51 passed = 46 + 3 测试 + 2 case。
2. vgsf 内容守卫新增：≥1 期望键；`expect_hit/not_hit/any` 为 list、`expect_empty` 为 bool；
   `config.{tolerance,duplicate_ratio,max_results,top_k}` 数值；`config.{contamination,forbidden,delivery}`
   映射；`leak_markers` 列表。
3. 删死代码 `ITEM_ID_LINE_RE`；`VERDICT_LINE_RE` 只做规范形态校验；形状 case 断言收窄为「缺 id 或 query」。
4. decoy 证据（`r7-decoy-red-r5-green-head-*.txt`）自包含：fixture sha256 + r5(`691b1d3e`) 源码落写 /
   HEAD 拒绝零写双跑。
5. 目录级沙箱外 1964 passed / 6 skipped / 1 xfailed 红 0（= r6 的 1959 + 5）。

## ③ 按重要性排序的问题（逐条回答；答不了就答「无可读证据」）

⓪ 守卫是否真覆盖两个 runner 的取值面：按上面 runner 行逐条对照 vgsf 守卫，还有哪些「sha 相符但
   runner 会崩」的输入残留（含 `expect_any` 项缺索引/类型、`delivery` 内部键、`contamination` 内部键、
   `forbidden` 内部键、`cfg["version"]` 类型、`group_id`/`vault_id` 类型等）？能给可复现输入就给。
① 节点树定位还有没有「写入落非目标区域」或「误拒正常文件」的输入？（含顶层 `queries` 重复键、
   merge key `<<`、alias 条目、flow 形态键行、BOM/CRLF/无尾换行）
② 三个补齐的测试是否真在目标分支上判别、且无空转（断言是否只在目标分支成立）？
③ 证据链：`r7-*` 数字自洽；decoy 证据是否够独立复算；UAT §十三 有无 overclaim（尤其「如实登记
   事故」与「已知语义」两处）。
④ r6 清单（M×2 / L×7）逐条点名闭合。

## ④ 输出格式

- 逐条给 **BLOCKER / HIGH / MEDIUM / LOW**（无则写「未发现」），每条：`file:line` + 一句话复现思路。
- 必须有一段「未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径」（没有就写「无」）。
- 结尾「本轮总评：B=x / H=y / M=z / L=w」+ 一句 `22c1603a` 是否达成本次自述目标。

## ⑤ 边界

- 只读；⛔ 不改任何文件；不连 7691/7687/8011；不跑两 runner 非 shadow 模式。
- 不评 G4-14 七指标 / R-SLO schema / L-5（Tier-R top10 盲区，已登记，属判分语义面）。
- 不评 103 条 query 的语义本身，只评工具 / 测试 / 证据链。
