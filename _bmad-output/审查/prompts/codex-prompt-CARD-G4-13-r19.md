# CARD-G4-13 r19 独立复核任务书（Codex × DeepSeek V4.1 Flash · 开发/证据面）

> 复核对象 = commit `c6782824`（父 `97c71428`）；批次 `[BATCH-2026-09-18-第十五批 / CARD-G4-13]`。
> 只读复核，**不改任何文件**。

## ① 背景与最小读取面

r18 复核对 `97c71428` 报 **B=0/H=0/M=1/L=5**：唯一 M-4 = `build --bump-revision` 继承 approved，
新内容无新签字却 verify 全绿，且 approve 拒重签（放行+误拒）。`c6782824` 按最小修法：升版时把旧签名
写进 `revision_history[].prev_adjudication` 并把 adjudication 重置回 pending（保留 checklist_path）。

最小读取面：
- `git --no-pager diff 97c71428 c6782824`
- `backend/scripts/gold_set_manifest_tool.py` 的 `build_manifest`（bump 段 + prev_adj 段）
- `backend/tests/regression/test_gold_set_manifest_g413.py` 的 `test_build_bump_resets_signature_and_forces_resign`
- `_bmad-output/审查/codex-review-CARD-G4-13-r18.md`（上一轮全文）
- `_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19.md` §二十七
- 证据：`_bmad-output/审查/evidence-g413/r20-gate-green-*.txt` / `r21-*`

## ② 核对点（收口判定）

1. M-4 复算：pending→approve→改内容→bump→pending+留痕+verify 0→重签，整条生命周期（给 r18 源码 vs
   r22 源码的同 fixture 对照）；旧签名留痕是否完整、`checklist_path` 是否保留；
2. 是否引入新问题：**首次 build**（无 manifest）不受影响；无签名的 bump 是否也重置（会不会误伤
   「未签就升版」的正常路径）；history 里 `prev_adjudication` 的格式是否会被 verify/下游误读；
   bump 后 `adjudication` 为 pending 时 verify 是否仍 rc=0；
3. 是否有新的放行/误拒/崩溃；四真金集是否仍 T、无误拒；
4. gate 90 / 目录级 2003 自洽；生命周期测试判别力；
5. UAT §二十七 有无 overclaim；§22.3/§26.4 登记项是否仍诚实。

## ③ 输出格式

逐条 **BLOCKER/HIGH/MEDIUM/LOW**（无则写「未发现」）+ `file:line` + 一句话复现思路；
一段「未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径」；末尾「本轮总评：B= / H= / M= / L=」。

## ④ 边界

只读；不改文件；不连 7691/7687/8011；不跑非 shadow runner；不评 G4-14/R-SLO/L-5/103 条语义。
