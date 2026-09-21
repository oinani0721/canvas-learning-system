只读审计完成：未改文件、未连数据库/网络服务、未运行 pytest/pyright/openapi/schemathesis。只读复算了 Git 对象/日志/清单，并读取了 10 个 lane worktree 的本地 HEAD。你提供的 20:54 `ls-remote` transcript 未复连网；本地 `origin`/`backup` tracking refs 均为 `85a157dc50bb81d75e7b676ad464462672b002ec`。

先给 r4 五项闭合结论：

- **H-1：未闭合，且升级**——见下方 BLOCKER-1。
- **M-1：闭合**——总账 §六已改为 J07 18:23 窗口/Day-0/跨日转第十六批，contract 改为红 nodeid 集合/计数等价，warnings 577→579 属非红面（`2026-08-28-主goal全量分goal总账-v2.md:1095-1096`）。
- **M-2：闭合**——r4 prompt 与 `83a280db` 三列 push transcript 均已入库（`codex-prompt-B15-CLOSEOUT-r4.md:1-5`、`branch-push-verify-20260920T203135.txt:1-10`）。
- **L-1：仅部分闭合**——89/93 已改 90/94，但同一注释仍留下 206/117 的不可加总口径，见 LOW-1。
- **L-2：仅部分闭合**——blob 缺失路径已被 `[MISSING]` 捕捉，但 semantic gate 本身仍 fail-open，见 HIGH-1。

## BLOCKER

### B-1 G8-7 证据面在最终 push 后继续漂移，权威修正只在 P3 lane，最终主干 `85a157dc` 不含它

- **位置 / SHA**：最终主干 `85a157dc` 提交于 20:54:06；P3 lane 本地新 commit **`ec9845fabcc20174822fbe270c1802a3ea889194`** 提交于 **20:57:43**，晚于你提供的 20:54:22 最终 push 自证。该 commit message 明确写：r15 绑 `32a405a4` = `B0/H1/M1/L1`，并补入 `search-20260920T2042.json`、把 artifacts 66→67。
- **复现思路**：
  1. 读最终主干：`_bmad-output/验收单/UAT-CARD-G8-7-2026-09-20.md:82` 仍登记 **59 artifacts**；`:158-163` 仍为 ③ fail / ⑥ fail；`:176-181` 只是尾部追加 `[[Pi search note回复3]]`。
  2. 读当前 P3 lane：同 UAT `:82` 已是 **67 artifacts**，`:163` 已是 ③ pass / ⑥ pass；`manifest.json:158-159` 将 ③ 改 pass，`:652` 新增 raw `search-20260920T2042.json`，`:663-681` 仍 signoff pending / result partial 并登记“输出截图仍缺”。
  3. `git cat-file -e 85a157dc:_bmad-output/审查/evidence-g87-journey/search-20260920T2042.json` rc=128；该文件只存在于 P3 lane `ec9845fa`。
  4. semantic 复跑档 `cross-lane-semantic2-fixL2-20260920T205324.txt:10` 绑 P3 tip `32a405a4`；当前 P3 lane HEAD 已是 `ec9845fa`。该证据档不再是当前 P3 tip 快照。
- **为什么 r4-H1 未闭合**：r4-H1 的修复是把用户回复-3和 UAT 链接入最终主干，但 P3 lane 后续 r15 审查明确判定当时的“逐字要点/normalized 登记件”不足以满足卡文原始返回体要件（`codex-review-CARD-G8-7-r15.md:21-30,73-77`），随后 `ec9845fa` 才补 raw JSON。也就是说，最终主干里的回复-3只是摘要/用户观察，不是 r15 认可的完整证据件。
- **当前仍开放**：P3 lane `ec9845fa` 后仍有未跟踪 r15/r16 prompt/review；其中 `codex-review-CARD-G8-7-r16.md` 在 21:05 采样时为 0 字节，说明 G8-7 证据审计仍在活动状态。用户签字位仍全部未勾（lane UAT `:104-114,179`）。
- **未被拦下的输入**：final main push 之后，B15 lane 分支继续提交 docs-only 证据修正；semantic gate 因 `:(exclude)_bmad-output` 不看这些文件（`cross-lane-semantic2.py:99`），main final-HEAD/tracked-clean 门也不监控 lane branch advancement。
- **对照输入**：main `85a157dc` = 59 artifacts / ③ fail / ⑥ fail；P3 lane `ec9845fa` = 67 artifacts / ③ pass / ⑥ pass / raw JSON in tree。两侧权威 manifest blob 明显不同。
- **负控输入**：若把 semantic gate 增加每 lane expected tip 锁定，或把 B15 evidence inventory 覆盖 P3 lane `_bmad-output/审查/evidence-g87-journey/**`，`32a405a4 → ec9845fa` 会立即失配；当前不会。
- **门未覆盖的路径**：post-final lane branch drift、lane docs-only evidence redefinition、main tree 与 lane authoritative manifest/UAT 的证据面同步、未合并 lane audit 结果的 closeout quiescence。
- **结论**：不能在 `85a157dc` 上宣称 B15 总收口清零。需要先停止/完成 G8-7 r16，裁定 raw JSON + 截图豁免/补图口径，merge 或显式排除该 post-final lane 证据面，再重跑 semantic/final inventory 并产生新最终 SHA。

## HIGH

### H-1 semantic v2.1 仍不是 fail-closed：FAIL 也 rc=0，且 lane 文件枚举 Git 失败会被当成 0 文件 PASS

