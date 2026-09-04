你是对抗性代码审查者。目标：找出 CARD-TEST-bark-autostub-R1 的 BLOCKER/HIGH 缺陷。
**绿色测试输出不是证据**——本卡上一轮（第八批 round-3）的三条 HIGH 全部发生在「所有裁判都绿」的前提下。
你必须自己重放反例，而不是复述我贴的结论。

## 审查锚点

- 仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2`
- 分支 `card/w4-safety-r2`，审查对象 = 该分支当前 HEAD 的**已提交**内容（`git log -1`）。
- 起点 `2cacbb0c`（第八批 Bark 栈终态，round-3 判 FAIL）。本卡是它的整改轮。
- 只读工具链：`/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/bin/python`（Python 3.14.4）。
- 复现命令一律加 `PYTHONDONTWRITEBYTECODE=1`，cwd = 仓库的 `backend/`。

## ⛔ 绝对禁止

- 不得运行 `scripts/daily_review_run.py`、`scripts/daily-review-push.sh` 或任何真实推送入口——它们会真的向用户手机发 Bark 通知（`--now` 注入的 10:00+08:00 恒在推送窗内）。
- 不得读取 `~/.config/canvas-review/bark.key` 的**内容**（路径比较可以）。
- 不得写 live vault、不得连 Neo4j 7691、不得改任何被审文件。你的复现必须在子进程 / 临时目录里做。
- 若要做变异实验，串行、单次一处、逐字节还原并复算 sha256。

## 上一轮（round-3）判定 FAIL 的三条 HIGH（本卡声称已关闭）

1. **H2 stale wrapper 先 reload 后 raise**：`_guarded_reload` 先执行 `_real_reload(module)` 才检查 inactive flag，异常不回滚，模块已被重载。
2. **H1 loopback 可被代理转出机**：预绑定 reload 依次重载 `urllib.request` 和 `send_bark` 后，HTTP proxy 接管 `http://127.0.0.1:9/push`，socket 层首跳记到代理主机。
3. **H3 验收单绝对承诺**：无条件承诺「以后都只收到真实推送／不会再收到测试假通知」，与实际布防边界矛盾。

另有 MEDIUM：负控来源绑定可用 stdout 伪造绕过；冷启动 KEY_FILE 残留；`from daily_review_run import osascript_fallback` 预绑定别名不受层③保护；八跑不锁 loopback 内容。

## 本卡的完成条件与落点（请逐条证伪）

| 条件 | 声称落点 |
|---|---|
| (a) stale wrapper 在 real reload **之前**拒绝，两个生产 sentinel 均不生效 | `backend/tests/regression/conftest.py` `_guarded_reload`；门 = `bark_egress_probe.py::test_stale_reload_stash` + `::test_stale_reload_refused_before_reload`（负控跑 S/S'） |
| (b) 系统/环境代理与**已建 opener** 均不能把 loopback 请求转出机 | conftest 层⑤a/b/c/d；门 = `test_proxy_first_hop_stays_loopback`（两段：已建 opener + 现场新建 opener）与 `test_proxy_state_neutralized`（负控跑 F/F'、F2/F2'） |
| (c) 冷启动和 teardown 后 KEY_FILE 不残留失效临时路径 | conftest `env_key_file_before`（**setenv 之前**取值）；门 = `backend/scripts/bark_keyfile_residue_check.py` + `bark_coldstart_probe.py`（负控跑 G、CS/CS'） |
| (d) osascript 直接别名也在副作用前被拦；其它模块零副作用 | conftest 层⑥（`subprocess.run` 的 osascript 过滤器）；门 = `test_osascript_prebound_alias_blocked`（H/H'）与 `bark_unguarded_probe.py`（U） |
| (e) 负控按 traceback frame 和精确文件名绑定，不接受 stdout 伪造 | `backend/scripts/bark_negctl_report_plugin.py` + `bark_autostub_negative_control.py::_judge_pytest` |
| (f) 二十跑锁住 loopback 内容、代理首跳和 armed/disarmed 红因 | `bark_autostub_negative_control.py` 的 CASES；另有 `bark_r1_mutation_negative_controls.py` 十二条变异逐层证明门承重 |
| (g) UAT 收窄承诺 | `_bmad-output/审查/CARD-TEST-bark-autostub-R1-验收单.md` |

