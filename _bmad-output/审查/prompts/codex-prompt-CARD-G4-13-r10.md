# CARD-G4-13 r10 独立复核任务书（Codex × DeepSeek V4.1 Flash · 开发/证据面）

> 复核对象 = commit `0b0fc8ac`（父 `908d459f`）；批次 `[BATCH-2026-09-18-第十五批 / CARD-G4-13]`。
> 只读复核，**不改任何文件**。

## ① 背景与最小读取面

r9 复核对 `908d459f` 报 **B=0/H=0/M=5/L=9**（H1 真关闭；M=类型面长尾）。`0b0fc8ac` 在**不改 runner**
前提下把该长尾收进 vgsf 守卫：全文档 `json.dumps` 检查（非 JSON 标量整类）、`id/query` 非空 str、
`language/query_type/category` 非空 str、范围（`max_results/top_k ≥1 int`、`tolerance/duplicate_ratio ∈[0,1]`、
`max_in_top_k ≥0`）、`delivery` 内部键（`hard_cap/min_relevance/elbow_drop_threshold`）、矛盾组合
（vault `expect_empty×expect_hit`、memory `expect_empty×expect_any`）。冻结面零改动。

最小读取面：
- `git --no-pager diff 908d459f 0b0fc8ac -- backend/scripts/gold_set_manifest_tool.py backend/tests/regression/test_gold_set_manifest_g413.py`
- `backend/scripts/gold_set_manifest_tool.py` 第 430-640（vgsf 内容守卫全段）
- `_bmad-output/审查/codex-review-CARD-G4-13-r9.md`（上一轮全文）
- `_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19.md` §十七
- 证据：`_bmad-output/审查/evidence-g413/r10-*`

## ② 核对点

1. r9 点名的 5 类长尾是否逐类被拦（给出 r9 源码 vs r10 的同 fixture 复算结论）；
2. 新增守卫是否**误拒**四份真实金集或未来合法扩展（新键/unknown 键/`source`/`user_verdict` 等任意形态、
   `language` 等缺失、`expect_empty` 与 `expect_not_hit` 并存、vault `expect_hit: []` 空列表）；
3. 是否还有「sha 相符但 runner exit 1 / 门禁 fail-open」的**新**残余（尤其 `contamination`/`forbidden`
   内部键、`cfg["version"]` 边界、`group_id` 空串、`leak_markers: []`）；
4. 6 个新 case 是否真在目标分支上判别、无空转；gate 62 / 目录级 1975 数字自洽；
5. UAT §十七 有无 overclaim；§十六.2 的「维持登记」项是否诚实。

## ③ 输出格式

逐条 **BLOCKER/HIGH/MEDIUM/LOW**（无则写「未发现」）+ `file:line` + 一句话复现思路；
一段「未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径」；末尾「本轮总评：B= / H= / M= / L=」。

## ④ 边界

只读；不改文件；不连 7691/7687/8011；不跑非 shadow runner；不评 G4-14/R-SLO/L-5/103 条语义。
