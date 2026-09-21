# CARD-G8-7 送审 prompt（r7 · 截图登记后复核 · SHA 内联自包含）

> 本件 = r6（判 B0/H0/M0/L0「收口闭合」）之后**包体发生变更**（截图登记入包）的复核轮，按卡文「送审后若改了 evidence/manifest ⇒ 再送一轮绑新 HEAD」。绑定值内联，缺省不可替换。
> 命令（cwd = 车道树）：`source "$HOME/.codex/zai.env" && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G8-7-r7.md)" > _bmad-output/审查/codex-review-CARD-G8-7-r7.md 2> _bmad-output/审查/codex-review-CARD-G8-7-r7.stderr </dev/null`

## ① 背景与最小读取面（写死）

- **PREV = `2202fde3`**（r6 后的归档 commit）；**FINAL = `26f9bbc5`**（截图登记 commit；`git rev-parse --short=8 HEAD` 应等于它）。
- 本轮对象 = 截图登记（8 件入包）+ 由它触发的登记面更新（UAT §2 截图列修正、⑥ 断言 note、journey T-3.6、05-g18 截图清单实测化）。
- 读取面（其余不读）：
  1. `git --no-pager diff --stat --no-color 2202fde3 26f9bbc5`（全清单）与 `git --no-pager diff --stat --no-color d9d64ea1 26f9bbc5 -- . ':(exclude)_bmad-output'`（应为空）
  2. `_bmad-output/审查/evidence-g87-journey/screenshots/`（`ls -la` = 8 个 png）+ `artifacts-sha-screenshots-20260920T190917.txt`（全文）
  3. `_bmad-output/审查/evidence-g87-journey/manifest.json`（`artifacts` 计数与 9 条新条目；`assertions` 中 G8-7-6 的 note；`notes` 末段）+ `b15-g8-7/journeys/J06/manifest.json`（validator rc 复跑）
  4. `_bmad-output/验收单/UAT-CARD-G8-7-2026-09-20.md` §2（表 + 截图登记注）与 §4-C ⑥ 行 + 收口待办
  5. `_bmad-output/审查/evidence-g87-journey/04-journey-log.md` T-3.6 段；`05-g18-material.md` §1
  6. `_bmad-output/审查/codex-review-CARD-G8-7-r6.md`（前轮闭合范围）

## ② 作者自述（请独立核对，逐条给 证实/部分/证伪）

1. **缺口认定**：r6 后核查 `find $EV -name '*.png'` = 0，而卡文 (c)⑥ / (o) 要求截图入包 ⇒ 属 AND 条件缺口（非锦上添花）。
2. **登记内容**：8 件 = 用户侧 4（① 现场 2 = 桌面截屏 2.40.03/2.40.05；⑥ 失败页 2 = 桌面 3.44.28 + 主树 `_bmad-output/截屏2026-09-20 下午3.44.49.png`）+ 车道侧 4（源 `/tmp/g87-*.png`）；每件 sha256 入 `artifacts-sha-screenshots-*.txt` 与 manifest。
3. **内容结论（车道目视转写）**：⑥ 两件用户侧截图 = `http://127.0.0.1:8011/api/v1/review/overview/refresh`「刷新失败 · test-vault / HTTP 503 / pick_failed」，traceback `ModuleNotFoundError: No module named 'decay_beta'` ⇒ 与已登记 GLM 503 结论同向；**故 ⑥ 维持 fail**（未洗成 pass）。
4. **诚实修正**：UAT §2 截图列此前对 ②/④/⑤ 写「用户侧有」，实测**无对应文件** ⇒ 改「无图（未留影）」；①③⑥ 亦已逐条改为实测。
5. **未变项**：零代码（排除 `_bmad-output` 后 diff 空）；六环节判定、`result=partial`、`E2`、`signoff=pending`、`outside=2` 开放项均未变；manifest artifacts 48 → **57**，validator rc=0。
6. **隐私口径**：用户侧截图含用户 Obsidian/浏览器画面，原样收录未脱敏，仅本地仓库、不 push；已写入 manifest `notes` 与 05-g18。
7. **图像真伪边界**：本轮不要求评审者目视（GLM 通道自证读不了图）；目视转写由车道完成并写入 T-3.6/UAT。评审者应核**登记完整性**（文件在、sha 对、来源可追、描述与文件名自洽），不得声称看过图。

## ③ 按重要性排序的核验点

⓪ 9 条新 artifacts（8 png + 1 台账）sha256/bytes 是否与磁盘逐条一致；manifest 是否 57/57 全匹配（validator rc=0 可独立复跑）。
① 截图列修正后 UAT §2 / §4-C ⑥ / journey T-3.6 / manifest ⑥ note 四面是否一致（⑥ 不得变 pass；②④⑤ 不得仍写「有图」）。
② 用户侧原件来源是否可追（桌面 3 件 + 主树 1 件），登记名与来源注记是否自洽；`user-06-refresh-503-154449.png` 是否确为主树 UAT 内嵌引用件。
③ 本轮是否有 `_bmad-output` 外改动（零代码卡）；是否动了 live vault（应零）。
④ 是否有新的双真相源或过度声明（含「14:10:18 原件已不在盘上、登记件为其衍生」这一表述是否如实）。
⑤ 隐私/边界：原样收录未脱敏 + 不 push 的声明是否与仓库状态一致（本卡不 push 为硬边界）。

## ④ 输出格式

BLOCKER/HIGH/MEDIUM/LOW 分级清单 + 每条 `file:line` + 一句复现思路；措辞用 **负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**。若截图登记闭合、无新发现、且前轮 r6 结论不受影响，请明确写 "**截图登记闭合，本卡可交主 session**"。

## ⑤ 边界

只读；不连 7691/7687；不评 G1-8 终审；不评 G6-13 跨日；不评 8 处 skill 差异本身对错；不评自研 Excalidraw 导出器设计；不要求用户签字位已勾选；不要求评审者目视图像内容（见 ②7）。用户侧仍开放：③ 带锚点复跑 / ⑥ 成功页截图 / 思维导图触发者确认 / 签字。
