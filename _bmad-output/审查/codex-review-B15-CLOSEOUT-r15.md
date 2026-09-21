# BLOCKER

无。

只读绑定复核通过：

- 当前 `HEAD = 9229ea54f8b8455e5c1df658b06258f7ace79582`；本地 branch、`origin/*`、`backup/*` 三个本地 tracking ref 均为同一 SHA。未重新执行 `ls-remote`，活态远端对齐采用你提供的 2026-09-21 00:18:51 自证。
- tracked worktree 干净：unstaged/staged diff 均为空；`git status --porcelain` 为 102 项全 untracked，且与 G8-10 digest 档的 `dirty=102 / dirty_tracked=0 / dirty_untracked=102` 口径一致。
- `3139cef7..9229ea54` 恰为 18 文件，全部在 `_bmad-output/**`；非 `_bmad-output` diff 为 0。
- 35 个本批 tag 的 push 档逐行解析为 35/35 local=origin=backup，且本地对象全部是最终 HEAD 祖先。
- 未发现 r14 后新增的假绿、未入库主声明、越权写库/写 live vault、或最终 feature 分支 force/reset 丢提交痕迹。未连数据库或业务服务。

# HIGH

无。

关键门与收口面复核结果：

- **semantic v2.5**：当前脚本 SHA-256 复算为 `61078e6e6e80c24c0e64fb29f5bc3f8a59548d76760510617fc3cee6f48478bd`，与主跑档一致。7 个负控脚本与主脚本的 one-line diff、各自 SHA-256、`rc=1` 输出均能在最终树复算。J07 负控关闭谓词后确实从 `EXCEPTION` 变 `[DIFF]`，`verdict=FAIL`。
- 我在最终 HEAD 独立重算跨车道面：`checked=129 / equiv=122 / exceptions=7 / diff=0 / missing=0 / empty=0`。J07 与 P5 lane 的 JSON 差异只有 `notes`，且 candidate `notes` 是 lane 原文的追加，不是其它键漂移。
- **G8-10 M1**：入库 digest 档的 `6fa6f3ac...` 绑 `3139cef7`，档内已明示 digest 含 HEAD、后续 docs commit 会改变值。我在最终 `9229ea54` 只读复算得到 `source_digest=917e400a1be26df5793a551a47e597ff`，`chains=6 / obj07=5 / failures=0 / dirty_tracked=0`；checker SHA-256 也与档内 `f7c63b3c...` 一致。内容检查在最终 tip 成立。
- **unit**：基线 33 红 → 终局 32 红；canonical nodeid set-diff 为 introduced=`[]`，removed 唯一 `tests/unit/test_candidate_service.py::test_accept_candidate_already_accepted_returns_422`。
- **contract**：三档红 nodeid 集合完全相同，均为两条既有红；计数均为 `2 failed / 75 passed`，warnings 577→579 只属非红面。
- **7692**：档案覆盖四文件，`107 passed / 0 failed`；自 `fe19b5bb` 起这些 integration/regression 文件零变更。
- **openapi/pyright**：我在最终 HEAD 复算 OpenAPI `DRIFT: none (paths=199 schemas=357)`；`1e907037..9229ea54` 在 `backend/app` 与 `backend/openapi.json` 零变更，因此 post-P9 pyright `app` 0 errors 证据仍覆盖当前代码面。
- **D40**：`04eb9a9f` 为 480 `.py` + `backend/openapi.json` 时间戳；480 个 `.py` 中 479 个父子 AST 全等，唯一差异是已在档的 docstring 尾随空白。只读复跑 `ruff check --no-cache backend` 得同两条既有 F821，`format --check` 为 912 files already formatted。
- **J07**：23:26 复捕获档、`docker inspect StartedAt=2026-09-20T21:01:44Z`、:05 档、8011 GET 200、UAT 顶部/末尾勘误指针与 manifest notes 均在；最终 manifest 校验器复跑 PASS。原始 18:23 四查输出缺失仍如实登记，未被冒充。
- **G4-13**：裁定清单 103 checked = relevant 64 + ambiguous 39；金集主集 75+28、pending 0；manifest `status=approved / signed_by=Heishing`，四文件 SHA verify 复跑 rc=0。
- **schemathesis**：清单为 90 行、90 个唯一 operation、全 GET；显式 skip 口径与最终注释一致。
- G8-7 签字仍为未勾、J07 跨日部分仍转第十六批，均未被写成 pass。

