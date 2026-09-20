# CARD-G6-13 · J07 次日复习旅程（开发门）独立审查请求（round-2）

## ① 背景与最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p5-review`
分支 `card/p5-review`（P5 车道末张）。基线 `PREV = f0cacff6`（P5-B 末 commit）。
**审查绑定 `28bd74a4`**（= commit B）。commit 序列：A=`00553b4e`（J07 证据 + manifest + 验收单）
→ **B=`28bd74a4`（r1 整改 + 负控两轮 + r1 存档）** → C（r2 存档 + 验收单终回填，仅 `_bmad-output`）。
批次 `[BATCH-2026-09-18-第十五批 / CARD-G6-13]`。本卡**零代码面改动**（territory 只
`docs/release-evidence/dev-b15-p5/journeys/J07/**` + `_bmad-output`）。

本卡性质（零代码 · 验收/证据卡）：fixture 半边（五面契约 ×4 PASS / 三面对账 / 校验器 / 套件）已执行；
用户旅程（跨日 UI 步骤）因**未授权 + 开窗前置未满足**整段 SKIP，全部 `not_run`；
`evidence_level=E2` / `result=partial` / `signoff=pending`。

**请读这些，不要扩大读取面：**

```
git --no-pager diff --no-color f0cacff6 28bd74a4 -- . ':(exclude)_bmad-output'
    （本卡代码面净 diff = 新增 J07 目录 17 文件: 15 artifact + manifest + 无其他）
docs/release-evidence/dev-b15-p5/journeys/J07/manifest.json         （全文, 核心被审对象; 15 artifacts）
docs/release-evidence/dev-b15-p5/journeys/J07/ 其余 16 件            （含 md-final.md 全量版 / copy-fidelity / three-face-compare-j07.txt）
docs/release-evidence/README.md:38-79 与 :100-124
backend/scripts/validate_release_manifest.py:263-300 与 :430-504
backend/scripts/g68_five_view_contract.py:1-30 与 :103-119
backend/app/api/v1/endpoints/review_overview.py:360-376 与 :1127-1150
_bmad-output/验收单/UAT-CARD-G6-13-J07-2026-09-20.md                 （全文; r1 后已改）
_bmad-output/审查/evidence-g613/three-face-compare.py               （r1 整改后全文）
_bmad-output/审查/evidence-g613/build-j07-manifest.py               （r1 整改后全文; 含逐件自证）
_bmad-output/审查/evidence-g613/three-face-compare-j07.txt          （J07 自含复跑输出）
_bmad-output/审查/evidence-g613/negctl-1-20260920T015822.txt / negctl-2-20260920T015822.txt  （重跑轮）
_bmad-output/审查/evidence-g613/negctl-1-20260920T013002.txt / negctl-2-20260920T013002.txt  （首轮）
_bmad-output/审查/evidence-g613/validate-j07-postfix-*.txt / validate-all-postfix-*.txt
_bmad-output/审查/evidence-g613/copy-fidelity-digest-v1-broken-note.txt   （整树摘要弃用记录）
_bmad-output/审查/codex-review-CARD-G6-13-r1.md                     （r1 原档; ①-bis 是索引）
_bmad-output/审查/prompts/codex-prompt-CARD-G6-13-r1.md             （r1 prompt）
_bmad-output/审查/2026-08-20-Canvas-Learning-System-生产力化长期Goal计划书.md:596-612
_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal总账-v2.md（:899/:965）
/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/feature-obsidian-hybrid-dev/_bmad-output/审查/2026-09-15-第十四批复核裁定与待裁决登记.md:143-144
```

行号为送审时实测；漂移以符号名为准。

## ①-bis round-1 处置 —— 请**独立核对每一条是否真的收口**（勿采信本节说法）

round-1（绑 `00553b4e`）判 **BLOCKER 0 / HIGH 3 / MEDIUM 3 / LOW 2**，存档
`_bmad-output/审查/codex-review-CARD-G6-13-r1.md`。处置如下：

