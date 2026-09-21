# CARD-G8-7 送审 prompt（r10 · r9 处置复审 · SHA 内联自包含）

> 本件 = r9（B0/**H1**/M1/L3）的最小处置复审。绑定值内联，缺省不可替换。
> 命令（cwd = 车道树）：`source "$HOME/.codex/zai.env" && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G8-7-r10.md)" > _bmad-output/审查/codex-review-CARD-G8-7-r10.md 2> _bmad-output/审查/codex-review-CARD-G8-7-r10.stderr </dev/null`

## ① 背景与最小读取面（写死）

- **PREV = `49247d54`**；**FINAL = `b22e51d4`**（`git rev-parse --short=8 HEAD` 应等于它）。
- 读取面（其余不读）：
  1. `git --no-pager diff --stat --no-color 49247d54 b22e51d4` 与 `git --no-pager diff --stat --no-color d9d64ea1 b22e51d4 -- . ':(exclude)_bmad-output'`（应为空）
  2. `_bmad-output/审查/evidence-g87-journey/minute0-reconstruct-20260920T193730.txt`（**含末尾 ERRATA v2 节**）与 `…/fsrs-decay-scope-20260920T193722.txt`（**含末尾补注 v2 节**）
  3. `_bmad-output/审查/evidence-g87-journey/manifest.json`（两档新 sha256/bytes；`known_limitations` 末 2 条；`notes` 末段）+ J06 副本 validator 独立复跑
  4. `_bmad-output/审查/evidence-g87-journey/04-journey-log.md`（T-3.7 BASE 行更正 + **T-3.8**）
  5. `_bmad-output/验收单/UAT-CARD-G8-7-2026-09-20.md`（4-C ②⑤ 行 + §6 ⑦⑧）
  6. `_bmad-output/审查/codex-review-CARD-G8-7-r9.md`（被处置的四项原文）

## ② 作者自述（请独立核对，逐条给 证实/部分/证伪）

1. **H1 闭合**：minute0 档追加 **ERRATA v2**：明示第 4 条首跑为败录（引号转义 → grep/shasum No such file）、现复核 `grep -vc '^#'`=**33**、sha256=**726e998a7254871838cef77782830e6a719dcc26aefa93abe28fe3e945042cb4**、mtime 09-17；原文不改写；journey T-3.7 的「sha256 在案」表述已改为直书 sha 前缀 + errata 指针。
2. **M1 闭合**：fsrs 档补注 —— B(2) 段登记后重跑会出现 2 命中（源 = manifest artifacts `description` 文本自引用），复现口径须排除 description 行；实质判定不变（命中为散文非命令）。
3. **L1/L2 闭合**：6→7 时点差、允许面含 `01-skill-versions.md:37` 结论段的分类宽贷，均在档内注明。
4. **L3 闭合**：伴随件 `_bmad-output/审查/evidence-g87/jev-triage-<SHA>.json` 入 UAT §6 台账（⑧）。
5. **(g)② 登记**：②⑤ 无截图 ⇒ **环境级 partial** 写入 UAT 4-C（🔶）与 `known_limitations`；assertions 语句级 pass 未改（其 statement 成立）；是否收紧交主 session 裁定。
6. **未变项**：六环节 assertions（①pass②pass③fail④fail⑤pass⑥fail）、`result=partial`、`E2`、`signoff=pending`、`outside=2` 未变；零代码；live vault 零写；manifest artifacts 仍 **59**（两档哈希随补注重算）。

## ③ 按重要性排序的核验点

⓪ 两档补注后 sha256/bytes 是否与 manifest 逐条一致（59/59）；validator rc=0 可否独立复跑。
① ERRATA v2 的数值是否属实（可独立重跑 `grep -vc '^#' <BASE>` 与 `shasum -a 256 <BASE>`）；「原文不改写」是否为真（首跑败录行是否仍在）。
② fsrs 档补注后的复现口径是否可照做且能得 0 命中（可独立复跑：排除 description 行后两段意图检查应均 0 命中）。
③ (g)② 的登记是否**没有**偷偷把 fail/partial 洗成 pass，也没有把 pass 硬翻成 fail 而不给理由；「交主 session 裁定」是否写明。
④ 索引一致性：artifacts 59 / 文件数（如需）在各面是否一致；有无残留旧值。
⑤ 零代码 / 零 live 写；本轮 delta 是否全在 `_bmad-output`。
⑥ r8/r9 的既有结论是否受影响（是否出现新的判定翻面或双真相源）。

## ④ 输出格式

BLOCKER/HIGH/MEDIUM/LOW 分级清单 + 每条 `file:line` + 一句复现思路；措辞用 **负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**。若四项闭合、(g)② 登记无洗白、无新发现，请明确写 "**r9 处置闭合，本卡可交主 session**"。

## ⑤ 边界

只读；不连 7691/7687；不评 G1-8 终审；不评 G6-13 跨日；不评 8 处 skill 差异本身对错；不评自研 Excalidraw 导出器设计；不要求用户签字位已勾选；不要求目视图像内容。用户侧仍开放：③ 带锚点复跑 / ⑥ 成功页截图 / 思维导图触发者确认 / 签字。
