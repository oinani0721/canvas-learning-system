## 结论

复核对象为 `card/w4-safety-r2` 当前 HEAD `919a9a48c98aa5118a05c4ac8547e8b63c3f91fd`。

**BLOCKER 0 / HIGH 3 / MEDIUM 7 / LOW 2。**

正常使用路径下，上一轮的 stale reload、普通代理首跳、冷启动残留和固定形态通知别名均已修好；但仍有两个可抵达网络/进程检查点的组合绕过，且自检与验收绑定存在实质缺口，因此不能通过。

除 Git 命令外，以下动态复现均以 `backend/` 为 cwd，使用：

`env PYTHONDONTWRITEBYTECODE=1 /Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/bin/python`

所有连接和进程均在 `socket.create_connection` 或 `subprocess.Popen` 前被检查墙截断。

## 发现

[HIGH] [backend/tests/regression/conftest.py:236](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/regression/conftest.py:236) — reload 自愈名单遗漏同样被守卫修改的 `subprocess`，属性式 `importlib.reload(subprocess)` 会拆掉层⑥，使预绑定通知别名抵达真实 spawn 层；复现：`python -c` harness 在布防前绑定 `daily_review_run.osascript_fallback`，布防后执行 `importlib.reload(subprocess)`，再将 `Popen` 换成墙并调用别名；观测 `RUN_GUARD_SURVIVED_SUBPROCESS_RELOAD False`、`ALIAS_AFTER_SUBPROCESS_RELOAD AssertionError:Popen checkpoint reached`、`POPEN_CHECKPOINT_COUNT 1`。

[HIGH] [backend/tests/regression/conftest.py:297](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/regression/conftest.py:297) — “预绑定 reload 后仍不出机”的声明不适用于守卫前已持有的显式代理 opener；复现：先构造代理为 `http://198.51.100.1:63128` 的 held opener，布防后用预绑定 reload 依次重载 `urllib.request`、`send_bark`，再对 `http://127.0.0.1:9/push` 调 `held.open()`；观测 `HELD_AFTER_PREBOUND_RELOAD_HOPS [('198.51.100.1', 63128)]`、`POST_RELOAD_PROXY_BYPASS_LOOPBACK False`。全局 `send_bark._urlopen` 路径仍是 `127.0.0.1:9`，失败的是 held-opener 组合声明。

[HIGH] [_bmad-output/审查/CARD-TEST-bark-autostub-R1-验收单.md:8](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/_bmad-output/审查/CARD-TEST-bark-autostub-R1-验收单.md:8>) — 验收单绑定到错误提交 `6518e5af`，该提交与当前 HEAD 是同父 sibling，且缺少当前关键的层⑤e；复现：`git rev-parse HEAD` 得 `919a9a48...`，`git show -s --format='%H %P' 6518e5af HEAD` 显示二者同父 `2cacbb0c...`，`git diff 6518e5af HEAD -- backend/tests/regression/conftest.py` 显示旧提交没有 `proxy_bypass` 补丁；验收单第 240 行仍是 `<回填最终 HEAD>`。

[MEDIUM] [backend/tests/regression/bark_egress_probe.py:212](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/regression/bark_egress_probe.py:212) — C′ 只把默认路径当作真实 key；若生产通过 `BARK_KEY_FILE` 使用自定义路径，卸甲探针会在第 213 行读取该真实文件；复现：在临时目录创建只含 loopback 假值的自定义 key，设置 `BARK_KEY_FILE` 后运行 `pytest -q -p no:cacheprovider --noconftest tests/regression/bark_egress_probe.py::test_keyfile_guarded`；观测 `CUSTOM_KEY_DISARMED_RC 0`、`1 passed`，证明内容确被读取。本复现未访问真实 key。

[MEDIUM] [backend/scripts/bark_negctl_report_plugin.py:83](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/bark_negctl_report_plugin.py:83) — 全局恢复快照没有覆盖守卫实际修改的全部状态，包括 `send_bark.KEY_FILE/_urlopen`、`daily_review_run.osascript_fallback`、两侧 `_get_proxy_settings` 和 `sys.path`；复现：取快照后改写上述对象再取快照，观测 `MODULE_GLOBALS_UNSEEN True`、`SCPROXY_SETTINGS_UNSEEN True`，另一轨同时改六项仍得到 `whole_snapshot_equal_after_6_guard_owned_changes True`。

[MEDIUM] [backend/scripts/bark_negctl_report_plugin.py:69](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/bark_negctl_report_plugin.py:69) — 已纳入快照的函数/opener 指纹也不是单射，不同对象或行为能得到相同值；复现：重载 `urllib.request` 后观测 `RELOAD_ID_CHANGED True`，但两个指纹均为 `urllib.request.urlopen` 且 `WHOLE_SNAPSHOT_EQUAL_AFTER_RELOAD True`；两个 `addheaders` 不同的 opener 则得到 `OPENER_FP_COLLISION True True`。

[MEDIUM] [backend/scripts/bark_r1_mutation_negative_controls.py:288](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/bark_r1_mutation_negative_controls.py:288) — 十三条变异的元裁判只要求 `rc != 0` 加输出包含 sentinel，仍可把基础设施错误或打印文本判作“指定门承重”；复现：在内存中将 `_apply/_restore` 换成无写入桩、令 `_run_negctl` 返回 `(4, "pytest infrastructure failed\nBARK-GATE-F-FIRSTHOP")` 后调用 `_check`；观测 `指定门变红=True`、`sentinel 命中=True`、`UNRELATED_RC_PLUS_TEXT_ACCEPTED True`。

