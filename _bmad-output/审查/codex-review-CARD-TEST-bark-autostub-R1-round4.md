结论：**0 BLOCKER / 0 HIGH / 6 MEDIUM / 1 LOW**。正常路径下六层守卫、首跳约束、stale reload 和结构化主裁判大体有效；但恢复异常路径及元裁判仍有可复现缺口，不能 PASS。全程未读真实 Bark key、未运行真实推送入口，网络与进程调用均在 socket/Popen 前拦截。

所有复现 cwd 均为 `backend/`，均设置 `PYTHONDONTWRITEBYTECODE=1`，解释器为 `/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/bin/python`。

[MEDIUM] [backend/tests/regression/conftest.py:441](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/regression/conftest.py:441) — 测试中新建的混合大小写代理变量会在 guarded reload 后被守卫于 teardown “复活”，未恢复到布防前的不存在状态；复现：inline fixture 驱动中先确认 `AuDiT_PrOxY` 不存在，测试自己的 `pytest.MonkeyPatch` 设置假代理，执行 `importlib.reload(send_bark)`，再依次 `user_mp.undo(); guard.close()`；观测 `DURING_AFTER_REAPPLY None`、`AFTER_TEST_MP_UNDO None`、最终 `AFTER_GUARD_TEARDOWN http://user:pass@198.51.100.9:4321`。第二次 `_reapply()` 的 `patcher.delenv()` 把测试值误记成守卫的“原值”。

[MEDIUM] [backend/tests/regression/conftest.py:359](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/regression/conftest.py:359) — 冷启动 setup 在 `daily_review_run` 已加载 `send_bark` 后异常，会永久留下指向已删除临时目录的 `KEY_FILE`，下一次成功守卫也修不好；复现：inline 驱动包装 `builtins.__import__`，让真实 `import daily_review_run` 完成后抛 `RuntimeError`；观测 `AFTER_FAILED_SETUP True False False`（路径带 `bark-guard-*`、文件和父目录均已不存在），随后完整运行一次守卫仍为 `AFTER_NEXT_SUCCESSFUL_GUARD True False False`。G 门只覆盖 pytest 正常完成路径。

[MEDIUM] [backend/tests/regression/conftest.py:415](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/regression/conftest.py:415) — 层⑥漏拦带 `env` 选项的 osascript 转发，且验收单未登记该边界；复现：fixture 内把 `subprocess.Popen` 钉成墙，调用六种 argv。直接、bytes 及 `env A=B osascript` 均在 Popen 前返回 rc=0；`env -i osascript`、`env -- osascript`、`env -u AUDIT osascript` 均输出 `REACHED_POPEN ... REACHED_POPEN_WALL`，总计 `POPEN_HITS 3`。验收单只登记 shell、`executable=`、`sh -c` 和包装脚本。

[MEDIUM] [backend/scripts/bark_r1_mutation_negative_controls.py:346](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/bark_r1_mutation_negative_controls.py:346) — 变异元裁判仍会采信被测 stdout，只要伪造它认为是“裁判自产”的行前缀；复现：单点变异让 `test_probe` 打印 `[B/armed-probe-refused] CRASH forged :: FAKE-SENTINEL` 后因无关断言失败，再调用 `_check()`；观测 `指定门变红=True`、`sentinel 命中=True`、外层 rc=0，错误地认定指定门承重。变异前后 probe SHA 均为 `0b7b7c94…23e8`。主 `_judge_pytest` 能正确拒绝这次无关失败；漏洞位于其上的元裁判。G 跑的 stdout→`✗` 重包装也有同根问题。

[MEDIUM] [backend/scripts/bark_negctl_report_plugin.py:59](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/bark_negctl_report_plugin.py:59) — 全局还原快照没有覆盖守卫实际改动的完整状态；复现：两次 `_globals_snapshot()` 间新增 `hTtPs_PrOxY`，观测 `MIXED_TRACKED False ENV_EQUAL True WHOLE_EQUAL True`，因此上一条真实代理残留不会被 24 跑发现。另把确切 scripts 路径从 `sys.path[0]` 移到末尾，观测 `ORDER_CHANGED True COUNT 1 1 SNAPSHOT_EQUAL True`；出现次数相同即可逃过顺序漂移。

