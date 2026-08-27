结论：**FAIL（现态改名正确，但守卫闭环不合格）**。A/C/D 为 PASS，B 为 FAIL。无 BLOCKER，发现 1 个 HIGH、2 个 MEDIUM、1 个 LOW。

## BLOCKER

无。

## HIGH

- **守卫未验证真实 report 输出侧，半套改名仍可“测试全绿、生产静默漏比”。**  
  守卫只检查方向表、磁盘 JSON、baseline 解析，并在行为测试中手工构造已含 `hit_*` 的 report：[test:64](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/tests/unit/test_retrieval_regression_metric_guard.py:64)、[test:93](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/tests/unit/test_retrieval_regression_metric_guard.py:93)、[test:137](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/tests/unit/test_retrieval_regression_metric_guard.py:137)。它没有触达真实 producer 与打印契约：[memory producer:208](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/scripts/run_memory_retrieval_regression.py:208)、[vault producer:352](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/scripts/run_vault_retrieval_regression.py:352)。

  静态反事实：若 `METRIC_DIRECTIONS`、alias、baseline 和测试已迁移，但 producer 与对应打印仍整体输出旧 `recall_*`，现有守卫断言均可满足；生产比较器却按 `hit_*` 取当前值，得到 `None` 后继续执行：[memory:296-300](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/scripts/run_memory_retrieval_regression.py:296)、[vault:424-426](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/scripts/run_vault_retrieval_regression.py:424)。其余指标无回退时最终仍报绿。当前完整 WT 的 producer/print 已正确改名，因此这是**守卫闭环缺陷**，不是当前默认路径已发生的漏比。

## MEDIUM

- **`--no-judge` 与守卫 schema 冲突，合法运行会确定性误红。**  
  初始 report 不含 `hit_at_5_judged`，而 [脚本:341](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/scripts/run_memory_retrieval_regression.py:341) 明确支持 `--no-judge`；该路径跳过唯一补键步骤后仍写入 `last_run`，也允许重固化 baseline：[脚本:365](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/scripts/run_memory_retrieval_regression.py:365)、[脚本:373](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/scripts/run_memory_retrieval_regression.py:373)、[脚本:403](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/scripts/run_memory_retrieval_regression.py:403)。守卫却无条件要求两个文件都含 judged 键：[test:93-97](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/tests/unit/test_retrieval_regression_metric_guard.py:93)。应稳定输出 `hit_at_5_judged: null`，或允许该非门禁参考指标缺失但继续禁止旧键。

- **对账存档结论真实，但不能独立支撑 exact-bytes 声明。**  
  存档直接给出布尔结果及总裁定：[reconciliation:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G4-12-migration-reconciliation-2026-08-27.txt:1)、[reconciliation:38](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/_bmad-output/审查/G4-12-migration-reconciliation-2026-08-27.txt:38)，但没有 HEAD/base commit、生成命令、比较算法、old/new blob 或 SHA-256、退出状态。其内容与本轮独立 `git diff --full-index --unified=0` 完全一致，所以“真实性”PASS；作为可移交、可复算证据仅 PARTIAL。

## LOW

- **守卫说明夸大影响。**  
  [test:3-6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/tests/unit/test_retrieval_regression_metric_guard.py:3) 称“全部指标”被跳过、门禁完全空转；实际只会跳过被改名的 hit 指标，其余 MRR、污染率等仍会比较。应表述为“该指标失守/门禁部分空转”。

## 通过项

| 检查 | 结论 |
|---|---|
| A 零数值漂移 | PASS。四个 JSON 的 full-index diff 只有 6 个键行替换；memory 两文件的 `0.6364`、vault 两文件的 `0.9623` 及所有其余内容不变：[memory baseline:7,12](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/tests/fixtures/regression_baselines/memory_retrieval_baseline.json:7)、[vault baseline:6](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/tests/fixtures/regression_baselines/vault_retrieval_baseline.json:6)。 |
| B baseline 半迁移 | PASS/PARTIAL。legacy 行为测试调用的是真实 `compare_with_baseline`；alias 不会架空 JSON 迁移，因为另有 canonical-only 断言。但 report 输出侧半迁移未覆盖。 |
| C 改名与误杀 | PASS。两脚本残留 recall 仅为旧名说明及 alias；`definition_recall`/`example_recall` 保持未动：[vault gold:38](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/tests/regression/vault_gold_set.yaml:38)、[vault gold:114](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/tests/regression/vault_gold_set.yaml:114)。两个 history JSONL 与已跟踪 `_bmad-output` 均无 diff。 |
| D alias 边界 | PASS。resolver 仅从 baseline 变量调用：[memory:292-299](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/scripts/run_memory_retrieval_regression.py:292)、[vault:419-425](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-n6-contract/backend/scripts/run_vault_retrieval_regression.py:419)；last-run、stdout、新 baseline 均直接写 canonical report，不输出 legacy 键。 |

本轮未运行测试、迁移脚本或业务代码，也未修改文件。结论绑定当前未提交 WT；守卫测试与对账件仍是 untracked，因此“同一 commit 原子交付”尚未形成可验证事实。G2-1 未纳入审阅。