[MEDIUM] [backend/tests/regression/conftest.py:371](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/regression/conftest.py:371) — 层⑥的 substring 判定既会静默吞掉非 osascript 命令，也会漏掉间接调用；复现：布防并设置 Popen 墙后，`subprocess.run(["/tmp/not-osascript-helper"])` 返回 rc 0 且 Popen 命中 0；`subprocess.run(["/usr/bin/env","osascript",...])` 则抵达 Popen 墙，观测 `DECOY_SWALLOWED 0`、`INDIRECT_OSASCRIPT_FORWARDED POPEN_WALL`。当前生产固定的 `/usr/bin/osascript` 形态能被正确拦截。

[MEDIUM] [backend/tests/regression/conftest.py:239](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/tests/regression/conftest.py:239) — 题设所举 `test_daily_review_pick.py` 实际不是未布防文件，并且 teardown 后仍留下模块导入副作用；复现：直接以模块名 `test_daily_review_pick` 驱动 fixture，观测 `PICK_CLASSIFIED_GUARDED True`，布防前模块集合为空，布防中出现 `send_bark/daily_review_run` 和临时 key，teardown 后 env/sys.path 已还原但两个模块仍留在 `sys.modules`。

[MEDIUM] [_bmad-output/审查/CARD-TEST-bark-autostub-R1-验收单.md:52](</Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/_bmad-output/审查/CARD-TEST-bark-autostub-R1-验收单.md:52>) — 验收单仍存在比证据宽的内部声明：第 23 行称三个探针均受保护，但 `_is_guarded_module("bark_unguarded_probe")` 实测为 `False`；第 52 行称每层均有“拆掉即红”证明，而第 160 行又承认⑤b、⑤d没有各自证伪门，M2/M4实际必须成组拆。

[LOW] [backend/scripts/bark_keyfile_residue_check.py:59](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/bark_keyfile_residue_check.py:59) — G 门把正确恢复到“父目录尚未创建”的合法自定义配置误报为临时残留；复现：`BARK_KEY_FILE=/tmp/codex-bark-audit-no-parent-919a9a48/key ...python scripts/bark_keyfile_residue_check.py`，内部 coldstart 为 `1 passed`，最终却 rc 1 并输出 `RESIDUE KEY_FILE 的父目录已不存在`。

[LOW] [backend/scripts/bark_autostub_negative_control.py:332](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2/backend/scripts/bark_autostub_negative_control.py:332) — 补充生产 frame 约束使用 `endswith()` 而非路径全等，同尾的其他模块也能满足；复现：`git show HEAD:backend/scripts/bark_autostub_negative_control.py | nl -ba | sed -n '328,334p'` 确认判定为 `c.endswith(needle)`；当前 B 跑的 `crash_path` 本身确实使用 realpath 全等，未复现当前 HEAD 的实际误判。

## 已核无发现

- `...python -m pytest -q -p no:cacheprovider tests/regression/test_daily_review_run.py`：`32 passed, 10 warnings`。

- `...python scripts/bark_autostub_negative_control.py`：`NEGATIVE-CONTROL: PASS (20/20 runs as expected)`；当前二十跑的红因均与 CASES 相符。

- 在 HEAD 的隔离 `git archive` 副本运行 `bark_r1_mutation_negative_controls.py`：`13/13` 均命中当前预期 sentinel，每次逐字节恢复并复算 sha256 一致；M9 实测旧文本判据为 `True`、新结构判据拒绝。上述 MEDIUM 指出的是元裁判仍可被其他 rc/文本组合欺骗。

- 正常布防下，守卫前环境代理、已 install opener 和局部持有 opener 的首跳均为 `('127.0.0.1', 9)`；卸甲 F′ 精确落到 `('127.0.0.1', 63128)`。

- 预绑定 reload 后依次重载 `urllib.request`、`send_bark`：`getproxies()=={}`、`_opener is None`、`send_bark._urlopen is urllib.request.urlopen`，生产全局路径首跳仍为 `('127.0.0.1', 9)`。失败的是上述 held-opener 组合。

- stale reload 在 teardown 后调用得到 `RuntimeError`，`send/load_key` 身份均保持 `True`；冷启动 teardown 后 `KEY_FILE` 恢复默认路径、临时文件不存在、env 恢复。

- 当前固定的预绑定 `osascript_fallback` 调用返回 `True` 且未抵达 Popen；H′ 卸甲形态精确抵达 Popen 墙。真正不匹配前缀的 U 探针为 PASS。

- 宿主当前系统代理在沙箱外实测为 `127.0.0.1:1082`，M5 当前确实命中 `_scproxy` 红因；非 Darwin 或系统代理为空的主机没有本轮动态证据，验收单已登记该平台边界。

- Probe import 确实会永久污染同一 pytest 进程的 env、opener、socket、Popen、sys.path；二十跑通过逐跑独立子进程避免跨跑污染，验收单第 164 行已登记主要边界。

- 最终 `git diff --exit-code HEAD -- <全部受审文件>` 为 0；`conftest.py` 与 probe 的工作树 sha256 分别与 `git show HEAD:` 完全一致。仅保留审计前已有的两份未跟踪 round-2 文件。

全程未运行两个被禁止的真实入口、未读取默认真实 key 内容、未写 live vault、未连接 Neo4j，也未修改受审文件。

VERDICT: FAIL


