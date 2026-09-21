## 审计绑定与通过面

- 绑定复核：WT `worktree-feature-obsidian-hybrid-dev`，最终 HEAD = `51acf6cdcf090e87305e3172649477908b1162cb`；`origin` 与 `backup` 同名远端分支也指向该 SHA。tracked 工作区为净；当前 untracked 计数实测 98。
- 只读限制：未连接数据库/网络服务，未运行 pytest/pyright/schemathesis，未改文件；以下测试与类型门结论来自已入库日志 + 只读 git/blob 静态复算。
- 复算通过的面：
  - `f26e6a85` 只改协议文件，G1-1/G1-3/§2.4.2/§3/§6 条款均在最终协议中。
  - `69d26ed5` 的 `slo-manifest.yaml:5-7` 为 `locked/r2`，用户口令与逐项裁定记录在 `decision` 段；本地 tag `merged-squash/card/p10-docs-R-SLO-locked` 指向 `69d26ed5`。
  - `2bdbc685`、`d0e42bc4`、`4f6d17ca` 均只改 `backend/tests/integration/test_cypher_contract_gate.py`；测试口径与 `fallback_sync_service.py:619-646` 的 group_id > vault_id > env > quarantine 契约一致。
  - `0400d848` 的 381 个路径全部在 `_bmad-output/` 下，product diff = 0；r21 存档自报 `B/H/M/L = 0/0/0/0`。
  - D40 的 480 个 Python 文件中，479 个 parent/child AST 完全相等；唯一 AST 差异仅为 `test_security_p0_vulnerabilities.py` 三个 docstring 的行尾空白，未发现行为语义变化。
  - openapi 最终静态计数复算为 paths=199、schemas=357。
  - unit 基线/终局 pytest header 前 10 行逐字相同；33→32 的失败 nodeid 差集为：引入 `[]`，修复 `tests/unit/test_vault_install_manifest.py::test_digest_is_injective_over_adversarial_leaves`。
  - 台账 §二第 286–317 行恰为 32 张卡；32 个卡级 squash SHA 均存在且是最终 HEAD 祖先。
  - B15 窗口 reflog 只见正常 commit 与 fast-forward，无 reset/checkout/stash 破坏性移动；历史 stash 均为旧批次/旧分支，未发现绑定到本窗口的证据。

---

## BLOCKER

无。

---

## HIGH

### H-1 终局门证据没有绑定最终 HEAD：`51acf6cd` 在所有终跑门之后又改了 backend fixture

- 证据：`_bmad-output/审查/evidence-b15-closeout/FINAL-gates-20260920T173010.txt:1-5` 明确绑定 `46984d80`；G8-10 FINAL 同样绑定 `46984d80`；但 `51acf6cd` 相对 `46984d80` 的非 `_bmad-output` diff 非空，唯一文件是 `backend/tests/fixtures/regression_baselines/board_manifest_last_run.json:2-6` 的 `ts` 与 `generation` 变化。
- 复现思路：`git -c core.quotepath=false diff --name-only 46984d80..51acf6cd -- . ':(exclude)_bmad-output'` 返回该 JSON；而协议最终绑定判据要求该 diff 为空（`.claude/rules/card-batch-protocol.md:10`）。
- 判定：FAIL。
- 未被拦下的输入：终跑门之后把任一 backend/tests fixture 恢复为用户侧旧值并合入收尾 commit。
- 对照输入：若 `51acf6cd` 相对 `46984d80` 只有 `_bmad-output` 变化，则绑定成立。
- 负控输入：把该 JSON 的 `generation` 再改一字符；当前证据链不会变红。
- 门未覆盖的路径：最终 HEAD 的 `board_manifest_last_run.json` 及其回归脚本消费面没有 469 之后的重跑证明。

### H-2 7692 四文件门“107 passed”没有入库执行证据；唯一原始四文件日志是 105 passed

