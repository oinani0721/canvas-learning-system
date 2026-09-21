> 批次: BATCH-2026-09-18-第十五批 · 车道 P3 · 卡 CARD-G8-7 round-7
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `source "$HOME/.codex/zai.env" && codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G8-7-r7.md)" > _bmad-output/审查/codex-review-CARD-G8-7-r7.md 2> _bmad-output/审查/codex-review-CARD-G8-7-r7.stderr </dev/null`
> 　（prompt = `codex-prompt-CARD-G8-7-r7.md`，SHA 内联：PREV=`2202fde3` / FINAL=`26f9bbc5`）
> 审查绑定: `2202fde3..26f9bbc5`（FINAL = 审工作区 HEAD）；**判 B0/H0/M2/L2**（M-1 计数漂移 / M-2 journey 索引表截图列）
> 会话头自证（抄 .stderr 三行，行号括注；stderr 不入库）:
> `L2: OpenAI Codex v0.153.3` / `L5: model: glm-5.3` / `L9: reasoning effort: max`
---

# CARD-G8-7 r7 复核报告（截图登记后复核）

> 绑定：PREV=`2202fde3` → FINAL=`26f9bbc5`；实测 `git rev-parse --short=8 HEAD` = **`26f9bbc5`** ✓。本轮只读，未连 7691/7687，未目视任何图像内容（仅核登记完整性）。

## 总裁决

**PARTIAL：截图登记的实质面（文件/sha/来源/validator/零代码）独立证实闭合；但发现 2 个 MEDIUM 登记面索引漂移 ⇒ 不满足「无新发现」，暂不写「本卡可交主 session」。** 修复为纯文档小改（约 9 处单元格），改后按卡规需 r8 绑新 HEAD 复审。

---

## 分级清单

### BLOCKER（0）

无。

### HIGH（0）

无。⑥ 未被洗成 pass：manifest `assertions[G8-7-6].result=fail`、UAT §2/§4-C ⑥、T-3.6 四面一致维持 fail；六环节判定（①pass②pass③fail④fail⑤pass⑥fail）、`result=partial`、`E2`、`signoff=pending`、`outside=2` 均未变。

### MEDIUM（2）

**M-1 截图入包后 artifacts 计数索引面未随动（48 → 57 漏传 4 处）**
- `_bmad-output/验收单/UAT-CARD-G8-7-2026-09-20.md:11`（「evidence 目录文件数 = 66（含 48 件 manifest artifacts）」→ 实测 75 / 57）
- `_bmad-output/验收单/UAT-CARD-G8-7-2026-09-20.md:82`（「artifacts **48 件**」）
- `_bmad-output/验收单/UAT-CARD-G8-7-2026-09-20.md:161`（「**48 artifacts**…终版复核：48/48 件 sha256+bytes 全匹配」）
- `_bmad-output/审查/evidence-g87-journey/04-journey-log.md:28`（「artifacts **48 件**：35 + 13」）
- 复现：`python3 -c "import json;print(len(json.load(open('_bmad-output/审查/evidence-g87-journey/manifest.json'))['artifacts']))"` → **57**；`find _bmad-output/审查/evidence-g87-journey -type f | wc -l` → **75**；再 grep 上述 4 处仍写 48/66。与 r5 M-1（35→48 漏传）同类回归——本轮 48→57 又漏传。属「对照输入（manifest 权威计数）与索引面不一致」的双真相源，非证据缺失（我已独立全量复验 57/57 sha+bytes 全匹配）。

**M-2 journey T1..T6 索引表截图列仍保留已被撤回的「有」/「待补」声明**
- `_bmad-output/审查/evidence-g87-journey/04-journey-log.md:33`（② 截图列 =「有」）
- `_bmad-output/审查/evidence-g87-journey/04-journey-log.md:35`（④ =「有」）
- `_bmad-output/审查/evidence-g87-journey/04-journey-log.md:36`（⑤ =「有」）
- `_bmad-output/审查/evidence-g87-journey/04-journey-log.md:37`（⑥ =「**用户侧待补**」「整段 **fail 待补**」）
- 复现：对照同文件 `:185`（T-3.6「②/④/⑤ ⇒ 无图（未留影）」）与 UAT `:87-91`（②④⑤ 已改「无图」、⑥ 已登记失败页 ×2）——同一文件内索引表与权威修正段互相矛盾。这正是送审 prompt 核验点①明令「②④⑤ 不得仍写『有图』」的未被拦下的输入：本轮修了 UAT §2，漏修了同文件上方的 T1..T6 索引表（其「本表只作索引，不再逐格补登」序言反而让过期单元格继续以终版面目存活）。

### LOW（2）

