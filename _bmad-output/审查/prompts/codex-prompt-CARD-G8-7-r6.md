# CARD-G8-7 送审 prompt（r6 · 轻量闭合复核 · SHA 内联自包含）

> 本件 = r5（`codex-review-CARD-G8-7-r5.md`：B0/H0/**M1**/L1）的**最小收口复核轮**。绑定值内联，缺省不可替换。
> 命令（cwd = 车道树）：`source "$HOME/.codex/zai.env" && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G8-7-r6.md)" > _bmad-output/审查/codex-review-CARD-G8-7-r6.md 2> _bmad-output/审查/codex-review-CARD-G8-7-r6.stderr </dev/null`

## ① 背景与最小读取面（写死）

- **PREV = `67796927`**（r5 审对象）；**FINAL = `5ca21a29`**（收口 commit；`git rev-parse --short=8 HEAD` 应等于它）。
- 本轮=**轻量闭合**：只核 r5 的 M-1（artifacts 计数 35→48 三处）与 L-1（UAT 孤儿表头），外加"无新漂移"。
- 读取面（其余不读）：
  1. `git --no-pager diff --stat --no-color 67796927 5ca21a29`（全清单，应全在 `_bmad-output/`）
  2. `git --no-pager diff --stat --no-color d9d64ea1 5ca21a29 -- . ':(exclude)_bmad-output'`（应为空）
  3. `_bmad-output/验收单/UAT-CARD-G8-7-2026-09-20.md` §2（含注记 + 4-A 表）与 §4-C manifest 行
  4. `_bmad-output/审查/evidence-g87-journey/04-journey-log.md` T1..T6 索引段
  5. `_bmad-output/审查/evidence-g87-journey/manifest.json`（`artifacts` 计数与 `04-journey-log.md` 条目哈希）+ `b15-g8-7/journeys/J06/manifest.json`
  6. `_bmad-output/审查/codex-review-CARD-G8-7-r5.md`（被核的 M-1/L-1 原文）
  7. `_bmad-output/审查/prompts/codex-prompt-CARD-G8-7-r5.md` 首部（笔误更正块）

## ② 作者自述（请独立核对，逐条给 证实/部分/证伪）

1. **M-1 处置**：UAT §2 注记、UAT 4-C manifest 行、`04-journey-log.md` 索引段三处均改为 **48**，并注明「35 = 授权窗口时点 / 48 = 整改轮终版」；`grep -c '35 artifacts\|35/35\|artifacts 35 件'` 三处 = 0。
2. **L-1 处置**：UAT §2 旧 4-A 模板的孤儿表头两行已删（现该段只有一条注记 + 一张真表）。
3. **无新漂移**：`04-journey-log.md` 本次编辑后其 manifest 条目 `sha256+bytes` 已重算；manifest `artifacts` 仍 = **48**；J06 结构内副本 validator rc=0。
4. **自查笔误更正（非 r5 判罚项）**：r5 prompt 作者自述 #4 原写「免沙箱 = 33 红」，已加更正块（权威档 32 failed / 5845 passed；33 为沙箱首跑数），原文不改写；r5 报告 #4 已指出同一处。
5. **未变项**：本卡零代码（排除 `_bmad-output` 后 diff 空）；signoff 仍 `pending`；③/⑥ 判据未改判；`outside=2` 仍为开放项；用户侧四项开放维持。

## ③ 按重要性排序的核验点

⓪ M-1 三处计数是否真为 48、且与 `jq '.artifacts|length'` 实测一致（不得只改文字不核 manifest）。
① L-1 孤儿表头是否确已删除、且未误删 4-A 真表或其表头。
② `04-journey-log.md` 改动后 manifest 条目哈希是否重算（validator rc=0 是否可独立复跑）。
③ 本轮是否有任何 `_bmad-output` 外改动（零代码卡）。
④ 是否有新的双真相源（计数、判据、签字段三面）。

## ④ 输出格式

BLOCKER/HIGH/MEDIUM/LOW 分级清单 + 每条 `file:line` + 一句复现思路；措辞用 **负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**。若 M-1/L-1 全闭合且无新发现，请明确写 "**r5 收口闭合，本卡可交主 session**"。

## ⑤ 边界

只读；不连 7691/7687；不评 G1-8 终审；不评 G6-13 跨日；不评 8 处 skill 差异本身对错；不评自研 Excalidraw 导出器设计；不要求用户签字位已勾选（用户侧四项开放：③ 带锚点复跑 / ⑥ 截图 / 思维导图触发者确认 / 签字）。