- 证据：入库原始日志 `_bmad-output/审查/evidence-b15-closeout/e2e-7692-4files-20260920T152307.txt:10,68` 为 `collected 105` / `105 passed`，且时间早于 `4f6d17ca`；`4f6d17ca` commit body、`STATUS.md:6,41,44`、台账 `未合卡追踪台账.md:319`、总账 `2026-08-28-主goal全量分goal总账-v2.md:1096`、汇报 `_bmad-output/第十五批-完成的卡-汇报.md:14` 均宣称 107。
- 复现思路：在 evidence-b15-closeout 中搜索 `107 passed|105 passed`，只会找到声明层的 107 与原始日志层的 105；没有 post-`4f6d17ca` 或 post-D40 的 107 汇总存档。
- 判定：FAIL（不是说他定不可能——`4f6d17ca` 恰新增两条用例，105→107 合理；而是承重结果没有入库证据）。
- 未被拦下的输入：四文件命令少收集/少执行两条新增矩阵用例，仍可由 commit message 与台账自报 107。
- 对照输入：应有与 `4f6d17ca` 或之后代码树同绑的原始日志，显示 collected=107、passed=107、failed=0。
- 负控输入：从四文件选择中排除 `test_replay_entry_group_id_beats_vault_id` 与 `test_replay_entry_env_vault_branch`，当前证据无法发现。
- 门未覆盖的路径：post-`4f6d17ca`、post-D40 的 7692 四文件实际执行。

### H-3 跨车道等价终档机器 verdict 是 `FAIL(7)`，却被人工注释改读为通过，且注释与同档数据矛盾

- 证据：`cross-lane-FINAL-20260920T173804.txt:4-29` 显示 p1/p2 多文件 differs/MISSING，`:43-63` 显示 p9 四文件 MISSING，`:63` 为 `verdict=FAIL(7)`；`cross-lane-FINAL-annotated.txt:67-76` 又总结“本批 32 卡代码面等价”，并声称 p1–p8/p10 为 0 differs，与同档 p1/p2 differs=8 不一致。
- 复现思路：直接读同一目录的 FINAL 与 annotated 两档，再对照 pre-D40 `cross-lane-20260920T132702.txt:4-31`；pre-D40 只有 p1/p2 三个多写者 UNION-OK，p10 当时仍有 1 个 README MISSING。
- 判定：PARTIAL/FAIL——D40 后语义等价可由 AST 缓解，但作为“跨车道文件等价门”没有机器 PASS 证据。
- 未被拦下的输入：D40 之后某车道新增语义被格式化掩盖，或 p10 在 R-SLO 合入后未复跑即推定等价。
- 对照输入：应有 post-R-SLO、pre-D40 或 post-D40 的完整机器运行输出 `verdict=PASS`；或入库逐文件 AST/语义等价证明。
- 负控输入：把任一 p1/p2 多写者文件的一行语义删除后重跑脚本；当前 `FAIL(7)` 状态无法区分已知格式差异与新语义丢失。
- 门未覆盖的路径：R-SLO 合入后的 pre-D40 p10 复跑，以及 D40 后 p1/p2 MISSING 的完整机械归因。

---

## MEDIUM

### M-1 总账声称 tag/推送证据在 evidence-b15-closeout，但该目录没有 B15 push/tag 证据

- 证据：`2026-08-28-主goal全量分goal总账-v2.md:1093` 写“tag/推送见 `_bmad-output/审查/evidence-b15-closeout/`”；该目录无任何 push/tag 文件。`STATUS.md:16,54` 也只是计划“推送 origin+backup+tags”，没有完成输出。最终 commit 里改动的是旧 B14 `evidence-b14/tags-push-20260911T103527.txt`。
- 复现思路：`find _bmad-output/审查/evidence-b15-closeout -type f | grep -Ei 'push|tag'` 为空。
- 判定：PARTIAL。
- 未被拦下的输入：任一 tag 推送失败、被跳过或非逐个推送，总账指针仍指向空目录。
- 对照输入：本地 remote branch refs 已证明 feature 分支推到 `51acf6cd`，但 tag 远端状态不能由分支引用证明。
- 负控输入：删除一个远端 tag 或让一次 tag push 失败；入库证据不会出现红字。
- 门未覆盖的路径：origin/backup 逐个 tag push 的命令输出、非强推约束与远端验证。

### M-2 89 个 schemathesis operation 全量面显式 skip；部分运行已显示 health operation 失败，不能按“全门已跑”收口

