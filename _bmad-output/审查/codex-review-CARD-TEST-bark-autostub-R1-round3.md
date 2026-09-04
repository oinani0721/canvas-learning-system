结论：**0 BLOCKER / 3 HIGH / 9 MEDIUM / 1 LOW**。常规布防路径大多有效，但混合大小写代理可造成机外首跳，reload 半途异常可冲掉通知拦截；验收单也仍未绑定当前 HEAD，因此判定 FAIL。

下文 `$PY` 指 `/Users/Heishing/Desktop/canvas/canvas-learning-system/backend/.venv/bin/python`；Python/pytest 均在 `backend/` 下运行并设置 `PYTHONDONTWRITEBYTECODE=1`。

## 发现

[HIGH] `backend/tests/regression/conftest.py:219` — 代理变量按固定全小写/全大写名称删除，Python 仍会识别的 `Http_Proxy`/`No_Proxy` 可残留；预绑定真 reload 后请求会重新走机外代理；复现：隔离 `python -c` 布防前设置 `Http_Proxy=http://user:pass@198.51.100.1:63137`、`No_Proxy=example.invalid`，随后预绑定 `reload(urllib.request)`、`reload(send_bark)`，在 `socket.getaddrinfo` 墙记录到 `AUDIT_MIXED_CASE ... "first_hop": ["198.51.100.1",63137]`，`getproxies()` 也返回该代理；没有真实建连。

[HIGH] `backend/tests/regression/conftest.py:454` — `_reapply()` 只在 `_real_reload()` 正常返回后执行，部分重载后抛异常会让已被生产值覆盖的层保持失效；复现：隔离子进程用 trace 在 Python 3.14.4 `subprocess.py:755` 中断 reload，捕获异常后 `subprocess.run.__qualname__ == "run"`；调用布防前绑定的 `osascript_fallback` 抵达 Popen 墙，记录 argv `['/usr/bin/osascript','-','audit','audit']`。未启动进程。

[HIGH] `_bmad-output/审查/CARD-TEST-bark-autostub-R1-验收单.md:8` — 验收单仍绑定已废弃的 sibling `6518e5af`，文末 line 267 仍是 `<回填最终 HEAD>`，与 line 154“已回填”相反；复现：`git rev-parse HEAD` = `773bf856eb01d9124b637d4538464a414b3481b7`；`git merge-base --is-ancestor 6518e5af HEAD` rc=1；两对象在四份核心文件上相差 299 insertions/49 deletions。

[MEDIUM] `backend/tests/regression/conftest.py:395` — 层⑥扫描所有 argv 元素会误吞普通数据参数，同时漏掉 bytes executable、`executable=` 和 shell 形态；复现：Popen 墙下 `run(["/usr/bin/printf","osascript"])` 被伪造成 rc=0、Popen 0 次；`run([b"/usr/bin/osascript",...])`、`executable="/usr/bin/osascript"`、shell string、`sh -c` 均抵达 Popen 墙。验收单 line 174 仍错误描述为“argv[0] 含 osascript”，未完整登记这些边界。

[MEDIUM] `backend/tests/regression/bark_egress_probe.py:135` — E 门的 `reload(subprocess)` 会冲掉 probe import 期安装的 Popen 总账，E 门与快照均未发现；复现：直接执行现有 E 门得到 `AUDIT_LEDGER {"before":true,"after_E":false,"after_teardown":false}`，最终 `subprocess.Popen` 已是真实类；官方 E 跑仍判 PASS。因此验收单“本进程内不存在真实 spawn 路径”的总账声明不成立。

[MEDIUM] `backend/scripts/bark_autostub_negative_control.py:319` — `_judge_pytest` 只要求进程 rc 等于报告 exitstatus，不限制正常 pytest rc；复现：构造 `call=passed`、`exitstatus=rc=3`、globals 相等的结构报告，实测输出 `ok=True rc=3`、`rc3_accepted=true`，可把 internal error 后保留下来的 call 报告判绿。

[MEDIUM] `backend/scripts/bark_r1_mutation_negative_controls.py:321` — 变异元裁判仍把 sentinel 当不受约束的合并文本，不能证明指定门红在指定原因；复现：在 `/tmp` 的 HEAD 副本给 F 测试加入 `print("BARK-GATE-F-FIRSTHOP"); assert False, "unrelated mutation failure"`，官方 `_check` 仍输出 `指定门变红=True`、`sentinel 命中=True`、`END_TO_END_META_ACCEPTED=True`；随后逐字节恢复，sha256 回到 `a94afd55…`。

[MEDIUM] `backend/scripts/bark_negctl_report_plugin.py:84` — “全局还原对账”仍没有覆盖守卫实际修改的全部状态：遗漏 `sys.path`，且冷启动时 `tracked=()` 会跳过新加载模块的 `_urlopen`/`osascript_fallback`；复现：两次 `_globals_snapshot(())` 之间插入 sys.path 残留和冷模块桩，快照仍完全相等；在 `/tmp` 副本把 `_urlopen` 改成不恢复的直接赋值后，teardown 后拒绝器仍残留，而 G 门仍 PASS。