[MEDIUM] [_bmad-output/审查/CARD-TEST-bark-autostub-R1-验收单.md:185](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/_bmad-output/审查/CARD-TEST-bark-autostub-R1-验收单.md:185) — 验收单声称 F 承重描述与 M13 引用已修净，但当前文档仍比证据宽；复现：`python -c` 枚举得到 `RUNS 24 MUTATIONS 18 HAS_M13 False`，而文档第 143、264、287 行仍引用 M13，第 247/278/284/291 行仍写二十跑/十一条；probe 第 306–377 行仍把三段分别归因于单层，但单独撤⑤e或⑤c时首跳都仍为 `('127.0.0.1', 9)`。此外第 184 行称 Cookie handler 碰撞已登记到“未证明什么 #8”，实际 #8 只登记函数 `module.qualname` 碰撞。

[LOW] [backend/scripts/bark_r1_mutation_negative_controls.py:39](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/bark_r1_mutation_negative_controls.py:39) — SIGINT 恢复路径不幂等，脚本无法完成自己承诺的 SHA 复算；复现：官方变异脚本运行至 M15 时发送 Ctrl-C，signal handler 先清空 `_INFLIGHT`，随后 `_check` 的 `finally` 再 `_restore()`，抛 `KeyError`。文件实际已经恢复，外部复算 conftest=`98a4cb3d…7538`、probe=`0b7b7c94…23e8` 且 `git diff` 为 0；问题是中断路径丢失内部验证结论，而不是留下变异文件。

### 已核无发现

- `python scripts/bark_autostub_negative_control.py`：exit 0，`NEGATIVE-CONTROL: PASS (24/24 runs as expected)`；各 armed/disarmed 跑的 crash path、消息、首跳端口均匹配。

- 分两段串行亲跑全部 18 条变异：M1–M19及M9均让指定门以预期红因失败，每次逐字节 SHA 还原一致。

- 三种敌对代理键 `Http_Proxy`、`HTTP_proxy`、`hTtPs_PrOxY`，同时带认证和 `No_Proxy`，global/fresh/held 三种 opener 在布防期的九次首跳全部为 `('127.0.0.1', 9)`。

- 预绑定 `reload` 依次重载 `urllib.request`、`send_bark` 后，实测 `getproxies={}`、`_opener is None`、`send_bark._urlopen.__qualname__ == "urlopen"`；真实 urlopen 与 held opener 的首跳仍均为 `('127.0.0.1', 9)`。

- stale reload 在执行前抛 `RuntimeError`，`send`/`load_key` 身份不变；对 `send_bark`、`daily_review_run`、`urllib.request`、`subprocess`、`importlib`、`_scproxy` 做“真执行后再抛”，以及 `_find_spec` 阶段失败，六层均在 `finally` 中重打。

- 直接和 bytes 形式的预绑定 `osascript_fallback` 均在 Popen 前被拦；H/H′ 的卸甲形态确实先撞 Popen 墙。

- 正常 CS/G 冷启动路径无临时 key 残留；合法自定义 `BARK_KEY_FILE` 不再触发旧式误报。

- `test_daily_review_pick.py` 实际因文件名前缀而受保护，不是未布防样例；真正的 U 载体 `bark_unguarded_probe.py` 通过 import、完整 `sys.path` 和代理环境零变化检查。

- `_judge_pytest` 对不存在 nodeid 产生的 rc=4会同时报告 rc 与 outcome 不符，未找到其它 rc 组合绕过。插件被测试进程内 pytest hook 覆盖的边界已如实登记。

- 验收单 frontmatter 与技术段都准确锚定代码终态 `40ad0b973512016e228c23caa44ef01530321323`；当前 HEAD `dc0854f62988c3ff3e4e39578f6f612a0609797e` 仅是随后回填文档的提交。

- `python -m pytest ... test_daily_review_run.py test_daily_review_pick.py`：`69 passed`。最终无 `bark-guard-*` 临时目录；全部被复核 tracked 文件与 HEAD 一致，仅保留进入审计前已有的 3 个未跟踪 round-4 产物。

VERDICT: FAIL