- 证据：`STATUS.md:7,45` 明示 `test_openapi_contract.py` 89 操作未跑全量；`backend/tests/contract/test_openapi_contract.py:42-48,95-99` 定义 89 个 GET/HEAD operation；`contract-4files-dbup-20260920T150040.txt:14-22` 在前多个 health operation 上已出现 FAILED 后中断。
- 复现思路：3-file contract gate 排除了 `test_openapi_contract.py`，而 4-file 尝试没有完整汇总行，因此 89 operation 面无 PASS 证据。
- 判定：PARTIAL。
- 未被拦下的输入：任一未跑 GET operation 的 response schema 回归。
- 对照输入：3-file gate 的 2 个既有红与 75 passed 只覆盖 snapshot/node-id/health-contract 的既定面。
- 负控输入：篡改一个未被 3-file 覆盖的 GET response schema；当前收口门不会红。
- 门未覆盖的路径：89 个 operation 的完整 schemathesis 执行与汇总。

### M-3 最终 HEAD 后出现 B15 相关 untracked 产物，其中 D-15 r1 是 0 字节，当前没有入库的非空 D-15 终审绑定 `51acf6cd`

- 证据：`_bmad-output/审查/codex-review-B15-CLOSEOUT-r1.md` 存在但字节数为 0；`_bmad-output/审查/2026-08-30-主goal全量状态账.md:161-171` 是最终 commit 后更新的 untracked B15 状态账，并重复 107 声明。当前 untracked=98，而 `51acf6cd` commit body 自称 96 项长期 untracked。
- 复现思路：`git status --porcelain=v1 | awk '$1=="??"{n++} END{print n}'` 得 98；`wc -c _bmad-output/审查/codex-review-B15-CLOSEOUT-r1.md` 得 0。
- 判定：PARTIAL。
- 未被拦下的输入：失败/空审稿留在工作区但不入库，最终审查链可被忽略。
- 对照输入：协议 `.claude/rules/card-batch-protocol.md:12` 要求末轮绑最终代码树，`:14` 明确未入库复核不作依据。
- 负控输入：0 字节文件无法提供模型、绑定 SHA、B/H/M/L 任何自证。
- 门未覆盖的路径：非空、可验证、绑定 `51acf6cd` 的 D-15 审查存档。

### M-4 G8-7 用户签字位仍为 pending，但汇报层写“B15 总收口完成”，超出证据允许的结论

- 证据：`_bmad-output/验收单/UAT-CARD-G8-7-2026-09-20.md:92-102` 六个体验 checkbox 与旅程签字均未勾，且写明“未勾选 ⇒ manifest.signoff.status 保持 pending”；`未合卡追踪台账.md:24` 与总账 `:1095` 也登记未闭合；但 `_bmad-output/第十五批-完成的卡-汇报.md:14` 同时写“B15 总收口完成”。
- 复现思路：打开 UAT 签字区可见 `[ ]`，而最终汇报行使用完成语。
- 判定：PARTIAL。
- 未被拦下的输入：用户未完成/未认可旅程时，合并完成语被读成验收完成。
- 对照输入：R-SLO 有用户口令与逐项裁定，因此可写 locked；G8-7 只有“走查已执行、签字未勾”。
- 负控输入：manifest signoff 应保持 pending，不应自动 approved。
- 门未覆盖的路径：用户 felt-sense 六项与最终旅程认可。

---

## LOW

### L-1 D40 不是严格 format-only：480 个 Python 之外还改了 `backend/openapi.json` 的生成时间

- 证据：`04eb9a9f` 实际 481 文件 = 480 `.py` + 1 JSON；`backend/openapi.json:15852` 的 `x-generated-at` 从旧值变为 `2026-09-21T00:18:19.848733+00:00`，这是 metadata 变更而非 ruff format。
- 复现思路：`git diff --unified=0 04eb9a9f^ 04eb9a9f -- backend/openapi.json` 只有一对 `x-generated-at` 行。
- 判定：PARTIAL。
- 未被拦下的输入：把生成时间或其它 openapi metadata 混入 style commit。
- 对照输入：480 个 Python 文件的 AST 复算基本支持“无行为语义变化”。
- 负控输入：strict format-only 门应拒绝任何非 ruff hunk。
- 门未覆盖的路径：D40 commit message 对第 481 个 JSON 文件没有说明。

### L-2 openapi/pyright FINAL gate 只有摘要，无命令、`test -x` 与 rc 自证