[MEDIUM] `backend/scripts/bark_autostub_negative_control.py:324` — `R'` 的 `globals_may_drift=True` 跳过整份快照，而实际只需豁免 `_opener`；复现：当前原始 R' 报告仅 opener 漂移，但加入额外 env、`subprocess.run` 漂移的结构报告仍被判 `ok=True`；在 `/tmp` 副本额外污染 `BARK_KEY_FILE`，官方 R' 单跑仍 PASS。

[MEDIUM] `backend/scripts/bark_negctl_report_plugin.py:73` — opener 指纹补了 `addheaders` 后仍非行为单射；复现：两个 handler 类、proxies、addheaders 完全相同的 `HTTPCookieProcessor` opener，一个 CookieJar 为空、另一个含 `audit=different`，输出 `fingerprints_equal=true`，但 Cookie header 分别为 `null` 与 `audit=different`。验收单“opener 碰撞已关闭”不成立。

[MEDIUM] `backend/tests/regression/bark_egress_probe.py:343` — F 门第三段并非单独由层⑤e承重，验收单引用的 M13 也不存在；复现：布防后仅恢复真实 `urllib.request.proxy_bypass`、保留⑤c，再走外部代理 held opener，仍得到 `AUDIT_REMOVE_5E {"first_hop":["127.0.0.1",9],"gate_would_pass":true}`；`rg '"id": "M13"|M13' backend/scripts/bark_r1_mutation_negative_controls.py` 无命中。

[MEDIUM] `backend/tests/regression/bark_unguarded_probe.py:23` — U 门不能证明其声称的全部 env/sys.path 零副作用：只检查 `BARK_KEY_FILE`，sys.path 只比较 membership 布尔值；复现：导入时 scripts 已在 path 且 `http_proxy` 有值，之后删除代理并重复插入 scripts，直接调用 U 仍得到 `gate_passed=true, scripts_count=2, http_proxy=null`。当前 fixture 早退本身未见污染，问题在自检覆盖不足。

[LOW] `backend/scripts/bark_keyfile_residue_check.py:57` — 合法自定义路径只要名称含 `bark-guard-` 仍会误报残留；复现：`BARK_KEY_FILE=/tmp/legitimate-bark-guard-config/key PYTHONDONTWRITEBYTECODE=1 $PY scripts/bark_keyfile_residue_check.py`，coldstart `1 passed`、KEY_FILE 已恢复到预期路径，但脚本 rc=1 并报 `仍带守卫 tmp 目录痕迹`。

## 已核无发现

- `$PY scripts/bark_autostub_negative_control.py`：当前实际为 **22/22 PASS**；各卸甲跑的 crash path/message 正确。
- `/tmp` 的 `git archive HEAD` 副本运行变异裁判：当前实际为 **16/16 PASS**，每次变异均逐字节恢复并复算 sha256。
- `$PY -m pytest -p no:cacheprovider -q tests/regression/test_daily_review_run.py tests/regression/test_daily_review_pick.py`：**69 passed**；`test_daily_review_pick.py` 确实属于布防文件，U 才是未布防探针。
- 布防前由真实 macOS 系统代理构造的 held opener 确认为 `127.0.0.1:1082`；布防后首跳为 `127.0.0.1:9`。常规大小写的 HTTP、HTTPS、SOCKS、带认证、已有 `no_proxy`，以及全局/新建/局部持有 opener，首跳也均为 `127.0.0.1:9`。
- 成功 reload `send_bark`、`daily_review_run`、`urllib.request`、`subprocess`、`_scproxy`、`importlib` 后，六层均重新生效；名单没有漏掉其他被守卫修改的模块。
- 普通预绑定 reload 路径实测：`getproxies()=={}`、`_opener` 紧接 reload 后为 `None`、`send_bark._urlopen` 已变回真实全局 `urlopen`，held opener 首跳仍为 `127.0.0.1:9`。因此验收单关于②④失效、⑤a/⑤c继续承重的常规形态成立；混合大小写 env 是上述 HIGH 反例。
- stale reload wrapper 在 teardown 后于模块执行前拒绝，`send`/`load_key` 身份均未变化。
- 预绑定通知别名的生产 argv 形态被层⑥接管，Popen 检查点计数为 0。
- 自定义不存在的 `BARK_KEY_FILE` 路径下，C/C'/CS/CS'/G 为 **5/5 符合预期**，没有读取该 key 内容，teardown 后路径与 env 原样恢复。
- 单纯打印伪造 traceback 文本不能骗过 `_judge_pytest`；M9 的结构化 crash frame/绝对路径比较有效。被测代码仍可故意重绑报告插件内部记录，但验收单已明确把该进程内对抗登记为边界。
- 非 Darwin 的预绑定 reload + held opener 安全性未运行；代码和验收单均明确承认该性质只在 macOS 成立。
- 被审文件最终 sha256 与开工值一致，tracked 文件仍与 HEAD 相同；未运行真实推送入口、未读取真实 key 内容、未连接 Neo4j。

VERDICT: FAIL


