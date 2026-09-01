请对一段**测试隔离代码**做严格的代码复核。

## 背景（这段代码是干什么的）

这是一个个人学习工具（本地跑的每日复习提醒）。它的测试套件会调用真实的推送函数，
如果测试忘了打桩，就会真的往作者本人的手机上发一条假的复习提醒，并且可能弹出一个
macOS 桌面通知。为了避免这种事故，仓库里加了一个 pytest fixture 守卫：在指定的几个
测试文件运行期间，把推送出口、通知出口和代理配置临时换成安全值，测试结束后原样还原。

你的任务是复核**这个守卫是否真的做到了它声称的事**，以及**它自带的那些检查是不是
真的能发现问题**。这是防御性工作：目的是让测试更不容易误发通知，不是让它更容易发。

## 复核对象

- 仓库：`/Users/Heishing/Desktop/canvas/canvas-learning-system/.claude/worktrees/card-w4-safety-r2`
- 分支 `card/w4-safety-r2`，复核对象 = 该分支当前 HEAD 的已提交内容（`git log -1`）。
- 只读工具链：`/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/bin/python`（3.14.4）。
- 复现命令一律加 `PYTHONDONTWRITEBYTECODE=1`，cwd = 仓库的 `backend/`。

主要文件：
- `backend/tests/regression/conftest.py` 的 `_bark_egress_guard`（守卫本体，六层）
- `backend/tests/regression/bark_egress_probe.py` / `bark_coldstart_probe.py` / `bark_unguarded_probe.py`（自检探针）
- `backend/scripts/bark_autostub_negative_control.py`（二十跑裁判）
- `backend/scripts/bark_negctl_report_plugin.py`（结构化报告插件）
- `backend/scripts/bark_keyfile_residue_check.py`（残留检查）
- `backend/scripts/bark_r1_mutation_negative_controls.py`（十三条变异，验证每道门承重）
- `_bmad-output/审查/CARD-TEST-bark-autostub-R1-验收单.md`（声明与边界）

## ⛔ 运行限制

- 不要运行 `scripts/daily_review_run.py`、`scripts/daily-review-push.sh` 或任何真实推送入口——它们会真的发通知。
- 不要读取 `~/.config/canvas-review/bark.key` 的内容（比较路径可以）。
- 不要写 live vault、不要连 Neo4j 7691、不要修改任何被复核的文件。复现请在子进程或临时目录里做。
- 若要做变异实验：串行、单次一处、逐字节还原并复算 sha256。

## 上一轮遗留的三个问题（本轮声称已解决，请复核）

1. 守卫结束后残留的模块重载入口，旧实现是**先执行重载、再抛异常**，异常不回滚，模块已被重载。
2. 「只连本机」的兜底地址在有代理时会被代理转走，请求因此离开本机。
3. 验收文档把保护范围说得比实际大。

上一轮还有几个次要问题：判据只看文本输出因而不可靠；冷启动时临时 key 路径会残留；
`from daily_review_run import osascript_fallback` 这种提前绑定的别名不受保护；自检没有锁住兜底地址的内容。

## 本轮的声明与落点（请逐条独立验证，不要只读测试输出）

| 声明 | 落点 |
|---|---|
| (a) 守卫结束后残留的重载入口，在**执行重载之前**就拒绝 | `conftest.py` 的 `_guarded_reload`；自检 S/S' |
| (b) 系统代理、环境变量代理、以及已经构建好的 opener（含别处持有引用的），都不会把本机地址的请求转走 | 层⑤a–⑤e；自检 F/F'、F2/F2' |
| (c) 冷启动与结束后，`send_bark.KEY_FILE` 不残留失效的临时路径 | `env_key_file_before`（取值在 `setenv` 之前）；自检 CS/CS' 与 G |
| (d) 提前绑定的 `osascript_fallback` 别名在产生副作用之前被拦；未布防的模块零副作用 | 层⑥；自检 H/H' 与 U |
| (e) 判据按 traceback frame 与精确文件名绑定，不采信被测进程打印的文本 | `bark_negctl_report_plugin.py` + `_judge_pytest` |
| (f) 二十跑锁住兜底地址内容、首跳目标与放行/篡改两侧的红因 | `bark_autostub_negative_control.py` 的 CASES |
| (g) 验收文档收窄承诺 | 验收单 |


## 上一轮（round-2）的十二条发现与本轮的闭合声明（请逐条证伪）

上一轮判 FAIL（0 BLOCKER / 3 HIGH / 7 MEDIUM / 2 LOW）。本轮声称全部关闭或如实登记。**声明本身就是被审对象**：

