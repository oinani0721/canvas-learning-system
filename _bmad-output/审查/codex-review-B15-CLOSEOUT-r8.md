## r8 只读终审绑定与复算摘要

- **最终绑定成立**：当前 `HEAD = ae467faec12b84eff612eddf2de8ffed0fcc4a89`；本地、`origin/worktree-feature-obsidian-hybrid-dev`、`backup/worktree-feature-obsidian-hybrid-dev` 三个 ref 均为同一完整 SHA，与你提供的 21:53:20 活态 ls-remote 一致。本轮未自行连网。
- **最终档 docs-only 成立**：`ae467fae^..ae467fae` 恰 16 文件，全部在 `_bmad-output/**`；非 `_bmad-output` diff 为 0。tracked dirty = 0，untracked = 102，无 tracked 工作区漂移。
- **B15 主链形态**：`59e1f494..ae467fae` 共 66 个 first-parent commit、0 merge；台账 §二第 291–322 行的 32 张卡逐一存在且均为 `ae467fae` 祖先。协议回写、R-SLO、三笔 7692 集成修复、G8-10 squash/re-anchor、D40、P9 G4-13、r1–r7 整改链均可按 SHA 解引用。
- **r7-M1 闭合成立**：`cross-lane-semantic2.py:35-46` 的 10 个 pin 均为 40-hex；`:171-187` 使用 `tip_full != pin` 全 SHA 比较，非 40-hex/非 hex pin 在 `:176-177` 红。shortpin 与 prefixcollision 负控均 rc=1；6 个变异脚本与主脚本各自恰一行差异，SHA256 与负控全文档一致；主脚本 SHA256 `81a34da2…` 亦一致。`--self-test` 本轮复跑 PASS/rc=0。
- **semantic v2.4 终 HEAD 独立复算成立**：我不执行会写 temporary file 的主脚本完整跑，而在最终 HEAD 与十个 lane 的 Git blob 上按同口径重算，结果 `checked=129 equiv=123 exceptions=6 diff=0 missing=0 empty=0`；`9b96e5a6..ae467fae` 排除 `_bmad-output` 后 diff 为空，因此 v24 档的父 HEAD 执行结果可外推到最终代码/产品面。
- **P3 冻结排除成立**：`32a405a4..1726b695` 与 `34c29691..1726b695` 的非 `_bmad-output` diff 均为空；registry guard 已是 v2.4 口径（`b15-freeze-exclusions.json:15`）。
- **代码/文档分离成立**：`1e907037..ae467fae` 非 `_bmad-output` 仅 `backend/tests/contract/test_openapi_contract.py:42-49` 注释勘误，父/当前 AST 全等；D40 为 480 `.py` + OpenAPI timestamp，`ruff format --check --no-cache backend` 本轮复跑 `912 files already formatted` / rc=0。
- **门证据复算**：OpenAPI 本轮只读复跑 `DRIFT: none (paths=199 schemas=357)` / rc=0；pyright 日志 `0 errors, 83 warnings`；unit 最终日志 `32 failed / 6262 passed`，contract 最终日志 `2 failed / 75 passed` 且三份红 nodeid 集合一致；7692 日志 `107 passed`；schemathesis 实数 90 unique operations，档内明确“显式 skip、不称全量已跑”。
- **G8-10 final HEAD 复跑成立**：本轮在 `ae467fae` 以 actual digest `b9dbc25aa4733c7694d05bed8975c52f` 复跑，`chains=6 obj07=5 failures=0 dirty_tracked=0 rc=0`。r7 档的 `ef13b8ed…` 绑定的是当时 `9b96e5a6`，最终 HEAD 需要如上重算，结果仍绿。
- **P9 G4-13 核心事实成立**：主金集 75+28=103、无 pending，manifest `status=approved / signed_by=Heishing`；`gold_set_manifest_tool.py verify` 本轮 rc=0；裁定清单 103 个 gsid / 103 个 checked；r26 终审档记录 B/H/M/L=0/0/0/0。
- **破坏性痕迹**：近段 reflog 未见 force/reset 丢提交类操作；仅 `b31361b1 -> 1e907037` 的已登记 amend，以及一次移动到当前同 commit 的 no-op reset。35 个本批 tag 的本地对象与 push 档逐项一致。

