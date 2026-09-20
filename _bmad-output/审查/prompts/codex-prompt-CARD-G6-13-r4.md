# CARD-G6-13 · J07 次日复习旅程（开发门）独立审查请求（round-4）

## ① 背景与最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p5-review`
分支 `card/p5-review`（P5 车道末张）。基线 `PREV = f0cacff6`（P5-B 末 commit）。
**审查绑定 `2dc505e7`**（= commit D）。commit 序列：A=`00553b4e` → B=`28bd74a4` → 外部 docs-only
`1c355c3a`（G6-9c-R3 补审 jev 分诊归档，一个 `_bmad-output` json，如实披露）→ C=`a3103a49` →
**D=`2dc505e7`（r3 整改+存档+回填）** → E（r4 存档+终回填，仅 `_bmad-output`）。
批次 `[BATCH-2026-09-18-第十五批 / CARD-G6-13]`。**零代码面改动**（territory 只
`docs/release-evidence/dev-b15-p5/journeys/J07/**` + `_bmad-output`）。

本卡性质：零代码 · 验收/证据卡；用户旅程未授权整段 SKIP（`not_run`）；`E2 / partial / pending`。

**请读这些，不要扩大读取面：**

```
git --no-pager diff --no-color f0cacff6 2dc505e7 -- . ':(exclude)_bmad-output'   （J07 净 diff）
docs/release-evidence/dev-b15-p5/journeys/J07/manifest.json        （全文; 16 artifacts; candidate 钉 f0cacff6）
docs/release-evidence/dev-b15-p5/journeys/J07/ 其余 17 件
docs/release-evidence/README.md:38-79 与 :100-124
backend/scripts/validate_release_manifest.py:263-300 与 :430-504
_bmad-output/验收单/UAT-CARD-G6-13-J07-2026-09-20.md                （全文; r3 后已改）
_bmad-output/审查/evidence-g613/build-j07-manifest.py               （r3 整改后; 七前缀/演变/佐证条）
_bmad-output/审查/evidence-g613/candidate-zero-diff-*.txt           （candidate 绑定佐证）
_bmad-output/审查/evidence-g613/negctl-2-final-*.txt                （终版负控）
_bmad-output/审查/evidence-g613/validate-j07-r3fix-*.txt / validate-all-r3fix-*.txt
_bmad-output/审查/codex-review-CARD-G6-13-r{1,2,3}.md               （前三轮原档; ①-bis 是索引）
```

## ①-bis round-3 处置 —— 请**独立核对每一条是否真的收口**（勿采信本节说法）

round-3（绑 `a3103a49`）判 **B0 / H2 / M1 / L2**，原档 `codex-review-CARD-G6-13-r3.md`。

| 级 | r3 原文要点 | 处置（请核） |
|---|---|---|
| HIGH | UAT §七.12 称外部 json "未提交"（实为 `1c355c3a` 已提交） | §七.12 改为「外部 session 已提交、非本卡面、零代码面、绑定/门不受影响」；(o) 行同步 |
| HIGH | `candidate.sha` 随重建漂移（f0→A→B→1c），单一"执行期 checkout"陈述不成立 | **钉回执行期 checkout `f0cacff6`**（00:54 PDT 起手）；`unproven_fields` 逐阶段记 SHA 演变（含外部 `1c355c3a` 一瞬）；`notes` + `execution.commands` 新增**零 diff 佐证条**（`backend/ frontend/ scripts/` f0..C 逐文件零 diff；输出 `candidate-zero-diff-*.txt`）。请以该命令为**对照输入**复跑 |
| MEDIUM | (o) 行漏记 commit C 对 J07 的 4 件修订 | (o) 行明写：C 含 `copy-fidelity*.txt` / `manifest.json` / `three-face-api.json` |
| LOW | builder 拒收面有限（`/tmp/`、`/var/`、`/Volumes/` 未覆盖） | 拒收面扩至**七类前缀**（含上述三项），note 措辞同步 |
| LOW | (e) 行"整目录 grep = 0"口径不实（manifest 自身含前缀字面量） | 改为：artifact 面（排除 manifest）= 0；manifest 16 条 `redaction_note` 为说明文字 ⇒ 整目录非 0（口径注明） |

## ② 作者自述（请独立核对，勿直接采信）

1. manifest 15 键齐、**16 件 artifact** 全过默认产物真验（单份 rc=0 零 `[S`/`[A`；`--all` rc=0 2 份）；
   candidate.sha = `f0cacff6…`（执行期 checkout；40 位；`unproven_fields` 记演变与替身性质）。
2. `E2/partial/pending` 从低取；`reconstructed` + `unproven_fields`（candidate 条已按 r3 改写）；
   skip 3 条与 not_run 联动。
3. J07 自含复跑 `three_face_equal=True`；同源耦合如实声明；五桶偏差声明在场。
4. artifact 面（排除 manifest）七前缀 grep = 0；builder 七前缀拒收为机械门。
5. 负控 `negctl-2-final`（对终版 manifest）：单行 `[A2]` + validator rc=1 + `cmp: identical`。
6. 零 diff 佐证：`git --no-pager diff --name-only f0cacff6 2dc505e7 -- backend/ frontend/ scripts/` 为空。

## ③ 按重要性排序的问题（逐项给结论）

- **⓪ r3 的 H1/H2/M1/L1/L2 逐条是否收口**（尤其 candidate 的"钉定 + 演变登记 + 零 diff 佐证"
  三件套是否够支撑"执行期 checkout = f0cacff6"这一主张；还有没有表述仍会让人误读）。
- **① 绑定链全览核对**：A/B/C/D + 外部 1c 的时间线、每个 manifest 版本的 candidate、UAT 各处
  的"绑"字面是否全部自洽（可 `git log --format='%h %cI %s' F0..HEAD` 对照）。
- **② 证据件最终一致性**：16 件 sha/bytes 独立复算；`copy-fidelity-rsync.txt` 是否含任何绝对路径；
  `md-final.md` 全量版的敏感面（人工可判）。
- **③ 负控终版证据链**（`negctl-2-final`）是否自含可复核（快照哈希 / 变异 / rc / cmp / status）。
- **④ 仍有未被拦下的输入 / 门未覆盖的路径** 类问题吗（builder 七前缀之外、grep 口径之外）。
- **⑤ 其它真问题**按 ④ 格式照报。

## ④ 输出格式

- 发现清单，每条：`[BLOCKER|HIGH|MEDIUM|LOW] <file>:<line> — <一句话说明>；<一句复跑思路>`；
- 复跑思路的措辞必须用：**负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径**；
- 末尾必须有一行自检汇总：`BLOCKER=<n> HIGH=<n> MEDIUM=<n> LOW=<n>`（某级为 0 也写）；
- 用中文输出；结论先行（一两句裁决），再列发现。

## ⑤ 边界

- **只读**：不得修改任何文件（`--sandbox read-only`）；不连库；不 push。
- **不评**（范围外）：P5-A/P5-B 面；R-J07 RC 复跑；G8-6 dogfood；D-37 三口径；
  `inbox_preview.py:430` 产品口径本身（T3-B 待裁）；外部 commit `1c355c3a` 的内容本身。
- 本轮审 `2dc505e7` 所钉树态；后续 commit E 只含 `_bmad-output` 增量（r4 存档 + 终回填）。
