# CARD-G4-13 r16 独立复核任务书（Codex × DeepSeek V4.1 Flash · 开发/证据面 · 收口轮）

> 复核对象 = commit `f989d0fe`（父 `f277fdad`）；批次 `[BATCH-2026-09-18-第十五批 / CARD-G4-13]`。
> 只读复核，**不改任何文件**。

## ① 背景与最小读取面

r15 复核对 `f277fdad` 报 **B=0/H=0/M=0/L=3**（连续第二轮 M=0）；三条 LOW 均为文档/语义自由度级。
`f989d0fe` 收尾：`_contains_ok` 拒非有限浮点（nan/inf）、报错文案补全、UAT §22.3 列表补全。

最小读取面：
- `git --no-pager diff f277fdad f989d0fe`
- `backend/scripts/gold_set_manifest_tool.py` 第 395-570（`_contains_ok`/`expect_hit` 守卫与文案）
- `_bmad-output/审查/codex-review-CARD-G4-13-r15.md`（上一轮全文）
- `_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19.md` §二十~§二十三
- 证据：`_bmad-output/审查/evidence-g413/r16-*`

## ② 核对点（收口判定）

1. r15 三条 LOW 逐条复算（`contains: nan/inf/"0"/0/0.0/5/" "/\u00a0` 全表、文案与 `_contains_ok` 名实、§22.3 列表）；
2. **是否还有任何 M 级及以上的新路径**（守卫 T 但 runner 落 rc=1/崩溃/fail-open；或误拒 runner 可跑形状）；
2b. 四真金集是否仍全 T、无误拒（含 8 处 `contains`）；
3. gate 82 / 目录级 1995 / 四 sha / verify 自洽；
4. §22.3 残余登记（LOW-4、L-5、`vault_id:null`、`max_in_top_k` 注解自由度）是否诚实完整。

## ③ 输出格式

逐条 **BLOCKER/HIGH/MEDIUM/LOW**（无则写「未发现」）+ `file:line` + 一句话复现思路；
一段「未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径」；末尾「本轮总评：B= / H= / M= / L=」。

## ④ 边界

只读；不改文件；不连 7691/7687/8011；不跑非 shadow runner；不评 G4-14/R-SLO/L-5/103 条语义。
