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


## 上一轮（round-3）的十三条发现与本轮的闭合声明（请逐条证伪）

上一轮判 FAIL（0 BLOCKER / 3 HIGH / 9 MEDIUM / 1 LOW）。本轮声称全部关闭或如实登记。**声明本身就是被审对象**——凡写「已修」的，请你亲手复现上一轮那条反例，看它现在是不是真的红不了了；凡写「登记不修」的，请检查登记的措辞有没有比证据宽。

| 上一轮发现 | 本轮声称 | 请你复核 |
|---|---|---|
| HIGH 代理变量按固定大小写清单删除，`Http_Proxy` 残留，预绑定 reload 后走机外代理 | 改为「所有 `lower()` 后以 `_proxy` 结尾的 env」，与 `getproxies_environment()` 同口径；探针 import 期新增 `Http_Proxy` 敌对前置态；F2 断言改为归一化判定；变异 M18 | 请重跑你上一轮那条 `Http_Proxy` 反例；再试别的形态（`HTTP_proxy`、`hTtPs_PrOxY`、带认证、`No_Proxy` 已设） |
| HIGH `_reapply()` 只在 reload 正常返回后执行，半途异常留下失防模块 | 重打挪进 `finally`；新增 X/X' 门（patch loader **类**的 `exec_module` 复刻「先真执行、再抛」）；变异 M19 | 请重跑你上一轮的 trace 中断复现；也试试在 `_find_spec` 阶段失败、以及 reload 其它名单内模块时失败 |
| HIGH 验收单绑错提交、文末仍是占位符 | 由 docs commit 一次性回填代码终态 SHA，并列明三轮审查各自锚定的提交 | 核对验收单 frontmatter 与技术段的 SHA 是否等于代码终态提交 |
| MEDIUM 层⑥ 扫整条 argv 误吞数据参数；漏 bytes / `executable=` / shell 形态 | 收窄为「`argv[0]` basename 全等」或「`argv[0]` 是 `env` 转发时的首个非赋值参数」；bytes 走 `os.fsdecode`；H 门加两个误吞面断言；shell/`executable=`/`sh -c`/包装脚本**明确登记为不覆盖** | 还有别的既不误吞又该拦的形态吗？登记的边界列全了吗？ |
| MEDIUM E 门的 `reload(subprocess)` 冲掉探针 Popen 总账 | E 门与 X 门在 reload 之后立即补装总账 | 本进程内还有别的路径能把三个总账原语冲掉而无人补装吗？ |
| MEDIUM `_judge_pytest` 不限制 pytest 正常 rc | 新增「进程 rc 必须等于本跑期望的 0/1」 | 还能用别的 rc 组合骗过吗？ |
| MEDIUM 变异元裁判把 sentinel 当输出任意位置的文本 | sentinel 只在裁判自产的行里找：指定跑的 `CRASH` 行（来自异常对象）与 `✗` 问题行；G 跑红因也复述成 `✗` 行 | 请再试一次你上一轮那个「print 一行 sentinel + 无关失败」的构造 |
| MEDIUM 全局还原对账漏 `sys.path`；冷启动模块属性不在覆盖内 | 快照补「守卫那个**确切** scripts 目录在 `sys.path` 中的出现次数」（不能按 `/scripts` 后缀数——生产代码会插 vault 的 `.claude/scripts`）；冷启动模块属性归 G 门，G 门新增 `_urlopen` / `osascript_fallback` 两条断言 | 还有哪些守卫改过的状态既不在快照里、也不在 G 门里？ |
| MEDIUM `R'` 整份跳过快照 | 豁免改为按**键**给（`globals_drift_allow=("opener",)`） | 这个豁免还会盖住别的漂移吗？ |
| MEDIUM opener 指纹仍非行为单射（CookieJar） | **不修**：指纹是状态级不是行为级；验收单已把「碰撞已关闭」收窄为「关掉了 `addheaders` 这一类，handler 内部状态不在覆盖内」 | 收窄后的措辞还有没有比证据宽？ |
| MEDIUM F 门第三段承重层描述错误、引用了已删的 M13 | 按实际重写（⑤c/⑤e 在 darwin 互为冗余） | 现在的描述与代码一致吗？ |
| MEDIUM U 门覆盖不足 | 改为整份 `sys.path` 列表比对 + 全部 `*_proxy` 键的字典比对 | 还能造出 U 门看不见的未布防污染吗？ |
| LOW G 门误报合法自定义路径 | 痕迹检查只在「路径本来就不对」时才补报 | |

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
