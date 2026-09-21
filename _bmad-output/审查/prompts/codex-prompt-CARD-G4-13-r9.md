# CARD-G4-13 r9 独立复核任务书（Codex × DeepSeek V4.1 Flash · 开发/证据面）

> 复核对象 = commit `908d459f`（父 `c773e36b`）；批次 `[BATCH-2026-09-18-第十五批 / CARD-G4-13]`。
> 只读复核，**不改任何文件**。

## ① 背景与最小读取面

r8 复核对 `c773e36b` 报 **B=0/H=1/M=5/L=8**，其中 H1 是 r8 引入的回归（显式 YAML null 被当「缺键」
放行 ⇒ runner `float(None)` exit 1；r7 本来拒）。`908d459f` 修回该族，并把其余长尾**登记**为
防御性加固（见 UAT §十五：冻结金集 canonical、长尾需手改金集+重建 manifest 才能出现）。

最小读取面：
- `git --no-pager diff c773e36b 908d459f -- backend/scripts/gold_set_manifest_tool.py backend/tests/regression/test_gold_set_manifest_g413.py`
- `backend/scripts/gold_set_manifest_tool.py` 第 430-620（vgsf 内容守卫）
- `_bmad-output/审查/codex-review-CARD-G4-13-r8.md`（上一轮全文）
- `_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19.md` §十五
- 证据：`_bmad-output/审查/evidence-g413/r9-*`；两 runner 取值行按上一轮清单。

## ② 作者自述（核对点）

1. 显式 null 族修回：`tolerance/duplicate_ratio/max_results/top_k`、`leak_markers`、`expect_hit`、
   `expect_not_hit` 一律按「**键存在**」判定（存在即须合法类型，显式 null ⇒ 拒）；
   `group_id`/`vault_id` 保持「str 或 null」；`max_in_top_k` 排除 bool。
2. 形状 case +2（explicit-null-numeric / explicit-null-not-hit）；gate 56 passed；目录级 1969 passed 红 0；
   四 sha/verify 不变；金集/manifest 零改动。
3. 长尾（非 JSON 类型 id/category、超大整数、范围/空串、内部键、alias span、`queries: []` 主集等）
   登记移交，不在本 commit 修。

## ③ 问题（逐条回答）

⓪ H1 是否真关闭：对 r8 报告的五类显式 null（含 `expect_hit: null`、`expect_not_hit: null`、
   `leak_markers: null`、四个数值键 null）逐一给「r8 放行 / r9 拒绝」的复算结论；有无漏网的 null 面？
① §十五 的「长尾登记」口径是否诚实、是否有哪一项其实**不需要手改金集**就能在冻结态被触发（若是，
   给出输入并指出该登记不成立）？
② 新 case 是否真在目标分支上判别、无空转；gate 56 与目录级 1969 是否自洽。
③ 证据链/UAT §十五 有无 overclaim。
④ 总结：B/H/M/L + `908d459f` 是否达成本次自述目标。

## ④ 输出格式

逐条 **BLOCKER/HIGH/MEDIUM/LOW**（无则写「未发现」）+ `file:line` + 一句话复现思路；
末尾一段「未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径」；
最后「本轮总评：B= / H= / M= / L=」。

## ⑤ 边界

只读；不改文件；不连 7691/7687/8011；不跑非 shadow runner；不评 G4-14/R-SLO/L-5/103 条语义。
