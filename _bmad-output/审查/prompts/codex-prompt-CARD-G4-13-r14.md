# CARD-G4-13 r14 独立复核任务书（Codex × DeepSeek V4.1 Flash · 开发/证据面）

> 复核对象 = commit `12d61f9a`（父 `fe8952de`）；批次 `[BATCH-2026-09-18-第十五批 / CARD-G4-13]`。
> 只读复核，**不改任何文件**。

## ① 背景与最小读取面

r13 复核对 `fe8952de` 报 **B=0/H=0/M=0/L=5**（首轮 M=0）。`12d61f9a` 收 5 条 LOW：`_grade_ok` 名实同步 +
`int()` 解析放宽、`contains`/`max_in_top_k` 与 runner 契约对齐（含正向对照测试）、`group_id`/`vault_id`
真·非空、内部键消息写明理由、r13 中间态红运行作废注记、immutability 证据逐函数可见。

最小读取面：
- `git --no-pager diff fe8952de 12d61f9a -- backend/scripts/gold_set_manifest_tool.py backend/tests/regression/test_gold_set_manifest_g413.py`
- `backend/scripts/gold_set_manifest_tool.py` 第 390-700（守卫全段）
- `_bmad-output/审查/codex-review-CARD-G4-13-r13.md`（上一轮全文）
- `_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19.md` §二十一
- 证据：`_bmad-output/审查/evidence-g413/r14-*`

## ② 核对点

1. 5 条 LOW 逐条复算（r13 源码 vs r14 源码同 fixture：`_grade_ok` 全表、`contains` 标量、缺
   `max_in_top_k`、`group_id/vault_id` 空白/null、内部键消息、正向对照是否真 True）；
2. 放宽后是否引入新的 fail-open（`contains` 数字/`grade` 全角串的语义是否与 runner 一致；
   `max_in_top_k` 缺省=0 的语义是否真为 runner 行为）；
3. 是否还有「守卫 T 但 runner 落 rc=1 或 fail-open」的新路径；四真金集是否仍 T 无误拒；
4. 新增/改动测试是否真判别、无空转；gate 81 / 目录级 1994 自洽；
5. UAT §二十一 / §21.3 残余登记是否诚实。

## ③ 输出格式

逐条 **BLOCKER/HIGH/MEDIUM/LOW**（无则写「未发现」）+ `file:line` + 一句话复现思路；
一段「未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径」；末尾「本轮总评：B= / H= / M= / L=」。

## ④ 边界

只读；不改文件；不连 7691/7687/8011；不跑非 shadow runner；不评 G4-14/R-SLO/L-5/103 条语义。
