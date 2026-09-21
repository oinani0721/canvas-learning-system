# CARD-G4-13 r15 独立复核任务书（Codex × DeepSeek V4.1 Flash · 开发/证据面）

> 复核对象 = commit `f277fdad`（父 `12d61f9a`）；批次 `[BATCH-2026-09-18-第十五批 / CARD-G4-13]`。
> 只读复核，**不改任何文件**。

## ① 背景与最小读取面

r14 复核对 `12d61f9a` 报 **B=0/H=0/M=0/L=3**：`contains: 0` 窄口径 fail-open、expect_hit 文案名实、
r14 中间态证据未注记。`f277fdad` 三条收尾（`_contains_ok` 拒 falsy；文案同步；证据注记 + 1 case）。

最小读取面：
- `git --no-pager diff 12d61f9a f277fdad -- backend/scripts/gold_set_manifest_tool.py backend/tests/regression/test_gold_set_manifest_g413.py`
- `backend/scripts/gold_set_manifest_tool.py` 第 395-700（守卫全段）
- `_bmad-output/审查/codex-review-CARD-G4-13-r14.md`（上一轮全文）
- `_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19.md` §二十二
- 证据：`_bmad-output/审查/evidence-g413/r15-*`

## ② 核对点

1. r14 三条 LOW 逐条复算（r14 源码 vs r15 源码同 fixture：`contains: 0/"0"/0.0/.nan`、文案、证据）；
2. 放宽/收紧后是否引入新 fail-open 或误拒（`contains` 全形态表、`grade` 全形态表、四真金集 8 处
   `contains` 是否全 T）；
3. 是否还有「守卫 T 但 runner 落 rc=1 或 fail-open」的新路径；
4. 1 个新 case 是否真判别；gate 82 / 目录级 1995 自洽；
5. UAT §二十二 / §22.3 残余登记是否诚实。

## ③ 输出格式

逐条 **BLOCKER/HIGH/MEDIUM/LOW**（无则写「未发现」）+ `file:line` + 一句话复现思路；
一段「未被拦下的输入 / 对照输入 / 负控输入 / 门未覆盖的路径」；末尾「本轮总评：B= / H= / M= / L=」。

## ④ 边界

只读；不改文件；不连 7691/7687/8011；不跑非 shadow runner；不评 G4-14/R-SLO/L-5/103 条语义。
