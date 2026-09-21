# CARD-G8-7 送审 prompt（r9 · 判据覆盖自审补后复审 · SHA 内联自包含）

> 本件 = r8（B0/H0/M0/L1「r7 收口闭合」）之后**包体再次变更**（判据覆盖自审补：2 件新存档、artifacts 57→59）的复审轮。绑定值内联，缺省不可替换。
> 命令（cwd = 车道树）：`source "$HOME/.codex/zai.env" && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G8-7-r9.md)" > _bmad-output/审查/codex-review-CARD-G8-7-r9.md 2> _bmad-output/审查/codex-review-CARD-G8-7-r9.stderr </dev/null`

## ① 背景与最小读取面（写死）

- **PREV = `1464de1f`**；**FINAL = `49247d54`**（`git rev-parse --short=8 HEAD` 应等于它）。
- 本轮对象 = 按卡文 §一/§二逐条自审后补的两条**判据覆盖缺口**（此前未落档）：(m) fsrs_bridge/decay_beta 出现面 grep 补跑；§二.1 第 0 分钟判据重建。
- 读取面（其余不读）：
  1. `git --no-pager diff --stat --no-color 1464de1f 49247d54`（全清单）与 `git --no-pager diff --stat --no-color d9d64ea1 49247d54 -- . ':(exclude)_bmad-output'`（应为空）
  2. `_bmad-output/审查/evidence-g87-journey/fsrs-decay-scope-20260920T193722.txt`（全文）
  3. `_bmad-output/审查/evidence-g87-journey/minute0-reconstruct-20260920T193730.txt`（全文）
  4. `_bmad-output/审查/evidence-g87-journey/manifest.json`（`artifacts`=59 与两新条目；`known_limitations` 末条；`notes` 末段）+ J06 副本 validator 独立复跑
  5. `_bmad-output/审查/evidence-g87-journey/03-breakpoints.md`（§B 两新行）、`04-journey-log.md`（T-3.7 + 索引行 :28）
  6. `_bmad-output/验收单/UAT-CARD-G8-7-2026-09-20.md`（计数四处 + §5 第 6 条）
  7. 卡文 `…/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P3-C.md` §一(m) 与 §二.1（判据原文）

## ② 作者自述（请独立核对，逐条给 证实/部分/证伪）

1. **缺口认定**：(m) 的现象面 grep 与 §二.1 第 0 分钟判据在此前证据包内**均无落档**（`find $EV` 无对应文件）；r2–r8 各轮未点名此二项。
2. **(m) 补跑结论**：形态判据**红**（卡文原文只允许出现在 `01-skill-versions.md` sha 表行与 `00-README` 环节说明）—— 实测另有 03/04/05 共 7 行（缺陷登记/索引说明）与第三方报告（glm53-503 / glm53-pi / digest）共 15 行；**意图判据绿**（`cp|mv|install` 形态 0 命中、`tee|cat|shutil.copy` 形态 0 命中，且已排除本存档自身）；支撑 = 两文件 dev==live 2/2 SAME、本卡 `d9d64ea1..HEAD` 全 diff 触碰 0 行、live 现值 a766fbcc…/3bf4ed94… 在案。首版 intent-grep 自匹配已作废并在档内注明。
3. **§二.1 重建**：明示「非当场落档」；可重建三条（HEAD=9d4f7bf0 来源 `00-prefix-red-*.txt:2`、分支 card/p3-deploy、BASE `grep -vc '^#'`=33 现复核）+ 不适用一条（pyright，卡文 (h)）+ 等价证据一条（docker ps ↔ journey T-1）；**当时 `status` 与 §〇 sed 深核未落档**如实登记。
4. **登记面**：manifest artifacts 57 → **59**；两新条目 sha256/bytes 与磁盘一致；`known_limitations` +1（§二.1 缺口）；`notes` +1 段；03-breakpoints §B +2 行；journey T-3.7；UAT 计数四处 59/77 + §5 第 6 条。
5. **未变项**：六环节判定（①pass②pass③fail④fail⑤pass⑥fail）、`result=partial`、`E2`、`signoff=pending`、`outside=2` 开放项均未变；零代码；live vault 零写。
6. **本次自审的方法论声明**：这是「按卡文逐条对现状」的覆盖审计，不是翻案；两条均为**覆盖缺口**（判据未落档/形态过宽），非产物缺陷。

## ③ 按重要性排序的核验点

⓪ 两条新存档的 sha256/bytes 是否与 manifest 逐条一致；59/59 是否全匹配；validator rc=0 可否独立复跑。
① (m) 档内的分类计数（允许面 5 / 登记索引 7 / 第三方 15）是否与实测一致；意图判据两段是否真 0 命中（可独立重跑，注意排除本存档自身）。
② (m) 的**判定方向**是否被写反（形态红 / 意图绿 不得混为「绿」或写成「本卡零写者即全部通过」）；「判据形态过宽」是否如实交主 session 而非自裁收窄。
③ §二.1 重建是否被冒充实录（必须自证「非当场落档」，且未把不可重建项写成已重建）。
④ 索引计数：UAT 四处 / journey :28 / manifest 实测 是否同为 **59**（文件数 77）；有无残留 57/75。
⑤ 零代码 / 零 live 写：`d9d64ea1..49247d54` 排除 `_bmad-output` 是否为空；本轮 delta 文件是否全在 `_bmad-output`。
⑥ 有无新双真相源或判定翻面；r8 的闭合结论是否受影响。

## ④ 输出格式

BLOCKER/HIGH/MEDIUM/LOW 分级清单 + 每条 `file:line` + 一句复现思路；措辞用 **负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**。若两条覆盖缺口登记闭合、无新发现、r8 结论不受影响，请明确写 "**判据覆盖自查闭合，本卡可交主 session**"。

## ⑤ 边界

只读；不连 7691/7687；不评 G1-8 终审；不评 G6-13 跨日；不评 8 处 skill 差异本身对错；不评自研 Excalidraw 导出器设计；不要求用户签字位已勾选；不要求目视图像内容。用户侧仍开放：③ 带锚点复跑 / ⑥ 成功页截图 / 思维导图触发者确认 / 签字。
