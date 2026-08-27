# Codex 对抗审查 · CARD-D4 fallback serialize datetime 修复

> 审查模型: codex exec gpt-5.6-sol / model_reasoning_effort=ultra / --sandbox read-only
> 日期: 2026-08-28 · 分支 card/m2-honest（审查时未 commit 的工作树 diff）

## 一轮（终态：0 BLOCKER / 0 HIGH / 2 MEDIUM / 3 LOW，行为修复 PASS）

结论：当前 live worktree 中，CARD-D4 行为修复 **PASS**，真实 FSRS 分支零改动；**BLOCKER/HIGH 为 0**。提交与追踪状态为 **PARTIAL**，有 2 项 MEDIUM 治理问题。

## BLOCKER

- 当前 worktree：无。

- **条件性 BLOCKER / FAIL**：贴文路径是 `tests/regression/...`，实际文件是 [backend/tests/regression/test_fsrs_fallback_datetime_serialize.py:24](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/tests/regression/test_fsrs_fallback_datetime_serialize.py:24)。若贴文路径是待提交的 literal patch，`_LIB_PATH` 会误指不存在的 `<repo>/lib`，且不在 backend 标准测试收集范围；以当前 worktree 为权威则此项不存在。

## HIGH

- 无。

## MEDIUM

- **MEDIUM / PARTIAL — 回归测试尚未进入 Git patch**：[test_fsrs_fallback_datetime_serialize.py:1](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/tests/regression/test_fsrs_fallback_datetime_serialize.py:1) 当前状态为 `??`。普通 `git diff HEAD` 和 `git commit -am` 都会遗漏该文件，导致修复落地但唯一专用回归锁未落地。

- **MEDIUM / FAIL — Source 追踪锚点在当前 checkout 悬空**：[test_fsrs_fallback_datetime_serialize.py:2](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/tests/regression/test_fsrs_fallback_datetime_serialize.py:2) 引用的 goal-card 不存在于当前 HEAD；它只存在于非祖先提交 `b47ebfba` 所在的其他分支。因此当前分支无法自包含复算 CARD-D4 计划来源，属于 DD-14 追踪链缺口，不影响运行时修复。

## LOW

- **LOW / PARTIAL — `last_review` 仍写读不对称**：[fsrs_manager.py:303](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/lib/memory/temporal/fsrs_manager.py:303) 会将其转为 ISO 字符串，但 fallback 读侧 [fsrs_manager.py:385](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/lib/memory/temporal/fsrs_manager.py:385) 只还原 `due`。实测 roundtrip 后 `last_review` 为 `str`。现有 fallback create/review 不产该键，因此建议只入档，不扩本卡。

- **LOW / PARTIAL — 并非任意 aware datetime 都能严格等值还原**：[fsrs_manager.py:303](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/lib/memory/temporal/fsrs_manager.py:303)、[fsrs_manager.py:387](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/lib/memory/temporal/fsrs_manager.py:387)。UTC、naive、固定偏移 datetime 均等值；IANA `ZoneInfo` 的 DST 重叠时刻会丢失 zone key/fold，可能导致 `restored != original`。fallback 自产值全部是 UTC，故不阻断本卡。

- **LOW / PARTIAL — 子进程断言存在优化模式静默面**：[test_fsrs_fallback_datetime_serialize.py:42](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/tests/regression/test_fsrs_fallback_datetime_serialize.py:42)、[test_fsrs_fallback_datetime_serialize.py:73](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/tests/regression/test_fsrs_fallback_datetime_serialize.py:73) 使用裸 `assert`。在 `python -O` 下将 serializer 替换为返回 `"{}"`，探针仍能打印成功 marker 并退出 0。标准 pytest 环境不受影响，原 TypeError 也仍会直接中断；属于测试加固项。

## 已确认 PASS

- [fsrs_manager.py:277](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/lib/memory/temporal/fsrs_manager.py:277) 的真实 FSRS 分支前后 SHA-256 均为 `8f66a109…`；diff 只有 fallback `else` 内 `+6/-0`。
- HEAD 旧代码实测三条路径均为 `TypeError`：create、review、`card_to_state`；当前完整 CARD-D4 四文件套件 **60 passed**。
- `sys.modules["fsrs"]=None` 确实进入当前生产模块的 fallback。
- [fsrs_manager.py:297](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m2-honest/backend/lib/memory/temporal/fsrs_manager.py:297) 的浅拷贝足够：新增逻辑只重绑顶层键，调用方 dict、datetime 和嵌套对象均未变异。
- 已按要求不重复报告 P3 与 DEBT-8。

审阅期间新测试由贴文的 87 行 `0d466b7a` 并发变为当前 91 行 `9eda9919`，语义仅见格式变化；因此 exact-bytes 身份仍标记 **PARTIAL**。未运行全量 CI。



---

## 处置记录（开发侧）

- M1（新测试文件 ?? 未 staged）→ commit 时显式 git add，流程内解决
- M2（goal-card 档案不在本分支 HEAD）→ 如实入档：卡片档案按批次惯例存于 feature-obsidian-hybrid-dev worktree（绝对路径引用），合并日主仓归档
- LOW×3 入档不扩：fallback 读侧 last_review 不还原（fallback 卡不产该键）；ZoneInfo DST 边界（fallback 自产值全 UTC）；python -O 下裸 assert 静默面（标准 pytest 不受影响）
- 条件性 BLOCKER 澄清：diff 贴文路径前缀是 backend cwd 生成呈现问题，实际文件在 backend/tests/regression/，以 worktree 为权威时不存在
