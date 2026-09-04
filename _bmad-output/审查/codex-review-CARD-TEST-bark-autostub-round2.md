结论：round-2 仍有 3 个 HIGH，不能通过。32 条回归与八跑虽然全绿，但存在可复现的真实外发绕过和跨测试假绿。

### 发现

[HIGH] [backend/tests/regression/conftest.py:224](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/tests/regression/conftest.py:224) — collection 期预绑定的 `from importlib import reload` 可绕过属性补丁；reload 后合法假 key 仍存在而 `_urlopen` 恢复生产出口。安全复现中调用 `send()` 得到 `captured=['https://api.day.app/push']`、rc=0；去掉内存捕获器即真实外发通知内容。

[HIGH] [backend/tests/regression/conftest.py:256](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/tests/regression/conftest.py:256) — `_guarded_reload` 闭包可逃逸至 teardown 后并复用已 `undo()` 的旧 `MonkeyPatch`，永久重挂已删除的旧 key 路径，重新打开静默 rc=2 假绿。复现：保存守卫期 `importlib.reload`→fixture 结束→调用旧 wrapper；实测 `KEY_FILE.exists()==False` 且旧拒绝器被重挂，八跑因每案独立子进程看不到此污染。

[HIGH] [backend/tests/regression/conftest.py:233](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/tests/regression/conftest.py:233) — 未枚举的新推送测试文件默认 fail-open，与验收单“以后任何人加新测试也不会真推”的核心承诺直接冲突。复现：新增 `test_daily_review_push.py`，模块门立即早退，三层均保持生产值；验收单后文声明边界不能抵消前文绝对保证。

[MEDIUM] [backend/scripts/bark_autostub_negative_control.py:80](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/scripts/bark_autostub_negative_control.py:80) — 指定断言仍只是 stdout 文本匹配，没有绑定真实异常来源；测试打印目标 `E   AssertionError...` 后因无关原因失败即可假绿，且 C'/D'/E' 正则没有行尾锚。合成 rc=1 输出已得到 `body='1 failed', shape=True, regex=True`。

[MEDIUM] [backend/scripts/bark_autostub_negative_control.py:52](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/scripts/bark_autostub_negative_control.py:52) — `"error" not in body` 在前置 fullmatch 后是空操作，也不检查完整输出；插件或 `atexit` 在真实 error 摘要后追加伪 `1 failed` 摘要，会被反向扫描优先采用。

[MEDIUM] [backend/tests/regression/bark_egress_probe.py:133](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/tests/regression/bark_egress_probe.py:133) — E/E' 只 reload `send_bark` 并检查 KEY_FILE/_urlopen，没有 reload `daily_review_run` 或检查 fallback，不能证明验收单所称“两生产模块、三层自愈”。从 `_PATCHED_MODULES` 删除 `daily_review_run`，现有八跑仍可全绿。

[LOW] [scripts/send_bark.py:38](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/scripts/send_bark.py:38) — 注释仍保留“行为零变化”；导入后重绑 `urllib.request.urlopen` 时，冻结的 `_urlopen` 不会观察该变化，L2 措辞未真正收窄。

[LOW] [backend/tests/regression/conftest.py:211](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/tests/regression/conftest.py:211) — docstring 称缺 key 会让 `send` 返回 0，但 `send_bark.py:93-96` 实际返回 2；只有上层 runner 可能归并为 0。

[LOW] [_bmad-output/审查/CARD-TEST-bark-autostub-验收单.md:102](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/_bmad-output/审查/CARD-TEST-bark-autostub-验收单.md:102) — “非布防模块零 fixture 图变化”仍不准确；autouse fixture 与 `request` 依赖依然加入 closure，只是已移除 `tmp_path/monkeypatch`。

[LOW] [backend/tests/regression/conftest.py:203](/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/tests/regression/conftest.py:203) — 注释指向验收单“裁决点 2”，实际模块枚举边界位于裁决点 5。

### Round-1 九项复核

- H1：已整改。真实合法假 key、环境变量重定向和拒绝器均落地；正常路径 B 门响亮失败。
- H2：已整改。独立 `MonkeyPatch` 与正常逆序 teardown 有效，测试自己的 `undo()` 不会拆守卫。
- H3：部分整改。生产模块名判断已修正，属性式成功 reload 会重打；但预绑定绕过及 stale-wrapper 生命周期回归仍是 HIGH。
- M1：部分整改。rc、摘要、超时及八跑均落地，但异常来源与伪摘要仍可假绿。
- M2：部分整改。`endswith` 已替换为末段精确枚举；新文件默认漏防仍与核心承诺冲突。
- L1：部分整改。重依赖已移除、临时目录正确清理，但“零 fixture 图变化”仍是假声明。
- L2：部分整改。验收单已写明 import-time 边界，但源文件仍称“行为零变化”。
- L3：已整改。DNS 与建连双墙均存在，代理清理边界如实声明。
- L4：已整改。`:138/:140` 与当前 `send_bark.py` 行号一致。

### 验证与审查面

- `test_daily_review_run.py`：`32 passed, 10 warnings in 0.77s`。
- 八跑负控：全部按预期，脚本 exit 0、末行 `NEGATIVE-CONTROL: PASS`。
- R2 正常独立 MonkeyPatch teardown：无发现；发现集中在 wrapper 逃逸生命周期。
- R3：存在上述两个判据假绿面。
- R4：headline、E/E' 证明范围、fixture 图和裁决点引用均有声明差。
- R5：已枚举模块的末段匹配无额外问题；未枚举新文件默认漏防构成 HIGH。
- 4-A #3–#6 因“只读六文件”范围未独立复跑，不能把验收单自报结果升级为本轮确认。

VERDICT: FAIL


