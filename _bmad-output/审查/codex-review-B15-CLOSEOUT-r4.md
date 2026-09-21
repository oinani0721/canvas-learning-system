# D-15 r4 只读终审（绑定 `83a280dbaebb8f8d70eced748cf356950b89dd2d`）

**执行边界**：未连接数据库/网络服务，未运行 pytest / pyright / openapi drift / schemathesis，未改文件。只做读文件、只读 Git、静态解析/比对。

**Now / prohibited / unlock when**

- **Now**：本地 `HEAD`、`origin/worktree-feature-obsidian-hybrid-dev`、`backup/worktree-feature-obsidian-hybrid-dev` 均为 `83a280dbaebb8f8d70eced748cf356950b89dd2d`；活态 `ls-remote` 结论采信你提供的 20:31 transcript，本轮未自行连网。但审计期间工作区在 20:42 出现新的 G8-7 证据面改动：1 个 tracked M + 1 个 B15 相关 untracked 文件。
- **Prohibited**：不应宣称 B15 复核清零；不应删除或代用户裁定新 G8-7 回复；不应 force-push / 改写已推历史；不应为“清零”顺手跑服务或扩大代码面。
- **Unlock when**：先裁定/登记这份 post-final G8-7 证据并入库推送，或明确移出 B15 收口面；同步总账、补齐 r4 prompt/最终 push 证据链；再走下一轮只读复核。

## 已独立核验通过的关键声称

- `1e907037..83a280db` = 16 个文件，全部 `_bmad-output/**`，非 `_bmad-output` 计数 0；最终 docs-only 声称成立。
- D40 `04eb9a9f` = 481 文件：480 `.py` + `backend/openapi.json`；OpenAPI diff 仅 `x-generated-at` 时间戳。480 个 Python 文件在归一化 docstring 尾随空白后 AST 全等，format-only 声称成立。
- 7692 三个集成修复 `2bdbc685` / `d0e42bc4` / `4f6d17ca` 均只改 `backend/tests/integration/test_cypher_contract_gate.py`，无产品代码顺手改动。
- G8-10 `0400d848` 直接面 381 文件全 `_bmad-output/**`；与 lane tip `6346facb` 的 381 个对应 blob 全一致；lane diff 非 `_bmad-output` 0。按包含首 commit `4120e0b6`、剔除已合 `c53069d3` 口径为 24 commits，与声称一致。
- R-SLO `69d26ed5`：`slo-manifest@2026-09-20-r2` / `status: locked` / 用户口令与逐项裁定在案；lane `b0ac7192..d2db49af` = 14 commits。
- G4-13：`vault_gold_set.yaml` 75 条 + `memory_gold_set.yaml` 28 条 = 103；`gold_set_manifest.yaml` `main_set_queries: 103`、`adjudication.status: approved`、`signed_by/signed_at` 在案。
- unit：基线 33 红 vs post-P9 32 红；nodeid 差集仅移除 `test_vault_install_manifest.py::test_digest_is_injective_over_adversarial_leaves`，0 引入。
- contract：两份原始档红 nodeid 集合相同，均为 2 failed / 75 passed；差别在 warning 数等非红 nodeid 面，“红 nodeid 集合/计数等价”口径成立。
- 7692：post-P9 原始档 107 passed / 0 failed。
- semantic v2 日志：checked 129 / equiv 123 / exceptions 6 / diff 0 / PASS；我另按 10 个 lane tip 重算 129 个路径，missing=0、empty blob=0。
- push/tag 档：35/35 tag 三列 SHA 一致，mismatch=0；本地 tag 解析与档内 local SHA 全一致。

---

## BLOCKER

无。最终 commit 本身未失稳：审计期间两次采样 HEAD 均保持 `83a280db`，本地 tracking refs 也均为 `83a280db`。

---

## HIGH

### H-1 终审期间出现 post-final G8-7 证据面漂移：tracked UAT 被改 + 新回复未入库

- **位置**：`_bmad-output/验收单/UAT-CARD-G8-7-2026-09-20.md:181` 新增 `[[Pi search note回复3]]`；untracked `_bmad-output/Pi search note回复3.md:1-73`。两者 mtime 均为 2026-09-20 20:42，晚于最终 commit `83a280db` 的 20:31:19。
- **复现思路**：`git status --porcelain=v1` 显示 ` M _bmad-output/验收单/UAT-CARD-G8-7-2026-09-20.md` 与 `?? _bmad-output/Pi search note回复3.md`；`git diff -- <UAT>` 显示仅在末尾追加链接；`git ls-files --error-unmatch '_bmad-output/Pi search note回复3.md'` 失败。
- **影响**：新回复内容声称“UAT ③ 变体查询通过”，并给出同会话/同索引/同 marker 的对照；这会改变 G8-7 未完成项的证据状态，但它不在 `83a280db` tree 中，也未推送。最终树仍只能证明“签字未勾、非 pass”，不能包含这份新证据。
- **未被拦下的输入**：final commit 后继续手工追加 B15/G8-7 tracked 证据与 untracked 用户回复；现有 final-HEAD 绑定只看 commit SHA，不拦截工作区 post-final 漂移。
- **对照输入**：`83a280db` 中 UAT 末行为待办清单，无 line 181 链接；`git cat-file -e 83a280db:_bmad-output/Pi search note回复3.md` 失败。
- **负控输入**：把新回复第 1 行“通过”改成失败或删除该文件；`83a280db` 的 B15 证据与 gates 均不会变红。
- **门未覆盖的路径**：post-final B15 evidence inventory / tracked-clean quiescence / “final commit 后不得新增 B15 承重证据”检查。

