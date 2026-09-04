# 独立对抗审查 — CARD-TEST-bark-autostub（daily_review_run 测试套件推送打桩完备性）

你是独立代码审查员，审查一张测试基建卡：给每日复习推送脚本的测试套件加自动打桩防线，防止测试运行时向用户手机发送真实推送通知。请裁定改动是否真正达成其声明的保证。

只读以下文件（绝对路径，全部在同一 worktree 内）：

改动/新增面（本卡产物）：
1. /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/scripts/send_bark.py — 新增模块级别名 `_urlopen = urllib.request.urlopen` 作为唯一网络出口缝，:128 调用点改用该缝
2. /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/tests/regression/conftest.py — 末尾新增 autouse fixture `_bark_egress_guard`（三层防线 + 模块门）
3. /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/tests/regression/test_daily_review_run.py — `_capture_bark_request` 改 patch `send_bark._urlopen`（原来 patch 全局 urllib.request.urlopen）
4. /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/tests/regression/bark_egress_probe.py — 新增探针（不带 test_ 前缀，仅由负控脚本显式 nodeid 调起）
5. /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend/scripts/bark_autostub_negative_control.py — 新增 A/B 双跑负控裁判脚本

上下文参考（本卡零改动，勿提改它们的建议）：
6. /Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/scripts/daily_review_run.py — 生产 runner（:250 调 send_bark.send；:267-272 失败走 osascript_fallback）

## 声明的保证（逐条裁定 真/假，给 file:line 证据）

- G1: send_bark.py 的改动零行为变化——`_urlopen` 在 import 时与 `urllib.request.urlopen` 绑定同一函数对象，生产路径语义不变；除该缝外 send_bark.py 无任何其它改动。
- G2: autouse 守卫使「在 test_daily_review_run.py 新增一条调 runner.main() 的测试而忘打桩」的默认后果从真实推送变为测试响亮失败。两层：① KEY_FILE 重定向到 tmp 下不存在的路径（send 走 rc=2 分支，不进网络重试循环）；② `_urlopen` 拒绝器抛 `AssertionError("Bark egress attempted in tests")`，且该异常类型不被 send_bark.py 的 except 子句（:138 HTTPError / :140 URLError,TimeoutError,OSError）捕获，必然穿透 send 与 runner.main 使测试失败。
- G3: 守卫布防的模块内，`daily_review_run.osascript_fallback` 已打桩为记录+返回 True，不再 subprocess 弹真 macOS 通知。
- G4: 模块门（`request.module.__name__.endswith(("test_daily_review_run", "bark_egress_probe"))`）对其余 ~45 个 regression 测试文件零副作用：不 import scripts 模块、不动 sys.path、不 patch 任何东西。
- G5: 负控脚本核的是指定的那道断言（B 跑输出须含 `AssertionError: Bark egress attempted in tests` 且 `1 failed`），而非「有任何失败」；A 跑核 `1 passed` 而非仅 rc==0（rc==5 未收集也非 0，但不算证明）。
- G6: 探针在有守卫与无守卫两种形态下都不产生真实网络连接：无守卫时 `socket.getaddrinfo` 拦截器记录 host 并抛 gaierror（连接在 DNS 层断掉）；有守卫时拒绝器在 DNS 之前抛断言。探针另 patch `urllib.request.getproxies` 为空 + 清代理 env（本机有系统代理，否则首跳解析记到的是代理主机 127.0.0.1 而非 api.day.app，断言锚点失配）。

## 对抗审查重点（逐条给结论）

- R1: 守卫是否可被 `--noconftest` 以外的方式意外绕过——例如某测试经不同 sys.path 项 import 出第二个 send_bark 模块对象，令守卫 patch 的对象与被测代码实际调用的对象不是同一个（注意 conftest 守卫用 `syspath_prepend(仓根/scripts)` 后 import，test_daily_review_run.py 与探针自己也各有 `sys.path.insert(0, WT/"scripts")`——判断这些路径是否恒指同一模块实例）。
- R2: 拒绝器 AssertionError 被吞掉的任何路径（send_bark 内、runner 内、pytest 层）。
- R3: 真弹 macOS 通知的残余路径：守卫模块内、探针 A 模式（--noconftest 时守卫不在，探针自己 patch osascript_fallback 是否足够）、负控子进程内。
- R4: 负控的假绿形态：探针文件未被收集（rc=5）、收集错误、探针里别的断言失败恰好也含相同字符串、A/B 判据可被非预期路径满足。
- R5: 模块门 endswith 双模块元组的误伤/漏防形态（其它 regression 文件名、future 文件名）。
- R6: 任何「注释/docstring/判据声明比它实际证明的宽」之处（例如声称"唯一网络出口"是否属实——send_bark.py 内是否还有其它出网路径；声称"零副作用"是否被 fixture 参数 tmp_path/monkeypatch 的实例化打破）。

## 输出格式

每条发现一行：`[BLOCKER|HIGH|MEDIUM|LOW] file:line — 一句话缺陷 + 一句复现思路`。
无发现的审查面明确写「R# 无发现」。
末行必须是 `VERDICT: PASS` 或 `VERDICT: FAIL`（存在 BLOCKER/HIGH 即 FAIL）。
