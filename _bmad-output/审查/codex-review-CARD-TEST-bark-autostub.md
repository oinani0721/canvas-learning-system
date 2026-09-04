保证裁定：

G1: 真（常规生产路径）— `scripts/send_bark.py:40,128`；diff 仅新增别名并替换调用点。绝对“零行为变化”有 LOW 限定，见下。

G2: 假 — `conftest.py:232` 使 `send_bark.py:94-96` 先返回 2，`daily_review_run.py:260-279` 最终仍返回 0；内存复现得到 `push:skip-nokey fallback:ok`。

G3: 真（正常 fixture 生命周期）— `conftest.py:239-245` 覆盖 `daily_review_run.py:267-272` 的唯一 fallback 调用；绕过形态见 R1。

G4: 假（“零副作用”绝对表述）— `conftest.py:205` 的依赖会在 `:223` 模块门前实例化；狭义“不导入 scripts、不改 sys.path、不 patch”成立。

G5: 假（作为“指定断言来源”的证明）— `bark_autostub_negative_control.py:39,42` 仅匹配 stdout 子串；rc=5/纯收集错误会被拒绝，但额外错误或同文字符串碰撞可假绿。

G6: 真（核心无真实连接）— A 在 `bark_egress_probe.py:51-55` 阻断 DNS、`:69-71` 阻断本地通知；B 在 `conftest.py:234-237` 更早拒绝。其“强制直连”附属表述不绝对。

[HIGH] backend/tests/regression/conftest.py:232 — 缺失 `KEY_FILE` 令忘打桩的 `runner.main()` 在触达拒绝器前正常返回，核心“默认响亮失败”保证不成立。复现：窗口内构造 notification、仅断言 `runner.main() == 0`，实际得到 rc=0。

[HIGH] backend/tests/regression/conftest.py:205 — 守卫与测试共用同一个 `monkeypatch` 实例，测试调用 `monkeypatch.undo()` 会一次撤销 KEY、网络和 osascript 三层防线。复现：在 guarded test 中先 `monkeypatch.undo()`，再调用有效推送路径即可恢复真实出口。

[HIGH] backend/tests/regression/conftest.py:229 — 补丁只附着于当前模块状态，`importlib.reload(runner.send_bark)` 会恢复生产 `KEY_FILE` 与 `_urlopen`，`reload(runner)` 会恢复真实 osascript。复现：fixture 生效后 reload 对应模块；内存检查显示相关守卫均被覆盖。

[MEDIUM] backend/scripts/bark_autostub_negative_control.py:42 — B 判据不要求 rc==1、无额外 error 或拒绝文本来自目标 traceback，因此不是精确裁判。复现：令 B stdout 为拒绝文本加 `1 failed, 1 error`，脚本仍返回 0 并宣告 PASS。

[MEDIUM] backend/tests/regression/conftest.py:201 — 裸 `endswith` 既会误伤 `foo_test_daily_review_run`，也会漏防常见的未来拆分名 `test_daily_review_run_cli`。复现：以这两个模块名放置同一 `runner.main()` 测试，前者布防、后者不布防。

[LOW] backend/tests/regression/conftest.py:205 — 无关 regression 测试仍会解析 `monkeypatch`、创建 `tmp_path` 并改变 fixture 图，“零副作用”不成立。复现：在无关模块覆写 `tmp_path` 为抛错 fixture，即使测试未请求它也会失败。

[LOW] scripts/send_bark.py:40 — import 时冻结别名不再观察之后对 `urllib.request.urlopen` 的 tracing/rebind，因此绝对“零行为变化”过宽。复现：import 后替换全局 `urlopen`，`send_bark._urlopen` 仍是旧对象。

[LOW] backend/tests/regression/bark_egress_probe.py:60 — 清代理环境并 patch `getproxies` 不会重建已缓存的 `urllib.request._opener`，“强制直连”并非恒真。复现：预装指向 `127.0.0.1` 的 ProxyHandler 后，DNS 哨兵记录的是 `127.0.0.1`；连接仍被安全阻断。

[LOW] backend/tests/regression/conftest.py:213 — docstring 的异常行号 `send_bark.py:134/:136` 已漂移，实际为 `:138/:140`。复现：按注释定位会落到成功判断而非 except。

R1: 当前三处 `WT/scripts` 裸导入会命中同一 `sys.modules` 对象，无 sys.path 导致的第二实例；但存在上述 `undo`/reload 高危绕过。

R2 无发现：`AssertionError` 不属于 `send_bark.py:138-141` 的捕获类型，runner 的广义捕获只包围 `ensure_payload`，不会吞发送异常。

R3: 标准 guarded/A/B 路径无新增残余；R1 的撤桩与 reload 绕过同时适用于真实 Bark/macOS 通知面。

R4: 存在负控子串判据假绿；rc=5 和纯收集错误本身不会假绿。

R5: 存在 suffix 误伤与未来文件漏防。

R6: 存在零行为、零副作用、强制直连及行号声明过宽；`send_bark.py` 内唯一实际网络调用点仍为 `:128`。

VERDICT: FAIL