---

## MEDIUM

### M-1 总账 §六未同步 r3 后的 J07 与 contract 更正口径

- **位置**：`_bmad-output/implementation-artifacts/goal-cards/2026-08-28-主goal全量分goal总账-v2.md:1095-1096`。
- **复现思路**：
  - 该总账仍写 “G6-13 J07 窗口（显式 SKIP）”，但权威台账 `_bmad-output/implementation-artifacts/goal-cards/未合卡追踪台账.md:157` 已更正为“J07 窗口 2026-09-20 18:23 开启、Day 0 进行中、跨日转第十六批”。
  - 总账仍写 contract “与基线逐字同”；实际两档是红 nodeid 集合/计数等价，非全文逐字相同：baseline `contract-3files-20260920T151657.txt:2031-2034` 为 577 warnings，post-P9 `contract-3files-FINALPOSTP9-20260920T192431.txt:2038-2041` 为 579 warnings，且 rootdir 不同。
- **未被拦下的输入**：未来读者只读总账 §六，会误判 J07 仍为 SKIP，或误以为 contract 输出全文逐字相同。
- **对照输入**：`未合卡追踪台账.md:157-164` 与 `STATUS.md:10-18` 已是 corrected 口径。
- **负控输入**：修改 contract 的 warning 数、路径或非红输出；总账“逐字同”句不变，不会被现有 gate 拦下。
- **门未覆盖的路径**：总账、台账、STATUS、汇报之间的跨文档一致性机器门。

### M-2 STATUS 引用的 r4 prompt 不存在于最终树，最终 tip push transcript 也只在树外

- **位置**：`_bmad-output/审查/evidence-b15-closeout/STATUS.md:24` 指向 `_bmad-output/审查/prompts/codex-prompt-B15-CLOSEOUT-r4.md`，并称“绑 SHA 以 prompt 首部为准”；但 `git cat-file -e 83a280db:_bmad-output/审查/prompts/codex-prompt-B15-CLOSEOUT-r4.md` rc=128，当前文件也不存在。
- **关联证据**：`push-and-tags-evidence-20260920T203021.txt:2-7` 只绑 `5a2abccc`；该档 line 3 明说最终 tip 自身对齐 transcript 见 r4 prompt。你提供的 chat transcript 证明 20:31:35 时 origin/backup 均为 `83a280db`，但该 transcript 未随最终树入库。
- **复现思路**：在 `83a280db` tree 中查找 r4 prompt 与完整 `83a280db` 分支 push transcript；二者均不存在。当前本地 tracking refs 可复核，但树内证据链断裂。
- **未被拦下的输入**：STATUS 可以引用不存在的 prompt 路径，并把最终 push 自证留在 chat/transcript 中；现有 docs diff 门只检查路径是否 `_bmad-output/**`，不检查引用目标存在。
- **对照输入**：35 tag 档完整入库，且本地 tag SHA 与档内三列一致。
- **负控输入**：删除或改动树外 r4 prompt / push transcript；`83a280db` 内引用与证据不会变化。
- **门未覆盖的路径**：Markdown 引用目标存在性、最终 HEAD push transcript 入库清单、证据文件 inventory 对账。

---

## LOW

### L-1 代码内 schemathesis 覆盖注释仍写 89，与最终 90-operation 口径不一致

- **位置**：`backend/tests/contract/test_openapi_contract.py:42-45` 写“收窄到 89 条 / 93 GET - 4 GET”；最终 `_bmad-output/审查/evidence-b15-closeout/schemathesis-ops-90.txt:1-90` 为 90 行，勘误块 `schemathesis-nonhealth-v-20260920T194546.txt:1358-1363` 也明确实数 90。
- **复现思路**：`wc -l schemathesis-ops-90.txt` = 90；collect manifest 为 92 tests = 90 schemathesis + 2 非 schemathesis；再读源码注释仍是 89。
- **未被拦下的输入**：后续维护者按源码注释计算 excluded/selected 面，会少算 1 个 operation。
- **对照输入**：STATUS、台账、汇报和勘误块均已经按 90 登记。
- **负控输入**：再新增或删除一个 GET operation 而不改注释；无注释/manifest 对账门会红。
- **门未覆盖的路径**：源码注释与 collect manifest 的机器一致性检查。

### L-2 semantic v2 的 `blob()` 不检查 `git show` rc，可把“路径缺失”与“空 blob”都当成 `b''` 等价

- **位置**：`_bmad-output/审查/evidence-b15-closeout/cross-lane-semantic2.py:30-44`；`run()` / `blob()` 只返回 stdout，不检查 returncode/stderr，`a == b` 直接判 `BYTES`。
- **复现思路**：构造 lane-added empty file 而候选树缺失该路径；两侧 `git show` 都得到空 stdout（一侧是空 blob，一侧是 error），脚本计为 `BYTES` equivalence。
- **当前结果影响**：我按 10 个 lane tip 独立重算 129 个路径，missing=0、empty blob=0，因此本轮 `123 equiv / 6 exceptions / 0 diff` 未被该盲区改变。
- **未被拦下的输入**：空文件缺失、双侧 `git show` 同因路径/引用错误失败。
- **对照输入**：当前 129 个路径在 candidate 与 lane tip 均存在且非空。
- **负控输入**：对每个路径先执行 `git cat-file -e <rev>:<path>` 并断言 rc=0，再取 blob；当前脚本不会红。
- **门未覆盖的路径**：Git 子命令失败语义与路径存在性检查。

---

清零：否；B/H/M/L = 0/1/2/2