# MEDIUM

无。

r14 的 M1/M2/M3 实质闭合：

- M1 由“3139 档 + 档内 HEAD 复算口径 + 本轮最终 HEAD 复算”闭合；
- M2 由 J07 内容谓词、其它键/路径 self-test、`neg-j07pred-off` 负控闭合；
- M3 的 heredoc 去缩进输入在当前实现中必然落入 `[DIFF]`，当前 `scripts/j01_e2e.sh` 双端 Git blob 同为 `16f153b5...` 且 `bash -n` rc=0，无实际漂移。

# LOW

### LOW-1 r14 宣称“docstring / freeze guard 同步 v2.5”，但最终树仍残留 v2.4 口径与旧 `.sh` 归一化描述；且 `.sh` 的 `bash -n` 分支实际不是通过判据

- **位置 / SHA**：`9229ea54f8b8455e5c1df658b06258f7ace79582`
  - `_bmad-output/审查/evidence-b15-closeout/D-15-r14-整改说明.md:8` 声称 “docstring 与 freeze guard 口径同步 v2.5”；
  - `_bmad-output/审查/evidence-b15-closeout/STATUS.md:21` 仍写 “semantic v2.4 以 40-hex 全 SHA pin 监控”；
  - `_bmad-output/审查/evidence-b15-closeout/b15-freeze-exclusions.json:15` 的 `guard` 仍以 “semantic v2.4” 开头；
  - `_bmad-output/审查/evidence-b15-closeout/cross-lane-semantic2.py:9` 仍描述旧口径 “`bash -n` + 去注释/空行后的行序列相等”，而不是 v2.5 字节相等；
  - `_bmad-output/审查/evidence-b15-closeout/cross-lane-semantic2.py:163-190` 的实现与该描述不一致：`a == b` 在 `:164-165` 先短路为 `BYTES`，所以相同字节的 `.sh` 不会执行 `bash -n`；若 `.sh` 两端字节不同，`:188-190` 即使双端 `bash -n` 通过，也因 `a == b` 为 false 而恒返回 `None`。因此没有任何输入会以 `"SH"` 通过，`bash -n` 实际不参与 PASS 判定。
- **一句复现思路**：直接 `grep -n 'semantic v2\.4' STATUS.md b15-freeze-exclusions.json` 可见残留；再对照 semantic 脚本 `:9` 与 `:163-190`，可见文档描述的 shell 比较机制与实际控制流不一致。
- **未被拦下的输入**：
  1. candidate 与 lane 同时携带同一个语法损坏的 `.sh` 时，`:164-165` 会先以 `BYTES` 通过，不跑 `bash -n`；
  2. 两端 `.sh` 字节不同但语法均合法时，实际总是 `[DIFF]`，并不是文档所称“语法 OK 后按归一化/字节口径可判等”；
  3. 读者按 STATUS/freeze guard 选择或复核 v2.4 口径时，会发现版本标签与最终 v2.5 证据链不一致。
- **对照输入**：当前 `scripts/j01_e2e.sh` candidate 与 P3 lane Git blob 同为 `16f153b5019978327bcb89ef585cfad836fe68af`，大小 102473 bytes，最终树 `bash -n scripts/j01_e2e.sh` rc=0；因此当前没有实际 shell 漂移或运行语法损坏。
- **负控输入**：v2.5 的 `sh-heredoc-dedent` 已能证明“去缩进的不同字节必须不等价”，该 M3 风险本身闭合；但缺少两个控制件——①“双端相同但语法损坏的 `.sh`”是否必须拒绝，②registry/STATUS/docstring 的版本号是否必须等于脚本输出 `version=v2.5`。
- **门未覆盖的路径**：`script_sha256` 只绑定脚本自身，没有机器校验 STATUS、freeze registry、脚本 docstring 与输出 version 的一致性；也没有 lint/负控检查 `.sh` comparator 的文档化算法与实际控制流一致。实际门比旧文档更严格，未造成本轮假绿，但按“LOW 也必须为 0”的用户口径不能清零。

清零：否；B/H/M/L = 0/0/0/1
