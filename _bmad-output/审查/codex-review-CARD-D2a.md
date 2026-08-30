静态审阅结论：存在 1 个 HIGH。按要求未运行测试或业务代码，未修改文件。

## BLOCKER

无。

## HIGH

- [scripts/daily_review_run.py:172](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/scripts/daily_review_run.py:172)：升级当天不兼容旧 state。若旧 runner 已留下 `board_last_recommended[A]=today`、`last_generate_date=today`，但自然缺少新字段，同日重扫 B 登顶时 `None != today` 成立，随后 [177–178 行](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/scripts/daily_review_run.py:177) 会再给 B 落账，导致 A、B 同日均为 `today`，突破每日一次上界并污染 CARD-A3 tie-break。建议缺 marker 时同时用 `today in board_last_recommended.values()` 识别旧版当天已落账，并补充 legacy-state 同日换榜测试；旧空首扫因 map 中没有 `today`，仍可正常落账。

## MEDIUM

- [scripts/daily_review_run.py:172](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/scripts/daily_review_run.py:172)：标量 marker 只在日期单调时成立。对 live state 执行 `D1 → D2 → --now D1 → D2` 会反复开启 `!=` 门并回拨 marker，从而让 D2 再次落账。正常补跑、单调跨午夜不受影响。建议强制 `--now` 使用隔离 vault/state，或对日期倒拨 fail-closed，而非覆盖为旧日期。

## LOW

- [test_daily_review_run.py:300](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/backend/tests/regression/test_daily_review_run.py:300)：新增测试始终复用同一个内存 `st`，未锁定 marker 的跨进程持久化。当前赋值后调用 `save_state` 的实现静态正确，但“赋值移到保存之后”等回归可能逃过测试。建议落账后断言磁盘字段，再通过 `load_state()` 重载后执行换榜重扫。
- [test_daily_review_run.py:5](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/backend/tests/regression/test_daily_review_run.py:5)、[264](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/backend/tests/regression/test_daily_review_run.py:264)、[284](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-m3-push/backend/tests/regression/test_daily_review_run.py:284)：说明仍写成“只在首次生成/重扫路径不写/只属于首扫”，已不符合“首次非空生成可发生在重扫”。建议改成“当天已有 credit 后的换榜重扫不补写”。

逐项核验：

1. 新鲜 state 的普通首扫非空路径与旧实现的 payload、榜首落账完全相同；完整 state 文件仅多预期的加性字段。已有 credit 后重扫换榜不会补账。
2. per-vault `state_path`、整 dict 原子 `os.replace` 均覆盖新字段；JSON 解析/OSError 损坏重建后也能自举。合法 JSON 但结构错误仍是既有、非本 diff 引入的限制。
3. 正常跨午夜、同日本地日补跑及 `last_generate_date != credit_date` 的空首扫状态语义正确。
4. 指定 mutation 均能被抓住：改回旧门由两个新增测试捕获；删除 marker 写入或改为无条件落账，由休息日第三轮和既有换榜守卫捕获。缺口是升级当天旧 state 与持久化重载。
5. `scripts/daily_review_pick.py` diff 为空，due 判定及 payload 字段零改动。

BLOCKER/HIGH 清零: 否
