# CARD-G6-13 · J07 次日复习旅程（开发门）独立审查请求（round-3）

## ① 背景与最小读取面

仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-p5-review`
分支 `card/p5-review`（P5 车道末张）。基线 `PREV = f0cacff6`（P5-B 末 commit）。
**审查绑定 `a3103a49`**（= commit C）。commit 序列：A=`00553b4e`（J07 证据+manifest+验收单）
→ B=`28bd74a4`（r1 整改+负控+存档）→ 【外部 session 的 docs-only commit `1c355c3a`
（G6-9c-R3 补审 jev 分诊归档，仅 `_bmad-output` 一个 json；非本卡面，如实披露）】→
**C=`a3103a49`（r2 整改+存档+回填）** → D（r3 存档+终回填，仅 `_bmad-output`）。
批次 `[BATCH-2026-09-18-第十五批 / CARD-G6-13]`。本卡**零代码面改动**（territory 只
`docs/release-evidence/dev-b15-p5/journeys/J07/**` + `_bmad-output`）。

本卡性质：零代码 · 验收/证据卡；用户旅程因未授权整段 SKIP（`not_run`）、`E2 / partial / pending`。

**请读这些，不要扩大读取面：**

```
git --no-pager diff --no-color f0cacff6 a3103a49 -- . ':(exclude)_bmad-output'   （J07 净 diff）
docs/release-evidence/dev-b15-p5/journeys/J07/manifest.json        （全文; 16 artifacts）
docs/release-evidence/dev-b15-p5/journeys/J07/ 其余 17 件           （含 copy-fidelity-rsync.txt / three-face-compare-j07.txt）
docs/release-evidence/README.md:38-79 与 :100-124
backend/scripts/validate_release_manifest.py:263-300 与 :430-504
backend/scripts/g68_five_view_contract.py:1-30 与 :103-119
_bmad-output/验收单/UAT-CARD-G6-13-J07-2026-09-20.md                （全文; r2 后已改）
_bmad-output/审查/evidence-g613/three-face-compare.py / build-j07-manifest.py  （r2 整改后全文）
_bmad-output/审查/evidence-g613/negctl-1-20260920T021408.txt / negctl-2-20260920T021408.txt / negctl-2-redo-20260920T021432.txt
_bmad-output/审查/evidence-g613/validate-j07-final-*.txt / validate-all-final-*.txt / validate-all-full-*.txt（时序错留档）
_bmad-output/审查/evidence-g613/copy-fidelity-digest-v1-broken-note.txt
_bmad-output/审查/codex-review-CARD-G6-13-r1.md / -r2.md            （前两轮原档; ①-bis 是索引）
_bmad-output/审查/prompts/codex-prompt-CARD-G6-13-r1.md / -r2.md
```

## ①-bis round-2 处置 —— 请**独立核对每一条是否真的收口**（勿采信本节说法）

round-2（绑 `28bd74a4`）判 **B0 / H1 / M4 / L1**，原档 `codex-review-CARD-G6-13-r2.md`。

| 级 | r2 原文要点 | 处置（请核） |
|---|---|---|
| HIGH | UAT 头部 / §一 把 r1 误绑到 B/最终 HEAD（实为绑 A） | 已改：header 与 §一#6 = 「r1 绑 A(`00553b4e`) → r2 绑 B(`28bd74a4`) → r3 绑 C(`a3103a49`)」链；§三附(n)/§四#14 同步。请以 r1/r2 原档与 prompt 的绑定行为**对照输入**核 |
| MEDIUM | md `redaction_note` 与实物不符（"另裁至标题+板序行"） | 全量版 + note 同步改写（"机械核查前缀清单 + 人工检视无正文 + 全量版"，见 builder 常量） |
| MEDIUM | 构建器只拒 `/Users/`（其余路径前缀为**未被拦下的输入**） | 拒收面扩至 `/Users/`、`/private/`、`/home/`、`/opt/homebrew/`；`three-face-api.json` 的 `/private<tmp>` 残留已清（现 J07 全目录 `/Users/`、`/private`、`/home/` 计 0）。请以含 `/private/...` 的**对照输入**验 builder 拒收 |
| MEDIUM | copy-fidelity 未附完整命令/stdout/rc | 新增 `copy-fidelity-rsync.txt`（完整命令 + 逐行 stdout + `rc=0`；`-8` 保 UTF-8 原名）；`copy-fidelity.txt` 引用之 |
| MEDIUM | negctl 重跑轮缺快照/还原证据 | `negctl-1/2-(021408)` 加强 + `negctl-2-redo-(021432)`（rc 修正版）：快照命令+快照哈希、变异前后**完整 status**、恢复 `cmp: identical`、validator rc=**1** 正确捕获。⚠️ 复现：021408 版的 rc 行曾误取 `tail` rc（0），redo 修正。请以快照文件为**对照输入**逐件 cmp |
| LOW | postfix `--all` 存档被 tail 截 | 全量重取 `validate-all-final-*`（J07/J08 两行 + rc 全在场，rc=0） |

**另如实登记两件**：① 整改期一次「产物先改、manifest 后重建」的时序错被校验器 `[A2]/[A3]`
**当场抓住**（`validate-all-full-20260920T021408.txt` 留档；重建后 `validate-{j07,all}-final-*` 双绿）——
这是产物真验在工作的正面证据；② commit 序列里夹了一个**外部 session 的 docs-only commit**
`1c355c3a`（仅一个 `_bmad-output` json：G6-9c-R3 补审 jev 分诊归档），非本卡产物、不影响本卡面，
如实披露。

## ② 作者自述（请独立核对，勿直接采信）

1. manifest 15 键齐、**16 件 artifact** 全部过默认产物真验（单份 rc=0 零 `[S`/`[A`；`--all` rc=0
   2 份）；构建器逐件自证（空件 / 四类绝对路径前缀即拒），本次 16 件全过。
2. `E2/partial/pending` 从低取未 overclaim；`reconstructed` + `unproven_fields` 6 条；skip 3 条联动。
3. J07 自含复跑成立：`three-face-compare-j07.txt`（仅 J07 三件）= `three_face_equal=True`。
4. 同源耦合（picker=API 投影、MD 同链）在 known_limitations 与 UAT 4-B 均如实声明。
5. 五桶偏差声明仍在；J07 脱敏门（`/Users/`、`/private`、`/home/`）= 0；车道零写 live。
6. 负控三轮红点不变（`ranked 板序不等` / `[A2]`），恢复 `cmp: identical`。
7. 本轮回填只动 `_bmad-output`（UAT/存档）；J07 面在 commit C 已定稿。

## ③ 按重要性排序的问题（逐项给结论）

- **⓪ r2 的 H1 + M4 + L1 是否真的收口**：①UAT 全部绑定链是否自洽（搜 "绑" 字面与 §八）；②use
  含 `/private/` 对照输入验 builder；③negctl-redo 的 rc/快照链是否足以独立复核。
- **① 时序错留档是否如实**：`validate-all-full-*`（失败）与 `validate-{j07,all}-final-*`（通过）是否
  构成「先改产物→后重建」教训的完整证据链；这类"错误留档"有没有被误读为最终态？
- **② 16 件 artifact 与 manifest 的一致性**（sha/bytes 独立复算；`copy-fidelity-rsync.txt` 的
  `-8` 输出是否含任何绝对路径/敏感名）。
- **③ 外部 commit `1c355c3a` 的披露**是否足够（读者能否理解它不属本卡且不破坏绑定）。
- **④ 是否仍有 r1/r2 未收口的残留**（对照两轮原档逐条过；含 UAT §五/§六/§七 的措辞）。
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
- 本轮审 `a3103a49` 所钉树态；后续 commit D 只含 `_bmad-output` 增量（r3 存档 + 终回填）。
