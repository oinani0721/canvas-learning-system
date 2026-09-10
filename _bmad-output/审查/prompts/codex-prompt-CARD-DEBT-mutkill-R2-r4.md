# 独立复核请求 — CARD-DEBT-mutkill-R2（变异 harness 的击杀身份判据）

## 一 背景与最小读取面

仓库根：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-u8-mutgates`
被审提交范围：HEAD `01ac27d0`（round-4；基线 = U8-A 末 commit `3f073a1a`）。工作树干净（`git status --porcelain` 空）。

这张卡改的是**四套变异自检 harness 的判据层**。它们的作用是回答「我们那些测试门，到底守不守得住它声称的性质」——做法是把生产代码退回旧的缺陷形态（一条「变异」），再看指定的那道门会不会变红。判据不硬的话，「已验证」全是自证。

请**只**读下面这些，不要扩大读取面：

1. 本次改动的全量 diff：
   `git diff 3f073a1a 01ac27d0 -- backend/scripts/mutation_kill_identity.py backend/scripts/g32b_mutation_gates.py backend/scripts/g32cb_mutation_gates.py backend/scripts/g32ccr1_negative_controls.py backend/scripts/g33_mutation_gates.py`
2. HEAD 上 `backend/scripts/mutation_kill_identity.py` **全文**（共用判据，全部新逻辑都在这里）。
3. 四套 harness 的**判定块**与**信号块**：
   - `backend/scripts/g32b_mutation_gates.py`：`run_gate` / `is_killed` / `observed_loc` / `_check_expect_loc` / `_ACTIVE_SNAPSHOT` 与 `_GUARD` 附近 / `main()` 的变异循环与汇总段
   - `backend/scripts/g32cb_mutation_gates.py`：`_run_gate` / `_restore_active` / `_GUARD` / 变异循环里 `kill_identity(...)` 那一段 / 汇总段
   - `backend/scripts/g32ccr1_negative_controls.py`：同上对应位置
   - `backend/scripts/g33_mutation_gates.py`：`_run_gate` / `restore_all` / `_guard` / 变异循环里 `kill_identity(...)` 那一段 / 汇总段
4. 负控与证据（**取每个前缀下时间戳最新的 `*-v2-*` / 末次存档**；早于代码定稿的旧存档已作废）：
   `_bmad-output/审查/evidence-mutkill-r2/` 下的 `negctl-n1n2-v2-*.txt`、`negctl-signal-v2-*.txt`、
   `negctl-thirdparty-v2-*.txt`、`pyeof-negctl-v2-*.txt`、`premise-screen-v2-*.txt`、
   `run-g32b-*.txt` / `run-g32cb-*.txt` / `run-g32ccr1-*.txt` / `run-g33-*.txt`（**最后一组**，时间戳最大者）、
   `six-verdicts-before-after-*.txt`、`finalize-*.txt`（最后一组）
   以及负控脚本本体 `negctl_n1n2.py`、`negctl_signal.py`、`negctl_thirdparty.py`、`pyeof_negctl.py`、
   `premise_anchor_screen.py`、`fill_expect_loc.py`、`make_disposition_table.py`
5. 39 条处置表与四套分档对照表：验收单 `_bmad-output/验收单/UAT-CARD-DEBT-mutkill-R2-2026-09-08.md` 第 6 节
   （最终数字：36 条改绑位置身份 / 3 条保留 KILLED-UNBOUND（M97 落在门文件外、M89/M90 锚在前置 setup 断言上）/ 退役 0 条）。
   另请读该验收单第 9 节「本卡未证明什么」与第 10 节台账条目 #20——作者已做过一轮 8 维对抗复核
   （43 条原始发现、18 条完成三视角验证：8 站立 10 推翻、其余被用量限额中断后人工处置），
   **请独立核对其处置是否有错杀/漏杀**，特别是不采信的那 10 条「被推翻」。
6. 上一轮外审存档里的两段：`_bmad-output/审查/codex-review-CARD-DEBT-mutation-kill-identity.md` 的 HIGH-1 与 HIGH-2。

## 二 作者自述（请独立核对，不要采信）

1. **(c) 击杀身份改绑「断言源位置」**。原判据是「`expect_msg` 这个片段出现在该 nodeid 的短摘要 reason 里」。作者声称：本树实测证明**任何基于消息文本的判据**都分不开「前提断言红了」与「目标断言红了」——前提断言 `assert X, r.stderr[:250]` 的消息**就是**被测子进程的输出。于是新增 `EXPECT_LOC`：pytest `--tb=line` 打出的失败**位置**必须命中门文件里那条语句的 AST 规范化指纹（`stmt:<12 位十六进制>`）。两维是 AND。
2. **(d) 解析限定摘要区**。`parse_failed_nodeids` / `failed_reasons` 只在 `=== short test summary info ===` 之后到收尾统计行之间 `findall`，且只认 `^(FAILED|ERROR) ` 开头的行；摘要区不存在 ⇒ 判 `HARNESS-ERROR` 而不是 SURVIVED。另加 `--show-capture=no` 作为第二道独立防线。
3. **(e) 两条负控 + 一条正控 + 一段独立防线对照**，四个结论在 `negctl-n1n2-*.txt`。作者声称：同一份 pytest 输出喂给旧版与新版判据，旧版放行、新版拒；正控（目标断言真的红了）两版都判 KILLED。
4. **(f) 39 条 `KILLED-UNBOUND` 收口**：作者声称消息绑不出来的那些条目，**位置绑得出来**，所以 0 条退役。逐条见验收单第 6 节。
5. **(g) 四套裁决统一成六档**（`KILLED / KILLED-UNBOUND / SURVIVED / HARNESS-ERROR / ANCHOR-ERROR / SYNTAX-INVALID`），四套都从共用模块的 `VERDICTS` 取，且「六档之和 = 变异条数」写成了判据。g33 原先只有三档、锚点异常另叫 `ANCHOR-DRIFT`。
6. **(h) 信号统一**：`RestoreGuard` 挂四个信号（补齐 SIGQUIT）、先还原再退出、**还原期收到的信号只记待办不打断**。负控里「收口前的写法」留下 3 个未还原文件，新写法 0 个。
7. **(i) `PYEOF_RE`**：修。作者自述初稿对洞的形态判断**是错的**，实测后更正为三种形态（见该常量的注释与 `pyeof-negctl-*.txt`）。
8. **(j) 四套实测数字**：见验收单第 4-A 节引用的运行输出。

## 三 请按重要性回答的问题

1. **新判据是否还有「不是目标断言红的，却被记成 KILLED」的形态？** 尤其：变异体本身语法不合法 ⇒ 编译期就死 ⇒ 门因**别的**断言红；以及位置行归属（`--tb=line` 的位置行不带 nodeid，多条失败时怎么归）。
2. **摘要区截取的边界**：多段 summary、`-p no:cacheprovider` 之外的插件改了摘要格式、`COLUMNS` 变化、`ERROR` 行与 `FAILED` 行混排、收尾统计行的形态（`= 1 failed, 2 passed in 3s =`）。`_SUMMARY_TAIL_RE` / `_SUMMARY_HEAD_RE` / `_LOC_RE` 三个正则各自的失配面。
3. **`expect_loc` 的锚在门文件被别的卡改动后，是漂移报错还是静默失配？** 作者的设计是「门文件里找不到该指纹 ⇒ `HARNESS-ERROR`（锚失效）」，请核这条路径是否真的走得到，以及 `stmt_fingerprints` 用 `ast.dump(include_attributes=False)` 做规范化时，哪些改写会/不会改变指纹（例如改注释、改缩进、改断言消息、把 `assert a == b` 换成 `assert b == a`）。
4. **(f) 的 39 条里，有没有哪一条的位置绑定其实不成立**（例如指纹命中门文件里 >1 条语句、或位置落在门文件之外却被当成 `stmt:` 处理）。`check_expect_loc_unique` 的三条判据是否覆盖得住。
5. **四套统一后，g33 的 `--selfcheck-syntax` 与新分档是否语义一致**；以及 g33 把 `judge_surface_missing` 从「单独调用后 `return 2` 整份中止」改成「由 `kill_identity` 判 `HARNESS-ERROR` 并继续跑」，这个改动是否会掩盖某类问题。
6. **(h) 的还原期屏蔽与退出路径**：`RestoreGuard.critical()` 的嵌套、`_finishing` 防重入闩（现在丢弃信号时会打日志）、`_finish` 的 try/except+不同退出码（130=还原成功被中断 / 131=还原失败）、`_restore_active` 的 `now==orig → continue` 分支（覆盖「未写完」「已还原」两窗口）、以及第三方改动存证现在与信号路径共用同一份比对——这条此前出过一次真回归（伪告警+真改动被覆盖），负控 `negctl_thirdparty.py` 的 N3/N4/P2/N5 是否把两个方向都钉住了。
7. **对抗复核已修的 8+ 条站立发现是否修对、有没有引入新面**（作者自己的两次修复各引入过一条新 HIGH）；尤其「位置与消息必须落在同一次失败上」的保守 HARNESS-ERROR 分支会不会误拒合法的参数化用例。

## 四 输出格式

每条发现写成：

```
[级别 BLOCKER/HIGH/MEDIUM/LOW] 一句话结论
位置：<文件>:<行号>
依据：<你在代码/输出里实际看到的东西；引用原文行>
建议：<最小改动>
```

只读判定不了的，请明写「未验证」并说明缺什么信息，⛔ 不要用推测代替结论。

## 五 边界

- **只读**。⛔ 不要跑任何 harness、不要跑 pytest、不要发起任何会改文件的动作 —— 这四套脚本在运行时会**把变异体写进生产文件**再还原，跑它们等于在别人的工作树上改文件。
- 不在本次范围内的文件（别的卡的地盘，请不要提改动建议）：
  `backend/scripts/lifespan_isolation_negative_control.py`（U8-A）、
  `backend/scripts/lifespan_isolation_guard_probes.py` 与 `backend/tests/support/**`（U7）、
  `lefthook.yml`（U8-C）、
  `backend/tests/unit/conftest.py`（U10-A）、
  `canvas-vault/.claude/skills/quiz-answer/SKILL.md`（U5-B）、
  `backend/tests/regression/test_g3_2_review_ledger.py`（门本体，本卡只读）、
  `backend/app/**`（本卡不触及）。
- 措辞：请用「负控输入 / 对照输入 / 未被拦下的输入 / 门未覆盖的路径」来描述问题，不需要给出任何攻击性示例。

## 六 round-3 整改说明（本轮请核这五条改对没有、有没有引入新面）

你上一轮判不通过（1 HIGH / 3 MEDIUM / 1 LOW，无 BLOCKER），**全部整改、无驳回**：

1. **HIGH 参数 ID 含 ` - ` 被误切** → 新增 `_boundary_ok(nodeid)`：**方括号必须成对闭合**，
   否则该记录进 `unparsed_failure_lines` ⇒ 调用方判 `HARNESS-ERROR`。
   `parse_failed_nodeids` / `failed_reasons` / `failure_records` 三处解析都过这道边界校验。
   ⛔ 按你的建议**没有**改成贪婪或 `rsplit`（reason 本身也可能含分隔符）。
   本树实测复现过你给的那行输入，修后它进「未解析」而不是带着截断 nodeid 进判据。
2. **MEDIUM FAILED/ERROR 合并** → 新增 `failure_records()`（保留 `status`、**不去重**）与
   `exactly_one_failed(out, nodeid)`（恰 1 条 FAILED、0 条 ERROR、无未解析记录）；
   g32b 的空对照与 `complete` 对照两处都改用它。
3. **MEDIUM 二次还原异常覆盖 131** → `RestoreGuard.exiting()` 暴露「已进入退出展开」；
   四套的 `finally` 改走保号包装（g32b/g32cb/g32ccr1 的 `_restore_active_or_keep_exit_code()`、
   g33 的 `restore_or_keep_exit_code()`）：还原尝试与 traceback 都保留，只是不让二次异常改写退出码。
4. **MEDIUM 阶段 2 对照锚异常保留 KILLED** → 两处（空对照锚异常、`complete` 对照锚异常）
   都改为撤销 `_verdicts[tag]` 的 KILLED 并记 `HARNESS-ERROR`。
5. **LOW premise 筛忽略否定语义** → 顶层 `ast.UnaryOp(Not)` 直接返回 False（期望失败不算构造前提）。

**v5 全跑与 v2/v3/v4 逐项一致**：g32b 131/3/0/4/0/0 六档和 138 rc=2；g32cb 9/9、
g32ccr1 11/11、g33 18/18 rc=0；同批 `run-code-state-*.txt` 记录跑时五脚本 sha 与 HEAD。

你上一轮标注的未验证项与 #27 的三项欠账（信号组合、十条被推翻不能整体采信、解析面失配
不明确报错）仍**不在本卡闭合**，已登记台账。本轮如仍无法只读判定，请继续标「未验证」。
