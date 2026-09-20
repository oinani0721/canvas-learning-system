> 批次: BATCH-2026-09-18-第十五批 · 车道 P3 · 卡 CARD-G8-7 round-1
> 模型: `glm-5.3` · reasoning_effort: `max` · codex: `codex-cli 0.153.3`
> 命令: `codex exec --profile zai --sandbox read-only -m glm-5.3 -c model_reasoning_effort="max" "$(cat _bmad-output/审查/prompts/codex-prompt-CARD-G8-7.md)"`
> 审查绑定: 审工作区 @ HEAD=9d4f7bf0（未提交；本卡零代码, 改动面全在 `_bmad-output/`）
> 会话头自证（抄 .stderr 三行, 行号括注）:
> `L2: OpenAI Codex v0.153.3` / `L5: model: glm-5.3` / `L9: reasoning effort: max`
---

## 复核结论：PARTIAL

未发现 **BLOCKER**：当前证据没有把六环节装绿，根 manifest 仍如实登记 `partial / E0 / pending`，且六环节均为 `not_run`。  
但 **⓪「零静默改写门已充分验证」不能成立**；只能说“指定文件的修正版负控通过，门实现与边界仍缺可复现证据”。

范围核对：`9d4f7bf0..HEAD` 排除 `_bmad-output` 后 diff-stat 为空；`git status --porcelain` 仅见 `_bmad-output/` 下未跟踪证据/审查/prompt 文件。

---

## BLOCKER

无。

---

## HIGH

1. **负控①的“卡文字面缺陷”证据不可复现，且该输入本身是 no-op**
   - `_bmad-output/审查/evidence-g87-journey/negctl1-cardtext-sed-noop-20260919T173131.txt:2-7`
   - 现象：验伪锚为 `0`，卡文字面检出为 `0`，修正版检出也为 `0`；说明负控输入没有产生实际变化，因此不能证明“门未拦下集外变化”，也不能证明 `sed`/`awk` 判据缺陷。
   - 复现思路：保留原始摘要行、精确 `sed`/`awk` 命令、变异后摘要行与 diff；用一个先确认 `diff=1` 的对照输入分别跑卡文字面与修正判据。

2. **路径含空格场景未被有效负控覆盖**
   - `_bmad-output/审查/evidence-g87-journey/02-live-snapshot-before.txt:3`
   - `_bmad-output/审查/evidence-g87-journey/negctl1-snapshot-20260919T173142.txt:4-9`
   - 现象：真实清单存在含空格路径，但通过的正控只改 `原白板/CS.md`，没有测试含空格路径被截断后的归属判断。
   - 复现思路：对一个含空格的 `原白板/... (…).md` 摘要行做单行变异，分别输出卡文字面提取路径与修正版完整路径，并核对 `outside` 计数。

3. **白名单粒度缺少“未相关节点”负控；不能证明未放行整个 `节点/` 前缀**
   - `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P3-C.md:29`
   - `_bmad-output/审查/evidence-g87-journey/silent-rewrite-gate-20260919T173124.txt:1`
   - 现象：卡文声明面是精确的 `节点/<被答节点>.md` 与 `节点/<新材料>.md`，但门产物只有 `changed=0 outside=0`，没有白名单实现或未相关节点变异结果。
   - 复现思路：变异一个既非被答节点也非新材料的 `节点/<other>.md`；期望输出 `outside=1` 且打印完整指定路径，若仍为 `0` 即为前缀过宽。

4. **manifest“先红/后绿”与 signoff 负控未形成孤立对照**
   - `_bmad-output/审查/evidence-g87-journey/manifest-green-20260919T173050.txt:1-4`
   - `_bmad-output/审查/evidence-g87-journey/manifest-red-20260919T173056.txt:1-6`
   - `_bmad-output/审查/evidence-g87-journey/negctl2-signoff-20260919T173154.txt:2-8`
   - 现象：J06 上的 S3 红档时间晚于绿档，不能仅凭文件名证明顺序；signoff 负控同时红在既有 `journey_id` schema 冲突与缺失 `user/at`，不是单变量对照。
   - 复现思路：从已绿的 J06 副本出发，仅把 `signoff.status` 改为 `approved` 且不填 `user/at`，单独跑 validator，并按顺序落 `before/red/after-green` 日志。

5. **`search_notes` 判据缺少新材料身份绑定，可被同名/同题旧材料命中**
   - `_bmad-output/审查/evidence-g87-journey/00-README.md:14`
   - `/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/implementation-artifacts/goal-cards/第十五批-goals/P3-C.md:28`
   - 现象：判据只写“返回体含新材料”，未强制匹配新材料完整路径、内容摘要或唯一标识。
   - 复现思路：准备一个与既有节点同名/同标题的旧材料，令返回体只含旧路径；若判据仍按字符串命中判绿，即证明假绿路径。

