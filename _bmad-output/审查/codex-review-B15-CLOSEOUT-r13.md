只读复核绑定：`HEAD = 0d712dd460690b6930cb91488802bb8b8de7411a`，tracked 工作区干净；本地 `origin/*` 与 `backup/*` tracking refs 均同 SHA。未连数据库/网络服务，未改文件，未跑测试/校验器；以下为 git 对象、文件内容与门脚本逻辑的只读复算。

# BLOCKER

### BLOCKER-1 r12 的 J07 manifest 补记使 semantic v2.4 在最终 HEAD 上预期转红，但收口仍宣称 PASS

- **位置 / SHA**：
  - `0d712dd460690b6930cb91488802bb8b8de7411a`：`docs/release-evidence/dev-b15-p5/journeys/J07/manifest.json:319` 仅追加 `notes`；
  - P5 lane pin/tip = `7af5306b3b28764574895aa5b38d952474e01b69`，见 `_bmad-output/审查/evidence-b15-closeout/cross-lane-semantic2-v24-20260920T215132.txt:13`；
  - semantic 规则：`_bmad-output/审查/evidence-b15-closeout/cross-lane-semantic2.py:131-134`（JSON 结构必须相等）、`:190-215`（逐个比较 lane-changed 非 `_bmad-output` 文件，无例外则 `diff_n++`）、`:221-223`（`diff_n != 0` ⇒ `verdict=FAIL` / rc=1）；
  - 例外面不含 J07 manifest：`cross-lane-semantic2.py:21-28`；冻结白名单只登记 P3：`_bmad-output/审查/evidence-b15-closeout/b15-freeze-exclusions.json:4-13`；
  - 最终树仍宣称 v2.4 PASS / 仅 P3 docs-drift 被容忍：`_bmad-output/审查/evidence-b15-closeout/STATUS.md:15`、`:20`；
  - r12 只登记了 release manifest 校验器 rc=0：`_bmad-output/审查/evidence-b15-closeout/j07-manifest-validate-after-notes-20260920T232725.txt:2-6`；r12 复核的 semantic PASS 绑定的是整改前 `9d799e22`，不是 `0d712dd4`：`_bmad-output/审查/codex-review-B15-CLOSEOUT-r12.md:3`、`:17`。
- **一句复现思路**：`git diff 7af5306b3b28764574895aa5b38d952474e01b69..0d712dd4 -- docs/release-evidence/dev-b15-p5/journeys/J07/manifest.json` 非空，且差异正是 `notes` 追加；该文件在 P5 lane 的 base..lane 变更清单内，又不在 `EXCEPTIONS` 或 P3-only 白名单内。
- **静态推演结果**：按 v2.4 代码逻辑，当前最终 HEAD 会从档案中的 `checked=129 / equiv=123 / exceptions=6 / undecided_diff=0 / verdict=PASS` 变为 **`checked=129 / equiv=122 / exceptions=6 / undecided_diff=1 / verdict=FAIL`（rc=1）**。我没有执行脚本；这是由 git blob 差异与脚本分支直接推出的确定结果。
- **未被拦下的输入**：候选树单独追加 release-evidence JSON 的 `notes`，不同步 P5 lane、不登记 P5 例外；`validate_release_manifest.py` 仍可 PASS，因为 schema/artifact checksums 未变。
- **对照输入**：`9d799e22` 时 candidate 与 P5 lane 的该 manifest 相等，v2.4 档案为 PASS；r12 之后唯一进入 semantic 比较面的漂移就是这 1 个 JSON 文件。
- **负控输入**：对该 lane-changed JSON 的 `notes` 做任意一字符变异，正是 semantic v2.4 应判红的输入；当前 r12 补记本身就是实例。
- **门未覆盖的路径**：r12 整改后没有新的 semantic v2.4 输出档；现有 PASS 档绑 `9b96e5a6`，r12 复核绑 `9d799e22`，均早于最终 manifest 变更。收口也没有机器检查“非 `_bmad-output` docs 变更必须同步 lane 或登记例外”。

# HIGH

无。

# MEDIUM

无。

# LOW

### LOW-1 J07 复捕获档声称捕获 `StartedAt`，实际命令捕获的是 `CreatedAt` 加粗略 uptime

- **位置 / SHA**：`0d712dd4`；`_bmad-output/审查/evidence-b15-closeout/j07-window-open-preflight-recapture-20260920T2326.txt:15-21`；整改说明同称“docker ps 容器 StartedAt 原始输出”：`_bmad-output/审查/evidence-b15-closeout/D-15-r12-整改说明.md:6`。
- **一句复现思路**：读第 17 行命令，`docker ps --format` 使用 `{{.CreatedAt}}`，不是 `docker inspect --format '{{.State.StartedAt}}'`；档内只有 `Up 9 hours` 可近似推出启动时间。
- **未被拦下的输入**：把“创建时间 + Up 9 hours”的摘要标成精确 `StartedAt`，文档审阅者无法从档中复核精确 state start timestamp。
- **对照输入**：R-SLO 取证档使用 `docker inspect` 并落出 `started=2026-09-20T20:14:13Z`：`_bmad-output/审查/evidence-rslo/code-sha-runtime-tree-20260920T131615.txt:14`。
- **负控输入**：改写 `Up 9 hours` 或 `CreatedAt` 摘要，release manifest validator 与 semantic 门均不校验 Docker 字段名。
- **门未覆盖的路径**：J07 复捕获档无字段名/命令语义机器校验；不过 `Up 9 hours` 仍足以把本次观测启动时间置于 18:23 开窗之前，故列为 LOW 而非更高。

### LOW-2 台账 J07 行被 r12 改成 4 列，与 3 列表头不一致；同档又声称 `台账 :157` “不修改”

- **位置 / SHA**：`0d712dd4`；表头 3 列在 `_bmad-output/implementation-artifacts/goal-cards/未合卡追踪台账.md:152-153`，J07 行 4 列在 `:157`；复捕获档声明“原始权威记录 = 1e907037 message + 台账 :157（不修改）”在 `_bmad-output/审查/evidence-b15-closeout/j07-window-open-preflight-recapture-20260920T2326.txt:4`。
- **一句复现思路**：用 `|` 分列计数，`:154-156` 与 `:158` 均为 3 列，只有 `:157` 为 4 列；同时 `git diff 9d799e22..0d712dd4` 显示该行被追加证据路径和重复的“第十六批（跨日续跑）”。
- **未被拦下的输入**：Markdown 表格行可多插一个 cell 而没有任何 docs lint 报红；部分渲染器会丢弃/悬空第四列，且“:157 不修改”的审计指引与最终树事实冲突。
- **对照输入**：`git show 1e907037:_bmad-output/implementation-artifacts/goal-cards/未合卡追踪台账.md` 中的 J07 行为原 3 列口径；相邻行仍保持 3 列。
- **负控输入**：对表格逐行做列数一致性检查，`:157` 会立即 mismatch。
- **门未覆盖的路径**：semantic/G8-10/OpenAPI/unit/contract 都不检查台账 Markdown 表结构；r12 只校验 J07 release manifest。

清零：否  
B/H/M/L = 1/0/0/2