| 上一轮发现 | 本轮声称 | 请你复核 |
|---|---|---|
| HIGH `reload(subprocess)` 冲掉层⑥ | reload 名单改为「守卫打过桩的全部模块」，补 `subprocess`/`_scproxy`/`importlib`；`importlib.reload` 的打桩也进了 `_reapply` | 还有没有别的被守卫改过、却不在名单里的模块？名单里的每一个 reload 之后，六层是不是真的都回来了？ |
| HIGH 预绑定 reload 之后握持的 opener 走代理出机 | ⑤c 的 proxy settings 存根语义改为「一切主机都绕过代理」；新增 R 门，判据锚机外地址 `198.51.100.1:63128` | 请重跑你上一轮那条链，并换别的代理形态（https、SOCKS、带认证、`no_proxy` 已设）再试 |
| HIGH 验收单绑错提交 | SHA 由随后的 docs commit 回填 | 核对验收单里的 SHA 与最终 HEAD |
| MEDIUM C' 会读自定义位置的真实 key | `REAL_KEY` 改为在守卫改环境变量之前取值 | 换 `BARK_KEY_FILE` 再试 |
| MEDIUM 全局快照覆盖不全 | 补模块属性、两侧 `_get_proxy_settings`、`proxy_bypass`、opener 的 `addheaders` | 还有哪些守卫改过的状态不在快照里？ |
| MEDIUM 指纹不是单射 | opener 指纹补 `addheaders`；函数指纹**刻意**保持语义级（`module.qualname`），登记为设计取舍 | 这个取舍在验收单里写清楚了吗？还有别的碰撞形态吗？ |
| MEDIUM 变异元裁判可被无关 rc+文本骗过 | 要求 rc 恰为 1、输出含 `NEGATIVE-CONTROL: FAIL`、且**指定的那道跑**自己判 `ok=False` | 还能骗过吗？ |
| MEDIUM 层⑥ substring 既误吞又漏判 | 改为扫整条 argv 按 basename 全等；H 门加双向断言，变异 M16/M17 各盯一面 | 还有别的形态（shell=True、包装脚本、`sh -c`）吗？这些是否已如实登记为边界？ |
| MEDIUM `test_daily_review_pick.py` 其实是布防文件 | 验收单已纠正；U 跑才是未布防零副作用的证据 | 验收单现在的说法准确吗？ |
| MEDIUM 验收单内部自相矛盾 | §🎯 与 4-A 抬头、「不比什么」表都已收窄 | 还有比证据宽的说法吗？ |
| LOW G 门误报合法自定义配置 | 父目录检查只在「路径本来就不对」时才补报 | |
| LOW frame 约束用 `endswith` | 改为还原绝对路径后全等 | |

另请注意本轮新增的一个判据豁免：负控里 `R'`（卸甲）单跑标了 `globals_may_drift=True`——理由是卸甲形态下该测试自己会真重载 `urllib.request` 而没有守卫去还原。请判断这个豁免是否被滥用（它会不会掩盖别的问题），以及豁免范围是否精确。

## 请你亲手复算的场景（只读结论不算复核）

1. **首跳目标**：在子进程里构造「守卫布防之前就存在的代理配置」（环境变量 + 已 `install_opener` 的 opener + 一个只被局部变量持有的 opener），布防状态下各走一次出网路径，在 `socket.create_connection` / `socket.getaddrinfo` 层记录**首跳 (host, port)**。首跳应当恒为 `('127.0.0.1', 9)`。注意本机系统代理实测是 `127.0.0.1:1082`，与兜底目标同主机不同端口——只比 host 看不出差别。
2. **模块重载路径**：用 `from importlib import reload` 提前绑定的形式，依次 `reload(urllib.request)` 与 `reload(send_bark)`，然后检查 `getproxies()`、`urllib.request._opener`、`send_bark._urlopen`，并在 socket 层实测一次首跳。验收单声称此形态下 ②④ 会失效但 ⑤a/⑤c 仍然有效因而请求不离开本机——请验证这个说法。
3. **残留的重载入口**：在布防期内取 `importlib.reload`，结束之后再调用它，检查 `send_bark` 里 `def` 出来的函数对象（`send` / `load_key`）身份是否变化。身份变了说明模块已被重新执行，(a) 不成立。注意只看 `KEY_FILE` / `_urlopen` 的值判不出来（新一轮守卫会把它们重打成同样的值）。
4. **提前绑定的通知别名**：`from daily_review_run import osascript_fallback` 之后调用，在 `subprocess.Popen` 层设检查点，看是否有真实进程启动抵达那里。
5. **临时 key 残留**：找一条能让 `send_bark` 在守卫布防期内首次加载的路径，检查结束之后 `sys.modules["send_bark"].KEY_FILE`。
6. **判据可靠性**：检查 `bark_autostub_negative_control.py` 的判定是否可能被被测进程的打印内容影响；`bark_negctl_report_plugin.py` 是否可能被被测代码覆盖。
7. **未布防模块**：确认非布防的 regression 文件（如 `test_daily_review_pick.py`）在 fixture 生效时确实没有 import / `sys.path` / 环境变量副作用。
8. **还原对账**：守卫一次测试里可能反复调用 `_reapply`。请检查插件的八项全局快照是否覆盖了守卫实际改过的全部全局，指纹（`__module__.__qualname__` + ProxyHandler 的 proxies）是否可能在两种不同状态下取到同一个值。

## 重点怀疑面

- 层⑤ 的五件套里是否有**在本机恒真因而根本没被验证**的分支（例如非 darwin 路径）；声明的覆盖面是否宽于证据。
- `pytest.MonkeyPatch` 多次 `setattr` 之后，`undo` 顺序是否真能把 `urllib.request._opener` / `proxy_bypass` / `subprocess.run` / `_scproxy` 恢复到布防之前的值。
- 层⑥ 用 `"osascript" in str(argv[0])` 判定：误判面（把别的命令当成它吞掉）与漏判面（同一个程序换个 argv 形态）各是什么。
- `bark_egress_probe.py` 在**模块 import 期**改环境变量、`install_opener`、并替换三个 socket/subprocess 原语。这些副作用会不会波及别的测试或别的跑。
- 二十跑里是否有「红了但红错原因」的跑。
- 验收单里是否仍有比证据宽的承诺。

## 输出格式

先给一段结论（BLOCKER/HIGH/MEDIUM/LOW 各几条）。然后逐条发现，每条：
`[级别] <file>:<line> — <一句话问题> ；复现：<你实际跑过的命令与观测>`
再给「已核无发现」段（列出你验证过但没问题的点，含你实际跑的命令）。
最后单独一行 `VERDICT: PASS` 或 `VERDICT: FAIL`。

只报你亲自验证过的问题。推测请标 MEDIUM 以下并写明「未复现」。
