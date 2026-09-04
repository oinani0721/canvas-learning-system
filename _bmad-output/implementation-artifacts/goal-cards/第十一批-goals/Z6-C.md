> ⚠️ 本文件是 CARD-G3-2c-D 的完整卡文——车道开工后必读并逐条执行；它不是 /goal 粘贴文本。/goal 在第十一批手册 §三 Z6-C 块。
> 批次标记 `[BATCH-2026-09-05-第十一批 / CARD-G3-2c-D]`。车道：`card-x7-ledger-c`，**前提 Z6-B 已独立 commit**。⛔ 本批最高危动作：138 条变异 × 单条 pytest（timeout=900s），**每一次中断都在生产文件里留变异体**（X7-C 已实证污染两轮）。勘探 2026-09-05。协议：`.claude/rules/card-batch-protocol.md`。

# CARD-G3-2c-D — g32b 全量杀灭表：138 条一次跑完 + M2b 假门定性

## 〇 事实
| 事实 | 位置 |
|---|---|
| `g32b_mutation_gates.py` 共 **138 条变异**（tag 行计数 138），全部绑 `test_g3_2_review_ledger.py`（TESTF `:22`）；13 条挂 LAYER2/LAYER3_ALSO 同层、4 条 `kind="complete"` → 额外触发空变异对照与 body-only 对照，实际 pytest 调用 ≈ 155 | g32b:22 / :525 |
| pytest 路径缺口**已修**：`:497-517 _PYTEST_BIN()`（`G32B_PYTEST` → 车道 venv → SystemExit） | g32b |
| X7-C 的 (g) 缺口 = 全量杀灭表缺失：上次跑到中途因 **pgrep -f 自匹配误判进程已死 → 两个 g32b 并发原地变异** → 裁判 1 从 330 passed 掉到 7 failed/323 passed（失败门全是 M88 窗口的 scored_at 相关）；中断前已看到 `M2b-R2-drop-utc-offset-check` **SURVIVED** 这条真信号悬而未决 | UAT-CARD-G3-2c-C :191-237 / :461 |
| X7-C UAT §六 登记的 schema 基线 `58434ea3…` 已对不上当前字节（实为 `10ca9214…`，被 991ae914/ae53fa05 改过）——**跑前在本车道 HEAD 重钉基线，禁止照抄** | 风险 |
| KILLED 判据 = rc==1 且指定门红；`grep MUTANT` 为空**不是**干净证据（变异体替换文本可不含该字样，g32b:1832-1838 教训） | 判据 |

## 一 完成条件（AND）
- (a) 在本车道（Z6-B 之后、独占）跑，`G32B_PYTEST` 指向存在的 pytest 绝对路径；不改 g32b 判据逻辑。
- (b) 跑前在**本车道 HEAD** 重钉全文件 sha 基线（SKILL.md / fsrs_bridge.py / validate_learning_events.py / docs/learning-events-schema-v1.md），写进证据文件。
- (c) 单进程、串行、一次跑完 138 条 + 13 条空变异对照 + 4 条 complete 对照；全程 `nohup` 落盘；判存活用 `ps -ax -o args= | grep -F '<解释器绝对路径> <脚本绝对路径>'`（**禁 pgrep -f**）；结束进程后必须复查为空再动下一步。
- (d) 产出**全量杀灭表**（138 行：tag / 绑定门 / KILLED|SURVIVED|ANCHOR-ERROR / 失败身份首行）入 `_bmad-output/审查/evidence-g32b/`；SURVIVED 与 ANCHOR-ERROR 逐条给结论（假门 / 锚点漂移 / 应退役）。
- (e) 对 `M2b-R2-drop-utc-offset-check` 出明确裁定：复现 SURVIVED 则判 `test_r2_non_whole_second_durable_review_time_fail_closed` 为假门并补一道真承重门（或说明该防线已被上游校验器接管、变异应退役）；不允许只登记不定性。
- (f) 跑后逐文件 sha 复核相同；`git status --porcelain` 空；`grep -rn 'MUTANT' canvas-vault/` = 0（**辅助**锚点）。
- (g) 裁判 1 复跑回到 335 passed 1 skipped（或如实登记新数字与归因）。
- (h) 一轮 Codex（gpt-6-astra ultra）只审 (e) 的新门/退役决定与杀灭表的定性（不审 harness 本体）。

## 二 裁判命令
1. 基线：`shasum -a 256 canvas-vault/.claude/skills/quiz-answer/SKILL.md canvas-vault/.claude/scripts/fsrs_bridge.py backend/scripts/validate_learning_events.py docs/learning-events-schema-v1.md | tee _bmad-output/审查/evidence-g32b/sha-before.txt`。
2. 主跑：`G32B_PYTEST=<venv>/pytest nohup <venv>/python backend/scripts/g32b_mutation_gates.py > _bmad-output/审查/evidence-g32b/g32b-full-run.txt 2>&1 &`；存活判据 `ps -ax -o args= | grep -F 'g32b_mutation_gates.py' | grep -v grep`。
3. 表齐备：`grep -c ' → KILLED' …/g32b-full-run.txt` + `grep -c 'SURVIVED' …` + `grep -c 'ANCHOR' …` 之和 = 138。
4. 收尾：run 文件出现 `变异验证 PASS: 138/138 …` 或 `变异验证 FAIL:` 后逐条列出（两者都算完成，FAIL 需 (d)(e) 定性）；`shasum … | diff - sha-before.txt` 为空。
5. `cd <树>/backend && PYTHONDONTWRITEBYTECODE=1 $PYTEST -q -p no:cacheprovider tests/regression/test_g3_2_review_ledger.py` → 335 passed 1 skipped。

## 三 禁改与隔离
禁同时启动两个 g32b（本卡核心教训）；禁 `pgrep -f`/正则判进程存活；禁在中断后「凭 grep MUTANT 为空」判定干净（必须全文件 sha）；禁改 g32b 的 KILLED 判据或删变异凑全绿；禁部署到 live skill；live vault 与主库 canvas-vault/ 只读；**若中途必须放弃，退出前先跑一次 sha 复核再收工**；不改台账；不 push。

## 四 Codex / 验收单
命令同协议（`codex-prompt-CARD-G3-2c-D.md` → `codex-review-CARD-G3-2c-D.md`，1 轮）。验收单 `…/验收单/UAT-CARD-G3-2c-D-<日期>.md`：DoD-3 双段；4-B「无变化（把上批没跑完的 138 项『故意弄坏看能不能被发现』全部跑完并逐项登记）」；「本卡未证明什么」必填：不改行为、不部署 live；`q_()` 纵深由 Z6-B 负责；「台账待登记条目」必填（X7-C (g) 缺口闭合）。commit header ≤100 含批次标记，body 行 ≤100；不 push；跑完说「复核第十一批 Z6」。
