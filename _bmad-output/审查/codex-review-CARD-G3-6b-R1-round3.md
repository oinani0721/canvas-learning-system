结论：**FAIL（0 BLOCKER / 0 HIGH / 5 MEDIUM / 3 LOW）**。目标 commit 当前实现未复现产品错误，但防回退证据仍可假绿，且 M3/M4/M5 留有未闭合声明。

## 发现

- [MEDIUM] [g36b_r1_recheck.py:295](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/_bmad-output/审查/evidence-g36b-r1/g36b_r1_recheck.py:295)、[test_daily_review_pick.py:1308](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/backend/tests/regression/test_daily_review_pick.py:1308) — M1 原变异已关闭，但非默认分钟的生产 fixture 只有一块板。隔离单变异让首板使用 11/13、后续板回落 3/5，探针仍 `22/22`、裁判仍 `130/130`；双板入口实际输出一板 13、另一板 5，而两板均应为 13，rank SHA 仍登记 11/13。建议用至少两板、多种 factors，逐行按加载后的分钟配置复算并加入负控。

- [MEDIUM] [g36b_r1_recheck.py:378](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/_bmad-output/审查/evidence-g36b-r1/g36b_r1_recheck.py:378)、[test_daily_review_pick.py:1392](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/backend/tests/regression/test_daily_review_pick.py:1392) — M2 原 `top_boards` 变异已关闭，但 recorded-only fixture 全是到期板，`upcoming` 分支为空。让 `recorded.limits.upcoming` 控制截断后仍 `22/22 + 130/130`；四个未来板中 recorded=3 输出 3 行、recorded=99 输出 4 行，完整 payload 不同。建议同一 manifest 对同时覆盖四个到期板和四个未来板，并精确锁定两个榜长均为 3。

- [MEDIUM] [g36b_r1_negctl_probe.py:87](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/_bmad-output/审查/evidence-g36b-r1/g36b_r1_negctl_probe.py:87)、[g36b_r1_negctl_probe.py:110](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/_bmad-output/审查/evidence-g36b-r1/g36b_r1_negctl_probe.py:110)、[UAT:446](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/_bmad-output/验收单/UAT-CARD-G3-6b-板级why_this_board与rank_manifest-2026-09-01.md:446) — 五个单变异确实逐条匹配指定 `[FAIL]`，空源码也正确判 `INVALID`；但第六个“全部叠加”传入 `expect_kw=None`，任意 `[FAIL]` 即算 `CAUGHT`。用无关精度失败实测可被该分支误判。建议要求五个指定关键词全部出现，或不要把叠加项称为“由指定断言抓住”。

- [MEDIUM] [UAT:204](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/_bmad-output/验收单/UAT-CARD-G3-6b-板级why_this_board与rank_manifest-2026-09-01.md:204)、[UAT:246](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/_bmad-output/验收单/UAT-CARD-G3-6b-板级why_this_board与rank_manifest-2026-09-01.md:246)、[UAT:273](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/_bmad-output/验收单/UAT-CARD-G3-6b-板级why_this_board与rank_manifest-2026-09-01.md:273)、[g36b_r1_recheck.py:180](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/_bmad-output/审查/evidence-g36b-r1/g36b_r1_recheck.py:180) — M4 指定的源码、测试三处已经正确收窄，但验收单全文仍无条件写“交换位置序与 SHA 同变”“规则变⟹SHA 变”，并残留“三条声明”。这使“全部措辞已统一”不成立。建议限定为相应 fixture，并统一成“本文件字节或明列生效值变⟹SHA 变；排序是否变化取决于数据”；历史栏若保留，应标记已被后续 H1 收窄。

- [MEDIUM] [UAT:68](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/_bmad-output/验收单/UAT-CARD-G3-6b-板级why_this_board与rank_manifest-2026-09-01.md:68)、[verify-high-decay-output.txt:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/_bmad-output/审查/evidence-g36b-r1/verify-high-decay-output.txt:1)、[daily_review_pick.py:642](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/scripts/daily_review_pick.py:642) — M5 四组数值均复算正确：`c2d2e590 ad1a38a5→b3ff4b99`、`9e158d82 2c8da36c→503fd4b6`、`66346bce 2c8186a1→eb6b6710`、`ae7f67a4 1f5eb882→bc3aa142`。但前两条历史行缺 commit/pick SHA，末行仅写“本次提交”；`9e158d82` 又把测试文件中的第三处 docstring 混入 rank SHA 归因。当前 HIGH 输出已是 `bc3aa142` 且无 commit/pick-SHA 头，而其他位置仍引用未绑定的 `503fd4b6`。建议只把 Git-object 可绑定状态放入三元组表，并给每份输出加 immutable commit/pick SHA 头。

- [LOW] [g36b_r1_mutations.py:19](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/_bmad-output/审查/evidence-g36b-r1/g36b_r1_mutations.py:19)、[g36b_r1_mutations.py:32](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/_bmad-output/审查/evidence-g36b-r1/g36b_r1_mutations.py:32)、[g36b_r1_mutations.py:169](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/_bmad-output/审查/evidence-g36b-r1/g36b_r1_mutations.py:169) — clean-clone 说明仍不精确：脚本硬编码原车道，且 `.venv` 与 `.env` 都未跟踪；在别处“直接跑”并不能唯一归因为缺 `.env`。第 169 行还残留“EXIT trap 等价物”，与文件头的不等价声明冲突。建议从参数/`__file__` 解析车道并列全环境前置，删除该残句。

- [LOW] [g36b_r1_mutations.py:113](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/_bmad-output/审查/evidence-g36b-r1/g36b_r1_mutations.py:113)、[g36b_r1_mutations.py:186](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/_bmad-output/审查/evidence-g36b-r1/g36b_r1_mutations.py:186)、[UAT:448](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/_bmad-output/验收单/UAT-CARD-G3-6b-板级why_this_board与rank_manifest-2026-09-01.md:448) — tail 只是打印且再截 360 字符，可能截掉 stderr；目标树也没有本轮 mutation 输出归档，故“红时归档 tail”不实。建议提交完整运行输出，分别保存 stdout/stderr，并机器校验预期断言。

- [LOW] [UAT:461](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w6-whyboard/_bmad-output/验收单/UAT-CARD-G3-6b-板级why_this_board与rank_manifest-2026-09-01.md:461) — 仍称 W4 停在 `2cacbb0c`，与同文及当前实际 `d3fba4e0` 冲突。刷新该处即可；runner `BLOCKED` 结论本身真实。

## 已核实

- HEAD/分支/目标 commit 正确；tracked diff 为零。porcelain 非字面 clean，仅有三个未跟踪 round-3 审查侧车，我未读取或修改。
- 当前裁判实跑 `130 passed, 10 warnings`。
- A=`ad1a38a5…` 与 B=`1f5eb882…` 均独立实跑 `22/22`。
- 原 M1/M2 指定变异分别被新 SHA 同源门和四板 `top_boards` 门抓住。
- 五个单负控、空源码 `INVALID`、末尾“未枚举仍可能漏网”均成立。
- launchd 过宽表述已收回。
- 把卡文 §5-2 转为 owner 待裁决而不擅改只读卡文，程序处置恰当；但 A/B 未裁决前该裁判不能记为满足。
- W4 当前为 `d3fba4e0`，尚无 R1 非空终审；`batch9/integration` ref 与 `batch9-integration` worktree 均不存在，因此 runner 继续 `BLOCKED` 是诚实登记。
- 未运行 runner、未读取 live 节点，也未构造任何 `.pyc`、mtime 或运行时字节码替换验证。

**总裁决：FAIL**


