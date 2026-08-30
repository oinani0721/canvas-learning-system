结论：七项处置中，H1/H2/L1 可降级为已知限制；M1/M2/M3/L2 已解决。无剩余 BLOCKER/HIGH，但有 2 项 MEDIUM 一致性/既有残余。

## BLOCKER

无。

## HIGH

无。

## MEDIUM

1. 契约重述尚未全文件一致。

   限定版只出现在 [UAT:55](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/_bmad-output/验收单/UAT-CARD-D2b-休息日反转推送-2026-08-27.md:55)，但 [UAT:16](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/_bmad-output/验收单/UAT-CARD-D2b-休息日反转推送-2026-08-27.md:16)、[UAT:36](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/_bmad-output/验收单/UAT-CARD-D2b-休息日反转推送-2026-08-27.md:36)、[runner:139](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/scripts/daily_review_run.py:139)、[runner:238](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/scripts/daily_review_run.py:238) 和 [测试:687](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/backend/tests/regression/test_daily_review_run.py:687) 仍无条件承诺“每天至多 2 推”。

   准确契约应是：

   > 经生产 wrapper 按 vault 串行执行，且每次 runner 观察到 `send_bark.send()==0` 后 state 成功提交并在当日持续可读、未损坏/丢失时，每本地日、每 vault 至多两个本地可观察 accepted 成功轮次。

   不能把它解释为远端实际接收 HTTP 请求次数；`send_bark` 自身存在网络重试。

2. M1 精确反例已修，但 A7 的广义“损坏 state 不炸”仍未成立。

   例如 `next_due_utc=true`，同时当日 payload SHA 匹配，会在 [runner:150](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/scripts/daily_review_run.py:150) 执行 `bool <= str`，随后 [runner:224](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/scripts/daily_review_run.py:224) 返回失败而不隔离 state。此为既有字段级校验缺口，不是本次 `isinstance` 修复引入，也不推翻原 M1 两形态的 RESOLVED。

## LOW

1. M1 修复后两处注释过时：[migrator:134](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/scripts/migrate_daily_review_state.py:134) 和 [测试:621](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/backend/tests/regression/test_daily_review_run.py:621) 仍称顶层 `[]` 会让 runner 当场崩溃。

2. [M1 新测试:865](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/backend/tests/regression/test_daily_review_run.py:865) 验证了重建和继续推送，但未断言 `.corrupt-*` 隔离件存在；删除 quarantine rename、直接返回空 state 的 mutant 仍可通过。此外 [UAT:67](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/_bmad-output/验收单/UAT-CARD-D2b-休息日反转推送-2026-08-27.md:67) 仍写“新增 4 条测试”，实际为 7 条。

## 逐条裁决

| 项目 | 判定 | 静态结论 |
|---|---|---|
| H1 | ACCEPTED-AS-LIMITATION | A4 原设计确为本地 at-least-once、发送成功后再持久化。但 D2b 确实把单次落账崩溃的数量效应从旧第 2 次扩大到新第 3 次，不能称“完全没有新增效应”。同 ID 能更新对应通知内容，但官方文档要求 Bark ≥1.5.2、server ≥2.2.5；它不能证明不会再次出现横幅、声音或振动，因此“手机端不可见”表述过强。[Bark 官方文档](https://github.com/Finb/Bark/blob/master/docs/en-us/tutorial.md) |
| H2 | ACCEPTED-AS-LIMITATION | 损坏后隔离重建、丢失当日账本是 A7 既有 fail-open 语义；D2b 未新建该故障类别。反复损坏仍可无界重推，必须纳入上述 state 连续有效前提。 |
| M1 | RESOLVED | [runner:76](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/scripts/daily_review_run.py:76) 的短路校验安全覆盖顶层及账本容器错型；缺键仍补 `{}`。生产唯一调用方是 `main()`；八条 migrate 测试均不调用 `load_state()`，无兼容回归。 |
| M2 | RESOLVED | 缺键 legacy payload 记 `due`，关闭反转门；显式 `[]` 仍记 rest，非空榜仍记 due；`notification=None` 在此前即走 skip-empty。四条既有 D2b 路径语义不变。 |
| M3 | RESOLVED | `rest→due→rest→due` 状态链真实成立；`rcs=[0,0]` 对任意第三次 `send` 都会越界失败，哨兵有效。 |
| L2 | RESOLVED | `[0,1,1,0]` 已锁定连续失败、fallback 同日一次、错误落账及成功清错。 |
| L1 | ACCEPTED-AS-LIMITATION | `rc=2` 在网络请求前返回；自 A7 起字段事实上表示最后一次实际网络尝试。现有 health 消费方只看 accepted/fallback 日期，不读取这两个字段。 |

按要求未运行测试；“47 passed”仅作为用户给定裁判基线。Graphiti MCP 本会话未暴露，未执行 Graphiti 查询或写入。

BLOCKER/HIGH 清零: 是


