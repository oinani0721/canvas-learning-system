## 绑定与只读复核摘要

- 本地 `HEAD` = `refs/heads/worktree-feature-obsidian-hybrid-dev` = local `origin/*` tracking = local `backup/*` tracking = **`b55744ba6cc1263746fce5d4a561adfa62cdd2cc`**；与提示中的活态 ls-remote 自证一致。本轮未连数据库/网络服务、未改文件、未推送。
- tracked working tree 干净；当前 102 个 untracked 中未发现 B15/D-15/G8-7/G4-13/R-SLO/J07/closeout 关键字命中的未入库收口产物。
- 静态/日志复算通过面：OpenAPI 当前 JSON = paths 199 / schemas 357 / operations 211，其中筛选面实数 90；unit 基线 33 红 → 终局 32 红，introduced=`[]`，removed 唯一 = `test_candidate_service.py::test_accept_candidate_already_accepted_returns_422`；7692 四文件日志 = 107 passed；contract 3-file 三个阶段红 nodeid 集合同为 2 条既有红；`1e907037..a6303136` 非 `_bmad-output` 仅 contract 注释且 AST 相等，此后到 `b55744ba` 均 docs-only。
- 我在最终 HEAD 只读复跑 G8-10 checker：`chains=6 obj07=5 failures=0`，fresh digest = `024fe59eb52f9e96e22b7add1ec5b5a0`，`head=b55744ba...`，`dirty_tracked=0`。
- r9 的 L-1/L-2 已实质闭合：r8 汇报行现为 22:15早于引入 commit 22:16:17；r8 勘误清单已补 r5。**但 r9-M-1 未闭合，且整改声称与 diff 不一致。**

## BLOCKER

无。

## HIGH

### HIGH-1 r9-M-1 是假整改：commit 与整改说明宣称「STATUS 剩余块已整块改写为终态」，最终 HEAD 中原矛盾块原样保留

- **位置 / SHA**：`f3518c40266cbdd443b94ce1f4d3821ca2cc9299`；`_bmad-output/审查/evidence-b15-closeout/D-15-r9-整改说明.md:5`；最终 `_bmad-output/审查/evidence-b15-closeout/STATUS.md:36-40`；对照 `_bmad-output/implementation-artifacts/goal-cards/未合卡追踪台账.md:156-158`、`_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal总账-v2.md:1095`。
- **复现思路**：`git diff c11487c8..f3518c40 -- STATUS.md` 显示 r9 对 STATUS 只改历史阶段标题/说明，并没有改写「剩余」块。最终 HEAD 仍写着：G4-13/J07「无口令 ⇒ not_run + SKIP」、3 处 feature 删除待处置、ff-only restore 待办；这与 G4-13 已 103/103 approved、J07 18:23 已开窗、主干早已越过 `f16c867a` 到 `b55744ba` 的 Git/台账事实冲突。整改说明第 5 行却宣称已整块改写为 5 条终态。
- **未被拦下的输入**：信任 r9 commit message / 整改说明 / STATUS「ff 后步骤已全部执行」的读者，会认为 M-1 已修；实际官方 STATUS 仍把已裁定项和已完成 ff 前置呈现为未闭合。
- **对照输入**：台账第 156-158 行分别给出 G8-7 非 pass、J07 已开窗转批、G4-13 approved；总账第 1095 行同口径；本地/远端 tracking refs 已在 `b55744ba`。
- **负控输入**：`git show --stat f3518c40` 只有 STATUS 3 行变更；`grep -nE 'G4-13|J07|ff-only|restore' STATUS.md` 直接命中旧矛盾块。无需跑服务。
- **门未覆盖的路径**：OpenAPI/unit/contract/semantic/G8-10/G4-13 manifest 均不校验「整改说明声称的文档编辑是否真实落在 commit diff 中」，也不校验 STATUS 剩余块与权威台账/Git ref 的交叉一致性。

## MEDIUM

### MEDIUM-1 D40 的 `LEFTHOOK_EXCLUDE=python-lint` 缺少协议要求的被跳过 hook 原始输出与“非本卡改动行”入库证明

- **位置 / SHA**：`04eb9a9f44ec22e64286966dbe688d42da984337`；`.claude/rules/card-batch-protocol.md:65-67`；`_bmad-output/审查/evidence-b15-closeout/d40-format-20260920T171657.txt:1-8`。
- **复现思路**：`git show -s 04eb9a9f` 自述因两处既有 F821 使用 `LEFTHOOK_EXCLUDE=python-lint`，但收口证据档只包含 `ruff format` / `ruff format --check`，没有 `ruff check` 的原始失败输出，也没有两处 F821 不在 D40 语义改动行的可审计对照。协议第 65 行要求凡使用 `LEFTHOOK_EXCLUDE`，验收单必须贴被跳过 hook 原始输出和归因证明。
- **未被拦下的输入**：一个 480 文件的 format commit 可以绕过 lint hook 后，仅凭事后 format-only 证据宣称 hook 阻力已归因；真实新增 lint 错误不会被该证据面排除。
- **对照输入**：我独立比较 D40 父子 Python AST，480 个 `.py` 中 479 个 AST 相等，唯一差异是既登记的 docstring 行尾空白；因此未发现实际语义走私，但这是独立补算，不是协议要求的原始 hook 证据。
- **负控输入**：在 `04eb9a9f` 树内检索两处精确 F821 报错原文 / `ruff check` 输出，`evidence-b15-closeout` 与验收单无对应原始档；`d40-format-*.txt:1-8` 只有 format 命令。
- **门未覆盖的路径**：pyright、unit、7692、contract 均不重建 lefthook `python-lint` 的合规证据链，也不检查 D40 commit 使用 hook exclusion 时是否满足协议存档条款。

## LOW

### LOW-1 r10 声称同类时序排查已完成，但汇报首条 09-20 18:02 行仍晚于其引入 commit 17:52:12

- **位置 / SHA**：`_bmad-output/第十五批-完成的卡-汇报.md:14`；引入 commit `51acf6cdcf090e87305e3172649477908b1162cb`；对照最终修正 commit `b55744ba6cc1263746fce5d4a561adfa62cdd2cc`。
- **复现思路**：`git blame 51acf6cd -- ...汇报.md` 显示该 18:02 行由 `51acf6cd` 引入，而该 commit author/committer time 均为 `2026-09-20T17:52:12-07:00`；最终 `b55744ba` 只修正 20:45/21:35/21:56 三行，未修这条更早的同类负时序。
- **未被拦下的输入**：信任汇报时间列会得到“18:02 的收口事件在 17:52 已入库”的不可能时序，也会误以为 r10 前置已完成全表 chronology audit。
- **对照输入**：第 15-21 行修正后均满足行时间 ≤ 引入 commit 时间；第 14 行是现存反例。
- **负控输入**：`git blame -L 14,14 b55744ba -- ...汇报.md` 加 `git show -s --format='%aI %cI' 51acf6cd` 即可复现，无需网络。
- **门未覆盖的路径**：D-15 文档门仍没有机械校验“每行事件时间 ≤ 首次引入该行的 commit 时间”。

清零：否；B/H/M/L = 0/1/1/1