- **位置**：`_bmad-output/审查/evidence-b15-closeout/cross-lane-semantic2.py:30-31,93-99,119-121`。
- **复现思路**：
  1. 脚本末尾只 `print(verdict=...)`，全文件没有 `sys.exit` / `raise SystemExit`。因此即使打印 `verdict=FAIL(...)`，进程 exit code 仍是 0。
  2. `run()` 只返回 `subprocess.run(...).stdout`，不检查 `returncode` / stderr。若 `git diff --name-only <BASE>..HEAD` 因 BASE 无效、引用坏、pathspec 错误等失败，stdout 为空，`files=[]`，最终可得到 `checked=0 / diff=0 / missing=0 ⇒ verdict=PASS`，且 rc=0。
  3. 因此 `D-15-r4-整改说明.md:9` 把“rc=0”当作 semantic v2.1 通过证据，并不具备判别力：PASS 与 FAIL 都是 rc=0，枚举失败也可能变成 vacuous PASS。
- **当前结果影响**：本次复跑档本身不是 vacuous：`cross-lane-semantic2-fixL2-20260920T205324.txt:2-17` 有 10 个 lane、非零文件数，`:19-20` 为 `checked=129 ... missing=0 empty=0 verdict=PASS`。但这些计数需人工读文本确认，不能由 rc 门承重。
- **未被拦下的输入**：undeclared diff（打印 FAIL 但 rc=0）；坏 BASE/ref 使 lane diff 输出为空；git rev-parse 失败导致 tip 为空但循环继续。
- **对照输入**：当前日志每个 lane 均有具体 tip/files 数，且 129 个路径计数非零；这证明当前这一次不是 0 文件假绿，不证明工具 fail-closed。
- **负控输入**：应在 `diff_n/missing_n/empty_n` 非零、Git rc 非零、lane tip 与 expected SHA 不符时 `sys.exit(1)`。当前脚本不会。
- **门未覆盖的路径**：Git 子命令失败语义、per-lane expected tip pin、最低文件数断例、verdict→exit code 传播、wrapper 对 `verdict=` 行的强制解析。

## MEDIUM

无。

## LOW

### L-1 r4-L1 只修正了 90/94，源码注释仍留下不可加总的 206/117 覆盖口径

- **位置**：`backend/tests/contract/test_openapi_contract.py:42-45`。
- **复现思路**：
  - 注释现写“206 个 operation 收窄到 90；94 GET - 4 GET；被排除共 117（POST 96 + DELETE 9 + PUT 6 + PATCH 2 + GET 4）”。
  - 只读重算当前 `backend/openapi.json`：**211 operations = GET 94 / POST 100 / DELETE 9 / PUT 6 / PATCH 2**。选中面确为 90 GET；未选中面应为 **121**，其中 POST 为 100。
  - 旧 `excluded-operations.txt` 只有 117 行、POST 96，不能解释当前 OpenAPI 的 4 个新增 POST。`206 - 117 = 89` 也与同句的 90 矛盾。
- **未被拦下的输入**：后续维护者按 206/117/POST96 计算恢复范围，会漏掉 4 个 POST 的契约面归属或恢复风险。
- **对照输入**：`schemathesis-ops-90.txt` 恰 90 行且全 GET；collect manifest 为 92 tests = 90 schemathesis + 2 非 schemathesis。90/94 这半边已修正。
- **负控输入**：再新增/删除一个 POST 而不更新 206/117；没有源码注释 ↔ OpenAPI method census ↔ excluded manifest 的机器对账门会红。
- **门未覆盖的路径**：schemathesis skip 登记只核选中 90，不核“总 operation - 选中 = excluded”的完整会计恒等式。

### L-2 旧 push/tag 档的 35 tag 分解公式写错：`32 + 4 = 35`

- **位置**：`_bmad-output/审查/evidence-b15-closeout/push-and-tags-evidence-20260920T202239.txt:5`。
- **复现思路**：该行写“32 原批卡 + R-SLO-locked + G8-10 + G4-13-verdicts + G8-7-final = 35”。实际 `grep -c '^OK '` 为 35；台账口径是“31 张卡级 squash + G8-10 收口 squash = 32 卡”（`未合卡追踪台账.md:15`），再加 R-SLO-locked / G4-13-verdicts / G8-7-final 三个后续 tag 才是 35。G8-10 本身是 32 卡之一，不是第 33 个额外项。
- **未被拦下的输入**：读者按该行推导会得出 36 或误认为 G8-10 在 32 卡之外。
- **对照输入**：较新的 `push-and-tags-evidence-20260920T203021.txt:7,43` 只写“本批 tag 35”并给 `35/35 OK`，无错误分解；我另按本地 `tag^{commit}` 重算 35 条三列 SHA，全部与档内一致。
- **负控输入**：改动该分解文字或 tag 数；现有 evidence 引用只查 SHA 一致，不解析 Markdown 计数公式。
- **门未覆盖的路径**：tag 清单计数/批次卡数分解的机器一致性检查。

---

其他关键只读复算结果未发现新增问题：`HEAD=85a157dc`、tracked dirty=0；`1e907037..83a280db` 确为 16 文件全 `_bmad-output/**`；`85a157dc` 唯一非 `_bmad-output` 改动确为 contract 注释，且父子 AST 完全相等；D40 独立重算为 481 文件 = 480 `.py` + OpenAPI 时间戳，480 个 Python AST 全等；unit 33→32 的 canonical nodeid 差集仅移除 digest injective 测试；contract 两档红 nodeid 集合相同；7692 档为 107 passed；G8-10 clean rerun 的 103 行 dirty 清单和 checker digest HEAD 定义可复算；G4-13 为 75+28=103、0 pending、approved 签字在案；R-SLO lane `b0ac7192..d2db49af` 确为 14 commits。

清零：否；B/H/M/L = 1/1/0/2