- 证据：`FINAL-gates-20260920T173010.txt:1-5` 仅 5 行摘要；`pyright-app-20260920T131059.txt` 从输出正文开始，没有绝对路径命令、`test -x`、rc；协议 `.claude/rules/card-batch-protocol.md:49,54` 要求 stdout/stderr+末行 rc，pyright 需绝对路径与可执行自证。
- 复现思路：读两份证据文件首尾，找不到命令行与 rc 行。
- 判定：PARTIAL。
- 未被拦下的输入：错误二进制、错误工作目录或命令失败后被手工摘要成通过。
- 对照输入：静态 openapi 计数 199/357 可复算；pyright 汇总本身为 0 errors。
- 负控输入：把 pyright 路径换成不存在但 shell rc 误为 0 的情况，协议已将其列为假绿教训。
- 门未覆盖的路径：FINAL gates 的原始命令 provenance 与退出码。

### L-3 跨车道等价脚本的 UNION 判据过弱：过滤短行、strip 后集合匹配，不校验顺序/删除/重复

- 证据：`cross-lane-equivalence.py:37-42` 先把 candidate 行变成 strip 后 set，再丢弃 `len < 12` 的 lane-added 行，只要剩余行文本存在即 UNION-OK。
- 复现思路：构造 lane-added `return False` / `break` / `continue` 等短行，或删除既有行而不新增长行；脚本仍可给 UNION-OK。
- 判定：PARTIAL。当前 p1/p2 三个多写者复算中，除空白行外未发现非空短行丢失，故暂列 LOW。
- 未被拦下的输入：短控制流语句丢失、语句顺序改变、重复次数改变、既有行被删。
- 对照输入：当前三个文件的长行并集在 pre-D40 候选中存在。
- 负控输入：移除 `len >= 12` 过滤，并加 AST/语句序列比较。
- 门未覆盖的路径：短行、顺序、删除与重复语义。

### L-4 INTEGFIX r3 残余 LOW-1：quarantine“全域零写”仍未完整断言

- 证据：`codex-review-INTEGFIX-7692-replay-r3.md:95-106,156` 明确 random-id Episode、User-only、边-only、既有 Node/Canvas 属性改写仍可全绿，最终 `B/H/M/L = 0/0/0/3`。
- 复现思路：让拒写路径在解析失败前写入未被断言的 Episode/User/边或改写既有属性；现有 Concept/record_id Episode 探针不红。
- 判定：PARTIAL。
- 未被拦下的输入：无 `record_id` 的 random-id Episode、User-only、关系-only、属性更新。
- 对照输入：生产 `_resolve_entry_source()` 得 None 后当前在图写前返回 False。
- 负控输入：对测试前缀的 Episode/User/关系类型做前后总量 delta。
- 门未覆盖的路径：全域图写零增量。

### L-5 INTEGFIX r3 残余 LOW-2：来源优先级矩阵缺 vault-vs-env 与三源冲突

- 证据：`codex-review-INTEGFIX-7692-replay-r3.md:108-135,156`。
- 复现思路：把生产 resolver 改为 `group_id > env > vault_id`；现有 group/vault、env-only、vault-only 用例仍可通过，`vault_id > env` 回归漏拦。
- 判定：PARTIAL。
- 未被拦下的输入：`{vault_id:B, env:C}` 应落 B、`{group:A, vault:B, env:C}` 应落 A。
- 对照输入：当前实现顺序为 group → vault → env → quarantine。
- 负控输入：新增 vault-vs-env 与三源同冲突矩阵。
- 门未覆盖的路径：完整优先级排列。

### L-6 INTEGFIX r3 残余 LOW-3：固定 `g21gate` 前缀与共享 7692 不隔离并发重复运行

- 证据：`codex-review-INTEGFIX-7692-replay-r3.md:137-155,156`。
- 复现思路：同一 7692 上并发跑两个本文件进程，B 的全局 cleanup 可删除 A 正在断言/计数的前缀数据，造成假红或漏清理。
- 判定：PARTIAL。
- 未被拦下的输入：多 pytest 进程/多 CI job 复用同一 7692；外部进程在同前缀上增删 Node/Canvas。
- 对照输入：顺序运行时当前 function/module cleanup 有效。
- 负控输入：引入一次性 run-id 前缀并绑定 cleanup、查询与 delta。
- 门未覆盖的路径：并发隔离与 run-id 级数据所有权。

---

清零：否；B/H/M/L = 0/3/4/6


