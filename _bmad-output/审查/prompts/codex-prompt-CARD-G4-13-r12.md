# CARD-G4-13 r12 独立复核任务书（Codex × DeepSeek V4.1 Flash · 开发/证据面）

> 复核对象 = commit `07d5c34b`（父 `191de457`）；批次 `[BATCH-2026-09-18-第十五批 / CARD-G4-13]`。
> 只读复核，**不改任何文件**。

## ① 背景与最小读取面

r11 复核对 `191de457` 报 **B=0/H=0/M=1/L=7**：M1 = `contamination`/`forbidden` 内部键未查（str 逐字符
迭代 ⇒ 含 `*` 假硬禁 rc=1 / 不含 ⇒ 恒空 fail-open）；LOW-1 整数无上界、LOW-2 grade 过拒、LOW-3 兜底透传
无钉子、LOW-6 登记旧、LOW-7 docstring rc 语义。`07d5c34b` 逐条修（内部键=非空 str 列表；整数上界；
`_grade_ok`；KeyboardInterrupt 透传测试；docstring 与登记更新）。

最小读取面：
- `git --no-pager diff 191de457 07d5c34b -- backend/scripts/gold_set_manifest_tool.py backend/scripts/run_vault_retrieval_regression.py backend/scripts/run_memory_retrieval_regression.py backend/tests/regression/test_gold_set_manifest_g413.py`
- `backend/scripts/gold_set_manifest_tool.py` 第 390-700（守卫全段）
- `_bmad-output/审查/codex-review-CARD-G4-13-r11.md`（上一轮全文）
- `_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19.md` §十九
- 证据：`_bmad-output/审查/evidence-g413/r12-*`

## ② 核对点

1. M1 与 LOW-1/2/3/7 逐条复算（r11 源码 vs r12 源码同 fixture 的「拒/收/异常」表）；
2. 新增内部键守卫是否误拒四真金集（`contamination/forbidden` 全表）或未来合法扩展；空列表语义是否合理登记；
3. 是否还有「守卫 T 但 runner 落 rc=1 或 fail-open」的**新**路径（含 `contamination/forbidden` 的值不是
   glob 语义的形态、`expect_hit[i].contains`、`markers` 空串、`doc_types` 含空串、`verdict_at` 过度拒绝等）；
4. 5 个新门是否真判别、无空转；gate 75 / 目录级 1988 自洽；
5. UAT §十九 / §19.3 残余登记（LOW-4/5、L-5）是否诚实、无 overclaim。

## ③ 输出格式

逐条 **BLOCKER/HIGH/MEDIUM/LOW**（无则写「未发现」）+ `file:line` + 一句话复现思路；
一段「未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径」；末尾「本轮总评：B= / H= / M= / L=」。

## ④ 边界

只读；不改文件；不连 7691/7687/8011；不跑非 shadow runner；不评 G4-14/R-SLO/L-5/103 条语义。