---

## MEDIUM

1. **环节⑤判据不足以证明 FSRS bridge 更新**
   - `_bmad-output/审查/evidence-g87-journey/00-README.md:16`
   - `_bmad-output/审查/evidence-g87-journey/manifest.json:98-101`
   - `canvas-vault/.claude/skills/quiz-answer/SKILL.md:74`
   - 现象：README 预期包含 `fsrs_*`，但 assertion/method 只检查 `mastery_*`；而 skill 自述不碰后端熟练度链，仅写本地 Beta 后验状态量。
   - 复现思路：跑前后 `grep -e mastery_ -e fsrs_`，并保存 `fsrs_bridge.py`/相关脚本的调用命令、退出码与输出摘要；若只有 `mastery_*` 变化，应记录为“本地掌握度更新，不证明 FSRS bridge”。

2. **根 manifest 不是完整证据包索引，执行窗口未覆盖后续门/负控**
   - `_bmad-output/审查/evidence-g87-journey/manifest.json:35-56`
   - `_bmad-output/审查/evidence-g87-journey/manifest.json:117-124`
   - `_bmad-output/审查/evidence-g87-journey/negctl2-signoff-20260919T173154.txt:1`
   - 现象：manifest `started/finished` 停在 `16:57:47`，commands/artifacts 只覆盖骨架期三命令与 before snapshot，未登记 17:30–17:31 的 validator、零改写门与负控产物。
   - 复现思路：为证据包增加一个顺序化 run log，或更新 manifest 的 execution/artifacts，使每个门/负控都有命令、时间、rc 与产物摘要。

---

## LOW

1. **README 对 unauthorized 分支的 `04` 产物描述与实际不一致**
   - `_bmad-output/审查/evidence-g87-journey/00-README.md:37`
   - `_bmad-output/审查/evidence-g87-journey/04-live-snapshot-after.txt:1`
   - `_bmad-output/审查/evidence-g87-journey/03-breakpoints.md:35`
   - 现象：README 说未授权则 `04-live-snapshot-after.txt` 不产出，但该文件存在且断点表声明已跑。
   - 复现思路：把 README 改成“`04-journey-log.md` 未授权不产出；`04-live-snapshot-after.txt` 未授权仍做只读收尾快照”。

2. **`search_notes` 前置断点引用了读取面外文件，包内不可复核**
   - `_bmad-output/审查/evidence-g87-journey/03-breakpoints.md:13`
   - 现象：该行引用后端文件作为证据，但证据包未包含命令输出或摘录。
   - 复现思路：把当时的只读命令输出/关键行摘录纳入证据包，或标注为“读取面外主张，未复核”。

---

## 已核对为如实/有价值的点

- **六环节未装绿**：根 manifest 六个 assertion 全为 `not_run`（`manifest.json:68-110`），断点表 §C 同步登记（`03-breakpoints.md:22-33`）。
- **不自升证据等级**：`evidence_level=E0`、顶层 `partial`、`signoff=pending`（`manifest.json:130-135`）。
- **修正版正控确实红在指定文件**：`negctl1-snapshot-20260919T173142.txt:4-9` 打印了 `原白板/CS.md` 且计数为 1，不是单纯“diff 非空”。
- **skill 差异归属没有误记为缺陷**：断点表将其归为部署冻结（`03-breakpoints.md:10-12`），与总账裁定一致（`2026-08-28-主goal全量分goal总账-v2.md:1007`）。
- **manifest 混合方案本身披露诚实**：根件因 `G8-7` 恒红（`manifest-validator-conflict-20260919T170857.txt:4-9`）；J06 副本明确自称仅一致性副本（`b15-g8-7/journeys/J06/manifest.json:3-13`）并绿跑（`manifest-green-20260919T173050.txt:1-4`）。
- **未授权路径下仍有独立价值**：它保留了旅程判据、live skill 对照、跑前/跑后只读快照骨架、manifest 防装绿约束与部分负控；但价值限于车道侧备料，不能推出产品旅程可用。

## 读取面缺口

- 本次只允许读取两个 snapshot 的前 5 行，因此无法独立重算全量 `changed/outside`，只能核对门产物计数。
- 卡文 §二.7/§二.8 的精确命令未在指定读取面内，负控文件也未内嵌命令，所以“卡文字面判据 vs 修正判据”的差异无法完全独立复现。
