结论：**仍然 BLOCK，不可合入**。8 项中 4 项关闭、4 项维持。

| 项目 | 复审结论 | 核验结果 |
|---|---|---|
| B1 异常降级 | **关闭 / PASS** | stale 区段捕获全部 `Exception`；`_collect` 已逐库兜底为 corrupt，见 [review_overview.py:141](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/app/api/v1/endpoints/review_overview.py:141)、[review_overview.py:178](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/app/api/v1/endpoints/review_overview.py:178)。 |
| B2 generated_at | **维持 / BLOCKER** | 非 `str` 拒绝及常见宽松格式修复属实，但正则仍可被非法 offset 绕过。 |
| B3 v3 门禁 | **维持 / BLOCKER** | 版本和权威计数门禁有效；非有限数及嵌套元素仍可获 `ok`。 |
| HIGH fixture | **维持 / HIGH** | 环境键存在性与 `try/finally` 已修；原报告指出的 imported-settings split-brain 未修。 |
| MEDIUM stats 解耦 | **关闭** | 明细长度 1、stats=7，并断言输出 7，见 [test_review_overview.py:101](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/tests/unit/test_review_overview.py:101)。 |
| MEDIUM 敌对形状 | **维持（部分）** | 已补嵌套容器、非法计数、NaN、时间溢出；原清单中的 PermissionError、投影路径为目录仍无测试。 |
| MEDIUM mtime 反证 | **关闭** | 今日投影 mtime 回拨一周仍断言 `ok`，见 [test_review_overview.py:194](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/tests/unit/test_review_overview.py:194)。 |
| MEDIUM 只读断言 | **关闭** | 两端点前后 exact bytes 与 mtime 均锁定，见 [test_review_overview.py:221](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/tests/unit/test_review_overview.py:221)。 |

关键阻断证据：

- **B2**：正则的 offset 是不带范围约束的 `\d{2}:\d{2}`，见 [review_overview.py:35](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/app/api/v1/endpoints/review_overview.py:35)。真实 HTTP 入口实测：

  ```text
  2026-08-25T12:00:00+08:60 -> status=ok
  2026-08-25T12:00:00+08:99 -> status=ok
  ```

  Python 3.14 分别将它们归一化为 `+09:00`、`+09:39`。A2 的真实构造是 `isoformat(timespec="seconds")`，见 [daily_review_pick.py:273](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/scripts/daily_review_pick.py:273)，当前生产输出 `...+08:00` 不会被误杀，也绝不会产生上述非法分钟。因此“只认生产器确切形态”仍未成立。

- **B3**：`_strict_int(type is int)` 对默认 JSON 解码可靠：整数、布尔、浮点会分别解为 `int/bool/float`。`parse_constant` 也不会影响合法 JSON/A2 投影，但只拦裸 `NaN/Infinity`。标准数字 `1e999` 经 `parse_float` 解为 `inf`，随后 [review_overview.py:103](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/app/api/v1/endpoints/review_overview.py:103) 原样透传。真实入口结果为 HTTP 200、`status=ok`、`pending=null`。另外 `upcoming=["not-an-object"]` 等错误元素形状仍可获 `ok`。

- **HIGH**：fixture 的存在性恢复和 pre-yield `TestClient` 异常恢复均成立，见 [test_review_overview.py:77](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/tests/unit/test_review_overview.py:77)。但 [main.py:56](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/app/main.py:56) 按值导入 `settings`，而 [config.py:1064](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/app/config.py:1064) 只重绑定 `app.config.settings`。探针显示 fixture 前对象身份相同，teardown 后变为不同对象，原 HIGH 未完整处置。

`_collect` 的宽捕获确实会把编程错误转成 corrupt，且没有服务端 traceback 日志；响应仍保留异常类型和消息，所以不是静默失败，不新增 BLOCKER/HIGH，但可观测性仍应补 `logger.exception`。

存量失败归因基本成立：

- 单跑 `test_vault_id_changes_after_reload` 仍为 `canvas_vault != cs_61b`。
- 测试体只直接依赖 `app.config`；纯 `app.config` 子进程、未加载 `app.main` 或 CARD-C2，也得到 `canvas_vault`。
- 根因是 [config.py:765](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-l1-crossvault/backend/app/config.py:765) 的 yaml-first 优先级，以及实际 [.canvas-config.yaml:10](/Users/Heishing/Desktop/canvas/canvas-learning-system/canvas-vault/.canvas-config.yaml:10)。
- 严格说 pytest collection 会通过 `conftest → app.main → router` 间接导入 CARD-C2，但不调用 `_collect`，与失败数据流无关。
- “7 月已记录为 P0-3 存量债”属实；但不兼容实际由 2026-05-10 的 yaml-first 变更形成，不是 7 月才开始。

实跑：

```text
cd backend && .venv/bin/pytest tests/unit/test_review_overview.py -q
6 passed, 10 warnings in 0.60s
```

同跑两个文件结果：`31 passed, 1 failed`，唯一失败即上述存量 vault-switch 用例。

**最后结论：BLOCKER/HIGH 未清零（2 BLOCKER + 1 HIGH）；CARD-C2 不能合入。**



---

# 附录 B — 第二轮处置记录（Claude, 2026-08-25）

## BLOCKER 处置

- **B2 offset 绕过 → 已修**。正则 offset 收紧到日历合法范围 `[+-](0\d|1[0-4]):[0-5]\d`——+08:60/+08:99/+15:00 均通不过正则直接 stale（fromisoformat 的静默归一化再无入口）。新增 lax-bad-offset-60/99/15h 三用例锁定。
- **B3 残余 → 已修**。①json.loads 加 parse_float=_finite_float：标准数字 1e999 在解码层抛 ValueError → corrupt（bad-inf 用例）；②嵌套元素形状：upcoming[0] 必须 object（bad-upcoming-elem）、top.pending 非空必须非负非 bool int（bad-pending-str）、vault_id/date/board/top_node 非空必须 str（_opt_str）；透传进响应的每个字段现均有类型门禁。

## HIGH 处置

- **fixture split-brain → 已修**。fixture 前后各执行 `app.main.settings = app.config.settings` 同步——reload 后与 teardown 后两模块恒指同一对象，消除按值导入造成的分裂（根因在 main.py 的导入方式，属存量架构，本卡在测试生命周期内闭合）。

## MEDIUM 处置

- 敌对清单补齐 PermissionError（chmod 000，root 环境自动跳过防假绿）与目录冒充投影文件（IsADirectoryError）两用例。
- _collect 兜底加 logger.exception（corrupt 降级不再丢服务端 traceback）。

## 复验

6 passed；ruff 全绿；真实环境 e2e：全局 200，canvas-vault ok / test-vault ok / _bmad-output no_projection（严格化未误杀 A2 生产器真实输出）。