**L-1 用户侧 3.44.49 原件来源标注「主树」未指明 checkout，按字面解析不可达**
- `_bmad-output/审查/evidence-g87-journey/04-journey-log.md:181`、`_bmad-output/验收单/UAT-CARD-G8-7-2026-09-20.md:94`、`05-g18-material.md:22`
- 复现：`ls /Users/Heishing/Desktop/canvas/canvas-learning-system/_bmad-output/截屏2026-09-20\ 下午3.44.49.png` → **不存在**（git main checkout 无此件）；实际原件在 `…/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/截屏2026-09-20 下午3.44.49.png`，sha256=`b62ff273…1c28` 与登记件**逐字节一致**（来源本身可追、已证实）。建议补注「主树 = feature-obsidian-hybrid-dev worktree（batch15 主干收尾树，commit 51acf6cd 入库件）」。

**L-2 UAT 头部开放项摘要「⑥ 截图」未随收窄更新**
- `_bmad-output/验收单/UAT-CARD-G8-7-2026-09-20.md:13`
- 复现：对照 `:175`（收口待办已精确为「⑥ 用户侧**成功页**截图…15:44 两件失败页已在案」）。头部摘要仍写泛化「⑥ 截图」，读者会误以为 ⑥ 截图整体未登记。

---

## ⓪–⑤ 核验点逐条裁定

**⓪ 9 条新 artifacts sha/bytes + 57/57 + validator** → **证实**。8 png 磁盘 `shasum -a 256` 逐条重算 = 台账 = manifest；台账自身 sha/bytes（`48d84762…`/2130）匹配；root 与 J06 两份 manifest 各 57 条**全量独立复验 0 missing / 0 mismatch**（超出 r6 只抽查 1 件的口径）；`validate_release_manifest.py` 独立复跑 rc=0。PREV 树内 png 计数 = 0（缺口认定成立），FINAL = 8。

**① 四面一致性（⑥ 不得变 pass；②④⑤ 不得仍有图）** → **部分证实**。指定的四面（UAT §2 `:87-91`、UAT §4-C `:159`、T-3.6 `:173-186`、manifest G8-7-6 note）全部一致且 ⑥ 维持 fail ✓；但 journey **T1..T6 索引表**（第五面）②④⑤ 仍写「有」、⑥ 仍「待补」⇒ M-2。

**② 用户侧原件来源可追** → **证实**。桌面 3 件（2.40.03/2.40.05/3.44.28）存在且 sha 与登记件逐字节一致；3.44.49 在 feature-obsidian-hybrid-dev 主干树存在、sha 一致、确为该树 UAT §1⑥ 内嵌引用件（`:67`）——唯「主树」标注不精确（L-1）。14:10:18 原件实测确已不在桌面/主干树（陈述如实）；`/tmp/g87-annotate-issue.png`(14:13) 为存活衍生且 sha = 登记件。

**③ 零代码 / live vault** → **证实**。`d9d64ea1..26f9bbc5 -- . ':(exclude)_bmad-output)` diff 为空；14 文件全在 `_bmad-output/`；tracked 区干净（仅 2 个 r7 评审流程 untracked 件，同 r6 先例）。

**④ 新双真相源 / 过度声明** → **部分证实（有问题）**。M-1/M-2 即本轮新引入/残留的索引面双真相源；无判定翻面、无结果洗白。「14:10:18 衍生件」表述经查如实。

**⑤ 隐私 / 不 push** → **证实（本地可证范围）**。manifest 9 条新条目均 `redacted:false`（诚实登记未脱敏）；`card/p3-deploy` 无 upstream、26f9bbc5 仅存本地，与「仅本地仓库、不 push」一致。限制：只读沙箱无法核远端 ref 是否曾收过含图 commit。

---

## 建议收口动作（最小修复）

1. UAT `:11/:82/:161`、journey `:28`：48→57（66→75）并注明「35 授权窗口 + 13 整改轮 + 9 截图登记」。
2. journey `:33/:35/:36`：「有」→「无图（未留影）」；`:37`：「用户侧待补」→「失败页 ×2 已登记（user-06-…-1544*.png），成功页仍缺」。
3. （可选，随上两类一并）L-1 补注主树所指 worktree；L-2 头部「⑥ 截图」改「⑥ 成功页截图」。
4. 逐文件 add → 新 commit → **r8 绑新 HEAD**（复用本 prompt 改 SHA）。修复不触及任何判定字段与证据二进制。

**边界与限制**：本轮未目视图像内容（遵守 ②7，图像结论仍以车道转写 + 登记自洽为准）；未重评 G1-8/G6-13/skill 差异/Excalidraw 导出器；用户侧四项开放（③ 带锚点复跑 / ⑥ 成功页 / 思维导图触发者 / 签字）维持不变；远端不可达性未验。
