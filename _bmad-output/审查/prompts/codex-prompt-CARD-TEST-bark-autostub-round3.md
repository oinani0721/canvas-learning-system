# 独立对抗审查 round-3（终轮）— CARD-TEST-bark-autostub 整改复核

你是独立代码审查员。round-2 你（或前序审查）判 FAIL（3 HIGH + 3 MEDIUM + 4 LOW），开发者已整改。本轮核「整改是否成立 + 有无新引入缺陷」，是卡文允许的最后一轮。

⛔ 硬边界（用户真实机器）：
- 只读。禁止 Edit/Write/git 写。
- ⛔ 禁跑 scripts/daily_review_run.py、scripts/daily-review-push.sh、send_bark.py 真实入口（send 未替换 = 真推真机）。
- pytest 只允许跑 tests/regression/ 下文件，必须 -p no:cacheprovider，cwd=/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-micro/backend，解释器 .venv/bin/pytest。
- ⛔ 勿跑/勿读 backend/tests/api、backend/tests/unit 的测试文件——另一车道正在并行改造，它们的行为不代表本卡基线。
- 复现需要出网的场景时，必须用进程内捕获/拦截（如 patch urlopen 记录 URL），绝不真出网。

## round-2 发现 → 声称的整改落点（逐条核）

| # | round-2 发现 | 声称整改 | 落点 |
|---|---|---|---|
| H1 | reload 预绑定逃逸 → 合法假 key + 生产 _urlopen → 真出网 api.day.app | 假 key 内容改为整段 URL `http://127.0.0.1:9/bark-guard-fake-key-0001`（loopback discard 端口）——任何逃逸路径下 load_key 成功后最坏后果 = 对 127.0.0.1:9 发必被拒的请求，不出外网不触真 key；拒绝器仍是主承重层 | backend/tests/regression/conftest.py 假 key 写入处 + docstring ① |
| H2 | stale wrapper 逃逸：teardown 后调用留存的 reload wrapper 重挂已删 key 路径/跨测试污染 | fail-closed：flag=False（teardown 后）对受保护模块 reload 直接 raise RuntimeError，不再只做「真 reload」——teardown 后 reload 受保护模块必然产生生产态模块（真实 key 在位 + 真 urlopen），拒绝是唯一安全动作 | conftest.py `_guarded_reload` |
| H3 | 新推送测试文件默认 fail-open，与「任何人加新测试也不会真推」的绝对承诺冲突 | 声明面收窄：验收单目标段/用户段/裁判「不比什么」全部改为「test_daily_review* 前缀 + 探针精确名布防；其它文件不设防」的如实边界（卡文 (b) 本身就是单模块门，本实现是其最小扩展）；代码侧 docstring 已有同款边界声明 | 验收单 L21/L91/L102/L111 段 |
| M1 | 指定断言仅 stdout 子串匹配；C'/D'/E' 无行尾锚 | 三条 pattern 补全消息全文 + `\s*$` 行尾锚；新增**来源绑定**：`E ` 行前 1500 字符窗口必须含 src_hint（B→conftest.py，探针三条→bark_egress_probe.py），打印同文本却在别处失败不再满足 | backend/scripts/bark_autostub_negative_control.py CASES + `_judged` |
| M2 | `"error" not in body` 空操作；反向扫描可采伪摘要 | 摘要唯一性：全 stdout 形态匹配的摘要行必须恰 1 条（伪摘要→2 条→拒收）；`= ERRORS =` 段一律拒收 | `_summaries` + `_judged` |
| M3 | E/E' 只 reload send_bark，从 _PATCHED_MODULES 删 daily_review_run 八跑仍全绿 | E 门扩展为 reload **两个**受保护模块并断言两侧桩自愈（send_bark KEY_FILE/_urlopen + runner 的 send_bark.KEY_FILE + osascript_fallback qualname）；守卫漏 rearm daily_review_run 时 E 必红 | backend/tests/regression/bark_egress_probe.py `test_reload_selfheal` |
| L1 | send_bark.py:38 注释「行为零变化」过宽 | 措辞收窄为「生产路径常规行为不变；唯一可观察差异 = import 后对 urllib.request.urlopen 的重绑不再被本模块观察」 | scripts/send_bark.py:37-40 |
| L2 | conftest docstring「缺 key 会让 send 返回 0」错误 | ①段重写：send 返回 2 / runner.main 归并为 0，并描述 loopback 纵深语义 | conftest.py docstring |
| L3 | 验收单「非布防模块零 fixture 图变化」不准 | 收窄为「autouse fixture 与 request 依赖仍在 closure；变化是不再实例化 tmp_path/monkeypatch、不 import、不打桩」 | 验收单裁判 4「不比什么」 |
| L4 | 注释「裁决点 2」应为 5 | 复核：当前 conftest.py 内唯一裁决点引用已是「裁决点 5」（round-2 看到的 L203 与现文件行号漂移）；如仍有错指请指出 | conftest.py:208 |

## 审查要求

1. 逐条核上表：整改是否真实落地（file:line）、是否解决了原发现、是否**引入新缺陷**（特别是：H1 的 loopback key 是否改变了负控各跑的语义？H2 的 raise 会不会误伤合法路径？M1 来源绑定窗口 1500 字符会不会过窄/过宽？M3 扩展后 E' 的 pattern 与实际首条失败断言是否一致？）。
2. 你 round-2 复现过的场景（预绑定 reload 逃逸、stale wrapper、伪摘要注入），按整改后代码重新推演/复现，给出新结果。
3. 声明一致性：验收单 `_bmad-output/审查/CARD-TEST-bark-autostub-验收单.md` 当前版本（可能刚更新，以你读到的为准）与代码事实是否逐字相符；若仍读到绝对化承诺（如「不会再真推」无条件版）即为缺陷。
4. 全局负面清单：整改后的八跑负控（backend/scripts/bark_autostub_negative_control.py，可运行）是否存在新的假绿形态；conftest 四层防线是否存在新的绕过形态（在你 round-2 已知形态之外）。

## 输出格式

每条发现一行：`[BLOCKER|HIGH|MEDIUM|LOW] file:line — 缺陷 + 复现/证据`。
明确核过但无问题的项列「已核无发现」清单（对应上表编号）。
末行必须 `VERDICT: PASS` 或 `VERDICT: FAIL`（存在 BLOCKER/HIGH 即 FAIL）。
