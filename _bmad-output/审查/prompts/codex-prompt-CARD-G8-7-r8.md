# CARD-G8-7 送审 prompt（r8 · r7 收口复审 · SHA 内联自包含）

> 本件 = r7（B0/H0/**M2**/L2：计数漂移 M-1 + journey 索引表 M-2；L-1/L-2）的**最小收口复审**。绑定值内联，缺省不可替换。
> 命令（cwd = 车道树）：`source "$HOME/.codex/zai.env" && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G8-7-r8.md)" > _bmad-output/审查/codex-review-CARD-G8-7-r8.md 2> _bmad-output/审查/codex-review-CARD-G8-7-r8.stderr </dev/null`

## ① 背景与最小读取面（写死）

- **PREV = `26f9bbc5`**；**FINAL = `acf8cedf`**（r7 收口 commit；`git rev-parse --short=8 HEAD` 应等于它）。
- 本轮只核 r7 的 4 项（M-1/M-2/L-1/L-2）+「无新漂移」。
- 读取面（其余不读）：
  1. `git --no-pager diff --stat --no-color 26f9bbc5 acf8cedf`（全清单）与 `git --no-pager diff --stat --no-color d9d64ea1 acf8cedf -- . ':(exclude)_bmad-output'`（应为空）
  2. `_bmad-output/验收单/UAT-CARD-G8-7-2026-09-20.md`：头部终态字段（:9-13）、§2 注记（:82）、§2 表截图列（:87-91）、§4-C manifest 行（:161）、截图登记注（:94）
  3. `_bmad-output/审查/evidence-g87-journey/04-journey-log.md`：:28 索引说明、:30-37 T1..T6 表、:181（L-1 行）、T-3.6 段
  4. `_bmad-output/审查/evidence-g87-journey/manifest.json`（`artifacts` 计数）+ J06 副本 validator 独立复跑
  5. `_bmad-output/审查/evidence-g87-journey/05-g18-material.md`（L-1 行）
  6. `_bmad-output/审查/codex-review-CARD-G8-7-r7.md`（被核的四项原文）

## ② 作者自述（请独立核对，逐条给 证实/部分/证伪）

1. **M-1 闭合**：artifacts 计数四处（UAT 头部终态 / §2 注记 / §4-C / journey :28）已改 **57**（= 35 授权窗口 + 13 整改轮裁判 + 9 截图登记）；evidence 文件数 **75**；终态字段改为「权威 = `git log` / `jq '.artifacts|length'` / `find | wc -l`」口径以免下轮归档再漂移。
2. **M-2 闭合**：journey T1..T6 索引表截图列 —— ②④⑤「有」→「无图（未留影）」；⑥「用户侧待补」→「失败页 ×2 已登记（`screenshots/user-06-refresh-503-1544*.png`），成功页仍缺 / 整段 fail（用户侧实见 503）」。
3. **L-1 闭合**：三处「主树」→ 主干树 `feature-obsidian-hybrid-dev` worktree 全称（UAT :94 / journey :181 / 05-g18 :22）。
4. **L-2 闭合**：UAT 头部开放项「⑥ 截图」→「⑥ 成功页截图（15:44 失败页 ×2 已入包）」。
5. **无新漂移**：六环节判定（①pass②pass③fail④fail⑤pass⑥fail）、`result=partial`、`E2`、`signoff=pending`、`outside=2` 开放项均未变；manifest artifacts 仍 57 且 57/57 匹配；validator rc=0；零代码；本 commit 仅 7 个文件全在 `_bmad-output/`。
6. **口径诚实性**：本轮未新增/删除任何证据二进制（8 png + 台账均为上一 commit 内容），只改索引文本。

## ③ 按重要性排序的核验点

⓪ r7 四项是否逐条真闭合（M-1 四处计数、M-2 四个单元格、L-1 三处、L-2 一处）。
① 索引文本与 `jq '.artifacts|length'` / `find | wc -l` 实测是否一致（57 / 75）。
② journey 索引表与 T-3.6 / UAT §2 是否仍自相矛盾（应无）。
③ 是否有 `_bmad-output` 外改动（零代码卡）；是否动了 live vault（应零）。
④ 是否引入新的双真相源或过度声明（含「无图（未留影）」是否被误写成「缺失缺陷」）。
⑤ manifest 两份中 04-journey-log / 05-g18 条目哈希是否与磁盘一致（validator 可独立复跑）。

## ④ 输出格式

BLOCKER/HIGH/MEDIUM/LOW 分级清单 + 每条 `file:line` + 一句复现思路；措辞用 **负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**。若四项全闭合且无新发现，请明确写 "**r7 收口闭合，本卡可交主 session**"。

## ⑤ 边界

只读；不连 7691/7687；不评 G1-8 终审；不评 G6-13 跨日；不评 8 处 skill 差异本身对错；不评自研 Excalidraw 导出器设计；不要求用户签字位已勾选；不要求目视图像内容（图像结论以车道转写 + 登记自洽为准）。用户侧仍开放：③ 带锚点复跑 / ⑥ 成功页截图 / 思维导图触发者确认 / 签字。