| 级 | r1 原文要点 | 处置（请核） |
|---|---|---|
| HIGH-1 | `three-face-compare.py` 空集判据只看 picker 面 ⇒ 单面空误报"作废 rc=2" | 改为**三面全空才 rc=2**；单面空 = rc=1 不等（见脚本 `作废条件` 段）。请用「picker 空、API/MD 非空」型对照输入复核逻辑；再用正常输入复核仍 rc=0 |
| HIGH-2 | J07 内 `md-final.md` 被裁到标题+板序 ⇒ J07 无法自含复跑（md=0、FALSE） | `md-final.md` 换**全量脱敏版**；新增 `three-face-compare-j07.txt` = **仅用 J07 三件**（picker-final/three-face-api/md-final）复跑输出（three_face_equal=True）。请仅读 J07 目录自行复跑该命令以证 |
| HIGH-3 | 验收单把 Codex 与 commit B 后干净树**预收口**为 ✅ | UAT 已改：r1=3H 如实、(n) 标 🔁 待 r2、(o) 注明 C 回填、干净以末 commit 为准；§八 补注含整改表 |
| MEDIUM-1 | 4-B 过度强调三面独立性 | 4-B 已改写为「**同一份清单在三个出口呈现一致**」+ 显式同源声明（picker/API 读同一投影、MD 同链渲染） |
| MEDIUM-2 | copy-fidelity 只核 `.canvas-config.yaml` 单件 | 已强化：rsync 命令 + rc + 副本文件数 + `rsync -ainc` **全树对拍** + 差异成因（恰 outputs/ 两件投影 = 副本上 `picker --write` 设计内重算；其余逐字节同）。⚠️ 首版"整树摘要"（`shasum|xargs`）因空格/CJK 文件名被打散已**弃用**，弃用记录见 `copy-fidelity-digest-v1-broken-note.txt` |
| MEDIUM-3 | 构建器把目录内文件无条件 `redacted=true`、无自证 | 已加**逐件自证**：空件 / 含 `/Users/` 即 `SystemExit` 拒绝收编（见 builder 顶部循环） |
| LOW-1 | UAT 写 13 件 vs 实测 14 | 重建后为 **15 件**（新增 `three-face-compare-j07.txt`；md 换全量）；UAT 已更正 |
| LOW-2 | `_tmp_cmp.py` 误入 commit A | 已移出（commit B 记删除） |

负控**重跑轮**（整改后）说明：因 rebuild 后工作树 ≠ HEAD，重跑改用**工作树快照还原**（`cp` 快照 /
`cp` 回；与 P5-A §五.20 的"`git show HEAD` 在卡内多轮整改时冲掉当轮修复"同款）。首轮（commit A，
`git show HEAD` 还原）与重跑轮红点一致：`ranked 板序不等` / `[A2] artifact checksum 不符`。

## ② 作者自述（请独立核对，勿直接采信）

1. manifest 15 键齐、**15 件 artifact** 全部过默认产物真验（单份 rc=0 零 `[S`/`[A`；`--all` rc=0
   2 份）；构建器现对每件自证（空件/`/Users/` 拒收），本次 15 件全部通过该自证。
2. `evidence_level=E2` 从低取未 overclaim；`provenance.mode=reconstructed` + `unproven_fields` 6 条；
   `signoff=pending`；`skips_or_mocks.declared=true`（3 条）与 not_run 联动。
3. J07 **自含复跑**已成立：`three-face-compare-j07.txt` 仅用 J07 内三件；集合 6=6=6、ranked
   3 前缀 + api/md 4 全长、`three_face_equal=True`。
4. 同源耦合（picker 与 API 读同一投影）在 `known_limitations` 与 UAT 4-B 均如实声明。
5. 五桶偏差声明仍在；J07 全目录 `grep '/Users/'`=0；车道零写 live（rsync 只读 + copy-fidelity 全树对照）。
6. 负控两轮红点不变、shasum 前后逐字同；`git status -- docs/release-evidence` 在本轮送审前
   应为空（仅 `_bmad-output` 有本卡增量）。

## ③ 按重要性排序的问题（逐项给结论）

- **⓪ r1 三条 HIGH 是否真的收口**：①对照输入「picker 空 + API/MD 非空」是否确得 rc=1（而非 2）；
  ②仅凭 J07 目录能否复跑出 `three_face_equal=True`（请亲自跑 `three-face-compare.py` on J07 only）；
  ③UAT 是否还有任何"预收口"残留（搜 ✅ 与待判项）。
- **① 整改有无引入新问题**：md 换全量后是否含任何敏感内容（人工笔记正文/绝对路径）？`md-final.md`
   与 J07 其余件的 redaction 声明（一律 `redacted=true` + 统一说明）现在是否有**不实**之处？
- **② manifest 与 R1 摘要的边界**：`J07-6=pass` 的范围（副本三面、同源）是否够窄不误导？
  `candidate.sha`（车道树替身）+ `dirty=false` 口径在 `notes`/`unproven_fields` 是否够强？
- **③ 负控重跑的还原基准**（快照 vs `git show HEAD`）是否被说清楚、有据可查？
- **④ 验收单 4-B**：改写后是否仍零技术词、felt-sense 是否仍为"待确认"而未冒充已发生？
- **⑤ 其它真问题**按 ④ 格式照报。

## ④ 输出格式

- 发现清单，每条：`[BLOCKER|HIGH|MEDIUM|LOW] <file>:<line> — <一句话说明>；<一句复跑思路>`；
- 复跑思路的措辞必须用：**负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**；
- 末尾必须有一行自检汇总：`BLOCKER=<n> HIGH=<n> MEDIUM=<n> LOW=<n>`（某级为 0 也写）；
- 用中文输出；结论先行（一两句裁决），再列发现。

## ⑤ 边界

- **只读**：不得修改任何文件（`--sandbox read-only`）；不连库；不 push。
- **不评**（范围外）：P5-A/P5-B 面；R-J07 的 RC 复跑与 `--require-complete`；G8-6 dogfood；
  D-37 三个产品口径；`inbox_preview.py:430` 产品口径本身（T3-B 待裁）。
- 本轮审 `28bd74a4` 所钉树态；后续 commit C 只含 `_bmad-output` 增量（r2 存档 + 验收单回填）。