边界：本轮没有连接数据库、没有启动/调用 7692 等服务；unit/pyright/7692/contract 以原始日志 + 代码面不变性复核。OpenAPI 只读复算时 LiteLLM 输出过“远端 cost map DNS 失败、使用本地 fallback”警告；受沙箱网络限制未建立外部连接。

## BLOCKER

无。

## HIGH

无。

## MEDIUM

无。

## LOW

### L-1 P9 G4-13 主 UAT 的“终态字段”仍停留在裁定前 pending 状态，与最终 approved manifest 相冲突

- **位置 / SHA**：`ae467fae` 树内 `_bmad-output/验收单/UAT-CARD-G4-13-2026-09-19.md:11-19` 与 `:950-984`；对照最终事实 `backend/tests/regression/gold_set_manifest.yaml:83-91`、`_bmad-output/审查/evidence-g413/r26-final-audit-20260920T183708.txt:3-13`。实际裁定/签字由 `89be3d0e8a577db7bd94c729df05e120b08663b4` 引入。
- **复现思路**：直接读同一最终树：主 UAT 顶部写“用户裁定未开窗口”“`user_verdict` 全部 pending”，末段也写“103 条仍 pending、manifest pending”；但最终 manifest 是 `main_set_queries: 103`、`status: approved`、`signed_by: Heishing`，且本轮 `verify` rc=0。
- **未被拦下的输入**：只读主 UAT 顶部/末段的读者会把 G4-13 用户裁定误读为仍未发生；主 UAT 终态字段没有 “superseded by r26/裁定清单” 的机器化指针。
- **对照输入**：台账、STATUS、汇报、裁定清单、金集 YAML 与 manifest 彼此一致，均为 103/103 + approved；因此这是主 UAT 文档滞后，不是产品/数据面假绿。
- **负控输入**：把主 UAT 顶部改为“r26 后 approved / 旧段落为裁定前历史”应消除冲突；当前无该勘误或 supersession 标记。
- **门未覆盖的路径**：P9 终审与台账门校验 manifest/hash/103 条，不校验主 UAT 顶部终态字段与 manifest 状态一致。

### L-2 r7 复核存档对 unit “只减”差集的 nodeid 陈述错误：实际移除的是 candidate_service 旧 flaky，而非 digest 用例

- **位置 / SHA**：`ae467fae` 树内 `_bmad-output/审查/codex-review-B15-CLOSEOUT-r7.md:14`；协议基线 `_bmad-output/审查/evidence-b15/unit-red-baseline-9c4e7e82.txt:2-7`；最终日志 `_bmad-output/审查/evidence-b15-closeout/unit-FINALPOSTP9-20260920T192431.txt:48,1006`；中间 33 红档 `_bmad-output/审查/evidence-b15-closeout/unit-20260920T132728.txt:1000,1008`。
- **复现思路**：把基线与最终日志的 `FAILED ` 行 canonical 化（去掉 ` - ` 后的错误尾巴）后求差集：基线 33、最终 32、added=0、removed 仅 `tests/unit/test_candidate_service.py::test_accept_candidate_already_accepted_returns_422`；r7 存档却写成“仅移除 test_digest_is_injective_over_adversarial_leaves”。digest 只出现在 15:16 的中间 33 红档，后续 `8a651d2a`/终局修复后已不在最终红集。
- **未被拦下的输入**：信任 r7 复核存档的“具体移除 nodeid”会得到错误归因；不过 33→32、added=0 的“只减”总结仍正确。
- **对照输入**：`unit-FINALPOSTP9` 的最终 32 条与 `unit-final-nodeids.txt` 逐项一致；二者都不含 candidate_service，也不含 digest。
- **负控输入**：机械执行上述 canonical set-diff 即可复现本 LOW；无需跑测试。
- **门未覆盖的路径**：现有门只比较红数/红集合与基线，不把 D-15 复核存档中的 prose nodeid 归因再对账。

清零：否；B/H/M/L = 0/0/0/2


