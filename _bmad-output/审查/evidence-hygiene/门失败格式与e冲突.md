# session fixture teardown fail 的输出格式，与 (e) 的冲突

## 实测格式（独立最小 pytest 工程，scratchpad，不碰 backend/）

```
==================================== ERRORS ====================================
_________________________ ERROR at teardown of test_b __________________________
模拟不变量门失败:
  新出现 vault 骨架: /x/backend/raw
=========================== short test summary info ============================
ERROR tests/test_x.py::test_b - Failed: 模拟不变量门失败:
2 passed, 1 error in 0.24s
```

rc=1。**关键**：short summary 那行是

```
ERROR tests/test_x.py::test_b - Failed: ...
```

它**会**被基线口径 `grep -E '^(FAILED|ERROR) tests/'` 捞到，
且 nodeid 取的是**最后一个跑完的测试**（不是固定值，会随收集顺序变）。

## 由此产生的冲突

- 卡文 (c) 要求：违反即 `pytest.fail`（session teardown → 末尾 ERROR，rc 非 0）。
- 卡文 (e) 要求：tests/unit 基线逐 nodeid diff **不得出现新增 `>` 行**。

`/tmp` 是全机共享的，本批 9 车道并行。若在裁判 6 那 ~5.5 分钟里，**别的车道**
跑 tests/unit 造出 `/tmp/test-vault*`（实测 card-y9-maingoal 就干过），
本卡的门就会 fail，基线 diff 随即多出一条 `>` 行 —— (c) 与 (e) 在这种情况下
不可同时满足，且触发条件不在本卡控制范围内。

## 本卡处置

1. 照卡文 (c) 实现 fail（甲方要求；且假红方向是「过严」，不是「漏网」）。
2. 跑裁判 6 之前：`ps` 检查有无别的车道在跑 tests/unit，并把 `/tmp/test-vault*`
   改名清空（重新武装）。
3. 跑完若出现该 ERROR，用 `stat -f '%Sm'` + `ps -ww` / `lsof -a -d cwd` 判归属，
   如实记录是本卡引入还是并行干扰。
4. **本卡自身零污染有独立证明**：`backend/` 四路径与两文件 sha 这两组判据
   是本 worktree 独有的，不受别的车道影响 —— 无论 `/tmp` 那条怎样，
   它们都能独立回答「本卡有没有把东西写进仓库」。

## 建议（待登记）

把 `/tmp` 那段判据收窄为进程归属绑定，或降级为 warning。
现状下它在并行批次里是一个已知的假红源。