## 你必须亲手重放的反例（不重放就不算审过）

1. **代理向量**：在子进程里构造敌对代理前置态（env 代理 + `install_opener(build_opener(ProxyHandler({...})))`），布防形态下走一次 `send_bark.send` 或 `urllib.request` 的出网路径，在 `socket.create_connection` / `socket.getaddrinfo` 层记录**首跳 (host, port)**。任何一次首跳落在非 `127.0.0.1:9` 的地址 = HIGH。本机系统代理实测是 `127.0.0.1:1082`——只比 host 不比 port 会看不出差别。
2. **reload 逃逸链**：复现 round-3 的 `from importlib import reload` 预绑定形态；先 `reload(urllib.request)` 再 `reload(send_bark)`，然后检查 `getproxies()`、`urllib.request._opener`、`send_bark._urlopen`，并在 socket 层验证一次实际首跳。本卡声称此形态下 ②④ 会被抹掉但 ⑤a/⑤c 仍然有效因而「不出机」——请证伪这个声明。
3. **stale wrapper**：在布防期内取 `importlib.reload`，teardown 之后调用它，检查 `send_bark` 模块内 def 出来的函数对象（如 `send` / `load_key`）身份是否变化。身份变了 = 模块已被重新执行 = (a) 不成立。注意：只看 `KEY_FILE` / `_urlopen` 的值判不出来（新守卫会把它们重打成同样的值，本卡自己的变异 M7 首跑证伪过值断言版本）。
4. **预绑定 osascript 别名**：`from daily_review_run import osascript_fallback` 后调用，在 `subprocess.Popen` 层设墙检查是否有真实 spawn 抵达。
5. **KEY_FILE 残留**：找一条能让 `send_bark` 在守卫的 band 内首次加载的路径，检查 teardown 之后 `sys.modules["send_bark"].KEY_FILE`。
6. **判据本身**：尝试用 stdout 伪造欺骗 `bark_autostub_negative_control.py` 的判据（老判据的绕过形态已在 `bark_r1_mutation_negative_controls.py::M9` 复刻）。也请检查 `bark_negctl_report_plugin.py` 是否可被被测代码覆盖。
7. **模块门零副作用**：确认非布防的 regression 文件（如 `test_daily_review_pick.py`）在 fixture 生效时确实没有 import / sys.path / env 副作用。

## 重点怀疑面（请优先攻击）

- 层⑤ 的四件套里是否有**在本机恒真因而根本没被验证**的分支（例如非 darwin 路径）；声明的覆盖面是否宽于证据。
- `_reapply()` 被多次调用时 `pytest.MonkeyPatch` 的 undo 顺序是否真能把 `urllib.request._opener` / `subprocess.run` / `_scproxy` 恢复到 band 之前的值（**跨测试污染**）。本卡对此有一道门：插件在 collection 结束与 sessionfinish 各取一次八项全局快照，负控每一跑都比对。请攻击这道门本身——快照项是否覆盖了守卫实际改过的全部全局？指纹（`__module__.__qualname__` + ProxyHandler 的 proxies）是否可能两种状态同值？
- 层⑥ 用 `"osascript" in str(argv[0])` 判定：误判面（把别的命令当 osascript 吞掉）与漏判面（真 osascript 换个 argv 形态）各是什么。
- `bark_egress_probe.py` 在**模块 import 期**改 `os.environ` 和 `install_opener` —— 这个副作用会不会泄漏到别的测试/别的跑。
- 二十跑里是否有「红了但红错原因」的跑（本卡 CS' 首跑就是 `ModuleNotFoundError` 而非指定断言，已修）。
- 验收单里是否仍有比证据宽的承诺。

## 输出格式

先给一段结论（BLOCKER/HIGH/MEDIUM/LOW 各几条）。然后逐条发现，每条：
`[级别] <file>:<line> — <一句话缺陷> ；复现：<你实际跑过的命令与观测>`
再给「已核无发现」段（列出你验证过但没问题的点，含你实际跑的命令）。
最后单独一行 `VERDICT: PASS` 或 `VERDICT: FAIL`。

只报你亲自验证过的问题。推测请标 MEDIUM 以下并写明「未复现」。
